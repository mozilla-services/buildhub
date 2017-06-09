module Main exposing (..)

import Init exposing (init)
import Navigation exposing (..)
import Types exposing (..)
import Update exposing (update)
import View exposing (view)


main : Program Never Model Msg
main =
    Navigation.program
        UrlChange
        { init = init
        , view = view
        , update = update
        , subscriptions = always Sub.none
        }
