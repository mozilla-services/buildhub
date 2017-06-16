module ElasticSearch exposing (..)

import Http
import Decoder exposing (buildRecordDecoder)
import Json.Decode as Decode
import Json.Encode as Encode
import Types exposing (..)


type alias Clauses =
    ( List MustClause, List ShouldClause )


type ClauseKind
    = Match
    | Prefix


type alias MustClause =
    Encode.Value


type alias ShouldClause =
    Encode.Value


clauseName : ClauseKind -> String
clauseName kind =
    case kind of
        Prefix ->
            "prefix"

        _ ->
            "match"


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

        values ->
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


encodeFilters : Filters -> Encode.Value
encodeFilters { product, channel, locale, version, platform, buildId } =
    Encode.object
        [ ( "must"
          , [ extractClauses Match "source.product" product
            , extractClauses Match "target.channel" channel
            , extractClauses Match "target.version" version
            , extractClauses Match "target.locale" locale
            , extractClauses Match "target.platform" platform
            , extractClauses Prefix "build.id" [ buildId ]
            ]
                |> List.filterMap identity
                |> Encode.list
          )
        ]


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
            , ( "sort", Encode.list [ Encode.object [ ( "download.date", Encode.string "desc" ) ] ] )
            , ( "post_filter", Encode.object [ ( "bool", encodeFilters filters ) ] )
            , ( "aggs"
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
