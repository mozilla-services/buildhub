module Update exposing (update)

import ElasticSearch
import Init
import Http
import Navigation exposing (..)
import Types exposing (..)
import Url exposing (..)


navigateToPage : Model -> Page -> ( Model, Cmd Msg )
navigateToPage ({ filters } as model) newPage =
    let
        updatedFilters =
            { filters | page = newPage }

        updatedRoute =
            routeFromFilters updatedFilters
    in
        { model | route = updatedRoute, filters = updatedFilters }
            ! [ newUrl <| urlFromRoute updatedRoute ]


updateFilters : Facets -> NewFilter -> Filters -> Filters
updateFilters facets newFilter filters =
    let
        toggleFilter facets value values =
            if List.member value values then
                List.filter (\v -> v /= value) values
            else
                value :: values
    in
        case newFilter of
            ClearAll ->
                Init.initFilters

            ClearProducts ->
                { filters | product = [], page = 1 }

            ClearVersions ->
                { filters | version = [], page = 1 }

            ClearChannels ->
                { filters | channel = [], page = 1 }

            ClearPlatforms ->
                { filters | platform = [], page = 1 }

            ClearLocales ->
                { filters | locale = [], page = 1 }

            ClearSearch ->
                { filters | search = "", page = 1 }

            NewProductFilter value active ->
                { filters | product = filters.product |> toggleFilter facets.products value, page = 1 }

            NewVersionFilter value active ->
                { filters | version = filters.version |> toggleFilter facets.versions value, page = 1 }

            NewPlatformFilter value active ->
                { filters | platform = filters.platform |> toggleFilter facets.platforms value, page = 1 }

            NewChannelFilter value active ->
                { filters | channel = filters.channel |> toggleFilter facets.channels value, page = 1 }

            NewLocaleFilter value active ->
                { filters | locale = filters.locale |> toggleFilter facets.locales value, page = 1 }

            NewSearch search ->
                { filters | search = search, page = 1 }


update : Msg -> Model -> ( Model, Cmd Msg )
update msg ({ filters, settings } as model) =
    case msg of
        FacetsReceived (Ok facets) ->
            { model | facets = Just <| ElasticSearch.processFacets facets } ! []

        FacetsReceived (Err error) ->
            { model | error = Just (toString error) } ! []

        LoadNextPage ->
            navigateToPage model <| filters.page + 1

        LoadPreviousPage ->
            navigateToPage model <| filters.page - 1

        UpdateFilter newFilter ->
            case model.facets of
                Nothing ->
                    model ! []

                Just facets ->
                    let
                        updatedFilters =
                            updateFilters facets newFilter filters

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

        SubmitSearch ->
            model ! []

        ToggleBuildDetails id ->
            if List.member id model.expanded then
                { model | expanded = List.filter (\i -> i /= id) model.expanded } ! []
            else
                { model | expanded = id :: model.expanded } ! []
