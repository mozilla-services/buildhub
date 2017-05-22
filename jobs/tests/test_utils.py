import pytest
from buildhub.utils import (
    build_record_id, parse_nightly_filename, is_release_metadata, is_release_filename
)


RECORDS = [
    # Firefox Nightly
    {
        "id": "firefox_2017-05-15-10-02-38_55-0a1_linux-x86_64_en-us",
        "source": {
            "product": "firefox",
        },
        "target": {
            "version": "55.0a1",
            "platform": "linux-x86_64",
            "locale": "en-US",
            "channel": "nightly"
        },
        "download": {
            "url": "https://archive.mozilla.org/pub/firefox/nightly/2017/05/"
            "2017-05-15-10-02-38-mozilla-central/firefox-55.0a1.en-US.linux-x86_64.tar.bz2"
        }
     },

    # Firefox Aurora
    {
        "id": "firefox_54-0a2_mac_en-us",
        "source": {
            "product": "firefox",
        },
        "target": {
            "version": "54.0a2",
            "platform": "mac",
            "locale": "en-US",
            "channel": "aurora"
        },
        "download": {
            "url": "https://archive.mozilla.org/pub/firefox/nightly/2017/04/"
            "2017-04-03-00-40-02-mozilla-aurora/firefox-54.0a2.en-US.mac.dmg"
        }
    },

    # Firefox Beta
    {
        "id": "firefox_52-0b6_linux-x86_64_en-us",
        "source": {
            "product": "firefox",
        },
        "target": {
            "version": "52.0b6",
            "platform": "linux-x86_64",
            "locale": "en-US",
            "channel": "beta"
        },
        "download": {
            "url": "https://archive.mozilla.org/pub/firefox/releases/52.0b6/linux-x86_64/en-US/"
            "firefox-52.0b6.tar.bz2"
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
            "locale": "fr",
            "channel": "release"
        },
        "download": {
            "url": "https://archive.mozilla.org/pub/firefox/candidates/50.0-candidates/build1/"
            "linux-x86_64/fr/firefox-50.0.tar.bz2"
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
            "locale": "fr",
            "channel": "release"
        },
        "download": {
            "url": "https://archive.mozilla.org/pub/firefox/releases/52.0/linux-x86_64/fr/"
            "firefox-52.0.tar.bz2"
        }
    },

    # Firefox ESR
    {
        "id": "firefox_52-0esr_linux-x86_64_en-us",
        "source": {
            "product": "firefox",
        },
        "target": {
            "version": "52.0esr",
            "platform": "linux-x86_64",
            "locale": "en-US",
            "channel": "esr"
        },
        "download": {
            "url": "https://archive.mozilla.org/pub/firefox/releases/52.0esr/linux-x86_64/en-US/"
            "firefox-52.0esr.tar.bz2",
        }
    },

    # Thunderbird Release
    {
        "id": "thunderbird_17-0-8esr_linux-x86_64_gd",
        "source": {
            "product": "thunderbird",
        },
        "target": {
            "version": "17.0.8esr",
            "platform": "linux-x86_64",
            "locale": "gd",
            "channel": "esr"
        },
        "download": {
            "url": "https://archive.mozilla.org/pub/thunderbird/releases/17.0.8esr/linux-x86_64/"
            "gd/thunderbird-17.0.8esr.tar.bz2",
        }
    },

    # Fennec
    {
        "id": "fennec_39-0b5_android-api-9_sl",
        "source": {
            "product": "fennec",
        },
        "target": {
            "version": "39.0b5",
            "platform": "android-api-9",
            "locale": "sl",
            "channel": "beta"
        },
        "download": {
            "url": "https://archive.mozilla.org/pub/mobile/releases/39.0b5/android-api-9/sl/"
            "fennec-39.0b5.sl.android-arm.apk",
        }
    },

    # Localized Fennec
    {
        "id": "fennec_42-0b2_android-api-9_fr",
        "source": {
            "product": "fennec",
        },
        "target": {
            "version": "42.0b2",
            "platform": "android-api-9",
            "locale": "fr",
            "channel": "beta"
        },
        "download": {
            "url": "https://archive.mozilla.org/pub/mobile/releases/42.0b2/android-api-9/fr/"
            "fennec-42.0b2.fr.android-arm.apk",
        }
    },
]


# Build record_id from record
@pytest.mark.parametrize("record", RECORDS)
def test_build_record_id(record):
    record_id = build_record_id(record)
    assert record_id == record["id"]


NIGHTLY_FILENAMES = [
    ("firefox-55.0a1.en-US.linux-x86_64.tar.bz2", "55.0a1", "en-US", "linux-x86_64")
]


@pytest.mark.parametrize("filename,version,locale,platform", NIGHTLY_FILENAMES)
def test_parse_nightly_filename(filename, version, locale, platform):
    results = parse_nightly_filename(filename)
    assert results == (version, locale, platform)


NIGHTLY_WRONG_FILENAMES = [
    "firefox-tests.bz2",
    "firefox-crashreporter.gz",
    "foobar.bz2",
]


@pytest.mark.parametrize("filename", NIGHTLY_WRONG_FILENAMES)
def test_parse_nightly_filename_raise_a_value_error(filename):
    with pytest.raises(ValueError):
        parse_nightly_filename(filename)


RELEASE_METADATA_FILENAMES = [
    ("firefox", "52.0b7", "firefox-52.0b7.json"),
    ("fennec", "51.0b2", "fennec-51.0b2.en-US.android-i386.json"),
]


@pytest.mark.parametrize("product,version,filename", RELEASE_METADATA_FILENAMES)
def test_is_release_metadata(product, version, filename):
    assert is_release_metadata(product, version, filename)


WRONG_RELEASE_METADATA_FILENAMES = [
    ("firefox", "52.0b7", "thunderbird-52.0b7.json"),
    ("fennec", "51.0b2", "fennec-52.0.en-US.android-i386.json"),
    ("fennec", "52.0", "fennec-52.0.en-US.android-i386.asc"),
]


@pytest.mark.parametrize("product,version,filename", WRONG_RELEASE_METADATA_FILENAMES)
def test_wrong_release_metadata(product, version, filename):
    assert not is_release_metadata(product, version, filename)


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
]


@pytest.mark.parametrize("product,filename", RELEASE_FILENAMES)
def test_is_release_filename(product, filename):
    assert is_release_filename(product, filename)


WRONG_RELEASE_FILENAMES = [
    ("firefox", "firefox-1.5.0.5.tar.gz.asc"),
    ("firefox", "firefox-52.0.win32.sdk.zip"),
]


@pytest.mark.parametrize("product,filename", WRONG_RELEASE_FILENAMES)
def test_wrong_release_filename(product, filename):
    assert not is_release_filename(product, filename)
