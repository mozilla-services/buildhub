module Snippet exposing (snippets)

import Types exposing (..)


snippets : List Snippet
snippets =
    [ { title = "Is this an official buildid?"
      , description = "In order to check that a build id exists, we'll just check that it is mentionned in at least one record."
      , snippets =
            { curl = """curl -s -I "https://kinto-ota.dev.mozaws.net/v1/buckets/build-hub/collections/releases/records?build.id=20110110192031&_limit=1" | grep "Total-Records: 1" """
            , js = """import KintoClient from "kinto-http";
const client = new KintoClient("https://kinto-ota.dev.mozaws.net/v1");

records = await client.listRecords({limit: 1, filters: {"build.id": "20110110192031"}});
console.log(records.length == 1);
"""
            , python = """import kinto_http

client = kinto_http.Client("https://kinto-ota.dev.mozaws.net/v1")
records = client.get_records(**{"build.id": "20110110192031", "_limit": 1, "pages": 1},
                             bucket="build-hub", collection="releases")
print(len(records) == 1)
"""
            }
      }
    , { title = "What is the revision of a build id?"
      , description = ""
      , snippets =
            { curl = """curl -s "https://kinto-ota.dev.mozaws.net/v1/buckets/build-hub/collections/releases/records?build.id=20110110192031&_limit=1" | grep -Po '"revision":"[^"]+' | sed 's/"revision":"//'"""
            , js = """import KintoClient from "kinto-http";

const client = new KintoClient("https://kinto-ota.dev.mozaws.net/v1");
const collection = client.bucket("build-hub").collection("releases");
const records = await collection.listRecords({limit: 1, filters: {"build.id": "20110110192031"}});
const revision = records[0].source.revision;"""
            , python = """client = kinto_http.Client("https://kinto-ota.dev.mozaws.net/v1")
records = client.get_records(**{"build.id": "20110110192031", "_limit": 1, "pages": 1},
                             bucket="build-hub", collection="releases")
revision = records[0]["source"]["revision"]"""
            }
      }
    , { title = "What are the locales of a specific version?"
      , description = ""
      , snippets =
            { curl = """curl -s "https://kinto-ota.dev.mozaws.net/v1/buckets/build-hub/collections/releases/records?target.version=53.0b9&_fields=target.locale" | grep -Po '"locale":"[^"]+' | sed 's/"locale":"//' | sort -u"""
            , js = """import KintoClient from "kinto-http";

const client = new KintoClient("https://kinto-ota.dev.mozaws.net/v1");
const collection = client.bucket("build-hub").collection("releases");
const records = await collection.listRecords({filters: {"target.version": "53.0b9"}});
const locales = new Set(records.map(r => r.target.locale));"""
            , python = """import kinto_http

client = kinto_http.Client("https://kinto-ota.dev.mozaws.net/v1")
records = client.get_records(**{"target.version": "53.0b9"},
                             bucket="build-hub", collection="releases")
locales = set({record["target"]["locale"] for record in records})"""
            }
      }
    ]
