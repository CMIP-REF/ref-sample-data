# CMIP Rapid Evaluation Framework Sample Data


<!--- --8<-- [start:description] -->

**Status**: This project is in active development. We expect to be ready for beta releases in Q2 2025.

The [CMIP Rapid Evaluation Framework](https://github.com/CMIP-REF/cmip-ref) is a Python application
that provides the ability to rapidly process and evaluate CMIP data against a set of reference data.
This repository contains a set of sample data that can be used to test the REF.

CMIP REF is a community project, and we welcome contributions from anyone.

## Getting started

The sample data is stored in the `data` directory.
The data is stored in a directory structure that mirrors the structure of the data on the ESGF,
but each file contains only a subset of the data.
The `registry.txt` file contains a list of the datasets that are included in the sample data and their hashes.
These data are fetched by the REF's test suite to ensure a consistent collection of input datasets are used for testing.

The data that are tracked and the decimation process is described in: [scripts/fetch_test_data.py]()


### Regenerating the sample data

The binary content of the generated sample data may vary by platform and various other dependencies.
In order to ensure that the hashes are consistent across platforms,
the hashes are generated on the CI and stored in the `registry.txt` file.
These hashes are verified as part of the CI pipeline to ensure that the data is consistent.

If the hashes in the `registry.txt` file are out of date,
you can regenerate the sample data by adding a comment to an open Pull Request with the text `/regenerate`.
This will trigger a [GitHub Actions workflow](https://github.com/CMIP-REF/ref-sample-data/actions/workflows/pr-comment.yaml)
that will regenerate the sample data and update the `registry.txt` file.
Be sure to pull the new commit if you need to add any additional changes to your pull request.
