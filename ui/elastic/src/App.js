import React, { Component } from "react";
import "./App.css";

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
  "https://kinto-ota.dev.mozaws.net/v1/buckets/build-hub/collections/releasesv2/",
  { searchUrlPath: "search" }
);

function HitItem(toggleExpand, expandedEntry) {
  return ({result: { _source: { build, download, source, target }, _id }}) => {
    const revisionUrl = source.revision
      ? <a href={`${source.repository}/rev/${source.revision}`}>
          {source.revision.substring(0, 6)}
        </a>
      : "";
    const filename = download.url.split("/").reverse()[0];
    const clickHandler = (event, data) =>
      toggleExpand(event, data, _id);

    return (
      <div key={_id} id={_id} className="panel">
        <div className="panel-heading" onClick={clickHandler}>
          <strong>
            <a href={`#${_id}`}>
              {source.product} {target.version} ({target.platform} | {target.channel} | {target.locale})
            </a>
          </strong>
          <span>{build && build.date}</span>
          <em>{build && build.id} (<span className="revision-url">{revisionUrl}</span>)</em>
        </div>
        <div
          className="panel-body"
          style={(expandedEntry === _id) ? {display: "block"} : {display: "none"}}>

          <table className="table table-condensed">
            <tbody>
              <tr>
                <th>Tree</th>
                <td>{source.tree}</td>
                <th>URL</th>
                <td><a href={download.url}>{filename}</a></td>
              </tr>
              <tr>
                <th>Size</th>
                <td>{download.size}</td>
                <th>Published on</th>
                <td>{download.date}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    )
  };
};

class App extends Component {
  constructor(props) {
    super(props);
    this.state = {
      expandedEntry: null,
    };
  }

  toggleExpand = (event, data, id) => {
    if (this.state.expandedEntry === id) {
      this.setState({ expandedEntry: null });
    } else {
      this.setState({ expandedEntry: id });
    }
  };

  render() {
    return (
      <div className="App">
        <SearchkitProvider searchkit={searchkit}>
          <Layout>

            <TopBar>
              <SearchBox
                autofocus={true}
                searchOnChange={true}
                placeholder="Search a build ID, eg: 201706*"
                queryFields={["build.id"]}
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
                  itemComponent={HitItem(
                    this.toggleExpand,
                    this.state.expandedEntry
                  )}
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
