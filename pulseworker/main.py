import functools
import logging
import os
import sys
import json

from kinto_http import cli_utils
from mozillapulse.consumers import NormalizedBuildConsumer


DEFAULT_SERVER = "https://kinto-ota.dev.mozaws.net/v1"
DEFAULT_BUCKET = "build-hub-test"
DEFAULT_COLLECTION = "builds"
PULSEGUARDIAN_USER = os.getenv("PULSEGUARDIAN_USER", "")
PULSEGUARDIAN_PASSWORD = os.getenv("PULSEGUARDIAN_PASSWORD", "")


logger = logging.getLogger(__name__)


def callback(body, msg, client):
    routing_key = body['_meta']['routing_key']
    # https://github.com/mozilla/pulsetranslator#routing-keys
    prefix, tree = routing_key.split('.', 2)[:2]
    if prefix == "build" and tree not in ("autoland", "try"):
        r = client.create_record(body['payload'])
        logger.info("Created record %s" % r)
    else:
        logger.debug("Skip routing key '%s'" % routing_key)


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

    public = {"read": ["system.Everyone"]}
    client.create_bucket(permissions=public, if_not_exists=True)
    client.create_collection(if_not_exists=True)

    c = NormalizedBuildConsumer(user=PULSEGUARDIAN_USER,
                                password=PULSEGUARDIAN_PASSWORD,
                                topic='#',
                                callback=functools.partial(callback, client=client))
    c.listen()
