import asyncio
import async_timeout
import concurrent.futures
import datetime
import logging
import sys
import re
from os.path import basename

import aiohttp
import backoff
from kinto_http import cli_utils
from kinto_http.exceptions import KintoException
from .utils import is_release_filename
from .index_filters import build_version_id
from.scrape_archives import (
    archive, fetch_release_metadata, fetch_nightly_metadata, parse_nightly_filename
)

ARCHIVE_URL = "https://archive.mozilla.org/pub/"
PRODUCTS = ("fennec", "firefox", "thunderbird")
DEFAULT_SERVER = "https://kinto-ota.dev.mozaws.net/v1"
DEFAULT_BUCKET = "build-hub"
DEFAULT_COLLECTION = "archives"
NB_THREADS = 3
NB_RETRY_REQUEST = 3
TIMEOUT_SECONDS = 5 * 60
today = datetime.date.today()

logger = logging.getLogger(__name__)


def build_record_id(url):
    # Generate an ID that looks like that: firefox_53.0b9_linux-i686_en-US
    parts = basename(url.replace(' ', '-').lower()).split('.')
    url_parts = url.split('/')

    try:
        product_name, major_version = parts[0].replace('-setup', '').split('-')
    except Exception:
        return None
    channel = 'release'

    # Nightly URL
    # https://archive.mozilla.org/pub/firefox/nightly/2017/05/
    # 2017-05-15-10-02-38-mozilla-central/firefox-55.0a1.en-US.linux-x86_64.tar.bz2
    if 'nightly' in url:
        build_date = '-'.join(url_parts[8].split('-')[:6])
        version_number = '{}.{}'.format(major_version, parts[1])
        locale = parts[2]
        arch = parts[3]
        if 'android-api' in url_parts[8]:
            arch = '-'.join(url_parts[8].split('-')[8:11])
        if 'aurora' in url:
            channel = 'aurora'
            version = version_number
        else:
            channel = 'nightly'
            version = '{}_{}'.format(build_date, version_number)
    # Candidates URL
    # https://archive.mozilla.org/pub/firefox/candidates/50.0-candidates/build1/
    # linux-x86_64/fr/firefox-50.0.tar.bz2
    elif 'candidates' in url:
        candidate_number = url_parts[7].strip('build')
        version = '{}.{}rc{}'.format(major_version, parts[1], candidate_number)
        locale = url_parts[9]
        arch = url_parts[8]
    # Beta, Release or ESR URL
    # https://archive.mozilla.org/pub/firefox/releases/52.0b6/linux-x86_64/en-US/
    # firefox-52.0b6.tar.bz2
    else:
        version = url_parts[6]
        locale = url_parts[8]
        arch = url_parts[7]
        if 'b' in version:
            channel = 'beta'

    if 'old-id' in url:
        channel += "-old-id"

    channel = channel + "_" if channel != "release" else ""

    if arch == 'mac':
        arch = 'macosx'

    return '{}_{}{}_{}_{}'.format(
        product_name, channel, version, arch, locale).replace('.', '-').lower()


def archive_url(product, version=None, platform=None, locale=None, nightly=None, candidate=None):
    product = product if product != "fennec" else "mobile"

    url = ARCHIVE_URL + product
    if nightly:
        url += "/nightly/" + nightly + "/"
    elif candidate:
        url += "/candidates"
        if version:
            url += "/{}-candidates".format(version)
        url += candidate
        if platform:
            url += platform + "/"
        if locale:
            url += locale + "/"
    else:
        url += "/releases/"
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
async def fetch_json(loop, session, url):
    headers = {
        "Accept": "application/json",
        "User-Agent": "BuildHub;storage-team@mozilla.com"
    }
    try:
        with async_timeout.timeout(TIMEOUT_SECONDS):
            async with session.get(url, headers=headers, timeout=None) as response:
                return await response.json()
    except (asyncio.TimeoutError, aiohttp.ClientConnectionError):
        # Retry with a fresh session
        async with aiohttp.ClientSession(loop=loop) as session:
            return await fetch_json(loop, session, url)


async def fetch_listing(loop, session, url):
    try:
        data = await fetch_json(loop, session, url)
        return data["prefixes"], data["files"]
    except (aiohttp.ClientError, KeyError, ValueError) as e:
        raise ValueError("Could not fetch {}: {}".format(url, e))


async def fetch_nightlies(loop, session, queue, product, client):
    # Check latest known version on server.
    latest_nightly_folder = ""

    current_month = "{}/{:02d}".format(today.year, today.month)
    month_url = archive_url(product, nightly=current_month)
    days_folders, _ = await fetch_listing(loop, session, month_url)

    # Skip aurora nightlies and known nightlies...
    days_urls = [archive_url(product, nightly=current_month + "/" + f[:-1])
                 for f in days_folders if f > latest_nightly_folder]
    days_urls = [url for url in days_urls if "mozilla-central" in url]

    futures = [fetch_listing(loop, session, day_url) for day_url in days_urls]
    listings = await asyncio.gather(*futures)

    batch_size = 10  # Add URL in the consumer queue 10 by 10

    for day_url, (_, files) in zip(days_urls, listings):
        nb_batches = (len(files) // batch_size) + 1
        for i in range(nb_batches):
            files_subset = files[(i * batch_size):((i + 1) * batch_size)]

            # Fetch metadata in batch.
            futures = [fetch_nightly_metadata(session, day_url + file_["name"])
                       for file_ in files_subset]
            metadatas = await asyncio.gather(*futures)

            futures = []
            for file_, metadata in zip(files_subset, metadatas):
                url = day_url + file_['name']
                filename = file_["name"]
                size = file_["size"]
                date = file_["last_modified"]
                try:
                    version, locale, platform = parse_nightly_filename(filename)
                except ValueError:
                    continue
                if not is_release_filename(product, file_['name']):
                    print('Skipping', url)
                    continue
                record = archive(product, version, platform, locale, url,
                                 size, date, metadata)
                futures.append(queue.put(record))
            await asyncio.gather(*futures)


async def fetch_versions(loop, session, queue, product, client):
    product_url = archive_url(product)
    versions_folders, _ = await fetch_listing(loop, session, product_url)

    versions = [v[:-1] for v in versions_folders if re.match(r'^[0-9]', v)]
    versions = [v for v in versions if "funnelcake" not in v]
    # Scrape only unknown recent versions.
    versions = sorted(versions, key=lambda v: build_version_id(v.replace('-real', '')),
                      reverse=True)

    futures = [fetch_platforms(loop, session, queue, product, version)
               for version in versions]
    return await asyncio.gather(*futures)


async def fetch_platforms(loop, session, queue, product, version):
    version_url = archive_url(product, version)
    platform_folders, _ = await fetch_listing(loop, session, version_url)

    platforms = [p[:-1] for p in platform_folders]  # strip trailing /
    platforms = [p for p in platforms if p not in ("source", "update", "contrib")]

    futures = [fetch_locales(loop, session, queue, product, version, platform)
               for platform in platforms]
    return await asyncio.gather(*futures)


async def fetch_locales(loop, session, queue, product, version, platform):
    platform_url = archive_url(product, version, platform)
    locale_folders, _ = await fetch_listing(loop, session, platform_url)

    locales = [l[:-1] for l in locale_folders]
    locales = [l for l in locales if l != "xpi"]

    futures = [fetch_files(loop, session, queue, product, version, platform, locale)
               for locale in locales]
    return await asyncio.gather(*futures)


async def fetch_files(loop, session, queue, product, version, platform, locale):
    locale_url = archive_url(product, version, platform, locale)
    _, files = await fetch_listing(loop, session, locale_url)

    futures = []
    for file_ in files:
        filename = file_["name"]
        url = locale_url + filename

        if not is_release_filename(product, filename):
            print('Skipping', url)
            continue

        size = file_["size"]
        date = file_["last_modified"]

        metadata = await fetch_release_metadata(session, product, version, platform, locale)
        record = archive(product, version, platform, locale, url, size, date, metadata)
        logger.debug("Release found {}".format(url))

        futures.append(queue.put(record))

    return await asyncio.gather(*futures)


async def fetch_products(loop, session, queue, products, client):
    # Nightlies
    # futures = [fetch_nightlies(loop, session, queue, product, client) for product in products]
    # await asyncio.gather(*futures)
    # Releases
    futures = [fetch_versions(loop, session, queue, product, client) for product in products]
    await asyncio.gather(*futures)


async def produce(loop, queue, client):
    """Grab releases from the archives website."""
    async with aiohttp.ClientSession(loop=loop) as session:
        await fetch_products(loop, session, queue, PRODUCTS, client)
    logger.info("Scraping releases done.")


async def consume(loop, queue, executor, client, records_ids):
    """Store grabbed releases from the archives website in Kinto."""

    # Check for 200 or 404 on the release name
    print("Start consumer.")

    while True:
        record = await queue.get()
        release_url = record['download']['url']
        release_id = build_record_id(release_url)
        if release_id is None:
            print('Skipping', release_url)
            continue
        if release_id in records_ids:
            status = 'OK'
        else:
            status = 'MISSING'
            client.create_record(data=record)
        print(status, release_id, '\t', release_url)

        queue.task_done()


async def main(loop):
    parser = cli_utils.add_parser_options(
        description="Send releases archives to Kinto",
        default_server=DEFAULT_SERVER,
        default_bucket=DEFAULT_BUCKET,
        default_retry=NB_RETRY_REQUEST,
        default_collection=DEFAULT_COLLECTION)

    args = parser.parse_args(sys.argv[1:])

    cli_utils.setup_logger(logger, args)

    logger.info("Validate collection at {server}/buckets/{bucket}/collections/{collection}"
                .format(**args.__dict__))

    client = cli_utils.create_client_from_args(args)

    # Fetch the list of known records ids.
    records = client.get_records(pages=float("inf"))
    records_ids = set([r['id'] for r in records])
    print("{} existing records found.".format(len(records_ids)))

    # Start a producer and a consumer with threaded kinto requests.
    queue = asyncio.Queue()
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=NB_THREADS)
    # Schedule the consumer
    consumer_coro = consume(loop, queue, executor, client, records_ids)
    consumer = asyncio.ensure_future(consumer_coro)
    # Run the producer and wait for completion
    await produce(loop, queue, client)
    # Wait until the consumer is done consuming everything.
    await queue.join()
    # The consumer is still awaiting for the producer, cancel it.
    consumer.cancel()


def run():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(loop))
    loop.close()


if __name__ == "__main__":
    run()
