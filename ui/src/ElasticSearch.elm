module ElasticSearch exposing (..)

import Http
import Decoder exposing (buildRecordDecoder)
import Json.Decode as Decode
import Json.Encode as Encode
import Types exposing (..)


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
            if k == "build.id" then
                if v /= "" then
                    ( "build.id", v ) :: acc
                else
                    acc
            else if v /= "all" then
                ( k, v ) :: acc
            else
                acc
    in
        [ ( "build.id", buildId )
        , ( "source.product", product )
        , ( "target.channel", channel )
        , ( "target.locale", locale )
        , ( "target.version", version )
        , ( "target.platform", platform )
        ]
            |> List.foldr refineFilters []
            |> List.map encodeFilter
            |> Encode.list


encodeQuery : Filters -> Int -> Encode.Value
encodeQuery filters pageSize =
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
            , ( "from", Encode.int <| (filters.page - 1) * pageSize )
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
                    [ encodeFacet "products" "source.product"
                    , encodeFacet "channels" "target.channel"
                    , encodeFacet "platforms" "target.platform"
                    , encodeFacet "versions" "target.version"
                    , encodeFacet "locales" "target.locale"
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
            (decodeFilter "products")
            (decodeFilter "versions")
            (decodeFilter "channels")
            (decodeFilter "platforms")
            (decodeFilter "locales")


getFacets : Filters -> Int -> Http.Request Facets
getFacets filters size =
    let
        endpoint =
            "https://kinto-ota.dev.mozaws.net/v1/buckets/build-hub/collections/releases/search"
    in
        Http.post endpoint (Http.jsonBody (encodeQuery filters size)) decodeResponse


processFacets : Facets -> Facets
processFacets ({ versions } as facets) =
    let
        toVersionParts { value, count } =
            value
                |> String.split "."
                |> (\parts ->
                        case parts of
                            major :: _ ->
                                ( Result.withDefault 0 <| String.toInt major, Facet count value )

                            _ ->
                                ( 0, Facet count value )
                   )

        orderedVersions =
            versions
                |> List.map toVersionParts
                |> List.sortBy (\( major, _ ) -> major)
                |> List.map (\( _, facet ) -> facet)
                |> List.reverse
    in
        { facets | versions = orderedVersions }
