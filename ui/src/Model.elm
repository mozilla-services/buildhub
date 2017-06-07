module Model
    exposing
        ( init
        , initFilters
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
            , filters = initFilters
            , loading = True
            , route = MainView
            , error = Nothing
            , settings = { pageSize = 100 }
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


initFilters : Filters
initFilters =
    { product = "all"
    , version = "all"
    , platform = "all"
    , channel = "all"
    , locale = "all"
    , buildId = ""
    }


getFilters : String -> Cmd Msg
getFilters filterName =
    client
        |> Kinto.getList (filterRecordResource filterName)
        |> Kinto.sortBy [ "id" ]
        |> Kinto.send (FiltersReceived filterName)


getBuildRecordList : Model -> Cmd Msg
getBuildRecordList { filters, settings } =
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
            if filters.buildId /= "" then
                Kinto.withFilter (Kinto.LIKE "build.id" <| ("\"" ++ filters.buildId ++ "\"")) request
            else
                request
    in
        client
            |> Kinto.getList buildRecordResource
            |> Kinto.limit settings.pageSize
            |> Kinto.sortBy [ "-build.date" ]
            |> applyListFilter (Kinto.Equal "source.product") filters.product
            |> applyListFilter (Kinto.Equal "target.channel") filters.channel
            |> applyListFilter (Kinto.Equal "target.platform") filters.platform
            |> applyListFilter (Kinto.Equal "target.version") filters.version
            |> applyListFilter (Kinto.Equal "target.locale") filters.locale
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
