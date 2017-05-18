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
                        , map BuildIdView (s "builds" </> (s "buildId" </> string))
                        ]
                    )
                    location
    in
        case route of
            Just DocsView ->
                { model | route = DocsView }

            Just (BuildIdView buildId) ->
                { model | route = BuildIdView buildId, buildIdFilter = Debug.log "id filter" buildId }

            _ ->
                { model | route = MainView }
