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
                        )
                    ]
                )
                location
    in
        case route of
            Just DocsView ->
                { model | route = DocsView }

            Just (FilteredView product channel platform version locale buildId) ->
                { model
                    | route = FilteredView product channel platform version locale buildId
                    , filters =
                        { buildId = buildId
                        , product = product
                        , channel = channel
                        , platform = platform
                        , version = version
                        , locale = locale
                        }
                }

            _ ->
                { model
                    | route = MainView
                    , filters =
                        { buildId = ""
                        , product = "all"
                        , channel = "all"
                        , platform = "all"
                        , version = "all"
                        , locale = "all"
                        }
                }


urlFromRoute : Route -> String
urlFromRoute route =
    case route of
        DocsView ->
            "#/docs/"

        FilteredView product channel platform version locale buildId ->
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

        _ ->
            "#/builds/"


routeFromFilters : Filters -> Route
routeFromFilters { buildId, locale, version, platform, channel, product } =
    if
        (buildId /= "")
            || (locale /= "all")
            || (version /= "all")
            || (platform /= "all")
            || (channel /= "all")
            || (product /= "all")
    then
        FilteredView product channel platform version locale buildId
    else
        MainView
