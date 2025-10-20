# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased

### Added

- Support for Python 3.13
- Adds `--report=filename` to generate a test report
- Adds `--format=[json|yaml]` to specify the report format
- Points are reported in the test report and on the output
- CLI arguments can now be passed in the configuration file
- Adds pretty table summary using rich
- Points distribution mechanism
- Adds `baygon.yml` self-test so Baygon can validate itself with Baygon
- `Schema()` accepts YAML strings and file-like objects in addition to mappings
- Changelog is now published inside the MkDocs documentation
- Adds API documentation

### Changed

- Upgrade dependencies
- Migration to Poetry, Ruff and Black
- Adopted keepachangelog format
- Configuration validation now relies on Pydantic instead of Voluptuous for clearer errors
- YAML parsing errors raise `ConfigSyntaxError` with line and column details
- Documentation migrated from VuePress to MkDocs Material with refreshed navigation
- Migrate documentation from VuePress to MkDocs Material
- `--config` accepts both `-c` and legacy `-t` short flags; the summary table flag now maps to `-T`.

### Fixed

- Summary table now shows failed and skipped tests with the correct status labels.
- '4 failed, 0 passed (0.0%% ok).' remove the duplicated pecentage sign
- Fix output by adding quotes and `(empty)` for empty strings
- More tests (89% coverage), enabled doctests

### Deprecated

- Drop support for Python 3.6, 3.7 and 3.8

## 0.6.0 (2025-10-14)

### Changed

- Replace the short option for `--config` with `-c` so `-t` can be used for the summary table flag.

### Fixed

- Restore compatibility with Click 8.3 by using boolean defaults for flags and avoiding attribute access on integers.
- Ensure report files are written when the format is omitted by selecting a format based on the filename extension.
- Reapply suite-level filters to test output so configuration filters such as `ignorespaces` work again.
- Avoid passing positional arguments directly to the Click command when running `python -m baygon`.

## 0.5.1 (2022-11-08)

- Add tests for filters
- Fix filters args

## 0.5.0 (2022-11-10)

- Code Refactoring
- Migrate documentation from VuePress 1.x to 2.x
- Add new features
- Add optional `points` to config file to rank tests
- Add `--json` option to `baygon` command

## 0.2.1

- Use config.cfg
- Fix documentation (exit-status -> exit)

## 0.2.0

- Add negation `not` keyword
- PATH is resolved for binaries
