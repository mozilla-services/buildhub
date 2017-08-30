import asyncio
import json
import logging
import os.path
import zlib

import aiobotocore
import botocore
import kinto_http

from buildhub.inventory_to_records import NB_RETRY_REQUEST, csv_to_records
from buildhub.to_kinto import main as to_kinto


REGION_NAME = 'us-east-1'
BUCKET = 'net-mozaws-prod-delivery-inventory-us-east-1'
FOLDER = 'public/inventories/net-mozaws-prod-delivery-{inventory}/delivery-{inventory}/'
CHUNK_SIZE = 1024 * 256  # 256 KB


logger = logging.getLogger()  # root logger.


async def list_manifest_entries(loop, client, inventory):
    prefix = FOLDER.format(inventory=inventory)
    paginator = client.get_paginator('list_objects')

    manifest_folders = []
    async for result in paginator.paginate(Bucket=BUCKET, Prefix=prefix, Delimiter='/'):
        # Take latest inventory.
        files = list(result.get('CommonPrefixes', []))
        manifest_folders += [f['Prefix'] for f in files]

    # Download latest manifest.json
    last_inventory = sorted(manifest_folders)[-2]  # -1 is data
    logger.info('Latest inventory is {}'.format(last_inventory))
    key = last_inventory + 'manifest.json'
    manifest = await client.get_object(Bucket=BUCKET, Key=key)
    async with manifest['Body'] as stream:
        body = await stream.read()
    manifest_content = json.loads(body.decode('utf-8'))
    # Return keys of csv.gz files
    for f in manifest_content['files']:
        yield f['key']


async def download_csv(loop, client, keys_stream, chunk_size=CHUNK_SIZE):

    async for key in keys_stream:
        key = 'public/' + key
        logger.info('Fetching inventory piece {}'.format(key))
        file_csv_gz = await client.get_object(Bucket=BUCKET, Key=key)
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

    session = aiobotocore.get_session(loop=loop)
    boto_config = botocore.config.Config(signature_version=botocore.UNSIGNED)
    async with session.create_client('s3', region_name=REGION_NAME, config=boto_config) as client:
        keys_stream = list_manifest_entries(loop, client, inventory)
        csv_stream = download_csv(loop, client, keys_stream)
        records_stream = csv_to_records(loop, csv_stream)
        await to_kinto(loop, records_stream, kinto_client, skip_existing=True)


def lambda_handler(event=None, context=None):
    # Log everything to stderr.
    logger.addHandler(logging.StreamHandler())
    logger.setLevel(logging.DEBUG)

    loop = asyncio.get_event_loop()
    futures = [main(loop, inventory) for inventory in ('firefox', 'archive')]
    loop.run_until_complete(asyncio.gather(*futures))
    loop.close()
