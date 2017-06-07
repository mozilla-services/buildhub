module ElasticSearch exposing (..)

import Http
import Json.Decode as Decode
import Json.Encode as Encode
import Types exposing (..)


filterToJsonProperty : String -> String
filterToJsonProperty filter =
    if filter == "product" then
        "source.product"
    else if filter == "channel" then
        "target.channel"
    else if filter == "locale" then
        "target.locale"
    else if filter == "version" then
        "target.version"
    else
        "target.platform"


mustClause : Filters -> List ( String, String )
mustClause { product, channel, locale, version, platform } =
    [ ( "product", product )
    , ( "channel", channel )
    , ( "locale", locale )
    , ( "version", version )
    , ( "platform", platform )
    ]
        |> List.filter (\( k, v ) -> v /= "all")
        |> List.map (\( k, v ) -> ( filterToJsonProperty k, v ))


encodeQuery : Filters -> Encode.Value
encodeQuery filters =
    let
        encodeFilter ( name, value ) =
            Encode.object
                [ ( "match"
                  , Encode.object [ ( name, Encode.string value ) ]
                  )
                ]

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
                            [ ( "must"
                              , mustClause filters
                                    |> List.map encodeFilter
                                    |> Encode.list
                              )
                            ]
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
        Decode.map5 Facets
            (decodeFilter "product_filters")
            (decodeFilter "version_filters")
            (decodeFilter "channel_filters")
            (decodeFilter "platform_filters")
            (decodeFilter "locale_filters")


getFilters : String -> Filters -> Http.Request Facets
getFilters endpoint filters =
    Http.post endpoint (Http.jsonBody (encodeQuery filters)) decodeResponse
