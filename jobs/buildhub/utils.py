# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, you can obtain one at http://mozilla.org/MPL/2.0/.

import asyncio
import datetime
import os.path
import re

from decouple import config


ALL_PRODUCTS = ('firefox', 'thunderbird', 'mobile', 'devedition')
ARCHIVE_URL = config('ARCHIVE_URL', 'https://archive.mozilla.org/')
DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%SZ'
FILE_EXTENSIONS = ('zip', 'tar.gz', 'tar.bz2', 'dmg', 'apk', 'exe')
KNOWN_MIMETYPES = {
    'apk': 'application/vnd.android.package-archive',
    'bz2': 'application/x-bzip2',
    'zip': 'application/zip',
    'dmg': 'application/x-apple-diskimage',
    'gz': 'application/x-gzip',
    'exe': 'application/msdos-windows',
    }


def key_to_archive_url(key):
    # If the key (e.g.
    # pub/firefox/releases/60.0.1/win32/en-US/Firefox+Setup+60.0.1.exe
    # ) uses escaped spaced, we need to remove them. Otherwise it
    # won't match on the regular expressions for is_build_url() etc.
    return ARCHIVE_URL + key.replace('+', ' ')


def archive_url(
    product,
    version=None,
    platform=None,
    locale=None,
    nightly=None,
    candidate=None
):
    """Returns the related URL on archive.mozilla.org
    """
    if product == 'fennec':
        product = 'mobile'

    if platform is not None:
        platform = platform.replace('eme', 'EME')

        if platform.startswith('macosx'):
            platform = platform.replace('macosx', 'mac')

    url = ARCHIVE_URL + 'pub/' + product
    if nightly:
        url += '/nightly/' + nightly + '/'
    elif candidate:
        url += '/candidates'
        if version:
            url += '/{}-candidates'.format(version)
        url += candidate
        if platform:
            url += platform + '/'
        if locale:
            url += locale + '/'
    else:
        url += '/releases/'
        if version:
            url += version + '/'
        if platform:
            url += platform + '/'
        if locale:
            url += locale + '/'
    return url


def localize_nightly_url(nightly_url):
    nightly_url = nightly_url.replace('-l10n', '')
    nightly_url = nightly_url.replace('.installer', '')
    parts = nightly_url.split('.')
    locale = 'en-US'
    index = -3
    if 'tar' in nightly_url:
        index = -4
    if ('/mobile/' in nightly_url
       and '/en-US/' not in nightly_url
       and 'macosx' not in nightly_url):
        locale = 'multi'
    parts[index] = locale
    return '.'.join(parts)


def localize_release_candidate_url(rc_url):
    tokens = rc_url.split('/')
    lang = tokens[-2]
    us_url = rc_url.replace('.%s.' % lang, '.en-US.')\
                   .replace('/%s/' % lang, '/en-US/')\
                   .replace('-EME-free', '')
    return us_url


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
        channel += '-old-id'

    return channel


def normalized_platform(platform):
    if 'eabi' in platform:
        return 'android'
    for p in ('linux', 'win', 'mac', 'android', 'maemo'):
        if p in platform:
            return p
    raise ValueError('Unknown plaform {}'.format(platform))


def build_record_id(record):
    version = record['target']['version']

    if 'nightly' in record['target']['channel']:
        url_parts = record['download']['url'].split('/')
        date_parts = url_parts[8].split('-')
        date = '-'.join(date_parts[:6])
        version = '{}_{}'.format(date, version)

    channel = record['target']['channel']
    channel = channel + '_' if channel != 'release' else ''
    values = dict(product=record['source']['product'],
                  channel=channel,
                  version=version,
                  platform=record['target']['platform'],
                  locale=record['target']['locale'])
    id_ = '{product}_{channel}{version}_{platform}_{locale}'.format(**values)
    return id_.replace('.', '-').lower()


# Compile these regexes once per module to speed up their use inside
# the is_build_url() function.

_build_url_exclude_names_regex = re.compile(
    '.+(tinderbox|try-builds|partner-repacks|latest|contrib|/0\.|'
    'experimental|namoroka|debug|sha1-installers|candidates/archived|'
    'stylo-bindings|/1.0rc/|/releases/win../|dominspector|/test/|testing|'
    '%28.+%29|\sInstaller\.(\w{2,3}\-?\w{0,3})\.exe)'
)

_build_url_exclude_suffixes_regex = re.compile(
    '.+(sdk|tests|crashreporter|stub|gtk2.+xft|source|asan)'
)


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
    - mobile/nightly/2017/08/2017-08-09-10-03-39-mozilla-central-android-api-15-l10n/
          fennec-57.0a1.hi-IN.android-arm.apk
    - firefox/nightly/2017/08/2017-08-25-10-01-26-mozilla-central-l10n/Firefox Installer.fr.exe
    """  # noqa
    if (
        'nightly' in url and
        'mozilla-central' not in url and
        'comm-central' not in url
    ):
        return False

    if _build_url_exclude_names_regex.match(url):
        return False

    extensions = FILE_EXTENSIONS
    # Only .exe for Windows.
    if 'win' in url:
        extensions = [x for x in extensions if x != 'zip']

    if product == 'devedition':
        product = 'firefox'
    if product == 'mobile':
        product = 'fennec'
    filename = os.path.basename(url)
    match_filename = filename.replace(' ', '-').lower()
    if _build_url_exclude_suffixes_regex.match(match_filename):
        return False

    re_filename = re.compile(
        '{}-(.+)({})$'.format(product, '|'.join(extensions))
    )
    return re_filename.match(match_filename)


def is_release_build_metadata(product, version, filename):
    """
    Examples of release metadata filenames:

    - firefox-52.0b7.json
    - fennec-51.0b2.en-US.android-i386.json
    """
    if product == 'devedition':
        product = 'firefox'
    re_metadata = re.compile('{}-{}(.*).json'.format(product, version))
    return bool(re_metadata.match(filename))


def is_nightly_build_metadata(product, url):
    if 'nightly' not in url:
        return False
    if 'nightly' in url and 'mozilla-central' not in url:
        # pub/mobile/nightly/2017/08/2017-08-01-15-03-46-date-android-api-15/...
        return False
    if product == 'mobile':
        product = 'fennec'
    # Exlude alias folder, and other metadata.
    re_exclude = re.compile('.+(latest-mozilla-central|test_packages|mozinfo)')
    if re_exclude.match(url):
        return False
    # Note: devedition has no nightly.
    re_metadata = re.compile('.+/{}-(.*)\.(.*)\.(.*)\.json$'.format(product))
    return bool(re_metadata.match(url))


def is_rc_build_metadata(product, url):
    if product == 'mobile':
        product = 'fennec'
    if product == 'devedition':
        product = 'firefox'
    m = re.search('/candidates/(.+)-candidates', url)
    if not m:
        return False
    version = m.group(1)
    if product == 'fennec':  # fennec-56.0b1.en-US.android-arm.json
        re_metadata = re.compile(
            '.+/{}-{}\.([^\.]+)\.([^\.]+)\.json$'.format(product, version)
        )
    else:  # firefox-56.0b1.json
        re_metadata = re.compile('.+/{}-{}\.json$'.format(product, version))
    return bool(re_metadata.match(url))


def guess_mimetype(url):
    """Try to guess what kind of mimetype a given archive URL would be."""
    _, extension = os.path.splitext(url)
    return KNOWN_MIMETYPES.get(extension.strip('.'), None)


def chunked(iterable, size):
    """Split the `iterable` into chunks of `size` elements."""
    nb_chunks = (len(iterable) // size) + 1
    for i in range(nb_chunks):
        yield iterable[(i * size):((i + 1) * size)]


async def split_lines(stream):
    """Split the chunks of bytes on new lines.
    """
    leftover = ''
    async for chunk in stream:
        chunk_str = chunk.decode('utf-8')
        chunk_str = leftover + chunk_str
        chunk_str = chunk_str.lstrip('\n')
        lines = chunk_str.split('\n')
        # Everything after \n belongs to the next line.
        leftover = lines.pop()
        if lines:
            yield lines


async def stream_as_generator(loop, stream):
    reader = asyncio.StreamReader(loop=loop)
    reader_protocol = asyncio.StreamReaderProtocol(reader)
    await loop.connect_read_pipe(lambda: reader_protocol, stream)

    while 'stream receives input':
        line = await reader.readline()
        if not line:  # EOF.
            break
        yield line


def record_from_url(url):
    # Extract infos from URL and return a record.

    # Get rid of spaces and capitalized names (eg. 'Firefox Setup.exe')
    normalized_url = url.replace(' ', '-').lower()
    url_parts = normalized_url.split('/')
    filename = os.path.basename(normalized_url)
    filename_parts = filename.split('.')

    product = url_parts[4]
    if product == 'mobile':
        product = 'fennec'

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
        if 'funnelcake' in platform:
            # 49.0.1-candidates/build3/funnelcake90/win32/en-US/\
            # Firefox Setup 49.0.1.exe
            version = '{}-{}'.format(version, platform)
            platform = url_parts[9]
            locale = url_parts[10]

    # Old release url
    elif len(url_parts) < 9:
        major_version = filename_parts[0].split('-')[1]
        version = '{}.{}'.format(major_version, filename_parts[1])
        locale = filename_parts[2]
        platform = filename_parts[3]

    # Some funnelcakes
    elif 'funnelcake' in url and len(url_parts) == 11:
        version = url_parts[6]
        locale = url_parts[9]
        platform = url_parts[8]

    # Beta, Release or ESR URL
    # https://archive.mozilla.org/pub/firefox/releases/52.0b6/linux-x86_64/en-US/
    # firefox-52.0b6.tar.bz2
    else:
        version = url_parts[6]
        locale = url_parts[8]
        platform = url_parts[7]

    if platform.startswith('mac'):
        platform = platform.replace('mac', 'macosx')

    channel = guess_channel(url, version)

    if '-' in locale:
        locale_parts = locale.split('-')
        locale_parts[1] = locale_parts[1].upper()
        locale = '-'.join(locale_parts)  # fr-FR, ja-JP-mac

    record = {
        'source': {
            'product': product,
        },
        'target': {
            'platform': platform,
            'os': normalized_platform(platform),
            'locale': locale,
            'version': version,
            'channel': channel,
        },
        'download': {
            'url': url,
            'mimetype': guess_mimetype(url),
        }
    }

    record['id'] = build_record_id(record)
    return record


def check_record(record):
    """Quick sanity check on record."""
    if 'id' not in record.get('build', {}):
        raise ValueError("Missing build id in {}".format(record))
    channel = record['target']['channel']
    if not re.match(r"^(release|aurora|beta|esr|nightly)(-old-id)?$", channel):
        raise ValueError("Suspicious channel '{}': {}".format(channel, record))

    platform = record['target']['platform']
    if not re.match(r"^(win|mac|linux|android|maemo|eabi).{0,4}", platform):
        raise ValueError("Suspicious platform '{platform}': {record}")

    locale = record['target']['locale']
    if not re.match(r"^([A-Za-z]{2,3}\-?){1,3}$", locale):
        raise ValueError(f"Suspicious locale '{locale}': {record}")

    version = record['target']['version']
    if not re.match(
        r"^(\d+|\.|\-|esr|rc|b|a|pre|funnelcake|real|plugin)+$",
        version
    ):
        raise ValueError(f"Suspicious version '{version}': {record}")


def merge_metadata(record, metadata):
    if metadata is None:
        return record

    # XXX: deepcopy instead of mutation

    # Example of metadata:
    #  https://archive.mozilla.org/pub/thunderbird/candidates \
    #  /50.0b1-candidates/build2/linux-i686/en-US/thunderbird-50.0b1.json
    # If the channel is present in the metadata it is more reliable
    # than our guess.
    channel = metadata.get('moz_update_channel', record['target']['channel'])
    record['target']['channel'] = channel

    repository = metadata['moz_source_repo'].replace('MOZ_SOURCE_REPO=', '')
    record['source']['revision'] = metadata['moz_source_stamp']
    record['source']['repository'] = repository
    record['source']['tree'] = repository.split('hg.mozilla.org/', 1)[-1]

    buildid = metadata['buildid']
    builddate = datetime.datetime.strptime(buildid[:14], '%Y%m%d%H%M%S')
    builddate = builddate.strftime(DATETIME_FORMAT)
    record['build'] = {
        'id': buildid,
        'date': builddate,
    }
    # Additional compilation stuff.
    for field in ('as', 'cc', 'cxx', 'ld', 'host_alias', 'target_alias'):
        if field in metadata:
            record['build'][field.replace('_alias', '')] = metadata[field]

    # For release builds, we have the build number:
    if 'buildnumber' in metadata:
        record['build']['number'] = metadata['buildnumber']

    return record
