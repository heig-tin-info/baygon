# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased

### Added

- `number` matcher: the output is a number equal to a value, with an optional `tolerance`, or within `min`/`max` (#27)
- `length` and `lines` matchers: number of characters or lines of the output, exact or within a range (#27)
- `stdin` can be the output of a generator program: `stdin: {executable, args}` (#30)
- `same-as` matcher: compare an output with the output of a reference program run with the same arguments and input (#30)
- `filters` can be set on a test or a group, as the documentation said
- A bare executable name such as `grep` is looked up in the `PATH` when it is not a file next to the configuration
- Documentation: matchers, expressions (`eval`), and a page of recipes to check the source code (#21)

### Changed

- Exit status failures read `Invalid exit status: expected 1, got 0.` instead of `1 != 0`

### Fixed

- `regex` and `replace` filters given in the configuration crashed the run
- Summary percentage without float noise (`14.29% ok`)
- Documentation examples that were invalid (YAML syntax, unknown `match` matcher, `stdin` used as a file name)

## 0.8.0 (2026-11-16)

### Added

- Support for Python 3.14 and 3.15
- `timeout` key (seconds) at suite, group and test level, and `--timeout` option: a program that hangs is killed, with the processes it started, and only its test fails (#47)
- `max-output` key (bytes, or sizes such as `64K`): a program that prints without end is killed once a stream goes over the limit. Output is capped at 16 MiB by default (#51)
- The report written by `--report` lists every test (`cases`) and a subtotal per group (`groups`); also available as `RunReport.as_dict()` (#51)
- `--only ID` and `-k/--keyword TEXT` run a subset of the tests; `SuiteContext.select()` and `baygon.core.select_tests()` do the same from Python (#51)
- `--strict` exits with status 1 when a test fails (#51)

### Changed

- Upgrade dependencies (typer up to 0.29, rich 15); `termynal` is now a docs-only dependency and the unused `eval-type-backport` dependency is dropped
- CI: up-to-date actions, Python 3.10 to 3.15 and macOS; a release now runs the whole CI before publishing to PyPI
- A group or a test can override an inherited `executable`; the nearest one wins (#51)
- Invalid configurations are reported as one line per error, without a traceback (#26)

### Fixed

- A failed negated matcher (`not: contains`) now says the output should not contain the value, instead of the opposite (#51)
- A boolean filter set to `false` (e.g. `uppercase: false`) is no longer applied
- Output that is not valid UTF-8 no longer stops the run; invalid bytes are replaced
- A program that cannot be started (e.g. a script without shebang) fails its test instead of stopping the run
- `Executable(path, encoding=...)` no longer raises a `TypeError`
- `eval` given as a mapping (`start`, `end`, `init`) no longer crashes on load (regression of 0.7.0), and `eval: false` no longer enables eval
- `eval` delimiters are literal text (`start: "[["` works) and `iter()` works inside nested calls such as `iter(int(5), 1)`
- `exit: true`/`exit: false` are read as 1 and 0 instead of crashing the run
- An empty expected output (`stdout: ""`, `equals: ""`) is accepted
- `min-points` must be greater than 0 (0 crashed the score computation)
- An invalid regex, a non-numeric `exit` or an eval error fails its test instead of stopping the run
- `--report report.yml` writes YAML (only `.yaml` was recognised)
- Point totals no longer show float noise (`0.30000000000000004`)
- Configuration errors point to the test case or group that is wrong, instead of both
- Documentation: the filters are applied in a fixed order; the program runs in the current directory
- Documentation: the filter is `ignorespaces` (`ignore-spaces` is an accepted alias) (#32)

## 0.7.0 (2026-03-02)

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
- Expose a programmatic runner via `baygon.runtime.BaygonRunner` and configuration helpers in `baygon.config`
- Provide public dataclasses in `baygon.core.models` to represent suites, groups and cases

### Changed

- Migration to Poetry, Ruff and Black
- Development tooling now relies on Nox sessions backed by uv groups instead of tox
- Contributor documentation now explains the uv-powered workflow for development and docs builds
- Adopted keepachangelog format
- Configuration validation now relies on Pydantic instead of Voluptuous for clearer errors
- YAML parsing errors raise `ConfigSyntaxError` with line and column details
- Documentation migrated from VuePress to MkDocs Material with refreshed navigation
- Migrate documentation from VuePress to MkDocs Material
- `--config` accepts both `-c` and legacy `-t` short flags; the summary table flag now maps to `-T`.
- CLI rendering now delegates to dedicated presentation modules and the core runtime service
- Filters and matchers rely on explicit registries instead of module introspection

### Fixed

- Summary table now shows failed and skipped tests with the correct status labels.
- '4 failed, 0 passed (0.0%% ok).' remove the duplicated pecentage sign
- Fix output by adding quotes and `(empty)` for empty strings
- Self-test now targets the repository binary and reports the resolved configuration path, so `uv run baygon $(which baygon)` succeeds again
- More tests (89% coverage), enabled doctests

### Deprecated

- Drop support for Python 3.6, 3.7 and 3.8
- The legacy object wrappers (`TestSuite`, `TestGroup`, `TestCase`) have been removed in favor of the service-based API (`SuiteLoader`, `SuiteExecutor`, `SuiteService`).
- The legacy `-t` short flag for `--config` (still accepted in this release)

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
