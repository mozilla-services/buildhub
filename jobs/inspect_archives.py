import asyncio
import configparser
import concurrent.futures
import copy
import datetime
import json
import logging
import os
import sys
import tarfile

import requests
import kinto_http.exceptions
from kinto_http import cli_utils


DEFAULT_SERVER = "https://kinto-ota.dev.mozaws.net/v1"
DEFAULT_BUCKET = "build-hub"
DEFAULT_COLLECTION = "archives"
NB_WORKERS = 10


logger = logging.getLogger(__name__)


def publish_record(client, record):
    try:
        r = client.create_record(record)
        logger.info("Created record %s" % json.dumps(r))
    except kinto_http.exceptions.KintoException:
        error_msg = "Could not create record for %s" % record["download"]["url"]
        logger.exception(error_msg)


def cached_download(url):
    urlpath = url.rsplit('/')[-4:]
    tempname = os.path.join(".cache", *urlpath)

    if not os.path.exists(tempname):
        folder = os.path.dirname(tempname)
        if not os.path.exists(folder):
            os.makedirs(folder)

        # Download !
        logger.info("Download %s" % url)
        with open(tempname, 'wb') as f:
            stream = requests.get(url, stream=True)
            for chunk in stream.iter_content(chunk_size=1024):
                if chunk:  # filter out keep-alive new chunks
                    f.write(chunk)

    return tempname


def process_archive(client, record):
    # Download archive
    url = record["download"]["url"]

    if not url.endswith("bz2"):
        # XXX: manage old .gz etc.
        return

    archive = cached_download(url)

    updated = copy.deepcopy(record)

    try:
        # Extract files from archive into tempdir.
        logger.info("Extract from %s" % url)
        tar = tarfile.open(archive, "r:bz2")
        for tarinfo in tar:
            filename = tarinfo.name
            # Inspect metadata.ini
            if filename.endswith("application.ini"):
                f = tar.extractfile(tarinfo)
                ini_content = f.read().decode('ascii')

                config = configparser.ConfigParser()
                config.read_string(ini_content)

                repository = config["App"]["SourceRepository"]
                tree = repository.rsplit("/", 1)[-1]
                buildid = config["App"]["BuildID"]
                builddate = datetime.datetime.strptime(buildid, "%Y%m%d%H%M%S").isoformat()
                revision = config["App"]["SourceStamp"]

                if updated.get("build") is None:
                    updated["build"] = {}
                updated["build"]["id"] = buildid
                updated["build"]["date"] = builddate
                if updated.get("source") is None:
                    updated["source"] = {}
                updated["source"]["tree"] = tree
                updated["source"]["revision"] = revision
                updated["source"]["repository"] = repository
                break
            # XXX Inspect system addons
        tar.close()
    except:
        logger.exception("Could not introspect archive %s" % url)

    if record["source"]["revision"] != updated["source"]["revision"]:
        logger.info("Update metadata of %s" % updated)
        # XXX why 412 here? why safe=False?
        client.update_record(updated, safe=False)


def main():
    parser = cli_utils.add_parser_options(
        description="Inspect and complete archives on Kinto",
        default_server=DEFAULT_SERVER,
        default_bucket=DEFAULT_BUCKET,
        default_collection=DEFAULT_COLLECTION)

    args = parser.parse_args(sys.argv[1:])

    cli_utils.setup_logger(logger, args)

    logger.info("Inspect {server}/buckets/{bucket}/collections/{collection}"
                .format(**args.__dict__))

    client = cli_utils.create_client_from_args(args)
    client.session.nb_retry = 1

    filters = {
        # "_since": "1493977727760",  # XXX: store previous timestamp in a file
        # "target.platform": "linux-x86_64",
        # "target.locale": "en-US",
        "source.product": "firefox"
    }
    records = client.get_records(**filters)
    # XXX: https://github.com/Kinto/kinto/issues/1215
    records = [r for r in records if r["source"].get("revision") is None]
    logger.info("%s archives to process." % len(records))
    if len(records) == 0:
        return

    loop = asyncio.get_event_loop()

    executor = concurrent.futures.ProcessPoolExecutor(max_workers=NB_WORKERS)
    tasks = [
        loop.run_in_executor(executor, process_archive, client, record)
        for record in records
    ]
    future = asyncio.wait(tasks)
    try:
        loop.run_until_complete(future)
    finally:
        loop.close()


if __name__ == "__main__":
    main()
