# Baygon

[![CI](https://img.shields.io/github/actions/workflow/status/heig-tin-info/baygon/ci.yml?branch=main&logo=github&label=CI)](https://github.com/heig-tin-info/baygon/actions?query=event%3Apush+branch%3Amain+workflow%3ACI)
[![Coverage](https://coverage-badge.samuelcolvin.workers.dev/heig-tin-info/baygon.svg)](https://coverage-badge.samuelcolvin.workers.dev/redirect/heig-tin-info/baygon)
[![pypi](https://img.shields.io/pypi/v/baygon.svg)](https://pypi.python.org/pypi/baygon)
[![downloads](https://static.pepy.tech/badge/baygon/month)](https://pepy.tech/project/baygon)
[![versions](https://img.shields.io/pypi/pyversions/baygon.svg)](https://github.com/heig-tin-info/baygon)
[![license](https://img.shields.io/github/license/heig-tin-info/baygon.svg)](https://github.com/heig-tin-info/baygon/blob/main/LICENSE)
[![GitHub issues](https://img.shields.io/github/issues/heig-tin-info/baygon.svg)](https://github.com/heig-tin-info/baygon/issues)
[![GitHub last commit](https://img.shields.io/github/last-commit/heig-tin-info/baygon.svg)](https://github.com/heig-tin-info/baygon/commits/master)
![Build and Deploy](https://github.com/heig-tin-info/baygon/workflows/Build%20and%20Deploy/badge.svg)
![Python](https://img.shields.io/pypi/pyversions/baygon)
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

## How to install?

```console
pip3 install baygon
```

## Build documentation

The documentation is build upon VuePress.

```console
cd docs
yarn install
yarn docs:build
yarn docs:dev
```

## Contributing

### Quick Start with uv (Recommended)

[uv](https://github.com/astral-sh/uv) is a fast Python package installer and resolver:

```bash
git clone https://github.com/heig-tin-info/baygon.git
cd baygon

# Install dependencies and create virtual environment
uv sync --all-extras

# Run tests
uv run pytest

# Run linters
uv run ruff check baygon tests
uv run black --check baygon tests

# Run all tests with tox
uv run tox
```

### Alternative: Using Poetry

```bash
git clone https://github.com/heig-tin-info/baygon.git
cd baygon

# Install dependencies
poetry install --with dev

# Run tests
poetry run pytest

# Run linters
poetry run ruff check baygon tests
poetry run black --check baygon tests

# Run all tests with tox
poetry run tox
```

### Development Setup

For running tests across multiple Python versions, install `pyenv`:

```bash
# Install required Python versions
pyenv install 3.10.15
pyenv install 3.11.11
pyenv install 3.12.8
pyenv install 3.13.3
pyenv global 3.10.15 3.11.11 3.12.8 3.13.3
```

### Running Tests

Using the Makefile (recommended):

```bash
# Install dependencies (auto-detects uv or poetry)
make install

# Run all tests
make test

# Run tests with coverage
make test-cov

# Run linters
make lint

# Format code
make format

# Run all tox environments
make tox

# Clean build artifacts
make clean

# Show all available commands
make help
```

Or run commands directly:

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_schema.py

# Run with coverage
pytest --cov=baygon --cov-report=html

# Run linters and formatters
ruff check baygon tests
black --check baygon tests

# Run all environments (Python 3.10-3.13, linters, coverage)
tox
```

### Code Quality Tools

This project uses modern Python tooling:

- **pytest**: Testing framework
- **pytest-cov**: Coverage reporting
- **ruff**: Fast Python linter (replaces flake8, isort, and more)
- **black**: Code formatter
- **tox**: Test automation across Python versions
- **mypy**: Optional static type checking
