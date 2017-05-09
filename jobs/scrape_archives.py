import asyncio
import concurrent.futures
import json
import logging
import re
import sys
from packaging.version import parse as version_parse

import aiohttp
import kinto_http.exceptions
from kinto_http import cli_utils


ARCHIVE_URL = "https://archive.mozilla.org/pub/"
PRODUCTS = ("firefox", "thunderbird")
DEFAULT_SERVER = "https://kinto-ota.dev.mozaws.net/v1"
DEFAULT_BUCKET = "build-hub"
DEFAULT_COLLECTION = "archives"
NB_THREADS = 5


logger = logging.getLogger(__name__)


def publish_records(client, records):
    try:
        with client.batch() as batch:
            for record in records:
                batch.create_record(record, safe=False)
        logger.info("Created %s records" % len(records))
    except kinto_http.exceptions.KintoException:
        logger.exception("Could not create records")


def archive_url(product, version=None, platform=None, locale=None):
    url = ARCHIVE_URL + product + "/releases/"
    if version:
        url += version + "/"
    if platform:
        url += platform + "/"
    if locale:
        url += locale + "/"
    return url


async def fetch_listing(session, url):
    headers = {
        "Accept": "application/json",
        "User-Agent": "BuildHub;storage-team@mozilla.com"
    }
    async with session.get(url, headers=headers) as response:
        try:
            data = await response.json()
            return data["prefixes"], data["files"]
        except (aiohttp.ClientError, KeyError) as e:
            raise ValueError("Could not fetch %s: %s" % (url, e))


async def fetch_products(session, queue, products):
    futures = [fetch_versions(session, queue, product) for product in products]
    return await asyncio.gather(*futures)


async def fetch_versions(session, queue, product):
    product_url = archive_url(product)
    versions_folders, _ = await fetch_listing(session, product_url)

    versions = [v[:-1] for v in versions_folders if re.match(r'^[0-9]', v)]
    versions = [v for v in versions if "funnelcake" not in v]
    versions = sorted(versions, key=lambda v: version_parse(v), reverse=True)

    futures = [fetch_platforms(session, queue, product, version)
               for version in versions]
    return await asyncio.gather(*futures)


async def fetch_platforms(session, queue, product, version):
    version_url = archive_url(product, version)
    platform_folders, _ = await fetch_listing(session, version_url)

    platforms = [p[:-1] for p in platform_folders]  # strip trailing /
    platforms = [p for p in platforms if p not in ("source", "update")]

    futures = [fetch_locales(session, queue, product, version, platform)
               for platform in platforms]
    return await asyncio.gather(*futures)


async def fetch_locales(session, queue, product, version, platform):
    platform_url = archive_url(product, version, platform)
    locale_folders, _ = await fetch_listing(session, platform_url)

    locales = [l[:-1] for l in locale_folders]
    locales = [l for l in locales if l != "xpi"]

    futures = [fetch_files(session, queue, product, version, platform, locale)
               for locale in locales]
    return await asyncio.gather(*futures)


async def fetch_files(session, queue, product, version, platform, locale):
    locale_url = archive_url(product, version, platform, locale)
    _, files = await fetch_listing(session, locale_url)

    fileregexp = re.compile("%s-(.+)(zip|gz|bz|bz2|dmg|apk)$" % product)
    files = [f for f in files if fileregexp.match(f["name"])]

    futures = []
    for file_ in files:
        filename = file_["name"]
        record = {
            "build": None,
            "source": {
                "revision": None,
                "tree": None,
                "product": product,
            },
            "target": {
                "platform": platform,
                "locale": locale,
                "version": version,
                "channel": None,
            },
            "download": {
                "url": locale_url + filename,
                "mimetype": None,
                "size": None,
            },
            "systemaddons": None
        }
        logger.debug("Release found %s" % record["download"]["url"])
        futures.append(queue.put(record))

    return await asyncio.gather(*futures)


async def produce(loop, queue):
    """Grab releases from the archives website."""
    async with aiohttp.ClientSession(loop=loop) as session:
        await fetch_products(session, queue, PRODUCTS)
    logger.info("Scraping releases done.")


async def consume(loop, executor, client, queue):
    """Store grabbed releases from the archives website in Kinto."""
    info = client.server_info()
    batch_size = info["settings"]["batch_max_requests"]
    while True:
        records = [await queue.get()]
        while not queue.empty() and len(records) < batch_size:
            records.append(await queue.get())
        task = loop.run_in_executor(executor, publish_records, client, records)
        # Counting tasks done allows us to wait for the queue with queue.join()
        task.add_done_callback(lambda fut: queue.task_done())


def main():
    parser = cli_utils.add_parser_options(
        description="Send releases archives to Kinto",
        default_server=DEFAULT_SERVER,
        default_bucket=DEFAULT_BUCKET,
        default_collection=DEFAULT_COLLECTION)

    args = parser.parse_args(sys.argv[1:])

    cli_utils.setup_logger(logger, args)

    logger.info("Publish at {server}/buckets/{bucket}/collections/{collection}"
                .format(**args.__dict__))

    client = cli_utils.create_client_from_args(args)
    client.session.nb_retry = 3

    public_perms = {"read": ["system.Everyone"]}
    client.create_bucket(permissions=public_perms, if_not_exists=True)
    client.create_collection(if_not_exists=True)

    loop = asyncio.get_event_loop()
    queue = asyncio.Queue(loop=loop)

    executor = concurrent.futures.ThreadPoolExecutor(max_workers=NB_THREADS)
    consumer_coro = consume(loop, executor, client, queue)
    consumer_task = asyncio.ensure_future(consumer_coro)

    # Wait for scraping of releases and all records to be published.
    producer = produce(loop, queue)
    wait_queue = queue.join()
    future = asyncio.gather(producer, wait_queue)
    try:
        loop.run_until_complete(future)
    finally:
        # Everything processed, stop consuming.
        consumer_task.cancel()
        loop.close()


if __name__ == "__main__":
    main()
