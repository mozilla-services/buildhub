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


def localize_nightly_url(nightly_url):
    nightly_url = nightly_url.replace('-l10n', '')
    parts = nightly_url.split('.')
    locale = 'en-US'
    index = -3
    if 'tar' in nightly_url:
        index = -4
    if 'mobile' in nightly_url:
        locale = 'multi'
    parts[index] = locale
    return '.'.join(parts)


def guess_channel(url, version):
    channel = 'release'
    if 'nightly' in url:
        if 'aurora' in url:
            channel = 'aurora'
        else:
            channel = 'nightly'
    else:
        if 'b' in version:
            channel = 'beta'

    # Fennec can have different app store ids.
    if 'old-id' in url:
        channel += "-old-id"

    return channel


def build_record_id(record):
    version = record["target"]["version"]

    if 'nightly' in record["target"]["channel"]:
        url_parts = record["download"]["url"].split('/')
        date_parts = url_parts[8].split('-')
        date = '-'.join(date_parts[:6])
        version = '{}_{}'.format(date, version)

    channel = record["target"]["channel"]
    channel = channel + "_" if channel != "release" else ""
    values = dict(product=record["source"]["product"],
                  channel=channel,
                  version=version,
                  platform=record["target"]["platform"],
                  locale=record["target"]["locale"])
    id_ = '{product}_{channel}{version}_{platform}_{locale}'.format(**values)
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
    - Thunderbird 10.0.12esr.dmg
    """
    match_filename = filename.replace(' ', '-').lower()
    re_filename = re.compile("{}-(.+)({})$".format(product, FILE_EXTENSIONS))
    re_exclude = re.compile(".+(sdk|tests|crashreporter)")
    return re_filename.match(match_filename) and not re_exclude.match(match_filename)


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


def chunked(iterable, size):
    """Split the `iterable` into chunks of `size` elements."""
    nb_chunks = (len(iterable) // size) + 1
    for i in range(nb_chunks):
        yield iterable[(i * size):((i + 1) * size)]
