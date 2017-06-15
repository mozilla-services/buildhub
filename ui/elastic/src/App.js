import React, { Component } from 'react';
import './App.css';

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
  Layout, TopBar, LayoutBody, LayoutResults,
  ActionBar, ActionBarRow, SideBar
} from "searchkit"

const searchkit = new SearchkitManager("https://kinto-ota.dev.mozaws.net/v1/buckets/build-hub/collections/releasesv2/", {searchUrlPath: "search"})


const HitsTable = (toggleExpand, expandedEntry) => {
  const tableStyle = {width: "100%", boxSizing: 'border-box'};
  return ({hits}) => {
    return (
      <div style={{width: '100%', boxSizing: 'border-box', padding: 8}}>
        <table className="sk-table sk-table-striped" style={tableStyle}>
          <thead>
            <tr>
              <th>Product</th>
              <th>Version</th>
              <th>Platform</th>
              <th>Channel</th>
              <th>Locale</th>
              <th>Published on</th>
            </tr>
          </thead>
          <tbody>
            {hits.map(hit => {
              const revisionUrl = (hit._source.source.revision)
                ? (<a href={(hit._source.source.repository + '/rev/' + hit._source.source.revision)}>{hit._source.source.revision}</a>)
                : "";
              const filename = hit._source.download.url.split("/").reverse()[0];
              const clickHandler = (event, data) => toggleExpand(event, data, hit._id);
              if (expandedEntry === hit._id) {
                return (
                  <tr key={hit._id} onClick={clickHandler}>
                    <td colSpan="6">
                      <table className="sk-table sk-table-striped" style={tableStyle}>
                        <thead>
                          <tr>
                            <th>Product</th>
                            <th>Tree</th>
                            <th>Revision</th>
                          </tr>
                        </thead>
                        <tbody>
                          <tr>
                            <td>{hit._source.source.product}</td>
                            <td>{hit._source.source.tree}</td>
                            <td>{revisionUrl}</td>
                          </tr>
                        </tbody>
                      </table>

                      <h4>Target</h4>
                      <table className="sk-table sk-table-striped" style={tableStyle}>
                        <thead>
                          <tr>
                            <th>Version</th>
                            <th>Platform</th>
                            <th>Channel</th>
                            <th>Locale</th>
                          </tr>
                        </thead>
                        <tbody>
                          <tr>
                            <td>{hit._source.target.version}</td>
                            <td>{hit._source.target.platform}</td>
                            <td>{hit._source.target.channel}</td>
                            <td>{hit._source.target.locale}</td>
                          </tr>
                        </tbody>
                      </table>

                      <h4>Download</h4>
                      <table className="sk-table sk-table-striped" style={tableStyle}>
                        <thead>
                          <tr>
                            <th>URL</th>
                            <th>Mimetype</th>
                            <th>Size</th>
                            <th>Published on</th>
                          </tr>
                        </thead>
                        <tbody>
                          <tr>
                            <td><a href={hit._source.download.url}>{filename}</a></td>
                            <td>{hit._source.download.mimetype}</td>
                            <td>{hit._source.download.size}</td>
                            <td>{hit._source.download.date}</td>
                          </tr>
                        </tbody>
                      </table>

                      <h4>Build</h4>
                      <table className="sk-table sk-table-striped" style={tableStyle}>
                        <thead>
                          <tr>
                            <th>id</th>
                            <th>Date</th>
                          </tr>
                        </thead>
                        <tbody>
                          <tr>
                            <td>{hit._source.build && hit._source.build.id}</td>
                            <td>{hit._source.build && hit._source.build.date}</td>
                          </tr>
                        </tbody>
                      </table>

                    </td>
                  </tr>
                )
              } else {
                return (
                  <tr key={hit._id} onClick={clickHandler}>
                    <td>{hit._source.source.product}</td>
                    <td>{hit._source.target.version}</td>
                    <td>{hit._source.target.platform}</td>
                    <td>{hit._source.target.channel}</td>
                    <td>{hit._source.target.locale}</td>
                    <td>{hit._source.download.date}</td>
                  </tr>
                )
              }
            })}
          </tbody>
        </table>
      </div>
    );
  };
};


class App extends Component {
  constructor(props) {
    super(props);
    this.state = {
      expandedEntry: null
    };
  }

  toggleExpand(event, data, id) {
    if (this.state.expandedEntry === id) {
      this.setState({expandedEntry: null});
    } else {
      this.setState({expandedEntry: id});
    }
  }

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
              queryFields={["build.id"]}/>
            </TopBar>

            <LayoutBody>
              <SideBar>
                <RefinementListFilter field="target.version"
                            title="Version"
                            id="versions"
                            size={1000}
                            operator="OR"
                            orderKey="_term"
                            orderDirection="desc"
                            listComponent={ItemCheckboxList}
                            translations={{"All":"All versions"}}/>
                <RefinementListFilter field="target.platform"
                            title="Platform"
                            id="platform"
                            size={1000}
                            operator="OR"
                            orderKey="_term"
                            listComponent={ItemCheckboxList}
                            translations={{"All":"All platforms"}}/>
                <RefinementListFilter field="target.channel"
                            title="Channel"
                            id="channel"
                            size={1000}
                            operator="OR"
                            orderKey="_term"
                            listComponent={ItemCheckboxList}
                            translations={{"All":"All channels"}}/>
                <RefinementListFilter field="target.locale"
                            title="Locale"
                            id="locale"
                            size={1000}
                            operator="OR"
                            orderKey="_term"
                            listComponent={ItemCheckboxList}
                            translations={{"All":"All locales"}}/>
              </SideBar>

              <LayoutResults>

                <ActionBar>
                  <ActionBarRow>
                    <HitsStats/>
                    <SortingSelector options={[
                      {label: "Published on", field:"download.date", order: "desc", defaultOption: true},
                      {label: "Build date", field:"build.date", order: "desc"}
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

                <Hits hitsPerPage={30} listComponent={HitsTable(this.toggleExpand.bind(this), this.state.expandedEntry)}/>
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
