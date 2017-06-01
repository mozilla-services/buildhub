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
            let
                newPager =
                    Kinto.updatePager buildsPager model.buildsPager
            in
                updateModelWithFilters
                    { model
                        | buildsPager = newPager
                        , filteredBuilds = newPager.objects
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

        UpdateFilter newFilter ->
            let
                updatedModelWithFilters =
                    case newFilter of
                        ClearAll ->
                            { model
                                | productFilter = "all"
                                , versionFilter = "all"
                                , platformFilter = "all"
                                , channelFilter = "all"
                                , localeFilter = "all"
                                , buildIdFilter = ""
                            }

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

                updatedModelWithRoute =
                    { model | route = routeFromFilters updatedModelWithFilters }
            in
                updateModelWithFilters updatedModelWithRoute
                    ! [ newUrl <| urlFromRoute updatedModelWithRoute.route
                      , getBuildRecordList updatedModelWithRoute
                      ]

        UrlChange location ->
            let
                updatedModel =
                    updateModelWithFilters (routeFromUrl model location)
            in
                updatedModel ! [ getBuildRecordList updatedModel ]
