# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, you can obtain one at http://mozilla.org/MPL/2.0/.

"""
Read records as JSON from stdin, and pushes them on a Kinto server
concurrently.

Usage:

    $ echo '{"data": {"title": "a"}}
    {"data": {"title": "b"}}
    {"data": {"title": "c"}}' | to-kinto --server=https://localhost:8888/v1 \
                                         --bucket=bid \
                                         --collection=cid \
                                         --auth=user:pass

It is meant to be combined with other commands that output records to stdout :)

    $ cat filename.csv | inventory-to-records | to-kinto --auth=user:pass
    $ scrape-archives | to-kinto --auth=user:pass

"""
import asyncio
import async_timeout
import concurrent.futures
import copy
import hashlib
import json
import logging
import os
import sys
from urllib.parse import urlparse

from kinto_http import cli_utils
from decouple import config

from buildhub.utils import stream_as_generator
from buildhub.configure_markus import get_metrics


DEFAULT_SERVER = 'http://localhost:8888/v1'
DEFAULT_BUCKET = 'default'
DEFAULT_COLLECTION = 'cid'
NB_THREADS = 3
NB_RETRY_REQUEST = 3
WAIT_TIMEOUT = 5
BATCH_MAX_REQUESTS = config('BATCH_MAX_REQUESTS', default=9999, cast=int)
OLD_PREVIOUS_DUMP_FILENAME = '.records-{server}-{bucket}-{collection}.json'
PREVIOUS_DUMP_FILENAME = '.records-hashes-{server}-{bucket}-{collection}.json'
CACHE_FOLDER = config('CACHE_FOLDER', default='.')

logger = logging.getLogger(__name__)
metrics = get_metrics('buildhub')

done = object()


def _migrate_old_dump_file(old_file, new_file):
    """The old file is a .json file that, when opened, is a massive list of
    dictionaries. Open it and save to the new JSON file.

    The format of the JSON file is like this:

        ID --> [last_modified, md5_hash_string]

    E.g.
    """
    with open(old_file) as f:
        data = json.load(f)

    new_data = {}
    for record in data:
        new_data[record['id']] = [
            record['last_modified'],
            _hash_record_mutate(record)
        ]

    with open(new_file, 'w') as f:
        json.dump(new_data, f, sort_keys=True, indent=2)


def hash_record(record):
    """Return a hash string (based of MD5) that is 32 characters long.

    This function does *not mutate* the record but needs to make a copy of
    the record (and mutate that) so it's less performant.
    """
    return _hash_record_mutate(copy.deepcopy(record))


def _hash_record_mutate(record):
    """Return a hash string (based of MD5) that is 32 characters long.

    NOTE! For performance, this function *will mutate* the record object.
    Yeah, that sucks but it's more performant than having to clone a copy
    when you have to do it 1 million of these records.
    """
    record.pop('last_modified', None)
    record.pop('schema', None)
    return hashlib.md5(
       json.dumps(record, sort_keys=True).encode('utf-8')
    ).hexdigest()


def fetch_existing(
    client,
    cache_file=PREVIOUS_DUMP_FILENAME,
    old_cache_file=OLD_PREVIOUS_DUMP_FILENAME,
):
    """Fetch all records since last run. A JSON file on disk is used to store
    records from previous run.
    """
    cache_file = os.path.join(CACHE_FOLDER, cache_file.format(
        server=urlparse(client.session.server_url).hostname,
        bucket=client._bucket_name,
        collection=client._collection_name))

    # Note! Some time in late 2018 we can delete these lines. By then,
    # Stage and Prod (and pretty much every active developers') will have
    # switched to the new hash-based dump file. Till then, let these lines
    # sit around. If the migration happens and is successful, the old
    # cache file gets deleted.
    if not os.path.exists(cache_file):

        # Perhaps the old file exists!
        # Prior to April 2018 we used dump ALL kinto records into a .json
        # file as a massive list of dicts.
        # The problem with that was that it bloated RAM badly.
        # The .json file was around 700+MB and when loaded into Python as a
        # list object it would take up about 2.4GB of RAM.
        # (Note the .json file of hashes, when read in to Python becomes
        # about 200MB)
        # Also, by always hashing the records consistently we could just
        # compare two hashes (as strings) instead of having to compare
        # dictionaries.
        old_cache_file = os.path.join(CACHE_FOLDER, old_cache_file.format(
            server=urlparse(client.session.server_url).hostname,
            bucket=client._bucket_name,
            collection=client._collection_name))
        if os.path.exists(old_cache_file):
            _migrate_old_dump_file(old_cache_file, cache_file)
            logger.info(f'Migrated dump file {old_cache_file} to {cache_file}')
            os.remove(old_cache_file)
        # End dump file migration.

    records = {}
    previous_run_etag = None

    if os.path.exists(cache_file):
        with open(cache_file) as f:
            records = json.load(f)
            highest_timestamp = max(
                [r[0] for r in records.values()]
            )
            previous_run_etag = '"%s"' % highest_timestamp

    new_records = client.get_records(
        _since=previous_run_etag,
        pages=float('inf')
    )

    for record in new_records:
        records[record['id']] = [
            record['last_modified'],
            hash_record(record)
        ]

    # Atomic write.
    if records:
        tmpfilename = cache_file + '.tmp'
        with open(tmpfilename, 'w') as f:
            json.dump(records, f, sort_keys=True, indent=2)
        os.rename(tmpfilename, cache_file)

    return records


@metrics.timer_decorator('to_kinto_publish_records')
def publish_records(client, records):
    """Synchronuous function that pushes records on Kinto in batch.
    """
    with client.batch() as batch:
        for record in records:
            if 'id' in record['data']:
                metrics.incr('to_kinto_update_record')
                batch.update_record(**record)
            else:
                metrics.incr('to_kinto_create_record')
                batch.create_record(**record)
    results = batch.results()

    # Batch don't fail with 4XX errors. Make sure we output a comprehensive
    # error here when we encounter them.
    error_msgs = []
    for result in results:
        error_status = result.get('code')
        if error_status == 412:
            error_msg = ("Record '{details[existing][id]}' already exists: "
                         '{details[existing]}').format_map(result)
            error_msgs.append(error_msg)
        elif error_status == 400:
            error_msg = 'Invalid record: {}'.format(result)
            error_msgs.append(error_msg)
        elif error_status is not None:
            error_msgs.append('Error: {}'.format(result))
    if error_msgs:
        raise ValueError('\n'.join(error_msgs))

    return results


async def produce(loop, records, queue):
    """Reads an asynchronous generator of records and puts them into the queue.
    """
    async for record in records:
        if 'data' not in record and 'permission' not in record:
            raise ValueError("Invalid record (missing 'data' attribute)")

        await queue.put(record)

    # Notify consumer that we are done.
    await queue.put(done)


async def consume(loop, queue, executor, client, existing):
    """Store grabbed releases from the archives website in Kinto.
    """
    def markdone(queue, n):
        """Returns a callback that will mark `n` queue items done."""
        def done(future):
            [queue.task_done() for _ in range(n)]
            results = future.result()  # will raise exception if failed.
            logger.info('Pushed {} records'.format(len(results)))
            return results
        return done

    def record_unchanged(record):
        return (
            record['id'] in existing and
            existing.get(record['id']) == hash_record(record)
        )

    info = client.server_info()
    ideal_batch_size = min(
        BATCH_MAX_REQUESTS,
        info['settings']['batch_max_requests']
    )

    while 'consumer is not cancelled':
        # Consume records from queue, and batch operations.
        # But don't wait too much if there's not enough records
        # to fill a batch.
        batch = []
        try:
            with async_timeout.timeout(WAIT_TIMEOUT):
                while len(batch) < ideal_batch_size:
                    record = await queue.get()
                    # Producer is done, don't wait for items to come in.
                    if record is done:
                        queue.task_done()
                        break
                    # Check if known and hasn't changed.
                    if record_unchanged(record['data']):
                        logger.debug(
                            f"Skip unchanged record {record['id']}"
                        )
                        queue.task_done()
                        continue

                    # Add record to current batch, and wait for more.
                    batch.append(record)

        except asyncio.TimeoutError:
            if batch:
                logger.debug(
                    f'Stop waiting, proceed with {len(batch)} records.'
                )
            else:
                logger.debug('Waiting for records in the queue.')

        # We have a batch of records, let's publish them using
        # parallel workers.
        # When done, mark queue items as done.
        if batch:
            task = loop.run_in_executor(
                executor, publish_records, client, batch
            )
            task.add_done_callback(markdone(queue, len(batch)))


async def parse_json(lines):
    async for line in lines:
        record = json.loads(line.decode('utf-8'))
        yield record


async def main(
    loop,
    stdin_generator,
    client,
    skip_existing=True,
    existing=None,
):
    existing = existing or {}  # Because it can't be a mutable default argument
    if skip_existing:
        # Fetch the list of records to skip records that exist
        # and haven't changed.
        existing = fetch_existing(client)

    # Start a producer and a consumer with threaded kinto requests.
    queue = asyncio.Queue()
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=NB_THREADS)
    # Schedule the consumer
    consumer_coro = consume(loop, queue, executor, client, existing)
    consumer = asyncio.ensure_future(consumer_coro)
    # Run the producer and wait for completion
    await produce(loop, stdin_generator, queue)
    # Wait until the consumer is done consuming everything.
    await queue.join()
    # The consumer is still awaiting for the producer, cancel it.
    consumer.cancel()


def run():
    loop = asyncio.get_event_loop()
    stdin_generator = stream_as_generator(loop, sys.stdin)
    records_generator = parse_json(stdin_generator)

    parser = cli_utils.add_parser_options(
        description='Read records from stdin as JSON and push them to Kinto',
        default_server=DEFAULT_SERVER,
        default_bucket=DEFAULT_BUCKET,
        default_retry=NB_RETRY_REQUEST,
        default_collection=DEFAULT_COLLECTION)
    parser.add_argument('--skip', action='store_true',
                        help='Skip records that exist and are equal.')
    cli_args = parser.parse_args()
    cli_utils.setup_logger(logger, cli_args)

    logger.info('Publish at {server}/buckets/{bucket}/collections/{collection}'
                .format(**cli_args.__dict__))

    client = cli_utils.create_client_from_args(cli_args)

    main_coro = main(
        loop,
        records_generator,
        client,
        skip_existing=cli_args.skip
    )

    loop.run_until_complete(main_coro)
    loop.close()


if __name__ == '__main__':
    run()
