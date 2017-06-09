module Model
    exposing
        ( init
        , initFilters
        , getFilterFacets
        )

import ElasticSearch
import Http
import Navigation exposing (..)
import Types exposing (..)
import Url exposing (..)


kintoServer : String
kintoServer =
    "https://kinto-ota.dev.mozaws.net/v1/"


init : Location -> ( Model, Cmd Msg )
init location =
    let
        defaultSettings =
            { pageSize = 100 }

        defaultModel =
            { filters = initFilters
            , facets = Nothing
            , page = 1
            , route = MainView
            , error = Nothing
            , settings = defaultSettings
            }

        updatedModel =
            routeFromUrl defaultModel location
    in
        updatedModel
            ! [ getFilterFacets updatedModel.filters defaultSettings.pageSize updatedModel.page ]


initFilters : Filters
initFilters =
    { product = "all"
    , version = "all"
    , platform = "all"
    , channel = "all"
    , locale = "all"
    , buildId = ""
    }


getFilterFacets : Filters -> Int -> Int -> Cmd Msg
getFilterFacets filters pageSize page =
    let
        searchEndpoint =
            kintoServer ++ "buckets/build-hub/collections/releases/search"
    in
        ElasticSearch.getFacets searchEndpoint filters pageSize page
            |> Http.send FacetsReceived
