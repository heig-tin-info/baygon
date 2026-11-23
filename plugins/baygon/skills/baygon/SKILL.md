---
name: baygon
description: Write, run and debug Baygon functional tests (baygon.yml / tests.yml) for command-line programs, typically student assignments in C or any language. Use when a project contains a Baygon configuration file, when the user wants to test a program's exit status, stdout or stderr from a YAML/JSON description, to grade an assignment with points, or to check source code (headers, forbidden functions, warnings) with Baygon.
---

# Baygon

Baygon runs an executable with given arguments and standard input, then checks
its exit status, standard output and standard error against a YAML or JSON
description. It is made for teaching: points, groups, reports, time limits.

Install: `pip install baygon` or `uv tool install baygon`. Check: `baygon --version`.

Full key reference and more examples: [reference.md](reference.md).

## Configuration file name and location

Name the file `baygon.yml` (preferred). Baygon looks for these names, in this
order, in the current directory and then in each parent directory:

| Base name | Extensions (in order) |
|---|---|
| `baygon`, then `t`, `test`, `tests` | `.json`, `.yml`, `.yaml` |

So `baygon.yml`, `tests.yaml` or `t.json` are all found. Any other name must be
given explicitly: `baygon -c path/to/file.yml` (`.yml`, `.yaml` or `.json` only).

Paths:

- A relative `executable` is relative to the **directory of the config file**.
  A bare name (`grep`, `gcc`) that is not a file there is looked up in `PATH`.
- The program runs in the **current directory**, so relative paths in `args`
  are relative to where `baygon` is started.
- An executable given on the command line (`baygon ./a.out`) is relative to the
  current directory, and cannot be combined with a top-level `executable` key.

## Minimal file

```yaml
version: 1
executable: ./a.out
tests:
  - name: Sum of two numbers
    args: [1, 2]
    stdout: "3\n"   # stdout includes the trailing newline
    exit: 0
```

## Writing tests

A test is a mapping in a `tests` list. A mapping with its own `tests` list is a
group. Settings (`executable`, `filters`, `timeout`, `max-output`, points) are
inherited from parents; the nearest value wins. Ids are automatic: `1`, `2.1`...

Keys of a test: `name`, `args` (list), `stdin` (text, or a generator program),
`env` (mapping), `exit` (expected status), `stdout`, `stderr` (lists of
conditions), `repeat`, `filters`, `timeout`, `max-output`, `executable`,
`points`/`weight`, `message`.

Matchers in a `stdout`/`stderr` condition (after filters):

| Matcher | Passes when the output... |
|---|---|
| `equals: text` | is exactly `text` (a plain value is a shortcut: `stdout: 3`) |
| `contains: text` | contains `text` |
| `regex: pattern` | matches the Python regex (search, not full match) |
| `number: 3.14` / `{value, tolerance}` / `{min, max}` | is a number, equal or in range |
| `length: n` / `{min, max}` | has n characters |
| `lines: n` / `{min, max}` | has n lines |
| `same-as: ./solution` | equals the output of a reference program (same args/stdin) |
| `not: [ {contains: x}, ... ]` | every listed matcher fails |

```yaml
version: 1
executable: ./calc
filters: { trim: true }          # applied to every output
tests:
  - name: Usage error without arguments
    args: []
    exit: 1
    stderr:
      - contains: usage
  - name: Area of a circle
    args: [area, 2]
    stdout:
      - filters: { regex: ['^Area: ', ''] }   # keep the number only
        number: { value: 12.566, tolerance: 0.001 }
  - name: No debug output
    args: [add, 1, 2]
    stdout:
      - lines: 1
      - not:
          - contains: DEBUG
    stderr: ""                   # nothing on stderr
```

Filters: `trim`, `lowercase`, `uppercase`, `ignorespaces`, `regex: [pattern,
replacement]`, `replace: [old, new]`. They are applied in that fixed order, on
the whole file, a group, a test or a single condition.

## Messages for students

A failing test prints the command to run it again (`$ ./prog abc`), then the
issue. For beginners, add a `message` in their language saying what to fix. It
goes on a test, a group (inherited by its tests), a `stdout`/`stderr`
condition, or the exit status:

```yaml
version: 1
executable: ./prog
tests:
  - name: Invalid argument
    args: [abc]
    exit: { value: 2, message: "main must end with return 2;" }
    stdout:
      - regex: '^usage: '
        message: Print the usage with printf.
```

Messages accept `{{ }}` expressions, evaluated with the values of the failing
run. Prefer a message to a clever regex: the regex is shown to the student.

## Random and repeated inputs

Set `eval: true` at the top level to evaluate `{{ python }}` in `args`, `stdin`,
`env`, `exit` and expected values. `math`, `random` and `statistics` functions
are available; `{{ a = randint(1, 9) }}` assigns and prints; `iter()` gives
0, 1, 2... across runs of a repeated test. Quote mustaches in YAML.

```yaml
version: 1
eval: true
executable: ./add
tests:
  - repeat: 10
    args: ["{{ a = randint(0, 100) }}", "{{ b = randint(0, 100) }}"]
    stdout:
      - number: "{{ a + b }}"
```

Generated input and reference solution:

```yaml
  - repeat: 20
    stdin: { executable: ./generate, args: ["{{ iter() }}"] }
    stdout:
      - same-as: ./solution
```

## Limits (always set them for student code)

`timeout: 5` (seconds) and `max-output: 64K` at any level. A program that hangs
or prints forever is killed with its children; only its test fails. Output is
capped at 16 MiB by default; there is no default timeout unless `--timeout`.

## Running

```console
baygon                     # finds baygon.yml, runs ./executable from the config
baygon ./a.out             # executable from the command line
baygon -v                  # list each test;  -vvv shows every command
baygon --pretty            # rich panels for failing tests (args, stdin, outputs)
baygon -T                  # summary table with points
baygon --only 2.1          # run test/group by id prefix (repeatable, or 1,3)
baygon -k parsing          # run tests whose name or group name contains text
baygon --timeout 5         # default time limit for every test
baygon --strict            # exit 1 if a test fails (use in CI / make test)
baygon -r report.json      # JSON/YAML report: totals, cases, groups, points
```

Baygon exits with 0 even when tests fail unless `--strict` is given; it exits
with 1 on configuration errors (printed one per line, e.g.
`tests.0.stdout.0.bogus: Extra inputs are not permitted`).

## Workflow when asked to write tests

1. Read the assignment and the program's usage; build it if needed.
2. Run the program by hand on a few inputs to see the exact output format
   (trailing newline, spacing, stderr vs stdout, exit status).
3. Write `baygon.yml` next to the sources with `version: 1`, the
   `executable`, a `timeout`, and one group per feature of the specification.
4. Prefer robust matchers: `trim` filter, `contains`/`regex`/`number` with a
   tolerance over exact `equals` on long outputs.
5. Run `baygon -v` (or `--pretty` on failures) and fix the tests, not the
   program, until a correct implementation passes everything.
6. For grading, add `points` and check the totals with `baygon -T`.

## Common pitfalls

- `stdout: "3"` fails on `3\n`: write `"3\n"` or add `filters: {trim: true}`.
- `{{ ... }}` is left as is when `eval` is not set.
- `exit` compares the status as an integer; `grep` exits 1 when it finds nothing.
- `regex` searches anywhere; anchor with `^`/`$` (single line) or `\A`/`\Z`.
- Quote regexes and strings with `:` `{` `[` `#` in YAML: `regex: '^\d+: ok$'`.
- Each item of `not` must hold exactly one matcher; `same-as` cannot be negated.
- `iter()` keeps one counter per expression text: two tests with the very same
  `{{ n = iter(1) }}` share it. Vary the text or pass `ctx="name"`.
- A repeated test stops at its first failing run.
- Destructive programs (`rm`, `mv`, `dd`, `mkfs`, `wget`) are refused as
  executables.
