import React, { Component } from "react";
import "./App.css";
import filesize from "filesize";

import {
  SearchBox,
  NoHits,
  Hits,
  HitsStats,
  ItemCheckboxList,
  SortingSelector,
  SelectedFilters,
  MenuFilter,
  Pagination,
  RefinementListFilter,
  ResetFilters,
  SearchkitManager,
  SearchkitProvider,
  Tabs,
} from "searchkit";

import {
  Layout,
  TopBar,
  LayoutBody,
  LayoutResults,
  ActionBar,
  ActionBarRow,
  SideBar,
} from "searchkit";

const searchkit = new SearchkitManager(
  "https://kinto-ota.dev.mozaws.net/v1/buckets/build-hub/collections/releases/",
  { searchUrlPath: "search" }
);

const HitsTable = ({ hits }) => {
  return (
    <div style={{ width: "100%", boxSizing: "border-box", padding: 8 }}>
      <table className="sk-table sk-table-striped" style={{ width: "100%", boxSizing: "border-box" }}>
        <thead>
          <tr>
            <th></th>
            <th>Product</th>
            <th>Version</th>
            <th>platform</th>
            <th>channel</th>
            <th>locale</th>
            <th>Tree</th>
            <th>Size</th>
            <th>Published on</th>
            <th>Build ID</th>
            <th>Revision</th>
          </tr>
        </thead>
        <tbody>
          {hits.map(
            ({ _source: { build, download, source, target }, _id, highlight }) => {
              const revisionUrl = source.revision
                ? <a href={`${source.repository}/rev/${source.revision}`}>
                    {source.revision.substring(0, 6)}
                  </a>
                : "";
              const getHighlight = (title, value) => {return {__html: ((highlight && highlight[title]) || value)}}
              return (
                <tr key={_id} id={_id}>
                  <td><a href={`#${_id}`}>#</a></td>
                  <td dangerouslySetInnerHTML={getHighlight("source.product", source.product)}/>
                  <td><a href={download.url} dangerouslySetInnerHTML={getHighlight("target.version", target.version)}/></td>
                  <td dangerouslySetInnerHTML={getHighlight("target.platform", target.platform)}/>
                  <td dangerouslySetInnerHTML={getHighlight("target.channel", target.channel)}/>
                  <td dangerouslySetInnerHTML={getHighlight("target.locale", target.locale)}/>
                  <td>{source.tree}</td>
                  <td>{filesize(download.size)}</td>
                  <td title={download.date}><time dateTime={download.date}>{new Date(download.date).toLocaleDateString()}</time></td>
                  <td dangerouslySetInnerHTML={getHighlight("build.id", build && build.id)}/>
                  <td>{revisionUrl}</td>
                </tr>
              );
            }
          )
          }
        </tbody>
      </table>
    </div>
  );
};


const sortVersions = (filters) => {
  return filters.sort((a, b) => {
    const majorA = parseInt(a.key.split(".", 1)[0], 10)
    const majorB = parseInt(b.key.split(".", 1)[0], 10)
    return majorB - majorA
  })
}

const fullText = (query, options) => {
  if(!query){
    return
  }
  const fulltextQuery = query.split(" ").map((term) => {return `${term}*`}).join(" ");
  return {
    "query_string": Object.assign({query: fulltextQuery}, options)
  }
}

class App extends Component {
  render() {
    return (
      <div className="App">
        <SearchkitProvider searchkit={searchkit}>
          <Layout>

            <TopBar>
              <SearchBox
                autofocus={true}
                searchOnChange={true}
                placeholder="firefox 54 linux"
                queryBuilder={fullText}
                queryOptions={{
                          analyzer: "standard",
                          default_operator: "AND",
                          phrase_slop: 1 ,
                          auto_generate_phrase_queries: true,
                          analyze_wildcard: true,
                          lenient: true,
                          split_on_whitespace: true
                }}
                queryFields={["source.product",
                              "target.channel^1.2",
                              "target.version^10",
                              "target.locale^3",
                              "target.platform^2",
                              "build.id"]}
              />
            </TopBar>

            <LayoutBody>
              <SideBar>
                <RefinementListFilter
                  field="target.version"
                  title="Version"
                  id="versions"
                  size={1000}
                  operator="OR"
                  orderKey="_term"
                  orderDirection="desc"
                  listComponent={ItemCheckboxList}
                  bucketsTransform={sortVersions}
                  translations={{ All: "All versions" }}
                />
                <RefinementListFilter
                  field="target.platform"
                  title="Platform"
                  id="platform"
                  size={1000}
                  operator="OR"
                  orderKey="_term"
                  listComponent={ItemCheckboxList}
                  translations={{ All: "All platforms" }}
                />
                <RefinementListFilter
                  field="target.channel"
                  title="Channel"
                  id="channel"
                  size={1000}
                  operator="OR"
                  orderKey="_term"
                  listComponent={ItemCheckboxList}
                  translations={{ All: "All channels" }}
                />
                <RefinementListFilter
                  field="target.locale"
                  title="Locale"
                  id="locale"
                  size={1000}
                  operator="OR"
                  orderKey="_term"
                  listComponent={ItemCheckboxList}
                  translations={{ All: "All locales" }}
                />
              </SideBar>

              <LayoutResults>

                <ActionBar>
                  <ActionBarRow>
                    <HitsStats />
                    <SortingSelector
                      options={[
                        {
                          label: "Published on",
                          field: "download.date",
                          order: "desc",
                          defaultOption: true,
                        },
                        {
                          label: "Build date",
                          field: "build.date",
                          order: "desc",
                        },
                      ]}
                    />
                  </ActionBarRow>

                  <ActionBarRow>
                    <SelectedFilters />
                    <ResetFilters />
                  </ActionBarRow>

                  <MenuFilter
                    field="source.product"
                    title="Product"
                    id="products"
                    listComponent={Tabs}
                    translations={{ All: "All products" }}
                  />
                </ActionBar>

                <Hits
                  hitsPerPage={30}
                  listComponent={HitsTable}
                  highlightFields={[
                    "source.product",
                    "target.channel",
                    "target.version",
                    "target.locale",
                    "target.platform",
                    "build.id"
                  ]}
                />
                <NoHits
                  translations={{
                    "NoHits.NoResultsFound":
                      "No release found were found for {query}",
                    "NoHits.DidYouMean": "Search for {suggestion}",
                    "NoHits.SearchWithoutFilters":
                      "Search for {query} without filters",
                  }}
                  suggestionsField="target.version"
                />

                <Pagination showNumbers={true} />

              </LayoutResults>
            </LayoutBody>
          </Layout>
        </SearchkitProvider>
      </div>
    );
  }
}

export default App;
