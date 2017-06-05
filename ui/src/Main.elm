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
                , error = Nothing
            }
                ! []

        BuildRecordsFetched (Err err) ->
            { model | error = Just err, loading = False } ! []

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
                    , error = Nothing
                }
                    ! []

        BuildRecordsNextPageFetched (Err err) ->
            { model | error = Just err, loading = False } ! []

        FiltersReceived filterName (Ok { objects }) ->
            let
                values =
                    List.map .name objects
            in
                case filterName of
                    "product" ->
                        { model | filterValues = { filterValues | productList = values } } ! []

                    "channel" ->
                        { model | filterValues = { filterValues | channelList = values } } ! []

                    "platform" ->
                        { model | filterValues = { filterValues | platformList = values } } ! []

                    "version" ->
                        { model | filterValues = { filterValues | versionList = values } } ! []

                    "locale" ->
                        { model | filterValues = { filterValues | localeList = values } } ! []

                    _ ->
                        model ! []

        FiltersReceived filterName (Err err) ->
            { model | error = Just err, loading = False } ! []

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
            in
                updatedModelWithFilters ! []

        SubmitFilters ->
            let
                route =
                    routeFromFilters model
            in
                { model | route = route, loading = True, error = Nothing }
                    ! [ newUrl <| urlFromRoute route ]

        UrlChange location ->
            let
                updatedModel =
                    routeFromUrl model location
            in
                { updatedModel | loading = True, error = Nothing }
                    ! [ getBuildRecordList updatedModel ]

        DismissError ->
            { model | error = Nothing } ! []
