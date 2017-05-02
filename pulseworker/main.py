import datetime
import functools
import logging
import os
import sys
import json

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


def pulse2kinto(body, msg, client):
    # https://github.com/mozilla/pulsetranslator#routing-keys
    buildinfo = body["payload"]

    if buildinfo["tree"] in ("autoland", "try"):
        logger.debug("Skip routing key '%s'" % body["_meta"]["routing_key"])
        return  # Do nothing.

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
            "version": None,
            "channel": None,
        },
        "download": {
            "url": buildinfo["buildurl"],
            "size": None,
        },
        "systemaddons": None
    }
    r = client.create_record(record)
    logger.info("Created record %s" % r)


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
