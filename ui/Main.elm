module Main exposing (..)

import Html exposing (..)
import Model exposing (..)
import Set
import Types exposing (..)
import View exposing (..)


main : Program Never Model Msg
main =
    Html.program
        { init = init
        , view = view
        , update = update
        , subscriptions = always Sub.none
        }


update : Msg -> Model -> ( Model, Cmd Msg )
update msg model =
    case msg of
        BuildRecordsFetched (Ok buildRecordList) ->
            { model
                | builds = buildRecordList
                , filteredBuilds = buildRecordList
                , filterValues = extractFilterValues buildRecordList
                , loading = False
            }
                ! []

        BuildRecordsFetched (Err err) ->
            let
                _ =
                    Debug.log "An error occured while fetching the build records" err
            in
                model ! []

        NewTreeFilter value ->
            let
                updatedModelWithFilters =
                    { model | treeFilter = value }

                updatedFilteredBuilds =
                    applyFilters updatedModelWithFilters
            in
                { updatedModelWithFilters
                    | filteredBuilds = updatedFilteredBuilds
                    , filterValues = extractFilterValues updatedFilteredBuilds
                }
                    ! []

        NewProductFilter value ->
            let
                updatedModelWithFilters =
                    { model | productFilter = value }

                updatedFilteredBuilds =
                    applyFilters updatedModelWithFilters
            in
                { updatedModelWithFilters
                    | filteredBuilds = updatedFilteredBuilds
                    , filterValues = extractFilterValues updatedFilteredBuilds
                }
                    ! []

        NewVersionFilter value ->
            let
                updatedModelWithFilters =
                    { model | versionFilter = value }

                updatedFilteredBuilds =
                    applyFilters updatedModelWithFilters
            in
                { updatedModelWithFilters
                    | filteredBuilds = updatedFilteredBuilds
                    , filterValues = extractFilterValues updatedFilteredBuilds
                }
                    ! []

        NewPlatformFilter value ->
            let
                updatedModelWithFilters =
                    { model | platformFilter = value }

                updatedFilteredBuilds =
                    applyFilters updatedModelWithFilters
            in
                { updatedModelWithFilters
                    | filteredBuilds = updatedFilteredBuilds
                    , filterValues = extractFilterValues updatedFilteredBuilds
                }
                    ! []

        NewChannelFilter value ->
            let
                updatedModelWithFilters =
                    { model | channelFilter = value }

                updatedFilteredBuilds =
                    applyFilters updatedModelWithFilters
            in
                { updatedModelWithFilters
                    | filteredBuilds = updatedFilteredBuilds
                    , filterValues = extractFilterValues updatedFilteredBuilds
                }
                    ! []

        NewLocaleFilter value ->
            let
                updatedModelWithFilters =
                    { model | localeFilter = value }

                updatedFilteredBuilds =
                    applyFilters updatedModelWithFilters
            in
                { updatedModelWithFilters
                    | filteredBuilds = updatedFilteredBuilds
                    , filterValues = extractFilterValues updatedFilteredBuilds
                }
                    ! []


extractFilterValues : List BuildRecord -> FilterValues
extractFilterValues buildRecordList =
    let
        filterValues =
            (List.foldl
                (\buildRecord filterValues ->
                    { treeList = buildRecord.source.tree :: filterValues.treeList
                    , productList = buildRecord.source.product :: filterValues.productList
                    , versionList = (Maybe.withDefault "" buildRecord.target.version) :: filterValues.versionList
                    , platformList = buildRecord.target.platform :: filterValues.platformList
                    , channelList = (Maybe.withDefault "" buildRecord.target.channel) :: filterValues.channelList
                    , localeList = buildRecord.target.locale :: filterValues.localeList
                    }
                )
                { treeList = []
                , productList = []
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
            | treeList = filterValues.treeList |> normalizeFilterValues
            , productList = filterValues.productList |> normalizeFilterValues
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
                (recordStringEquals (.source >> .tree) model.treeFilter) buildRecord
                    && (recordStringEquals (.source >> .product) model.productFilter) buildRecord
                    && (recordMaybeStringEquals (.target >> .version) model.versionFilter) buildRecord
                    && (recordStringEquals (.target >> .platform) model.platformFilter) buildRecord
                    && (recordMaybeStringEquals (.target >> .channel) model.channelFilter) buildRecord
                    && (recordStringEquals (.target >> .locale) model.localeFilter) buildRecord
            )
