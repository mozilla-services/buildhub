module ElasticSearch exposing (..)

import Http
import Decoder exposing (buildRecordDecoder)
import Json.Decode as Decode
import Json.Encode as Encode
import Types exposing (..)


type ClauseKind
    = Match
    | Prefix
    | Term


clauseName : ClauseKind -> String
clauseName kind =
    case kind of
        Prefix ->
            "prefix"

        Match ->
            "match"

        _ ->
            "term"


encodeClause : ClauseKind -> String -> String -> Encode.Value
encodeClause kind name value =
    Encode.object
        [ ( clauseName kind
          , Encode.object [ ( name, Encode.string value ) ]
          )
        ]


extractClauses : ClauseKind -> String -> List String -> Maybe Encode.Value
extractClauses kind field values =
    case values of
        [] ->
            Nothing

        [ "" ] ->
            Nothing

        [ value ] ->
            -- Only this value
            Just <|
                Encode.object
                    [ ( "bool"
                      , Encode.object
                            [ ( "must", encodeClause kind field value ) ]
                      )
                    ]

        values ->
            -- Any of those values
            Just <|
                Encode.object
                    [ ( "bool"
                      , Encode.object
                            [ ( "should"
                              , values
                                    |> List.map (encodeClause kind field)
                                    |> Encode.list
                              )
                            ]
                      )
                    ]


encodeAggregate : String -> List (Maybe Encode.Value) -> ( String, Encode.Value )
encodeAggregate field clauses =
    ( field
    , Encode.object
        [ ( "filter", encodeFilter clauses )
        , ( "aggs"
          , Encode.object
                [ ( field ++ "_agg"
                  , Encode.object
                        [ ( "terms"
                          , Encode.object
                                [ ( "field", Encode.string field )
                                , ( "size", Encode.int 1000 )
                                ]
                          )
                        ]
                  )
                ]
          )
        ]
    )


encodeFilter : List (Maybe Encode.Value) -> Encode.Value
encodeFilter clauses =
    Encode.object
        [ ( "bool"
          , Encode.object
                [ ( "must"
                  , clauses
                        |> List.filterMap identity
                        |> Encode.list
                  )
                ]
          )
        ]


encodeQuery : Filters -> Int -> Encode.Value
encodeQuery { page, product, channel, locale, version, platform, buildId } pageSize =
    let
        productClauses =
            extractClauses Term "source.product" product

        channelClauses =
            extractClauses Term "target.channel" channel

        versionClauses =
            extractClauses Term "target.version" version

        localeClauses =
            extractClauses Term "target.locale" locale

        platformClauses =
            extractClauses Term "target.platform" platform

        buildIdClauses =
            extractClauses Prefix "build.id" [ buildId ]
    in
        Encode.object
            [ ( "size", Encode.int pageSize )
            , ( "from", Encode.int <| (page - 1) * pageSize )
            , ( "sort", Encode.list [ Encode.object [ ( "download.date", Encode.string "desc" ) ] ] )
            , ( "post_filter"
              , encodeFilter
                    [ productClauses
                    , channelClauses
                    , versionClauses
                    , localeClauses
                    , platformClauses
                    , buildIdClauses
                    ]
              )
            , ( "aggs"
              , Encode.object
                    [ encodeAggregate "source.product"
                        [ channelClauses
                        , versionClauses
                        , localeClauses
                        , platformClauses
                        , buildIdClauses
                        ]
                    , encodeAggregate "target.channel"
                        [ productClauses
                        , versionClauses
                        , localeClauses
                        , platformClauses
                        , buildIdClauses
                        ]
                    , encodeAggregate "target.platform"
                        [ productClauses
                        , channelClauses
                        , versionClauses
                        , localeClauses
                        , buildIdClauses
                        ]
                    , encodeAggregate "target.version"
                        [ productClauses
                        , channelClauses
                        , localeClauses
                        , platformClauses
                        , buildIdClauses
                        ]
                    , encodeAggregate "target.locale"
                        [ productClauses
                        , channelClauses
                        , versionClauses
                        , platformClauses
                        , buildIdClauses
                        ]
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
                |> Decode.at [ "aggregations", name, name ++ "_agg", "buckets" ]
    in
        Decode.map7 Facets
            (Decode.at [ "hits", "hits" ] (Decode.list decodeBuildRecordHit))
            (Decode.at [ "hits", "total" ] Decode.int)
            (decodeFilter "source.product")
            (decodeFilter "target.version")
            (decodeFilter "target.channel")
            (decodeFilter "target.platform")
            (decodeFilter "target.locale")


getFacets : Filters -> Int -> Http.Request Facets
getFacets filters size =
    let
        endpoint =
            "https://kinto-ota.dev.mozaws.net/v1/buckets/build-hub/collections/releasesv2/search"
    in
        Http.post endpoint (Http.jsonBody (encodeQuery filters size)) decodeResponse


orderVersions : List Facet -> List Facet
orderVersions versions =
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
    in
        versions
            |> List.map toVersionParts
            |> List.sortBy (\( major, _ ) -> major)
            |> List.map (\( _, facet ) -> facet)
            |> List.reverse


processFacets : Facets -> Facets
processFacets ({ versions, locales } as facets) =
    { facets
        | versions = orderVersions versions
        , locales = locales |> List.sortBy .value
    }
