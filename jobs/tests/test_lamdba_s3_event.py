import unittest
from unittest import mock

from buildhub.lambda_s3_event import lambda_handler


def fake_event(key):
    return {
        "eventTime": "2017-08-08T17:06:52.030Z",
        "Records": [{
            "s3": {
                "bucket": {"name": "abc"},
                "object": {
                    "key": key,
                    "size": 51001024
                }
            }
        }]
    }


class FromArchive(unittest.TestCase):
    def setUp(self):
        patch = mock.patch("buildhub.lambda_s3_event.kinto_http.Client.create_record")
        self.addCleanup(patch.stop)
        self.mock_create_record = patch.start()

    def test_from_release_archive(self):
        event = fake_event("pub/firefox/releases/54.0/win64/fr/Firefox Setup 54.0.exe")
        lambda_handler(event, None)

        self.mock_create_record.assert_called_with(
            bucket='build-hub',
            collection='releases',
            data={
                'id': 'firefox_54-0_win64_fr',
                'source': {
                    'product': 'firefox'
                },
                'target': {
                    'platform': 'win64',
                    'os': 'win',
                    'locale': 'fr',
                    'version': '54.0',
                    'channel': 'release'
                },
                'download': {
                    'url': 'https://archive.mozilla.org/pub/firefox/releases/54.0/'
                           'win64/fr/Firefox Setup 54.0.exe',
                    'mimetype': 'application/msdos-windows',
                    'size': 51001024,
                    'date': '2017-08-08T17:06:52Z'
                },
            },
            if_not_exists=True)

    def test_from_nightly_archive(self):
        event = fake_event("pub/firefox/nightly/2017/08/2017-08-05-10-03-34-"
                           "mozilla-central-l10n/firefox-57.0a1.ru.win32.zip")
        lambda_handler(event, None)

        self.mock_create_record.assert_called_with(
            bucket='build-hub',
            collection='releases',
            data={
                'id': 'firefox_nightly_2017-08-05-10-03-34_57-0a1_win32_ru',
                'source': {
                    'product': 'firefox'
                },
                'target': {
                    'platform': 'win32',
                    'os': 'win',
                    'locale': 'ru',
                    'version': '57.0a1',
                    'channel': 'nightly'
                },
                'download': {
                    'url': 'https://archive.mozilla.org/pub/firefox/nightly/2017/08/'
                           '2017-08-05-10-03-34-mozilla-central-l10n/firefox-57.0a1.ru.win32.zip',
                    'mimetype': 'application/zip',
                    'size': 51001024,
                    'date': '2017-08-08T17:06:52Z'
                },
            },
            if_not_exists=True)

    def test_from_rc_archive(self):
        event = fake_event("pub/firefox/candidates/51.0-candidates/build1/linux-x86_64-EME-free/"
                           "zh-TW/firefox-51.0.tar.bz2")
        lambda_handler(event, None)

        self.mock_create_record.assert_called_with(
            bucket='build-hub',
            collection='releases',
            data={
                'id': 'firefox_51-0rc1_linux-x86_64-eme-free_zh-tw',
                'source': {
                    'product': 'firefox'
                },
                'target': {
                    'platform': 'linux-x86_64-eme-free',
                    'os': 'linux',
                    'locale': 'zh-TW',
                    'version': '51.0rc1',
                    'channel': 'release'
                },
                'download': {
                    'url': 'https://archive.mozilla.org/pub/firefox/candidates/51.0-candidates/'
                           'build1/linux-x86_64-EME-free/zh-TW/firefox-51.0.tar.bz2',
                    'mimetype': 'application/x-bzip2',
                    'size': 51001024,
                    'date': '2017-08-08T17:06:52Z'
                },
            },
            if_not_exists=True)
