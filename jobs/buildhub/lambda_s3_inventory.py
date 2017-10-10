import asyncio
import json
import logging
import os
import pkgutil
import zlib
from concurrent.futures import ThreadPoolExecutor

import aiobotocore
import botocore
import kinto_http
import raven
from raven.handlers.logging import SentryHandler
from ruamel import yaml
from kinto_wizard.async_kinto import AsyncKintoClient
from kinto_wizard.yaml2kinto import initialize_server

from buildhub.inventory_to_records import NB_RETRY_REQUEST, csv_to_records
from buildhub.to_kinto import main as to_kinto


REGION_NAME = 'us-east-1'
BUCKET = 'net-mozaws-prod-delivery-inventory-us-east-1'
FOLDER = 'public/inventories/net-mozaws-prod-delivery-{inventory}/delivery-{inventory}/'
CHUNK_SIZE = 1024 * 256  # 256 KB

INITIALIZE_SERVER = os.getenv('INITIALIZE_SERVER', 'true').lower() == 'true'

# Optional Sentry with synchronuous client.
SENTRY_DSN = os.getenv('SENTRY_DSN')
sentry = raven.Client(SENTRY_DSN, transport=raven.transport.http.HTTPTransport)

logger = logging.getLogger()  # root logger.


async def initialize_kinto(loop, kinto_client, bucket, collection):
    """
    Initialize the remote server with the initialization.yml file.
    """
    # Leverage kinto-wizard async client.
    thread_pool = ThreadPoolExecutor()
    async_client = AsyncKintoClient(kinto_client, loop, thread_pool)

    initialization_manifest = pkgutil.get_data('buildhub', 'initialization.yml')
    config = yaml.safe_load(initialization_manifest)

    # Check that we push the records at the right place.
    if bucket not in config:
        raise ValueError(f"Bucket '{bucket}' not specified in `initialization.yml`.")
    if collection not in config[bucket]['collections']:
        raise ValueError(f"Collection '{collection}' not specified in `initialization.yml`.")

    await initialize_server(async_client,
                            config,
                            bucket=bucket,
                            collection=collection,
                            force=False)


async def list_manifest_entries(loop, s3_client, inventory):
    """Fetch the latest S3 inventory manifest, and the keys of every
    *.csv.gz file it contains.

    :param loop: asyncio event loop.
    :param s3_client: Initialized S3 client.
    :param inventory str: Either "archive" or "firefox".
    """
    prefix = FOLDER.format(inventory=inventory)
    paginator = s3_client.get_paginator('list_objects')

    manifest_folders = []
    async for result in paginator.paginate(Bucket=BUCKET, Prefix=prefix, Delimiter='/'):
        # Take latest inventory.
        files = list(result.get('CommonPrefixes', []))
        manifest_folders += [f['Prefix'] for f in files]

    # Download latest manifest.json
    last_inventory = sorted(manifest_folders)[-2]  # -1 is data
    logger.info('Latest inventory is {}'.format(last_inventory))
    key = last_inventory + 'manifest.json'
    manifest = await s3_client.get_object(Bucket=BUCKET, Key=key)
    async with manifest['Body'] as stream:
        body = await stream.read()
    manifest_content = json.loads(body.decode('utf-8'))
    # Return keys of csv.gz files
    for f in manifest_content['files']:
        yield f['key']


async def download_csv(loop, s3_client, keys_stream, chunk_size=CHUNK_SIZE):
    """
    Download the S3 object of each key and return deflated data chunks (CSV).
    :param loop: asyncio event loop.
    :param s3_client: Initialized S3 client.
    :param keys_stream async generator: List of object keys for the csv.gz manifests.
    """
    async for key in keys_stream:
        key = 'public/' + key
        logger.info('Fetching inventory piece {}'.format(key))
        file_csv_gz = await s3_client.get_object(Bucket=BUCKET, Key=key)
        gzip = zlib.decompressobj(zlib.MAX_WBITS | 16)
        async with file_csv_gz['Body'] as stream:
            while 'there are chunks to read':
                gzip_chunk = await stream.read(chunk_size)
                if not gzip_chunk:
                    break  # End of response.
                csv_chunk = gzip.decompress(gzip_chunk)
                if csv_chunk:
                    # If the received doesn't have enough data to complete at least
                    # one block, the decompressor returns an empty string.
                    # A later chunk added to the compressor will then complete the block,
                    # it'll be decompressed and we get data then.
                    # Thanks Martijn Pieters http://bit.ly/2vbgQ3x
                    yield csv_chunk


async def main(loop, inventory):
    """
    Trigger to populate kinto with the last inventories.
    """
    server_url = os.getenv('SERVER_URL', 'http://localhost:8888/v1')
    bucket = os.getenv('BUCKET', 'build-hub')
    collection = os.getenv('COLLECTION', 'releases')
    kinto_auth = tuple(os.getenv('AUTH', 'user:pass').split(':'))

    kinto_client = kinto_http.Client(server_url=server_url, auth=kinto_auth,
                                     bucket=bucket, collection=collection,
                                     retry=NB_RETRY_REQUEST)

    # Create bucket/collection and schemas.
    if INITIALIZE_SERVER:
        await initialize_kinto(loop, kinto_client, bucket, collection)

    # Download CSVs, deduce records and push to Kinto.
    session = aiobotocore.get_session(loop=loop)
    boto_config = botocore.config.Config(signature_version=botocore.UNSIGNED)
    async with session.create_client('s3', region_name=REGION_NAME, config=boto_config) as client:
        keys_stream = list_manifest_entries(loop, client, inventory)
        csv_stream = download_csv(loop, client, keys_stream)
        records_stream = csv_to_records(loop, csv_stream, skip_incomplete=True)
        await to_kinto(loop, records_stream, kinto_client, skip_existing=True)


def lambda_handler(event=None, context=None):
    # Log everything to stderr.
    logger.addHandler(logging.StreamHandler())
    logger.setLevel(logging.DEBUG)

    # Add Sentry (no-op if no configured).
    handler = SentryHandler(sentry)
    handler.setLevel(logging.ERROR)
    logger.addHandler(handler)

    loop = asyncio.get_event_loop()
    futures = [main(loop, inventory) for inventory in ('firefox', 'archive')]
    try:
        loop.run_until_complete(asyncio.gather(*futures))
    except:
        logger.exception('Aborted.')
        raise
    finally:
        loop.close()
