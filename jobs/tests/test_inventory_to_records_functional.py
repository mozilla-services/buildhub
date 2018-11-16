# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, you can obtain one at http://mozilla.org/MPL/2.0/.


import os
import io
import json
import sys
from unittest import mock

import asynctest
import pytest

from buildhub import inventory_to_records
from buildhub.utils import ARCHIVE_URL

here = os.path.dirname(__file__)


class CsvToRecordsTest(asynctest.TestCase):
    def setUp(self):
        self.stdout = sys.stdout
        self.stdin = sys.stdin
        self.argv = sys.argv

        filename = os.path.join(here, 'data', 'inventory-simple.csv')
        sys.stdin = open(filename, 'r')
        sys.stdout = io.StringIO()
        sys.argv = ['inventory-to-records']

        async def fake_stream(loop, stream):
            # Workaround for "Pipe transport is for pipes/sockets only".
            # Here stream is just a file descriptor.
            for line in stream.readlines():
                yield bytes(line, 'utf-8')

        p = mock.patch('buildhub.inventory_to_records.stream_as_generator',
                       wraps=fake_stream)
        self.addCleanup(p.stop)
        p.start()

    def tearDown(self):
        sys.stdin.close()
        sys.argv = self.argv
        sys.stdout = self.stdout
        sys.stdin = self.stdin

    @pytest.fixture(autouse=True)
    def init_cache_folder(self, tmpdir):
        # Use str() on these LocalPath instances to turn them into plain
        # strings since to_kinto.fetch_existing() expects it to be a string.
        self.cache_folder = str(tmpdir)

    async def test_load_simple_file(self):
        await inventory_to_records.main(
            self.loop,
            cache_folder=self.cache_folder
        )

        output = sys.stdout.getvalue()
        records = [json.loads(o) for o in output.split('\n') if o]
        expected = [{
            'data': {
                'id': (
                    'firefox_nightly_2017-05-15-10-02-38_55-0a1_linux'
                    '-x86_64_en-us'
                ),
                'build': {
                    'id': '20170515100238',
                    'date': '2017-05-15T10:02:38Z',
                    'as': '$(CC)',
                    'cc': '/usr/bin/ccache '
                          '/home/worker/workspace/build/src/gcc/bin/gcc '
                          '-std=gnu99',
                    'cxx': '/usr/bin/ccache '
                           '/home/worker/workspace/build/src/gcc/bin/g++ '
                           '-std=gnu++11',
                    'host': 'x86_64-pc-linux-gnu',
                    'target': 'x86_64-pc-linux-gnu'
                },
                'source': {
                    'product': 'firefox',
                    'revision': 'e66dedabe582ba7b394aee4f89ed70fe389b3c46',
                    'repository': 'https://hg.mozilla.org/mozilla-central',
                    'tree': 'mozilla-central'
                },
                'target': {
                    'platform': 'linux-x86_64',
                    'os': 'linux',
                    'locale': 'en-US',
                    'version': '55.0a1',
                    'channel': 'nightly'
                },
                'download': {
                    'url': (f'{ARCHIVE_URL}pub/firefox/nightly/'
                            '2017/05/2017-05-15-10-02-38-mozilla-central/'
                            'firefox-55.0a1.en-US.linux-x86_64.tar.bz2'),
                    'mimetype': 'application/x-bzip2',
                    'size': 50000,
                    'date': '2017-06-02T12:20:10Z'
                }
            }
        }, {
            'data': {
                'id': 'firefox_52-0_linux-x86_64_fr',
                'build': {
                    'id': '20170302120751',
                    'date': '2017-03-02T12:07:51Z',
                    'number': 2,
                    'as': '$(CC)',
                    'cc': (
                        '/builds/slave/m-rel-l64-00000000000000000000/build/'
                        'src/gcc/bin/gcc -std=gnu99'
                    ),
                    'cxx': (
                        '/builds/slave/m-rel-l64-00000000000000000000/build/'
                        'src/gcc/bin/g++ -std=gnu++11'
                    ),
                    'host': 'x86_64-pc-linux-gnu',
                    'ld': 'ld',
                    'target': 'x86_64-pc-linux-gnu',
                    'number': 2
                },
                'source': {
                    'product': 'firefox',
                    'revision': '44d6a57ab554308585a67a13035d31b264be781e',
                    'repository': (
                        'https://hg.mozilla.org/releases/mozilla-release'
                    ),
                    'tree': 'releases/mozilla-release'
                },
                'target': {
                    'platform': 'linux-x86_64',
                    'os': 'linux',
                    'locale': 'fr',
                    'version': '52.0',
                    'channel': 'release'
                },
                'download': {
                    'url': (
                        f'{ARCHIVE_URL}pub/firefox/releases/'
                        '52.0/linux-x86_64/fr/firefox-52.0.tar.bz2'
                    ),
                    'mimetype': 'application/x-bzip2',
                    'size': 60000,
                    'date': '2017-06-02T15:20:10Z'
                }
            }
        }, {
            'data': {
                'id': 'firefox_beta_55-0b9rc2_win64_zh-tw',
                'download': {
                    'date': '2017-07-13T23:37:23Z',
                    'mimetype': 'application/msdos-windows',
                    'size': 37219504,
                    'url': (
                        f'{ARCHIVE_URL}pub/firefox/candidates/'
                        '55.0b9-candidates/build2/win64/zh-TW/'
                        'Firefox Setup 55.0b9.exe'
                    ),
                },
                'build': {
                    'id': '20170713130618',
                    'date': '2017-07-13T13:06:18Z',
                    'number': 2,
                    'as': 'ml64.exe',
                    'cc': (
                        'c:/builds/moz2_slave/m-beta-w64-0000000000000000000/'
                        'build/src/vs2015u3/VC/bin/amd64/cl.exe'
                    ),
                    'cxx': (
                        'c:/builds/moz2_slave/m-beta-w64-0000000000000000000/'
                        'build/src/vs2015u3/VC/bin/amd64/cl.exe'
                    ),
                    'host': 'x86_64-pc-mingw32',
                    'target': 'x86_64-pc-mingw32'
                },
                'source': {
                    'product': 'firefox',
                    'revision': '91e10e2411762dea81d5df70d9fefe96fe619353',
                    'repository': (
                        'https://hg.mozilla.org/releases/mozilla-beta'
                    ),
                    'tree': 'releases/mozilla-beta'
                },
                'target': {
                    'channel': 'beta',
                    'locale': 'zh-TW',
                    'platform': 'win64',
                    'os': 'win',
                    'version': '55.0b9rc2'
                }
            }
        }, {
            'data': {
                'id': 'devedition_aurora_55-0b1rc5_win64_pt-br',
                'source': {
                    'product': 'devedition',
                    'revision': '6872377277a618b2b9e0d2b4c2b9e51765ac199e',
                    'repository': (
                        'https://hg.mozilla.org/releases/mozilla-beta'
                    ),
                    'tree': 'releases/mozilla-beta'
                },
                'target': {
                    'platform': 'win64',
                    'os': 'win',
                    'locale': 'pt-BR',
                    'version': '55.0b1rc5',
                    'channel': 'aurora'
                },
                'download': {
                    'url': (
                        f'{ARCHIVE_URL}pub/devedition/'
                        'candidates/55.0b1-candidates/build5/win64/'
                        'pt-BR/Firefox Setup 55.0b1.exe'
                    ),
                    'mimetype': 'application/msdos-windows',
                    'size': 53718907,
                    'date': '2017-06-14T00:41:56Z'
                },
                'build': {
                    'id': '20170612224034',
                    'date': '2017-06-12T22:40:34Z',
                    'number': 5,
                    'as': 'ml64.exe',
                    'cc': (
                        'c:/builds/moz2_slave/m-beta-w64-de-0000000000000000/'
                        'build/src/vs2015u3/VC/bin/amd64/cl.exe'
                    ),
                    'cxx': (
                        'c:/builds/moz2_slave/m-beta-w64-de-0000000000000000/'
                        'build/src/vs2015u3/VC/bin/amd64/cl.exe'
                    ),
                    'date': '2017-06-12T22:40:34Z',
                    'host': 'x86_64-pc-mingw32',
                    'target': 'x86_64-pc-mingw32'
                }
            }
        }, {
            'data': {
                'id': 'firefox_beta_51-0b11_macosx-eme-free_mr',
                'build': {
                    'as': '$(CC)',
                    'cc': (
                        '/usr/local/bin/ccache '
                        '/builds/slave/m-beta-m64-0000000000000000000/build/'
                        'src/clang/bin/clang -arch x86_64 -std=gnu99'
                    ),
                    'cxx': (
                        '/usr/local/bin/ccache '
                        '/builds/slave/m-beta-m64-0000000000000000000/build/'
                        'src/clang/bin/clang++ -arch x86_64 -std=gnu++11'
                    ),
                    'date': '2017-01-03T03:11:19Z',
                    'host': 'x86_64-apple-darwin11.2.0',
                    'id': '20170103031119',
                    'ld': 'ld',
                    'number': 1,
                    'target': 'x86_64-apple-darwin11.2.0'
                },
                'download': {
                    'date': '2017-01-04T00:05:18Z',
                    'mimetype': 'application/x-apple-diskimage',
                    'size': 85984611,
                    'url': (
                        f'{ARCHIVE_URL}pub/firefox/releases/'
                        '51.0b11/mac-EME-free/mr/Firefox 51.0b11.dmg'
                    ),
                },
                'source': {
                    'product': 'firefox',
                    'repository': (
                        'https://hg.mozilla.org/releases/mozilla-beta'
                    ),
                    'revision': '0a17d39220700e742bf37a960967480b2f8159f1',
                    'tree': 'releases/mozilla-beta'
                },
                'target': {
                    'channel': 'beta',
                    'locale': 'mr',
                    'os': 'mac',
                    'platform': 'macosx-eme-free',
                    'version': '51.0b11'
                }
            }
        }, {
            'data': {
                'download': {
                    'date': '2015-10-16T23:25:18Z',
                    'mimetype': 'application/x-apple-diskimage',
                    'size': 18694173,
                    'url': (
                        f'{ARCHIVE_URL}pub/mobile/nightly/'
                        '2011/01/2011-01-27-03-mozilla-central-macosx/'
                        'fennec-4.0b5pre.en-US.mac.dmg'
                    )
                },
                'id': (
                    'fennec_nightly_2011-01-27-03-mozilla-central_4-0b5'
                    'pre_macosx_en-us'
                ),
                'source': {
                    'product': 'fennec',
                    'repository': 'http://hg.mozilla.org/mozilla-central',
                    'revision': 'b5314bc1a926',
                    'tree': 'mozilla-central',
                },
                'build': {
                    'date': '2011-01-27T03:25:41Z',
                    'id': '20110127032541'
                },
                'target': {
                    'channel': 'nightly',
                    'locale': 'en-US',
                    'os': 'mac',
                    'platform': 'macosx',
                    'version': '4.0b5pre'
                }
            }
        }, {
            'data': {
                'source': {
                    'product': 'firefox',
                    'revision': 'f6df375b86987b2772067a61873ebfe3a98c353a',
                    'repository': 'https://hg.mozilla.org/mozilla-central',
                    'tree': 'mozilla-central',
                },
                'target': {
                    'platform': 'win32',
                    'os': 'win',
                    'locale': 'en-US',
                    'version': '65.0a1',
                    'channel': 'nightly',
                },
                'download': {
                    'url': (
                        f'{ARCHIVE_URL}pub/firefox/nightly'
                        '/2018/11/2018-11-13-10-00-51-mozilla-central/'
                        'firefox-65.0a1.en-US.win32.installer.exe'
                    ),
                    'mimetype': 'application/msdos-windows',
                    'size': 50000,
                    'date': '2018-11-13T13:10:00Z',
                },
                'id': 'firefox_nightly_2018-11-13-10-00-51_65-0a1_win32_en-us',
                'build': {
                    'id': '20181113100051',
                    'date': '2018-11-13T10:00:51Z',
                    'as': 'z:/build/build/src/vs2017_15.8.4/VC/bin/Hostx64/x86/ml.exe',
                    'cc': (
                        'z:/build/build/src/clang/bin/clang-cl.exe -Xclang '
                        '-std=gnu99 -fms-compatibility-version=19.15.26726 -m32'
                    ),
                    'cxx': (
                        'z:/build/build/src/clang/bin/clang-cl.exe '
                        '-fms-compatibility-version=19.15.26726 -m32'
                    ),
                    'host': 'x86_64-pc-mingw32',
                    'target': 'i686-pc-mingw32',
                },
            }
        }, {
            'data': {
                'source': {
                    'product': 'firefox',
                    'revision': 'f6df375b86987b2772067a61873ebfe3a98c353a',
                    'repository': 'https://hg.mozilla.org/mozilla-central',
                    'tree': 'mozilla-central',
                },
                'target': {
                    'platform': 'macosx',
                    'os': 'mac',
                    'locale': 'en-US',
                    'version': '65.0a1',
                    'channel': 'nightly',
                },
                'download': {
                    'url': (
                        f'{ARCHIVE_URL}pub/firefox/nightly'
                        '/2018/11/2018-11-13-10-00-51-mozilla-central/'
                        'firefox-65.0a1.en-US.mac.dmg'
                    ),
                    'mimetype': 'application/x-apple-diskimage',
                    'size': 50000,
                    'date': '2018-11-13T13:10:00Z',
                },
                'id': 'firefox_nightly_2018-11-13-10-00-51_65-0a1_macosx_en-us',
                'build': {
                    'id': '20181113100051',
                    'date': '2018-11-13T10:00:51Z',
                    'as': (
                        '/builds/worker/workspace/build/src/clang/bin/clang '
                        '-target x86_64-apple-darwin11 -B /builds/worker/workspace/'
                        'build/src/cctools/bin -isysroot /builds/worker/workspace/'
                        'build/src/MacOSX10.11.sdk -std=gnu99'
                    ),
                    'cc': (
                        '/builds/worker/workspace/build/src/clang/bin/clang '
                        '-target x86_64-apple-darwin11 -B /builds/worker/workspace/'
                        'build/src/cctools/bin -isysroot /builds/worker/workspace/'
                        'build/src/MacOSX10.11.sdk -std=gnu99'
                    ),
                    'cxx': (
                        '/builds/worker/workspace/build/src/clang/bin/clang++ '
                        '-target x86_64-apple-darwin11 -B /builds/worker/workspace/'
                        'build/src/cctools/bin -isysroot /builds/worker/workspace/'
                        'build/src/MacOSX10.11.sdk'
                    ),
                    'host': 'x86_64-pc-linux-gnu',
                    'target': 'x86_64-apple-darwin',
                },
            }
        }, {
            'data': {
                'source': {
                    'product': 'firefox',
                    'revision': 'f6df375b86987b2772067a61873ebfe3a98c353a',
                    'repository': 'https://hg.mozilla.org/mozilla-central',
                    'tree': 'mozilla-central',
                },
                'target': {
                    'platform': 'linux-x86_64',
                    'os': 'linux',
                    'locale': 'en-US',
                    'version': '65.0a1',
                    'channel': 'nightly',
                },
                'download': {
                    'url': (
                        f'{ARCHIVE_URL}pub/firefox/nightly'
                        '/2018/11/2018-11-13-10-00-51-mozilla-central/'
                        'firefox-65.0a1.en-US.linux-x86_64.tar.bz2'
                    ),
                    'mimetype': 'application/x-bzip2',
                    'size': 50000,
                    'date': '2018-11-13T13:10:00Z',
                },
                'id': 'firefox_nightly_2018-11-13-10-00-51_65-0a1_linux-x86_64_en-us',
                'build': {
                    'id': '20181113100051',
                    'date': '2018-11-13T10:00:51Z',
                    'as': '/builds/worker/workspace/build/src/clang/bin/clang -std=gnu99',
                    'cc': '/builds/worker/workspace/build/src/clang/bin/clang -std=gnu99',
                    'cxx': '/builds/worker/workspace/build/src/clang/bin/clang++',
                    'host': 'x86_64-pc-linux-gnu',
                    'target': 'x86_64-pc-linux-gnu',
                },
            }
        }]

        assert len(records) == len(expected), [r['data']['id'] for r in records]
        assert [
            r['data']['id'] for r in records
        ] == [
            r['data']['id'] for r in expected
        ], [r['data']['id'] for r in records]
        assert records == expected
