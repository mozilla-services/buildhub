Changelog
=========

1.3.0 (2018-05-03)
------------------

- optimize fetch_existing, fixes #447 #445 #446 (#448)

- in lambda, fetch_listing with retry_on_notfound, fixes #424 (#442)

- Use ciso8601 to parse CSV dates, fixes #443 (#444)

- Fix readthedocs fixes 438 (#440)

- add link to Datadog dashboard

- fix for bad check_output in script



1.2.1 (2018-04-27)
------------------

- fix for subprocess

- document all configurations (#436)

- Use cloudwatch metrics for lambda 433 (#435)

- use decouple for env vars to be able to read from .env

- more default NB_RETRY_REQUEST, fixes #425 (#432)

- Tests shouldn't depend on the network, fixes #429 (#430)

- Skip based on date earlier, fixes #427 (#428)

- Make release script (#422)



1.2.0 (2018-04-23)
------------------

- run fetch_existing only once, fixes #412 (#414)

- fix sorting in searchKit (#419)

- add psql makefile target (#418)

- docs typo (#416)

- upgrade pytest to 3.5.0 (#415)

- Ability to quiet markus, fixes 410 (#411)

- Dump file is growing unsustainably fixes 394 (#404)

- bail on 404 responses in cron job (#389)

- use python-decouple everywhere (#409)

- Disk cache the manifests, fixes #392 (#403)

- Optionally configure markus to log fixes 402 (#405)

- pluggy sha's changed since they added wheels (#408)

- Update markus to 1.1.2 (#398)

- do raven for lambda correctly, fixes #387 (#391)

- Update .pyup.yml (#393)

- add a .pyup.yml file (#390)

- Add statsd metrics (#388)

- 80 lines pep8 (#384)

- refactor script name, fixes #377 (#383)

- skip old csv entries, fixes #380 (#382)

- drop css-animation, fixes #371 (#376)

- Use dockerhub repo (#375)

- change license to mpl 2.0, fixes #366 (#374)

- remove leftover console warn (#373)

- upgrade Prettier, fixes #369 (#372)

- bundle searchkit css, fixes #368 (#370)

- use yarn instead, fixes #365 (#367)

- Feature: RefinementAutosuggest for perf (#304)

- DOCKER_* env var names correction (#364)

- circle only (#358)

- pin all requirements, fixes #353 (#356)


1.1.5 (2018-02-22)
------------------

**Bug fixes**

- Now pick Windows .exe archives only (fixes #338)


1.1.4 (2018-02-15)
------------------

**Bug fixes**

- Be more robust about skipping non-date folders when looking for
  manifests (ref https://bugzilla.mozilla.org/show_bug.cgi?id=1437931)
- Retry requests on ``409 Conflict``


1.1.3 (2018-02-02)
------------------

- Retry fetch JSON when status is not 200 (ref #327)

**Bug fixes**

- Fix ordering of release candidates build folders (fixes #328)

**UI**

- Use classic ISO format for publication date (fixes #320)
- Improve search placeholder (fixes #305)
- Better favicon (fixes #306)
- Add contribute.json endpoint (fixes #324)
- Add link to Kinto record (fixes #286)


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
