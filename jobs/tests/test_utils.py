import pytest

from buildhub.utils import (
    archive_url, build_record_id, is_release_build_metadata, is_build_url,
    guess_mimetype, guess_channel, chunked, localize_nightly_url, normalized_platform,
    localize_release_candidate_url, record_from_url, merge_metadata, check_record
)


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


RECORDS = [
    # Old Firefox
    {
        "id": "firefox_1-0rc1_linux-i686_ca-ad",
        "source": {
            "product": "firefox",
        },
        "target": {
            "version": "1.0rc1",
            "platform": "linux-i686",
            "os": "linux",
            "locale": "ca-AD",
            "channel": "release"
        },
        "download": {
            "url": "https://archive.mozilla.org/pub/firefox/releases/1.0rc1/"
            "firefox-1.0rc1.ca-AD.linux-i686.installer.tar.gz",
            "mimetype": "application/x-gzip"
        }
    },

    # Firefox Nightly
    {
        "id": "firefox_nightly_2017-05-15-10-02-38_55-0a1_linux-x86_64_en-us",
        "source": {
            "product": "firefox",
        },
        "target": {
            "version": "55.0a1",
            "platform": "linux-x86_64",
            "os": "linux",
            "locale": "en-US",
            "channel": "nightly"
        },
        "download": {
            "url": "https://archive.mozilla.org/pub/firefox/nightly/2017/05/"
            "2017-05-15-10-02-38-mozilla-central/firefox-55.0a1.en-US.linux-x86_64.tar.bz2",
            "mimetype": "application/x-bzip2"
        }
     },

    # Firefox Aurora
    {
        "id": "firefox_aurora_54-0a2_macosx_en-us",
        "source": {
            "product": "firefox",
        },
        "target": {
            "version": "54.0a2",
            "platform": "macosx",
            "os": "mac",
            "locale": "en-US",
            "channel": "aurora"
        },
        "download": {
            "url": "https://archive.mozilla.org/pub/firefox/nightly/2017/04/"
            "2017-04-03-00-40-02-mozilla-aurora/firefox-54.0a2.en-US.mac.dmg",
            "mimetype": "application/x-apple-diskimage"
        }
    },

    # Firefox DevEdition
    {
        "id": "firefox_aurora_55-0b3_macosx_en-us",
        "source": {
            "product": "firefox",
        },
        "target": {
            "version": "55.0b3",
            "platform": "macosx",
            "os": "mac",
            "locale": "en-US",
            "channel": "aurora"
        },
        "download": {
            "url": "https://archive.mozilla.org/pub/devedition/releases/55.0b3/macosx/en-US/"
            "firefox-55.0b3.dmg",
            "mimetype": "application/x-apple-diskimage"
        }
    },

    # Firefox Beta
    {
        "id": "firefox_beta_52-0b6_linux-x86_64_en-us",
        "source": {
            "product": "firefox",
        },
        "target": {
            "version": "52.0b6",
            "platform": "linux-x86_64",
            "os": "linux",
            "locale": "en-US",
            "channel": "beta"
        },
        "download": {
            "url": "https://archive.mozilla.org/pub/firefox/releases/52.0b6/linux-x86_64/en-US/"
            "firefox-52.0b6.tar.bz2",
            "mimetype": "application/x-bzip2"
        }
    },

    # Firefox Candidates
    {
        "id": "firefox_50-0rc1_linux-x86_64_fr",
        "source": {
            "product": "firefox",
        },
        "target": {
            "version": "50.0rc1",
            "platform": "linux-x86_64",
            "os": "linux",
            "locale": "fr",
            "channel": "release"
        },
        "download": {
            "url": "https://archive.mozilla.org/pub/firefox/candidates/50.0-candidates/build1/"
            "linux-x86_64/fr/firefox-50.0.tar.bz2",
            "mimetype": "application/x-bzip2"
        }
    },

    # Firefox Beta Candidates
    {
        "id": "firefox_beta_55-0b9rc2_win64_zh-tw",
        "source": {
            "product": "firefox",
        },
        "target": {
            "version": "55.0b9rc2",
            "platform": "win64",
            'os': 'win',
            "locale": "zh-TW",
            "channel": "beta"
        },
        "download": {
            "url": "https://archive.mozilla.org/pub/firefox/candidates/55.0b9-candidates/build2/"
            "win64/zh-TW/firefox-55.0b9.zip",
            "mimetype": "application/zip"
        }
    },

    # Firefox Release
    {
        "id": "firefox_52-0_linux-x86_64_fr",
        "source": {
            "product": "firefox",
        },
        "target": {
            "version": "52.0",
            "platform": "linux-x86_64",
            "os": "linux",
            "locale": "fr",
            "channel": "release"
        },
        "download": {
            "url": "https://archive.mozilla.org/pub/firefox/releases/52.0/linux-x86_64/fr/"
            "firefox-52.0.tar.bz2",
            "mimetype": "application/x-bzip2"
        }
    },

    # Firefox ESR
    {
        "id": "firefox_esr_52-0esr_linux-x86_64_en-us",
        "source": {
            "product": "firefox",
        },
        "target": {
            "version": "52.0esr",
            "platform": "linux-x86_64",
            "os": "linux",
            "locale": "en-US",
            "channel": "esr"
        },
        "download": {
            "url": "https://archive.mozilla.org/pub/firefox/releases/52.0esr/linux-x86_64/en-US/"
            "firefox-52.0esr.tar.bz2",
            "mimetype": "application/x-bzip2"
        }
    },

    # Firefox Win release
    {
        "id": "firefox_beta_16-0b6_win32_bs",
        "source": {
            "product": "firefox",
        },
        "target": {
            "version": "16.0b6",
            "platform": "win32",
            "os": "win",
            "locale": "bs",
            "channel": "beta"
        },
        "download": {
            "url": "https://archive.mozilla.org/pub/firefox/releases/16.0b6/win32/bs/"
            "Firefox Setup 16.0b6.exe",
            "mimetype": "application/msdos-windows"
        }
    },

    # Firefox MacOSX release
    {
        "id": "firefox_50-0-1_macosx_ko",
        "source": {
            "product": "firefox",
        },
        "target": {
            "version": "50.0.1",
            "platform": "macosx",
            "os": "mac",
            "locale": "ko",
            "channel": "release"
        },
        "download": {
            "url": "https://archive.mozilla.org/pub/firefox/releases/50.0.1/mac/ko/"
            "Firefox 50.0.1.dmg",
            "mimetype": "application/x-apple-diskimage"
        }
    },

    # Firefox funnelcake
    {
        'id': 'firefox_22-0-funnelcake23_linux-i686_id',
        'source': {
            'product': 'firefox'
        },
        'target': {
            'locale': 'id',
            'version': '22.0-funnelcake23',
            'platform': 'linux-i686',
            "os": "linux",
            'channel': 'release'
        },
        'download': {
            'url': ('https://archive.mozilla.org/pub/firefox/releases/'
                    '22.0-funnelcake23/linux-i686/id/firefox-22.0.tar.bz2'),
            'mimetype': 'application/x-bzip2',
        }
    },

    # Firefox real version (?)
    {
        'id': 'firefox_3-0-19-real-real_linux-i686_si',
        'source': {
            'product': 'firefox'
        },
        'target': {
            'locale': 'si',
            'version': '3.0.19-real-real',
            'platform': 'linux-i686',
            "os": "linux",
            'channel': 'release'
        },
        'download': {
            'url': ('https://archive.mozilla.org/pub/firefox/releases/3.0.19-real-real/'
                    'linux-i686/si/firefox-3.0.19.tar.bz2'),
            'mimetype': 'application/x-bzip2'
        }
    },

    # Firefox plugin version (?)
    {
        'id': 'firefox_3-6-3plugin1_linux-i686_fi',
        'source': {
            'product': 'firefox'
        },
        'target': {
            'locale': 'fi',
            'version': '3.6.3plugin1',
            'platform': 'linux-i686',
            "os": "linux",
            'channel': 'release'
        },
        'download': {
            'url': ('https://archive.mozilla.org/pub/firefox/releases/3.6.3plugin1/'
                    'linux-i686/fi/firefox-3.6.3plugin1.tar.bz2'),
            'mimetype': 'application/x-bzip2'
        }
    },

    # Firefox second beta
    {
        'source': {
            'product': 'firefox'
        },
        'id': 'firefox_beta_38-0-5b1-2_linux-i686_es-ar',
        'target': {
            'locale': 'es-AR',
            'version': '38.0.5b1-2',
            'platform': 'linux-i686',
            "os": "linux",
            'channel': 'beta'
        },
        'download': {
            'url': ('https://archive.mozilla.org/pub/firefox/releases/38.0.5b1-2/'
                    'linux-i686/es-AR/firefox-38.0.5b1.tar.bz2'),
            'mimetype': 'application/x-bzip2'
        }
    },

    # Firefox preview
    {
        'source': {
            'product': 'firefox'
        },
        'id': 'firefox_nightly_2010-03-28-03-mozilla-central_3-7a4pre_win32_en-us',
        'target': {
            'locale': 'en-US',
            'version': '3.7a4pre',
            'platform': 'win32',
            "os": "win",
            'channel': 'nightly'
        },
        'download': {
            'url': ('https://archive.mozilla.org/pub/firefox/nightly/2010/03/'
                    '2010-03-28-03-mozilla-central/firefox-3.7a4pre.en-US.win32.zip'),
            'mimetype': 'application/zip'
        }
    },

    # Thunderbird Windows Beta
    {
        "id": "thunderbird_beta_11-0b2_win32_eu",
        "source": {
            "product": "thunderbird",
        },
        "target": {
            "version": "11.0b2",
            "platform": "win32",
            "os": "win",
            "locale": "eu",
            "channel": "beta"
        },
        "download": {
            "url": "https://archive.mozilla.org/pub/thunderbird/releases/11.0b2/win32/eu/"
            "Thunderbird Setup 11.0b2.exe",
            "mimetype": "application/msdos-windows"
        }
    },

    # Thunderbird Mac OS X ESR
    {
        "id": "thunderbird_esr_10-0-12esr_macosx_pt-br",
        "source": {
            "product": "thunderbird",
        },
        "target": {
            "version": "10.0.12esr",
            "platform": "macosx",
            "os": "mac",
            "locale": "pt-BR",
            "channel": "esr"
        },
        "download": {
            "url": "https://archive.mozilla.org/pub/thunderbird/releases/10.0.12esr/mac/pt-BR/"
            "Thunderbird 10.0.12esr.dmg",
            "mimetype": "application/x-apple-diskimage"
        }
    },

    # Thunderbird ESR
    {
        "id": "thunderbird_esr_17-0-8esr_linux-x86_64_gd",
        "source": {
            "product": "thunderbird",
        },
        "target": {
            "version": "17.0.8esr",
            "platform": "linux-x86_64",
            "os": "linux",
            "locale": "gd",
            "channel": "esr"
        },
        "download": {
            "url": "https://archive.mozilla.org/pub/thunderbird/releases/17.0.8esr/linux-x86_64/"
            "gd/thunderbird-17.0.8esr.tar.bz2",
            "mimetype": "application/x-bzip2"
        }
    },

    # Thunderbird Pre-ESR Switch Release
    {
        "id": "thunderbird_17-0_linux-x86_64_gd",
        "source": {
            "product": "thunderbird",
        },
        "target": {
            "version": "17.0",
            "platform": "linux-x86_64",
            "os": "linux",
            "locale": "gd",
            "channel": "release"
        },
        "download": {
            "url": "https://archive.mozilla.org/pub/thunderbird/releases/17.0/linux-x86_64/"
            "gd/thunderbird-17.0.tar.bz2",
            "mimetype": "application/x-bzip2"
        }
    },

    # Thunderbird Post-ESR Switch Release
    {
        "id": "thunderbird_24-0_linux-x86_64_gd",
        "source": {
            "product": "thunderbird",
        },
        "target": {
            "version": "24.0",
            "platform": "linux-x86_64",
            "os": "linux",
            "locale": "gd",
            "channel": "release"
        },
        "download": {
            "url": "https://archive.mozilla.org/pub/thunderbird/releases/24.0/linux-x86_64/"
            "gd/thunderbird-24.0.tar.bz2",
            "mimetype": "application/x-bzip2"
        }
    },

    # Fennec
    {
        "id": "fennec_beta_39-0b5_android-api-9_sl",
        "source": {
            "product": "fennec",
        },
        "target": {
            "version": "39.0b5",
            "platform": "android-api-9",
            "os": "android",
            "locale": "sl",
            "channel": "beta"
        },
        "download": {
            "url": "https://archive.mozilla.org/pub/mobile/releases/39.0b5/android-api-9/sl/"
            "fennec-39.0b5.sl.android-arm.apk",
            "mimetype": "application/vnd.android.package-archive"
        }
    },

    # Localized Fennec
    {
        "id": "fennec_beta_42-0b2_android-api-9_fr",
        "source": {
            "product": "fennec",
        },
        "target": {
            "version": "42.0b2",
            "platform": "android-api-9",
            "os": "android",
            "locale": "fr",
            "channel": "beta"
        },
        "download": {
            "url": "https://archive.mozilla.org/pub/mobile/releases/42.0b2/android-api-9/fr/"
            "fennec-42.0b2.fr.android-arm.apk",
            "mimetype": "application/vnd.android.package-archive"
        }
    },


    # Fennec ARM
    {
        "id": "fennec_nightly_2017-05-30-10-01-27_55-0a1_android-api-15_multi",
        "source": {
            "product": "fennec",
        },
        "target": {
            "version": "55.0a1",
            "platform": "android-api-15",
            "os": "android",
            "locale": "multi",
            "channel": "nightly"
        },
        "download": {
            "url": "https://archive.mozilla.org/pub/mobile/nightly/2017/05/2017-05-30-10-01-27-"
            "mozilla-central-android-api-15/fennec-55.0a1.multi.android-arm.apk",
            "mimetype": "application/vnd.android.package-archive"
        }
    },

    {
        "id": "fennec_nightly-old-id_2017-05-30-10-01-27_55-0a1_android-api-15_multi",
        "source": {
            "product": "fennec",
        },
        "target": {
            "version": "55.0a1",
            "platform": "android-api-15",
            "os": "android",
            "locale": "multi",
            "channel": "nightly-old-id"
        },
        "download": {
            "url": "https://archive.mozilla.org/pub/mobile/nightly/2017/05/2017-05-30-10-01-27-"
            "mozilla-central-android-api-15-old-id/fennec-55.0a1.multi.android-arm.apk",
            "mimetype": "application/vnd.android.package-archive"
        }
    },

    # Fennec i386
    {
        "id": "fennec_nightly_2017-05-30-10-01-27_55-0a1_android-i386_multi",
        "source": {
            "product": "fennec",
        },
        "target": {
            "version": "55.0a1",
            "platform": "android-i386",
            "os": "android",
            "locale": "multi",
            "channel": "nightly"
        },
        "download": {
            "url": "https://archive.mozilla.org/pub/mobile/nightly/2017/05/2017-05-30-10-01-27-"
            "mozilla-central-android-x86/fennec-55.0a1.multi.android-i386.apk",
            "mimetype": "application/vnd.android.package-archive"
        }
    },
    {
        "id": "fennec_nightly-old-id_2017-05-30-10-01-27_55-0a1_android-i386_multi",
        "source": {
            "product": "fennec",
        },
        "target": {
            "version": "55.0a1",
            "platform": "android-i386",
            "os": "android",
            "locale": "multi",
            "channel": "nightly-old-id"
        },
        "download": {
            "url": "https://archive.mozilla.org/pub/mobile/nightly/2017/05/2017-05-30-10-01-27-"
            "mozilla-central-android-x86-old-id/fennec-55.0a1.multi.android-i386.apk",
            "mimetype": "application/vnd.android.package-archive"
        }
    },

]


# Build record_id from record
@pytest.mark.parametrize("record", RECORDS)
def test_build_record_id(record):
    record_id = build_record_id(record)
    assert record_id == record["id"]


@pytest.mark.parametrize("record", RECORDS)
def test_check_record(record):
    check_record(record)  # not raising.


RELEASE_METADATA_FILENAMES = [
    ("firefox", "52.0b7", "firefox-52.0b7.json"),
    ("fennec", "51.0b2", "fennec-51.0b2.en-US.android-i386.json"),
    ("devedition", "54.0b11", "firefox-54.0b11.json"),
]


@pytest.mark.parametrize("product,version,filename", RELEASE_METADATA_FILENAMES)
def test_is_release_build_metadata(product, version, filename):
    assert is_release_build_metadata(product, version, filename)


WRONG_RELEASE_METADATA_FILENAMES = [
    ("firefox", "52.0b7", "thunderbird-52.0b7.json"),
    ("fennec", "51.0b2", "fennec-52.0.en-US.android-i386.json"),
    ("fennec", "52.0", "fennec-52.0.en-US.android-i386.asc"),
]


@pytest.mark.parametrize("product,version,filename", WRONG_RELEASE_METADATA_FILENAMES)
def test_wrong_release_metadata(product, version, filename):
    assert not is_release_build_metadata(product, version, filename)


RELEASE_FILENAMES = [
    ("firefox", "firefox-53.0.tar.bz2"),
    ("firefox", "firefox-54.0a2.en-US.mac.dmg"),
    ("firefox", "firefox-52.0b6.tar.bz2"),
    ("firefox", "firefox-50.0.tar.bz2"),
    ("firefox", "firefox-52.0.tar.bz2"),
    ("firefox", "firefox-52.0esr.tar.bz2"),
    ("thunderbird", "thunderbird-17.0.8esr.tar.bz2"),
    ("fennec", "fennec-39.0b5.sl.android-arm.apk"),
    ("fennec", "fennec-42.0b2.fr.android-arm.apk"),
    ("thunderbird", "Thunderbird 10.0.12esr.dmg"),
    ("thunderbird", "Thunderbird Setup 11.0b2.exe"),
    ("firefox", "Firefox Setup 17.0b3.exe"),
    ("firefox", "Firefox 50.0.1.dmg"),
    ("devedition", "Firefox Setup 54.0b11.exe"),
    ("devedition", "firefox-54.0b11.tar.bz2"),
    ("firefox", ("pub/firefox/candidates/50.0-candidates/build1/"
                 "linux-x86_64/fr/firefox-50.0.tar.bz2")),
]


@pytest.mark.parametrize("product,filename", RELEASE_FILENAMES)
def test_is_build_url(product, filename):
    assert is_build_url(product, filename)


WRONG_RELEASE_FILENAMES = [
    ("firefox", "firefox-1.5.0.5.tar.gz.asc"),
    ("firefox", "firefox-52.0.win32.sdk.zip"),
    ("fennec", "fennec-21.0b1.multi.android-arm-armv6.tests.zip"),
    ("fennec", "fennec-24.0b1.en-US.android-arm.crashreporter-symbols.zip"),
    ("firefox", "Firefox Setup Stub 49.0.exe"),
    ("firefox", "/releases/sha1-installers/aurora/firefox-45.0a2.ja.win32.installer.exe"),
    ("firefox", ("/candidates/51.0.1-candidates/build3/funnelcake99-testing/v1/win32/en-US/"
                 "firefox-51.0.1.en-US.win32.installer.exe")),
    ("firefox", "firefox-56.0a1.en-US.win64.stylo-bindings.zip"),
    ("thunderbird", "/pub/thunderbird/releases/1.0rc/thunderbird-1.0rc-win32.zip"),
    ("thunderbird", "/pub/thunderbird/extensions/inspector/thunderbird-dominspector-0.9%2B.zip"),
    ("thunderbird", "/pub/thunderbird/test/inlinespellcheck-test-build/thunderbird-win32.zip"),
    ("thunderbird", "/pub/thunderbird/test/standard8-jmalloc-test/special-test-no-jemalloc.exe"),
    ("firefox", "/pub/firefox/try-builds/jg%40m.com-e/try-win64/firefox-56.0a1.en-US.win64.zip"),
    ("firefox", "/pub/firefox/releases/namoroka/alpha2/wince-arm/en-US/firefox-3.6a2.zip")
]


@pytest.mark.parametrize("product,filename", WRONG_RELEASE_FILENAMES)
def test_wrong_release_url(product, filename):
    assert not is_build_url(product, filename)


URLS_MIMETYPES = [
    ("firefox-55.0a1.en-US.linux-x86_64.tar.bz2", "application/x-bzip2"),
    ("fennec-42.0b2.fr.android-arm.apk", "application/vnd.android.package-archive"),
    ("firefox-52.0.win32.sdk.zip", "application/zip"),
    ("firefox-54.0a2.en-US.mac.dmg", "application/x-apple-diskimage"),
    ("firefox-1.5.0.5.tar.gz", "application/x-gzip"),
    ("firefox-1.5.0.5.tar.gz.asc", None)
]


@pytest.mark.parametrize("url,expected_mimetype", URLS_MIMETYPES)
def test_guess_mimetype(url, expected_mimetype):
    mimetype = guess_mimetype(url)
    assert mimetype == expected_mimetype


@pytest.mark.parametrize("record", RECORDS)
def test_guess_channel(record):
    url = record["download"]["url"]
    version = record["target"]["version"]
    expected_channel = record["target"]["channel"]
    channel = guess_channel(url, version)
    assert channel == expected_channel


CHUNKS = [
    ([], 5, [[]]),
    ([1, 2, 3], 5, [[1, 2, 3]]),
    ([1, 2, 3, 4, 5], 2, [[1, 2], [3, 4], [5]]),
]


@pytest.mark.parametrize("iterable,size,chunks", CHUNKS)
def test_chunked(iterable, size, chunks):
    assert list(chunked(iterable, size)) == chunks


NIGHTLY_URLS = [
    # Mobile ARM not localized
    ("https://archive.mozilla.org/pub/mobile/nightly/2017/05/2017-05-30-10-01-27-"
     "mozilla-central-android-x86-old-id/fennec-55.0a1.multi.android-i386.apk",
     "https://archive.mozilla.org/pub/mobile/nightly/2017/05/2017-05-30-10-01-27-"
     "mozilla-central-android-x86-old-id/fennec-55.0a1.multi.android-i386.apk"),

    # Mobile ARM localized
    ("https://archive.mozilla.org/pub/mobile/nightly/2017/06/2017-06-01-10-02-05-"
     "mozilla-central-android-api-15-l10n/fennec-55.0a1.ar.android-arm.apk",
     "https://archive.mozilla.org/pub/mobile/nightly/2017/06/2017-06-01-10-02-05-"
     "mozilla-central-android-api-15/fennec-55.0a1.multi.android-arm.apk"),

    # Mobile i386 not localized
    ("https://archive.mozilla.org/pub/mobile/nightly/2017/05/2017-05-30-10-01-27-"
     "mozilla-central-android-x86/fennec-55.0a1.multi.android-i386.apk",
     "https://archive.mozilla.org/pub/mobile/nightly/2017/05/2017-05-30-10-01-27-"
     "mozilla-central-android-x86/fennec-55.0a1.multi.android-i386.apk"),

    # firefox Mac not localized
    ("https://archive.mozilla.org/pub/firefox/nightly/2017/05/2017-05-01-03-02-04-"
     "mozilla-central/firefox-55.0a1.en-US.mac.dmg",
     "https://archive.mozilla.org/pub/firefox/nightly/2017/05/2017-05-01-03-02-04-"
     "mozilla-central/firefox-55.0a1.en-US.mac.dmg"),

    # Firefox Mac localized
    ("https://archive.mozilla.org/pub/firefox/nightly/2017/05/2017-05-01-03-02-04-"
     "mozilla-central-l10n/firefox-55.0a1.ach.mac.dmg",
     "https://archive.mozilla.org/pub/firefox/nightly/2017/05/2017-05-01-03-02-04-"
     "mozilla-central/firefox-55.0a1.en-US.mac.dmg"),

    # Firefox linux not localized
    ("https://archive.mozilla.org/pub/firefox/nightly/2017/05/"
     "2017-05-15-10-02-38-mozilla-central/firefox-55.0a1.en-US.linux-x86_64.tar.bz2",
     "https://archive.mozilla.org/pub/firefox/nightly/2017/05/"
     "2017-05-15-10-02-38-mozilla-central/firefox-55.0a1.en-US.linux-x86_64.tar.bz2"),

    # Firefox linux localized
    ("https://archive.mozilla.org/pub/firefox/nightly/2017/05/2017-05-15-10-02-38-"
     "mozilla-central-l10n/firefox-55.0a1.ach.linux-x86_64.tar.bz2",
     "https://archive.mozilla.org/pub/firefox/nightly/2017/05/"
     "2017-05-15-10-02-38-mozilla-central/firefox-55.0a1.en-US.linux-x86_64.tar.bz2"
     ),

    # Some random Mac.
    ("https://archive.mozilla.org/pub/firefox/nightly/2017/06/2017-06-20-03-02-08-"
     "mozilla-central-l10n/firefox-56.0a1.ru.mac.dmg",
     "https://archive.mozilla.org/pub/firefox/nightly/2017/06/2017-06-20-03-02-08-"
     "mozilla-central/firefox-56.0a1.en-US.mac.dmg"),
]


@pytest.mark.parametrize("localized_url,american_url", NIGHTLY_URLS)
def test_localize_nightly_url(localized_url, american_url):
    assert localize_nightly_url(localized_url) == american_url


RC_URLS = [
    ("https://archive.mozilla.org/pub/firefox/candidates/54.0b9-candidates/build1/"
     "win64/ta/Firefox%20Setup%2054.0b9.exe",
     "https://archive.mozilla.org/pub/firefox/candidates/54.0b9-candidates/build1/"
     "win64/en-US/Firefox%20Setup%2054.0b9.exe"),
    ("https://archive.mozilla.org/pub/firefox/candidates/52.0.2-candidates/build1/"
     "linux-x86_64-EME-free/cak/firefox-52.0.2.tar.bz2",
     "https://archive.mozilla.org/pub/firefox/candidates/52.0.2-candidates/build1/"
     "linux-x86_64/en-US/firefox-52.0.2.tar.bz2")
]


@pytest.mark.parametrize("localized_url,american_url", RC_URLS)
def test_localize_rc_url(localized_url, american_url):
    assert localize_release_candidate_url(localized_url) == american_url


@pytest.mark.parametrize("record", RECORDS)
def test_record_from_url(record):
    url = record["download"]["url"]
    from_url = record_from_url(url)
    assert from_url == record


METADATA_RECORDS = [
    ({"source": {"product": "firefox"}}, None, {"source": {"product": "firefox"}}),
    ({
        "target": {"channel": "release"},
        "source": {"product": "firefox"}
     }, {
        "buildid": "201706121152",
        "moz_source_repo": "a",
        "moz_source_stamp": "b",
     }, {
        "target": {"channel": "release"},
        "source": {
            "product": "firefox",
            "revision": "b",
            "repository": "a",
            "tree": "a",
        },
        "build": {
            "date": "2017-06-12T11:05:02Z",
            "id": "201706121152"
        }
    }),
    ({
        "target": {"channel": "release"},
        "source": {"product": "firefox"}
     }, {
        "buildid": "201706121152",
        "buildnumber": 3,
        "moz_source_repo": "MOZ_SOURCE_REPO=https://hg.mozilla.org/central/beta",
        "moz_source_stamp": "b0925nfubg",
     }, {
        "target": {"channel": "release"},
        "source": {
            "product": "firefox",
            "revision": "b0925nfubg",
            "repository": "https://hg.mozilla.org/central/beta",
            "tree": "central/beta",
        },
        "build": {
            "date": "2017-06-12T11:05:02Z",
            "id": "201706121152",
            "number": 3
        }
    }),
]


@pytest.mark.parametrize("record,metadata,expected", METADATA_RECORDS)
def test_merge_metadata(record, metadata, expected):
    result = merge_metadata(record, metadata)
    assert result == expected


NORMALIZED_PLATFORMS = (
    ("android", "android"),
    ("android", "android-aarch64"),
    ("android", "android-api-11"),
    ("android", "android-api-15"),
    ("android", "android-api-9"),
    ("android", "android-arm"),
    ("android", "android-armv6"),
    ("android", "android-i386"),
    ("android", "android-r7"),
    ("android", "android-x86"),
    ("android", "android-xul"),
    ("linux", "linux"),
    ("linux", "linux-i686"),
    ("linux", "linux-x86_64"),
    ("linux", "linux-x86_64-eme-free"),
    ("mac", "mac-EME-free"),
    ("mac", "mac-ppc"),
    ("mac", "mac-shark"),
    ("mac", "mac64"),
    ("mac", "macosx"),
    ("maemo", "maemo"),
    ("maemo", "maemo4"),
    ("maemo", "maemo5-gtk"),
    ("win", "win32"),
    ("win", "win32-EME-free"),
    ("win", "win32-EUballot"),
    ("win", "win32-EUballot-rc2"),
    ("win", "win32-funnelcake26"),
    ("win", "win32-funnelcake27"),
    ("win", "win32-funnelcake28"),
    ("win", "win32-funnelcake29"),
    ("win", "win32-sha1"),
    ("win", "win64"),
    ("win", "win64-EME-free"),
    ("win", "win64-sha1"),
    ("win", "win64-x86_64"),
    ("win", "wince-arm"),
)


@pytest.mark.parametrize("expected,platform", NORMALIZED_PLATFORMS)
def test_normalized_platform(expected, platform):
    result = normalized_platform(platform)
    assert result == expected


def test_normalized_unknown_platform():
    with pytest.raises(ValueError):
        normalized_platform("namokora")
