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
            { filters | product = value, page = 1 }

        NewVersionFilter value ->
            { filters | version = value, page = 1 }

        NewPlatformFilter value ->
            { filters | platform = value, page = 1 }

        NewChannelFilter value ->
            { filters | channel = value, page = 1 }

        NewLocaleFilter value ->
            { filters | locale = value, page = 1 }

        NewBuildIdSearch value ->
            { filters | buildId = value, page = 1 }


update : Msg -> Model -> ( Model, Cmd Msg )
update msg ({ filters, settings } as model) =
    case msg of
        FacetsReceived (Ok facets) ->
            { model | facets = Just <| ElasticSearch.processFacets facets } ! []

        FacetsReceived (Err error) ->
            { model | error = Just (toString error) } ! []

        LoadNextPage ->
            let
                updatedFilters =
                    { filters | page = filters.page + 1 }

                updatedRoute =
                    routeFromFilters updatedFilters
            in
                { model | route = updatedRoute, filters = updatedFilters }
                    ! [ newUrl <| urlFromRoute updatedRoute ]

        LoadPreviousPage ->
            let
                updatedFilters =
                    { filters | page = filters.page - 1 }

                updatedRoute =
                    routeFromFilters updatedFilters
            in
                { model | route = updatedRoute, filters = updatedFilters }
                    ! [ newUrl <| urlFromRoute updatedRoute ]

        UpdateFilter newFilter ->
            let
                updatedFilters =
                    updateFilters newFilter filters

                updatedRoute =
                    routeFromFilters updatedFilters
            in
                { model | filters = updatedFilters }
                    ! [ newUrl <| urlFromRoute updatedRoute ]

        UrlChange location ->
            let
                updatedModel =
                    routeFromUrl model location
            in
                { updatedModel | error = Nothing }
                    ! [ ElasticSearch.getFacets updatedModel.filters settings.pageSize
                            |> Http.send FacetsReceived
                      ]

        DismissError ->
            { model | error = Nothing } ! []

        NewPageSize sizeStr ->
            let
                newPageSize =
                    Result.withDefault 100 <| String.toInt sizeStr

                updatedFilters =
                    { filters | page = 1 }
            in
                { model
                    | filters = updatedFilters
                    , settings = { settings | pageSize = newPageSize }
                }
                    ! [ ElasticSearch.getFacets updatedFilters newPageSize
                            |> Http.send FacetsReceived
                      ]
