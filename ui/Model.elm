module Model exposing (init)

import Decoder exposing (..)
import Json.Decode exposing (..)
import Types exposing (..)


init : ( Model, Cmd Msg )
init =
    Model [ testDecode ] True ! []


testDecode : BuildRecord
testDecode =
    case (decodeString buildRecordDecoder record) of
        Err message ->
            Debug.crash message

        Ok buildRecord ->
            buildRecord


record =
    """
    {
      "id": "e0f2fc81-e46a-4920-bb2c-5e45614861c7",
      "target": {
        "version": "55.0a1",
        "platform": "win32",
        "channel": null,
        "locale": "en-US"
      },
      "download": {
        "mimetype": "application/zip",
        "size": 51095048,
        "url": "https://archive.mozilla.org/pub/firefox/tinderbox-builds/mozilla-central-win32/1493737641/firefox-55.0a1.en-US.win32.zip"
      },
      "source": {
        "product": "firefox",
        "tree": "mozilla-central",
        "revision": "bfc7b187005cabbc828ed9f5b61daf139c3cfd90"
      },
      "systemaddons": null,
      "build": {
        "date": "2017-05-02T08:07:21",
        "id": "20170502080721",
        "type": "opt"
      },
      "last_modified": 1493742886032
    }
"""
