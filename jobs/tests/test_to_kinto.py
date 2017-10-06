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
        except:
            pass

    def test_records_are_not_duplicated(self):
        mocked = mock.MagicMock()
        mocked.session.server_url = 'http://localhost:8888/v1'
        # First, populate the cache.
        mocked.get_records.return_value = [{'id': 'a', 'title': 'a', 'last_modified': 1}]
        fetch_existing(mocked, self.cache_file)

        mocked.get_records.return_value = [{'id': 'a', 'title': 'b', 'last_modified': 2}]
        second = fetch_existing(mocked, self.cache_file)

        assert len(second) == 1
        assert second[0]['title'] == 'b'
