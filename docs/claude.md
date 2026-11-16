# Claude Code skill

Baygon ships a [skill](https://code.claude.com/docs/en/skills) for
[Claude Code](https://code.claude.com). With it, Claude knows how to name and
find the configuration file, write tests (matchers, filters, expressions,
limits, points), run Baygon and read its results. Claude uses it on its own when
a project holds a `baygon.yml`, or when you ask for functional tests of a
program.

## Install as a plugin

The Baygon repository is a Claude Code plugin marketplace. Add it once, then
install the plugin:

```console
claude plugin marketplace add heig-tin-info/baygon
claude plugin install baygon@baygon
```

The same commands work inside a session as `/plugin marketplace add
heig-tin-info/baygon` and `/plugin install baygon@baygon`. The plugin follows
the repository, and `/plugin` lists, updates or removes it.

## Install from the Python package

The skill is also part of the `baygon` package. Copy it where Claude Code looks
for skills:

```console
baygon --install-skill user      # ~/.claude/skills/baygon, for every project
baygon --install-skill project   # ./.claude/skills/baygon, for this project only
```

`baygon --install-skill DIR` copies it into another skills directory. Running
the command again replaces the previous copy, for example after upgrading
Baygon; a `baygon` directory that holds something else is never replaced. Start
a new Claude Code session to load the skill.

A project skill can be committed with the assignment, so that everyone working
on it with Claude Code gets it.

## What the skill contains

- `SKILL.md`: file names and discovery, writing tests, matchers, filters,
  expressions, limits, command-line options, a workflow to write tests and the
  common pitfalls.
- `reference.md`: every configuration key, scoring, the report format, source
  code checks, the Python API and the failure messages.
