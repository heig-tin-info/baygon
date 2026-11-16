# Config File Syntax

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
- `ignorespaces`: All spaces are removed from all outputs (`ignore-spaces` is accepted as an alias).
- `regex`: A remplacement is made using regular expressions.
- `replace`: A remplacement is made using a string.

If more than one filter is applied, they are applied in the order they are written.

A boolean filter set to `false` (e.g. `uppercase: false`) is not applied.

In the following, both standard output and standard error will be in lowercase and every occurrences of `foo` or `foobar` will be replaced by `bar`:

```yaml
version: 1
filters:
  lowercase: true
  regex: [foo(bar)?, bar]
tests:
  - args: [1, 2]
    stdout: 3
```

Filters can also be applied to a single test:

```yaml
version: 1
tests:
  - args: [1, 2]
    stdout:
      - contains: foo
      - regex: f(oo|aa|uu)
    filters:
      lowercase: true
```

Or even at a stream output level:

```yaml
stdout: [{ filters: { trim: true }, equals: 3 }]
```

## Naming

All tests can be optionally named:

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

Tests can be grouped into sub sections, by nesting each test into categories:

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

The executable is propagated through the test tree, and the nearest one wins: a group or a test can set its own executable even when a parent already has one.

```yaml
version: 1
executable: ./app
tests:
  - name: Run
    stdin: "0\n"
  - name: No compiler warning
    executable: /bin/cat # Replaces ./app for this test only
    args: [obj/gcc_output.cmd]
    stdout:
      - not:
          - contains: 'warning:'
```

!!! note
    Up to Baygon 0.7, overriding an inherited executable was an error
    (`Executable can't be overridden`). An executable given on the command line
    still cannot be combined with one at the top level of the configuration.

One approach is name the executable at the top level:

```yaml
version: 1
executable: ./foobar
tests:
  - name: Test ./foobar
    exit: 0
```

Or even from the shell:

```console
baygon ./foobar
```

Note that the working directory is the directory of the config file, except if you specify the executable from the shell. In this case the working directory is the current directory.

## Time and output limits

A program that never ends, or that prints without end (a menu shown again and
again at the end of input is a classic), must not block the whole run. Two keys,
accepted at the top level, on a group or on a test, limit each run of a program.
Like `executable`, the nearest value wins.

- `timeout`: wall-clock limit in seconds (an integer or a decimal number).
- `max-output`: number of bytes kept from each output stream (`stdout` and
  `stderr`). A number of bytes, or a size such as `64K`, `10M` or `1G`.
  `0` removes the limit.

```yaml
version: 1
executable: ./app
timeout: 5 # Default of every test
tests:
  - name: Exits with code 1 on EOF
    timeout: 1 # This test only
    stdin: ""
    exit: 1
  - name: Prints the menu
    max-output: 64K
    stdout:
      - contains: Menu
```

When a limit is reached, the program and every process it started are killed,
the test fails with `Timeout after 1 s.` or `Output limit exceeded`, and the
rest of the suite goes on. A test with `repeat` stops at the first run that
reaches a limit.

There is no time limit by default. The `--timeout` option sets one for every
test whose configuration has none:

```console
baygon --timeout 10
```

The output of each stream is capped at 16 MiB by default, so Baygon never
holds an unbounded amount of output in memory.

## Configuration file

By default Baygon will look for a file named `baygon.yml` in the current directory. You can specify a different file with the `-c` or `--config` option:

```console
baygon --config other.yaml
```

!!! note
    Baygon 0.5.x historically used the `-t` flag for selecting the configuration file. The CLI still accepts `-t` for backward compatibility, but newer releases prefer `-c`/`--config`.

Other names such as `t`, `test` or `tests` can be used, but the extension must be `.json`, `.yml` or `.yaml`. Here some valid configuration names:

```text
baygon.yml
baygon.yaml
baygon.json
tests.yml
t.json
...
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
