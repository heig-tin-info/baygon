# Baygon reference

## Top-level keys

| Key | Meaning |
|---|---|
| `version` | `1` or `2` (syntax version, use `1`) |
| `name` | Name of the suite |
| `executable` | Program under test, inherited by every test |
| `tests` | **Required.** List of tests and groups |
| `filters` | Filters applied to every output |
| `eval` | `true`, or `{start, end, init}`, to evaluate `{{ }}` expressions |
| `timeout` | Default time limit in seconds |
| `max-output` | Default cap per output stream (`64K`, `10M`, bytes; `0` = none) |
| `points` / `weight` / `min-points` | Scoring (see below) |

## Test keys

| Key | Default | Meaning |
|---|---|---|
| `name` | `""` | Shown in the output and the report |
| `executable` | inherited | Overrides the inherited program |
| `args` | `[]` | Arguments; numbers are converted to strings |
| `stdin` | `""` | Text, or `{executable, args}` of a generator whose output is the input |
| `env` | `{}` | Extra environment variables |
| `exit` | not checked | Expected exit status (`true`/`false` read as 1/0), or `{value, message}` |
| `stdout` / `stderr` | `[]` | Conditions (a plain value means `equals`) |
| `repeat` | `1` | Runs the test N times, stops at the first failing run |
| `message` | inherited | Explanation shown when the test fails (`{{ }}` allowed) |
| `filters` | inherited | Added to the inherited filters |
| `timeout` / `max-output` | inherited | Limits for this test |
| `points` / `weight` | computed | Scoring |

A group has `name`, `tests` and any inheritable key (`executable`, `filters`,
`timeout`, `max-output`, `points`, `weight`, `min-points`, `message`).

## Conditions

A condition is a mapping with optional `filters` and one or more matchers. All
matchers of all conditions must pass.

```yaml
stdout:
  - equals: "exact text\n"
  - contains: part
  - regex: '^\d+ items$'
  - number: 42                              # equal to within 1e-9
  - number: { value: 3.14, tolerance: 0.01 }
  - number: { min: 0, max: 100 }            # bounds included
  - length: { max: 80 }                     # characters
  - lines: 3
  - same-as: ./solution                     # run with the same args, stdin, env
  - filters: { lowercase: true }
    contains: error                         # filters for this condition only
  - not:
      - contains: Traceback
      - number: 0
  - regex: '^usage: '
    message: Print the usage on stdout.     # explains this condition only
```

- `number` parses the whole (filtered, stripped) output. Use a `regex` filter to
  remove surrounding text: `filters: {regex: ['^Result: ', '']}`.
- `same-as` runs the reference once per run of the test, even if used on both
  `stdout` and `stderr`; its exit status is ignored; filters apply to both
  outputs. A reference or generator that fails to start, times out, or (for a
  generator) exits non-zero fails the test with `Generator ./x failed: ...`.

## Filters

`trim` (whitespace at both ends of the output), `lowercase`, `uppercase`, `ignorespaces` (alias
`ignore-spaces`), `regex: [pattern, replacement]`, `replace: [old, new]`.
Applied in that order whatever the order in the file. `uppercase: false`
disables a filter.

## Expressions (`eval`)

```yaml
eval:
  start: "{{"          # default delimiters
  end: "}}"
  init: "from datetime import date"   # string or list, run once
```

Evaluation order in a run: `args`, `stdin`, `env`, `exit`, generator args, then
matcher values after the program ran. Assignments (`{{ x = 3 }}`) are visible to
later expressions. Available: `math`, `random`, `statistics` functions and
`iter(start=0, step=1)`, one counter per expression text.

## Scoring

- Without any `points` or `weight` anywhere, no points are computed.
- `points` at any level is distributed to its children according to their
  `weight` (default 10), rounded to `min-points` (default 0.1).
- A test with explicit `points` keeps them; the rest is shared by the others.

```yaml
version: 1
points: 20
tests:
  - name: Basics
    weight: 5          # 20 * 5 / 15 = 6.7
    tests:
      - args: [1, 2]   # 3.3
      - args: [2, 3]   # 3.4
  - name: Edge cases
    weight: 10         # 13.3
    tests:
      - args: []       # 13.3
        exit: 1
```

`baygon -T` shows points per test; `-r report.json` writes:

```json
{
  "successes": 8, "failures": 2, "skipped": 0, "total": 10, "time": 0.4,
  "points": {"earned": 15.5, "total": 20},
  "cases": [{"id": "1.1", "name": "...", "status": "passed",
             "points": {"earned": 2, "total": 2}, "time": 0.01, "issues": []}],
  "groups": [{"id": "1", "name": "Basics", "successes": 4, "failures": 0,
              "skipped": 0, "total": 4, "points": {"earned": 6.7, "total": 6.7}}]
}
```

Grade one criterion at a time: `baygon --only 2 -r part2.json`.

## Source code checks

Each test can run another program on the sources. Paths in `args` are relative
to the current directory.

```yaml
version: 1
tests:
  - name: Program header with the author
    executable: cat
    args: [main.c]
    stdout:
      - regex: '^/\*[\s\S]*?Author:\s*\S+[\s\S]*?\*/'
  - name: Include guard
    executable: cat
    args: [sum.h]
    stdout:
      - regex: '#ifndef\s+(\w+)\s*\n#define\s+\1\b'
  - name: No forbidden function
    executable: grep
    args: [-nE, '\b(gets|system)\s*\(', main.c]
    exit: 1                       # grep finds nothing
  - name: At most 100 lines
    executable: wc
    args: [-l, main.c]
    stdout:
      - filters: { regex: ['^\s*(\d+).*$', '\1'] }
        number: { max: 100 }
  - name: No warnings
    executable: gcc
    args: [-std=c11, -Wall, -Wextra, -Werror, -fsyntax-only, main.c]
    exit: 0
  - name: Formatting
    executable: clang-format
    args: [--dry-run, --Werror, main.c]
    exit: 0
```

## Python API

```python
from baygon.suite import SuiteExecutor, SuiteService

service = SuiteService()
context = service.load(path="baygon.yml")
context = context.select(ids=["2"], keywords=None)    # like --only 2
report = SuiteExecutor().run(context, timeout=5)      # like --timeout 5
print(report.points_earned, report.points_total)
print(report.as_dict()["groups"])                     # same data as --report

from baygon import Schema
Schema(open("baygon.yml").read())   # validate; raises pydantic ValidationError
```

## Messages

| Message | Meaning |
|---|---|
| `Invalid exit status: expected 0, got 1.` | `exit` mismatch |
| `Output stdout does not contain X. Found "..." instead.` | `contains` failed |
| `Output stdout should not contain X.` | a `not` matcher matched |
| `Output stdout is not a number: "..."` | `number` could not parse the output |
| `Timeout after 5 s.` | the program was killed at its time limit |
| `Output limit exceeded (more than N bytes)` | the program printed too much |
| `Invalid test: ...` | bad regex, non-numeric `exit`, eval error in the test |
| `Error: invalid configuration` + `path: message` lines | schema error, exit code 1 |
