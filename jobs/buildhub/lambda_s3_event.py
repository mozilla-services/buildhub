import aiohttp
import datetime
import json
import logging
import os
from io import BytesIO
from collections import namedtuple
from urllib.parse import urlparse

import kinto_http

from . import utils
from .inventory_to_records import fetch_listing, fetch_json


def fetch_release_metadata(record):
    return None
    # product = record["source"]["product"]
    # version = record["target"]["version"]

    # builds_url = archive_url(product, version, candidate="/")
    # build_folders = await fetch_listing(session, builds_url)
    # latest_build_folder = "/" + sorted(build_folders)[-1]
    # url = archive_url(product, version, platform, locale, candidate=latest_build_folder)
    # _, files = await fetch_listing(session, url)
    # for f in files:
    #     filename = f["name"]
    #     if utils.is_release_build_metadata(product, version, filename):
    #         metadata = await fetch_json(session, url + filename)
    #         return metadata
    # raise


def lambda_handler(event, context):
    server_url = "http://localhost:8888/v1"
    kinto_auth = ("user", "pass")
    kinto_client = kinto_http.Client(server_url=server_url, auth=kinto_auth)
    bucket = "build-hub"
    collection = "releases"

    version = "55.0a1"
    filename = "toto.exe"

    logging.basicConfig()
    logger = logging.getLogger(__name__)

    event_time = datetime.datetime.strptime(event['eventTime'],
                                            "%Y-%m-%dT%H:%M:%S.%fZ")
    event_time = event_time.strftime(utils.DATETIME_FORMAT)

    # http://docs.aws.amazon.com/AmazonS3/latest/dev/notification-content-structure.html
    for record in event['Records']:
        key = record['s3']['object']['key']
        filesize = record['s3']['object']['size']
        url = utils.ARCHIVE_URL + key


        try:
            product = key.split('/')[1]  # /pub/thunderbird/nightly/...
        except IndexError:
            continue  # e.g. https://archive.mozilla.org/favicon.ico

        if product not in utils.PRODUCTS:
            logger.warning('Skip product {}'.format(product))
            continue

        logger.info('Processing {} item: {}'.format(product, key))

        # If Release metadata.
        if utils.is_release_build_metadata(product, version, filename):
            logger.info('Release metadata found {}'.format(key))
            # XXX: Find corresponding release files (e.g every platforms/locales/...)

        # elif RC metadata
        # elif Nightly metadata
        # elif Nightly archive
        # elif RC archive
        # elif Release archive
        elif utils.is_build_url(product, url):
            record = utils.record_from_url(url)
            record["download"]["size"] = filesize
            record["download"]["date"] = event_time

            # Fetch release metadata.
            try:
                metadata = fetch_release_metadata(record)
            except ValueError as e:
                # If JSON metadata not available, archive will be handled when JSON
                # is delivered.
                logger.warning('JSON metadata not available {}'.format(record["id"]))
                continue
            # Merge obtained metadata.
            record = utils.merge_metadata(record, metadata)
            # Push result to Kinto.
            kinto_client.create_record(data=record,
                                       bucket=bucket,
                                       collection=collection,
                                       if_not_exists=True)
            logger.info('Created {}'.format(record["id"]))

        else:
            logger.warning('Ignored {}'.format(key))
