from buildhub.utils import build_record_id


def test_build_id_from_record_for_nightly():
    record_id = build_record_id("https://archive.mozilla.org/pub/"
                                "firefox/nightly/2017/05/2017-05-15-10-02-38-mozilla-central/"
                                "firefox-55.0a1.en-US.linux-x86_64.tar.bz2")
    assert record_id == "firefox_2017-05-15-10-02-38_55-0a1_linux-x86_64_en-US"


def test_build_id_from_record_for_firefox_beta():
    record_id = build_record_id("https://archive.mozilla.org/pub/"
                                "firefox/releases/52.0b6/linux-x86_64/en-US/"
                                "firefox-52.0b6.tar.bz2")
    assert record_id == "firefox_52-0b6_linux-x86_64_en-US"


def test_build_id_from_record_for_thunderbird():
    record_id = build_record_id("https://archive.mozilla.org/pub/"
                                "thunderbird/releases/17.0.8esr/linux-x86_64/gd/"
                                "thunderbird-17.0.8esr.tar.bz2")
    assert record_id == "thunderbird_17-0-8esr_linux-x86_64_gd"


def test_build_id_for_firefox_esr():
    record_id = build_record_id("https://archive.mozilla.org/pub/"
                                "firefox/releases/52.0esr/linux-x86_64/"
                                "en-US/firefox-52.0esr.tar.bz2")
    assert record_id == "firefox_52-0esr_linux-x86_64_en-US"


def test_build_id_from_record_for_fennec():
    record_id = build_record_id("https://archive.mozilla.org/pub/"
                                "mobile/releases/39.0b5/android-api-9/sl/"
                                "fennec-39.0b5.sl.android-arm.apk")
    assert record_id == "fennec_39-0b5_android-api-9_sl"


def test_build_id_from_localized_fennec():
    record_id = build_record_id("https://archive.mozilla.org/pub/"
                                "mobile/releases/42.0b2/android-api-9/fr/"
                                "fennec-42.0b2.fr.android-arm.apk")
    assert record_id == "fennec_42-0b2_android-api-9_fr"
