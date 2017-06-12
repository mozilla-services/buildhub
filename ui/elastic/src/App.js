import React, { Component } from 'react';
import './App.css';

import {
    SearchBox,
    RefinementListFilter,
    NoHits,
    Hits,
    HitsStats,
    SearchkitComponent,
    ItemHistogramList,
    SortingSelector,
    SelectedFilters,
    MenuFilter,
    HierarchicalMenuFilter,
    Pagination,
    ResetFilters,
    Select,
    SearchkitManager,
    SearchkitProvider,
    Tabs,
    } from "searchkit";

import {
  Layout, TopBar, LayoutBody, LayoutResults,
  ActionBar, ActionBarRow, SideBar
} from "searchkit"

const searchkit = new SearchkitManager("https://kinto-ota.dev.mozaws.net/v1/buckets/build-hub/collections/releases/", {searchUrlPath: "search"})


const HitsTable = ({hits}) => {
  return (
    <div style={{width: '100%', boxSizing: 'border-box', padding: 8}}>
      <table className="sk-table sk-table-striped" style={{width: '100%', boxSizing: 'border-box'}}>
        <thead>
          <tr>
            <th>Product</th>
            <th>Version</th>
            <th>Locale</th>
            <th>Platform</th>
            <th>Revision</th>
            <th>Date</th>
          </tr>
        </thead>
        <tbody>
          {hits.map(hit => {
            const url = (hit._source.source.revision)
              ? (<a href={(hit._source.source.repository + '/rev/' + hit._source.source.revision)}>{hit._source.source.revision}</a>)
              : "";
            return (
              <tr key={hit._id}>
                <td>{hit._source.source.product}</td>
                <td>{hit._source.target.version}</td>
                <td>{hit._source.target.locale}</td>
                <td>{hit._source.target.platform}</td>
                <td>{url}</td>
                <td>{hit._source.download.date}</td>
              </tr>
          )})}
        </tbody>
      </table>
    </div>
  );
};


class App extends Component {
  render() {
    return (
      <div className="App">
        <SearchkitProvider searchkit={searchkit}>
          <Layout>

            <TopBar>
              <SearchBox/>
            </TopBar>

            <LayoutBody>
              <SideBar>
                <MenuFilter field="target.version"
                            title="Version"
                            id="versions"
                            listComponent={Select}
                            size={1000}
                            showMore={false}
                            translations={{"All":"All versions"}}/>
                <MenuFilter field="target.locale"
                            title="Locale"
                            id="locale"
                            listComponent={ItemHistogramList}
                            size={10}
                            translations={{"All":"All locales"}}/>
                <MenuFilter field="target.platform"
                            title="Platform"
                            id="platform"
                            size={10}
                            listComponent={ItemHistogramList}
                            translations={{"All":"All platforms"}}/>
              </SideBar>

              <LayoutResults>

                <ActionBar>
                  <ActionBarRow>
                    <HitsStats/>
                    <SortingSelector options={[
                      {label: "Relevance", field: "_score", order: "desc", defaultOption: true},
                      {label: "Latest Releases", field:"download.date", order: "desc"},
                    ]}/>
                  </ActionBarRow>

                  <ActionBarRow>
                    <SelectedFilters/>
                    <ResetFilters/>
                  </ActionBarRow>

                  <MenuFilter field="source.product"
                              title="Product"
                              id="products"
                              listComponent={Tabs}
                              translations={{"All":"All products"}}/>
                </ActionBar>

                <Hits hitsPerPage={30} listComponent={HitsTable}/>
                <NoHits translations={{
                  "NoHits.NoResultsFound":"No release found were found for {query}",
                  "NoHits.DidYouMean":"Search for {suggestion}",
                  "NoHits.SearchWithoutFilters":"Search for {query} without filters"}} suggestionsField="target.version"/>

                <Pagination showNumbers={true}/>

               </LayoutResults>
            </LayoutBody>
          </Layout>
        </SearchkitProvider>
      </div>
    );
  }
}

export default App;
