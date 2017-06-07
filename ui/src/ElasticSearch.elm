module ElasticSearch exposing (..)

import Http
import Json.Decode as Decode
import Json.Encode as Encode
import Types exposing (..)


filterToJsonProperty : String -> Maybe String
filterToJsonProperty filter =
    case filter of
        "product" ->
            Just "source.product"

        "channel" ->
            Just "target.channel"

        "locale" ->
            Just "target.locale"

        "version" ->
            Just "target.version"

        "platform" ->
            Just "target.platform"

        _ ->
            Nothing


getFilterNames : Filters -> List String
getFilterNames { product, channel, locale, version, platform } =
    [ product, channel, locale, version, platform ]
        |> List.filter (\v -> v /= "all")


encodeQuery : Filters -> Encode.Value
encodeQuery filters =
    let
        encodeFilter filter =
            case filterToJsonProperty filter of
                Just property ->
                    [ Encode.object
                        [ ( "match"
                          , Encode.object [ ( property, Encode.string filter ) ]
                          )
                        ]
                    ]

                Nothing ->
                    []

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
                              , getFilterNames filters
                                    |> List.map encodeFilter
                                    |> List.concat
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
