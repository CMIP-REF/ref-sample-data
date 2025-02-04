# Changelog

Versions follow [Semantic Versioning](https://semver.org/) (`<major>.<minor>.<patch>`).

Backward incompatible (breaking) changes will only be introduced in major versions
with advance notice in the **Deprecations** section of releases.

<!--
You should *NOT* be adding new changelog entries to this file,
this file is managed by towncrier.
See `changelog/README.md`.

You *may* edit previous changelogs to fix problems like typo corrections or such.
To add a new changelog entry, please see
`changelog/README.md`
and https://pip.pypa.io/en/latest/development/contributing/#news-entries,
noting that we use the `changelog` directory instead of news,
markdown instead of restructured text and use slightly different categories
from the examples given in that link.
-->

<!-- towncrier release notes start -->

## ref-sample-data 0.3.1 (2025-02-04)

### Features

- Added Obs4MIPs sample data to the fetching script. ([#11](https://github.com/CMIP-REF/ref-sample-data/pulls/11))
- Restructured code into classes so that additional sample datasets can be fetched easily in the future. ([#12](https://github.com/CMIP-REF/ref-sample-data/pulls/12))


## ref-sample-data 0.3.0 (2025-01-21)

### Breaking Changes

- Output files now contain a contiguous time dimension for a selected time span.

  The output files are no longer 6monthly samples of the results.
  This was not directly useful for metrics package developers.
  The output file names now contain the start and end date of the dataset
  instead of mimicking the original dataset. ([#5](https://github.com/CMIP-REF/ref-sample-data/pulls/5))

### Features

- Added the files required to run ESMValTool ECS and TCR metrics. ([#4](https://github.com/CMIP-REF/ref-sample-data/pulls/4))
- Added an action to regenerate the sample data in Pull Requests.

  A comment containing `/regenerate` will trigger the action. ([#7](https://github.com/CMIP-REF/ref-sample-data/pulls/7))

### Bug Fixes

- Migrates the source of truth for data generation to the server and documented the regeneration flow ([#8](https://github.com/CMIP-REF/ref-sample-data/pulls/8))


## ref-sample-data 0.2.1 (2025-01-10)

### Bug Fixes

- Fix the missing leading `v` in the version directory name ([#3](https://github.com/CMIP-REF/ref-sample-data/pulls/3))


## ref-sample-data 0.2.0 (2025-01-10)

### Breaking Changes

- Use the dataset version's from ESGF instead of the values in the netCDF files.
  Different files in the same dataset may contain different versions inside their netCDF files. ([#2](https://github.com/CMIP-REF/ref-sample-data/pulls/2))


## ref-sample-data 0.1.1 (2025-01-08)

### Bug Fixes

- Correct the location of the datasets within the repository ([#1](https://github.com/CMIP-REF/ref-sample-data/pulls/1))


## ref-sample-data 0.1.0 (2025-01-08)

Initial release of the CMIP Rapid Evaluation Framework Sample Data.
