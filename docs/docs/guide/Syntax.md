# Syntax

## Base

Each config file should start with the version of the syntax which is `1`. Then the mandatory `tests` dictionary must exist. The following is a minimal example composed of 1 test which tests if the output is 3 when the binary is run with two arguments `1` and `2`:

```yaml
version: 1
tests:
  - args: [1, 2]
    stdout: 3
```

## Filters

Global filters can be applied to all outputs of every tests. The outputs are `stdout` and `stderr`. Baygon features the following filters:

- `uppercase`: All outputs are transformed into uppercase.
- `lowercase`: All outputs are transformed into lowercase.
- `trim`: All outputs are trimmed (spaces are removed from both ends, on each line
- `regex`: A remplacement is made using regular expressions.

In the following, both standard output and standard error will be in lowercase and every occurence of `foo` or `foobar` will be replaced by `bar`:

```yaml
version: 1
filters:
  lowercase: true
  regex: [foo(bar)?, bar]
tests:
  - args: [1, 2]
    stdout: 3
```

## Naming

All tests can be optionnally named:

```yaml
version: 1
tests:
  - name: Test functionality of the additionner
    args: [--add, 40, 2]
    stdout: 42
  - name: Test error if less than two arguments
    args: []
    exit: 2
```

## Groups and subgroups

Tests can be groupped into sub sections, by nesting each test into categories:

```yaml
version: 1
tests:
  - name: Category 1
    tests:
      - args: [1, 2]
        stdout: 3
  - name: Category 2
    tests:
      - name: Subcategory 1
        tests:
          - args: [1, 2]
            stdout: 3
```

## Exit status

The exit status can be checked with the `exit` key followed with an integer. The following checks if the program returns 0

```yaml
version: 1
tests:
  - exit: 0
```

## Standard outputs

Both `stdout` and `stderr` can be tested against multiple conditions:

```yaml
tests:
  - stdout:
      - contains: foo # Must contain the word foo
      - regex: f(oo|aa|uu) # Must match
    stderr:
      - equals: foobar # Must be exactly equal to foobar
```

## Executable

In the case you want to specify a different executable name for a different test:

```yaml
tests:
  - name: Test ./foo
    executable: ./foo
    stdout: I am Foo
  - name: Test ./bar
    executable: ./bar
    stderr: I am bar
  - name: Group
    executable: ./baz
    tests:
      - name: Test 1
        exit: 0
```

The executable is propagated through the test tree and can be overwritten at any level. Of couse, the executable can also be defined on the main header:

```yaml
version: 1
executable: ./foobar
tests:
  - name: Test ./foobar
    exit: 0
```

Or even from the shell:

```console
$ baygon ./foobar
```

## Custom config file

You may want to tell Baygon to use a custom configuration file. This is possible from the command line:

```console
$ baygon --config other.yaml
```

## Tests of strings

Baygon currently features three type of tests :

- `contains`: A string contained into the corresponding output.
- `regex`: A Python regular expression
- `equals`: An exact match

You can combine any of the three tests together:

```yaml
tests:
  - stdout:
      - contains: foo # Must contain the word foo
      - regex: f(oo|aa|uu) # Must match
      - equals: foobar
```

You can also add a negation with the `not` keyword:

```yaml
tests:
  - stdout:
      not:
        - contains: foo # Must contain the word foo
        - regex: f(oo|aa|uu) # Must match
        - equals: foobar
```

