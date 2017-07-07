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

from .utils import (archive_url, chunked, is_release_metadata, is_release_filename,
                    record_from_url, localize_nightly_url, merge_metadata,
                    ARCHIVE_URL, FILE_EXTENSIONS, DATETIME_FORMAT)


NB_PARALLEL_REQUESTS = int(os.getenv("NB_PARALLEL_REQUESTS", 8))
NB_RETRY_REQUEST = int(os.getenv("NB_RETRY_REQUEST", 3))
TIMEOUT_SECONDS = int(os.getenv("TIMEOUT_SECONDS", 5 * 60))


logger = logging.getLogger(__name__)


def read_csv(filename):
    with open(filename, "r") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            yield row


@backoff.on_exception(backoff.expo,
                      asyncio.TimeoutError,
                      max_tries=NB_RETRY_REQUEST)
async def fetch_json(session, url, timeout=TIMEOUT_SECONDS):
    headers = {
        "Accept": "application/json",
        "User-Agent": "BuildHub;storage-team@mozilla.com"
    }
    try:
        with async_timeout.timeout(timeout):
            logger.debug("GET '{}'".format(url))
            async with session.get(url, headers=headers, timeout=None) as response:
                return await response.json()
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
    if record["target"]["channel"] == "nightly":
        return await fetch_nightly_metadata(session, record)
    return await fetch_release_metadata(session, record)


_nightly_metadata = {}


async def fetch_nightly_metadata(session, record):
    """A JSON file containing build info is published along the nightly archive.
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
        logger.error("Could not fetch metadata for '%s' from '%s'" % (record["id"], url))
        return None


_candidates_build_folder = defaultdict(dict)


async def scan_candidates(session, product):
    # For each version take the latest build.
    global _candidates_build_folder

    if len(_candidates_build_folder) > 0:
        return

    logger.info("Scan candidates to get their latest build folder...")
    candidates_url = archive_url(product, candidate="/")
    candidates_folders, _ = await fetch_listing(session, candidates_url)

    for chunk in chunked(candidates_folders, NB_PARALLEL_REQUESTS):
        futures = []
        versions = []
        for folder in chunk:
            if folder == "archived/":
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


async def fetch_release_metadata(session, record):
    """The `candidates` folder contains build info about recent released versions.
    """
    global _candidates_build_folder

    product = record["source"]["product"]
    version = record["target"]["version"]
    platform = record["target"]["platform"]
    locale = "en-US"

    try:
        latest_build_folder = "/" + _candidates_build_folder[product][version]
    except KeyError:
        # Version is not listed in candidates. Give up.
        return None

    url = archive_url(product, version, platform, locale, candidate=latest_build_folder)
    _, files = await fetch_listing(session, url)

    for f in files:
        filename = f["name"]
        if is_release_metadata(product, version, filename):
            metadata = await fetch_json(session, url + filename)
            return metadata

    # Version exists in candidates but has no metadata!
    raise ValueError("Missing metadata for candidate {}".format(url))


async def process_batch(session, batch, stdout):
    # Parallel fetch of metadata for each item of the batch.
    logger.info("Fetch metadata for {} releases...".format(len(batch)))
    futures = [fetch_metadata(session, record) for record in batch]
    metadatas = await asyncio.gather(*futures)
    results = [merge_metadata(record, metadata)
               for record, metadata in zip(batch, metadatas)]
    for result in results:
        stdout.write(json.dumps(result) + "\n")
    return results


async def csv_to_records(loop, filename, stdout):
    batch = []

    async with aiohttp.ClientSession(loop=loop) as session:
        for entry in read_csv(filename):
            bucket_name = entry["Bucket"]
            object_key = entry["Key"]

            product = bucket_name  # XXX ?

            # Scan the list of candidates metadata (no-op if already initialized).
            await scan_candidates(session, product)

            url = ARCHIVE_URL + bucket_name + object_key  # XXX ?

            if not is_release_filename(product, os.path.basename(url)):
                continue

            record = record_from_url(url)

            # XXX: skip existing records
            # if record["id"] in known_records_ids:
            #    continue

            # Complete with info that can't be obtained from the URL.
            filesize = int(float(entry["Size"]))  # e.g. 2E+10
            lastmodified = datetime.datetime.strptime(entry["LastModifiedDate"], "%Y-%m-%dT%H%M")
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
    parser = argparse.ArgumentParser(description='Load S3 inventory as Kinto releases.')
    parser.add_argument('filename', help='CSV file to load')
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
        logger.setLevel(logging.CRITICAL)

    await csv_to_records(loop, args.filename, sys.stdout)


def run():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(loop))
    loop.close()


if __name__ == "__main__":
    run()
