import asynctest
import os
import io
import json
import sys
from unittest import mock

from buildhub import inventory_to_records


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

    def test_load_simple_file(self):
        inventory_to_records.run()

        output = sys.stdout.getvalue()
        records = [json.loads(o) for o in output.split('\n') if o]
        assert records == [{
            'data': {
                'id': 'firefox_nightly_2017-05-15-10-02-38_55-0a1_linux-x86_64_en-us',
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
                    'url': ('https://archive.mozilla.org/pub/firefox/nightly/'
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
                    'cc': '/builds/slave/m-rel-l64-00000000000000000000/build/src/gcc/bin/gcc '
                          '-std=gnu99',
                    'cxx': '/builds/slave/m-rel-l64-00000000000000000000/build/src/gcc/bin/g++ '
                           '-std=gnu++11',
                    'host': 'x86_64-pc-linux-gnu',
                    'ld': 'ld',
                    'target': 'x86_64-pc-linux-gnu',
                    'number': 2
                },
                'source': {
                    'product': 'firefox',
                    'revision': '44d6a57ab554308585a67a13035d31b264be781e',
                    'repository': 'https://hg.mozilla.org/releases/mozilla-release',
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
                    'url': ('https://archive.mozilla.org/pub/firefox/releases/52.0/'
                            'linux-x86_64/fr/firefox-52.0.tar.bz2'),
                    'mimetype': 'application/x-bzip2',
                    'size': 60000,
                    'date': '2017-06-02T15:20:10Z'
                }
            }
        }, {
            'data': {
                'id': 'firefox_beta_1-5b2_linux-i686_en-us',
                'download': {
                    'date': '2015-10-09T15:20:10Z',
                    'mimetype': 'application/x-gzip',
                    'size': 60000,
                    'url': ('https://archive.mozilla.org/pub/firefox/releases/1.5b2/'
                            'linux-i686/en-US/firefox-1.5b2.tar.gz')
                },
                'source': {
                    'product': 'firefox'
                },
                'target': {
                    'channel': 'beta',
                    'locale': 'en-US',
                    'platform': 'linux-i686',
                    'os': 'linux',
                    'version': '1.5b2'
                }
            }
        }, {
            'data': {
                'id': 'firefox_beta_55-0b9rc2_win64_zh-tw',
                'download': {
                    'date': '2017-07-13T23:37:21Z',
                    'mimetype': 'application/zip',
                    'size': 53251778,
                    'url': 'https://archive.mozilla.org/pub/firefox/candidates/'
                           '55.0b9-candidates/build2/win64/zh-TW/firefox-55.0b9.zip'
                },
                'build': {
                    'id': '20170713130618',
                    'date': '2017-07-13T13:06:18Z',
                    'number': 2,
                    'as': 'ml64.exe',
                    'cc': 'c:/builds/moz2_slave/m-beta-w64-0000000000000000000/build/'
                          'src/vs2015u3/VC/bin/amd64/cl.exe',
                    'cxx': 'c:/builds/moz2_slave/m-beta-w64-0000000000000000000/build/'
                           'src/vs2015u3/VC/bin/amd64/cl.exe',
                    'host': 'x86_64-pc-mingw32',
                    'target': 'x86_64-pc-mingw32'
                },
                'source': {
                    'product': 'firefox',
                    'revision': '91e10e2411762dea81d5df70d9fefe96fe619353',
                    'repository': 'https://hg.mozilla.org/releases/mozilla-beta',
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
                    'repository': 'https://hg.mozilla.org/releases/mozilla-beta',
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
                    'url': 'https://archive.mozilla.org/pub/devedition/candidates/'
                           '55.0b1-candidates/build5/win64/pt-BR/firefox-55.0b1.zip',
                    'mimetype': 'application/zip',
                    'size': 53718907,
                    'date': '2017-06-14T00:41:56Z'
                },
                'build': {
                    'id': '20170612224034',
                    'date': '2017-06-12T22:40:34Z',
                    'number': 5,
                    'as': 'ml64.exe',
                    'cc': 'c:/builds/moz2_slave/m-beta-w64-de-0000000000000000/build/'
                          'src/vs2015u3/VC/bin/amd64/cl.exe',
                    'cxx': 'c:/builds/moz2_slave/m-beta-w64-de-0000000000000000/build/'
                           'src/vs2015u3/VC/bin/amd64/cl.exe',
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
                    'cc': '/usr/local/bin/ccache '
                          '/builds/slave/m-beta-m64-0000000000000000000/build/src/clang/bin/clang '
                          '-arch x86_64 -std=gnu99',
                    'cxx': '/usr/local/bin/ccache '
                           '/builds/slave/m-beta-m64-0000000000000000000/build/src/clang/bin/'
                           'clang++ -arch x86_64 -std=gnu++11',
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
                    'url': 'https://archive.mozilla.org/pub/firefox/releases/51.0b11/mac-EME-free/'
                           'mr/Firefox 51.0b11.dmg'
                },
                'source': {
                    'product': 'firefox',
                    'repository': 'https://hg.mozilla.org/releases/mozilla-beta',
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
        }]
