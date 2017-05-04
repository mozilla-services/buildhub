module Main exposing (..)

import Html exposing (..)
import Model exposing (..)
import Set
import Types exposing (..)
import View exposing (..)


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
    case msg of
        BuildRecordsFetched (Ok buildRecordList) ->
            let
                _ =
                    buildRecordList
                        |> List.map .source
                        |> List.map .tree
                        |> Set.fromList
                        |> Debug.log "trees"
            in
                { model | builds = buildRecordList, loading = False } ! []

        BuildRecordsFetched (Err err) ->
            let
                _ =
                    Debug.log "An error occured while fetching the build records" err
            in
                model ! []
