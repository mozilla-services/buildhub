module Types
    exposing
        ( Build
        , BuildRecord
        , Route(..)
        , Download
        , FilterValues
        , Model
        , Msg(..)
        , NewFilter(..)
        , Snippet
        , Source
        , SystemAddon
        , Target
        )

import Kinto
import Navigation exposing (..)


type alias Model =
    { builds : List BuildRecord
    , filteredBuilds : List BuildRecord
    , filterValues : FilterValues
    , productFilter : String
    , versionFilter : String
    , platformFilter : String
    , channelFilter : String
    , localeFilter : String
    , buildIdFilter : String
    , loading : Bool
    , route : Route
    }


type alias FilterValues =
    { productList : List String
    , versionList : List String
    , platformList : List String
    , channelList : List String
    , localeList : List String
    }


type alias BuildRecord =
    { id : String
    , last_modified : Int
    , build : Build
    , download : Download
    , source : Source
    , systemAddons : Maybe (List SystemAddon)
    , target : Target
    }


type alias Build =
    { date : String
    , id : String
    , type_ : String
    }


type alias Download =
    { mimetype : Maybe String
    , size : Maybe Int
    , url : String
    }


type alias Snippet =
    { title : String
    , description : String
    , snippets :
        { curl : String
        , js : String
        , python : String
        }
    }


type alias Source =
    { product : String
    , tree : String
    , revision : Maybe String
    }


type alias SystemAddon =
    { id : String
    , builtin : String
    , updated : String
    }


type alias Target =
    { version : Maybe String
    , platform : String
    , channel : Maybe String
    , locale : String
    }


type NewFilter
    = ClearAll
    | NewProductFilter String
    | NewVersionFilter String
    | NewPlatformFilter String
    | NewChannelFilter String
    | NewLocaleFilter String
    | NewBuildIdSearch String


type alias BuildId =
    String


type alias Product =
    String


type alias Channel =
    String


type alias Platform =
    String


type alias Version =
    String


type alias Locale =
    String


type Route
    = MainView
    | BuildIdView BuildId
    | ProductView Product
    | ChannelView Product Channel
    | PlatformView Product Channel Platform
    | VersionView Product Channel Platform Version
    | LocaleView Product Channel Platform Version Locale
    | DocsView


type Msg
    = BuildRecordsFetched (Result Kinto.Error (List BuildRecord))
    | UpdateFilter NewFilter
    | UrlChange Location
