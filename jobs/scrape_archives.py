import asyncio
import async_timeout
import concurrent.futures
import json
import logging
import re
import sys
from packaging.version import parse as version_parse

import aiohttp
import backoff
import kinto_http.exceptions
from kinto_http import cli_utils


ARCHIVE_URL = "https://archive.mozilla.org/pub/"
PRODUCTS = ("firefox", "thunderbird")
DEFAULT_SERVER = "https://kinto-ota.dev.mozaws.net/v1"
DEFAULT_BUCKET = "build-hub"
DEFAULT_COLLECTION = "archives"
NB_THREADS = 3
NB_RETRY_REQUEST = 3
TIMEOUT_SECONDS = 5 * 60


logger = logging.getLogger(__name__)


def publish_records(client, records):
    with client.batch() as batch:
        for record in records:
            batch.create_record(record)
    logger.info("Created %s records" % len(records))


def archive_url(product, version=None, platform=None, locale=None):
    url = ARCHIVE_URL + product + "/releases/"
    if version:
        url += version + "/"
    if platform:
        url += platform + "/"
    if locale:
        url += locale + "/"
    return url


@backoff.on_exception(backoff.expo,
                      asyncio.TimeoutError,
                      max_tries=NB_RETRY_REQUEST)
async def fetch_listing(session, url):
    headers = {
        "Accept": "application/json",
        "User-Agent": "BuildHub;storage-team@mozilla.com"
    }
    with async_timeout.timeout(TIMEOUT_SECONDS):
        async with session.get(url, headers=headers, timeout=None) as response:
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
    platforms = [p for p in platforms if p not in ("source", "update", "contrib")]

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
    files = [f for f in files if fileregexp.match(f["name"]) and 'sdk' not in f["name"]]

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


async def consume(loop, queue, executor, client):
    """Store grabbed releases from the archives website in Kinto."""

    def markdone(queue, n):
        """Returns a callback that will mark `n` queue items done."""
        return lambda fut: [queue.task_done() for _ in range(n)]

    info = client.server_info()
    batch_size = info["settings"]["batch_max_requests"]
    while True:
        # Consume records from queue, and batch operations.
        # But don't block if there's not enough records to fill a batch.
        batch = []
        try:
            with async_timeout.timeout(2):
                while len(batch) < batch_size:
                    record = await queue.get()
                    batch.append(record)
        except asyncio.TimeoutError:
            logger.debug("Scraping done or not fast enough, proceed.")
            pass

        if batch:
            task = loop.run_in_executor(executor, publish_records, client, batch)
            task.add_done_callback(markdone(queue, len(batch)))


async def main(loop):
    parser = cli_utils.add_parser_options(
        description="Send releases archives to Kinto",
        default_server=DEFAULT_SERVER,
        default_bucket=DEFAULT_BUCKET,
        default_retry=NB_RETRY_REQUEST,
        default_collection=DEFAULT_COLLECTION)

    args = parser.parse_args(sys.argv[1:])

    cli_utils.setup_logger(logger, args)

    logger.info("Publish at {server}/buckets/{bucket}/collections/{collection}"
                .format(**args.__dict__))

    client = cli_utils.create_client_from_args(args)

    public_perms = {"read": ["system.Everyone"]}
    client.create_bucket(permissions=public_perms, if_not_exists=True)
    client.create_collection(if_not_exists=True)

    # Start a producer and a consumer with threaded kinto requests.
    queue = asyncio.Queue()
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=NB_THREADS)
    # Schedule the consumer
    consumer_coro = consume(loop, queue, executor, client)
    consumer = asyncio.ensure_future(consumer_coro)
    # Run the producer and wait for completion
    await produce(loop, queue)
    # Wait until the consumer is done consuming everything.
    await queue.join()
    # The consumer is still awaiting for the producer, cancel it.
    consumer.cancel()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(loop))
    loop.close()
