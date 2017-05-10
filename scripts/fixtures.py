import datetime
import json

import requests
import kinto_http


def buildid2iso(buildid):
    return datetime.datetime.strptime(buildid, "%Y%m%d%H%M%S").isoformat()


def main():
    client = kinto_http.Client(server_url="https://kinto-ota.dev.mozaws.net/v1",
                               bucket="build-hub",
                               collection="fixtures",
                               auth=("user", "pass"))
    records = client.get_records(bucket="systemaddons", collection="versions")

    client.create_collection(if_not_exists=True)
    for record in records:
        buildid = record["release"]["buildId"]

        url = record["release"]["url"]
        resp = requests.head(url)
        size = int(resp.headers.get("Content-Length", 0))
        mimetype = resp.headers.get("Content-Type")

        addons_by_ids = {}
        for addon in record["builtins"]:
            addons_by_ids[addon["id"]] = {"id": addon["id"], "builtin": addon["version"]}
        for addon in record["updates"]:
            addons_by_ids.setdefault(addon["id"], {}).update({"id": addon["id"], "updated": addon["version"]})
        systemaddons = list(addons_by_ids.values())

        tree = {
            "beta": "mozilla-beta",
            "aurora": "mozilla-aurora",
            "release": "mozilla-release",
            "nightly": "mozilla-central"
        }[record["release"]["channel"]]

        fixture = {
            "build": {
                "id": buildid,
                "date": buildid2iso(buildid),
                "type": "opt"
            },
            "source": {
                "revision": record["id"],  # fake rev!
                "tree": tree,
                "product": "firefox",
            },
            "target": {
                "platform": record["release"]["target"],
                "locale": record["release"]["lang"],
                "version": record["release"]["version"],
                "channel": record["release"]["channel"],
            },
            "download": {
                "url": url,
                "mimetype": mimetype,
                "size": size,
            },
            "systemaddons": systemaddons
        }
        client.create_record(fixture)


if __name__ == "__main__":
    main()
