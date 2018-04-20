# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, you can obtain one at http://mozilla.org/MPL/2.0/.

import json
import os
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
        self.old_cache_file = str(tmpdir.join('old.json'))

    def test_records_are_not_duplicated(self):
        mocked = MagicMock()

        mocked.session.server_url = 'http://localhost:8888/v1'
        # First, populate the cache.
        mocked.get_records.return_value = [
            {'id': 'a', 'title': 'a', 'last_modified': 1}
        ]
        first = fetch_existing(mocked, cache_file=self.cache_file)
        assert isinstance(first, dict)
        assert len(first) == 1
        assert first['a'][0] == 1  # [0] is the last_modified
        first_hash = first['a'][1]  # [1] is the hash string

        mocked.get_records.return_value = [
            {'id': 'a', 'title': 'b', 'last_modified': 2}
        ]
        second = fetch_existing(mocked, cache_file=self.cache_file)
        assert isinstance(first, dict)
        assert len(second) == 1
        assert second['a'][0] == 2
        second_hash = second['a'][1]
        assert first_hash != second_hash

    def test_dump_file_cache_migration(self):
        # Make sure the new cache file doesn't exist
        if os.path.exists(self.cache_file):
            os.remove(self.cache_file)
        # The old dump used to a list of records.
        with open(self.old_cache_file, 'w') as f:
            records = [
                {'id': 'a', 'last_modified': 1, 'title': 'a'}
            ]
            json.dump(records, f)
        mocked = MagicMock()
        mocked.session.server_url = 'http://localhost:8888/v1'
        # First, populate the cache.
        mocked.get_records.return_value = [
            {'id': 'a', 'title': 'b', 'last_modified': 2},
        ]
        fetch_existing(
            mocked,
            cache_file=self.cache_file,
            old_cache_file=self.old_cache_file
        )
        assert not os.path.exists(self.old_cache_file)
        with open(self.cache_file) as f:
            records = json.load(f)
            assert len(records) == 1
            assert records['a'][0] == 2  # [0] is last modified

        # The migration is done, but let's make sure the fetch_existing
        # continues to work as expected.
        # Prend the get_records() is more realistically called with an
        # ?since=etag so this, second time, it won't include
        # the previous `{'id': 'a', 'title': 'b', 'last_modified': 2}` record.
        mocked.get_records.return_value = [
            {'id': 'b', 'title': 'bee', 'last_modified': 3},
        ]
        fetch_existing(
            mocked,
            cache_file=self.cache_file,
            old_cache_file=self.old_cache_file
        )
        assert not os.path.exists(self.old_cache_file)  # still
        with open(self.cache_file) as f:
            records = json.load(f)
            assert len(records) == 2
