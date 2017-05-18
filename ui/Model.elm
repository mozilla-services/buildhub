module Model exposing (init)

import Decoder exposing (..)
import Kinto
import Types exposing (..)


init : ( Model, Cmd Msg )
init =
    { builds = []
    , filteredBuilds = []
    , filterValues = FilterValues [] [] [] [] [] []
    , treeFilter = "all"
    , productFilter = "all"
    , versionFilter = "all"
    , platformFilter = "all"
    , channelFilter = "all"
    , localeFilter = "all"
    , buildIdFilter = ""
    , loading = True
    , currentView = MainView
    }
        ! [ getBuildRecordList ]


getBuildRecordList : Cmd Msg
getBuildRecordList =
    client
        |> Kinto.getList recordResource
        |> Kinto.sortBy [ "-build.date" ]
        |> Kinto.send BuildRecordsFetched


client : Kinto.Client
client =
    Kinto.client
        "https://kinto-ota.dev.mozaws.net/v1/"
        (Kinto.Basic "user" "pass")


recordResource : Kinto.Resource BuildRecord
recordResource =
    Kinto.recordResource "build-hub" "fixtures" buildRecordDecoder