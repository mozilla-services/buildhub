import asyncio
import async_timeout
import concurrent.futures
import datetime
import logging
import re
import sys
from packaging.version import parse as version_parse

import aiohttp
import backoff
from buildhub.utils import (
    FILE_EXTENSIONS, build_record_id, parse_nightly_filename, is_release_metadata,
    is_release_filename, guess_mimetype, guess_channel
)
from kinto_http import cli_utils


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


def publish_records(client, records):
    with client.batch() as batch:
        for record in records:
            batch.create_record(data=record)
    results = batch.results()

    # Batch don't fail with 4XX errors. Make sure we output a comprehensive
    # error here when we encounter them.
    error_msgs = []
    for result in results:
        error_status = result.get("code")
        if error_status == 412:
            error_msg = ("Record '{details[existing][id]}' already exists: "
                         "{details[existing]}").format_map(result)
            error_msgs.append(error_msg)
        elif error_status == 400:
            error_msg = "Invalid record: {}".format(result)
            error_msgs.append(error_msg)
        elif error_status is not None:
            error_msgs.append("Error: {}".format(result))
    if error_msgs:
        raise ValueError("\n".join(error_msgs))

    logger.info("Created {} records".format(len(records)))


def latest_known_nightly_datetime(client, product):
    """Check latest known nightly on server in order to resume scraping.
    """
    filters = {
        "source.product": product,
        "target.channel": "nightly",
        "_sort": "-download.date",
        "_limit": 1,
        "pages": 1
    }
    existing = client.get_records(**filters)
    latest = None
    if existing:
        latest_nightly = existing[0]["download"]["date"]
        latest = datetime.datetime.strptime(latest_nightly, "%Y-%m-%dT%H:%M:%SZ")
    return latest


def latest_known_version(client, product):
    """Check latest known version on server in order to resume scraping.
    """
    filters = {
        "source.product": product,
        "target.channel": "beta",
        "_sort": "-download.date",
        "_limit": 1,
        "pages": 1
    }
    existing = client.get_records(**filters)
    latest_version = ""
    if existing:
        latest_version = existing[0]["target"]["version"]
    return latest_version


def archive(product, version, platform, locale, url, size, date, metadata=None):
    build = None
    revision = None
    tree = None

    channel = guess_channel(url, version)

    if metadata:
        # Example of metadata:
        #  https://archive.mozilla.org/pub/thunderbird/candidates \
        #  /50.0b1-candidates/build2/linux-i686/en-US/thunderbird-50.0b1.json
        revision = metadata["moz_source_stamp"]
        channel = metadata.get("moz_update_channel", channel)
        repository = metadata["moz_source_repo"].replace("MOZ_SOURCE_REPO=", "")
        tree = repository.split("hg.mozilla.org/", 1)[-1]
        buildid = metadata["buildid"]
        builddate = datetime.datetime.strptime(buildid[:12], "%Y%m%d%H%M").isoformat()
        build = {
            "id": buildid,
            "date": builddate,
        }

    record = {
        "build": build,
        "source": {
            "revision": revision,
            "repository": repository,
            "tree": tree,
            "product": product,
        },
        "target": {
            "platform": platform,
            "locale": locale,
            "version": version,
            "channel": channel,
        },
        "download": {
            "url": url,
            "mimetype": guess_mimetype(url),
            "size": size,
            "date": date,
        },
        "systemaddons": None
    }
    record['id'] = build_record_id(record)
    return record


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
async def fetch_json(session, url):
    headers = {
        "Accept": "application/json",
        "User-Agent": "BuildHub;storage-team@mozilla.com"
    }
    with async_timeout.timeout(TIMEOUT_SECONDS):
        async with session.get(url, headers=headers, timeout=None) as response:
            return await response.json()


async def fetch_listing(session, url):
    try:
        data = await fetch_json(session, url)
        return data["prefixes"], data["files"]
    except (aiohttp.ClientError, KeyError, ValueError) as e:
        raise ValueError("Could not fetch {}: {}".format(url, e))


async def fetch_nightly_metadata(session, nightly_url):
    """A JSON file containing build info is published along the nightly archive.
    """
    # XXX: It is only available for en-US though. Should we use the same for every locale?
    if "en-US" not in nightly_url:
        return None

    try:
        metadata_url = re.sub("\.({})$".format(FILE_EXTENSIONS), ".json", nightly_url)
        metadata = await fetch_json(session, metadata_url)
        return metadata
    except aiohttp.ClientError:
        return None


_candidates = {}


async def fetch_release_metadata(session, product, version, platform, locale):
    """The `candidates` folder contains build info about recent released versions.
    """
    global _candidates

    # XXX: It is only available for en-US though. Should we use the same for every locale?
    if locale != "en-US":
        return None

    # Keep the list of latest available candidates per product, for more efficiency.
    if _candidates.get(product) is None:
        candidates_url = archive_url(product, candidate="/")
        candidates_folders, _ = await fetch_listing(session, candidates_url)
        # For each version take the latest build.
        _candidates[product] = {}
        for f in candidates_folders:
            if f == "archived":
                continue
            candidate_version = f.replace("-candidates/", "")
            builds_url = archive_url(product, candidate_version, candidate="/")
            build_folders, _ = await fetch_listing(session, builds_url)
            latest_build_folder = sorted(build_folders)[-1]
            _candidates[product][candidate_version] = latest_build_folder

    # Candidates are only available for a subset of versions.
    if version not in _candidates[product]:
        return None

    latest_build_folder = _candidates[product][version]
    try:
        url = archive_url(product, version, platform, locale, candidate=latest_build_folder)
        _, files = await fetch_listing(session, url)

        for f_ in files:
            filename = f_["name"]
            if is_release_metadata(filename):
                url += filename
                metadata = await fetch_json(session, url)
                return metadata

    except (ValueError, aiohttp.ClientError) as e:
        pass
    return None


async def fetch_products(session, queue, products, client):
    # Nightlies
    futures = [fetch_nightlies(session, queue, product, client) for product in products]
    await asyncio.gather(*futures)
    # Releases
    futures = [fetch_versions(session, queue, product, client) for product in products]
    await asyncio.gather(*futures)


async def fetch_nightlies(session, queue, product, client):
    # Check latest known version on server.
    latest_nightly_folder = ""
    latest_known = latest_known_nightly_datetime(client, product)
    if latest_known:
        latest_nightly_folder = latest_known.strftime("%Y-%m-%d-%H-%M-%S")

    current_month = "{}/{:02d}".format(today.year, today.month)
    month_url = archive_url(product, nightly=current_month)
    days_folders, _ = await fetch_listing(session, month_url)

    # Skip aurora nightlies and known nightlies...
    days_urls = [archive_url(product, nightly=current_month + "/" + f[:-1])
                 for f in days_folders if f > latest_nightly_folder]
    days_urls = [url for url in days_urls if "mozilla-central" in url]

    futures = [fetch_listing(session, day_url) for day_url in days_urls]
    listings = await asyncio.gather(*futures)

    batch_size = 10

    for day_url, (_, files) in zip(days_urls, listings):
        # Fetch metadata and put into queue in batch.
        nb_batches = (len(files) // batch_size) + 1
        for i in range(nb_batches):
            files_subset = files[(i * batch_size):((i + 1) * batch_size)]

            # Fetch metadata in batch.
            futures = [fetch_nightly_metadata(session, day_url + file_["name"])
                       for file_ in files_subset]
            metadatas = await asyncio.gather(*futures)

            # Add to queue in batch.
            futures = []
            for file_, metadata in zip(files_subset, metadatas):
                filename = file_["name"]
                size = file_["size"]
                date = file_["last_modified"]
                url = day_url + filename
                try:
                    version, locale, platform = parse_nightly_filename(filename)
                except ValueError:
                    continue
                record = archive(product, version, platform, locale, url,
                                 size, date, metadata)
                logger.debug("Nightly found {}".format(url))
                futures.append(queue.put(record))
            await asyncio.gather(*futures)


async def fetch_versions(session, queue, product, client):
    latest_version = latest_known_version(client, product)
    if latest_version:
        logger.info("Scrape {} from version {}".format(product, latest_version))

    product_url = archive_url(product)
    versions_folders, _ = await fetch_listing(session, product_url)

    versions = [v[:-1] for v in versions_folders if re.match(r'^[0-9]', v)]
    versions = [v for v in versions if "funnelcake" not in v]
    # Scrape only unknown recent versions.
    versions = [v for v in versions if version_parse(v) > version_parse(latest_version)]
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

    futures = []
    for file_ in files:
        filename = file_["name"]

        if not is_release_filename(product, filename):
            continue

        url = locale_url + filename
        size = file_["size"]
        date = file_["last_modified"]

        metadata = await fetch_release_metadata(session, product, version, platform, locale)
        record = archive(product, version, platform, locale, url, size, date, metadata)
        logger.debug("Release found {}".format(url))

        futures.append(queue.put(record))

    return await asyncio.gather(*futures)


async def produce(loop, queue, client):
    """Grab releases from the archives website."""
    async with aiohttp.ClientSession(loop=loop) as session:
        await fetch_products(session, queue, PRODUCTS, client)
    logger.info("Scraping releases done.")


async def consume(loop, queue, executor, client):
    """Store grabbed releases from the archives website in Kinto."""

    def markdone(queue, n):
        """Returns a callback that will mark `n` queue items done."""
        def done(future):
            exc = future.exception()
            if exc is not None:
                raise exc
            return [queue.task_done() for _ in range(n)]
        return done

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
