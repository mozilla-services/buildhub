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

const HitItem = (toggleExpand, expandedEntry) => {
  return ({result: { _source: { build, download, source, target }, _id }}) => {
    const revisionUrl = source.revision
      ? <a href={`${source.repository}/rev/${source.revision}`}>
          {source.revision}
        </a>
      : "";
    const filename = download.url.split("/").reverse()[0];
    const clickHandler = (event, data) =>
      toggleExpand(event, data, _id);

    return (
      <div key={_id} id={_id} className="panel">
        <div className="panel-heading" onClick={clickHandler}>
          <strong><a href={`#${_id}`}>{source.product} {target.version}</a></strong>
          <span>{download.date}</span>
          <em>{build && build.id}</em>
        </div>
        <div
          className="panel-body"
          style={(expandedEntry === _id) ? {display: "block"} : {display: "none"}}>

          <table>
            <thead>
              <tr>
                <th>Product</th>
                <th>Target</th>
                <th>Download</th>
                <th>Build</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>
                  Product: {source.product}<br/>
                  Tree: {source.tree}<br/>
                  Revision: {revisionUrl}
                </td>

                <td>
                  Version: {target.version}<br/>
                  Platform: {target.platform}<br/>
                  Channel: {target.channel}<br/>
                  Locale: {target.locale}
                </td>

                <td>
                  URL: <a href={download.url}>{filename}</a><br/>
                  Mimetype: {download.mimetype}<br/>
                  Size: {download.size}<br/>
                  Published on: {download.date}
                </td>

                <td>
                  ID: {build && build.id}<br/>
                  Date: {build && build.date}
                </td>
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
