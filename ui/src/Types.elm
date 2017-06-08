module Types exposing (..)

import Http
import Navigation exposing (..)


type alias Model =
    { filters : Filters
    , filterValues : FilterValues
    , facets : Maybe Facets
    , page : Int
    , loading : Bool
    , route : Route
    , error : Maybe String
    , settings : Settings
    }


type alias Facet =
    { count : Int, value : String }


type alias Facets =
    { hits : List BuildRecord
    , total : Int
    , product_filters : List Facet
    , version_filters : List Facet
    , channel_filters : List Facet
    , platform_filters : List Facet
    , locale_filters : List Facet
    }


type alias Settings =
    { pageSize : Int }


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
    | FilteredView Product Channel Platform Version Locale BuildId
    | DocsView


type Msg
    = FacetsReceived (Result Http.Error Facets)
    | LoadNextPage
    | LoadPreviousPage
    | UpdateFilter NewFilter
    | UrlChange Location
    | DismissError
    | NewPageSize String
