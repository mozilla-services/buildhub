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
        |> required "systemaddons" (nullable (list systemAddonDecoder))
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
        |> required "mimetype" string
        |> required "size" int
        |> required "url" string


targetDecoder : Decoder Target
targetDecoder =
    decode Target
        |> required "version" string
        |> required "platform" string
        |> required "channel" (nullable string)
        |> required "locale" string


sourceDecoder : Decoder Source
sourceDecoder =
    decode Source
        |> required "product" string
        |> required "tree" string
        |> required "revision" string


systemAddonDecoder : Decoder SystemAddon
systemAddonDecoder =
    decode SystemAddon
        |> required "id" string
        |> required "builtin_version" (nullable string)
        |> required "updated_version" (nullable string)
