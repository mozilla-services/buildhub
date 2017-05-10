import asyncio
import configparser
import concurrent.futures
import datetime
import json
import logging
import os
import re
import subprocess
import sys
import tarfile
import tempfile
import xml.etree.ElementTree as etree

import requests
import kinto_http.exceptions
from kinto_http import cli_utils


DEFAULT_SERVER = "https://kinto-ota.dev.mozaws.net/v1"
DEFAULT_BUCKET = "build-hub"
DEFAULT_COLLECTION = "archives"
NB_WORKERS = 5  # CPU + 1


logger = logging.getLogger(__name__)


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


def extract_application_metadata(ini_content):
    config = configparser.ConfigParser()
    config.read_string(ini_content.decode('utf8'))

    buildid = config["App"]["BuildID"]
    builddate = datetime.datetime.strptime(buildid[:12], "%Y%m%d%H%M").isoformat()
    revision = config["App"].get("SourceStamp")

    repository = config["App"].get("SourceRepository")
    tree = repository.rsplit("/", 1)[-1] if repository else None

    return {
        "build": {
            "id": buildid,
            "date": builddate,
        },
        "source": {
            "tree": tree,
            "revision": revision,
            "repository": repository,
        }
    }


def extract_systemaddon_metadata(xml_content):
    root = etree.fromstring(xml_content)
    description = root.find('.//{http://www.w3.org/1999/02/22-rdf-syntax-ns#}Description')
    id_ = description.find('{http://www.mozilla.org/2004/em-rdf#}id').text
    version = description.find('{http://www.mozilla.org/2004/em-rdf#}version').text
    return id_, version


def process_linux_archive(client, record):
    # Download archive
    url = record["download"]["url"]

    has_sysaddons = int(record["target"]["version"].split(".", 1)[0]) > 50
    systemaddons = [] if has_sysaddons else None

    updated = record.copy()

    archive = cached_download(url)

    size = os.path.getsize(archive)
    if url.endswith("bz2"):
        mode = "r:bz2"
        mimetype = "application/x-bzip2"
    else:
        mode = "r:gz"
        mimetype = "application/gzip"

    updated["download"]["size"] = size
    updated["download"]["mimetype"] = mimetype

    try:
        logger.info("Extract from %s" % url)
        tar = tarfile.open(archive, mode)
    except tarfile.ReadError:
        logger.error("Could not read archive %s." % archive)
        # Will retry download next run.
        os.remove(archive)
        return
    try:
        for tarinfo in tar:
            filename = tarinfo.name

            # Inspect metadata.ini
            if filename.endswith("application.ini"):
                logger.info("Read %s" % filename)
                f = tar.extractfile(tarinfo)
                ini_content = f.read()
                metadata = extract_application_metadata(ini_content)
                updated["build"] = {**(updated.get("build") or {}), **metadata["build"]}
                updated["source"] = {**(updated.get("source") or {}), **metadata["source"]}

                if not has_sysaddons:
                    break

            # Inspect system addons
            if has_sysaddons and re.match(r".+/browser/features/.+\.xpi$", filename):

                # XXX: Apparently Python can't unzip XPI files oO
                # zipfile.BadZipFile: Bad magic number for central directory
                with tempfile.TemporaryDirectory() as tmpdirname:
                    logger.info("Introspect system-addon %s" % filename)
                    tar.extractall(path=tmpdirname, members=[tarinfo])
                    xpipath = os.path.join(tmpdirname, filename)

                    logger.debug("Extract install manifest from %s" % xpipath)
                    subprocess.run(["unzip", "-o", xpipath, "install.rdf", "-d", tmpdirname])
                    xmlfile = os.path.join(tmpdirname, 'install.rdf')

                    logger.debug("Read version from %s" % xmlfile)
                    xml_content = open(xmlfile).read()
                    id_, version = extract_systemaddon_metadata(xml_content)
                    systemaddons.append({"id": id_, "builtin": version})

        tar.close()
    except:
        logger.exception("Could not introspect archive %s" % url)

    updated["systemaddons"] = systemaddons

    has_changed = json.dumps(record, sort_keys=True) != json.dumps(updated, sort_keys=True)
    if has_changed:
        logger.info("Update metadata of %s" % updated)
        client.update_record(updated)


def main():
    parser = cli_utils.add_parser_options(
        description="Inspect and complete archives on Kinto",
        default_server=DEFAULT_SERVER,
        default_bucket=DEFAULT_BUCKET,
        default_collection=DEFAULT_COLLECTION)

    args = parser.parse_args(sys.argv[1:])

    cli_utils.setup_logger(logger, args)
    kinto_logger = logging.getLogger('kinto_http')
    cli_utils.setup_logger(kinto_logger, args)

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
    records = [r for r in records if (r["build"] or {}).get("id") is None]
    # XXX: Currently only inspects linux tarballs
    records = [r for r in records if re.match(".+(bz2|gz)$", r["download"]["url"])]

    logger.info("%s archives to process." % len(records))
    if len(records) == 0:
        return

    loop = asyncio.get_event_loop()
    executor = concurrent.futures.ProcessPoolExecutor(max_workers=NB_WORKERS)
    tasks = [
        loop.run_in_executor(executor, process_linux_archive, client, record)
        for record in records
    ]
    future = asyncio.wait(tasks)
    try:
        loop.run_until_complete(future)
    finally:
        for task in tasks:
            task.cancel()
        executor.shutdown()
        loop.close()


if __name__ == "__main__":
    main()
