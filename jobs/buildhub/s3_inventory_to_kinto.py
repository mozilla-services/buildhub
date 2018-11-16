# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, you can obtain one at http://mozilla.org/MPL/2.0/.

import re
import asyncio
import datetime
import glob
import json
import logging
import os
import pkgutil
import tempfile
import time
import zlib
from concurrent.futures import ThreadPoolExecutor

import aiofiles
import aiobotocore
import botocore
from decouple import config, Csv
from aiohttp.client_exceptions import ClientPayloadError
import kinto_http
import raven
from raven.handlers.logging import SentryHandler
from ruamel import yaml
from kinto_wizard.async_kinto import AsyncKintoClient
from kinto_wizard.yaml2kinto import initialize_server

from buildhub.inventory_to_records import (
    __version__,
    NB_RETRY_REQUEST,
    csv_to_records,
)
from buildhub.to_kinto import fetch_existing, main as to_kinto_main
from buildhub.configure_markus import get_metrics


REGION_NAME = 'us-east-1'
BUCKET = 'net-mozaws-prod-delivery-inventory-us-east-1'
FOLDER = (
    'public/inventories/net-mozaws-prod-delivery-{inventory}/'
    'delivery-{inventory}/'
)
CHUNK_SIZE = 1024 * 256  # 256 KB
MAX_CSV_DOWNLOAD_AGE = 60 * 60 * 24 * 2  # two days

INITIALIZE_SERVER = config('INITIALIZE_SERVER', default=True, cast=bool)

# Minimum number of hours old an entry in the CSV files need to be
# to NOT be skipped.
MIN_AGE_LAST_MODIFIED_HOURS = config(
    'MIN_AGE_LAST_MODIFIED_HOURS', default=0, cast=int
)

CSV_DOWNLOAD_DIRECTORY = config(
    'CSV_DOWNLOAD_DIRECTORY',
    default=tempfile.gettempdir()
)

INVENTORIES = tuple(config(
    'INVENTORIES',
    default='firefox, archive',
    cast=Csv()
))

LOG_LEVEL = config('LOG_LEVEL', default='INFO')

STORE_DAILY_MANIFEST = config('STORE_DAILY_MANIFEST', default=False, cast=bool)

# Optional Sentry with synchronuous client.
SENTRY_DSN = config('SENTRY_DSN', default=None)
sentry = raven.Client(
    SENTRY_DSN,
    transport=raven.transport.http.HTTPTransport,
    release=__version__,
)

logger = logging.getLogger()  # root logger.
metrics = get_metrics('buildhub')


async def initialize_kinto(loop, kinto_client, bucket, collection):
    """
    Initialize the remote server with the initialization.yml file.
    """
    # Leverage kinto-wizard async client.
    thread_pool = ThreadPoolExecutor()
    async_client = AsyncKintoClient(kinto_client, loop, thread_pool)

    initialization_manifest = pkgutil.get_data(
        'buildhub',
        'initialization.yml'
    )
    config = yaml.safe_load(initialization_manifest)

    # Check that we push the records at the right place.
    if bucket not in config:
        raise ValueError(
            f"Bucket '{bucket}' not specified in `initialization.yml`."
        )
    if collection not in config[bucket]['collections']:
        raise ValueError(
            f"Collection '{collection}' not specified in `initialization.yml`."
        )

    await initialize_server(async_client,
                            config,
                            bucket=bucket,
                            collection=collection,
                            force=False)


# A regular expression corresponding to the date format in use in
# delivery-firefox paths.
DATE_RE = re.compile(r'\d{4}-\d{2}-\d{2}T\d{2}-\d{2}Z')


def ends_with_date(prefix):
    """Predicate to let us inspect prefixes such as:

    public/inventories/net-mozaws-prod-delivery-firefox/delivery-firefox/2017-07-01T03-09Z/

    while excluding those such as:

    public/inventories/net-mozaws-prod-delivery-firefox/delivery-firefox/hive/
    """
    parts = prefix.strip('/').split('/')
    return DATE_RE.match(parts[-1])


async def list_manifest_entries(loop, s3_client, inventory):
    """Fetch the latest S3 inventory manifest, and the keys of every
    *.csv.gz file it contains.

    :param loop: asyncio event loop.
    :param s3_client: Initialized S3 client.
    :param inventory str: Either "archive" or "firefox".
    """
    if STORE_DAILY_MANIFEST:
        today_utc = datetime.datetime.utcnow().strftime('%Y%m%d')
        manifest_content_file_path = f'.manifest-{today_utc}.json'

    if STORE_DAILY_MANIFEST and os.path.isfile(manifest_content_file_path):
        logger.info(f"Using stored manifest file {manifest_content_file_path}")
        with open(manifest_content_file_path) as f:
            manifest_content = json.load(f)
    else:
        prefix = FOLDER.format(inventory=inventory)
        paginator = s3_client.get_paginator('list_objects')
        manifest_folders = []
        async for result in paginator.paginate(
            Bucket=BUCKET,
            Prefix=prefix,
            Delimiter='/'
        ):
            # Take latest inventory.
            files = list(result.get('CommonPrefixes', []))
            prefixes = [f['Prefix'] for f in files]
            manifest_folders += [
                prefix for prefix in prefixes if ends_with_date(prefix)
            ]

        # Download latest manifest.json
        last_inventory = sorted(manifest_folders)[-1]
        logger.info('Latest inventory is {}'.format(last_inventory))
        key = last_inventory + 'manifest.json'
        manifest = await s3_client.get_object(Bucket=BUCKET, Key=key)
        async with manifest['Body'] as stream:
            body = await stream.read()
        manifest_content = json.loads(body.decode('utf-8'))
        if STORE_DAILY_MANIFEST:
            logger.info(
                f"Writing stored manifest file {manifest_content_file_path}"
            )
            with open(manifest_content_file_path, 'w') as f:
                json.dump(manifest_content, f, indent=3)
    for f in manifest_content['files']:
        # Here, each 'f' is a dictionary that looks something like this:
        #
        #  {
        #     "key" : "inventories/net-mozaw...f-b1a0-5fb25bb83752.csv.gz",
        #     "size" : 7945521,
        #     "MD5checksum" : "7454b0d773000f790f15b867ee152049"
        #  }
        #
        # We yield the whole thing. The key is used to download from S3.
        # The MD5checksum is used to know how to store the file on
        # disk for caching.
        yield f


async def download_csv(
    loop,
    s3_client,
    files_stream,
    chunk_size=CHUNK_SIZE,
    download_directory=CSV_DOWNLOAD_DIRECTORY,
):
    """
    Download the S3 object of each key and return deflated data chunks (CSV).
    :param loop: asyncio event loop.
    :param s3_client: Initialized S3 client.
    :param keys_stream async generator: List of object keys for
    the csv.gz manifests.
    """

    # Make sure the directory exists if it wasn't already created.
    if not os.path.isdir(download_directory):
        os.makedirs(download_directory, exist_ok=True)

    # Look for old download junk in the download directory.
    too_old = MAX_CSV_DOWNLOAD_AGE
    for file_path in glob.glob(os.path.join(download_directory, '*.csv.gz')):
        age = time.time() - os.stat(file_path).st_mtime
        if age > too_old:
            logger.info(
                f'Delete old download file {file_path} '
                f'({age} seconds old)'
            )
            os.remove(file_path)

    async for files in files_stream:
        # If it doesn't exist on disk, download to disk.
        file_path = os.path.join(
            download_directory,
            files['MD5checksum'] + '.csv.gz'
        )
        # The file neither exists or has data.
        if os.path.isfile(file_path) and os.stat(file_path).st_size:
            logger.debug(f'{file_path} was already downloaded locally')
        else:
            key = 'public/' + files['key']
            logger.info('Fetching inventory piece {}'.format(key))
            file_csv_gz = await s3_client.get_object(Bucket=BUCKET, Key=key)
            try:
                async with aiofiles.open(file_path, 'wb') as destination:
                    async with file_csv_gz['Body'] as source:
                        while 'there are chunks to read':
                            gzip_chunk = await source.read(chunk_size)
                            if not gzip_chunk:
                                break  # End of response.
                            await destination.write(gzip_chunk)
                size = os.stat(file_path).st_size
                logger.info(f'Downloaded {key} to {file_path} ({size} bytes)')
            except ClientPayloadError:
                if os.path.exists(file_path):
                    os.remove(file_path)
                raise

        # Now we expect the file to exist locally. Let's read it.
        gzip = zlib.decompressobj(zlib.MAX_WBITS | 16)
        async with aiofiles.open(file_path, 'rb') as stream:
            while 'there are chunks to read':
                gzip_chunk = await stream.read(chunk_size)
                if not gzip_chunk:
                    break  # End of response.
                csv_chunk = gzip.decompress(gzip_chunk)
                if csv_chunk:
                    # If the received doesn't have enough data to complete
                    # at least one block, the decompressor returns an
                    # empty string.
                    # A later chunk added to the compressor will then
                    # complete the block, it'll be decompressed and we
                    # get data then.
                    # Thanks Martijn Pieters http://bit.ly/2vbgQ3x
                    yield csv_chunk


async def main(loop, inventories=INVENTORIES):
    """
    Trigger to populate kinto with the last inventories.
    """
    server_url = config('SERVER_URL', default='http://localhost:8888/v1')
    bucket = config('BUCKET', default='build-hub')
    collection = config('COLLECTION', default='releases')
    kinto_auth = tuple(config('AUTH', default='user:pass').split(':'))

    kinto_client = kinto_http.Client(server_url=server_url, auth=kinto_auth,
                                     bucket=bucket, collection=collection,
                                     retry=NB_RETRY_REQUEST)

    # Create bucket/collection and schemas.
    if INITIALIZE_SERVER:
        await initialize_kinto(loop, kinto_client, bucket, collection)

    min_last_modified = None
    # Convert the simple env var integer to a datetime.datetime instance.
    if MIN_AGE_LAST_MODIFIED_HOURS:
        assert MIN_AGE_LAST_MODIFIED_HOURS > 0, MIN_AGE_LAST_MODIFIED_HOURS
        min_last_modified = datetime.datetime.utcnow() - datetime.timedelta(
            hours=MIN_AGE_LAST_MODIFIED_HOURS
        )
        # Make it timezone aware (to UTC)
        min_last_modified = min_last_modified.replace(
            tzinfo=datetime.timezone.utc
        )

    # Fetch all existing records as a big dict from kinto
    existing = fetch_existing(kinto_client)

    # Download CSVs, deduce records and push to Kinto.
    session = aiobotocore.get_session(loop=loop)
    boto_config = botocore.config.Config(signature_version=botocore.UNSIGNED)
    async with session.create_client(
        's3', region_name=REGION_NAME, config=boto_config
    ) as client:
        for inventory in inventories:
            files_stream = list_manifest_entries(loop, client, inventory)
            csv_stream = download_csv(loop, client, files_stream)
            records_stream = csv_to_records(
                loop,
                csv_stream,
                skip_incomplete=True,
                min_last_modified=min_last_modified,
            )
            await to_kinto_main(
                loop,
                records_stream,
                kinto_client,
                existing=existing,
                skip_existing=False
            )


@metrics.timer_decorator('s3_inventory_to_kinto_run')
def run():
    # Log everything to stderr.
    logger.addHandler(logging.StreamHandler())
    if LOG_LEVEL.lower() == 'debug':
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    # Add Sentry (no-op if no configured).
    handler = SentryHandler(sentry)
    handler.setLevel(logging.ERROR)
    logger.addHandler(handler)

    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main(loop))
    except Exception:
        logger.exception('Aborted.')
        raise
    finally:
        loop.close()
