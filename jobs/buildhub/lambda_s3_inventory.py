import asyncio
import aiobotocore
import gzip
import json
import os.path
from io import BytesIO, StringIO

from buildhub.inventory_to_records import csv_to_records

BUCKET = "net-mozaws-prod-delivery-inventory-us-east-1"
FOLDER = "public/inventories/net-mozaws-prod-delivery-{inventory}/delivery-{inventory}/"


async def handle_file(loop, client, file_key):
    # 2. For each inventory file, convert it to records and populate Kinto
    gzipped_csv_file = await client.get_object(Bucket=BUCKET, Key=file_key)
    async with gzipped_csv_file['Body'] as stream:
        gzipped_body = await stream.read()
        gzip_fd = BytesIO(gzipped_body)
        with gzip.open(gzip_fd, 'rb') as csv_fd:
            json_fd = StringIO()
            await csv_to_records(loop, csv_fd, json_fd)
            print(json_fd.getvalue())


async def main(loop, event, inventory):
    """
    Trigger to populate kinto with the last inventories.
    """
    # 0. Get the last inventory date and download its manifest.json
    session = aiobotocore.get_session(loop=loop)
    async with session.create_client('s3', region_name='us-east-1') as client:
        paginator = client.get_paginator('list_objects')
        inventory_folder = FOLDER.format(inventory=inventory)
        async for result in paginator.paginate(Bucket=BUCKET, Prefix=inventory_folder,
                                               Delimiter='/'):
            files = list(result.get('CommonPrefixes', []))
            last_inventory = os.path.basename(files[-2]['Prefix'].strip('/'))  # -1 is data
            # Download manifest.json
            key = '{}{}/manifest.json'.format(inventory_folder, last_inventory)
            manifest = await client.get_object(Bucket=BUCKET, Key=key)
            async with manifest['Body'] as stream:
                body = await stream.read()
            manifest_content = json.loads(body.decode('utf-8'))
            print(manifest_content)
            files = [f['key'] for f in manifest_content['files']]

            # 1. Download Firefox and Archives inventories in S3
            for file_key in files:
                await handle_file(loop, client, file_key)
                break


def get_lambda_handler(inventory):
    def lambda_handler(event, context):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main(loop, event, inventory))
        loop.close()
    return lambda_handler

firefox_inventory_handler = get_lambda_handler("firefox")
archive_inventory_handler = get_lambda_handler("archive")
