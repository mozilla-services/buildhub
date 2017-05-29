module Url exposing (parsePage)

import Navigation exposing (..)
import Types exposing (..)
import UrlParser exposing (..)


parsePage : Model -> Location -> Model
parsePage model location =
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
                }

            Just (ProductView product) ->
                { model
                    | route = ProductView product
                    , productFilter = Debug.log "product filter" product
                    , channelFilter = "all"
                    , platformFilter = "all"
                    , versionFilter = "all"
                }

            Just (ChannelView product channel) ->
                { model
                    | route = ChannelView product channel
                    , productFilter = Debug.log "product filter" product
                    , channelFilter = Debug.log "channel filter" channel
                    , platformFilter = "all"
                    , versionFilter = "all"
                }

            Just (PlatformView product channel platform) ->
                { model
                    | route = PlatformView product channel platform
                    , productFilter = Debug.log "product filter" product
                    , channelFilter = Debug.log "channel filter" channel
                    , platformFilter = Debug.log "platform filter" platform
                    , versionFilter = "all"
                }

            Just (VersionView product channel platform version) ->
                { model
                    | route = VersionView product channel platform version
                    , productFilter = Debug.log "product filter" product
                    , channelFilter = Debug.log "channel filter" channel
                    , platformFilter = Debug.log "platform filter" platform
                    , versionFilter = Debug.log "version filter" version
                }

            _ ->
                { model | route = MainView }
