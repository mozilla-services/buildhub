from io import BytesIO
from unittest import mock

import pytest

from buildhub.lambda_s3_event import lambda_handler


def test_event_handler():
    event = {
        "eventTime": "2017-08-08T17:06:52.030Z",
        "Records": [{
            "s3": {
                "bucket": {"name": "abc"},
                "object": {
                    "key": "pub/firefox/releases/54.0/win64/fr/Firefox Setup 54.0.exe",
                    "size": 51001024
                }
            }
        }]
    }

    with mock.patch("buildhub.lambda_s3_event.kinto_http.Client.create_record") as mock_create_record:
        lambda_handler(event, None)

        mock_create_record.assert_called_with(
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
