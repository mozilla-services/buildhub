# buildhub

This *experimental* project aims to provide a public database of comprehensive information about
releases and builds.

This repository has two main folders:

* [ui/](https://github.com/mozilla-services/buildhub/tree/master/ui#readme): A Web UI to browse the available data
* [jobs/](https://github.com/mozilla-services/buildhub/tree/master/jobs#readme): A set of jobs in charge of aggregating and keeping the data up-to-date.

![](overview.png)

Currently we use [Kinto](http://kinto-storage.org) as a generic database service. It allows us to leverage its simple API for storing and querying records. It also comes with a set of client libraries for JavaScript, Python etc.

> More specific solutions may replace it when the product scope evolves.

* [Automatic Update Service (AUS, a.k.a Balrog)](https://wiki.mozilla.org/Balrog)

## Licence

Apache 2
