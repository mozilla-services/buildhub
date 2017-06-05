module Decoder exposing (..)

import Json.Decode exposing (..)
import Json.Decode.Pipeline exposing (..)
import Types exposing (..)


buildRecordDecoder : Decoder BuildRecord
buildRecordDecoder =
    decode BuildRecord
        |> required "id" string
        |> required "last_modified" int
        |> optional "build" (nullable buildDecoder) Nothing
        |> required "download" downloadDecoder
        |> required "source" sourceDecoder
        |> optional "systemaddons" (list systemAddonDecoder) []
        |> required "target" targetDecoder


buildDecoder : Decoder Build
buildDecoder =
    decode Build
        |> required "date" string
        |> required "id" string


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
        |> required "channel" string
        |> required "locale" string


sourceDecoder : Decoder Source
sourceDecoder =
    decode Source
        |> required "product" string
        |> optional "tree" (nullable string) Nothing
        |> optional "revision" (nullable string) Nothing
        |> optional "repository" (nullable string) Nothing


systemAddonDecoder : Decoder SystemAddon
systemAddonDecoder =
    decode SystemAddon
        |> required "id" string
        |> optional "builtin" string ""
        |> optional "updated" string ""
