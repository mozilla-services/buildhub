import asyncio
import os
import io
import json

import aiohttp
import asynctest
from aioresponses import aioresponses

from buildhub import inventory_to_records


here = os.path.dirname(__file__)


class LongResponse:
    def __init__(*args, **kwargs):
        pass

    async def __call__(self, *args, **kwargs):
        return self

    async def __aenter__(self, *args):
        return self

    async def __aexit__(self, *args):
        pass

    async def json(self):
        return await asyncio.sleep(10000)


class FetchJsonTest(asynctest.TestCase):
    url = 'http://test.example.com'
    data = {'foo': 'bar'}

    async def setUp(self):
        self.session = aiohttp.ClientSession(loop=self.loop)
        self.addCleanup(self.session.close)

        mocked = aioresponses()
        mocked.start()
        mocked.get(self.url, payload=self.data)
        self.addCleanup(mocked.stop)

    async def test_returns_json_response(self):
        received = await inventory_to_records.fetch_json(self.session, self.url)
        assert received == self.data

    async def test_raises_timeout_response(self):
        with asynctest.patch.object(self.session, "get", LongResponse):
            with self.assertRaises(asyncio.TimeoutError):
                await inventory_to_records.fetch_json(self.session, self.url, 0.1)


class FetchListingTest(asynctest.TestCase):
    url = 'http://test.example.com'

    async def setUp(self):
        self.session = aiohttp.ClientSession(loop=self.loop)
        self.addCleanup(self.session.close)

    async def test_returns_tuple_with_directories_and_files(self):
        with aioresponses() as m:
            m.get(self.url, payload={
                "prefixes": ["a/", "b/"],
                "files": [{"name": "foo.txt"}]
            })
            received = await inventory_to_records.fetch_listing(self.session, self.url)
            assert received == (["a/", "b/"], [{"name": "foo.txt"}])

    async def test_raises_valueerror_if_bad_json(self):
        with aioresponses() as m:
            m.get(self.url, payload={
                "prfixes": ["a/", "b/"],
            })
            with self.assertRaises(ValueError):
                await inventory_to_records.fetch_listing(self.session, self.url)

    async def test_raises_valueerror_if_html(self):
        with aioresponses() as m:
            m.get(self.url, body="<html></html>")
            with self.assertRaises(ValueError):
                await inventory_to_records.fetch_listing(self.session, self.url)


class CsvToRecordsTest(asynctest.TestCase):
    def test_load_simple_file(self):
        filename = os.path.join(here, 'data', 'inventory-simple.csv')
        stdout = io.StringIO()

        future = inventory_to_records.csv_to_records(self.loop, filename, stdout)
        self.loop.run_until_complete(future)

        output = stdout.getvalue()
        records = [json.loads(o) for o in output.split('\n') if o]
        assert records == [{
            'id': 'firefox_nightly_2017-05-15-10-02-38_55-0a1_linux-x86_64_en-us',
            'build': {
                'id': '20170515100238',
                'date': '2017-05-15T10:02:38Z'
            },
            'source': {
                'product': 'firefox',
                'revision': 'e66dedabe582ba7b394aee4f89ed70fe389b3c46',
                'repository': 'https://hg.mozilla.org/mozilla-central',
                'tree': 'mozilla-central'
            },
            'target': {
                'platform': 'linux-x86_64',
                'locale': 'en-US',
                'version': '55.0a1',
                'channel': 'nightly'
            },
            'download': {
                'url': ('https://archive.mozilla.org/pub/firefox/nightly/'
                        '2017/05/2017-05-15-10-02-38-mozilla-central/'
                        'firefox-55.0a1.en-US.linux-x86_64.tar.bz2'),
                'mimetype': 'application/x-bzip2',
                'size': 50000,
                'date': '2017-06-02T12:20:00Z'
            }
        }, {
            'id': 'firefox_52-0_linux-x86_64_fr',
            'build': {
                'id': '20170302120751',
                'date': '2017-03-02T12:07:51Z'
            },
            'source': {
                'product': 'firefox',
                'revision': '44d6a57ab554308585a67a13035d31b264be781e',
                'repository': 'https://hg.mozilla.org/releases/mozilla-release',
                'tree': 'releases/mozilla-release'
            },
            'target': {
                'platform': 'linux-x86_64',
                'locale': 'fr',
                'version': '52.0',
                'channel': 'release'
            },
            'download': {
                'url': ('https://archive.mozilla.org/pub/firefox/releases/52.0/'
                        'linux-x86_64/fr/firefox-52.0.tar.bz2'),
                'mimetype': 'application/x-bzip2',
                'size': 60000,
                'date': '2017-06-02T15:20:00Z'
            }
        }]
