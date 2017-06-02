module Types
    exposing
        ( pageSize
        , Build
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


pageSize =
    10


type alias Model =
    { buildsPager : Kinto.Pager BuildRecord
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
    , channelList : List String
    , platformList : List String
    , versionList : List String
    , localeList : List String
    }


type alias BuildRecord =
    { id : String
    , last_modified : Int
    , build : Maybe Build
    , download : Download
    , source : Source
    , systemAddons : List SystemAddon
    , target : Target
    }


type alias Build =
    { date : String
    , id : String
    }


type alias Download =
    { mimetype : String
    , size : Int
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
    , tree : Maybe String
    , revision : Maybe String
    , repository : Maybe String
    }


type alias SystemAddon =
    { id : String
    , builtin : String
    , updated : String
    }


type alias Target =
    { version : String
    , platform : String
    , channel : String
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
    = BuildRecordsFetched (Result Kinto.Error (Kinto.Pager BuildRecord))
    | LoadNextPage
    | BuildRecordsNextPageFetched (Result Kinto.Error (Kinto.Pager BuildRecord))
    | UpdateFilter NewFilter
    | UrlChange Location
