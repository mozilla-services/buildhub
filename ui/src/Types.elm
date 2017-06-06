module Types
    exposing
        ( pageSize
        , Build
        , BuildRecord
        , FilterRecord
        , Route(..)
        , Download
        , Filters
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


pageSize : Int
pageSize =
    10


type alias Model =
    { buildsPager : Kinto.Pager BuildRecord
    , filters : Filters
    , filterValues : FilterValues
    , loading : Bool
    , route : Route
    , error : Maybe Kinto.Error
    }


type alias Filters =
    { product : String
    , version : String
    , platform : String
    , channel : String
    , locale : String
    , buildId : String
    }


type alias FilterValues =
    { productList : List String
    , channelList : List String
    , platformList : List String
    , versionList : List String
    , localeList : List String
    }


type alias FilterRecord =
    { id : String, name : String }


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
    , date : String
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
    | ProductView Product
    | ChannelView Product Channel
    | PlatformView Product Channel Platform
    | VersionView Product Channel Platform Version
    | LocaleView Product Channel Platform Version Locale
    | BuildIdView Product Channel Platform Version Locale BuildId
    | DocsView


type Msg
    = BuildRecordsFetched (Result Kinto.Error (Kinto.Pager BuildRecord))
    | FiltersReceived String (Result Kinto.Error (Kinto.Pager FilterRecord))
    | LoadNextPage
    | BuildRecordsNextPageFetched (Result Kinto.Error (Kinto.Pager BuildRecord))
    | UpdateFilter NewFilter
    | UrlChange Location
    | SubmitFilters
    | DismissError
