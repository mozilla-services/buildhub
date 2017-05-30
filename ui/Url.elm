module Url exposing (routeFromFilters, routeFromUrl, urlFromRoute)

import Navigation exposing (..)
import Types exposing (..)
import UrlParser exposing (..)


routeFromUrl : Model -> Location -> Model
routeFromUrl model location =
    let
        route =
            Debug.log "route" <|
                parseHash
                    (oneOf
                        [ map DocsView (s "docs" </> top)
                        , map MainView (s "builds" </> top)
                        , map BuildIdView
                            (s "builds"
                                </> (s "buildId" </> string)
                            )
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
                        ]
                    )
                    location
    in
        case route of
            Just DocsView ->
                { model | route = DocsView }

            Just (BuildIdView buildId) ->
                { model
                    | route = BuildIdView buildId
                    , buildIdFilter = Debug.log "id filter" buildId
                    , productFilter = "all"
                    , channelFilter = "all"
                    , platformFilter = "all"
                    , versionFilter = "all"
                    , localeFilter = "all"
                }

            Just (ProductView product) ->
                { model
                    | route = ProductView product
                    , buildIdFilter = ""
                    , productFilter = Debug.log "product filter" product
                    , channelFilter = "all"
                    , platformFilter = "all"
                    , versionFilter = "all"
                    , localeFilter = "all"
                }

            Just (ChannelView product channel) ->
                { model
                    | route = ChannelView product channel
                    , buildIdFilter = ""
                    , productFilter = Debug.log "product filter" product
                    , channelFilter = Debug.log "channel filter" channel
                    , platformFilter = "all"
                    , versionFilter = "all"
                    , localeFilter = "all"
                }

            Just (PlatformView product channel platform) ->
                { model
                    | route = PlatformView product channel platform
                    , buildIdFilter = ""
                    , productFilter = Debug.log "product filter" product
                    , channelFilter = Debug.log "channel filter" channel
                    , platformFilter = Debug.log "platform filter" platform
                    , versionFilter = "all"
                    , localeFilter = "all"
                }

            Just (VersionView product channel platform version) ->
                { model
                    | route = VersionView product channel platform version
                    , buildIdFilter = ""
                    , productFilter = Debug.log "product filter" product
                    , channelFilter = Debug.log "channel filter" channel
                    , platformFilter = Debug.log "platform filter" platform
                    , versionFilter = Debug.log "version filter" version
                    , localeFilter = "all"
                }

            Just (LocaleView product channel platform version locale) ->
                { model
                    | route = VersionView product channel platform version
                    , buildIdFilter = ""
                    , productFilter = Debug.log "product filter" product
                    , channelFilter = Debug.log "channel filter" channel
                    , platformFilter = Debug.log "platform filter" platform
                    , versionFilter = Debug.log "version filter" version
                    , localeFilter = Debug.log "locale fitler" locale
                }

            _ ->
                { model
                    | route = MainView
                    , buildIdFilter = ""
                    , productFilter = "all"
                    , channelFilter = "all"
                    , platformFilter = "all"
                    , versionFilter = "all"
                    , localeFilter = "all"
                }


urlFromRoute : Model -> String
urlFromRoute model =
    case model.route of
        DocsView ->
            "#/docs/"

        BuildIdView buildId ->
            "#/builds/buildId/" ++ buildId

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

        _ ->
            "#/builds/"


routeFromFilters : Model -> Route
routeFromFilters model =
    if model.buildIdFilter /= "" then
        BuildIdView model.buildIdFilter
    else if model.localeFilter /= "all" then
        LocaleView model.productFilter model.channelFilter model.platformFilter model.versionFilter model.localeFilter
    else if model.versionFilter /= "all" then
        VersionView model.productFilter model.channelFilter model.platformFilter model.versionFilter
    else if model.platformFilter /= "all" then
        PlatformView model.productFilter model.channelFilter model.platformFilter
    else if model.channelFilter /= "all" then
        ChannelView model.productFilter model.channelFilter
    else if model.productFilter /= "all" then
        ProductView model.productFilter
    else
        MainView
