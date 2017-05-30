import asyncio
import async_timeout
import logging
import sys
import xml.etree.ElementTree as etree

import aiohttp
from kinto_http import cli_utils

from .utils import chunked


AUS_URL = ("https://aus5.mozilla.org/update/3/SystemAddons/{VERSION}/{BUILD_ID}/"
           "{BUILD_TARGET}/{LOCALE}/{CHANNEL}/{OS_VERSION}/{DISTRIBUTION}/"
           "{DISTRIBUTION_VERSION}/update.xml")
AUS_BATCH_SIZE = 10
DEFAULT_SERVER = "https://kinto-ota.dev.mozaws.net/v1"
DEFAULT_BUCKET = "build-hub"
DEFAULT_COLLECTION = "archives"
NB_RETRY_REQUEST = 5
TIMEOUT_SECONDS = 5 * 60


logger = logging.getLogger(__name__)


async def fetch_updates(session, url, entry):
    # https://gecko.readthedocs.io/en/latest/toolkit/mozapps/extensions/ \
    #    addon-manager/SystemAddons.html#system-add-on-updates
    url = url.format(VERSION=entry["target"]["version"],
                     BUILD_ID=entry["build"]["id"],
                     BUILD_TARGET=entry["target"]["platform"],
                     LOCALE=entry["target"]["locale"],
                     CHANNEL=entry["target"]["channel"],
                     OS_VERSION="default",
                     DISTRIBUTION="default",
                     DISTRIBUTION_VERSION="default")

    logger.info("Fetch updates info from {}".format(url))

    headers = {
        "Accept": "application/xml",
        "User-Agent": "BuildHub;storage-team@mozilla.com"
    }
    with async_timeout.timeout(TIMEOUT_SECONDS):
        async with session.get(url, headers=headers, timeout=None) as response:
            try:
                xml_content = await response.text()
                addons = parse_response(xml_content)
                return addons
            except aiohttp.ClientError as e:
                raise ValueError("Could not fetch %s: %s" % (url, e))


def parse_response(xml_content):
    # <?xml version="1.0"?>
    # <updates>
    #   <addons>
    #     <addon id="flyweb@mozilla.org"
    #            URL="https://ftp.mozilla.org/pub/system-addons/flyweb/flyweb@mozilla.org-1.0.xpi"
    #            hashFunction="sha512" hashValue="abcdef123" size="1234" version="1.0"/>
    #     <addon id="pocket@mozilla.org"
    #            URL="https://ftp.mozilla.org/pub/system-addons/pocket/pocket@mozilla.org-1.0.xpi"
    #            hashFunction="sha512" hashValue="abcdef123" size="1234" version="1.0"/>
    #   </addons>
    # </updates>
    root = etree.fromstring(xml_content)
    addons = {}
    addons_nodes = root.findall(".//addons/addon")
    for addon_node in addons_nodes:
        id_ = addon_node.attrib["id"]
        version = addon_node.attrib["version"]
        addons[id_] = version
    return addons


async def main(loop):
    parser = cli_utils.add_parser_options(
        description="Send releases archives to Kinto",
        default_server=DEFAULT_SERVER,
        default_bucket=DEFAULT_BUCKET,
        default_retry=NB_RETRY_REQUEST,
        default_collection=DEFAULT_COLLECTION)

    args = parser.parse_args(sys.argv[1:])

    cli_utils.setup_logger(logger, args)
    kinto_logger = logging.getLogger('kinto_http')
    cli_utils.setup_logger(kinto_logger, args)

    logger.info("Fetch from at {server}/buckets/{bucket}/collections/{collection}"
                .format(**args.__dict__))

    client = cli_utils.create_client_from_args(args)

    filters = {
        "source.product": "firefox"
    }
    records = client.get_records(**filters)

    with_sysaddons = [r for r in records if r.get('systemaddons') is not None
                      and 'id' in (r.get('build') or {})]
    logger.info("{} entries found.".format(len(with_sysaddons)))

    # Check kinto maximum batch size (can differ from AUS_BATCH_SIZE).
    info = client.server_info()
    kinto_batch_size = info["settings"]["batch_max_requests"]

    chunks = chunked(with_sysaddons, AUS_BATCH_SIZE)
    nb_batches = len(chunks)

    async with aiohttp.ClientSession(loop=loop) as session:
        patches = []
        for i, records_subset in enumerate(chunks):
            logger.debug("{}/{}".format(i, nb_batches))

            # Launch a bunch of parallel requests to AUS.
            coros = []
            for record in records_subset:
                coro = fetch_updates(session, AUS_URL, record)
                coros.append(coro)
            results = await asyncio.gather(*coros)

            # Merge systemaddons updates with builtins.
            for record, sysaddons_updates in zip(records_subset, results):
                by_id = {s["id"]: s for s in record.setdefault("systemaddons", [])}

                for id_, version in sysaddons_updates.items():
                    by_id.setdefault(id_, {})
                    by_id[id_].setdefault("id", id_)
                    by_id[id_].setdefault("builtin", None)
                    by_id[id_]["updated"] = version

                # Enqueue patch record for the next kinto batch.
                systemaddons = list(by_id.values())
                patch = {"id": record["id"], "systemaddons": systemaddons}
                patches.append(patch)

                # Kinto batch full enough?
                if len(patches) == kinto_batch_size or i == nb_batches - 1:
                    with client.batch() as batch:
                        for patch in patches:
                            batch.patch_record(data=patch)
                    patches = []

    logger.info("Done.")


def run():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(loop))
    loop.close()


if __name__ == "__main__":
    run()
