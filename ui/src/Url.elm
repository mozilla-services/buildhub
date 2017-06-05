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
                    , map ProductView
                        (s "builds"
                            </> (s "product" </> string)
                        )
                    , map ChannelView
                        (s "builds"
                            </> (s "product" </> string)
                            </> (s "channel" </> string)
                        )
                    , map PlatformView
                        (s "builds"
                            </> (s "product" </> string)
                            </> (s "channel" </> string)
                            </> (s "platform" </> string)
                        )
                    , map VersionView
                        (s "builds"
                            </> (s "product" </> string)
                            </> (s "channel" </> string)
                            </> (s "platform" </> string)
                            </> (s "version" </> string)
                        )
                    , map LocaleView
                        (s "builds"
                            </> (s "product" </> string)
                            </> (s "channel" </> string)
                            </> (s "platform" </> string)
                            </> (s "version" </> string)
                            </> (s "locale" </> string)
                        )
                    , map BuildIdView
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

            Just (BuildIdView product channel platform version locale buildId) ->
                { model
                    | route = BuildIdView product channel platform version locale buildId
                    , filters =
                        { buildId = buildId
                        , product = product
                        , channel = channel
                        , platform = platform
                        , version = version
                        , locale = locale
                        }
                }

            Just (ProductView product) ->
                { model
                    | route = ProductView product
                    , filters =
                        { buildId = ""
                        , product = product
                        , channel = "all"
                        , platform = "all"
                        , version = "all"
                        , locale = "all"
                        }
                }

            Just (ChannelView product channel) ->
                { model
                    | route = ChannelView product channel
                    , filters =
                        { buildId = ""
                        , product = product
                        , channel = channel
                        , platform = "all"
                        , version = "all"
                        , locale = "all"
                        }
                }

            Just (PlatformView product channel platform) ->
                { model
                    | route = PlatformView product channel platform
                    , filters =
                        { buildId = ""
                        , product = product
                        , channel = channel
                        , platform = platform
                        , version = "all"
                        , locale = "all"
                        }
                }

            Just (VersionView product channel platform version) ->
                { model
                    | route = VersionView product channel platform version
                    , filters =
                        { buildId = ""
                        , product = product
                        , channel = channel
                        , platform = platform
                        , version = version
                        , locale = "all"
                        }
                }

            Just (LocaleView product channel platform version locale) ->
                { model
                    | route = VersionView product channel platform version
                    , filters =
                        { buildId = ""
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

        ProductView product ->
            "#/builds/product/" ++ product

        ChannelView product channel ->
            "#/builds/product/"
                ++ product
                ++ "/channel/"
                ++ channel

        PlatformView product channel platform ->
            "#/builds/product/"
                ++ product
                ++ "/channel/"
                ++ channel
                ++ "/platform/"
                ++ platform

        VersionView product channel platform version ->
            "#/builds/product/"
                ++ product
                ++ "/channel/"
                ++ channel
                ++ "/platform/"
                ++ platform
                ++ "/version/"
                ++ version

        LocaleView product channel platform version locale ->
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

        BuildIdView product channel platform version locale buildId ->
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
    if buildId /= "" then
        BuildIdView product channel platform version locale buildId
    else if locale /= "all" then
        LocaleView product channel platform version locale
    else if version /= "all" then
        VersionView product channel platform version
    else if platform /= "all" then
        PlatformView product channel platform
    else if channel /= "all" then
        ChannelView product channel
    else if product /= "all" then
        ProductView product
    else
        MainView
