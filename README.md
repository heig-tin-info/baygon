# HEIG Test

This package is a minimalist functional test suite for executables. It relies on a `test.yml` or `test.json` file that lists all the possible tests.

## Test file format

It can be either a `.yml` or a `.json` file.

```yml
version: 1
executable: ./a.out
tests:
  - name: No errors if two arguments
    args: [1, 2]
    exit-status: 0
  - name: Error if less than two arguments
    args: [1]
    exit-status: 1
  - name: Stdout is the sum of arguments
    args: [1, 2]
    stdout: 3
  - name: Version on stderr
    args: ['--version']
    stderr:
      - regex: '\b\d\.\d\.\d\b'
      - contains: 'Version'
```

## Usage

It can have the standard output:

```console
$ heig-tests
....

Ran 4 tests found in tests.yml.

ok.
```

It can be quiet:

```console
$ heig-tests
$ echo $?
0
```

It can be verbose:

```console
$ heig-tests -v

Test 1: No errors if two arguments  PASSED
Test 2: Error if less than two arguments  PASSED
Test 3: Stdout is the sum of arguments  PASSED
Test 4: Version on stderr  PASSED

Ran 4 tests found in tests.yml.

ok.
```

## How to install?

```
pip3 install -U heig-test
```

## Contributing ?

```
sudo apt update python3-venv
git clone https://github.com/heig-tin-info/heig-test.git
cd heig-test
python3 -m venv env
source env/bin/activate
pip install -e .
```
