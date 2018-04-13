# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, you can obtain one at http://mozilla.org/MPL/2.0/.

import os
import tempfile
import unittest
from unittest import mock

from buildhub.to_kinto import fetch_existing


class CacheValueTest(unittest.TestCase):
    def setUp(self):
        self.cache_file = os.path.join(tempfile.gettempdir(), 'cache.dat')

    def tearDown(self):
        try:
            os.path.remove(self.cache_file)
        except Exception:
            pass

    def test_records_are_not_duplicated(self):
        mocked = mock.MagicMock()
        mocked.session.server_url = 'http://localhost:8888/v1'
        # First, populate the cache.
        mocked.get_records.return_value = [
            {'id': 'a', 'title': 'a', 'last_modified': 1}
        ]
        first = fetch_existing(mocked, self.cache_file)
        assert isinstance(first, dict)
        assert len(first) == 1
        assert first['a'][0] == 1  # [0] is the last_modified
        first_hash = first['a'][1]  # [1] is the hash string

        mocked.get_records.return_value = [
            {'id': 'a', 'title': 'b', 'last_modified': 2}
        ]
        second = fetch_existing(mocked, self.cache_file)
        assert isinstance(first, dict)
        assert len(second) == 1
        assert second['a'][0] == 2
        second_hash = second['a'][1]  # [1] is the hash string
        assert first_hash != second_hash
