module Main exposing (..)

import Kinto
import Model exposing (..)
import Navigation exposing (..)
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
        BuildRecordsFetched (Ok buildsPager) ->
            { model
                | buildsPager = buildsPager
                , loading = False
            }
                ! []

        BuildRecordsFetched (Err err) ->
            let
                _ =
                    Debug.log "An error occured while fetching the build records" err
            in
                model ! []

        LoadNextPage ->
            model ! [ getNextBuilds model.buildsPager ]

        BuildRecordsNextPageFetched (Ok buildsPager) ->
            let
                newPager =
                    Kinto.updatePager buildsPager model.buildsPager
            in
                { model
                    | buildsPager = newPager
                    , loading = False
                }
                    ! []

        BuildRecordsNextPageFetched (Err err) ->
            let
                _ =
                    Debug.log "An error occured while fetching the next page of build records" err
            in
                model ! []

        UpdateFilter newFilter ->
            let
                noFilters =
                    { model
                        | productFilter = "all"
                        , versionFilter = "all"
                        , platformFilter = "all"
                        , channelFilter = "all"
                        , localeFilter = "all"
                        , buildIdFilter = ""
                    }

                noBuildId =
                    { model | buildIdFilter = "" }

                updatedModelWithFilters =
                    case newFilter of
                        ClearAll ->
                            noFilters

                        NewProductFilter value ->
                            { noBuildId | productFilter = value }

                        NewVersionFilter value ->
                            { noBuildId | versionFilter = value }

                        NewPlatformFilter value ->
                            { noBuildId | platformFilter = value }

                        NewChannelFilter value ->
                            { noBuildId | channelFilter = value }

                        NewLocaleFilter value ->
                            { noBuildId | localeFilter = value }

                        NewBuildIdSearch value ->
                            { noFilters | buildIdFilter = value }

                updatedModelWithRoute =
                    { model | route = routeFromFilters updatedModelWithFilters }
            in
                { updatedModelWithRoute | loading = True }
                    ! [ newUrl <| urlFromRoute updatedModelWithRoute.route ]

        UrlChange location ->
            let
                updatedModel =
                    routeFromUrl model location
            in
                { updatedModel | loading = True } ! [ getBuildRecordList updatedModel ]
