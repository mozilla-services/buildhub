from os.path import basename


def build_record_id(url):
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
    else:
        version = url_parts[6]
        locale = url_parts[8]
        arch = url_parts[7]

    return '{}_{}_{}_{}'.format(product_name, version, arch, locale).replace('.', '-').lower()
