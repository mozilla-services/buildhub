import argparse
import asyncio
import async_timeout
import csv
import datetime
import json
import logging
import os
import re
import sys
from collections import defaultdict

import aiohttp
import backoff

from .utils import (archive_url, chunked, is_release_build_metadata, is_build_url,
                    record_from_url, localize_nightly_url, merge_metadata, check_record,
                    ARCHIVE_URL, FILE_EXTENSIONS, DATETIME_FORMAT)


NB_PARALLEL_REQUESTS = int(os.getenv("NB_PARALLEL_REQUESTS", 8))
NB_RETRY_REQUEST = int(os.getenv("NB_RETRY_REQUEST", 3))
TIMEOUT_SECONDS = int(os.getenv("TIMEOUT_SECONDS", 5 * 60))
PRODUCTS = os.getenv("PRODUCTS", "firefox thunderbird mobile").split(" ")


logger = logging.getLogger(__name__)


def read_csv(stream):
    fieldnames = ["Bucket", "Key", "Size", "LastModifiedDate", "md5"]
    reader = csv.DictReader(stream, fieldnames=fieldnames)
    for row in reader:
        yield row


@backoff.on_exception(backoff.expo,
                      asyncio.TimeoutError,
                      max_tries=NB_RETRY_REQUEST)
async def fetch_json(session, url, timeout=TIMEOUT_SECONDS):
    headers = {
        "Accept": "application/json",
        "Cache": "no-cache",
        "User-Agent": "BuildHub;storage-team@mozilla.com"
    }
    try:
        with async_timeout.timeout(timeout):
            logger.debug("GET '{}'".format(url))
            async with session.get(url, headers=headers, timeout=None) as response:
                try:
                    return await response.json()
                except aiohttp.ClientResponseError as e:
                    # Some JSON files are served with wrong content-type.
                    return await response.json(content_type="application/octet-stream")
    except asyncio.TimeoutError:
        logger.error("Timeout on GET '{}'".format(url))
        raise


async def fetch_listing(session, url):
    try:
        data = await fetch_json(session, url)
        return data["prefixes"], data["files"]
    except (aiohttp.ClientError, KeyError, ValueError) as e:
        raise ValueError("Could not fetch '{}': {}".format(url, e))


async def fetch_metadata(session, record):
    try:
        if record["target"]["channel"] == "nightly":
            return await fetch_nightly_metadata(session, record)
        return await fetch_release_metadata(session, record)
    except ValueError as e:
        logger.warning(e)
    return None


_nightly_metadata = {}


async def fetch_nightly_metadata(session, record):
    """A JSON file containing build info is published along the nightly build archive.
    """
    global _nightly_metadata

    url = record["download"]["url"]

    # Make sure the nightly_url is turned into a en-US one.
    nightly_url = localize_nightly_url(url)

    if nightly_url in _nightly_metadata:
        return _nightly_metadata[nightly_url]

    try:
        metadata_url = re.sub("\.({})$".format(FILE_EXTENSIONS), ".json", nightly_url)
        metadata = await fetch_json(session, metadata_url)
        _nightly_metadata[nightly_url] = metadata
        return metadata
    except aiohttp.ClientError:

        # Very old nightly metadata is published as .txt files.
        try:
            # e.g. https://archive.mozilla.org/pub/firefox/nightly/2011/05/
            #      2011-05-05-03-mozilla-central/firefox-6.0a1.en-US.mac.txt
            old_metadata_url = re.sub("\.({})$".format(FILE_EXTENSIONS), ".txt", nightly_url)
            async with session.get(old_metadata_url) as response:
                old_metadata = await response.text()
                m = re.search("^(\d+)\n(http.+)/rev/(.+)$", old_metadata)
                if m:
                    return {
                        "buildid": m.group(1),
                        "moz_source_repo": m.group(2),
                        "moz_source_stamp": m.group(3),
                    }
                # e.g. https://archive.mozilla.org/pub/firefox/nightly/2010/07/2010-07-04-05
                #      -mozilla-central/firefox-4.0b2pre.en-US.win64-x86_64.txt
                m = re.search("^(\d+) (.+)$", old_metadata)
                if m:
                    return {
                        "buildid": m.group(1),
                        "moz_source_stamp": m.group(2),
                        "moz_source_repo": "http://hg.mozilla.org/mozilla-central",
                    }
        except aiohttp.ClientError as e:
            pass

        logger.error("Could not fetch metadata for '%s' from '%s'" % (record["id"], metadata_url))
        return None


_candidates_build_folder = defaultdict(dict)


async def scan_candidates(session, product):
    # For each version take the latest build.
    global _candidates_build_folder

    if product in _candidates_build_folder:
        return

    logger.info("Scan '{}' candidates to get their latest build folder...".format(product))
    candidates_url = archive_url(product, candidate="/")
    candidates_folders, _ = await fetch_listing(session, candidates_url)

    for chunk in chunked(candidates_folders, NB_PARALLEL_REQUESTS):
        futures = []
        versions = []
        for folder in chunk:
            if "-candidates" not in folder:
                continue
            version = folder.replace("-candidates/", "")
            versions.append(version)
            builds_url = archive_url(product, version, candidate="/")
            future = fetch_listing(session, builds_url)
            futures.append(future)
        listings = await asyncio.gather(*futures)

        for version, (build_folders, _) in zip(versions, listings):
            latest_build_folder = sorted(build_folders)[-1]
            _candidates_build_folder[product][version] = latest_build_folder


_release_metadata = {}


async def fetch_release_metadata(session, record):
    """The `candidates` folder contains build info about recent released versions.
    """
    global _candidates_build_folder

    product = record["source"]["product"]
    version = record["target"]["version"]
    platform = record["target"]["platform"]
    locale = "en-US"

    # Metadata for EME-free are the same as original release.
    platform = platform.replace("-eme-free", "")

    try:
        latest_build_folder = "/" + _candidates_build_folder[product][version]
    except KeyError:
        # Version is not listed in candidates. Give up.
        return None

    url = archive_url(product, version, platform, locale, candidate=latest_build_folder)

    # We already have the metadata for this platform and version.
    if url in _release_metadata:
        return _release_metadata[url]

    _, files = await fetch_listing(session, url)
    for f in files:
        filename = f["name"]
        if is_release_build_metadata(product, version, filename):
            metadata = await fetch_json(session, url + filename)
            _release_metadata[url] = metadata
            return metadata

    # Version exists in candidates but has no metadata!
    _release_metadata[url] = None  # Don't try it anymore.
    raise ValueError("Missing metadata for candidate {}".format(url))


async def process_batch(session, batch, stdout):
    # Parallel fetch of metadata for each item of the batch.
    logger.info("Fetch metadata for {} releases...".format(len(batch)))
    futures = [fetch_metadata(session, record) for record in batch]
    metadatas = await asyncio.gather(*futures)
    results = [merge_metadata(record, metadata)
               for record, metadata in zip(batch, metadatas)]
    for result in results:
        try:
            check_record(result)
        except ValueError as e:
            logger.warning(e)
        stdout.write(json.dumps({"data": result}) + "\n")
    return results


async def csv_to_records(loop, stdin, stdout):

    def inventory_by_folder(stdin):
        previous = None
        result = []
        for entry in read_csv(stdin):
            object_key = entry["Key"]
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

    def deduplicate_windows_entries(entries):
        # Windows releases are published as both .zip and .exe files.
        # Deduplicate these (keep .zip if .exe is present, else .exe only).
        # Some old Linux versions (1.5b2) were published with installer.tar.gz.
        longer_first = sorted(entries, key=lambda e: len(e["Key"]), reverse=True)
        deduplicate = {
            e["Key"].replace('.installer.exe', '')
                    .replace('.exe', '')
                    .replace('.installer.tar.gz', '')
                    .replace('.tar.gz', '')
                    .replace('.zip', ''): e
            for e in longer_first}
        return deduplicate.values()

    async with aiohttp.ClientSession(loop=loop) as session:
        batch = []

        for entries in inventory_by_folder(stdin):

            entries = deduplicate_windows_entries(entries)

            for entry in entries:
                object_key = entry["Key"]

                try:
                    product = object_key.split('/')[1]  # /pub/thunderbird/nightly/...
                except IndexError:
                    continue  # e.g. https://archive.mozilla.org/favicon.ico

                if product not in PRODUCTS:
                    continue

                # Scan the list of candidates metadata (no-op if already initialized).
                await scan_candidates(session, product)

                url = ARCHIVE_URL + object_key

                if not is_build_url(product, url):
                    continue

                record = record_from_url(url)

                # Complete with info that can't be obtained from the URL.
                filesize = int(float(entry["Size"]))  # e.g. 2E+10
                lastmodified = datetime.datetime.strptime(entry["LastModifiedDate"],
                                                          "%Y-%m-%dT%H:%M:%S.%fZ")
                lastmodified = lastmodified.strftime(DATETIME_FORMAT)
                record["download"]["size"] = filesize
                record["download"]["date"] = lastmodified

                if len(batch) < NB_PARALLEL_REQUESTS:
                    batch.append(record)
                else:
                    await process_batch(session, batch, stdout)

                    batch = []  # Go on.

        await process_batch(session, batch, stdout)  # Last loop iteration.


async def main(loop):
    parser = argparse.ArgumentParser(description=('Read S3 CSV inventory from stdin '
                                                  'and print out Kinto records.'))
    parser.add_argument('-v', '--verbose', action='store_const',
                        const=logging.INFO, dest='verbosity',
                        help='Show all messages.')

    parser.add_argument('-D', '--debug', action='store_const',
                        const=logging.DEBUG, dest='verbosity',
                        help='Show all messages, including debug messages.')
    args = parser.parse_args()

    logger.addHandler(logging.StreamHandler())
    if args.verbosity:
        logger.setLevel(args.verbosity)
    else:
        logger.setLevel(logging.WARNING)

    await csv_to_records(loop, sys.stdin, sys.stdout)


def run():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(loop))
    loop.close()


if __name__ == "__main__":
    run()
