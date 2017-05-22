import pytest
from buildhub.scrape_archives import archive, archive_url

ARCHIVE_INFOS = [
    (("firefox", "55.0a1", "win64", "en-US", "nightly",
      "https://archive.mozilla.org/pub/firefox/nightly/2017/05/2017-05-03-03-02-12-"
      "mozilla-central/firefox-55.0a1.en-US.win64.zip", 56704543, "2017-05-03T12:57:55Z"), {
        "moz_source_stamp": "82c2d17e74ef9cdf38a5d5ac4eb3ae846ec30ba4",
        "moz_update_channel": "nightly",
        "moz_source_repo": "MOZ_SOURCE_REPO=https://hg.mozilla.com/mozilla-central",
        "buildid": "20170503030212",
      }, {
          "target": {
              "locale": "en-US",
              "version": "55.0a1",
              "platform": "win64",
              "channel": "nightly"
          },
          "download": {
              "size": 56704543,
              "mimetype": "application/zip",
              "date": "2017-05-03T12:57:55Z",
              "url": "https://archive.mozilla.org/pub/firefox/nightly/2017/05/"
              "2017-05-03-03-02-12-mozilla-central/firefox-55.0a1.en-US.win64.zip"
          },
          "systemaddons": None,
          "build": {
              "date": "2017-05-03T03:02:00",
              "id": "20170503030212"
          },
          "id": "firefox_2017-05-03-03-02-12_55-0a1_win64_en-us",
          "source": {
              "tree": "mozilla-central",
              "product": "firefox",
              "revision": "82c2d17e74ef9cdf38a5d5ac4eb3ae846ec30ba4"
          }
      }),
]


@pytest.mark.parametrize("info,metadata,expected_record", ARCHIVE_INFOS)
def test_archive(info, metadata, expected_record):
    assert archive(*info, metadata=metadata) == expected_record


ARCHIVE_URL_INFOS = [
    (("firefox", "55.0", "win64", "fr", False, None),
     "https://archive.mozilla.org/pub/firefox/releases/55.0/win64/fr/"),
    (("firefox", "55.0a1", "win64", "en-US", "2017/05", None),
     "https://archive.mozilla.org/pub/firefox/nightly/2017/05/"),
    (("firefox", "55.0", "win64", "fr", False, "/"),
     "https://archive.mozilla.org/pub/firefox/candidates/55.0-candidates/win64/fr/"),
]


@pytest.mark.parametrize("info,expected_record", ARCHIVE_URL_INFOS)
def test_archive_url(info, expected_record):
    assert archive_url(*info) == expected_record
