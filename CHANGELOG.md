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
