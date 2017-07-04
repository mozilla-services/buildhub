module View exposing (view)

import Filesize
import Html exposing (..)
import Html.Attributes exposing (..)
import Html.Events exposing (..)
import Snippet exposing (snippets)
import Types exposing (..)
import Url exposing (..)


view : Model -> Html Msg
view model =
    div [ class "container-fluid" ]
        [ headerView model
        , case model.route of
            DocsView ->
                docsView model

            _ ->
                mainView model
        ]


highlighSearchTerm : String -> List String -> String -> Html Msg
highlighSearchTerm search terms fieldValue =
    let
        fullTerms =
            search
                |> String.split " "
                |> List.filter (not << String.isEmpty)
                |> List.append terms
    in
        if List.member fieldValue fullTerms then
            span [ class "highlight" ] [ text fieldValue ]
        else
            text fieldValue


clearableTextInput : msg -> List (Attribute msg) -> String -> Html msg
clearableTextInput onClearMsg attrs txt =
    div [ class "btn-group clearable-text" ]
        [ input attrs []
        , if String.length txt > 0 then
            span
                [ class "text-clear-btn"
                , onClick onClearMsg
                ]
                [ i [ class "glyphicon glyphicon-remove" ] [] ]
          else
            text ""
        ]


searchForm : Filters -> Html Msg
searchForm filters =
    Html.form [ class "search-form well", onSubmit SubmitSearch ]
        [ clearableTextInput
            (UpdateFilter ClearSearch)
            [ type_ "search"
            , class "form-control"
            , placeholder "Search builds, eg. \"firefox 54 linux\""
            , value filters.search
            , onInput <| UpdateFilter << NewSearch
            ]
            filters.search
        ]


mainView : Model -> Html Msg
mainView { settings, error, facets, filters } =
    div [ class "row" ]
        [ div [ class "col-sm-9" ]
            [ errorView error
            , searchForm filters
            , case facets of
                Just facets ->
                    div []
                        [ paginationView facets settings.pageSize filters.page
                        , table [ class "table table-stripped table-hover" ]
                            [ thead []
                                [ tr []
                                    [ th [ style [ ( "width", "10px" ) ] ] []
                                    , th [ style [ ( "width", "10px" ) ] ] []
                                    , th [] [ text "Product" ]
                                    , th [] [ text "Version" ]
                                    , th [] [ text "Channel" ]
                                    , th [] [ text "Tree" ]
                                    , th [] [ text "Platform" ]
                                    , th [] [ text "Locale" ]
                                    , th [] [ text "Build id" ]
                                    , th [] [ text "Date" ]
                                    , th [] [ text "Revision" ]
                                    , th [] [ text "Download" ]
                                    ]
                                ]
                            , tbody [] <| List.map (recordView filters) facets.hits
                            ]
                        , if List.length facets.hits > 0 then
                            paginationView facets settings.pageSize filters.page
                          else
                            text ""
                        ]

                Nothing ->
                    spinner
            ]
        , div [ class "col-sm-3" ]
            [ case facets of
                Just facets ->
                    filtersView facets filters

                Nothing ->
                    text ""
            , settingsView settings
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


errorView : Maybe String -> Html Msg
errorView err =
    case err of
        Just err ->
            div [ class "panel panel-warning" ]
                [ div [ class "panel-heading" ]
                    [ h3 [ class "panel-title" ]
                        [ text "An error occured while fetching builds"
                        , button [ type_ "button", class "close", onClick DismissError ]
                            [ span [ class "glyphicon glyphicon-remove" ] []
                            ]
                        ]
                    ]
                , div [ class "panel-body" ]
                    [ text err ]
                ]

        _ ->
            text ""


paginationView : Facets -> Int -> Int -> Html Msg
paginationView { total, hits } pageSize page =
    let
        nbBuilds =
            List.length hits

        index =
            (page - 1) * pageSize

        ( chunkStart, chunkStop ) =
            ( index + 1, index + nbBuilds )
    in
        div [ class "well" ]
            [ div [ class "row" ]
                [ p [ class "col-sm-6" ] <|
                    [ text <|
                        if nbBuilds == 0 then
                            "No results were found matching your query."
                        else
                            "Build result"
                                ++ (if nbBuilds == 1 then
                                        ""
                                    else
                                        "s"
                                   )
                                ++ " "
                                ++ (toString chunkStart)
                                ++ ".."
                                ++ (toString chunkStop)
                                ++ " of "
                                ++ toString total
                                ++ "."
                    ]
                , if nbBuilds > 0 then
                    div [ class "col-sm-6 text-right" ]
                        [ div [ class "btn-group" ]
                            [ if page /= 1 then
                                button
                                    [ class "btn btn-default", onClick LoadPreviousPage ]
                                    [ text <| "« Page " ++ (toString (page - 1)) ]
                              else
                                text ""
                            , button [ class "btn btn-default active", disabled True ]
                                [ text <| "Page " ++ (toString page) ]
                            , if page /= ceiling ((toFloat total) / (toFloat pageSize)) then
                                button
                                    [ class "btn btn-default", onClick LoadNextPage ]
                                    [ text <| "Page " ++ (toString (page + 1)) ++ " »" ]
                              else
                                text ""
                            ]
                        ]
                  else
                    text ""
                ]
            ]


buildPermalink : BuildRecord -> String
buildPermalink { build, source, target } =
    let
        buildInfo =
            Maybe.withDefault (Build "" "") build
    in
        { product = [ source.product ]
        , version = [ target.version ]
        , platform = [ target.platform ]
        , channel = [ target.channel ]
        , locale = [ target.locale ]
        , buildId = buildInfo.id
        , search = ""
        , page = 1
        }
            |> routeFromFilters
            |> urlFromRoute


recordView : Filters -> BuildRecord -> Html Msg
recordView filters ({ id, build, download, source, target, systemAddons } as record) =
    let
        filename =
            String.split "/" download.url
                |> List.reverse
                |> List.head
                |> Maybe.withDefault ""

        ( revision, revisionUrl ) =
            case ( source.repository, source.revision ) of
                ( Just repository, Just revision ) ->
                    ( revision, Just <| repository ++ "/rev/" ++ revision )

                _ ->
                    ( "unknown", Nothing )

        sourceTree =
            Maybe.withDefault "unknown" source.tree

        buildDate =
            case build of
                Just { date } ->
                    date

                Nothing ->
                    download.date
    in
        tr
            [ Html.Attributes.id id ]
            [ td []
                [ a
                    [ href <| buildPermalink record
                    , title "Build permalink"
                    ]
                    [ i [ class "glyphicon glyphicon-link" ] [] ]
                ]
            , td []
                [ a
                    [ href "#"
                    , title "View build details"
                    ]
                    [ i [ class "glyphicon glyphicon-eye-open" ] [] ]
                ]
            , td [ title source.product ]
                [ highlighSearchTerm filters.search filters.product source.product ]
            , td [ title target.version ]
                [ highlighSearchTerm filters.search filters.version target.version ]
            , td [ title target.channel ]
                [ highlighSearchTerm filters.search filters.channel target.channel ]
            , td [ title sourceTree ]
                [ highlighSearchTerm filters.search [] sourceTree ]
            , td [ title target.platform ]
                [ highlighSearchTerm filters.search filters.platform target.platform ]
            , td [ title target.locale ]
                [ highlighSearchTerm filters.search filters.locale target.locale ]
            , case build of
                Just { id } ->
                    td [ title id ]
                        [ highlighSearchTerm filters.search [ filters.buildId ] id ]

                Nothing ->
                    td [] [ text "unknown" ]
            , td [ title buildDate ] [ text buildDate ]
            , td [ title revision ]
                [ case revisionUrl of
                    Just url ->
                        a [ href url ] [ text revision ]

                    Nothing ->
                        text revision
                ]
            , td [ class "text-right" ]
                [ a
                    [ href download.url
                    , title <| filename ++ " (" ++ download.mimetype ++ ")"
                    ]
                    [ text <| Filesize.formatBase2 download.size
                    , text " "
                    , i [ class "glyphicon glyphicon-download" ] []
                    ]
                ]
            ]


viewSystemAddonsDetails : List SystemAddon -> Html Msg
viewSystemAddonsDetails systemAddons =
    case systemAddons of
        [] ->
            text ""

        _ ->
            div []
                [ h4 [] [ text "System Addons" ]
                , table [ class "table table-stripped table-condensed" ]
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
                ]


spinner : Html Msg
spinner =
    div [ class "loader" ] []


facetSelector :
    String
    -> Int
    -> List String
    -> (String -> Bool -> NewFilter)
    -> NewFilter
    -> List Facet
    -> Html Msg
facetSelector title total selectedValues filterMsg clearMsg facets =
    let
        choice entry =
            let
                active =
                    List.member entry.value selectedValues
            in
                div [ class "checkbox" ]
                    [ label []
                        [ input
                            [ type_ "checkbox"
                            , value entry.value
                            , checked active
                            , onCheck <| UpdateFilter << (filterMsg entry.value)
                            , disabled <| List.length facets == 1
                            ]
                            []
                        , span []
                            [ span [ class "filter-value" ] [ text entry.value ]
                            , span [ class "badge" ] [ text <| toString entry.count ]
                            ]
                        ]
                    ]
    in
        div [ class "form-group" ]
            [ p []
                [ strong [] [ text title ]
                , if List.length selectedValues > 0 then
                    button [ class "close", onClick <| UpdateFilter clearMsg ]
                        [ text "×" ]
                  else
                    text ""
                ]
            , div [ class "scrollable-choices" ] <| List.map choice facets
            ]


filtersView : Facets -> Filters -> Html Msg
filtersView facets filters =
    let
        { total, products, versions, platforms, channels, locales } =
            facets

        { buildId, product, version, platform, channel, locale } =
            filters
    in
        div [ class "panel panel-default" ]
            [ div [ class "panel-heading" ] [ strong [] [ text "Filters" ] ]
            , div [ class "panel-body" ]
                [ div []
                    [ facetSelector "Products" total product NewProductFilter ClearProducts products
                    , facetSelector "Versions" total version NewVersionFilter ClearVersions versions
                    , facetSelector "Platforms" total platform NewPlatformFilter ClearPlatforms platforms
                    , facetSelector "Channels" total channel NewChannelFilter ClearChannels channels
                    , facetSelector "Locales" total locale NewLocaleFilter ClearLocales locales
                    , div [ class "btn-group btn-group-justified" ]
                        [ div [ class "btn-group" ]
                            [ button
                                [ class "btn btn-default", type_ "button", onClick (UpdateFilter ClearAll) ]
                                [ text "Reset all filters" ]
                            ]
                        ]
                    ]
                ]
            ]


settingsView : Settings -> Html Msg
settingsView { pageSize } =
    div [ class "panel panel-default" ]
        [ div [ class "panel-heading" ] [ strong [] [ text "Settings" ] ]
        , Html.form [ class "panel-body" ]
            [ let
                optionView value_ =
                    option [ value value_, selected (value_ == toString pageSize) ] [ text value_ ]
              in
                div [ class "form-group", style [ ( "display", "block" ) ] ]
                    [ label [] [ text "number of records per page" ]
                    , select
                        [ class "form-control"
                        , onInput NewPageSize
                        , value <| toString pageSize
                        ]
                        (List.map optionView [ "10", "20", "50", "100" ])
                    ]
            ]
        ]
