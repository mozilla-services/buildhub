module View exposing (view)

import Dict
import Html exposing (..)
import Html.Attributes exposing (..)
import Types exposing (..)


view : Model -> Html Msg
view model =
    div [ class "container" ]
        [ div [ class "header" ]
            [ h1 [] [ Html.text "Build Hub" ] ]
        , div [ class "row" ] <|
            if model.loading then
                [ spinner ]
            else
                [ div [ class "col-sm-9" ]
                    [ div [] <| List.map recordView model.builds ]
                , div [ class "col-sm-3" ]
                    [ text "some filters here, someday" ]
                ]
        ]


recordView : BuildRecord -> Html Msg
recordView record =
    div
        [ class "panel panel-default", Html.Attributes.id record.id ]
        [ div [ class "panel-heading" ]
            [ div [ class "row" ]
                [ strong [ class "col-sm-6" ]
                    [ a [ href <| "./#" ++ record.id ]
                        [ text <|
                            record.source.product
                                ++ " "
                                ++ Maybe.withDefault "" record.target.version
                        ]
                    ]
                , em [ class "col-sm-6 text-right" ] [ text record.build.date ]
                ]
            ]
        , div [ class "panel-body" ]
            [ h4 [] [ text "Build" ]
            , viewBuildDetails record.build
            , h4 [] [ text "Download" ]
            , viewDownloadDetails record.download
            , h4 [] [ text "Source" ]
            , viewSourceDetails record.source
            , h4 [] [ text "System Addons" ]
            , viewSystemAddonsDetails record.systemAddons
            , h4 [] [ text "Target" ]
            , viewTargetDetails record.target
            ]
        ]


viewBuildDetails : Build -> Html Msg
viewBuildDetails build =
    table [ class "table table-stripped table-condensed" ]
        [ thead []
            [ tr []
                [ th [] [ text "Id" ]
                , th [] [ text "Type" ]
                , th [] [ text "Date" ]
                ]
            ]
        , tbody []
            [ tr []
                [ td [] [ text build.id ]
                , td [] [ text build.type_ ]
                , td [] [ text build.date ]
                ]
            ]
        ]


viewDownloadDetails : Download -> Html Msg
viewDownloadDetails download =
    let
        filename =
            String.split "/" download.url
                |> List.reverse
                |> List.head
                |> Maybe.withDefault ""
    in
        table [ class "table table-stripped table-condensed" ]
            [ thead []
                [ tr []
                    [ th [] [ text "URL" ]
                    , th [] [ text "Mimetype" ]
                    , th [] [ text "Size" ]
                    ]
                ]
            , tbody []
                [ tr []
                    [ td [] [ a [ href download.url ] [ text filename ] ]
                    , td [] [ text <| Maybe.withDefault "" download.mimetype ]
                      -- TODO display the size in an humanly readable format
                    , td [] [ text <| toString <| Maybe.withDefault 0 download.size ]
                    ]
                ]
            ]


treeToMozillaHgUrl : String -> Maybe String
treeToMozillaHgUrl tree =
    let
        mappingTable =
            Dict.fromList
                [ ( "comm-aurora", "releases/comm-aurora" )
                , ( "comm-beta", "releases/comm-beta" )
                , ( "comm-central", "comm-central" )
                , ( "comm-esr45", "releases/comm-esr45" )
                , ( "comm-esr52", "releases/comm-esr52" )
                , ( "graphics", "projects/graphics" )
                , ( "mozilla-aurora", "releases/mozilla-aurora" )
                , ( "mozilla-beta", "releases/mozilla-beta" )
                , ( "mozilla-central", "mozilla-central" )
                , ( "mozilla-esr45", "releases/mozilla-esr45" )
                , ( "mozilla-esr52", "releases/mozilla-esr45" )
                , ( "mozilla-release", "releases/mozilla-release" )
                , ( "oak", "projects/oak" )
                , ( "try-comm-central", "try-comm-central" )
                ]
    in
        Maybe.map
            (\folder ->
                "https://hg.mozilla.org/" ++ folder ++ "/rev/"
            )
            (Dict.get tree mappingTable)


viewSourceDetails : Source -> Html Msg
viewSourceDetails source =
    let
        revisionUrl =
            case source.revision of
                Just revision ->
                    let
                        mozillaHgUrl =
                            treeToMozillaHgUrl source.tree
                    in
                        case mozillaHgUrl of
                            Just url ->
                                a [ href <| url ++ revision ] [ text revision ]

                            Nothing ->
                                text ""

                Nothing ->
                    text ""
    in
        table [ class "table table-stripped table-condensed" ]
            [ thead []
                [ tr []
                    [ th [] [ text "Product" ]
                    , th [] [ text "Tree" ]
                    , th [] [ text "Revision" ]
                    ]
                ]
            , tbody []
                [ tr []
                    [ td [] [ text source.product ]
                    , td [] [ text source.tree ]
                    , td [] [ revisionUrl ]
                    ]
                ]
            ]


viewSystemAddonsDetails : Maybe (List SystemAddon) -> Html Msg
viewSystemAddonsDetails systemAddons =
    let
        systemAddonsList =
            Maybe.withDefault [] systemAddons
    in
        table [ class "table table-stripped table-condensed" ]
            [ thead []
                [ tr []
                    [ th [] [ text "Id" ]
                    , th [] [ text "Builtin version" ]
                    , th [] [ text "Updated version" ]
                    ]
                ]
            , tbody []
                (systemAddonsList
                    |> List.map
                        (\systemAddon ->
                            tr []
                                [ td [] [ text systemAddon.id ]
                                , td [] [ text <| Maybe.withDefault "" systemAddon.builtinVersion ]
                                , td [] [ text <| Maybe.withDefault "" systemAddon.updatedVersion ]
                                ]
                        )
                )
            ]


viewTargetDetails : Target -> Html Msg
viewTargetDetails target =
    table [ class "table table-stripped table-condensed" ]
        [ thead []
            [ tr []
                [ th [] [ text "Version" ]
                , th [] [ text "Platform" ]
                , th [] [ text "Channel" ]
                , th [] [ text "Locale" ]
                ]
            ]
        , tbody []
            [ tr []
                [ td [] [ text <| Maybe.withDefault "" target.version ]
                , td [] [ text target.platform ]
                , td [] [ text <| Maybe.withDefault "" target.channel ]
                , td [] [ text target.locale ]
                ]
            ]
        ]


spinner : Html Msg
spinner =
    div [ class "loader-wrapper" ] [ div [ class "loader" ] [] ]
