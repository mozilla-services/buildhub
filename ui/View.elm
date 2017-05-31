module View exposing (view)

import Dict
import Html exposing (..)
import Html.Attributes exposing (..)
import Html.Events exposing (..)
import Json.Decode as Decode
import Snippet exposing (snippets)
import Types exposing (..)
import Filesize exposing (formatWith, defaultSettings, Units(..))


format : Int -> String
format =
    formatWith { defaultSettings | units = Base2 }


view : Model -> Html Msg
view model =
    div [ class "container" ]
        [ headerView model
        , case model.route of
            DocsView ->
                docsView model

            _ ->
                mainView model
        ]


mainView : Model -> Html Msg
mainView model =
    if model.loading then
        spinner
    else
        div [ class "row" ]
            [ div [ class "col-sm-9" ]
                [ numBuilds model
                , div [] <| List.map recordView model.filteredBuilds
                ]
            , div [ class "col-sm-3" ]
                [ div [ class "panel panel-default" ]
                    [ div [ class "panel-heading" ] [ strong [] [ text "Filters" ] ]
                    , div [ class "panel-body" ]
                        [ buildIdSearchForm model
                        , filterSelector model.filterValues.productList "Products" model.productFilter (UpdateFilter << NewProductFilter)
                        , filterSelector model.filterValues.versionList "Versions" model.versionFilter (UpdateFilter << NewVersionFilter)
                        , filterSelector model.filterValues.platformList "Platforms" model.platformFilter (UpdateFilter << NewPlatformFilter)
                        , filterSelector model.filterValues.channelList "Channels" model.channelFilter (UpdateFilter << NewChannelFilter)
                        , filterSelector model.filterValues.localeList "Locales" model.localeFilter (UpdateFilter << NewLocaleFilter)
                        , p [ class "text-right" ]
                            [ button
                                [ class "btn btn-default", type_ "button", onClick (UpdateFilter ClearAll) ]
                                [ text "Clear all filters" ]
                            ]
                        ]
                    ]
                ]
            ]


snippetView : Snippet -> Html Msg
snippetView { title, description, snippets } =
    div [ class "panel panel-default" ]
        [ div [ class "panel-heading" ] [ text title ]
        , div [ class "panel-body" ]
            [ p [] [ text description ]
            , h4 [] [ text "cURL" ]
            , pre [] [ text snippets.curl ]
            , h4 [] [ text "JavaScript" ]
            , pre [] [ text snippets.js ]
            , h4 [] [ text "Python" ]
            , pre [] [ text snippets.python ]
            ]
        ]


docsView : Model -> Html Msg
docsView model =
    div []
        [ h2 [] [ text "About this project" ]
        , p []
            [ text "The BuildHub API is powered by "
            , a [ href "https://www.kinto-storage.org/" ] [ text "Kinto" ]
            , text "."
            ]
        , h2 [] [ text "Snippets" ]
        , p [] [ text "Here are a few useful snippets to browse or query the API, leveraging different Kinto clients." ]
        , div [] <| List.map snippetView snippets
        , h3 [] [ text "More information" ]
        , ul []
            [ li [] [ a [ href "http://kinto.readthedocs.io/en/stable/api/1.x/filtering.html" ] [ text "Filtering docs" ] ]
            , li [] [ a [ href "http://kinto.readthedocs.io/en/stable/api/1.x/" ] [ text "Full API reference" ] ]
            , li [] [ a [ href "https://github.com/Kinto/kinto-http.js" ] [ text "kinto-http.js (JavaScript)" ] ]
            , li [] [ a [ href "https://github.com/Kinto/kinto-http.py" ] [ text "kinto-http.py (Python)" ] ]
            , li [] [ a [ href "https://github.com/Kinto/kinto-http.rs" ] [ text "kinto-http.rs (Rust)" ] ]
            , li [] [ a [ href "https://github.com/Kinto/elm-kinto" ] [ text "elm-kinto (Elm)" ] ]
            , li [] [ a [ href "https://github.com/Kinto" ] [ text "Github organization" ] ]
            , li [] [ a [ href "https://github.com/Kinto/kinto" ] [ text "Kinto Server" ] ]
            ]
        , h3 [] [ text "Interested? Come talk to us!" ]
        , ul []
            [ li [] [ text "storage-team@mozilla.com" ]
            , li [] [ text "irc.freenode.net#kinto" ]
            ]
        ]


headerView : Model -> Html Msg
headerView model =
    nav
        [ class "navbar navbar-default" ]
        [ div
            [ class "container-fluid" ]
            [ div
                [ class "navbar-header" ]
                [ a [ class "navbar-brand", href "#" ] [ text "BuildHub" ] ]
            , div
                [ class "collapse navbar-collapse" ]
                [ ul
                    [ class "nav navbar-nav navbar-right" ]
                    [ li [] [ a [ href "#/builds" ] [ text "Builds" ] ]
                    , li []
                        [ a [ href "#/docs" ]
                            [ i [ class "glyphicon glyphicon-question-sign" ] []
                            , text " Docs"
                            ]
                        ]
                    ]
                ]
            ]
        ]


numBuilds : Model -> Html Msg
numBuilds model =
    let
        nbBuilds =
            List.length model.filteredBuilds
    in
        p [ class "well" ] <|
            [ text <|
                (toString nbBuilds)
                    ++ " build"
                    ++ (if nbBuilds == 1 then
                            ""
                        else
                            "s"
                       )
                    ++ " found. "
            ]


buildIdSearchForm : Model -> Html Msg
buildIdSearchForm model =
    div [ class "form-group" ]
        [ label [] [ text "Build id" ]
        , input
            [ type_ "text"
            , class "form-control"
            , placeholder "Eg. 201705011233"
            , value model.buildIdFilter
            , onInput <| UpdateFilter << NewBuildIdSearch
            ]
            []
        ]


filterSelector : List String -> String -> String -> (String -> Msg) -> Html Msg
filterSelector filters filterTitle selectedFilter updateHandler =
    let
        optionView value_ =
            option [ value value_, selected (value_ == selectedFilter) ] [ text value_ ]

        selectView =
            select
                [ class "form-control"
                , onInput updateHandler
                , value selectedFilter
                ]
                (List.map optionView ("all" :: filters))

        selectedFilterView =
            div [ class "input-group" ]
                [ input [ class "form-control", type_ "text", value selectedFilter, disabled True ] []
                , span
                    [ class "input-group-btn" ]
                    [ button
                        [ class "btn btn-default"
                        , type_ "button"
                        , onClick_ <| updateHandler "all"
                        ]
                        [ text "x" ]
                    ]
                ]
    in
        div [ class "form-group", style [ ( "display", "block" ) ] ]
            [ label [] [ text filterTitle ]
            , if selectedFilter == "all" then
                selectView
              else
                selectedFilterView
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
                                ++ record.target.version
                        ]
                    ]
                , em [ class "col-sm-6 text-right" ]
                    [ case record.build of
                        Just build ->
                            text build.date

                        Nothing ->
                            text "Unknown"
                    ]
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


viewBuildDetails : Maybe Build -> Html Msg
viewBuildDetails build =
    case build of
        Just build ->
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

        Nothing ->
            text ""


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
                    , td [] [ text <| download.mimetype ]
                      -- TODO display the size in an humanly readable format
                    , td [] [ text <| format download.size ]
                    ]
                ]
            ]


treeToMozillaHgUrl : Maybe String -> Maybe String
treeToMozillaHgUrl tree =
    case tree of
        Just tree ->
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

        Nothing ->
            Nothing


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
                    , td [] [ text <| Maybe.withDefault "unknown" source.tree ]
                    , td [] [ revisionUrl ]
                    ]
                ]
            ]


viewSystemAddonsDetails : List SystemAddon -> Html Msg
viewSystemAddonsDetails systemAddons =
    table [ class "table table-stripped table-condensed" ]
        [ thead []
            [ tr []
                [ th [] [ text "Id" ]
                , th [] [ text "Builtin version" ]
                , th [] [ text "Updated version" ]
                ]
            ]
        , tbody []
            (systemAddons
                |> List.map
                    (\systemAddon ->
                        tr []
                            [ td [] [ text systemAddon.id ]
                            , td [] [ text systemAddon.builtin ]
                            , td [] [ text systemAddon.updated ]
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
                [ td [] [ text <| target.version ]
                , td [] [ text target.platform ]
                , td [] [ text <| target.channel ]
                , td [] [ text target.locale ]
                ]
            ]
        ]


spinner : Html Msg
spinner =
    div [ class "loader-wrapper" ] [ div [ class "loader" ] [] ]


onClick_ : msg -> Attribute msg
onClick_ msg =
    onWithOptions
        "click"
        { preventDefault = True, stopPropagation = True }
        (Decode.succeed msg)
