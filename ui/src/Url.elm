module Url exposing (routeFromFilters, routeFromUrl, urlFromRoute)

import Navigation exposing (..)
import Types exposing (..)
import UrlParser exposing (..)


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
                            </> (s "page" </> int)
                        )
                    ]
                )
                location
    in
        case route of
            Just DocsView ->
                { model | route = DocsView }

            Just (FilteredView product channel platform version locale buildId page) ->
                { model
                    | route = FilteredView product channel platform version locale buildId page
                    , filters =
                        { buildId = buildId
                        , product = product |> String.split "|" |> List.filter (\v -> v /= "all")
                        , channel = channel |> String.split "|" |> List.filter (\v -> v /= "all")
                        , platform = platform |> String.split "|" |> List.filter (\v -> v /= "all")
                        , version = version |> String.split "|" |> List.filter (\v -> v /= "all")
                        , locale = locale |> String.split "|" |> List.filter (\v -> v /= "all")
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
                        , page = 1
                        }
                }


urlFromRoute : Route -> String
urlFromRoute route =
    case route of
        DocsView ->
            "#/docs/"

        FilteredView product channel platform version locale buildId page ->
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
                ++ "/page/"
                ++ (toString page)

        _ ->
            "#/builds/"


routeFromFilters : Filters -> Route
routeFromFilters { buildId, locale, version, platform, channel, product, page } =
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
            page
