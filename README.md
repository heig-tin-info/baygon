# Baygon

[![GitHub issues](https://img.shields.io/github/issues/heig-tin-info/baygon.svg)](https://github.com/heig-tin-info/baygon/issues)
[![GitHub last commit](https://img.shields.io/github/last-commit/heig-tin-info/baygon.svg)](https://github.com/heig-tin-info/baygon/commits/master)
![Build and Deploy](https://github.com/heig-tin-info/baygon/workflows/Build%20and%20Deploy/badge.svg)
![Python](https://img.shields.io/pypi/pyversions/baygon)
[![PyPI version](https://img.shields.io/pypi/v/baygon)](https://pypi.org/project/baygon/)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/baygon)](https://pypi.org/project/baygon/#files)
[![License](https://img.shields.io/pypi/l/baygon)](https://github.com/heig-tin-info/baygon/blob/master/LICENSE.txt)
[![codecov](https://codecov.io/github/heig-tin-info/baygon/branch/master/graph/badge.svg?token=hFuVW5z784)](https://codecov.io/github/heig-tin-info/baygon)

**K**ills **B**ugs **D**ead!

<img src="https://github.com/heig-tin-info/baygon/raw/master/docs/docs/.vuepress/public/baygon.svg" data-canonical-src="https://github.com/heig-tin-info/baygon/docs/docs/.vuepress/public/baygon.svg" width="400"/>

This package is a minimalist functional test suite for binaries. It relies on a description of tests usually in `test.yml` or `test.json`.

The **documentation** is available [here](https://heig-tin-info.github.io/baygon/).

## Test file format

It can be either a `.yml` or a `.json` file.

```yml
version: 1
tests:
  - name: Arguments check
    tests:
      - name: No errors if two arguments
        args: [1, 2]
        exit: 0
      - name: Error if less than two arguments
        args: [1]
        exit: 1
  - name: Stdout is the sum of arguments
    args: [1, 2]
    stdout: []
  - name: Version on stderr
    args: ['--version']
    stderr:
      - regex: '\b\d\.\d\.\d\b'
      - contains: 'Version'
```

## Usage

```console
$ info-test -v ./a.out
Test 1: Arguments check
    Test 1.1: No errors if two arguments................ PASSED
    Test 1.2: Error if less than two arguments.......... PASSED
Test 2: Stdout is the sum of arguments.................. PASSED
Test 3: Version on stderr............................... PASSED

Ran 4 tests in 0.0s.

ok.
```

CLI highlights:

- Use `--pretty` to render rich panels for failing tests, including captured command telemetry.
- Pass `-T`/`--table` to display an aggregated summary table once the run completes.
- Provide a custom test definition with `-c`/`--config`. The legacy `-t` flag is still recognised but deprecated.

## Programmatic usage

Baygon now exposes the same building blocks used by the CLI so you can embed
the runner directly in your tooling:

```python
from baygon.config import load_config
from baygon.runtime import BaygonRunner

suite = load_config("tests/smoke.yml")
runner = BaygonRunner(suite, base_dir=Path("tests"))
report = runner.run()

for case in report.cases:
    print(f"{case.case.name}: {case.status}")
```

You can also extend Baygon by registering custom filters or matchers:

```python
from baygon.filters import Filter, register_filter

@register_filter("strip-digits")
class FilterStripDigits(Filter):
    def apply(self, value: str) -> str:
        return "".join(c for c in value if not c.isdigit())
```

## How to install?

```console
pip3 install baygon
```

## Build documentation

The site is powered by MkDocs Material. From the repository root:

```bash
uv sync --group docs
uv run --group docs mkdocs serve --strict
```

To create a production build:

```bash
uv run --group docs mkdocs build --strict
```

## Contributing ?

```console
git clone https://github.com/heig-tin-info/baygon.git
cd baygon
uv sync --group dev
```

### Tests

Install `pyenv` then install all required version of Python:

```bash
pyenv install 3.9.9
pyenv install 3.10.4
pyenv install 3.11.0
pyenv install 3.12.0
pyenv install 3.13.0
pyenv global 3.9.9 3.10.4 3.11.0 3.12.0 3.13.0
```

Then sync your uv environment:

```bash
uv sync --group dev
```

Run the automated checks:

```bash
uv run --group dev nox -s lint tests
```

Baygon can even test itself against all supported Python versions:

```bash
uv run baygon .venv/bin/baygon
```
