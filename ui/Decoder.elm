module Decoder exposing (..)

import Json.Decode exposing (..)
import Json.Decode.Pipeline exposing (..)
import Types exposing (..)


buildRecordDecoder : Decoder BuildRecord
buildRecordDecoder =
    decode BuildRecord
        |> required "id" string
        |> required "last_modified" int
        |> required "build" buildDecoder
        |> required "download" downloadDecoder
        |> required "source" sourceDecoder
        |> required "systemaddons" (maybe (list systemAddonDecoder))
        |> required "target" targetDecoder


buildDecoder : Decoder Build
buildDecoder =
    decode Build
        |> required "date" string
        |> required "id" string
        |> required "type" string


downloadDecoder : Decoder Download
downloadDecoder =
    decode Download
        |> required "mimetype" (maybe string)
        |> required "size" (maybe int)
        |> required "url" string


targetDecoder : Decoder Target
targetDecoder =
    decode Target
        |> required "version" (maybe string)
        |> required "platform" string
        |> required "channel" (maybe string)
        |> required "locale" string


sourceDecoder : Decoder Source
sourceDecoder =
    decode Source
        |> required "product" string
        |> required "tree" string
        |> required "revision" (maybe string)


systemAddonDecoder : Decoder SystemAddon
systemAddonDecoder =
    decode SystemAddon
        |> required "id" string
        |> required "builtin" (maybe string)
        |> required "updated" (maybe string)
