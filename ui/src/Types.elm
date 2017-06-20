module Types exposing (..)

import Http
import Navigation exposing (..)


type alias Model =
    { filters : Filters
    , facets : Maybe Facets
    , route : Route
    , error : Maybe String
    , settings : Settings
    }


type alias Facet =
    { count : Int, value : String }


type alias Facets =
    { hits : List BuildRecord
    , total : Int
    , products : List Facet
    , versions : List Facet
    , channels : List Facet
    , platforms : List Facet
    , locales : List Facet
    }


type alias Settings =
    { pageSize : Int }


type alias Filters =
    { product : List String
    , version : List String
    , platform : List String
    , channel : List String
    , locale : List String
    , buildId : String
    , search : String
    , page : Int
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
    | ClearProducts
    | ClearVersions
    | ClearPlatforms
    | ClearChannels
    | ClearLocales
    | NewProductFilter String Bool
    | NewVersionFilter String Bool
    | NewPlatformFilter String Bool
    | NewChannelFilter String Bool
    | NewLocaleFilter String Bool
    | NewBuildIdSearch String
    | NewSearch String


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


type alias Search =
    String


type alias Page =
    Int


type Route
    = MainView
    | FilteredView Product Channel Platform Version Locale BuildId Search Page
    | DocsView


type Msg
    = FacetsReceived (Result Http.Error Facets)
    | LoadNextPage
    | LoadPreviousPage
    | UpdateFilter NewFilter
    | UrlChange Location
    | DismissError
    | NewPageSize String
    | SubmitSearch
