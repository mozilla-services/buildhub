from unittest import mock

import asynctest
from aioresponses import aioresponses

from buildhub import utils, inventory_to_records, lambda_s3_event


def fake_event(key):
    return {
        "eventTime": "2017-08-08T17:06:52.030Z",
        "Records": [{
            "s3": {
                "bucket": {"name": "abc"},
                "object": {
                    "key": key,
                    "size": 51001024
                }
            }
        }]
    }


class FromArchive(asynctest.TestCase):
    remote_content = {
        "pub/firefox/candidates/": {
            "prefixes": [
                "54.0-candidates/",
                "archived/"
            ], "files": []
        },
        "pub/firefox/candidates/54.0-candidates/": {
            "prefixes": [
                "build1/",
                "build2/",
            ], "files": []
        },
        "pub/firefox/candidates/54.0-candidates/build2/win64/en-US/": {
            "prefixes": [], "files": [
                {"name": "firefox-54.0.zip"},
                {"name": "firefox-54.0.json"},
            ]
        },
        "pub/firefox/candidates/54.0-candidates/build2/win64/en-US/firefox-54.0.json": {
            "as": "ml64.exe",
            "buildid": "20170608105825",
            "cc": "c:/builds/moz2_slave/m-rel-w64-00000000000000000000/build/src/"
                  "vs2015u3/VC/bin/amd64/cl.exe",
            "cxx": "c:/builds/moz2_slave/m-rel-w64-00000000000000000000/build/src/"
                   "vs2015u3/VC/bin/amd64/cl.exe",
            "host_alias": "x86_64-pc-mingw32",
            "host_cpu": "x86_64",
            "host_os": "mingw32",
            "host_vendor": "pc",
            "moz_app_id": "{ec8030f7-c20a-464f-9b0e-13a3a9e97384}",
            "moz_app_maxversion": "54.*",
            "moz_app_name": "firefox",
            "moz_app_vendor": "Mozilla",
            "moz_app_version": "54.0",
            "moz_pkg_platform": "win64",
            "moz_source_repo": "MOZ_SOURCE_REPO=https://hg.mozilla.org/releases/mozilla-release",
            "moz_source_stamp": "e832ed037a3c23004be73178e546d240e57b6ee1",
            "moz_update_channel": "release",
            "target_alias": "x86_64-pc-mingw32",
            "target_cpu": "x86_64",
            "target_os": "mingw32",
            "target_vendor": "pc"
        },
        "pub/firefox/nightly/2017/08/2017-08-05-10-03-34-mozilla-central/"
        "firefox-57.0a1.en-US.win32.json": {
            "as": "ml.exe",
            "buildid": "20170805100334",
            "cc": "z:/build/build/src/vs2015u3/VC/bin/amd64_x86/cl.exe",
            "cxx": "z:/build/build/src/vs2015u3/VC/bin/amd64_x86/cl.exe",
            "host_alias": "i686-pc-mingw32",
            "host_cpu": "i686",
            "host_os": "mingw32",
            "host_vendor": "pc",
            "moz_app_id": "{ec8030f7-c20a-464f-9b0e-13a3a9e97384}",
            "moz_app_maxversion": "57.0a1",
            "moz_app_name": "firefox",
            "moz_app_vendor": "Mozilla",
            "moz_app_version": "57.0a1",
            "moz_pkg_platform": "win32",
            "moz_source_repo": "MOZ_SOURCE_REPO=https://hg.mozilla.org/mozilla-central",
            "moz_source_stamp": "933a04a91ce3bd44b230937083a835cb60637084",
            "moz_update_channel": "nightly",
            "target_alias": "i686-pc-mingw32",
            "target_cpu": "i686",
            "target_os": "mingw32",
            "target_vendor": "pc"
        },
        "pub/firefox/candidates/51.0-candidates/build1/linux-x86_64/en-US/firefox-51.0.json": {
            "as": "$(CC)",
            "buildid": "20170116133120",
            "cc": "/builds/slave/m-rel-l64-00000000000000000000/build/src/"
                  "gcc/bin/gcc -std=gnu99",
            "cxx": "/builds/slave/m-rel-l64-00000000000000000000/"
                   "build/src/gcc/bin/g++ -std=gnu++11",
            "host_alias": "x86_64-pc-linux-gnu",
            "host_cpu": "x86_64",
            "host_os": "linux-gnu",
            "host_vendor": "pc",
            "ld": "ld",
            "moz_app_id": "{ec8030f7-c20a-464f-9b0e-13a3a9e97384}",
            "moz_app_maxversion": "51.*",
            "moz_app_name": "firefox",
            "moz_app_vendor": "Mozilla",
            "moz_app_version": "51.0",
            "moz_pkg_platform": "linux-x86_64",
            "moz_source_repo": "MOZ_SOURCE_REPO=https://hg.mozilla.org/releases/mozilla-release",
            "moz_source_stamp": "85d16b0be539271da6484435f71c562acd9c3c56",
            "moz_update_channel": "release",
            "target_alias": "x86_64-pc-linux-gnu",
            "target_cpu": "x86_64",
            "target_os": "linux-gnu",
            "target_vendor": "pc"
        }

    }

    def setUp(self):
        patch = mock.patch("buildhub.lambda_s3_event.kinto_http.Client.create_record")
        self.addCleanup(patch.stop)
        self.mock_create_record = patch.start()

        mocked = aioresponses()
        mocked.start()
        for url, payload in self.remote_content.items():
            mocked.get(utils.ARCHIVE_URL + url, payload=payload)
        self.addCleanup(mocked.stop)

    def tearDown(self):
        inventory_to_records._candidates_build_folder.clear()

    async def test_from_release_archive_before_metadata(self):
        event = fake_event("pub/firefox/releases/55.0/mac/ar/Firefox 55.0.dmg")
        await lambda_s3_event.main(self.loop, event)

        assert not self.mock_create_record.called

    async def test_from_nightly_archive_before_metadata(self):
        event = fake_event("pub/firefox/nightly/2016/05/2016-05-02-03-02-07-"
                           "mozilla-central-l10n/firefox-49.0a1.ast.linux-i686.tar.bz2")
        await lambda_s3_event.main(self.loop, event)

        assert not self.mock_create_record.called

    async def test_from_rc_archive_before_metadata(self):
        event = fake_event("pub/firefox/candidates/56.0b1-candidates/build5/mac-EME-free/"
                           "de/Firefox 56.0b1.dmg")
        await lambda_s3_event.main(self.loop, event)

        assert not self.mock_create_record.called

    async def test_from_non_archive_files(self):
        event = fake_event("pub/firefox/releases/54.0.1-funnelcake117/win32/en-US/"
                           "Firefox Setup 54.0.1.exe.asc")
        await lambda_s3_event.main(self.loop, event)

        assert not self.mock_create_record.called

    async def test_from_unknown_product(self):
        event = fake_event("pub/calendar/releases/1.0b1/linux-x86_64/en-US/sunbird-1.0b1.tar.bz2")
        await lambda_s3_event.main(self.loop, event)

        assert not self.mock_create_record.called

    async def test_from_unrelated_files(self):
        event = fake_event("favicon.ico")
        await lambda_s3_event.main(self.loop, event)

        assert not self.mock_create_record.called

    async def test_from_release_archive(self):
        event = fake_event("pub/firefox/releases/54.0/win64/fr/Firefox Setup 54.0.exe")
        await lambda_s3_event.main(self.loop, event)

        self.mock_create_record.assert_called_with(
            bucket='build-hub',
            collection='releases',
            data={
                'id': 'firefox_54-0_win64_fr',
                'source': {
                    'product': 'firefox',
                    'revision': 'e832ed037a3c23004be73178e546d240e57b6ee1',
                    'repository': 'https://hg.mozilla.org/releases/mozilla-release',
                    'tree': 'releases/mozilla-release'
                },
                'build': {
                    'id': '20170608105825',
                    'date': '2017-06-08T10:58:25Z',
                    'number': 2
                },
                'target': {
                    'platform': 'win64',
                    'os': 'win',
                    'locale': 'fr',
                    'version': '54.0',
                    'channel': 'release'
                },
                'download': {
                    'url': 'https://archive.mozilla.org/pub/firefox/releases/54.0/'
                           'win64/fr/Firefox Setup 54.0.exe',
                    'mimetype': 'application/msdos-windows',
                    'size': 51001024,
                    'date': '2017-08-08T17:06:52Z'
                },
            },
            if_not_exists=True)

    async def test_from_nightly_archive(self):
        event = fake_event("pub/firefox/nightly/2017/08/2017-08-05-10-03-34-"
                           "mozilla-central-l10n/firefox-57.0a1.ru.win32.zip")
        await lambda_s3_event.main(self.loop, event)

        self.mock_create_record.assert_called_with(
            bucket='build-hub',
            collection='releases',
            data={
                'id': 'firefox_nightly_2017-08-05-10-03-34_57-0a1_win32_ru',
                'source': {
                    'product': 'firefox',
                    'revision': '933a04a91ce3bd44b230937083a835cb60637084',
                    'repository': 'https://hg.mozilla.org/mozilla-central',
                    'tree': 'mozilla-central'
                },
                'build': {
                    'id': '20170805100334',
                    'date': '2017-08-05T10:03:34Z'
                },
                'target': {
                    'platform': 'win32',
                    'os': 'win',
                    'locale': 'ru',
                    'version': '57.0a1',
                    'channel': 'nightly'
                },
                'download': {
                    'url': 'https://archive.mozilla.org/pub/firefox/nightly/2017/08/'
                           '2017-08-05-10-03-34-mozilla-central-l10n/firefox-57.0a1.ru.win32.zip',
                    'mimetype': 'application/zip',
                    'size': 51001024,
                    'date': '2017-08-08T17:06:52Z'
                },
            },
            if_not_exists=True)

    async def test_from_rc_archive(self):
        event = fake_event("pub/firefox/candidates/51.0-candidates/build1/linux-x86_64-EME-free/"
                           "zh-TW/firefox-51.0.tar.bz2")
        await lambda_s3_event.main(self.loop, event)

        self.mock_create_record.assert_called_with(
            bucket='build-hub',
            collection='releases',
            data={
                'id': 'firefox_51-0rc1_linux-x86_64-eme-free_zh-tw',
                'source': {
                    'product': 'firefox',
                    'revision': '85d16b0be539271da6484435f71c562acd9c3c56',
                    'repository': 'https://hg.mozilla.org/releases/mozilla-release',
                    'tree': 'releases/mozilla-release'
                },
                'build': {
                    'id': '20170116133120',
                    'date': '2017-01-16T13:31:20Z',
                    'number': 1
                },
                'target': {
                    'platform': 'linux-x86_64-eme-free',
                    'os': 'linux',
                    'locale': 'zh-TW',
                    'version': '51.0rc1',
                    'channel': 'release'
                },
                'download': {
                    'url': 'https://archive.mozilla.org/pub/firefox/candidates/51.0-candidates/'
                           'build1/linux-x86_64-EME-free/zh-TW/firefox-51.0.tar.bz2',
                    'mimetype': 'application/x-bzip2',
                    'size': 51001024,
                    'date': '2017-08-08T17:06:52Z'
                },
            },
            if_not_exists=True)
