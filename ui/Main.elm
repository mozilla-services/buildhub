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
            let
                treeList =
                    buildRecordList
                        |> List.map .source
                        |> List.map .tree
                        |> Set.fromList
                        |> Set.toList

                productList =
                    buildRecordList
                        |> List.map .source
                        |> List.map .product
                        |> Set.fromList
                        |> Set.toList

                versionList =
                    buildRecordList
                        |> List.map .target
                        |> List.map .version
                        |> List.filterMap identity
                        |> Set.fromList
                        |> Set.toList

                platformList =
                    buildRecordList
                        |> List.map .target
                        |> List.map .platform
                        |> Set.fromList
                        |> Set.toList

                channelList =
                    buildRecordList
                        |> List.map .target
                        |> List.map .channel
                        |> List.filterMap identity
                        |> Set.fromList
                        |> Set.toList

                localeList =
                    buildRecordList
                        |> List.map .target
                        |> List.map .locale
                        |> Set.fromList
                        |> Set.toList
            in
                { model
                    | builds = buildRecordList
                    , filteredBuilds = buildRecordList
                    , treeList = treeList
                    , productList = productList
                    , versionList = versionList
                    , platformList = platformList
                    , channelList = channelList
                    , localeList = localeList
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
            in
                { updatedModelWithFilters | filteredBuilds = applyFilters updatedModelWithFilters } ! []

        NewProductFilter value ->
            let
                updatedModelWithFilters =
                    { model | productFilter = value }
            in
                { updatedModelWithFilters | filteredBuilds = applyFilters updatedModelWithFilters } ! []

        NewVersionFilter value ->
            let
                updatedModelWithFilters =
                    { model | versionFilter = value }
            in
                { updatedModelWithFilters | filteredBuilds = applyFilters updatedModelWithFilters } ! []

        NewPlatformFilter value ->
            let
                updatedModelWithFilters =
                    { model | platformFilter = value }
            in
                { updatedModelWithFilters | filteredBuilds = applyFilters updatedModelWithFilters } ! []

        NewChannelFilter value ->
            let
                updatedModelWithFilters =
                    { model | channelFilter = value }
            in
                { updatedModelWithFilters | filteredBuilds = applyFilters updatedModelWithFilters } ! []

        NewLocaleFilter value ->
            let
                updatedModelWithFilters =
                    { model | localeFilter = value }
            in
                { updatedModelWithFilters | filteredBuilds = applyFilters updatedModelWithFilters } ! []


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
