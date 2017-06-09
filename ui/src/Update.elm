module Update exposing (update)

import ElasticSearch
import Init
import Http
import Navigation exposing (..)
import Types exposing (..)
import Url exposing (..)


updateFilters : NewFilter -> Filters -> Filters
updateFilters newFilter filters =
    case newFilter of
        ClearAll ->
            Init.initFilters

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
            { model | facets = Just <| ElasticSearch.processFacets facets } ! []

        FacetsReceived (Err error) ->
            { model | error = Just (toString error) } ! []

        LoadNextPage ->
            let
                nextPage =
                    model.page + 1

                updatedRoute =
                    routeFromFilters nextPage model.filters
            in
                { model | route = updatedRoute, page = nextPage }
                    ! [ newUrl <| urlFromRoute updatedRoute ]

        LoadPreviousPage ->
            let
                previousPage =
                    model.page - 1

                updatedRoute =
                    routeFromFilters previousPage model.filters
            in
                { model | route = updatedRoute, page = previousPage }
                    ! [ newUrl <| urlFromRoute updatedRoute ]

        UpdateFilter newFilter ->
            let
                updatedFilters =
                    updateFilters newFilter filters

                updatedRoute =
                    routeFromFilters 1 updatedFilters
            in
                { model | filters = updatedFilters, page = 1 }
                    ! [ newUrl <| urlFromRoute updatedRoute ]

        UrlChange location ->
            let
                updatedModel =
                    routeFromUrl model location
            in
                { updatedModel | error = Nothing, page = updatedModel.page }
                    ! [ ElasticSearch.getFacets updatedModel.filters settings.pageSize updatedModel.page
                            |> Http.send FacetsReceived
                      ]

        DismissError ->
            { model | error = Nothing } ! []

        NewPageSize sizeStr ->
            let
                newPageSize =
                    Result.withDefault 100 <| String.toInt sizeStr
            in
                { model | settings = { settings | pageSize = newPageSize }, page = 1 }
                    ! [ ElasticSearch.getFacets model.filters newPageSize 1
                            |> Http.send FacetsReceived
                      ]
