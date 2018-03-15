# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, you can obtain one at http://mozilla.org/MPL/2.0/.

import base64

import asynctest

from buildhub.lambda_s3_inventory import list_manifest_entries, download_csv


class ListManifest(asynctest.TestCase):
    def setUp(self):
        class FakePaginator:
            async def paginate(self, *args, **kwargs):
                yield {'CommonPrefixes': [{'Prefix': 'some-prefix/2017-01-02T03-05Z/'}]}
                yield {'CommonPrefixes': [{'Prefix': 'some-prefix/2017-01-02T03-04Z/'}]}
                yield {'CommonPrefixes': [{'Prefix': 'some-prefix/2017-01-02T03-06Z/'},
                                          {'Prefix': 'some-prefix/data/'}]}
                yield {'CommonPrefixes': [{'Prefix': 'some-prefix/hive/'}]}

        class FakeStream:
            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                return self

            async def read(self):
                return b'{"files": [{"key": "a/b"}, {"key": "c/d"}]}'

        class FakeClient:
            def get_paginator(self, *args):
                return FakePaginator()

            async def get_object(self, Bucket, Key):
                if Key.endswith('some-prefix/2017-01-02T03-06Z/manifest.json'):
                    return {'Body': FakeStream()}

        self.client = FakeClient()

    async def test_return_keys_of_latest_manifest(self):
        results = []
        async for r in list_manifest_entries(self.loop, self.client, 'firefox'):
            results.append(r)
        assert results == ['a/b', 'c/d']


class DownloadCSV(asynctest.TestCase):
    def setUp(self):
        class FakeStream:
            async def __aenter__(self):
                self.content = [
                    # echo -n "1;2;3;4\n5;6" | gzip -cf | base64
                    base64.b64decode('H4sIADPbllkAAzO0NrI2tjbhMrU2AwDZEJLXCwAAAA=='),
                    None,
                ]
                return self

            async def __aexit__(self, *args):
                return self

            async def read(self, size):
                return self.content.pop(0)

        class FakeClient:
            async def get_object(self, Bucket, Key):
                if Key.endswith('public/key-1'):
                    return {'Body': FakeStream()}

        self.client = FakeClient()

    async def test_unzip_chunks(self):

        async def keys():
            yield 'key-1'

        keys = keys()
        results = []
        async for r in download_csv(self.loop, self.client, keys):
            results.append(r)
        assert results == [b"1;2;3;4\n5;6"]
