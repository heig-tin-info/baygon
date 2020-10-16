# Baygon

Kills Bugs Dead!

This package is a minimalist functional test suite for binaries. It relies on a description of tests usually in `test.yml` or `test.json`. 

## Test file format

It can be either a `.yml` or a `.json` file.

```yml
version: 1
tests:
  - name: Arguments check
    tests:
      - name: No errors if two arguments
        args: [1, 2]
        exit-status: 0
      - name: Error if less than two arguments
        args: [1]
        exit-status: 1
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

```
pip3 install -U baygon
```

## Contributing ?

```
sudo apt update python3-venv
git clone https://github.com/heig-tin-info/baygon.git
cd baygon
python3 -m venv env
source env/bin/activate
pip install -e .
```
