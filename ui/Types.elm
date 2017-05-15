module Types
    exposing
        ( Build
        , BuildRecord
        , CurrentView(..)
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


type alias Model =
    { builds : List BuildRecord
    , filteredBuilds : List BuildRecord
    , filterValues : FilterValues
    , treeFilter : String
    , productFilter : String
    , versionFilter : String
    , platformFilter : String
    , channelFilter : String
    , localeFilter : String
    , buildIdFilter : String
    , loading : Bool
    , currentView : CurrentView
    }


type alias FilterValues =
    { treeList : List String
    , productList : List String
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
    | NewTreeFilter String
    | NewProductFilter String
    | NewVersionFilter String
    | NewPlatformFilter String
    | NewChannelFilter String
    | NewLocaleFilter String
    | NewBuildIdSearch String


type CurrentView
    = MainView
    | DocsView


type Msg
    = BuildRecordsFetched (Result Kinto.Error (List BuildRecord))
    | UpdateFilter NewFilter
    | ChangeView CurrentView
