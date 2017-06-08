module ElasticSearch exposing (..)

import Http
import Json.Decode as Decode
import Json.Encode as Encode
import Types exposing (..)


filterToJsonProperty : String -> Maybe String
filterToJsonProperty filter =
    if filter == "product" then
        Just "source.product"
    else if filter == "channel" then
        Just "target.channel"
    else if filter == "locale" then
        Just "target.locale"
    else if filter == "version" then
        Just "target.version"
    else if filter == "platform" then
        Just "target.platform"
    else
        Nothing


encodeMustClause : Filters -> Encode.Value
encodeMustClause { product, channel, locale, version, platform, buildId } =
    let
        encodeFilter ( name, value ) =
            Encode.object
                [ ( if name == "build.id" then
                        "prefix"
                    else
                        "match"
                  , Encode.object [ ( name, Encode.string value ) ]
                  )
                ]

        refineFilters ( k, v ) acc =
            if k == "buildId" && v /= "" then
                ( "build.id", v ) :: acc
            else
                case filterToJsonProperty k of
                    Just property ->
                        if v /= "all" then
                            ( property, v ) :: acc
                        else
                            acc

                    Nothing ->
                        acc
    in
        [ ( "buildId", buildId )
        , ( "product", product )
        , ( "channel", channel )
        , ( "locale", locale )
        , ( "version", version )
        , ( "platform", platform )
        ]
            |> List.foldr refineFilters []
            |> List.map encodeFilter
            |> Encode.list


encodeQuery : Filters -> Encode.Value
encodeQuery filters =
    let
        encodeFacet name property =
            ( name
            , Encode.object
                [ ( "terms"
                  , Encode.object
                        [ ( "field", Encode.string property )
                        , ( "size", Encode.int 1000 )
                        ]
                  )
                ]
            )
    in
        Encode.object
            [ ( "size", Encode.int 0 )
            , ( "query"
              , Encode.object
                    [ ( "bool"
                      , Encode.object
                            [ ( "must", encodeMustClause filters ) ]
                      )
                    ]
              )
            , ( "aggregations"
              , Encode.object
                    [ encodeFacet "product_filters" "source.product"
                    , encodeFacet "channel_filters" "target.channel"
                    , encodeFacet "platform_filters" "target.platform"
                    , encodeFacet "version_filters" "target.version"
                    , encodeFacet "locale_filters" "target.locale"
                    ]
              )
            ]


decodeFacet : Decode.Decoder Facet
decodeFacet =
    Decode.map2 Facet
        (Decode.field "doc_count" Decode.int)
        (Decode.field "key" Decode.string)


decodeResponse : Decode.Decoder Facets
decodeResponse =
    let
        decodeFilter name =
            Decode.list decodeFacet
                |> Decode.at [ "aggregations", name, "buckets" ]
    in
        Decode.map6 Facets
            (Decode.at [ "hits", "total" ] Decode.int)
            (decodeFilter "product_filters")
            (decodeFilter "version_filters")
            (decodeFilter "channel_filters")
            (decodeFilter "platform_filters")
            (decodeFilter "locale_filters")


getFilters : String -> Filters -> Http.Request Facets
getFilters endpoint filters =
    Http.post endpoint (Http.jsonBody (encodeQuery filters)) decodeResponse
