import logging
import sys
from kinto_http import cli_utils
# 1. Grab the bucket/collections
# 2. Create filters collections:
#  - product_filters
#  - locale_filters
#  - platform_filters
#  - channels_filters
#  - version_filters

DEFAULT_SERVER = "https://kinto-ota.dev.mozaws.net/v1"
DEFAULT_BUCKET = "build-hub"
DEFAULT_COLLECTION = "releases"
NB_RETRY_REQUEST = 3

logger = logging.getLogger(__name__)


def main(argv):
    parser = cli_utils.add_parser_options(
        description="Send releases archives to Kinto",
        default_server=DEFAULT_SERVER,
        default_bucket=DEFAULT_BUCKET,
        default_retry=NB_RETRY_REQUEST,
        default_collection=DEFAULT_COLLECTION)

    args = parser.parse_args(argv)

    cli_utils.setup_logger(logger, args)

    client = cli_utils.create_client_from_args(args)

    releases = client.get_records()

    with client.batch() as batch:
        for cid in ['product_filters', 'locale_filters', 'platform_filters',
                    'channel_filters', ' version_filters']:
            batch.create_collection(id=cid)

    product_filters = set()
    locale_filters = set()
    platform_filters = set()
    channel_filters = set()
    version_filters = set()

    for release in releases:
        product_filters.add(release['source']['product'])
        locale_filters.add(release['target']['locale'])
        platform_filters.add(release['target']['platform'])
        channel_filters.add(release['target']['channel'])
        version_filters.add(release['target']['version'])

    with client.batch() as batch:
        # product_filters
        for pf in product_filters:
            batch.create_record(id=pf, data={"name": pf},
                                collection='product_filters', safe=False)

    with client.batch() as batch:
        # locale_filters
        for lf in locale_filters:
            batch.create_record(id=lf, data={"name": lf},
                                collection='locale_filters', safe=False)

    with client.batch() as batch:
        # platform_filters
        for pf in platform_filters:
            batch.create_record(id=pf, data={"name": pf},
                                collection='platform_filters', safe=False)

    with client.batch() as batch:
        # channel_filters
        for cf in channel_filters:
            batch.create_record(id=cf, data={"name": cf},
                                collection='channel_filters', safe=False)

    with client.batch() as batch:
        # version_filters
        for vf in version_filters:
            batch.create_record(id=vf, data={"name": vf},
                                collection='version_filters', safe=False)


def run():
    main(sys.argv[1:])


if __name__ == "__main__":
    run()
