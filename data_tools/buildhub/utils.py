from os.path import basename


def build_record_from_url(url):
    record = {}
    parts = basename(url).split('.')
    url_parts = url.split('/')

    product_name, major_version = parts[0].split('-')
    channel = 'release'

    if 'nightly' in url:
        version = '{}.{}'.format(major_version, parts[1])
        locale = parts[2]
        platform = parts[3]
        channel = 'nightly'
    elif 'candidates' in url:
        candidate_number = url_parts[7].strip('build')
        version = '{}.{}rc{}'.format(major_version, parts[1], candidate_number)
        locale = url_parts[9]
        platform = url_parts[8]
    else:
        version = url_parts[6]
        locale = url_parts[8]
        platform = url_parts[7]
        if 'esr' in version:
            channel = 'esr'
        elif 'b' in version:
            channel = 'beta'
        elif 'a' in version:
            channel = 'aurora'

    record['target'] = {
        'product': product_name,
        'version': version,
        'platform': platform,
        'locale': locale,
        'channel': channel,
    }
    record["download"] = {"url": url}
    record_id = build_record_id(record)
    record['id'] = record_id
    return record


def build_record_id(record):
    version = record["target"]["version"]
    if record["target"]["channel"] == 'nightly':
        if not 'download' in record:
            import pdb; pdb.set_trace()
        url_parts = record["download"]["url"].split('/')
        date_parts = url_parts[8].split('-')
        date = '-'.join(date_parts[:6])
        version = '{}_{}'.format(date, version)
    return '{target[product]}_{version}_{target[platform]}_{target[locale]}'.format(
        target=record['target'], version=version).replace('.', '-').lower()


def build_record_id_from_url(url):
    # Generate an ID that looks like that: firefox_53.0b9_linux-i686_en-US
    parts = basename(url).split('.')
    url_parts = url.split('/')

    product_name, major_version = parts[0].split('-')

    if 'nightly' in url:
        build_date = '-'.join(url_parts[8].split('-')[:6])
        version_number = '{}.{}'.format(major_version, parts[1])
        version = '{}_{}'.format(build_date, version_number)
        locale = parts[2]
        arch = parts[3]
    elif 'candidates' in url:
        candidate_number = url_parts[7].strip('build')
        version = '{}.{}rc{}'.format(major_version, parts[1], candidate_number)
        locale = url_parts[9]
        arch = url_parts[8]
    else:
        version = url_parts[6]
        locale = url_parts[8]
        arch = url_parts[7]

    return '{}_{}_{}_{}'.format(product_name, version, arch, locale).replace('.', '-').lower()
