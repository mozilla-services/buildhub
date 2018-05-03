# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, you can obtain one at http://mozilla.org/MPL/2.0/.

import unittest
# Because you can't just import unittest and access 'unittest.mock.MagicMock'
from unittest.mock import MagicMock

import pytest

from buildhub.to_kinto import fetch_existing


class CacheValueTest(unittest.TestCase):

    @pytest.fixture(autouse=True)
    def init_cache_files(self, tmpdir):
        # Use str() on these LocalPath instances to turn them into plain
        # strings since to_kinto.fetch_existing() expects it to be a string.
        self.cache_file = str(tmpdir.join('cache.json'))

    def test_records_are_not_duplicated(self):
        mocked = MagicMock()

        mocked.session.server_url = 'http://localhost:8888/v1'
        # First, populate the cache.
        mocked.session.request.return_value = (
            {
                'data': [{'id': 'a', 'title': 'a', 'last_modified': 1}]
            },
            {}  # headers
        )
        first = fetch_existing(mocked, cache_file=self.cache_file)
        assert isinstance(first, dict)
        assert len(first) == 1
        assert first['a'][0] == 1  # [0] is the last_modified
        first_hash = first['a'][1]  # [1] is the hash string

        # Now that the cache file exists, it will use the regular
        # client.get_records call.
        mocked.get_records.return_value = [
            {'id': 'a', 'title': 'b', 'last_modified': 2}
        ]
        second = fetch_existing(mocked, cache_file=self.cache_file)
        assert isinstance(first, dict)
        assert len(second) == 1
        assert second['a'][0] == 2
        second_hash = second['a'][1]
        assert first_hash != second_hash
