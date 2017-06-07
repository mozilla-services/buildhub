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


updateFilters : NewFilter -> Filters -> Filters
updateFilters newFilter filters =
    case newFilter of
        ClearAll ->
            initFilters

        NewProductFilter value ->
            { filters | product = value }

        NewVersionFilter value ->
            { filters | version = value }

        NewPlatformFilter value ->
            { filters | platform = value }

        NewChannelFilter value ->
            { filters | channel = value }

        NewLocaleFilter value ->
            { filters | locale = value }

        NewBuildIdSearch value ->
            { filters | buildId = value }


update : Msg -> Model -> ( Model, Cmd Msg )
update msg ({ filters, filterValues } as model) =
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
            { model
                | buildsPager = Kinto.updatePager buildsPager model.buildsPager
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
            { model | filters = updateFilters newFilter filters } ! []

        SubmitFilters ->
            let
                route =
                    routeFromFilters filters
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

        NewPageSize sizeStr ->
            let
                modelSettings =
                    model.settings

                updatedSettings =
                    { modelSettings | pageSize = Result.withDefault 100 <| String.toInt sizeStr }

                updatedModel =
                    { model | settings = updatedSettings, loading = True }
            in
                updatedModel ! [ getBuildRecordList updatedModel ]
