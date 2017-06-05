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
    {- FIXME: https://github.com/Kinto/kinto/issues/1217: here we surround all qs param values with quotes
       in case they're treated as numbers by Kinto, which makes it crash.
    -}
    let
        applyListFilter apply filter request =
            if filter /= "all" then
                Kinto.withFilter (apply ("\"" ++ filter ++ "\"")) request
            else
                request

        applyBuildIdFilter request =
            if buildIdFilter /= "" then
                Kinto.withFilter (Kinto.LIKE "build.id" <| ("\"" ++ buildIdFilter ++ "\"")) request
            else
                request
    in
        client
            |> Kinto.getList buildRecordResource
            |> Kinto.limit pageSize
            |> Kinto.sortBy [ "-build.date" ]
            |> applyListFilter (Kinto.Equal "source.product") productFilter
            |> applyListFilter (Kinto.Equal "target.channel") channelFilter
            |> applyListFilter (Kinto.Equal "target.platform") platformFilter
            |> applyListFilter (Kinto.Equal "target.version") versionFilter
            |> applyListFilter (Kinto.Equal "target.locale") localeFilter
            |> applyBuildIdFilter
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
