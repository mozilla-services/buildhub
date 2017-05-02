import datetime
import functools
import logging
import os
import sys
import json

import requests
from kinto_http import cli_utils
from mozillapulse.consumers import NormalizedBuildConsumer


DEFAULT_SERVER = "https://kinto-ota.dev.mozaws.net/v1"
DEFAULT_BUCKET = "build-hub"
DEFAULT_COLLECTION = "builds"
PULSE_TOPIC = "build.#"
PULSEGUARDIAN_USER = os.getenv("PULSEGUARDIAN_USER", "")
PULSEGUARDIAN_PASSWORD = os.getenv("PULSEGUARDIAN_PASSWORD", "")


logger = logging.getLogger(__name__)


def epoch2iso(timestamp):
    dt = datetime.datetime.utcfromtimestamp(timestamp)
    # XXX: Python 3
    if sys.version_info >= (3, 2):
        dt = dt.replace(tzinfo=datetime.timezone.utc)
    return dt.isoformat()

def update_download_info(client, record):
    rid = record["data"]["id"]
    dlinfo = dict(record["data"]["download"])

    resp = requests.head(dlinfo["url"])
    dlinfo["size"] = int(resp.headers["Content-Length"])
    dlinfo["mimetype"] = resp.headers["Content-Type"]

    # XXX: use JSON-merge header.
    client.patch_record({"download": dlinfo}, id=rid)


def pulse2kinto(body, msg, client):
    # https://github.com/mozilla/pulsetranslator#routing-keys
    buildinfo = body["payload"]

    skip = (
        buildinfo["tree"] in ("autoland", "try") or
        buildinfo["buildtype"] in ("pgo",) or
        buildinfo["tree"] in ("mozilla-inbound",))
    if skip:
        logger.debug("Skip routing key '%s'" % body["_meta"]["routing_key"])
        return  # Do nothing.

    # XXX: no safer way to obtain version?
    filename = buildinfo["buildurl"].split('/')[-1]
    version = filename.split('.' + buildinfo["locale"])[0].replace(buildinfo["product"] + '-', '')

    record = {
        "build": {
            "id": buildinfo["buildid"],
            "date": epoch2iso(buildinfo["builddate"]),
            "type": buildinfo["buildtype"]
        },
        "source": {
            "revision": buildinfo["revision"],
            "tree": buildinfo["tree"],
            "product": buildinfo["product"],
        },
        "target": {
            "platform": buildinfo["platform"],
            "locale": buildinfo["locale"],
            "version": version,
            "channel": None,
        },
        "download": {
            "url": buildinfo["buildurl"],
            "mimetype": None,
            "size": None,
        },
        "systemaddons": None
    }
    r = client.create_record(record)
    logger.info("Created record %s" % r)

    # XXX: Python 3 async
    update_download_info(client, r)


if __name__ == "__main__":
    parser = cli_utils.add_parser_options(
        description="Send Pulse data to Kinto",
        default_server=DEFAULT_SERVER,
        default_bucket=DEFAULT_BUCKET,
        default_collection=DEFAULT_COLLECTION)

    args = parser.parse_args(sys.argv[1:])

    cli_utils.setup_logger(logger, args)

    logger.info("Publish at %s/buckets/%s/collections/%s/records" % (
        args.server, args.bucket, args.collection))

    client = cli_utils.create_client_from_args(args)

    public_perms = {"read": ["system.Everyone"]}
    client.create_bucket(permissions=public_perms, if_not_exists=True)
    client.create_collection(if_not_exists=True)

    callback = functools.partial(pulse2kinto, client=client)

    c = NormalizedBuildConsumer(user=PULSEGUARDIAN_USER,
                                password=PULSEGUARDIAN_PASSWORD,
                                topic=PULSE_TOPIC,
                                callback=callback)
    c.listen()
