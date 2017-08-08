import datetime
import os

import kinto_http

from . import utils
from .inventory_to_records import fetch_listing, fetch_json


def fetch_release_metadata(record):
    # XXX
    return None

    session = None  # loop
    product = record["source"]["product"]
    version = record["target"]["version"]
    platform = record["target"]["platform"]
    locale = record["target"]["locale"]

    builds_url = utils.archive_url(product, version, candidate="/")
    build_folders = fetch_listing(session, builds_url)
    latest_build_folder = "/" + sorted(build_folders)[-1]
    url = utils.archive_url(product, version, platform, locale, candidate=latest_build_folder)
    _, files = fetch_listing(session, url)
    for f in files:
        filename = f["name"]
        if utils.is_release_build_metadata(product, version, filename):
            metadata = fetch_json(session, url + filename)
            return metadata
    raise ValueError("")


def lambda_handler(event, context):
    server_url = os.getenv("SERVER_URL", "http://localhost:8888/v1")
    bucket = os.getenv("BUCKET", "build-hub")
    collection = os.getenv("COLLECTION", "releases")
    kinto_auth = tuple(os.getenv("AUTH", "user:pass").split(":"))

    kinto_client = kinto_http.Client(server_url=server_url, auth=kinto_auth)

    # Use event time as archive publication.
    event_time = datetime.datetime.strptime(event['eventTime'], "%Y-%m-%dT%H:%M:%S.%fZ")
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

        if product not in utils.ALL_PRODUCTS:
            print('Skip product {}'.format(product))
            continue

        print('Processing {} item: {}'.format(product, key))

        # Release / Nightly archive
        print(url, utils.is_build_url(product, url))
        if utils.is_build_url(product, url):
            record = utils.record_from_url(url)
            record["download"]["size"] = filesize
            record["download"]["date"] = event_time

            # Fetch release metadata.
            try:
                metadata = fetch_release_metadata(record)
            except ValueError as e:
                # If JSON metadata not available, archive will be handled when JSON
                # is delivered.
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
        # elif RC archive

        # If Release metadata.
        if utils.is_release_build_metadata(product, "55.0a1", "toto.exe"):
            print('Release metadata found {}'.format(key))
            # XXX: Find corresponding release files (e.g every platforms/locales/...)

        # elif RC metadata
        # elif Nightly metadata
        else:
            print('Ignored {}'.format(key))
