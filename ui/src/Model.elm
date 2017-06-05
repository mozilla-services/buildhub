module Model
    exposing
        ( init
        , getBuildRecordList
        , getNextBuilds
        )

import Decoder exposing (..)
import Kinto
import Navigation exposing (..)
import Types exposing (..)
import Url exposing (..)


init : Location -> ( Model, Cmd Msg )
init location =
    let
        defaultModel =
            { buildsPager = Kinto.emptyPager client buildRecordResource
            , filterValues = FilterValues [] [] [] [] []
            , productFilter = "all"
            , versionFilter = "all"
            , platformFilter = "all"
            , channelFilter = "all"
            , localeFilter = "all"
            , buildIdFilter = ""
            , loading = True
            , route = MainView
            , error = Nothing
            }

        updatedModel =
            routeFromUrl defaultModel location
    in
        updatedModel
            ! [ getFilters "product"
              , getFilters "channel"
              , getFilters "platform"
              , getFilters "version"
              , getFilters "locale"
              , getBuildRecordList updatedModel
              ]


getFilters : String -> Cmd Msg
getFilters filterName =
    client
        |> Kinto.getList (filterRecordResource filterName)
        |> Kinto.sortBy [ "name" ]
        |> Kinto.send (FiltersReceived filterName)


getBuildRecordList : Model -> Cmd Msg
getBuildRecordList { buildIdFilter, productFilter, channelFilter, platformFilter, versionFilter, localeFilter } =
    let
        request =
            client
                |> Kinto.getList buildRecordResource
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
                        -- Temporary workaround for https://github.com/Kinto/kinto/issues/1217 : surround version with quotes
                        Kinto.withFilter (Kinto.Equal "target.version" ("\"" ++ versionFilter ++ "\""))
                    else
                        identity
                   )
                |> (if localeFilter /= "all" then
                        Kinto.withFilter (Kinto.Equal "target.locale" localeFilter)
                    else
                        identity
                   )
                |> (if buildIdFilter /= "" then
                        -- Temporary workaround for https://github.com/Kinto/kinto/issues/1217 : surround version with quotes
                        Kinto.withFilter (Kinto.LIKE "build.id" <| ("\"" ++ buildIdFilter ++ "\""))
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


buildRecordResource : Kinto.Resource BuildRecord
buildRecordResource =
    Kinto.recordResource "build-hub" "releases" buildRecordDecoder


filterRecordResource : String -> Kinto.Resource FilterRecord
filterRecordResource filterName =
    Kinto.recordResource "build-hub" (filterName ++ "_filters") filterRecordDecoder
