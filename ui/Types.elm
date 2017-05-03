module Types
    exposing
        ( Build
        , BuildRecord
        , Download
        , Model
        , Msg(..)
        , Source
        , SystemAddon
        , Target
        )


type alias Model =
    { builds : List BuildRecord }


type alias BuildRecord =
    { id : String
    , last_modified : Int
    , build : Build
    , download : Download
    , source : Source
    , systemaddons : Maybe (List SystemAddon)
    , target : Target
    }


type alias Build =
    { date : String
    , id : String
    , type_ : String
    }


type alias Download =
    { mimetype : String
    , size : Int
    , url : String
    }


type alias Source =
    { product : String
    , tree : String
    , revision : String
    }


type alias SystemAddon =
    { id : String
    , builtin_version : Maybe String
    , updated_version : Maybe String
    }


type alias Target =
    { version : String
    , platform : String
    , channel : Maybe String
    , locale : String
    }


type Msg
    = NoOp
