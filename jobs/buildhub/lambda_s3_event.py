import asyncio
import datetime
import os
import re

import aiohttp
import async_timeout
import kinto_http

from . import utils
from .inventory_to_records import fetch_json, fetch_listing, fetch_metadata, scan_candidates


TIMEOUT_SECONDS = int(os.getenv("TIMEOUT_SECONDS", 5 * 60))


async def check_exists(session, url, timeout=TIMEOUT_SECONDS):
    try:
        with async_timeout.timeout(timeout):
            # async with session.head(url, timeout=None) as response:
            async with session.get(url, timeout=None) as response:
                return response.status == 200
    except aiohttp.ClientError:
        return False


async def main(loop, event):
    """
    Trigger when S3 event kicks in.
    http://docs.aws.amazon.com/AmazonS3/latest/dev/notification-content-structure.html
    """
    server_url = os.getenv("SERVER_URL", "http://localhost:8888/v1")
    bucket = os.getenv("BUCKET", "build-hub")
    collection = os.getenv("COLLECTION", "releases")
    kinto_auth = tuple(os.getenv("AUTH", "user:pass").split(":"))

    kinto_client = kinto_http.Client(server_url=server_url, auth=kinto_auth)

    # Use event time as archive publication.
    event_time = datetime.datetime.strptime(event['eventTime'], "%Y-%m-%dT%H:%M:%S.%fZ")
    event_time = event_time.strftime(utils.DATETIME_FORMAT)

    async with aiohttp.ClientSession(loop=loop) as session:
        for record in event['Records']:
            records_to_create = []

            key = record['s3']['object']['key']
            filesize = record['s3']['object']['size']
            url = utils.ARCHIVE_URL + key

            try:
                product = key.split('/')[1]  # /pub/thunderbird/nightly/...
            except IndexError:
                continue  # e.g. https://archive.mozilla.org/favicon.ico

            if product not in utils.ALL_PRODUCTS:
                print('Skip product {}'.format(product))
                continue

            # Release / Nightly / RC archive.
            if utils.is_build_url(product, url):
                print('Processing {} archive: {}'.format(product, key))

                record = utils.record_from_url(url)

                # Fetch release metadata.
                await scan_candidates(session, product)
                metadata = await fetch_metadata(session, record)
                # If JSON metadata not available, archive will be handled when JSON
                # is delivered.
                if metadata is None:
                    print('JSON metadata not available {}'.format(record["id"]))
                    continue

                # Merge obtained metadata.
                record = utils.merge_metadata(record, metadata)
                records_to_create.append(record)

            # RC metadata
            elif utils.is_rc_build_metadata(product, url):
                print('Processing {} RC metadata: {}'.format(product, key))

                # pub/firefox/candidates/55.0b12-candidates/build1/mac/en-US/
                # firefox-55.0b12.json
                metadata = await fetch_json(session, url)
                metadata["buildnumber"] = int(re.search("/build(\d+)/", url).group(1))

                # Check if localized languages are here (including en-US archive).
                l10n_parent_url = re.sub("en-US/.+", "", url)
                l10n_folders, _ = await fetch_listing(session, l10n_parent_url)
                for locale in l10n_folders:
                    _, files = await fetch_listing(session, l10n_parent_url + locale)
                    for f in files:
                        rc_url = l10n_parent_url + locale + f["name"]
                        if utils.is_build_url(product, rc_url):
                            record = utils.record_from_url(rc_url)
                            record = utils.merge_metadata(record, metadata)
                            records_to_create.append(record)
                # Theorically release should never be there yet :)
                # And repacks like EME-free/sha1 don't seem to be published in RC.

            # Nightly metadata
            # pub/firefox/nightly/2017/08/2017-08-08-11-40-32-mozilla-central/
            # firefox-57.0a1.en-US.linux-i686.json
            # -l10n/...
            elif utils.is_nightly_build_metadata(product, url):
                print('Processing {} nightly metadata: {}'.format(product, key))

                metadata = await fetch_json(session, url)

                # Check if english version is here.
                platform = metadata["moz_pkg_platform"]
                extension = utils.extension_for_platform(platform)
                archive_url = url.replace(".json", extension)

                exists = await check_exists(session, archive_url)
                if exists:
                    record = utils.record_from_url(archive_url)
                    record = utils.merge_metadata(record, metadata)
                    records_to_create.append(record)
                # Check also localized versions.
                l10n_folder_url = re.sub("-mozilla-central([^/]*)/([^/]+)$",
                                         "-mozilla-central\\1-l10n/",
                                         url)
                try:
                    _, files = await fetch_listing(session, l10n_folder_url)
                except ValueError:
                    files = []  # No -l10/ folder published yet.
                for f in files:
                    if platform not in f["name"] and product != "mobile":
                        # metadata are by platform.
                        # (mobile platforms are contained by folder)
                        continue
                    nightly_url = l10n_folder_url + f["name"]
                    if utils.is_build_url(product, nightly_url):
                        record = utils.record_from_url(nightly_url)
                        record = utils.merge_metadata(record, metadata)
                        records_to_create.append(record)

            else:
                print('Ignored {}'.format(key))

            for record in records_to_create:
                # XXX: this is wrong for metadata events
                record["download"]["size"] = filesize
                record["download"]["date"] = event_time
                # Check that fields values look OK.
                utils.check_record(record)
                # Push result to Kinto.
                kinto_client.create_record(data=record,
                                           bucket=bucket,
                                           collection=collection,
                                           if_not_exists=True)
                print('Created {}'.format(record["id"]))



def lambda_handler(event, context):
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(loop, event))
    loop.close()
