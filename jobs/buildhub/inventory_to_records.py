import argparse
import asyncio
import async_timeout
import csv
import datetime
import json
import logging
import os
import re

import aiohttp
import backoff

from .utils import (archive_url, is_release_metadata, is_release_filename,
                    record_from_url, localize_nightly_url, merge_metadata,
                    FILE_EXTENSIONS, DATETIME_FORMAT)


BATCH_SIZE = 4
NB_RETRY_REQUEST = 3
TIMEOUT_SECONDS = 5 * 60


logger = logging.getLogger(__name__)


def read_csv(filename):
    with open(filename, "rb") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            yield row


@backoff.on_exception(backoff.expo,
                      asyncio.TimeoutError,
                      max_tries=NB_RETRY_REQUEST)
async def fetch_json(session, url):
    headers = {
        "Accept": "application/json",
        "User-Agent": "BuildHub;storage-team@mozilla.com"
    }
    with async_timeout.timeout(TIMEOUT_SECONDS):
        async with session.get(url, headers=headers, timeout=None) as response:
            return await response.json()


async def fetch_listing(session, url):
    try:
        data = await fetch_json(session, url)
        return data["prefixes"], data["files"]
    except (aiohttp.ClientError, KeyError, ValueError) as e:
        raise ValueError("Could not fetch {}: {}".format(url, e))


async def fetch_metadata(session, record):
    if record["target"]["channel"] == "nightly":
        metadata = await fetch_nightly_metadata(session, record)
    else:
        metadata = await fetch_release_metadata(session, record)

    return metadata


_nightly_metadata = {}
_nightly_metadata_lock = asyncio.Lock()


async def fetch_nightly_metadata(session, record):
    """A JSON file containing build info is published along the nightly archive.
    """
    global _nightly_metadata

    download_url = record["download"]["url"]

    # Make sure the nightly_url is turned into a en-US one.
    nightly_url = localize_nightly_url(download_url)

    with await _nightly_metadata_lock:
        if nightly_url in _nightly_metadata:
            return _nightly_metadata[nightly_url]

        try:
            metadata_url = re.sub("\.({})$".format(FILE_EXTENSIONS), ".json", nightly_url)
            metadata = await fetch_json(session, metadata_url)
            _nightly_metadata[nightly_url] = metadata
            return metadata
        except aiohttp.ClientError:
            return None


_candidates = {}
_candidates_lock = asyncio.Lock()


async def fetch_release_metadata(session, record):
    """The `candidates` folder contains build info about recent released versions.
    """
    global _candidates

    product = record["source"]["product"]
    version = record["target"]["version"]
    platform = record["target"]["platform"]
    locale = record["target"]["locale"]

    if locale != "en-US":
        locale = 'en-US'

    with await _candidates_lock:
        # Keep the list of latest available candidates per product, for more efficiency.
        if _candidates.get(product) is None:
            candidates_url = archive_url(product, candidate="/")
            candidates_folders, _ = await fetch_listing(session, candidates_url)
            # For each version take the latest build.
            _candidates[product] = {}
            for f in candidates_folders:
                if f == "archived/":
                    continue
                candidate_version = f.replace("-candidates/", "")
                builds_url = archive_url(product, candidate_version, candidate="/")
                build_folders, _ = await fetch_listing(session, builds_url)
                latest_build_folder = sorted(build_folders)[-1]
                _candidates[product][candidate_version] = latest_build_folder

    # Candidates are only available for a subset of versions.
    if version not in _candidates[product]:
        return None

    latest_build_folder = "/" + _candidates[product][version]
    try:
        url = archive_url(product, version, platform, locale, candidate=latest_build_folder)
        _, files = await fetch_listing(session, url)

        for f_ in files:
            filename = f_["name"]
            if is_release_metadata(product, version, filename):
                url += filename
                metadata = await fetch_json(session, url)
                return metadata

    except (ValueError, aiohttp.ClientError) as e:
        logger.error("Could not fetch metadata for '%s' from '%s'" % (record["id"], url))
    return None


async def process_batch(session, batch):
    # Parallel fetch of metadata for each item of the batch.
    futures = [fetch_metadata(session, record) for record in batch]
    metadatas = await asyncio.gather(*futures)
    results = [merge_metadata(record, metadata)
               for record, metadata in zip(batch, metadatas)]
    return results


async def main(loop):
    parser = argparse.ArgumentParser(description='Load S3 inventory as Kinto releases.')
    parser.add_argument('filename', help='CSV file to load')
    args = parser.parse_args()

    batch = []

    async with aiohttp.ClientSession(loop=loop) as session:
        for entry in read_csv(args.filename):
            bucket_name = entry["Bucket"]
            object_key = entry["Key"]

            product = bucket_name  # XXX ?

            url = "https://archive.mozilla.org/" + bucket_name + object_key  # XXX ?

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

            if len(batch) < BATCH_SIZE:
                batch.append(record)
            else:
                results = await process_batch(session, batch)

                for result in results:
                    print(json.dumps(result))

                batch = []  # Go on.

        await process_batch(batch)  # Last loop iteration.


def run():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(loop))
    loop.close()


if __name__ == "__main__":
    run()
