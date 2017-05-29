module Model exposing (init, updateModelWithFilters)

import Decoder exposing (..)
import Kinto
import Navigation exposing (..)
import Set
import Types exposing (..)
import Url exposing (..)


init : Location -> ( Model, Cmd Msg )
init location =
    let
        defaultModel =
            { builds = []
            , filteredBuilds = []
            , filterValues = FilterValues [] [] [] [] []
            , productFilter = "all"
            , versionFilter = "all"
            , platformFilter = "all"
            , channelFilter = "all"
            , localeFilter = "all"
            , buildIdFilter = ""
            , loading = True
            , route = MainView
            }
    in
        updateModelWithFilters (routeFromUrl defaultModel location) ! [ getBuildRecordList ]


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


extractFilterValues : List BuildRecord -> FilterValues
extractFilterValues buildRecordList =
    let
        filterValues =
            (List.foldl
                (\buildRecord filterValues ->
                    { productList = buildRecord.source.product :: filterValues.productList
                    , versionList = buildRecord.target.version :: filterValues.versionList
                    , platformList = buildRecord.target.platform :: filterValues.platformList
                    , channelList = buildRecord.target.channel :: filterValues.channelList
                    , localeList = buildRecord.target.locale :: filterValues.localeList
                    }
                )
                { productList = []
                , versionList = []
                , platformList = []
                , channelList = []
                , localeList = []
                }
                buildRecordList
            )

        normalizeFilterValues : List String -> List String
        normalizeFilterValues values =
            values
                |> Set.fromList
                |> Set.remove ""
                |> Set.toList
    in
        { filterValues
            | productList = filterValues.productList |> normalizeFilterValues
            , versionList = filterValues.versionList |> normalizeFilterValues
            , platformList = filterValues.platformList |> normalizeFilterValues
            , channelList = filterValues.channelList |> normalizeFilterValues
            , localeList = filterValues.localeList |> normalizeFilterValues
        }


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


recordMaybeStringEquals : (BuildRecord -> Maybe String) -> String -> BuildRecord -> Bool
recordMaybeStringEquals path filterValue buildRecord =
    (filterValue == "all")
        || (buildRecord
                |> path
                |> Maybe.withDefault ""
                |> (==) filterValue
           )


applyFilters : Model -> List BuildRecord
applyFilters model =
    model.builds
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
            , filterValues = extractFilterValues filteredBuilds
        }
