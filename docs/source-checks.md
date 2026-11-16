# Checking the source code

Baygon tests programs from the outside, but a test can run any program, not
only the one under test. Checks on the source code of an assignment are
therefore tests that run `cat`, `grep`, `wc`, a compiler or a formatter on the
sources, and check their output or their exit status.

A bare name such as `grep` is looked up in the `PATH` (see
[Executable](syntax.md#executable)), and each test can use its own executable.
The paths given in `args` are relative to the directory Baygon is started from.

The checks below run on a small C project made of `main.c`, `sum.c` and
`sum.h`.

## Program header

The file must start with a comment giving the author:

```yaml
- name: Program header with the author
  executable: cat
  args: [main.c]
  stdout:
    - regex: '^/\*[\s\S]*?Author:\s*\S+[\s\S]*?\*/'
```

## Include guard

The header must be protected against multiple inclusion, with the same name in
`#ifndef` and `#define`:

```yaml
- name: Include guard in sum.h
  executable: cat
  args: [sum.h]
  stdout:
    - regex: '#ifndef\s+(\w+)\s*\n#define\s+\1\b'
```

## Forbidden functions

`grep` exits with 1 when it finds nothing, and prints the offending lines
otherwise, which shows up in the failure message:

```yaml
- name: No forbidden function
  executable: grep
  args: [-nE, '\b(gets|system)\s*\(', main.c, sum.c]
  exit: 1 # grep exits with 1 when it finds nothing
```

## Code left in comments

A line comment that ends with a semicolon is most likely code that was
commented out:

```yaml
- name: No commented-out code
  executable: grep
  args: [-nE, '^\s*//.*;\s*$', main.c, sum.c]
  exit: 1
```

## Length of a file

`wc -l` prints the number of lines followed by the file name. A `regex` filter
keeps the number, which the [`number` matcher](syntax.md#numbers) compares:

```yaml
- name: At most 100 lines in main.c
  executable: wc
  args: [-l, main.c]
  stdout:
    - filters:
        regex: ['^\s*(\d+).*$', '\1'] # Keep the number only
      number: { max: 100 }
```

## Compiler warnings

```yaml
- name: Compiles without warnings
  executable: gcc
  args: [-std=c11, -Wall, -Wextra, -Werror, -fsyntax-only, main.c, sum.c]
  exit: 0
```

A static analyser works the same way, for example
`cppcheck --error-exitcode=1 --enable=warning main.c sum.c` with `exit: 0`.

## Indentation and formatting

[clang-format](https://clang.llvm.org/docs/ClangFormat.html) checks the files
against the style given in a `.clang-format` file, and fails on the first
difference with `--Werror`:

```yaml
- name: Formatting follows .clang-format
  executable: clang-format
  args: [--dry-run, --Werror, main.c, sum.c, sum.h]
  exit: 0
```

`pip install clang-format` installs it when it is not available on the system.

## Putting it together

The checks are tests like any other. Put them in a group to give them their
own share of the points, and run them alone with `--only`:

```yaml
version: 1
executable: ./a.out
tests:
  - name: Behaviour
    points: 15
    tests:
      - args: [1, 2]
        stdout: "3\n"
  - name: Code quality
    points: 5
    tests:
      - name: Compiles without warnings
        executable: gcc
        args: [-std=c11, -Wall, -Wextra, -Werror, -fsyntax-only, main.c, sum.c]
        exit: 0
      - name: No forbidden function
        executable: grep
        args: [-nE, '\b(gets|system)\s*\(', main.c, sum.c]
        exit: 1
```

```console
baygon --only 2 --report quality.json
```
