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
                        , product = product |> String.split "|"
                        , channel = channel |> String.split "|"
                        , platform = platform |> String.split "|"
                        , version = version |> String.split "|"
                        , locale = locale |> String.split "|"
                        , page = page
                        }
                }

            _ ->
                { model
                    | route = MainView
                    , filters =
                        { buildId = ""
                        , product = [ "all" ]
                        , channel = [ "all" ]
                        , platform = [ "all" ]
                        , version = [ "all" ]
                        , locale = [ "all" ]
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
    FilteredView
        (product |> String.join "|")
        (channel |> String.join "|")
        (platform |> String.join "|")
        (version |> String.join "|")
        (locale |> String.join "|")
        buildId
        page
