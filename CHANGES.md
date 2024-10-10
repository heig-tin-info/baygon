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

### Changed

- Upgrade dependencies
- Migration to Poetry, Ruff and Black
- Adopted keepachangelog format

### Fixed

- '4 failed, 0 passed (0.0%% ok).' remove the duplicated pecentage sign
- Fix output by adding quotes and `(empty)` for empty strings
- More tests (89% coverage), enabled doctests

### Deprecated

- Drop support for Python 3.6, 3.7 and 3.8

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
