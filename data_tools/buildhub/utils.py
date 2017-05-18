from os.path import basename


def build_record_id(record):
    version = record["target"]["version"]
    if record["target"]["channel"] == 'nightly':
        url_parts = record["download"]["url"].split('/')
        date_parts = url_parts[8].split('-')
        date = '-'.join(date_parts[:6])
        version = '{}_{}'.format(date, version)
    return '{source[product]}_{version}_{target[platform]}_{target[locale]}'.format(
        **record, version=version).replace('.', '-').lower()
