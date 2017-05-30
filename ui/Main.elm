module Main exposing (..)

import Model exposing (..)
import Navigation exposing (..)
import Set
import Types exposing (..)
import Url exposing (..)
import View exposing (..)


main : Program Never Model Msg
main =
    Navigation.program
        UrlChange
        { init = init
        , view = view
        , update = update
        , subscriptions = always Sub.none
        }


update : Msg -> Model -> ( Model, Cmd Msg )
update msg ({ filterValues } as model) =
    case msg of
        BuildRecordsFetched (Ok buildRecordList) ->
            updateModelWithFilters ({ model | builds = buildRecordList, loading = False })
                ! []

        BuildRecordsFetched (Err err) ->
            let
                _ =
                    Debug.log "An error occured while fetching the build records" err
            in
                model ! []

        UpdateFilter newFilter ->
            let
                updatedFilters =
                    case newFilter of
                        ClearAll ->
                            { model
                                | treeFilter = "all"
                                , productFilter = "all"
                                , versionFilter = "all"
                                , platformFilter = "all"
                                , channelFilter = "all"
                                , localeFilter = "all"
                                , buildIdFilter = ""
                            }

                        NewTreeFilter value ->
                            { model | treeFilter = value }

                        NewProductFilter value ->
                            { model | productFilter = value }

                        NewVersionFilter value ->
                            { model | versionFilter = value }

                        NewPlatformFilter value ->
                            { model | platformFilter = value }

                        NewChannelFilter value ->
                            { model | channelFilter = value }

                        NewLocaleFilter value ->
                            { model | localeFilter = value }

                        NewBuildIdSearch value ->
                            { model | buildIdFilter = value }

                updatedRoute =
                    { model | route = routeFromFilters updatedFilters }
            in
                updateModelWithFilters updatedRoute
                    ! [ newUrl <| urlFromRoute updatedRoute ]

        UrlChange location ->
            updateModelWithFilters (routeFromUrl model location) ! []
