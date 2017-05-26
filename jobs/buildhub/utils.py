import os.path
import re

FILE_EXTENSIONS = "zip|tar.gz|tar.bz2|dmg|apk"
KNOWN_MIMETYPES = {
    'apk': 'application/vnd.android.package-archive',
    'bz2': 'application/x-bzip2',
    'zip': 'application/zip',
    'dmg': 'application/x-apple-diskimage',
    'gz': 'application/x-gzip',
    }


def guess_channel(url, version):
    channel = 'release'
    if 'nightly' in url:
        if 'aurora' in url:
            channel = 'aurora'
        else:
            channel = 'nightly'
    else:
        if 'esr' in url:
            channel = 'esr'
        elif 'b' in version:
            channel = 'beta'
    return channel


def build_record_id(record):
    version = record["target"]["version"]

    if record["target"]["channel"] == 'nightly':
        url_parts = record["download"]["url"].split('/')
        date_parts = url_parts[8].split('-')
        date = '-'.join(date_parts[:6])
        version = '{}_{}'.format(date, version)

    id_ = '{product}_{version}_{platform}_{locale}'.format(product=record["source"]["product"],
                                                           version=version,
                                                           platform=record["target"]["platform"],
                                                           locale=record["target"]["locale"])
    return id_.replace('.', '-').lower()


def parse_nightly_filename(filename):
    """
    Examples of nightly filenames:

    - firefox-55.0a1.ach.win64.zip
    - firefox-55.0a1.bn-IN.mac.dmg

    And things we'll want to ignore:

    - firefox-55.0a1.en-US.linux-i686.talos.tests.zip
    - firefox-55.0a1.en-US.mac.crashreporter-symbols.zip
    """
    re_nightly = re.compile(r"\w+-(\d+.+)\."  # product-version
                            r"([a-z]+(\-[A-Z]+)?)"  # locale
                            r"\.(.+)"  # platform
                            r"\.({})$".format(FILE_EXTENSIONS))
    match = re_nightly.search(filename)
    if not match or "tests" in filename or "crashreporter" in filename:
        raise ValueError()
    version = match.group(1)
    locale = match.group(2)
    platform = match.group(4)
    return version, locale, platform


def is_release_filename(product, filename):
    """
    Examples of release filenames:

    - firefox-53.0.tar.bz2

    And things we'll want to ignore:

    - firefox-1.5.0.5.tar.gz.asc
    - firefox-52.0.win32.sdk.zip
    """
    re_filename = re.compile("{}-(.+)({})$".format(product, FILE_EXTENSIONS))
    return re_filename.match(filename) and 'sdk' not in filename


def is_release_metadata(product, version, filename):
    """
    Examples of release metadata filenames:

    - firefox-52.0b7.json
    - fennec-51.0b2.en-US.android-i386.json
    """
    re_metadata = re.compile("{}-{}(.*).json".format(product, version))
    return re_metadata.match(filename)


def guess_mimetype(url):
    """Try to guess what kind of mimetype a given archive URL would be."""
    _, extension = os.path.splitext(url)
    return KNOWN_MIMETYPES.get(extension.strip('.'), None)
