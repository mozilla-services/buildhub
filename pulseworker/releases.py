import asyncio
import json
import logging
import re
import sys
from packaging.version import parse as version_parse

import aiohttp
from kinto_http import cli_utils


ARCHIVE_URL = "https://archive.mozilla.org/pub/"
DEFAULT_SERVER = "https://kinto-ota.dev.mozaws.net/v1"
DEFAULT_BUCKET = "build-hub"
DEFAULT_COLLECTION = "archives"


logger = logging.getLogger(__name__)


async def fetch_listing(session, url):
    headers = {"Accept": "application/json"}
    async with session.get(url, headers=headers) as response:
        try:
            data = await response.json()
            return data["prefixes"], data["files"]
        except (aiohttp.ClientError, KeyError) as e:
            raise ValueError("Could not fetch %s: %s" % (url, e))


async def walk_releases(loop, queue):
    async with aiohttp.ClientSession(loop=loop) as session:

        for product in ("firefox", "thunderbird"):
            releasesurl = ARCHIVE_URL + product + "/releases/"

            version_folders, _ = await fetch_listing(session, releasesurl)
            versions = [v[:-1] for v in version_folders if re.match(r'^[0-9]', v)]
            versions = sorted(versions, key=lambda v: version_parse(v), reverse=True)

            for version in versions:
                versionurl = releasesurl + version + "/"

                platform_folders, _ = await fetch_listing(session, versionurl)
                platforms = [p[:-1] for p in platform_folders]
                platforms = [p for p in platforms if p not in ("source", "update")]

                for platform in platforms:
                    localeurl = versionurl + platform + "/"

                    locale_folders, _ = await fetch_listing(session, localeurl)
                    locales = [l[:-1] for l in locale_folders]
                    locales = [l for l in locales if l != "xpi"]

                    for locale in locales:
                        filesurl = localeurl + locale + "/"

                        _, files = await fetch_listing(session, filesurl)
                        fileregexp = re.compile("%s-(.+)(zip|gz|bz|bz2|dmg|apk)$" % product)
                        files = [f for f in files if fileregexp.match(f["name"])]

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
                                    "url": filesurl + filename,
                                    "mimetype": None,
                                    "size": None,
                                },
                                "systemaddons": None
                            }
                            logger.debug("Release found %s" % (filesurl + filename))
                            await queue.put(record)

    logger.debug("Walking releases done.")
    await queue.put(None)


async def consume(client, queue):
    while True:
        record = await queue.get()
        if record is None:
            # the producer emits None to indicate that it is done
            break

        r = client.create_record(record)
        logger.info("Created record %s" % json.dumps(r))


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

    public_perms = {"read": ["system.Everyone"]}
    client.create_bucket(permissions=public_perms, if_not_exists=True)
    client.create_collection(if_not_exists=True)

    loop = asyncio.get_event_loop()
    queue = asyncio.Queue(loop=loop)

    producer_coro = walk_releases(loop, queue)
    consumer_coros = [consume(client, queue) for i in range(5)]
    future = asyncio.gather(producer_coro, *consumer_coros)
    loop.run_until_complete(future)


if __name__ == "__main__":
    main()
