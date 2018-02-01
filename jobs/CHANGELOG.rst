Changelog
=========

This document describes changes between each past release.

1.1.3 (unreleased)
------------------

- Retry fetch JSON when status is not 200 (ref #327)

**Bug fixes**

- Fix ordering of release candidates build folders (fixes #328)


1.1.2 (2017-12-20)
------------------

- Fix event handling of RC metadata (fixes #314)
- Fix exclusion of thunderbird nightly releases (fixes #312)
- Prevent mozinfo JSON files to be mistaken as Nightly metadata (fixes #315)

1.1.1 (2017-11-30)
------------------

- Fix test_packages regexp to avoid confusion with build metadata (fixes #295, #309)

1.1.0 (2017-11-03)
------------------

- Changed log level from error to warning when metadata could not be found (#297, #298)
- Updated docs with prod URLs (#293)
- Added ElasticSearch queries examples (#294)

**Bug fixes**

- Use ``requirements.txt`` versions when building the container (fixes #299)
- Prevent test_packages metadata from being recognized as release metadata (fixes #295)


1.0.0 (2017-10-12)
------------------

- Add ability to configure cache folder via environment variable ``CACHE_FOLDER``
- Keep trace but skip build urls that have unsupported formats
- Fix support of some funnelcake archives (fixes #287)
- Skip very old RC release with parenthesis in filenames (fixes #288)


0.6.0 (2017-10-10)
------------------

- Add support for SNS events (#281)


0.5.0 (2017-10-10)
------------------

- Skip incomplete records ­- ie. without build id
- Fix Mac OS X metadata URLs (fixes #261)
- Fix Mac and Windows metadata URLs from installers (fixes #269)
- Fix beta and devedition medata URLs (#269)
- Skip exe installers where version is missing from URL (fixes #263)
- Fix Fennec metadata location (fixes #264)
- Fix caching when partial updates metadata is missing (fixes #276)
- Fix handling of bad server response, like XML (fixes #259)


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
