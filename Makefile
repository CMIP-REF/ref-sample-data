# Makefile to help automate key steps

.DEFAULT_GOAL := help
# Will likely fail on Windows, but Makefiles are in general not Windows
# compatible so we're not too worried
TEMP_FILE := $(shell mktemp)

# A helper script to get short descriptions of each target in the Makefile
define PRINT_HELP_PYSCRIPT
import re, sys

for line in sys.stdin:
	match = re.match(r'^([\$$\(\)a-zA-Z_-]+):.*?## (.*)$$', line)
	if match:
		target, help = match.groups()
		print("%-30s %s" % (target, help))
endef
export PRINT_HELP_PYSCRIPT


.PHONY: help
help:  ## print short description of each target
	@python3 -c "$$PRINT_HELP_PYSCRIPT" < $(MAKEFILE_LIST)

.PHONY: pre-commit
pre-commit:  ## run all the linting checks of the codebase
	uv run pre-commit run --all-files


.PHONY: ruff-fixes
ruff-fixes:  ## fix the code using ruff
	uv run ruff check --fix
	uv run ruff format

		-r a -v --doctest-modules --cov=packages/ref-metrics-esmvaltool/src

.PHONY: changelog-draft
changelog-draft:  ## compile a draft of the next changelog
	uv run towncrier build --draft --version v0.0.0

.PHONY: licence-check
licence-check:  ## Check that licences of the dependencies are suitable
	uv export --no-dev > $(TEMP_FILE)
	uv run liccheck -r $(TEMP_FILE) -R licence-check.txt
	rm -f $(TEMP_FILE)

.PHONY: virtual-environment
virtual-environment:  ## update virtual environment, create a new one if it doesn't already exist
	uv sync
	uv run pre-commit install

.PHONY: fetch-test-data
fetch-test-data:  ## Fetch test data
	rm -rf data
	uv run python ./scripts/fetch_test_data.py

registry.txt: data  ## Generate a registry of all the packages
	uv run python -c "import pooch; pooch.make_registry('data', 'registry.txt')"
