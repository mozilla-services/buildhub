import asyncio
import os
import io
import json

import aiohttp
import asynctest
from aioresponses import aioresponses

from buildhub import inventory_to_records, utils


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


class FetchNightlyMetadata(asynctest.TestCase):
    async def setUp(self):
        self.session = aiohttp.ClientSession(loop=self.loop)
        self.addCleanup(self.session.close)

    async def test_fetch_nightly_metadata(self):
        record = {"id": "a", "download": {"url": "http://server.org/firefox.fr.win32.exe"}}

        with aioresponses() as m:
            m.get("http://server.org/firefox.en-US.win32.json", payload={
                "buildid": "20170512"
            })
            received = await inventory_to_records.fetch_nightly_metadata(self.session,
                                                                         record)
        assert received == {"buildid": "20170512"}

    async def test_does_not_hit_server_if_already_known(self):
        record = {"id": "a", "download": {"url": "http://server.org/firefox.fr.win32.exe"}}

        with aioresponses() as m:
            m.get("http://server.org/firefox.en-US.win32.json", payload={
                "buildid": "20170512"
            })
            await inventory_to_records.fetch_nightly_metadata(self.session, record)

        record["download"]["url"] = record["download"]["url"].replace(".fr.", ".it.")
        # Now cached, no need to mock HTTP responses.
        received = await inventory_to_records.fetch_nightly_metadata(self.session, record)
        assert received == {"buildid": "20170512"}

    async def test_returns_none_if_not_available(self):
        record = {"id": "a", "download": {"url": "http://archive.org/firefox.fr.win32.exe"}}
        # XXX: add ability to mock server.org/* on pnuckowski/aioresponses
        received = await inventory_to_records.fetch_nightly_metadata(self.session, record)
        assert received is None

    async def test_fetch_nightly_metadata_from_installer_url(self):
        record = {"id": "a", "download": {
            "url": "http://server.org/firefox.fr.win64.installer.exe"}}

        with aioresponses() as m:
            m.get("http://server.org/firefox.en-US.win64.json", payload={
                "buildid": "20170512"
            })
            received = await inventory_to_records.fetch_nightly_metadata(self.session,
                                                                         record)
        assert received == {"buildid": "20170512"}


class FetchReleaseMetadata(asynctest.TestCase):
    async def setUp(self):
        self.session = aiohttp.ClientSession(loop=self.loop)
        self.addCleanup(self.session.close)

        inventory_to_records._candidates_build_folder["firefox"] = {"54.0": "build3/"}
        self.record = {
            "source": {"product": "firefox"},
            "target": {"version": "54.0", "platform": "win64", "locale": "fr-FR"}
        }

    def tearDown(self):
        inventory_to_records._candidates_build_folder.clear()
        inventory_to_records._release_metadata.clear()

    async def test_fetch_release_metadata_unknown_version(self):
        result = await inventory_to_records.fetch_release_metadata(self.session, {
            "source": {"product": "firefox"},
            "target": {"version": "1.0", "platform": "p"}})
        assert result is None

    async def test_fetch_release_metadata(self):
        archive_url = utils.ARCHIVE_URL + "pub/firefox/candidates/"
        with aioresponses() as m:
            candidate_folder = archive_url + "54.0-candidates/build3/win64/en-US/"
            m.get(candidate_folder, payload={
                "prefixes": [], "files": [
                    {"name": "firefox-54.0.json"}
                ]
            })
            m.get(candidate_folder + "firefox-54.0.json", payload={"buildid": "20170512"})
            received = await inventory_to_records.fetch_release_metadata(self.session, self.record)
            assert received == {
                "buildid": "20170512"
            }
        # Now cached, no need to mock HTTP responses.
        received = await inventory_to_records.fetch_release_metadata(self.session, self.record)
        assert received == {"buildid": "20170512"}

    async def test_fetch_release_metadata_failing(self):
        archive_url = utils.ARCHIVE_URL + "pub/firefox/candidates/"
        with aioresponses() as m:
            candidate_folder = archive_url + "54.0-candidates/build3/win64/en-US/"
            m.get(candidate_folder, payload={
                "prefixes": [], "files": [
                    {"name": "only-a-random-file.json"}
                ]
            })
            with self.assertRaises(ValueError):
                await inventory_to_records.fetch_release_metadata(self.session, self.record)


class ScanCandidates(asynctest.TestCase):
    async def setUp(self):
        self.session = aiohttp.ClientSession(loop=self.loop)
        self.addCleanup(self.session.close)

    def tearDown(self):
        inventory_to_records._candidates_build_folder.clear()

    async def test_scan_candidates_does_nothing_if_already_done(self):
        inventory_to_records._candidates_build_folder["firefox"] = {}
        await inventory_to_records.scan_candidates(self.session, "firefox")

    async def test_scan_candidates(self):
        with aioresponses() as m:
            candidates_listing = utils.ARCHIVE_URL + "pub/firefox/candidates/"
            m.get(candidates_listing, payload={
                "prefixes": [
                    "54.0-candidates/",
                    "52.0.2esr-candidates/",
                    "archived/"
                ], "files": []
            })
            m.get(candidates_listing + "52.0.2esr-candidates/", payload={
                "prefixes": [
                    "build1/",
                    "build2/",
                    "build3/",
                ], "files": []
            })
            m.get(candidates_listing + "54.0-candidates/", payload={
                "prefixes": [
                    "build1/",
                ], "files": []
            })
            await inventory_to_records.scan_candidates(self.session, "firefox")

            assert inventory_to_records._candidates_build_folder == {
                "firefox": {
                    "54.0": "build1/",
                    "52.0.2esr": "build3/",
                }
            }


class CsvToRecordsTest(asynctest.TestCase):
    def test_load_simple_file(self):
        filename = os.path.join(here, 'data', 'inventory-simple.csv')
        stdout = io.StringIO()
        with open(filename, "r") as stdin:
            future = inventory_to_records.csv_to_records(self.loop, stdin, stdout)
            self.loop.run_until_complete(future)

        output = stdout.getvalue()
        records = [json.loads(o) for o in output.split('\n') if o]
        assert records == [{
            "data": {
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
                    'date': '2017-06-02T12:20:10Z'
                }
            }
        }, {
            "data": {
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
                    'date': '2017-06-02T15:20:10Z'
                }
            }
        }]
