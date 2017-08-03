import asynctest
import os
import io
import json
import sys

from buildhub import inventory_to_records


here = os.path.dirname(__file__)


class CsvToRecordsTest(asynctest.TestCase):
    def setUp(self):
        self.stdout = sys.stdout
        self.stdin = sys.stdin
        self.argv = sys.argv

        filename = os.path.join(here, 'data', 'inventory-simple.csv')
        sys.stdin = open(filename, "r")
        sys.stdout = io.StringIO()
        sys.argv = ["inventory-to-records"]

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
                    'version': '1.5b2'
                }
            }
        }]
