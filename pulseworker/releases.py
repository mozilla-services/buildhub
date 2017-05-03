import json
import logging
import re
import sys
from packaging.version import parse as version_parse


import requests
from kinto_http import cli_utils
from mozillapulse.consumers import NormalizedBuildConsumer


DEFAULT_SERVER = "https://kinto-ota.dev.mozaws.net/v1"
DEFAULT_BUCKET = "build-hub"
DEFAULT_COLLECTION = "releases"


logger = logging.getLogger(__name__)


def fetch_listing(url):
    try:
        resp = requests.get(url, headers={"Accept": "application/json"})
        data = resp.json()
        return data["prefixes"], data["files"]
    except (ValueError, KeyError) as e:
        raise ValueError("Could not fetch %s: %s" % (url, e))


def release2kinto(client, record):
    r = client.create_record(record)
    logger.info("Created record %s" % json.dumps(r))


if __name__ == "__main__":
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

    for product in ("firefox", "thunderbird"):
        producturl = "https://archive.mozilla.org/pub/%s/" % product

        releasesurl = producturl + "releases/"
        version_folders, _ = fetch_listing(releasesurl)
        versions = [v[:-1] for v in version_folders if re.match(r'^[0-9]', v)]
        versions = sorted(versions, key=lambda v: version_parse(v), reverse=True)

        for version in versions[:10]:
            versionurl = releasesurl + version + "/"

            platform_folders, _ = fetch_listing(versionurl)
            platforms = [p[:-1] for p in platform_folders]
            platforms = [p for p in platforms if p not in ("source", "update")]

            for platform in platforms:
                localeurl = versionurl + platform + "/"

                locale_folders, _ = fetch_listing(localeurl)
                locales = [l[:-1] for l in locale_folders]
                locales = [l for l in locales if l != "xpi"]

                for locale in locales:
                    filesurl = localeurl + locale + "/"

                    _, files = fetch_listing(filesurl)
                    for file_ in files:
                        filename = file_["name"]
                        filesize = file_["size"]
                        if not re.match("%s-(.+)(zip|gz|bz|bz2|dmg|apk)$" % product, filename):
                            logger.warn("Skipped %s" % (filesurl + filename))
                            continue

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
                                "size": filesize,
                            },
                            "systemaddons": None
                        }
                        release2kinto(client, record)
