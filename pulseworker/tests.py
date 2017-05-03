import unittest

from main import url2version

class TestUrl2Version(unittest.TestCase):

    def test_extract_from_url(self):
        assert url2version("/firefox-55.0a1.en-US.win32.zip") == "55.0a1"


if __name__ == '__main__':
    unittest.main()
