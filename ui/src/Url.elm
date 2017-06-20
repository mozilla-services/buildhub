module Url exposing (routeFromFilters, routeFromUrl, urlFromRoute)

import Navigation exposing (..)
import Types exposing (..)
import UrlParser exposing (..)


parseFilter : String -> List String
parseFilter textFilter =
    if textFilter == "all" then
        []
    else
        String.split "|" textFilter


routeFromUrl : Model -> Location -> Model
routeFromUrl model location =
    let
        route =
            parseHash
                (oneOf
                    [ map DocsView (s "docs" </> top)
                    , map MainView (s "builds" </> top)
                    , map FilteredView
                        (s "builds"
                            </> (s "product" </> string)
                            </> (s "channel" </> string)
                            </> (s "platform" </> string)
                            </> (s "version" </> string)
                            </> (s "locale" </> string)
                            </> (s "buildId" </> string)
                            </> (s "search" </> string)
                            </> (s "page" </> int)
                        )
                    ]
                )
                location
    in
        case route of
            Just DocsView ->
                { model | route = DocsView }

            Just (FilteredView product channel platform version locale buildId search page) ->
                { model
                    | route = FilteredView product channel platform version locale buildId search page
                    , filters =
                        { buildId = buildId
                        , product = parseFilter product
                        , channel = parseFilter channel
                        , platform = parseFilter platform
                        , version = parseFilter version
                        , locale = parseFilter locale
                        , search = search
                        , page = page
                        }
                }

            _ ->
                { model
                    | route = MainView
                    , filters =
                        { buildId = ""
                        , product = []
                        , channel = []
                        , platform = []
                        , version = []
                        , locale = []
                        , search = ""
                        , page = 1
                        }
                }


urlFromRoute : Route -> String
urlFromRoute route =
    case route of
        DocsView ->
            "#/docs/"

        FilteredView product channel platform version locale buildId search page ->
            "#/builds/product/"
                ++ product
                ++ "/channel/"
                ++ channel
                ++ "/platform/"
                ++ platform
                ++ "/version/"
                ++ version
                ++ "/locale/"
                ++ locale
                ++ "/buildId/"
                ++ buildId
                ++ "/search/"
                ++ search
                ++ "/page/"
                ++ (toString page)

        _ ->
            "#/builds/"


routeFromFilters : Filters -> Route
routeFromFilters { buildId, locale, version, platform, channel, product, search, page } =
    let
        buildUrlParam values =
            if List.length values == 0 then
                "all"
            else
                String.join "|" values
    in
        FilteredView
            (buildUrlParam product)
            (buildUrlParam channel)
            (buildUrlParam platform)
            (buildUrlParam version)
            (buildUrlParam locale)
            buildId
            search
            page
