module Model
    exposing
        ( init
        , getBuildRecordList
        , getNextBuilds
        , updateModelWithFilters
        )

import Decoder exposing (..)
import Filters exposing (..)
import Kinto
import Navigation exposing (..)
import Types exposing (..)
import Url exposing (..)


init : Location -> ( Model, Cmd Msg )
init location =
    let
        defaultModel =
            { buildsPager = Kinto.emptyPager client recordResource
            , filteredBuilds = []
            , filterValues = FilterValues productList channelList platformList versionList localeList
            , productFilter = "all"
            , versionFilter = "all"
            , platformFilter = "all"
            , channelFilter = "all"
            , localeFilter = "all"
            , buildIdFilter = ""
            , loading = True
            , route = MainView
            }

        updatedModel =
            updateModelWithFilters (routeFromUrl defaultModel location)
    in
        updatedModel ! [ getBuildRecordList updatedModel ]


getBuildRecordList : Model -> Cmd Msg
getBuildRecordList { productFilter, channelFilter, platformFilter, versionFilter, localeFilter } =
    let
        request =
            client
                |> Kinto.getList recordResource
                |> Kinto.limit pageSize
                |> Kinto.sortBy [ "-build.date" ]

        filteredRequest =
            request
                |> (if productFilter /= "all" then
                        Kinto.withFilter (Kinto.Equal "source.product" productFilter)
                    else
                        identity
                   )
                |> (if channelFilter /= "all" then
                        Kinto.withFilter (Kinto.Equal "target.channel" channelFilter)
                    else
                        identity
                   )
                |> (if platformFilter /= "all" then
                        Kinto.withFilter (Kinto.Equal "target.platform" platformFilter)
                    else
                        identity
                   )
                |> (if versionFilter /= "all" then
                        Kinto.withFilter (Kinto.Equal "target.version" versionFilter)
                    else
                        identity
                   )
                |> (if localeFilter /= "all" then
                        Kinto.withFilter (Kinto.Equal "target.locale" localeFilter)
                    else
                        identity
                   )
    in
        filteredRequest
            |> Kinto.send BuildRecordsFetched


getNextBuilds : Kinto.Pager BuildRecord -> Cmd Msg
getNextBuilds pager =
    case Kinto.loadNextPage pager of
        Just request ->
            request |> Kinto.send BuildRecordsNextPageFetched

        Nothing ->
            Cmd.none


client : Kinto.Client
client =
    Kinto.client
        "https://kinto-ota.dev.mozaws.net/v1/"
        (Kinto.Basic "user" "pass")


recordResource : Kinto.Resource BuildRecord
recordResource =
    Kinto.recordResource "build-hub" "fixtures" buildRecordDecoder


recordStringEquals : (BuildRecord -> String) -> String -> BuildRecord -> Bool
recordStringEquals path filterValue buildRecord =
    (filterValue == "all")
        || (buildRecord
                |> path
                |> (==) filterValue
           )


recordStringStartsWith : (BuildRecord -> String) -> String -> BuildRecord -> Bool
recordStringStartsWith path filterValue buildRecord =
    buildRecord
        |> path
        |> String.startsWith filterValue


applyFilters : Model -> List BuildRecord
applyFilters model =
    model.buildsPager.objects
        |> List.filter
            (\buildRecord ->
                (recordStringEquals (.source >> .product) model.productFilter) buildRecord
                    && (recordStringEquals (.target >> .version) model.versionFilter) buildRecord
                    && (recordStringEquals (.target >> .platform) model.platformFilter) buildRecord
                    && (recordStringEquals (.target >> .channel) model.channelFilter) buildRecord
                    && (recordStringEquals (.target >> .locale) model.localeFilter) buildRecord
                    && (recordStringStartsWith (.build >> Maybe.withDefault (Build "" "" "") >> .id) model.buildIdFilter) buildRecord
            )


updateModelWithFilters : Model -> Model
updateModelWithFilters model =
    let
        filteredBuilds =
            applyFilters model
    in
        { model
            | filteredBuilds = filteredBuilds
        }
