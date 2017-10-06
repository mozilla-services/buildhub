from unittest import mock

import asynctest
from aioresponses import aioresponses

from buildhub import utils, inventory_to_records, lambda_s3_event


def fake_event(key):
    return {
        'Records': [{
            'eventTime': '2017-08-08T17:06:52.030Z',
            's3': {
                'bucket': {'name': 'abc'},
                'object': {
                    'key': key,
                    'size': 51001024
                }
            }
        }]
    }


class BaseTest(asynctest.TestCase):

    remote_content = {}

    def setUp(self):
        patch = mock.patch('buildhub.lambda_s3_event.kinto_http.Client.create_record')
        self.addCleanup(patch.stop)
        self.mock_create_record = patch.start()

        mocked = aioresponses()
        mocked.start()
        for url, payload in self.remote_content.items():
            mocked.get(utils.ARCHIVE_URL + url, payload=payload)
        self.addCleanup(mocked.stop)

    def tearDown(self):
        inventory_to_records._candidates_build_folder.clear()


class FromArchiveFirefox(BaseTest):
    remote_content = {
        'pub/firefox/candidates/': {
            'prefixes': [
                '54.0-candidates/',
                'archived/'
            ], 'files': []
        },
        'pub/firefox/candidates/54.0-candidates/': {
            'prefixes': [
                'build1/',
                'build2/',
            ], 'files': []
        },
        'pub/firefox/candidates/54.0-candidates/build2/win64/en-US/': {
            'prefixes': [], 'files': [
                {'name': 'firefox-54.0.zip'},
                {'name': 'firefox-54.0.json'},
            ]
        },
        'pub/firefox/candidates/54.0-candidates/build2/win64/en-US/firefox-54.0.json': {
            'as': 'ml64.exe',
            'buildid': '20170608105825',
            'cc': 'c:/builds/moz2_slave/m-rel-w64-00000000000000000000/build/src/'
                  'vs2015u3/VC/bin/amd64/cl.exe',
            'cxx': 'c:/builds/moz2_slave/m-rel-w64-00000000000000000000/build/src/'
                   'vs2015u3/VC/bin/amd64/cl.exe',
            'host_alias': 'x86_64-pc-mingw32',
            'host_cpu': 'x86_64',
            'host_os': 'mingw32',
            'host_vendor': 'pc',
            'moz_app_id': '{ec8030f7-c20a-464f-9b0e-13a3a9e97384}',
            'moz_app_maxversion': '54.*',
            'moz_app_name': 'firefox',
            'moz_app_vendor': 'Mozilla',
            'moz_app_version': '54.0',
            'moz_pkg_platform': 'win64',
            'moz_source_repo': 'MOZ_SOURCE_REPO=https://hg.mozilla.org/releases/mozilla-release',
            'moz_source_stamp': 'e832ed037a3c23004be73178e546d240e57b6ee1',
            'moz_update_channel': 'release',
            'target_alias': 'x86_64-pc-mingw32',
            'target_cpu': 'x86_64',
            'target_os': 'mingw32',
            'target_vendor': 'pc'
        },
        'pub/firefox/nightly/2017/08/2017-08-05-10-03-34-mozilla-central/'
        'firefox-57.0a1.en-US.win32.json': {
            'as': 'ml.exe',
            'buildid': '20170805100334',
            'cc': 'z:/build/build/src/vs2015u3/VC/bin/amd64_x86/cl.exe',
            'cxx': 'z:/build/build/src/vs2015u3/VC/bin/amd64_x86/cl.exe',
            'host_alias': 'i686-pc-mingw32',
            'host_cpu': 'i686',
            'host_os': 'mingw32',
            'host_vendor': 'pc',
            'moz_app_id': '{ec8030f7-c20a-464f-9b0e-13a3a9e97384}',
            'moz_app_maxversion': '57.0a1',
            'moz_app_name': 'firefox',
            'moz_app_vendor': 'Mozilla',
            'moz_app_version': '57.0a1',
            'moz_pkg_platform': 'win32',
            'moz_source_repo': 'MOZ_SOURCE_REPO=https://hg.mozilla.org/mozilla-central',
            'moz_source_stamp': '933a04a91ce3bd44b230937083a835cb60637084',
            'moz_update_channel': 'nightly',
            'target_alias': 'i686-pc-mingw32',
            'target_cpu': 'i686',
            'target_os': 'mingw32',
            'target_vendor': 'pc'
        },
        'pub/firefox/candidates/51.0-candidates/build1/linux-x86_64/en-US/firefox-51.0.json': {
            'as': '$(CC)',
            'buildid': '20170116133120',
            'cc': '/builds/slave/m-rel-l64-00000000000000000000/build/src/'
                  'gcc/bin/gcc -std=gnu99',
            'cxx': '/builds/slave/m-rel-l64-00000000000000000000/'
                   'build/src/gcc/bin/g++ -std=gnu++11',
            'host_alias': 'x86_64-pc-linux-gnu',
            'host_cpu': 'x86_64',
            'host_os': 'linux-gnu',
            'host_vendor': 'pc',
            'ld': 'ld',
            'moz_app_id': '{ec8030f7-c20a-464f-9b0e-13a3a9e97384}',
            'moz_app_maxversion': '51.*',
            'moz_app_name': 'firefox',
            'moz_app_vendor': 'Mozilla',
            'moz_app_version': '51.0',
            'moz_pkg_platform': 'linux-x86_64',
            'moz_source_repo': 'MOZ_SOURCE_REPO=https://hg.mozilla.org/releases/mozilla-release',
            'moz_source_stamp': '85d16b0be539271da6484435f71c562acd9c3c56',
            'moz_update_channel': 'release',
            'target_alias': 'x86_64-pc-linux-gnu',
            'target_cpu': 'x86_64',
            'target_os': 'linux-gnu',
            'target_vendor': 'pc'
        }

    }

    async def test_from_release_archive_before_metadata(self):
        event = fake_event('pub/firefox/releases/55.0/mac/ar/Firefox 55.0.dmg')
        await lambda_s3_event.main(self.loop, event)

        assert not self.mock_create_record.called

    async def test_from_nightly_archive_before_metadata(self):
        event = fake_event('pub/firefox/nightly/2016/05/2016-05-02-03-02-07-'
                           'mozilla-central-l10n/firefox-49.0a1.ast.linux-i686.tar.bz2')
        await lambda_s3_event.main(self.loop, event)

        assert not self.mock_create_record.called

    async def test_from_rc_archive_before_metadata(self):
        event = fake_event('pub/firefox/candidates/56.0b1-candidates/build5/mac-EME-free/'
                           'de/Firefox 56.0b1.dmg')
        await lambda_s3_event.main(self.loop, event)

        assert not self.mock_create_record.called

    async def test_from_non_archive_files(self):
        event = fake_event('pub/firefox/releases/54.0.1-funnelcake117/win32/en-US/'
                           'Firefox Setup 54.0.1.exe.asc')
        await lambda_s3_event.main(self.loop, event)

        assert not self.mock_create_record.called

    async def test_from_unknown_product(self):
        event = fake_event('pub/calendar/releases/1.0b1/linux-x86_64/en-US/sunbird-1.0b1.tar.bz2')
        await lambda_s3_event.main(self.loop, event)

        assert not self.mock_create_record.called

    async def test_from_unrelated_files(self):
        event = fake_event('favicon.ico')
        await lambda_s3_event.main(self.loop, event)

        assert not self.mock_create_record.called

    async def test_from_release_archive(self):
        event = fake_event('pub/firefox/releases/54.0/win64/fr/Firefox Setup 54.0.exe')
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
                    'number': 2,
                    'as': 'ml64.exe',
                    'cc': 'c:/builds/moz2_slave/m-rel-w64-00000000000000000000/build/src/'
                          'vs2015u3/VC/bin/amd64/cl.exe',
                    'cxx': 'c:/builds/moz2_slave/m-rel-w64-00000000000000000000/build/src/'
                           'vs2015u3/VC/bin/amd64/cl.exe',
                    'host': 'x86_64-pc-mingw32',
                    'target': 'x86_64-pc-mingw32',
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
        event = fake_event('pub/firefox/nightly/2017/08/2017-08-05-10-03-34-'
                           'mozilla-central-l10n/firefox-57.0a1.ru.win32.zip')
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
                    'date': '2017-08-05T10:03:34Z',
                    'as': 'ml.exe',
                    'cc': 'z:/build/build/src/vs2015u3/VC/bin/amd64_x86/cl.exe',
                    'cxx': 'z:/build/build/src/vs2015u3/VC/bin/amd64_x86/cl.exe',
                    'host': 'i686-pc-mingw32',
                    'target': 'i686-pc-mingw32',
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
        event = fake_event('pub/firefox/candidates/51.0-candidates/build1/linux-x86_64-EME-free/'
                           'zh-TW/firefox-51.0.tar.bz2')
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
                    'number': 1,
                    'as': '$(CC)',
                    'cc': '/builds/slave/m-rel-l64-00000000000000000000/build/src/'
                          'gcc/bin/gcc -std=gnu99',
                    'cxx': '/builds/slave/m-rel-l64-00000000000000000000/'
                           'build/src/gcc/bin/g++ -std=gnu++11',
                    'host': 'x86_64-pc-linux-gnu',
                    'target': 'x86_64-pc-linux-gnu',
                    'ld': 'ld'
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


class FromRCMetadataFirefox(BaseTest):
    remote_content = {
        'pub/firefox/candidates/56.0b1-candidates/build4/linux-x86_64/': {
            'prefixes': [
                'es-ES/',
                'ca/',
                'en-US/',
                'xpi/',
            ], 'files': [],
        },
        'pub/firefox/candidates/56.0b1-candidates/build4/linux-x86_64/xpi/': {
            'prefixes': [], 'files': [
                {'name': 'en-US.xpi'}
            ]
        },
        'pub/firefox/candidates/56.0b1-candidates/build4/linux-x86_64/ca/': {
            'prefixes': [], 'files': [{
                'name': 'firefox-56.0b1.tar.bz2',
                'last_modified': '2017-08-03T20:55:11Z',
                'size': 34138800
            }]
        },
        'pub/firefox/candidates/56.0b1-candidates/build4/linux-x86_64/en-US/': {
            'prefixes': [], 'files': [{
                'name': 'firefox-56.0b1.tar.bz2',
                'last_modified': '2017-08-03T20:55:11Z',
                'size': 34138800
            }]
        },
        'pub/firefox/candidates/56.0b1-candidates/build4/linux-x86_64/es-ES/': {
            'prefixes': [], 'files': [
                {'name': 'firefox-56.0b1.checksums'}
            ]
        },
        'pub/firefox/candidates/56.0b1-candidates/build4/linux-x86_64/en-US/'
        'firefox-56.0b1.json': {
            'as': '$(CC)',
            'buildid': '20170808170225',
            'cc': '/usr/bin/ccache /home/worker/workspace/build/src/gcc/bin/gcc -std=gnu99',
            'cxx': '/usr/bin/ccache /home/worker/workspace/build/src/gcc/bin/g++ -std=gnu++11',
            'host_alias': 'x86_64-pc-linux-gnu',
            'host_cpu': 'x86_64',
            'host_os': 'linux-gnu',
            'host_vendor': 'pc',
            'moz_app_id': '{ec8030f7-c20a-464f-9b0e-13a3a9e97384}',
            'moz_app_maxversion': '56.*',
            'moz_app_name': 'firefox',
            'moz_app_vendor': 'Mozilla',
            'moz_app_version': '56.0',
            'moz_pkg_platform': 'linux-x86_64',
            'moz_source_repo': 'MOZ_SOURCE_REPO=https://hg.mozilla.org/releases/mozilla-beta',
            'moz_source_stamp': 'da6760885a24e03e13f3b566f319fc255dbb4027',
            'moz_update_channel': 'beta',
            'target_alias': 'x86_64-pc-linux-gnu',
            'target_cpu': 'x86_64',
            'target_os': 'linux-gnu',
            'target_vendor': 'pc'
        }
    }

    async def test_pick_rc_and_locales(self):
        event = fake_event('pub/firefox/candidates/56.0b1-candidates/build4/linux-x86_64/'
                           'en-US/firefox-56.0b1.json')
        await lambda_s3_event.main(self.loop, event)

        assert self.mock_create_record.call_count == 2

        self.mock_create_record.assert_any_call(
            bucket='build-hub',
            collection='releases',
            data={
                'id': 'firefox_beta_56-0b1rc4_linux-x86_64_en-us',
                'source': {
                    'product': 'firefox',
                    'revision': 'da6760885a24e03e13f3b566f319fc255dbb4027',
                    'repository': 'https://hg.mozilla.org/releases/mozilla-beta',
                    'tree': 'releases/mozilla-beta'
                },
                'build': {
                    'id': '20170808170225',
                    'date': '2017-08-08T17:02:25Z',
                    'number': 4,
                    'as': '$(CC)',
                    'cc': '/usr/bin/ccache /home/worker/workspace/build/src/gcc/'
                          'bin/gcc -std=gnu99',
                    'cxx': '/usr/bin/ccache /home/worker/workspace/build/src/gcc/'
                           'bin/g++ -std=gnu++11',
                    'host': 'x86_64-pc-linux-gnu',
                    'target': 'x86_64-pc-linux-gnu',
                },
                'target': {
                    'platform': 'linux-x86_64',
                    'os': 'linux',
                    'locale': 'en-US',
                    'version': '56.0b1rc4',
                    'channel': 'beta'
                },
                'download': {
                    'url': 'https://archive.mozilla.org/pub/firefox/candidates/56.0b1-candidates/'
                           'build4/linux-x86_64/en-US/firefox-56.0b1.tar.bz2',
                    'mimetype': 'application/x-bzip2',
                    'size': 34138800,
                    'date': '2017-08-03T20:55:11Z'
                },
            },
            if_not_exists=True)

        self.mock_create_record.assert_any_call(
            bucket='build-hub',
            collection='releases',
            data={
                'id': 'firefox_beta_56-0b1rc4_linux-x86_64_ca',
                'source': {
                    'product': 'firefox',
                    'revision': 'da6760885a24e03e13f3b566f319fc255dbb4027',
                    'repository': 'https://hg.mozilla.org/releases/mozilla-beta',
                    'tree': 'releases/mozilla-beta'
                },
                'build': {
                    'id': '20170808170225',
                    'date': '2017-08-08T17:02:25Z',
                    'number': 4,
                    'as': '$(CC)',
                    'cc': '/usr/bin/ccache /home/worker/workspace/build/src/gcc/'
                          'bin/gcc -std=gnu99',
                    'cxx': '/usr/bin/ccache /home/worker/workspace/build/src/gcc/'
                           'bin/g++ -std=gnu++11',
                    'host': 'x86_64-pc-linux-gnu',
                    'target': 'x86_64-pc-linux-gnu',
                },
                'target': {
                    'platform': 'linux-x86_64',
                    'os': 'linux',
                    'locale': 'ca',
                    'version': '56.0b1rc4',
                    'channel': 'beta'
                },
                'download': {
                    'url': 'https://archive.mozilla.org/pub/firefox/candidates/56.0b1-candidates/'
                           'build4/linux-x86_64/ca/firefox-56.0b1.tar.bz2',
                    'mimetype': 'application/x-bzip2',
                    'size': 34138800,
                    'date': '2017-08-03T20:55:11Z'
                },
            },
            if_not_exists=True)


class FromNightlyMetadataFirefox(BaseTest):
    remote_content = {
        'pub/firefox/nightly/2017/08/2017-08-05-10-03-34-mozilla-central-l10n/': {
            'prefixes': [], 'files': [{
                'name': 'firefox-57.0a1.ru.linux-i686.tar.bz2',
                'last_modified': '2017-08-03T20:55:11Z',
                'size': 34138800
            }, {
                'name': 'firefox-57.0a1.ru.linux-i686.tar.bz2.asc'
            }, {
                'name': 'firefox-57.0a1.ru.linux-x86_64.tar.bz2',
                'last_modified': '2017-08-03T20:55:11Z',
                'size': 34138800
            }, {
                'name': 'firefox-57.0a1.ru.linux-x86_64.tar.bz2.asc'
            }, {
                'name': 'firefox-57.0a1.pt-PT.linux-x86_64.tar.bz2',
                'last_modified': '2017-08-03T20:55:11Z',
                'size': 34138800
            }]
        },
        'pub/firefox/nightly/2017/08/2017-08-09-10-03-26-mozilla-central/': {
            'prefixes': [], 'files': []
        },
        'pub/firefox/nightly/2017/08/2017-08-05-10-03-34-mozilla-central/': {
            'prefixes': [], 'files': [{
                'name': 'firefox-57.0a1.en-US.linux-x86_64.tar.bz2',
                'last_modified': '2017-08-03T20:55:11Z',
                'size': 34138800
            }, {
                'name': 'firefox-57.0a1.en-US.win32.zip',
                'last_modified': '2017-08-03T20:55:11Z',
                'size': 34138800
            }, {
                'name': 'firefox-57.0a1.en-US.mac.dmg',
                'last_modified': '2017-08-03T20:55:11Z',
                'size': 34138800
            }]
        },
        # Metadata.
        'pub/firefox/nightly/2017/08/2017-08-05-10-03-34-mozilla-central/'
        'firefox-57.0a1.en-US.linux-x86_64.json': {
            'as': '$(CC)',
            'buildid': '20170805100334',
            'cc': '/usr/bin/ccache /home/worker/workspace/build/src/gcc/bin/gcc -std=gnu99',
            'cxx': '/usr/bin/ccache /home/worker/workspace/build/src/gcc/bin/g++ -std=gnu++11',
            'host_alias': 'x86_64-pc-linux-gnu',
            'host_cpu': 'x86_64',
            'host_os': 'linux-gnu',
            'host_vendor': 'pc',
            'moz_app_id': '{ec8030f7-c20a-464f-9b0e-13a3a9e97384}',
            'moz_app_maxversion': '57.0a1',
            'moz_app_name': 'firefox',
            'moz_app_vendor': 'Mozilla',
            'moz_app_version': '57.0a1',
            'moz_pkg_platform': 'linux-x86_64',
            'moz_source_repo': 'MOZ_SOURCE_REPO=https://hg.mozilla.org/mozilla-central',
            'moz_source_stamp': '933a04a91ce3bd44b230937083a835cb60637084',
            'moz_update_channel': 'nightly',
            'target_alias': 'x86_64-pc-linux-gnu',
            'target_cpu': 'x86_64',
            'target_os': 'linux-gnu',
            'target_vendor': 'pc'
        },
        'pub/firefox/nightly/2017/08/2017-08-05-10-03-34-mozilla-central/'
        'firefox-57.0a1.en-US.win32.json': {
            'as': 'ml.exe',
            'buildid': '20170805100334',
            'cc': 'z:/build/build/src/vs2015u3/VC/bin/amd64_x86/cl.exe',
            'cxx': 'z:/build/build/src/vs2015u3/VC/bin/amd64_x86/cl.exe',
            'host_alias': 'i686-pc-mingw32',
            'host_cpu': 'i686',
            'host_os': 'mingw32',
            'host_vendor': 'pc',
            'moz_app_id': '{ec8030f7-c20a-464f-9b0e-13a3a9e97384}',
            'moz_app_maxversion': '57.0a1',
            'moz_app_name': 'firefox',
            'moz_app_vendor': 'Mozilla',
            'moz_app_version': '57.0a1',
            'moz_pkg_platform': 'win32',
            'moz_source_repo': 'MOZ_SOURCE_REPO=https://hg.mozilla.org/mozilla-central',
            'moz_source_stamp': '933a04a91ce3bd44b230937083a835cb60637084',
            'moz_update_channel': 'nightly',
            'target_alias': 'i686-pc-mingw32',
            'target_cpu': 'i686',
            'target_os': 'mingw32',
            'target_vendor': 'pc'
        },
        'pub/firefox/nightly/2017/08/2017-08-05-10-03-34-mozilla-central/'
        'firefox-57.0a1.en-US.mac.json': {
            'as': '$(CC)',
            'buildid': '20170805100334',
            'cc': '/usr/bin/ccache /home/worker/workspace/build/src/clang/bin/clang -target '
                  'x86_64-apple-darwin11 -B /home/worker/workspace/build/src/cctools/bin '
                  '-isysroot /home/worker/workspace/build/src/MacOSX10.7.sdk -std=gnu99',
            'cxx': '/usr/bin/ccache /home/worker/workspace/build/src/clang/bin/clang++ '
                   '-target x86_64-apple-darwin11 -B /home/worker/workspace/build/src/cctools/bin'
                   ' -isysroot /home/worker/workspace/build/src/MacOSX10.7.sdk -std=gnu++11',
            'host_alias': 'x86_64-pc-linux-gnu',
            'host_cpu': 'x86_64',
            'host_os': 'linux-gnu',
            'host_vendor': 'pc',
            'moz_app_id': '{ec8030f7-c20a-464f-9b0e-13a3a9e97384}',
            'moz_app_maxversion': '57.0a1',
            'moz_app_name': 'firefox',
            'moz_app_vendor': 'Mozilla',
            'moz_app_version': '57.0a1',
            'moz_pkg_platform': 'mac',
            'moz_source_repo': 'MOZ_SOURCE_REPO=https://hg.mozilla.org/mozilla-central',
            'moz_source_stamp': '933a04a91ce3bd44b230937083a835cb60637084',
            'moz_update_channel': 'nightly',
            'target_alias': 'x86_64-apple-darwin',
            'target_cpu': 'x86_64',
            'target_os': 'darwin',
            'target_vendor': 'apple'
        },
        'pub/firefox/nightly/2017/08/2017-08-09-10-03-26-mozilla-central/'
        'firefox-57.0a1.en-US.linux-i686.json': {
            'as': '$(CC)',
            'buildid': '20170809100326',
            'cc': '/usr/bin/ccache /home/worker/workspace/build/src/gcc/bin/gcc '
                  '-m32 -march=pentium-m -std=gnu99',
            'cxx': '/usr/bin/ccache /home/worker/workspace/build/src/gcc/bin/g++ '
                   '-m32 -march=pentium-m -std=gnu++11',
            'host_alias': 'i686-pc-linux-gnu',
            'host_cpu': 'i686',
            'host_os': 'linux-gnu',
            'host_vendor': 'pc',
            'moz_app_id': '{ec8030f7-c20a-464f-9b0e-13a3a9e97384}',
            'moz_app_maxversion': '57.0a1',
            'moz_app_name': 'firefox',
            'moz_app_vendor': 'Mozilla',
            'moz_app_version': '57.0a1',
            'moz_pkg_platform': 'linux-i686',
            'moz_source_repo': 'MOZ_SOURCE_REPO=https://hg.mozilla.org/mozilla-central',
            'moz_source_stamp': '4c5fbf49376351679dcc49f4cff26c3c2e055ccc',
            'moz_update_channel': 'nightly',
            'target_alias': 'i686-pc-linux-gnu',
            'target_cpu': 'i686',
            'target_os': 'linux-gnu',
            'target_vendor': 'pc'
        },
    }

    async def test_from_nightly_metadata_linux_release_missing(self):
        event = fake_event('pub/firefox/nightly/2017/08/2017-08-09-10-03-26-mozilla-central/'
                           'firefox-57.0a1.en-US.linux-i686.json')
        await lambda_s3_event.main(self.loop, event)

        assert not self.mock_create_record.called

    async def test_from_nightly_date_is_ignored(self):
        event = fake_event('firefox/nightly/2017/08/2017-08-01-15-03-43-date/'
                           'firefox-56.0a1.en-US.linux-i686.json')
        await lambda_s3_event.main(self.loop, event)

        assert not self.mock_create_record.called

    async def test_from_nightly_metadata_linux(self):
        event = fake_event('pub/firefox/nightly/2017/08/2017-08-05-10-03-34-mozilla-central/'
                           'firefox-57.0a1.en-US.linux-x86_64.json')
        await lambda_s3_event.main(self.loop, event)

        self.mock_create_record.assert_any_call(
            bucket='build-hub',
            collection='releases',
            data={
                'id': 'firefox_nightly_2017-08-05-10-03-34_57-0a1_linux-x86_64_en-us',
                'source': {
                    'product': 'firefox',
                    'revision': '933a04a91ce3bd44b230937083a835cb60637084',
                    'repository': 'https://hg.mozilla.org/mozilla-central',
                    'tree': 'mozilla-central'
                },
                'build': {
                    'id': '20170805100334',
                    'date': '2017-08-05T10:03:34Z',
                    'cc': '/usr/bin/ccache /home/worker/workspace/build/src/gcc/'
                          'bin/gcc -std=gnu99',
                    'cxx': '/usr/bin/ccache /home/worker/workspace/build/src/gcc/'
                           'bin/g++ -std=gnu++11',
                    'host': 'x86_64-pc-linux-gnu',
                    'as': '$(CC)',
                    'target': 'x86_64-pc-linux-gnu',
                },
                'target': {
                    'platform': 'linux-x86_64',
                    'os': 'linux',
                    'locale': 'en-US',
                    'version': '57.0a1',
                    'channel': 'nightly'
                },
                'download': {
                    'url': 'https://archive.mozilla.org/pub/firefox/nightly/2017/08/'
                           '2017-08-05-10-03-34-mozilla-central/'
                           'firefox-57.0a1.en-US.linux-x86_64.tar.bz2',
                    'mimetype': 'application/x-bzip2',
                    'size': 34138800,
                    'date': '2017-08-03T20:55:11Z'
                },
            },
            if_not_exists=True)

        self.mock_create_record.assert_any_call(
            bucket='build-hub',
            collection='releases',
            data={
                'id': 'firefox_nightly_2017-08-05-10-03-34_57-0a1_linux-x86_64_ru',
                'source': {
                    'product': 'firefox',
                    'revision': '933a04a91ce3bd44b230937083a835cb60637084',
                    'repository': 'https://hg.mozilla.org/mozilla-central',
                    'tree': 'mozilla-central'
                },
                'build': {
                    'id': '20170805100334',
                    'date': '2017-08-05T10:03:34Z',
                    'cc': '/usr/bin/ccache /home/worker/workspace/build/src/gcc/'
                          'bin/gcc -std=gnu99',
                    'cxx': '/usr/bin/ccache /home/worker/workspace/build/src/gcc/'
                           'bin/g++ -std=gnu++11',
                    'host': 'x86_64-pc-linux-gnu',
                    'as': '$(CC)',
                    'target': 'x86_64-pc-linux-gnu',
                },
                'target': {
                    'platform': 'linux-x86_64',
                    'os': 'linux',
                    'locale': 'ru',
                    'version': '57.0a1',
                    'channel': 'nightly'
                },
                'download': {
                    'url': 'https://archive.mozilla.org/pub/firefox/nightly/2017/08/'
                           '2017-08-05-10-03-34-mozilla-central-l10n/'
                           'firefox-57.0a1.ru.linux-x86_64.tar.bz2',
                    'mimetype': 'application/x-bzip2',
                    'size': 34138800,
                    'date': '2017-08-03T20:55:11Z'
                },
            },
            if_not_exists=True)

        self.mock_create_record.assert_any_call(
            bucket='build-hub',
            collection='releases',
            data={
                'id': 'firefox_nightly_2017-08-05-10-03-34_57-0a1_linux-x86_64_pt-pt',
                'source': {
                    'product': 'firefox',
                    'revision': '933a04a91ce3bd44b230937083a835cb60637084',
                    'repository': 'https://hg.mozilla.org/mozilla-central',
                    'tree': 'mozilla-central'
                },
                'build': {
                    'id': '20170805100334',
                    'date': '2017-08-05T10:03:34Z',
                    'cc': '/usr/bin/ccache /home/worker/workspace/build/src/gcc/'
                          'bin/gcc -std=gnu99',
                    'cxx': '/usr/bin/ccache /home/worker/workspace/build/src/gcc/'
                           'bin/g++ -std=gnu++11',
                    'host': 'x86_64-pc-linux-gnu',
                    'as': '$(CC)',
                    'target': 'x86_64-pc-linux-gnu',
                },
                'target': {
                    'platform': 'linux-x86_64',
                    'os': 'linux',
                    'locale': 'pt-PT',
                    'version': '57.0a1',
                    'channel': 'nightly'
                },
                'download': {
                    'url': 'https://archive.mozilla.org/pub/firefox/nightly/2017/08/'
                           '2017-08-05-10-03-34-mozilla-central-l10n/'
                           'firefox-57.0a1.pt-PT.linux-x86_64.tar.bz2',
                    'mimetype': 'application/x-bzip2',
                    'size': 34138800,
                    'date': '2017-08-03T20:55:11Z'
                },
            },
            if_not_exists=True)

    async def test_from_nightly_metadata_windows(self):
        event = fake_event('pub/firefox/nightly/2017/08/2017-08-05-10-03-34-mozilla-central/'
                           'firefox-57.0a1.en-US.win32.json')
        await lambda_s3_event.main(self.loop, event)

        self.mock_create_record.assert_called_with(
            bucket='build-hub',
            collection='releases',
            data={
                'id': 'firefox_nightly_2017-08-05-10-03-34_57-0a1_win32_en-us',
                'source': {
                    'product': 'firefox',
                    'revision': '933a04a91ce3bd44b230937083a835cb60637084',
                    'repository': 'https://hg.mozilla.org/mozilla-central',
                    'tree': 'mozilla-central'
                },
                'build': {
                    'id': '20170805100334',
                    'date': '2017-08-05T10:03:34Z',
                    'as': 'ml.exe',
                    'cc': 'z:/build/build/src/vs2015u3/VC/bin/amd64_x86/cl.exe',
                    'cxx': 'z:/build/build/src/vs2015u3/VC/bin/amd64_x86/cl.exe',
                    'host': 'i686-pc-mingw32',
                    'target': 'i686-pc-mingw32',
                },
                'target': {
                    'platform': 'win32',
                    'os': 'win',
                    'locale': 'en-US',
                    'version': '57.0a1',
                    'channel': 'nightly'
                },
                'download': {
                    'url': 'https://archive.mozilla.org/pub/firefox/nightly/2017/08/'
                           '2017-08-05-10-03-34-mozilla-central/'
                           'firefox-57.0a1.en-US.win32.zip',
                    'mimetype': 'application/zip',
                    'size': 34138800,
                    'date': '2017-08-03T20:55:11Z'
                },
            },
            if_not_exists=True)

    async def test_from_nightly_metadata_mac(self):
        event = fake_event('pub/firefox/nightly/2017/08/2017-08-05-10-03-34-mozilla-central/'
                           'firefox-57.0a1.en-US.mac.json')
        await lambda_s3_event.main(self.loop, event)

        self.mock_create_record.assert_called_with(
            bucket='build-hub',
            collection='releases',
            data={
                'id': 'firefox_nightly_2017-08-05-10-03-34_57-0a1_macosx_en-us',
                'source': {
                    'product': 'firefox',
                    'revision': '933a04a91ce3bd44b230937083a835cb60637084',
                    'repository': 'https://hg.mozilla.org/mozilla-central',
                    'tree': 'mozilla-central'
                },
                'build': {
                    'id': '20170805100334',
                    'date': '2017-08-05T10:03:34Z',
                    'cc': '/usr/bin/ccache /home/worker/workspace/build/src/clang/bin/'
                          'clang -target '
                          'x86_64-apple-darwin11 -B /home/worker/workspace/build/src/'
                          'cctools/bin '
                          '-isysroot /home/worker/workspace/build/src/MacOSX10.7.sdk'
                          ' -std=gnu99',
                    'cxx': '/usr/bin/ccache /home/worker/workspace/build/src/clang/bin/'
                           'clang++ '
                           '-target x86_64-apple-darwin11 -B /home/worker/workspace/build/'
                           'src/cctools/bin'
                           ' -isysroot /home/worker/workspace/build/src/MacOSX10.7.sdk'
                           ' -std=gnu++11',
                    'host': 'x86_64-pc-linux-gnu',
                    'target': 'x86_64-apple-darwin',
                    'as': '$(CC)',
                },
                'target': {
                    'platform': 'macosx',
                    'os': 'mac',
                    'locale': 'en-US',
                    'version': '57.0a1',
                    'channel': 'nightly'
                },
                'download': {
                    'url': 'https://archive.mozilla.org/pub/firefox/nightly/2017/08/'
                           '2017-08-05-10-03-34-mozilla-central/'
                           'firefox-57.0a1.en-US.mac.dmg',
                    'mimetype': 'application/x-apple-diskimage',
                    'size': 34138800,
                    'date': '2017-08-03T20:55:11Z'
                },
            },
            if_not_exists=True)


class FromArchiveAndroid(BaseTest):
    remote_content = {
        'pub/mobile/candidates/': {
            'prefixes': [
                '55.0-candidates/'
            ], 'files': []
        },
        'pub/mobile/candidates/55.0-candidates/': {
            'prefixes': [
                'build1/',
                'build2/',
            ], 'files': []
        },
        'pub/mobile/candidates/55.0-candidates/build2/android-x86/en-US/': {
            'prefixes': [], 'files': [
                {'name': 'fennec-55.0.en-US.android-i386.json'}
            ]
        },
        # Release english metadata
        'pub/mobile/candidates/55.0-candidates/build2/android-x86/en-US/'
        'fennec-55.0.en-US.android-i386.json': {
            'as': '$(CC)',
            'buildid': '20170803202939',
            'cc': '/usr/bin/ccache /home/worker/workspace/build/src/android-ndk/toolchains/'
                  'x86-4.9/prebuilt/linux-x86_64/bin/i686-linux-android-gcc -std=gnu99',
            'cxx': '/usr/bin/ccache /home/worker/workspace/build/src/android-ndk/toolchains/'
                   'x86-4.9/prebuilt/linux-x86_64/bin/i686-linux-android-g++ -std=gnu++11',
            'host_alias': 'x86_64-pc-linux-gnu',
            'host_cpu': 'x86_64',
            'host_os': 'linux-gnu',
            'host_vendor': 'pc',
            'moz_app_id': '{aa3c5121-dab2-40e2-81ca-7ea25febc110}',
            'moz_app_maxversion': '55.*',
            'moz_app_name': 'fennec',
            'moz_app_vendor': 'Mozilla',
            'moz_app_version': '55.0',
            'moz_pkg_platform': 'android-i386',
            'moz_source_repo': 'MOZ_SOURCE_REPO=https://hg.mozilla.org/releases/mozilla-release',
            'moz_source_stamp': '9e30e915f1325f041d01c722bd640300f32dc9c3',
            'moz_update_channel': 'release',
            'target_alias': 'i386-pc-linux-android',
            'target_cpu': 'i386',
            'target_os': 'linux-android',
            'target_vendor': 'pc'
        },
        # Nightly metadata
        'pub/mobile/nightly/2017/08/2017-08-09-10-03-39-mozilla'
        '-central-android-aarch64/fennec-57.0a1.multi.android-aarch64.json': {
            'as': '$(CC)',
            'buildid': '20170809100339',
            'cc': '/usr/bin/ccache /home/worker/workspace/build/src/android-ndk/'
                  'toolchains/aarch64-linux-android-4.9/prebuilt/linux-x86_64/bin/'
                  'aarch64-linux-android-gcc -std=gnu99',
            'cxx': '/usr/bin/ccache /home/worker/workspace/build/src/android-ndk/'
                   'toolchains/aarch64-linux-android-4.9/prebuilt/linux-x86_64/bin/'
                   'aarch64-linux-android-g++ -std=gnu++11',
            'host_alias': 'x86_64-pc-linux-gnu',
            'host_cpu': 'x86_64',
            'host_os': 'linux-gnu',
            'host_vendor': 'pc',
            'moz_app_id': '{aa3c5121-dab2-40e2-81ca-7ea25febc110}',
            'moz_app_maxversion': '57.0a1',
            'moz_app_name': 'fennec',
            'moz_app_vendor': 'Mozilla',
            'moz_app_version': '57.0a1',
            'moz_pkg_platform': 'android-aarch64',
            'moz_source_repo': 'MOZ_SOURCE_REPO=https://hg.mozilla.org/mozilla-central',
            'moz_source_stamp': '4c5fbf49376351679dcc49f4cff26c3c2e055ccc',
            'moz_update_channel': 'nightly',
            'target_alias': 'aarch64-unknown-linux-android',
            'target_cpu': 'aarch64',
            'target_os': 'linux-android',
            'target_vendor': 'unknown'
        },
        'pub/mobile/nightly/2017/08/2017-08-09-10-03-39-mozilla'
        '-central-android-aarch64/en-US/fennec-57.0a1.en-US.android-aarch64.json': {
            'as': '$(CC)',
            'buildid': '20170809100339',
            'cc': '/usr/bin/ccache /home/worker/workspace/build/src/android-ndk/'
                  'toolchains/aarch64-linux-android-4.9/prebuilt/linux-x86_64/bin/'
                  'aarch64-linux-android-gcc -std=gnu99',
            'cxx': '/usr/bin/ccache /home/worker/workspace/build/src/android-ndk/'
                   'toolchains/aarch64-linux-android-4.9/prebuilt/linux-x86_64/bin/'
                   'aarch64-linux-android-g++ -std=gnu++11',
            'host_alias': 'x86_64-pc-linux-gnu',
            'host_cpu': 'x86_64',
            'host_os': 'linux-gnu',
            'host_vendor': 'pc',
            'moz_app_id': '{aa3c5121-dab2-40e2-81ca-7ea25febc110}',
            'moz_app_maxversion': '57.0a1',
            'moz_app_name': 'fennec',
            'moz_app_vendor': 'Mozilla',
            'moz_app_version': '57.0a1',
            'moz_pkg_platform': 'android-aarch64',
            'moz_source_repo': 'MOZ_SOURCE_REPO=https://hg.mozilla.org/mozilla-central',
            'moz_source_stamp': '4c5fbf49376351679dcc49f4cff26c3c2e055ccc',
            'moz_update_channel': 'nightly',
            'target_alias': 'aarch64-unknown-linux-android',
            'target_cpu': 'aarch64',
            'target_os': 'linux-android',
            'target_vendor': 'unknown'
        },
        'pub/mobile/nightly/2017/08/2017-08-09-10-03-39-mozilla-central-android-x86-old-id/'
        'fennec-57.0a1.multi.android-i386.json': {
            'as': '$(CC)',
            'buildid': '20170809100339',
            'cc': '/usr/bin/ccache /home/worker/workspace/build/src/android-ndk/toolchains/'
                  'x86-4.9/prebuilt/linux-x86_64/bin/i686-linux-android-gcc -std=gnu99',
            'cxx': '/usr/bin/ccache /home/worker/workspace/build/src/android-ndk/toolchains/'
                   'x86-4.9/prebuilt/linux-x86_64/bin/i686-linux-android-g++ -std=gnu++11',
            'host_alias': 'x86_64-pc-linux-gnu',
            'host_cpu': 'x86_64',
            'host_os': 'linux-gnu',
            'host_vendor': 'pc',
            'moz_app_id': '{aa3c5121-dab2-40e2-81ca-7ea25febc110}',
            'moz_app_maxversion': '57.0a1',
            'moz_app_name': 'fennec',
            'moz_app_vendor': 'Mozilla',
            'moz_app_version': '57.0a1',
            'moz_pkg_platform': 'android-i386',
            'moz_source_repo': 'MOZ_SOURCE_REPO=https://hg.mozilla.org/mozilla-central',
            'moz_source_stamp': '4c5fbf49376351679dcc49f4cff26c3c2e055ccc',
            'moz_update_channel': 'nightly-old-id',
            'target_alias': 'i386-pc-linux-android',
            'target_cpu': 'i386',
            'target_os': 'linux-android',
            'target_vendor': 'pc'
        }
    }

    async def test_from_release_archive_before_metadata(self):
        event = fake_event('pub/mobile/releases/55.0/android-api-15/en-US/'
                           'fennec-55.0.en-US.android-arm.apk')
        await lambda_s3_event.main(self.loop, event)

        assert not self.mock_create_record.called

    async def test_from_release_archive_english(self):
        event = fake_event('pub/mobile/releases/55.0/android-x86/en-US/'
                           'fennec-55.0.en-US.android-i386.apk')
        await lambda_s3_event.main(self.loop, event)

        self.mock_create_record.assert_called_with(
            bucket='build-hub',
            collection='releases',
            data={
                'id': 'fennec_55-0_android-x86_en-us',
                'source': {
                    'product': 'fennec',
                    'revision': '9e30e915f1325f041d01c722bd640300f32dc9c3',
                    'repository': 'https://hg.mozilla.org/releases/mozilla-release',
                    'tree': 'releases/mozilla-release'
                },
                'build': {
                    'id': '20170803202939',
                    'date': '2017-08-03T20:29:39Z',
                    'number': 2,
                    'as': '$(CC)',
                    'cc': '/usr/bin/ccache /home/worker/workspace/build/src/'
                          'android-ndk/toolchains/'
                          'x86-4.9/prebuilt/linux-x86_64/bin/i686-linux-android-gcc -std=gnu99',
                    'cxx': '/usr/bin/ccache /home/worker/workspace/build/src/'
                           'android-ndk/toolchains/'
                           'x86-4.9/prebuilt/linux-x86_64/bin/i686-linux-android-g++ -std=gnu++11',
                    'host': 'x86_64-pc-linux-gnu',
                    'target': 'i386-pc-linux-android',
                },
                'target': {
                    'platform': 'android-x86',
                    'os': 'android',
                    'locale': 'en-US',
                    'version': '55.0',
                    'channel': 'release'
                },
                'download': {
                    'url': 'https://archive.mozilla.org/pub/mobile/releases/55.0/android-x86/'
                           'en-US/fennec-55.0.en-US.android-i386.apk',
                    'mimetype': 'application/vnd.android.package-archive',
                    'size': 51001024,
                    'date': '2017-08-08T17:06:52Z'
                },
            },
            if_not_exists=True)

    async def test_from_release_archive_multi(self):
        event = fake_event('pub/mobile/releases/55.0/android-x86/multi/'
                           'fennec-55.0.multi.android-i386.apk')
        await lambda_s3_event.main(self.loop, event)

        self.mock_create_record.assert_called_with(
            bucket='build-hub',
            collection='releases',
            data={
                'id': 'fennec_55-0_android-x86_multi',
                'source': {
                    'product': 'fennec',
                    'revision': '9e30e915f1325f041d01c722bd640300f32dc9c3',
                    'repository': 'https://hg.mozilla.org/releases/mozilla-release',
                    'tree': 'releases/mozilla-release'
                },
                'build': {
                    'id': '20170803202939',
                    'date': '2017-08-03T20:29:39Z',
                    'number': 2,
                    'as': '$(CC)',
                    'cc': '/usr/bin/ccache /home/worker/workspace/build/src/android-ndk/'
                          'toolchains/'
                          'x86-4.9/prebuilt/linux-x86_64/bin/i686-linux-android-gcc -std=gnu99',
                    'cxx': '/usr/bin/ccache /home/worker/workspace/build/src/android-ndk/'
                           'toolchains/'
                           'x86-4.9/prebuilt/linux-x86_64/bin/i686-linux-android-g++ -std=gnu++11',
                    'host': 'x86_64-pc-linux-gnu',
                    'target': 'i386-pc-linux-android',
                },
                'target': {
                    'platform': 'android-x86',
                    'os': 'android',
                    'locale': 'multi',
                    'version': '55.0',
                    'channel': 'release'
                },
                'download': {
                    'url': 'https://archive.mozilla.org/pub/mobile/releases/55.0/android-x86/'
                           'multi/fennec-55.0.multi.android-i386.apk',
                    'mimetype': 'application/vnd.android.package-archive',
                    'size': 51001024,
                    'date': '2017-08-08T17:06:52Z'
                },
            },
            if_not_exists=True)

    async def test_from_nightly_archive_multi(self):
        event = fake_event('pub/mobile/nightly/2017/08/2017-08-09-10-03-39-mozilla'
                           '-central-android-aarch64/fennec-57.0a1.multi.android-aarch64.apk')
        await lambda_s3_event.main(self.loop, event)

        self.mock_create_record.assert_called_with(
            bucket='build-hub',
            collection='releases',
            data={
                'id': 'fennec_nightly_2017-08-09-10-03-39_57-0a1_android-aarch64_multi',
                'source': {
                    'product': 'fennec',
                    'revision': '4c5fbf49376351679dcc49f4cff26c3c2e055ccc',
                    'repository': 'https://hg.mozilla.org/mozilla-central',
                    'tree': 'mozilla-central'
                },
                'build': {
                    'id': '20170809100339',
                    'date': '2017-08-09T10:03:39Z',
                    'as': '$(CC)',
                    'cc': '/usr/bin/ccache /home/worker/workspace/build/src/android-ndk/'
                          'toolchains/aarch64-linux-android-4.9/prebuilt/linux-x86_64/bin/'
                          'aarch64-linux-android-gcc -std=gnu99',
                    'cxx': '/usr/bin/ccache /home/worker/workspace/build/src/android-ndk/'
                           'toolchains/aarch64-linux-android-4.9/prebuilt/linux-x86_64/bin/'
                           'aarch64-linux-android-g++ -std=gnu++11',
                    'host': 'x86_64-pc-linux-gnu',
                    'target': 'aarch64-unknown-linux-android',
                },
                'target': {
                    'platform': 'android-aarch64',
                    'os': 'android',
                    'locale': 'multi',
                    'version': '57.0a1',
                    'channel': 'nightly'
                },
                'download': {
                    'url': 'https://archive.mozilla.org/pub/mobile/nightly/2017/08/'
                           '2017-08-09-10-03-39-mozilla-central-android-aarch64/'
                           'fennec-57.0a1.multi.android-aarch64.apk',
                    'mimetype': 'application/vnd.android.package-archive',
                    'size': 51001024,
                    'date': '2017-08-08T17:06:52Z'
                },
            },
            if_not_exists=True)

    async def test_from_nightly_archive_english(self):
        event = fake_event('pub/mobile/nightly/2017/08/2017-08-09-10-03-39-mozilla-central'
                           '-android-aarch64/en-US/fennec-57.0a1.en-US.android-aarch64.apk')
        await lambda_s3_event.main(self.loop, event)

        self.mock_create_record.assert_called_with(
            bucket='build-hub',
            collection='releases',
            data={
                'id': 'fennec_nightly_2017-08-09-10-03-39_57-0a1_android-aarch64_en-us',
                'source': {
                    'product': 'fennec',
                    'revision': '4c5fbf49376351679dcc49f4cff26c3c2e055ccc',
                    'repository': 'https://hg.mozilla.org/mozilla-central',
                    'tree': 'mozilla-central'
                },
                'build': {
                    'id': '20170809100339',
                    'date': '2017-08-09T10:03:39Z',
                    'as': '$(CC)',
                    'cc': '/usr/bin/ccache /home/worker/workspace/build/src/android-ndk/'
                          'toolchains/aarch64-linux-android-4.9/prebuilt/linux-x86_64/bin/'
                          'aarch64-linux-android-gcc -std=gnu99',
                    'cxx': '/usr/bin/ccache /home/worker/workspace/build/src/android-ndk/'
                           'toolchains/aarch64-linux-android-4.9/prebuilt/linux-x86_64/bin/'
                           'aarch64-linux-android-g++ -std=gnu++11',
                    'host': 'x86_64-pc-linux-gnu',
                    'target': 'aarch64-unknown-linux-android',
                },
                'target': {
                    'platform': 'android-aarch64',
                    'os': 'android',
                    'locale': 'en-US',
                    'version': '57.0a1',
                    'channel': 'nightly'
                },
                'download': {
                    'url': 'https://archive.mozilla.org/pub/mobile/nightly/2017/08/'
                           '2017-08-09-10-03-39-mozilla-central-android-aarch64/en-US/'
                           'fennec-57.0a1.en-US.android-aarch64.apk',
                    'mimetype': 'application/vnd.android.package-archive',
                    'size': 51001024,
                    'date': '2017-08-08T17:06:52Z'
                },
            },
            if_not_exists=True)

    async def test_from_nightly_old_id(self):
        event = fake_event('pub/mobile/nightly/2017/08/2017-08-09-10-03-39-mozilla-central'
                           '-android-x86-old-id/fennec-57.0a1.multi.android-i386.apk')
        await lambda_s3_event.main(self.loop, event)

        self.mock_create_record.assert_called_with(
            bucket='build-hub',
            collection='releases',
            data={
                'id': 'fennec_nightly-old-id_2017-08-09-10-03-39_57-0a1_android-i386_multi',
                'source': {
                    'product': 'fennec',
                    'revision': '4c5fbf49376351679dcc49f4cff26c3c2e055ccc',
                    'repository': 'https://hg.mozilla.org/mozilla-central',
                    'tree': 'mozilla-central'
                },
                'build': {
                    'id': '20170809100339',
                    'date': '2017-08-09T10:03:39Z',
                    'as': '$(CC)',
                    'cc': '/usr/bin/ccache /home/worker/workspace/build/src/android-ndk/'
                          'toolchains/'
                          'x86-4.9/prebuilt/linux-x86_64/bin/i686-linux-android-gcc -std=gnu99',
                    'cxx': '/usr/bin/ccache /home/worker/workspace/build/src/android-ndk/'
                           'toolchains/'
                           'x86-4.9/prebuilt/linux-x86_64/bin/i686-linux-android-g++ -std=gnu++11',
                    'host': 'x86_64-pc-linux-gnu',
                    'target': 'i386-pc-linux-android',
                },
                'target': {
                    'platform': 'android-i386',
                    'os': 'android',
                    'locale': 'multi',
                    'version': '57.0a1',
                    'channel': 'nightly-old-id'
                },
                'download': {
                    'url': 'https://archive.mozilla.org/pub/mobile/nightly/2017/08/2017-08-09'
                           '-10-03-39-mozilla-central-android-x86-old-id/'
                           'fennec-57.0a1.multi.android-i386.apk',
                    'mimetype': 'application/vnd.android.package-archive',
                    'size': 51001024,
                    'date': '2017-08-08T17:06:52Z'
                },
            },
            if_not_exists=True)


class FromRCMetadataAndroid(BaseTest):
    remote_content = {
        'pub/mobile/candidates/56.0b1-candidates/build1/android-api-15/': {
            'prefixes': [
                'es-ES/',
                'ca/',
                'en-US/',
            ], 'files': [],
        },
        'pub/mobile/candidates/56.0b1-candidates/build1/android-api-15/ca/': {
            'prefixes': [], 'files': [{
                'name': 'fennec-56.0b1.ca.android-arm.apk',
                'last_modified': '2017-08-03T20:55:11Z',
                'size': 34138800
            }]
        },
        'pub/mobile/candidates/56.0b1-candidates/build1/android-api-15/en-US/': {
            'prefixes': [], 'files': [{
                'name': 'fennec-56.0b1.en-US.android-arm.apk',
                'last_modified': '2017-08-03T20:55:11Z',
                'size': 34138800
            }]
        },
        'pub/mobile/candidates/56.0b1-candidates/build1/android-api-15/es-ES/': {
            'prefixes': [], 'files': [
                {'name': 'fennec-56.0b1.en-US.android-arm.txt'}
            ]
        },
        'pub/mobile/candidates/56.0b1-candidates/build1/android-api-15/en-US/'
        'fennec-56.0b1.en-US.android-arm.json': {
            'as': '$(CC)',
            'buildid': '20170807232150',
            'cc': '/usr/bin/ccache /home/worker/workspace/build/src/android-ndk/'
                  'toolchains/arm-linux-androideabi-4.9/prebuilt/linux-x86_64/bin/'
                  'arm-linux-androideabi-gcc -std=gnu99',
            'cxx': '/usr/bin/ccache /home/worker/workspace/build/src/android-ndk/'
                   'toolchains/arm-linux-androideabi-4.9/prebuilt/linux-x86_64/'
                   'bin/arm-linux-androideabi-g++ -std=gnu++11',
            'host_alias': 'x86_64-pc-linux-gnu',
            'host_cpu': 'x86_64',
            'host_os': 'linux-gnu',
            'host_vendor': 'pc',
            'moz_app_id': '{aa3c5121-dab2-40e2-81ca-7ea25febc110}',
            'moz_app_maxversion': '56.*',
            'moz_app_name': 'fennec',
            'moz_app_vendor': 'Mozilla',
            'moz_app_version': '56.0',
            'moz_pkg_platform': 'android-arm',
            'moz_source_repo': 'MOZ_SOURCE_REPO=https://hg.mozilla.org/releases/mozilla-beta',
            'moz_source_stamp': '6c489d5df6d4d85ddb297666e8c1cbbda96a852c',
            'moz_update_channel': 'beta',
            'target_alias': 'arm-unknown-linux-androideabi',
            'target_cpu': 'arm',
            'target_os': 'linux-androideabi',
            'target_vendor': 'unknown'
        }
    }

    async def test_pick_rc_and_locales(self):
        event = fake_event('pub/mobile/candidates/56.0b1-candidates/build1/'
                           'android-api-15/en-US/fennec-56.0b1.en-US.android-arm.json')
        await lambda_s3_event.main(self.loop, event)

        assert self.mock_create_record.call_count == 2

        self.mock_create_record.assert_any_call(
            bucket='build-hub',
            collection='releases',
            data={
                'id': 'fennec_beta_56-0b1rc1_android-api-15_ca',
                'source': {
                    'product': 'fennec',
                    'revision': '6c489d5df6d4d85ddb297666e8c1cbbda96a852c',
                    'repository': 'https://hg.mozilla.org/releases/mozilla-beta',
                    'tree': 'releases/mozilla-beta'
                },
                'build': {
                    'id': '20170807232150',
                    'date': '2017-08-07T23:21:50Z',
                    'number': 1,
                    'as': '$(CC)',
                    'cc': '/usr/bin/ccache /home/worker/workspace/build/src/android-ndk/'
                          'toolchains/arm-linux-androideabi-4.9/prebuilt/linux-x86_64/bin/'
                          'arm-linux-androideabi-gcc -std=gnu99',
                    'cxx': '/usr/bin/ccache /home/worker/workspace/build/src/android-ndk/'
                           'toolchains/arm-linux-androideabi-4.9/prebuilt/linux-x86_64/'
                           'bin/arm-linux-androideabi-g++ -std=gnu++11',
                    'host': 'x86_64-pc-linux-gnu',
                    'target': 'arm-unknown-linux-androideabi',
                },
                'target': {
                    'platform': 'android-api-15',
                    'os': 'android',
                    'locale': 'ca',
                    'version': '56.0b1rc1',
                    'channel': 'beta'
                },
                'download': {
                    'url': 'https://archive.mozilla.org/pub/mobile/candidates/'
                           '56.0b1-candidates/build1/android-api-15/ca/'
                           'fennec-56.0b1.ca.android-arm.apk',
                    'mimetype': 'application/vnd.android.package-archive',
                    'size': 34138800,
                    'date': '2017-08-03T20:55:11Z'
                },
            },
            if_not_exists=True)

        self.mock_create_record.assert_any_call(
            bucket='build-hub',
            collection='releases',
            data={
                'id': 'fennec_beta_56-0b1rc1_android-api-15_en-us',
                'source': {
                    'product': 'fennec',
                    'revision': '6c489d5df6d4d85ddb297666e8c1cbbda96a852c',
                    'repository': 'https://hg.mozilla.org/releases/mozilla-beta',
                    'tree': 'releases/mozilla-beta'
                },
                'build': {
                    'id': '20170807232150',
                    'date': '2017-08-07T23:21:50Z',
                    'number': 1,
                    'as': '$(CC)',
                    'cc': '/usr/bin/ccache /home/worker/workspace/build/src/android-ndk/'
                          'toolchains/arm-linux-androideabi-4.9/prebuilt/linux-x86_64/bin/'
                          'arm-linux-androideabi-gcc -std=gnu99',
                    'cxx': '/usr/bin/ccache /home/worker/workspace/build/src/android-ndk/'
                           'toolchains/arm-linux-androideabi-4.9/prebuilt/linux-x86_64/'
                           'bin/arm-linux-androideabi-g++ -std=gnu++11',
                    'host': 'x86_64-pc-linux-gnu',
                    'target': 'arm-unknown-linux-androideabi',
                },
                'target': {
                    'platform': 'android-api-15',
                    'os': 'android',
                    'locale': 'en-US',
                    'version': '56.0b1rc1',
                    'channel': 'beta'
                },
                'download': {
                    'url': 'https://archive.mozilla.org/pub/mobile/candidates/'
                           '56.0b1-candidates/build1/android-api-15/en-US/'
                           'fennec-56.0b1.en-US.android-arm.apk',
                    'mimetype': 'application/vnd.android.package-archive',
                    'size': 34138800,
                    'date': '2017-08-03T20:55:11Z'
                },
            },
            if_not_exists=True)


class FromNightlyMetadataAndroid(BaseTest):
    remote_content = {
        'pub/mobile/nightly/2017/08/2017-08-01-15-03-46-mozilla-central-android-api-15/': {
            'prefixes': [], 'files': [{
                'name': 'fennec-56.0a1.multi.android-arm.apk',
                'last_modified': '2017-08-03T20:55:11Z',
                'size': 34138800
            }]
        },
        'pub/mobile/nightly/2017/08/2017-08-01-15-03-46-mozilla-central-android-api-15/'
        'fennec-56.0a1.multi.android-arm.json': {
            'as': '$(CC)',
            'buildid': '20170801150346',
            'cc': '/usr/bin/ccache /home/worker/workspace/build/src/android-ndk/'
                  'toolchains/arm-linux-androideabi-4.9/prebuilt/linux-x86_64/bin/'
                  'arm-linux-androideabi-gcc -std=gnu99',
            'cxx': '/usr/bin/ccache /home/worker/workspace/build/src/android-ndk/'
                   'toolchains/arm-linux-androideabi-4.9/prebuilt/linux-x86_64/bin/'
                   'arm-linux-androideabi-g++ -std=gnu++11',
            'host_alias': 'x86_64-pc-linux-gnu',
            'host_cpu': 'x86_64',
            'host_os': 'linux-gnu',
            'host_vendor': 'pc',
            'moz_app_id': '{aa3c5121-dab2-40e2-81ca-7ea25febc110}',
            'moz_app_maxversion': '57.0a1',
            'moz_app_name': 'fennec',
            'moz_app_vendor': 'Mozilla',
            'moz_app_version': '57.0a1',
            'moz_pkg_platform': 'android-arm',
            'moz_source_repo': 'MOZ_SOURCE_REPO=https://hg.mozilla.org/mozilla-central',
            'moz_source_stamp': '52285ea5e54c73d3ed824544cef2ee3f195f05e6',
            'moz_update_channel': 'nightly',
            'target_alias': 'arm-unknown-linux-androideabi',
            'target_cpu': 'arm',
            'target_os': 'linux-androideabi',
            'target_vendor': 'unknown'
        },
        # Pure english. Check that no l10n are associated (keep that for multi)
        'pub/mobile/nightly/2017/08/2017-08-01-15-03-46-mozilla-central-android-api-15/en-US/': {
            'prefixes': [], 'files': [{
                'name': 'fennec-56.0a1.en-US.android-arm.apk',
                'last_modified': '2017-08-03T20:55:11Z',
                'size': 34138800
            }]
        },
        'pub/mobile/nightly/2017/08/2017-08-01-15-03-46-mozilla-central-android-api-15/en-US/'
        'fennec-56.0a1.en-US.android-arm.json': {
            'as': '$(CC)',
            'buildid': '20170801150346',
            'cc': '/usr/bin/ccache /home/worker/workspace/build/src/android-ndk/'
                  'toolchains/arm-linux-androideabi-4.9/prebuilt/linux-x86_64/bin/'
                  'arm-linux-androideabi-gcc -std=gnu99',
            'cxx': '/usr/bin/ccache /home/worker/workspace/build/src/android-ndk/'
                   'toolchains/arm-linux-androideabi-4.9/prebuilt/linux-x86_64/bin/'
                   'arm-linux-androideabi-g++ -std=gnu++11',
            'host_alias': 'x86_64-pc-linux-gnu',
            'host_cpu': 'x86_64',
            'host_os': 'linux-gnu',
            'host_vendor': 'pc',
            'moz_app_id': '{aa3c5121-dab2-40e2-81ca-7ea25febc110}',
            'moz_app_maxversion': '57.0a1',
            'moz_app_name': 'fennec',
            'moz_app_vendor': 'Mozilla',
            'moz_app_version': '56.0a1',
            'moz_pkg_platform': 'android-arm',
            'moz_source_repo': 'MOZ_SOURCE_REPO=https://hg.mozilla.org/mozilla-central',
            'moz_source_stamp': '52285ea5e54c73d3ed824544cef2ee3f195f05e6',
            'moz_update_channel': 'nightly',
            'target_alias': 'arm-unknown-linux-androideabi',
            'target_cpu': 'arm',
            'target_os': 'linux-androideabi',
            'target_vendor': 'unknown'
        },
        'pub/mobile/nightly/2017/08/2017-08-01-15-03-46-mozilla-central-android-api-15-l10n/': {
            'prefixes': [], 'files': [{
                'name': 'fennec-56.0a1.fr.android-arm.apk',
                'last_modified': '2017-08-03T20:55:11Z',
                'size': 34138800
            }, {
                'name': 'fennec-56.0a1.fr.android-arm.checksums'
            }]
        },
        # Old-id stuff.
        'pub/mobile/nightly/2017/08/2017-08-02-10-03-02-mozilla-central-android-api-15-old-id/': {
            'prefixes': [], 'files': [{
                'name': 'fennec-57.0a1.multi.android-arm.apk',
                'last_modified': '2017-08-03T20:55:11Z',
                'size': 34138800
            }]
        },
        'pub/mobile/nightly/2017/08/2017-08-02-10-03-02-mozilla-central-android-api-15-old-id/'
        'fennec-57.0a1.multi.android-arm.json': {
            'as': '$(CC)',
            'buildid': '20170802100302',
            'cc': '/usr/bin/ccache /home/worker/workspace/build/src/android-ndk/'
                  'toolchains/arm-linux-androideabi-4.9/prebuilt/linux-x86_64/bin/'
                  'arm-linux-androideabi-gcc -std=gnu99',
            'cxx': '/usr/bin/ccache /home/worker/workspace/build/src/android-ndk/'
                   'toolchains/arm-linux-androideabi-4.9/prebuilt/linux-x86_64/bin/'
                   'arm-linux-androideabi-g++ -std=gnu++11',
            'host_alias': 'x86_64-pc-linux-gnu',
            'host_cpu': 'x86_64',
            'host_os': 'linux-gnu',
            'host_vendor': 'pc',
            'moz_app_id': '{aa3c5121-dab2-40e2-81ca-7ea25febc110}',
            'moz_app_maxversion': '57.0a1',
            'moz_app_name': 'fennec',
            'moz_app_vendor': 'Mozilla',
            'moz_app_version': '57.0a1',
            'moz_pkg_platform': 'android-arm',
            'moz_source_repo': 'MOZ_SOURCE_REPO=https://hg.mozilla.org/mozilla-central',
            'moz_source_stamp': '52285ea5e54c73d3ed824544cef2ee3f195f05e6',
            'moz_update_channel': 'nightly-old-id',
            'target_alias': 'arm-unknown-linux-androideabi',
            'target_cpu': 'arm',
            'target_os': 'linux-androideabi',
            'target_vendor': 'unknown'
        },
        # Find localized archives from a multi json.
        'pub/mobile/nightly/2017/08/2017-08-09-10-03-39-mozilla-central-android-api-15/': {
            'prefixes': [], 'files': []
        },
        'pub/mobile/nightly/2017/08/2017-08-09-10-03-39-mozilla-central-android-api-15/'
        'fennec-57.0a1.multi.android-arm.json': {
            'as': '$(CC)',
            'buildid': '20170809100339',
            'cc': '/usr/bin/ccache /home/worker/workspace/build/src/android-ndk/toolchains/'
                  'arm-linux-androideabi-4.9/prebuilt/linux-x86_64/bin/'
                  'arm-linux-androideabi-gcc -std=gnu99',
            'cxx': '/usr/bin/ccache /home/worker/workspace/build/src/android-ndk/toolchains/'
                   'arm-linux-androideabi-4.9/prebuilt/linux-x86_64/bin/arm-linux-androideabi'
                   '-g++ -std=gnu++11',
            'host_alias': 'x86_64-pc-linux-gnu',
            'host_cpu': 'x86_64',
            'host_os': 'linux-gnu',
            'host_vendor': 'pc',
            'moz_app_id': '{aa3c5121-dab2-40e2-81ca-7ea25febc110}',
            'moz_app_maxversion': '57.0a1',
            'moz_app_name': 'fennec',
            'moz_app_vendor': 'Mozilla',
            'moz_app_version': '57.0a1',
            'moz_pkg_platform': 'android-arm',
            'moz_source_repo': 'MOZ_SOURCE_REPO=https://hg.mozilla.org/mozilla-central',
            'moz_source_stamp': '4c5fbf49376351679dcc49f4cff26c3c2e055ccc',
            'moz_update_channel': 'nightly',
            'target_alias': 'arm-unknown-linux-androideabi',
            'target_cpu': 'arm',
            'target_os': 'linux-androideabi',
            'target_vendor': 'unknown'
        },
        'pub/mobile/nightly/2017/08/2017-08-09-10-03-39-mozilla-central-android-api-15-l10n/': {
            'prefixes': [], 'files': [{
                'name': 'fennec-57.0a1.be.android-arm.apk',
                'last_modified': '2017-08-03T20:55:11Z',
                'size': 34138800
            }, {
                'name': 'fennec-57.0a1.be.android-arm.checksums'
            }, {
                'name': 'fennec-57.0a1.hi-IN.android-arm.apk',
                'last_modified': '2017-08-03T20:55:11Z',
                'size': 34138800
            }, {
                'name': 'fennec-57.0a1.hi-IN.android-arm.checksums'
            }, {
                'name': 'fennec-57.0a1.hi-IN.android-arm.checksums.asc'
            }]
        }
    }

    async def test_from_nightly_date_are_ignored(self):
        event = fake_event('pub/mobile/nightly/2017/08/2017-08-01-15-03-46-date-android'
                           '-api-15/fennec-56.0a1.multi.android-arm.json')
        await lambda_s3_event.main(self.loop, event)

        assert not self.mock_create_record.called

    async def test_from_nightly_multi_arm(self):
        event = fake_event('pub/mobile/nightly/2017/08/2017-08-01-15-03-46-mozilla-central'
                           '-android-api-15/fennec-56.0a1.multi.android-arm.json')
        await lambda_s3_event.main(self.loop, event)

        self.mock_create_record.assert_any_call(
            bucket='build-hub',
            collection='releases',
            data={
                'id': 'fennec_nightly_2017-08-01-15-03-46_56-0a1_android-api-15_multi',
                'source': {
                    'product': 'fennec',
                    'revision': '52285ea5e54c73d3ed824544cef2ee3f195f05e6',
                    'repository': 'https://hg.mozilla.org/mozilla-central',
                    'tree': 'mozilla-central'
                },
                'build': {
                    'id': '20170801150346',
                    'date': '2017-08-01T15:03:46Z',
                    'as': '$(CC)',
                    'cc': '/usr/bin/ccache /home/worker/workspace/build/src/android-ndk/'
                          'toolchains/arm-linux-androideabi-4.9/prebuilt/linux-x86_64/bin/'
                          'arm-linux-androideabi-gcc -std=gnu99',
                    'cxx': '/usr/bin/ccache /home/worker/workspace/build/src/android-ndk/'
                           'toolchains/arm-linux-androideabi-4.9/prebuilt/linux-x86_64/bin/'
                           'arm-linux-androideabi-g++ -std=gnu++11',
                    'host': 'x86_64-pc-linux-gnu',
                    'target': 'arm-unknown-linux-androideabi',

                },
                'target': {
                    'platform': 'android-api-15',
                    'os': 'android',
                    'locale': 'multi',
                    'version': '56.0a1',
                    'channel': 'nightly'
                },
                'download': {
                    'url': 'https://archive.mozilla.org/pub/mobile/nightly/2017/'
                           '08/2017-08-01-15-03-46-mozilla-central'
                           '-android-api-15/fennec-56.0a1.multi.android-arm.apk',
                    'mimetype': 'application/vnd.android.package-archive',
                    'size': 34138800,
                    'date': '2017-08-03T20:55:11Z'
                },
            },
            if_not_exists=True)

    async def test_from_nightly_english_arm(self):
        event = fake_event('pub/mobile/nightly/2017/08/2017-08-01-15-03-46-mozilla-central'
                           '-android-api-15/en-US/fennec-56.0a1.en-US.android-arm.json')
        await lambda_s3_event.main(self.loop, event)

        # Do not create records for l10n files from en-US metadata.
        assert self.mock_create_record.call_count == 1

        self.mock_create_record.assert_called_with(
            bucket='build-hub',
            collection='releases',
            data={
                'id': 'fennec_nightly_2017-08-01-15-03-46_56-0a1_android-api-15_en-us',
                'source': {
                    'product': 'fennec',
                    'revision': '52285ea5e54c73d3ed824544cef2ee3f195f05e6',
                    'repository': 'https://hg.mozilla.org/mozilla-central',
                    'tree': 'mozilla-central'
                },
                'build': {
                    'id': '20170801150346',
                    'date': '2017-08-01T15:03:46Z',
                    'as': '$(CC)',
                    'cc': '/usr/bin/ccache /home/worker/workspace/build/src/android-ndk/'
                          'toolchains/arm-linux-androideabi-4.9/prebuilt/linux-x86_64/bin/'
                          'arm-linux-androideabi-gcc -std=gnu99',
                    'cxx': '/usr/bin/ccache /home/worker/workspace/build/src/android-ndk/'
                           'toolchains/arm-linux-androideabi-4.9/prebuilt/linux-x86_64/bin/'
                           'arm-linux-androideabi-g++ -std=gnu++11',
                    'host': 'x86_64-pc-linux-gnu',
                    'target': 'arm-unknown-linux-androideabi',
                },
                'target': {
                    'platform': 'android-api-15',
                    'os': 'android',
                    'locale': 'en-US',
                    'version': '56.0a1',
                    'channel': 'nightly'
                },
                'download': {
                    'url': 'https://archive.mozilla.org/pub/mobile/nightly/2017/'
                           '08/2017-08-01-15-03-46-mozilla-central'
                           '-android-api-15/en-US/fennec-56.0a1.en-US.android-arm.apk',
                    'mimetype': 'application/vnd.android.package-archive',
                    'size': 34138800,
                    'date': '2017-08-03T20:55:11Z'
                },
            },
            if_not_exists=True)

    async def test_from_nightly_multi_old_id(self):
        event = fake_event('pub/mobile/nightly/2017/08/2017-08-02-10-03-02-mozilla-central-'
                           'android-api-15-old-id/fennec-57.0a1.multi.android-arm.json')
        await lambda_s3_event.main(self.loop, event)

        self.mock_create_record.assert_called_with(
            bucket='build-hub',
            collection='releases',
            data={
                'id': 'fennec_nightly-old-id_2017-08-02-10-03-02_57-0a1_android-api-15_multi',
                'source': {
                    'product': 'fennec',
                    'revision': '52285ea5e54c73d3ed824544cef2ee3f195f05e6',
                    'repository': 'https://hg.mozilla.org/mozilla-central',
                    'tree': 'mozilla-central'
                },
                'build': {
                    'id': '20170802100302',
                    'date': '2017-08-02T10:03:02Z',
                    'as': '$(CC)',
                    'cc': '/usr/bin/ccache /home/worker/workspace/build/src/android-ndk/'
                          'toolchains/arm-linux-androideabi-4.9/prebuilt/linux-x86_64/bin/'
                          'arm-linux-androideabi-gcc -std=gnu99',
                    'cxx': '/usr/bin/ccache /home/worker/workspace/build/src/android-ndk/'
                           'toolchains/arm-linux-androideabi-4.9/prebuilt/linux-x86_64/bin/'
                           'arm-linux-androideabi-g++ -std=gnu++11',
                    'host': 'x86_64-pc-linux-gnu',
                    'target': 'arm-unknown-linux-androideabi',
                },
                'target': {
                    'platform': 'android-api-15',
                    'os': 'android',
                    'locale': 'multi',
                    'version': '57.0a1',
                    'channel': 'nightly-old-id'
                },
                'download': {
                    'url': 'https://archive.mozilla.org/pub/mobile/nightly/2017/08/'
                           '2017-08-02-10-03-02-mozilla-central-android-api-15-old-id/'
                           'fennec-57.0a1.multi.android-arm.apk',
                    'mimetype': 'application/vnd.android.package-archive',
                    'size': 34138800,
                    'date': '2017-08-03T20:55:11Z'
                },
            },
            if_not_exists=True)

    async def test_from_nightly_arm_fetches_other_languages(self):
        event = fake_event('pub/mobile/nightly/2017/08/2017-08-09-10-03-39-mozilla-central'
                           '-android-api-15/fennec-57.0a1.multi.android-arm.json')
        await lambda_s3_event.main(self.loop, event)

        # Note: simulate multi archive is not published yet. Only l10n derivatives
        # (see remote_content)
        assert self.mock_create_record.call_count == 2

        self.mock_create_record.assert_any_call(
            bucket='build-hub',
            collection='releases',
            data={
                'id': 'fennec_nightly_2017-08-09-10-03-39_57-0a1_android-api-15_hi-in',
                'source': {
                    'product': 'fennec',
                    'revision': '4c5fbf49376351679dcc49f4cff26c3c2e055ccc',
                    'repository': 'https://hg.mozilla.org/mozilla-central',
                    'tree': 'mozilla-central'
                },
                'build': {
                    'id': '20170809100339',
                    'date': '2017-08-09T10:03:39Z',
                    'as': '$(CC)',
                    'cc': '/usr/bin/ccache /home/worker/workspace/build/src/android-ndk/'
                          'toolchains/arm-linux-androideabi-4.9/prebuilt/linux-x86_64/bin/'
                          'arm-linux-androideabi-gcc -std=gnu99',
                    'cxx': '/usr/bin/ccache /home/worker/workspace/build/src/android-ndk/'
                           'toolchains/arm-linux-androideabi-4.9/prebuilt/linux-x86_64/bin/'
                           'arm-linux-androideabi-g++ -std=gnu++11',
                    'host': 'x86_64-pc-linux-gnu',
                    'target': 'arm-unknown-linux-androideabi',
                },
                'target': {
                    'platform': 'android-api-15',
                    'os': 'android',
                    'locale': 'hi-IN',
                    'version': '57.0a1',
                    'channel': 'nightly'
                },
                'download': {
                    'url': 'https://archive.mozilla.org/pub/mobile/nightly/2017/08/'
                           '2017-08-09-10-03-39-mozilla-central-android-api-15-l10n/'
                           'fennec-57.0a1.hi-IN.android-arm.apk',
                    'mimetype': 'application/vnd.android.package-archive',
                    'size': 34138800,
                    'date': '2017-08-03T20:55:11Z'
                },
            },
            if_not_exists=True)

        self.mock_create_record.assert_any_call(
            bucket='build-hub',
            collection='releases',
            data={
                'id': 'fennec_nightly_2017-08-09-10-03-39_57-0a1_android-api-15_be',
                'source': {
                    'product': 'fennec',
                    'revision': '4c5fbf49376351679dcc49f4cff26c3c2e055ccc',
                    'repository': 'https://hg.mozilla.org/mozilla-central',
                    'tree': 'mozilla-central'
                },
                'build': {
                    'id': '20170809100339',
                    'date': '2017-08-09T10:03:39Z',
                    'as': '$(CC)',
                    'cc': '/usr/bin/ccache /home/worker/workspace/build/src/android-ndk/'
                          'toolchains/arm-linux-androideabi-4.9/prebuilt/linux-x86_64/bin/'
                          'arm-linux-androideabi-gcc -std=gnu99',
                    'cxx': '/usr/bin/ccache /home/worker/workspace/build/src/android-ndk/'
                           'toolchains/arm-linux-androideabi-4.9/prebuilt/linux-x86_64/bin/'
                           'arm-linux-androideabi-g++ -std=gnu++11',
                    'host': 'x86_64-pc-linux-gnu',
                    'target': 'arm-unknown-linux-androideabi',
                },
                'target': {
                    'platform': 'android-api-15',
                    'os': 'android',
                    'locale': 'be',
                    'version': '57.0a1',
                    'channel': 'nightly'
                },
                'download': {
                    'url': 'https://archive.mozilla.org/pub/mobile/nightly/2017/08/'
                           '2017-08-09-10-03-39-mozilla-central-android-api-15-l10n/'
                           'fennec-57.0a1.be.android-arm.apk',
                    'mimetype': 'application/vnd.android.package-archive',
                    'size': 34138800,
                    'date': '2017-08-03T20:55:11Z'
                },
            },
            if_not_exists=True)
