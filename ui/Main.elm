module Main exposing (..)

import Html exposing (..)
import Model exposing (..)
import Types exposing (..)


main : Program Never Model Msg
main =
    Html.program
        { init = init
        , view = view
        , update = update
        , subscriptions = always Sub.none
        }


update : Msg -> Model -> ( Model, Cmd Msg )
update msg model =
    model ! []


view : Model -> Html Msg
view model =
    div []
        [ h1 [] [ text "Buildhub" ]
        , p [] [ text "Let's there be rock" ]
        , ul [] <|
            List.map recordView model.builds
        ]


recordView : BuildRecord -> Html Msg
recordView build =
    li []
        [ p [] [ text build.id ]
        , div [] [ text <| toString build ]
        ]
