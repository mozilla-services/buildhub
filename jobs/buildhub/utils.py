import datetime
import os.path
import re


PRODUCTS = ("firefox", "thunderbird", "mobile")
ARCHIVE_URL = "https://archive.mozilla.org/"
DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
FILE_EXTENSIONS = "zip|tar.gz|tar.bz2|dmg|apk|exe"
KNOWN_MIMETYPES = {
    'apk': 'application/vnd.android.package-archive',
    'bz2': 'application/x-bzip2',
    'zip': 'application/zip',
    'dmg': 'application/x-apple-diskimage',
    'gz': 'application/x-gzip',
    'exe': 'application/msdos-windows',
    }


def archive_url(product, version=None, platform=None, locale=None, nightly=None, candidate=None):
    """Returns the related URL on archive.mozilla.org
    """
    product = product if product != "fennec" else "mobile"

    if platform is not None:
        platform = platform.replace('eme', 'EME')

    url = ARCHIVE_URL + 'pub/' + product
    if nightly:
        url += "/nightly/" + nightly + "/"
    elif candidate:
        url += "/candidates"
        if version:
            url += "/{}-candidates".format(version)
        url += candidate
        if platform:
            url += platform + "/"
        if locale:
            url += locale + "/"
    else:
        url += "/releases/"
        if version:
            url += version + "/"
        if platform:
            url += platform + "/"
        if locale:
            url += locale + "/"
    return url


def localize_nightly_url(nightly_url):
    nightly_url = nightly_url.replace('-l10n', '')
    nightly_url = nightly_url.replace('.installer', '')
    parts = nightly_url.split('.')
    locale = 'en-US'
    index = -3
    if 'tar' in nightly_url:
        index = -4
    if 'mobile' in nightly_url:
        locale = 'multi'
    parts[index] = locale
    return '.'.join(parts)


def localize_release_candidate_url(rc_url):
    tokens = rc_url.split('/')
    tokens[-2] = "en-US"
    us_url = "/".join(tokens)
    return us_url.replace("-EME-free", "")


def guess_channel(url, version):
    channel = 'release'
    if 'nightly' in url:
        if 'aurora' in url:
            channel = 'aurora'
        else:
            channel = 'nightly'
    elif 'b' in version:
        if 'devedition' in url:
            channel = 'aurora'
        else:
            channel = 'beta'
    elif version.endswith('esr'):
        channel = 'esr'

    # Fennec can have different app store ids.
    if 'old-id' in url:
        channel += "-old-id"

    return channel


def normalized_platform(platform):
    for p in ("linux", "win", "mac", "android", "maemo"):
        if p in platform:
            return p
    raise ValueError("Unknown plaform {}".format(platform))


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


def is_build_url(product, url):
    """
    - firefox/nightly/experimental/sparc-633408-fix/
          firefox-4.0b11.en-US.solaris-10-fcs-sparc-fix-633408.tar.bz2
    - firefox/nightly/2017/06/2017-06-21-15-02-57-date-l10n/
          firefox-56.0a1.zh-CN.linux-x86_64.tar.bz2
    - firefox/releases/0.10.1/firefox-1.0PR-i686-linux-gtk2%2Bxft-installer.tar.gz
    - firefox/nightly/contrib/latest-trunk/firefox-win32-svg-GDI.zip
    - firefox/releases/0.9rc/firefox-0.9rc-i686-linux-gtk2%2Bxft.tar.gz
    - firefox/releases/0.8/Firefox-0.8.zip
    - firefox/nightly/2017/06/2017-06-21-10-23-01-mozilla-central/\
          firefox-56.0a1.te.en-US.installer.json
    - firefox/nightly/2017/06/2017-06-20-11-02-48-oak/firefox-55.0a1.en-US.linux-i686.tar.bz2
    - firefox/nightly/2016/03/2016-03-14-00-15-09-mozilla-esr45/firefox-45.0esrpre.en-US.win64.zip
    - firefox/nightly/2014/12/2014-12-10-mozilla-central-debug/ \
          firefox-37.0a1.en-US.debug-linux-x86_64-asan.tar.bz2
    """
    if 'nightly' in url and 'mozilla-central' not in url:
        return False

    re_exclude = re.compile(".+(tinderbox|try-builds|partner-repacks|latest|contrib|/0\.|"
                            "experimental|namoroka|debug|sha1-installers|candidates/archived|"
                            "stylo-bindings|/1.0rc/|dominspector|/test/|testing)")
    if re_exclude.match(url):
        return False
    """
    Examples of build filenames:

    - firefox-53.0.tar.bz2

    And things we'll want to ignore:

    - firefox-1.5.0.5.tar.gz.asc
    - firefox-52.0.win32.sdk.zip
    - Thunderbird 10.0.12esr.dmg
    - Firefox Setup 17.0b3.exe
    """
    if product == "devedition":
        product = "firefox"
    filename = os.path.basename(url)
    match_filename = filename.replace(' ', '-').lower()
    re_filename = re.compile("{}-(.+)({})$".format(product, FILE_EXTENSIONS))
    re_exclude = re.compile(".+(sdk|tests|crashreporter|stub|gtk2.+xft|source|asan)")
    return re_filename.match(match_filename) and not re_exclude.match(match_filename)


def is_release_build_metadata(product, version, filename):
    """
    Examples of release metadata filenames:

    - firefox-52.0b7.json
    - fennec-51.0b2.en-US.android-i386.json
    """
    if product == "devedition":
        product = "firefox"
    re_metadata = re.compile("{}-{}(.*).json".format(product, version))
    return bool(re_metadata.match(filename))


def guess_mimetype(url):
    """Try to guess what kind of mimetype a given archive URL would be."""
    _, extension = os.path.splitext(url)
    return KNOWN_MIMETYPES.get(extension.strip('.'), None)


def chunked(iterable, size):
    """Split the `iterable` into chunks of `size` elements."""
    nb_chunks = (len(iterable) // size) + 1
    for i in range(nb_chunks):
        yield iterable[(i * size):((i + 1) * size)]


def record_from_url(url):
    # Extract infos from URL and return a record.

    # Get rid of spaces and capitalized names (eg. 'Firefox Setup.exe')
    normalized_url = url.replace(' ', '-').lower()
    url_parts = normalized_url.split('/')
    filename = os.path.basename(normalized_url)
    filename_parts = filename.split('.')

    product = filename_parts[0].replace('-setup', '').split('-')[0]

    # Nightly URL
    # https://archive.mozilla.org/pub/firefox/nightly/2017/05/
    # 2017-05-15-10-02-38-mozilla-central/firefox-55.0a1.en-US.linux-x86_64.tar.bz2
    if 'nightly' in url:
        major_version = filename_parts[0].split('-')[1]
        version = '{}.{}'.format(major_version, filename_parts[1])
        locale = filename_parts[2]
        platform = filename_parts[3]
        if 'android-api' in url_parts[8]:
            platform = '-'.join(url_parts[8].split('-')[8:11])

    # Candidates URL
    # https://archive.mozilla.org/pub/firefox/candidates/50.0-candidates/build1/
    # linux-x86_64/fr/firefox-50.0.tar.bz2
    elif 'candidates' in url:
        version = url_parts[6].strip('-candidates')
        candidate_number = url_parts[7].strip('build')
        version = '{}rc{}'.format(version, candidate_number)
        platform = url_parts[8]
        locale = url_parts[9]

    # Old release url
    elif len(url_parts) < 9:
        major_version = filename_parts[0].split('-')[1]
        version = '{}.{}'.format(major_version, filename_parts[1])
        locale = filename_parts[2]
        platform = filename_parts[3]

    # Beta, Release or ESR URL
    # https://archive.mozilla.org/pub/firefox/releases/52.0b6/linux-x86_64/en-US/
    # firefox-52.0b6.tar.bz2
    else:
        version = url_parts[6]
        locale = url_parts[8]
        platform = url_parts[7]

    if platform == 'mac':
        platform = 'macosx'

    channel = guess_channel(url, version)

    if '-' in locale:
        locale_parts = locale.split('-')
        locale_parts[1] = locale_parts[1].upper()
        locale = '-'.join(locale_parts)  # fr-FR, ja-JP-mac

    record = {
        "source": {
            "product": product,
        },
        "target": {
            "platform": platform,
            "os": normalized_platform(platform),
            "locale": locale,
            "version": version,
            "channel": channel,
        },
        "download": {
            "url": url,
            "mimetype": guess_mimetype(url),
        }
    }

    record["id"] = build_record_id(record)
    return record


def check_record(record):
    """Quick sanity check on record."""
    channel = record["target"]["channel"]
    if not re.match(r"^(release|aurora|beta|esr|nightly)(-old-id)?$", channel):
        raise ValueError("Suspicious channel '{}': {}".format(channel, record))

    platform = record["target"]["platform"]
    if not re.match(r"^(win|mac|linux|android).{0,4}", platform):
        raise ValueError("Suspicious platform '{}': {}".format(platform, record))

    locale = record["target"]["locale"]
    if not re.match(r"^([A-Za-z]{2,3}\-?){1,3}$", locale):
        raise ValueError("Suspicious locale '{}': {}".format(locale, record))

    version = record["target"]["version"]
    if not re.match(r"^(\d+|\.|\-|esr|rc|b|a|pre|funnelcake|real|plugin)+$", version):
        raise ValueError("Suspicious version '{}': {}".format(version, record))


def merge_metadata(record, metadata):
    if metadata is None:
        return record

    # XXX: deepcopy instead of mutation

    # Example of metadata:
    #  https://archive.mozilla.org/pub/thunderbird/candidates \
    #  /50.0b1-candidates/build2/linux-i686/en-US/thunderbird-50.0b1.json
    # If the channel is present in the metadata it is more reliable than our guess.
    channel = metadata.get("moz_update_channel", record['target']['channel'])
    record['target']['channel'] = channel

    repository = metadata["moz_source_repo"].replace("MOZ_SOURCE_REPO=", "")
    record['source']['revision'] = metadata["moz_source_stamp"]
    record['source']['repository'] = repository
    record['source']['tree'] = repository.split("hg.mozilla.org/", 1)[-1]

    buildid = metadata["buildid"]
    builddate = datetime.datetime.strptime(buildid[:14], "%Y%m%d%H%M%S")
    builddate = builddate.strftime(DATETIME_FORMAT)
    record['build'] = {
        "id": buildid,
        "date": builddate,
    }
    # For release builds, we have the build number:
    if "buildnumber" in metadata:
        record['build']['number'] = metadata["buildnumber"]

    return record
