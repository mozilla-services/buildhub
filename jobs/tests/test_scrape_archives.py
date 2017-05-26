import pytest
from buildhub.scrape_archives import archive, archive_url

ARCHIVE_INFOS = [
    (("firefox", "55.0a1", "win64", "en-US",
      "https://archive.mozilla.org/pub/firefox/nightly/2017/05/2017-05-03-03-02-12-"
      "mozilla-central/firefox-55.0a1.en-US.win64.zip", 56704543, "2017-05-03T12:57:55Z"), {
        "moz_source_stamp": "82c2d17e74ef9cdf38a5d5ac4eb3ae846ec30ba4",
        "moz_update_channel": "nightly",
        "moz_source_repo": "MOZ_SOURCE_REPO=https://hg.mozilla.org/mozilla-central",
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
              "repository": "https://hg.mozilla.org/mozilla-central",
              "product": "firefox",
              "revision": "82c2d17e74ef9cdf38a5d5ac4eb3ae846ec30ba4"
          }
      }),
    (("thunderbird", "52.0.1", "linux-x86_64", "en-US",
      "https://archive.mozilla.org/pub/thunderbird/candidates/52.0.1-candidates/build3/"
      "linux-x86_64/en-US/thunderbird-52.0.1.tar.bz2", 56704543, "2017-05-03T12:57:55Z"), {
        "as": "$(CC)",
        "buildid": "20170413214957",
        "cc": "/builds/slave/tb-rel-c-esr52-l64_bld-0000000/build/gcc/bin/gcc -std=gnu99",
        "cxx": "/builds/slave/tb-rel-c-esr52-l64_bld-0000000/build/gcc/bin/g++ -std=gnu++11",
        "host_alias": "x86_64-pc-linux-gnu",
        "host_cpu": "x86_64",
        "host_os": "linux-gnu",
        "host_vendor": "pc",
        "ld": "ld",
        "moz_app_id": "{3550f703-e582-4d05-9a08-453d09bdfdc6}",
        "moz_app_maxversion": "52.*",
        "moz_app_name": "thunderbird",
        "moz_app_vendor": "",
        "moz_app_version": "52.0.1",
        "moz_pkg_platform": "linux-x86_64",
        "moz_source_repo": "MOZ_SOURCE_REPO=https://hg.mozilla.org/releases/comm-esr52",
        "moz_source_stamp": "3b5381b7085b2edb9f4f8176d7f023cfd74e4f63",
        "moz_update_channel": "release",
        "target_alias": "x86_64-pc-linux-gnu",
        "target_cpu": "x86_64",
        "target_os": "linux-gnu",
        "target_vendor": "pc"
      }, {
          "target": {
              "locale": "en-US",
              "version": "52.0.1",
              "platform": "linux-x86_64",
              "channel": "release"
          },
          "download": {
              "size": 56704543,
              "mimetype": "application/x-bzip2",
              "date": "2017-05-03T12:57:55Z",
              "url": "https://archive.mozilla.org/pub/thunderbird/candidates/"
              "52.0.1-candidates/build3/linux-x86_64/en-US/thunderbird-52.0.1.tar.bz2"
          },
          "systemaddons": None,
          "build": {
              "date": "2017-04-13T21:49:00",
              "id": "20170413214957"
          },
          "id": "thunderbird_52-0-1_linux-x86_64_en-us",
          "source": {
              "tree": "releases/comm-esr52",
              "repository": "https://hg.mozilla.org/releases/comm-esr52",
              "product": "thunderbird",
              "revision": "3b5381b7085b2edb9f4f8176d7f023cfd74e4f63"
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
