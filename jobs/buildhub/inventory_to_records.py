# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, you can obtain one at http://mozilla.org/MPL/2.0/.

import argparse
import asyncio
import async_timeout
import csv
import json
import logging
import os
import pkg_resources
import re
import sys
from collections import defaultdict

import aiohttp
import backoff
import ciso8601
from decouple import config

from buildhub.utils import (
    archive_url, chunked, is_release_build_metadata, is_build_url,
    record_from_url, localize_nightly_url, merge_metadata, check_record,
    localize_release_candidate_url, stream_as_generator, split_lines,
    key_to_archive_url,
    FILE_EXTENSIONS, DATETIME_FORMAT, ALL_PRODUCTS
)


NB_PARALLEL_REQUESTS = config('NB_PARALLEL_REQUESTS', default=8, cast=int)
NB_RETRY_REQUEST = config('NB_RETRY_REQUEST', default=9, cast=int)
TIMEOUT_SECONDS = config('TIMEOUT_SECONDS', default=5 * 60, cast=int)
PRODUCTS = config(
    'PRODUCTS', default=' '.join(ALL_PRODUCTS),
    cast=lambda v: [s.strip() for s in v.split()]
)
CACHE_FOLDER = config('CACHE_FOLDER', default='.')

logger = logging.getLogger()  # root logger.

# Module version, as defined in PEP-0396.
try:
    __version__ = pkg_resources.get_distribution(__package__).version
except pkg_resources.DistributionNotFound:
    __version__ = '0.1.dev'


class JSONFileNotFound(Exception):
    """Happens when we try to fetch a JSON URL and the response is a 404"""


async def read_csv(input_generator):
    """
    :param input_generator: async generator of raw bytes
    """
    fieldnames = ['Bucket', 'Key', 'Size', 'LastModifiedDate', 'md5']
    async for lines in split_lines(input_generator):
        reader = csv.DictReader(lines, fieldnames=fieldnames)
        for row in reader:
            yield row


@backoff.on_exception(backoff.expo,
                      (aiohttp.ClientResponseError, asyncio.TimeoutError),
                      max_tries=NB_RETRY_REQUEST)
async def fetch_json(
    session,
    url,
    timeout=TIMEOUT_SECONDS,
    retry_on_notfound=False
):
    """Return response JSON by the URL.

    By default, any response that is >=400 will raise a ClientResponseError
    which is part of the backoff.on_exception configuration.
    If you explicitly don't want that for status code 404, you can set
    the `retry_on_notfound` parameter to True. Then it will raise a
    JSONFileNotFound exception instead and will not retry automatically.

    *Sometimes* a 404 status code is actually something that can
    happen due to the latency of a slow update in
    archive.mozilla.org so if you just back off and try again
    in a couple of seconds it will work.
    """
    headers = {
        'Accept': 'application/json',
        'Cache': 'no-cache',
        'User-Agent': 'BuildHub;storage-team@mozilla.com'
    }
    try:
        with async_timeout.timeout(timeout):
            logger.debug("GET '{}'".format(url))
            async with session.get(
                url,
                headers=headers,
                timeout=None
            ) as response:
                if response.status == 404 and not retry_on_notfound:
                    raise JSONFileNotFound(url)

                response.raise_for_status()
                try:
                    return await response.json()
                except aiohttp.ClientResponseError as e:
                    # Some JSON files are served with wrong content-type.
                    return await response.json(
                        content_type='application/octet-stream'
                    )
    except asyncio.TimeoutError:
        logger.error("Timeout on GET '{}'".format(url))
        raise


async def fetch_listing(session, url, retry_on_notfound=False):
    try:
        data = await fetch_json(
            session,
            url,
            retry_on_notfound=retry_on_notfound,
        )
        return data['prefixes'], data['files']
    except (aiohttp.ClientError, KeyError, ValueError) as e:
        raise ValueError("Could not fetch '{}': {}".format(url, e))


async def fetch_metadata(session, record):
    try:
        if 'nightly' in record['target']['channel']:  # nightly-old-id
            return await fetch_nightly_metadata(session, record)
        if 'rc' in record['target']['version']:
            return await fetch_release_candidate_metadata(session, record)
        return await fetch_release_metadata(session, record)
    except ValueError as e:
        logger.warning(e)
    except JSONFileNotFound as e:
        logger.warning(f'Failed to download metadata file {e}')
    return None


_nightly_metadata = {}


async def fetch_nightly_metadata(session, record):
    """A JSON file containing build info is published along the
    nightly build archive.
    """
    global _nightly_metadata

    url = record['download']['url']

    # Make sure the nightly_url is turned into a en-US one.
    nightly_url = localize_nightly_url(url)

    if nightly_url in _nightly_metadata:
        return _nightly_metadata[nightly_url]

    extensions = '|'.join(FILE_EXTENSIONS)

    try:
        metadata_url = re.sub(
            '\.({})$'.format(extensions),
            '.json',
            nightly_url
        )
        metadata = await fetch_json(session, metadata_url)
        _nightly_metadata[nightly_url] = metadata
        return metadata
    except JSONFileNotFound:

        # Very old nightly metadata is published as .txt files.
        try:
            # e.g. https://archive.mozilla.org/pub/firefox/nightly/2011/05/
            #      2011-05-05-03-mozilla-central/firefox-6.0a1.en-US.mac.txt
            old_metadata_url = re.sub(
                '\.({})$'.format(extensions),
                '.txt',
                nightly_url
            )
            async with session.get(old_metadata_url) as response:
                old_metadata = await response.text()
                m = re.search('^(\d+)\n(http.+)/rev/(.+)$', old_metadata)
                if m:
                    metadata = {
                        'buildid': m.group(1),
                        'moz_source_repo': m.group(2),
                        'moz_source_stamp': m.group(3),
                    }
                    _nightly_metadata[nightly_url] = metadata
                    return metadata
                # e.g.
                # https://archive.mozilla.org/pub/firefox/nightly/2010/07/2010-07-04-05-mozilla-central/firefox-4.0b2pre.en-US.win64-x86_64.txt
                m = re.search('^(\d+) (.+)$', old_metadata)
                if m:
                    metadata = {
                        'buildid': m.group(1),
                        'moz_source_stamp': m.group(2),
                        'moz_source_repo': (
                            'http://hg.mozilla.org/mozilla-central'
                        ),
                    }
                    _nightly_metadata[nightly_url] = metadata
                    return metadata
        except aiohttp.ClientError as e:
            pass

        logger.warning(
            f"Could not fetch metadata for '{record['id']}' "
            f"from '{metadata_url}'"
        )
        _nightly_metadata[url] = None  # Don't try it anymore.
        return None


_rc_metadata = {}


async def fetch_release_candidate_metadata(session, record):
    """A JSON file containing build info is published along the
    nightly build archive.
    """
    global _rc_metadata

    url = record['download']['url']

    # Make sure the rc URL is turned into a en-US one.
    rc_url = localize_release_candidate_url(url)

    if rc_url in _rc_metadata:
        return _rc_metadata[rc_url]

    product = record['source']['product']
    if product == 'devedition':
        product = 'firefox'
    if product == 'fennec':
        metadata_url = re.sub(
            '\.({})$'.format('|'.join(FILE_EXTENSIONS)),
            '.json',
            rc_url
        )
    else:
        major_version = record['target']['version'].split('rc')[0]
        parts = rc_url.split('/')
        parts[-1] = '{}-{}.json'.format(product, major_version)
        metadata_url = '/'.join(parts)
    try:
        metadata = await fetch_json(session, metadata_url)
    except aiohttp.ClientError as e:
        # Old RC like https://archive.mozilla.org/pub/firefox/releases/1.0rc1/
        # don't have metadata.
        logger.warning(
            f"Could not fetch metadata for '{record['id']}' "
            f"from '{metadata_url}'"
        )
        _rc_metadata[rc_url] = None  # Don't try it anymore.
        return None

    m = re.search('/build(\d+)/', url)
    metadata['buildnumber'] = int(m.group(1))

    _rc_metadata[rc_url] = metadata
    return metadata


_candidates_build_folder = defaultdict(dict)


async def scan_candidates(session, product):
    # For each version take the latest build.
    global _candidates_build_folder

    if product == 'mobile':
        product = 'fennec'

    if product in _candidates_build_folder:
        return

    logger.info(
        f"Scan '{product}' candidates to get their latest build folder..."
    )
    candidates_url = archive_url(product, candidate='/')
    candidates_folders, _ = await fetch_listing(session, candidates_url)

    for chunk in chunked(candidates_folders, NB_PARALLEL_REQUESTS):
        futures = []
        versions = []
        for folder in chunk:
            if '-candidates' not in folder:
                continue
            version = folder.replace('-candidates/', '')
            versions.append(version)
            builds_url = archive_url(product, version, candidate='/')
            future = fetch_listing(session, builds_url)
            futures.append(future)
        listings = await asyncio.gather(*futures)

        for version, (build_folders, _) in zip(versions, listings):
            latest_build_folder = sorted(
                build_folders,
                key=lambda x: re.sub("[^0-9]", "", x).zfill(3)
            )[-1]
            _candidates_build_folder[product][version] = latest_build_folder


_release_metadata = {}


async def fetch_release_metadata(session, record):
    """The `candidates` folder contains build info about recent
    released versions.
    """
    global _candidates_build_folder

    product = record['source']['product']
    version = record['target']['version']
    platform = record['target']['platform']
    locale = 'en-US'

    try:
        latest_build_folder = _candidates_build_folder[product][version]
    except KeyError:
        # Version is not listed in candidates. Give up.
        return None

    build_number = int(latest_build_folder.strip('/')[-1])  # build3 -> 3

    # Metadata for EME-free and sha1 repacks are the same as original release.
    platform = re.sub('-(eme-free|sha1)', '', platform, flags=re.I)

    url = archive_url(
        product, version, platform, locale, candidate='/' + latest_build_folder
    )

    # We already have the metadata for this platform and version.
    if url in _release_metadata:
        return _release_metadata[url]

    try:
        _, files = await fetch_listing(session, url)
    except ValueError:
        # Some partial update don't have metadata. eg. /47.0.1-candidates/
        _release_metadata[url] = None
        return None

    for f in files:
        filename = f['name']
        if is_release_build_metadata(product, version, filename):
            try:
                metadata = await fetch_json(session, url + filename)
                metadata['buildnumber'] = build_number
                _release_metadata[url] = metadata
                return metadata
            except aiohttp.ClientError as e:
                # Sometimes, some XML comes out \o/ (see #259)
                pass

    # Version exists in candidates but has no metadata!
    _release_metadata[url] = None  # Don't try it anymore.
    raise ValueError('Missing metadata for candidate {}'.format(url))


async def process_batch(session, batch, skip_incomplete):
    # Parallel fetch of metadata for each item of the batch.
    logger.debug('Fetch metadata for {} releases...'.format(len(batch)))
    futures = [fetch_metadata(session, record) for record in batch]
    metadatas = await asyncio.gather(*futures)
    results = [merge_metadata(record, metadata)
               for record, metadata in zip(batch, metadatas)]
    for result in results:
        try:
            check_record(result)
        except ValueError as e:
            # Keep only results where metadata was found.
            if skip_incomplete:
                logger.warning(e)
                continue
        yield {'data': result}


async def csv_to_records(
    loop,
    stdin,
    skip_incomplete=True,
    min_last_modified=None,
    cache_folder=CACHE_FOLDER,
):
    """
    :rtype: async generator of records (dict-like)
    """

    async def inventory_by_folder(stdin):
        previous = None
        result = []
        async for entry in read_csv(stdin):
            object_key = entry['Key']
            folder = os.path.dirname(object_key)
            if previous is None:
                previous = folder

            if previous == folder:
                result.append(entry)
            else:
                yield result
                previous = folder
                result = [entry]
        if result:
            yield result

    # Read metadata of previous run, and warm up cache.
    # Will save a lot of hits to archive.mozilla.org.
    metadata_cache_file = os.path.join(
        cache_folder,
        '.metadata-{}.json'.format(__version__)
    )
    if os.path.exists(metadata_cache_file):
        with open(metadata_cache_file) as f:
            metadata = json.load(f)
        _rc_metadata.update(metadata['rc'])
        _release_metadata.update(metadata['release'])
        _nightly_metadata.update(metadata['nightly'])

    async with aiohttp.ClientSession(loop=loop) as session:
        batch = []

        async for entries in inventory_by_folder(stdin):
            for entry in entries:
                object_key = entry['Key']

                # This is the lowest barrier of entry (no pun intended).
                # If the entry's 'Key" value doesn't end on any of the
                # known FILE_EXTENSIONS it will never pass a build URL
                # later in the loop.
                if not any(
                    object_key.endswith(ext) for ext in FILE_EXTENSIONS
                ):
                    # Actually, eventually that FILE_EXTENSION check will
                    # be done again more detailed inside the is_build_url
                    # function.
                    # This step was just to weed out some easy ones.
                    continue

                # When you have a 'min_last_modified' set, and it's something
                # like 24 hours, then probably 99% of records can be skipped
                # with this little date comparison. So do this check
                # for a skip as early as possible.
                # See https://github.com/mozilla-services/buildhub/issues/427
                # Note! ciso8601.parse_datetime will always return a timezone
                # aware datetime.datetime instance with tzinfo=UTC.
                lastmodified = ciso8601.parse_datetime(
                    entry['LastModifiedDate']
                )
                if min_last_modified and lastmodified < min_last_modified:
                    continue

                try:
                    # /pub/thunderbird/nightly/...
                    product = object_key.split('/')[1]
                except IndexError:
                    continue  # e.g. https://archive.mozilla.org/favicon.ico

                if product not in PRODUCTS:
                    continue

                url = key_to_archive_url(object_key)

                if not is_build_url(product, url):
                    continue
                try:
                    record = record_from_url(url)
                except Exception as e:
                    logger.exception(e)
                    continue

                # Scan the list of candidates metadata (no-op if
                # already initialized).
                await scan_candidates(session, product)

                # Complete with info that can't be obtained from the URL.
                filesize = int(float(entry['Size']))  # e.g. 2E+10
                lastmodified = lastmodified.strftime(DATETIME_FORMAT)
                record['download']['size'] = filesize
                record['download']['date'] = lastmodified

                batch.append(record)

                if len(batch) == NB_PARALLEL_REQUESTS:
                    async for result in process_batch(
                        session,
                        batch,
                        skip_incomplete
                    ):
                        yield result

                    batch = []  # Go on.

        # Last loop iteration.
        async for result in process_batch(session, batch, skip_incomplete):
            yield result

    # Save accumulated metadata for next runs.
    tmpfilename = metadata_cache_file + '.tmp'
    metadata = {
        'rc': _rc_metadata,
        'release': _release_metadata,
        'nightly': _nightly_metadata,
    }
    json.dump(metadata, open(tmpfilename, 'w'))
    os.rename(tmpfilename, metadata_cache_file)


async def main(loop, cache_folder=CACHE_FOLDER):
    parser = argparse.ArgumentParser(
        description=(
            'Read S3 CSV inventory from stdin '
            'and print out Kinto records.'
        ),
    )
    parser.add_argument(
        '-v',
        '--verbose',
        action='store_const',
        const=logging.INFO,
        dest='verbosity',
        help='Show all messages.'
    )

    parser.add_argument(
        '-D',
        '--debug',
        action='store_const',
        const=logging.DEBUG,
        dest='verbosity',
        help='Show all messages, including debug messages.'
    )
    args = parser.parse_args()

    logger.addHandler(logging.StreamHandler())
    if args.verbosity:
        logger.setLevel(args.verbosity)
    else:
        logger.setLevel(logging.WARNING)

    async for record in csv_to_records(
        loop,
        stream_as_generator(
            loop, sys.stdin
        ),
        cache_folder=cache_folder,
    ):
        sys.stdout.write(json.dumps(record) + '\n')


def run():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(loop))
    loop.close()


if __name__ == '__main__':
    run()
