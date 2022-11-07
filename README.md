# Baygon

[![GitHub issues](https://img.shields.io/github/issues/heig-tin-info/baygon.svg)](https://github.com/heig-tin-info/baygon/issues)
[![GitHub last commit](https://img.shields.io/github/last-commit/heig-tin-info/baygon.svg)](https://github.com/heig-tin-info/baygon/commits/master)
![Build and Deploy](https://github.com/heig-tin-info/baygon/workflows/Build%20and%20Deploy/badge.svg)
![Python](https://img.shields.io/pypi/pyversions/baygon)

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
pip3 install -U baygon
```

## Build documentation

The documentation is build upon VuePress.

```console
cd docs
yarn install
yarn docs:build
yarn docs:dev
```

## Contributing ?

```console
sudo apt update python-venv
git clone https://github.com/heig-tin-info/baygon.git
cd baygon
python -m venv env
source env/bin/activate
pip install -e .
```
