Changelog
=========

This document describes changes between each past release.

0.5.0 (unreleased)
------------------

- Fix handling of bad server response, like XML (fixes #259)
- Fix Mac OS X metadata URLs (fixes #261)
- Fix Mac and Windows metadata URLs from installers (fixes #269)
- Fix beta and devedition medata URLs (#269)
- Skip exe installers where version is missing from URL (fixes #263)
- Fix Fennec metadata location (fixes #264)


0.4.1 (2017-09-29)
------------------

- Fix S3 event ``eventTime`` key error (fixes #253)


0.4.0 (2017-09-14)
------------------

- Allow number of requests in batch to be overriden via environment variable ``BATCH_MAX_REQUESTS``.
- Allow to run some commands from the container (fixes #41)

0.3.0 (2017-09-06)
------------------

- Load ``initialization.yml`` from the S3 inventory lambda (#236)
- Distinguish records cache files from a server to another (#235)
- Major documentation improvements (#228)

0.2.0 (2017-08-25)
------------------

- Add devedition to supported products. (#218)
- Document S3 inventories lambda configuration. (#217)
- Increase Gzip chunk size (#221)
- Fix S3 manifest key (#220)
- Add more build metadata (#219)
- Fix Gzip decompressor (#225 / #227)
- Skip WinCE and WinMo (#226)
- Handle eabi-arm platform (#230)


0.1.0 (2017-08-18)
------------------

**Initial version**

- Read build information from S3 inventories and https://archives.mozilla.org
- Lambda function to listen to S3 event
- Lambda function to populate kinto from the S3 inventories.
