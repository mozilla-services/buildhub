module ElasticSearch exposing (..)

import Http
import Decoder exposing (buildRecordDecoder)
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


encodeQuery : Filters -> Int -> Int -> Encode.Value
encodeQuery filters pageSize page =
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
            [ ( "size", Encode.int pageSize )
            , ( "from", Encode.int <| (page - 1) * pageSize )
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


decodeBuildRecordHit : Decode.Decoder BuildRecord
decodeBuildRecordHit =
    Decode.at [ "_source" ] buildRecordDecoder


decodeResponse : Decode.Decoder Facets
decodeResponse =
    let
        decodeFilter name =
            Decode.list decodeFacet
                |> Decode.at [ "aggregations", name, "buckets" ]
    in
        Decode.map7 Facets
            (Decode.at [ "hits", "hits" ] (Decode.list decodeBuildRecordHit))
            (Decode.at [ "hits", "total" ] Decode.int)
            (decodeFilter "product_filters")
            (decodeFilter "version_filters")
            (decodeFilter "channel_filters")
            (decodeFilter "platform_filters")
            (decodeFilter "locale_filters")


getFacets : String -> Filters -> Int -> Int -> Http.Request Facets
getFacets endpoint filters size page =
    Http.post endpoint (Http.jsonBody (encodeQuery filters size page)) decodeResponse
