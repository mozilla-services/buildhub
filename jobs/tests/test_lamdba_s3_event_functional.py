import unittest
import os
import json

import kinto_http

from buildhub import lambda_s3_event


here = os.path.dirname(__file__)

server = "http://localhost:8888/v1"
bid = "build-hub"
cid = "releases"


class LambdaTest(unittest.TestCase):
    def setUp(self):
        filename = os.path.join(here, 'data', 's3-event-simple.json')
        self.event = json.load(open(filename, "r"))

    def test_load_into_kinto(self):
        lambda_s3_event.lambda_handler(self.event, None)

        rid = "firefox_54-0_win64_fr"

        client = kinto_http.Client(server_url=server)
        record = client.get_record(bucket=bid, collection=cid, id=rid)["data"]
        record.pop("last_modified")
        assert record == {
            'id': 'firefox_54-0_win64_fr',
            'source': {
                'repository': 'https://hg.mozilla.org/releases/mozilla-release',
                'revision': 'e832ed037a3c23004be73178e546d240e57b6ee1',
                'product': 'firefox',
                'tree': 'releases/mozilla-release'
            },
            'download': {
                'mimetype': 'application/msdos-windows',
                'url': 'https://archive.mozilla.org/pub/firefox/releases/'
                       '54.0/win64/fr/Firefox Setup 54.0.exe',
                'size': 51001024,
                'date': '2017-08-08T17:06:52Z'
            },
            'target': {
                'locale': 'fr',
                'platform': 'win64',
                'os': 'win',
                'version': '54.0',
                'channel': 'release'
            },
            'build': {
                'as': 'ml64.exe',
                'cc': 'c:/builds/moz2_slave/m-rel-w64-00000000000000000000/build/'
                      'src/vs2015u3/VC/bin/amd64/cl.exe',
                'cxx': 'c:/builds/moz2_slave/m-rel-w64-00000000000000000000/build/'
                       'src/vs2015u3/VC/bin/amd64/cl.exe',
                'date': '2017-06-08T10:58:25Z',
                'host': 'x86_64-pc-mingw32',
                'id': '20170608105825',
                'number': 3,
                'target': 'x86_64-pc-mingw32'
            }
        }
