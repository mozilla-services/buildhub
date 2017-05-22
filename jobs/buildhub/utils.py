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
