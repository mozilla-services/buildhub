module Main exposing (..)

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
update msg ({ filters, settings } as model) =
    case msg of
        FacetsReceived (Ok facets) ->
            { model | facets = Just facets } ! []

        FacetsReceived (Err error) ->
            { model | error = Just (toString error) } ! []

        LoadNextPage ->
            { model | page = model.page + 1 }
                ! [ getFilterFacets filters settings.pageSize (model.page + 1) ]

        LoadPreviousPage ->
            { model | page = model.page - 1 }
                ! [ getFilterFacets filters settings.pageSize (model.page - 1) ]

        UpdateFilter newFilter ->
            let
                updatedFilters =
                    updateFilters newFilter filters
            in
                { model | filters = updatedFilters, page = 1 }
                    ! [ getFilterFacets updatedFilters settings.pageSize 1 ]

        UrlChange location ->
            let
                updatedModel =
                    routeFromUrl model location
            in
                { updatedModel | error = Nothing }
                    -- FIXME: load facets here
                    ! []

        DismissError ->
            { model | error = Nothing } ! []

        NewPageSize sizeStr ->
            let
                modelSettings =
                    model.settings

                updatedSettings =
                    { modelSettings | pageSize = Result.withDefault 100 <| String.toInt sizeStr }

                updatedModel =
                    { model | settings = updatedSettings }
            in
                -- FIXME: relad facets with new pageSize
                updatedModel ! []
