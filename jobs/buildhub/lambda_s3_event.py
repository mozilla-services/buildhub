import asyncio
import datetime
import logging
import os
import re

import aiohttp
import kinto_http
import raven
from raven.handlers.logging import SentryHandler

from buildhub import utils
from buildhub.inventory_to_records import (
    NB_RETRY_REQUEST, fetch_json, fetch_listing, fetch_metadata, scan_candidates)


# Optional Sentry with synchronuous client.
SENTRY_DSN = os.getenv('SENTRY_DSN')
sentry = raven.Client(SENTRY_DSN, transport=raven.transport.http.HTTPTransport)

logger = logging.getLogger()  # root logger.


async def main(loop, event):
    """
    Trigger when S3 event kicks in.
    http://docs.aws.amazon.com/AmazonS3/latest/dev/notification-content-structure.html
    """
    server_url = os.getenv('SERVER_URL', 'http://localhost:8888/v1')
    bucket = os.getenv('BUCKET', 'build-hub')
    collection = os.getenv('COLLECTION', 'releases')
    kinto_auth = tuple(os.getenv('AUTH', 'user:pass').split(':'))

    kinto_client = kinto_http.Client(server_url=server_url, auth=kinto_auth,
                                     retry=NB_RETRY_REQUEST)

    async with aiohttp.ClientSession(loop=loop) as session:
        for event_record in event['Records']:
            records_to_create = []

            # Use event time as archive publication.
            event_time = datetime.datetime.strptime(event_record['eventTime'],
                                                    '%Y-%m-%dT%H:%M:%S.%fZ')
            event_time = event_time.strftime(utils.DATETIME_FORMAT)

            key = event_record['s3']['object']['key']
            filesize = event_record['s3']['object']['size']
            url = utils.ARCHIVE_URL + key

            try:
                product = key.split('/')[1]  # /pub/thunderbird/nightly/...
            except IndexError:
                continue  # e.g. https://archive.mozilla.org/favicon.ico

            if product not in utils.ALL_PRODUCTS:
                logger.info('Skip product {}'.format(product))
                continue

            # Release / Nightly / RC archive.
            if utils.is_build_url(product, url):
                logger.info('Processing {} archive: {}'.format(product, key))

                record = utils.record_from_url(url)
                # Use S3 event infos for the archive.
                record['download']['size'] = filesize
                record['download']['date'] = event_time

                # Fetch release metadata.
                await scan_candidates(session, product)
                metadata = await fetch_metadata(session, record)
                # If JSON metadata not available, archive will be handled when JSON
                # is delivered.
                if metadata is None:
                    logger.info('JSON metadata not available {}'.format(record['id']))
                    continue

                # Merge obtained metadata.
                record = utils.merge_metadata(record, metadata)
                records_to_create.append(record)

            # RC metadata
            elif utils.is_rc_build_metadata(product, url):
                logger.info('Processing {} RC metadata: {}'.format(product, key))

                # pub/firefox/candidates/55.0b12-candidates/build1/mac/en-US/
                # firefox-55.0b12.json
                metadata = await fetch_json(session, url)
                metadata['buildnumber'] = int(re.search('/build(\d+)/', url).group(1))

                # Check if localized languages are here (including en-US archive).
                l10n_parent_url = re.sub('en-US/.+$', '', url)
                l10n_folders, _ = await fetch_listing(session, l10n_parent_url)
                for locale in l10n_folders:
                    _, files = await fetch_listing(session, l10n_parent_url + locale)
                    for f in files:
                        rc_url = l10n_parent_url + locale + f['name']
                        if utils.is_build_url(product, rc_url):
                            record = utils.record_from_url(rc_url)
                            record['download']['size'] = f['size']
                            record['download']['date'] = f['last_modified']
                            record = utils.merge_metadata(record, metadata)
                            records_to_create.append(record)
                # Theorically release should never be there yet :)
                # And repacks like EME-free/sha1 don't seem to be published in RC.

            # Nightly metadata
            # pub/firefox/nightly/2017/08/2017-08-08-11-40-32-mozilla-central/
            # firefox-57.0a1.en-US.linux-i686.json
            # -l10n/...
            elif utils.is_nightly_build_metadata(product, url):
                logger.info('Processing {} nightly metadata: {}'.format(product, key))

                metadata = await fetch_json(session, url)

                platform = metadata['moz_pkg_platform']

                # Check if english version is here.
                parent_url = re.sub('/[^/]+$', '/', url)
                _, files = await fetch_listing(session, parent_url)
                for f in files:
                    if ('.' + platform + '.') not in f['name']:
                        # metadata are by platform.
                        continue
                    en_nightly_url = parent_url + f['name']
                    if utils.is_build_url(product, en_nightly_url):
                        record = utils.record_from_url(en_nightly_url)
                        record['download']['size'] = f['size']
                        record['download']['date'] = f['last_modified']
                        record = utils.merge_metadata(record, metadata)
                        records_to_create.append(record)
                        break  # Only one file for english.

                # Check also localized versions.
                l10n_folder_url = re.sub('-mozilla-central([^/]*)/([^/]+)$',
                                         '-mozilla-central\\1-l10n/',
                                         url)
                try:
                    _, files = await fetch_listing(session, l10n_folder_url)
                except ValueError:
                    files = []  # No -l10/ folder published yet.
                for f in files:
                    if ('.' + platform + '.') not in f['name'] and product != 'mobile':
                        # metadata are by platform.
                        # (mobile platforms are contained by folder)
                        continue
                    nightly_url = l10n_folder_url + f['name']
                    if utils.is_build_url(product, nightly_url):
                        record = utils.record_from_url(nightly_url)
                        record['download']['size'] = f['size']
                        record['download']['date'] = f['last_modified']
                        record = utils.merge_metadata(record, metadata)
                        records_to_create.append(record)

            else:
                logger.info('Ignored {}'.format(key))

            for record in records_to_create:
                # Check that fields values look OK.
                utils.check_record(record)
                # Push result to Kinto.
                kinto_client.create_record(data=record,
                                           bucket=bucket,
                                           collection=collection,
                                           if_not_exists=True)
                logger.info('Created {}'.format(record['id']))


def lambda_handler(event, context):
    # Log everything to stderr.
    logger.addHandler(logging.StreamHandler(stream=sys.stdout))
    logger.setLevel(logging.DEBUG)

    # Add Sentry (no-op if no configured).
    handler = SentryHandler(sentry)
    handler.setLevel(logging.ERROR)
    logger.addHandler(handler)

    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main(loop, event))
    except:
        logger.exception('Aborted.')
        raise
    finally:
        loop.close()
