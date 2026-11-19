<!-- Title: <type>(<scope>): <description>, which becomes the commit message when squashed. -->

<!-- A promotion from dev to main lists "Closes #<issue>" instead, once for every issue it carries: GitHub closes issues
only from pull requests into main, and an issue is done once its change is on main. -->
Issue: #

## Changes

## Checks

- [ ] The checks for every area touched pass (`make go-check`, `make py-check`, `make docs-check`, `make ir-check`)
- [ ] A contract change (the IR schema and corpus, `proto/`) changes both sides and adds conformance cases
