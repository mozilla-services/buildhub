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
                treeList =
                    buildRecordList
                        |> List.map .source
                        |> List.map .tree
                        |> Set.fromList
                        |> Debug.log "trees"

                productList =
                    buildRecordList
                        |> List.map .source
                        |> List.map .product
                        |> Set.fromList
                        |> Debug.log "products"

                versionList =
                    buildRecordList
                        |> List.map .target
                        |> List.map .version
                        |> List.filterMap identity
                        |> Set.fromList
                        |> Debug.log "versions"

                platformList =
                    buildRecordList
                        |> List.map .target
                        |> List.map .platform
                        |> Set.fromList
                        |> Debug.log "platforms"

                channelList =
                    buildRecordList
                        |> List.map .target
                        |> List.map .channel
                        |> List.filterMap identity
                        |> Set.fromList
                        |> Debug.log "channels"

                localeList =
                    buildRecordList
                        |> List.map .target
                        |> List.map .locale
                        |> Set.fromList
                        |> Debug.log "locales"
            in
                { model
                    | builds = buildRecordList
                    , treeList = Set.toList treeList
                    , productList = Set.toList productList
                    , versionList = Set.toList versionList
                    , platformList = Set.toList platformList
                    , channelList = Set.toList channelList
                    , localeList = Set.toList localeList
                    , loading = False
                }
                    ! []

        BuildRecordsFetched (Err err) ->
            let
                _ =
                    Debug.log "An error occured while fetching the build records" err
            in
                model ! []
