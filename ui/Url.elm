module Url exposing (parsePage)

import Navigation exposing (..)
import Types exposing (..)


parsePage : Location -> CurrentView
parsePage location =
    if location.hash == "#/docs" then
        DocsView
    else
        MainView
