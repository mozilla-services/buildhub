import asyncio
import aiohttp
import datetime
import os

import kinto_http

from . import utils
from .inventory_to_records import fetch_metadata, scan_candidates


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

            print('Processing {} item: {}'.format(product, key))

            # Release / Nightly / RC archive.
            if utils.is_build_url(product, url):
                record = utils.record_from_url(url)
                record["download"]["size"] = filesize
                record["download"]["date"] = event_time

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
                # Push result to Kinto.
                kinto_client.create_record(data=record,
                                           bucket=bucket,
                                           collection=collection,
                                           if_not_exists=True)
                print('Created {}'.format(record["id"]))
            # elif

            # If Release metadata.
            if utils.is_release_build_metadata(product, "55.0a1", "toto.exe"):
                print('Release metadata found {}'.format(key))
                # XXX: Find corresponding release files (e.g every platforms/locales/...)

            # elif RC metadata
            # elif Nightly metadata
            else:
                print('Ignored {}'.format(key))


def lambda_handler(event, context):
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(loop, event))
    loop.close()
