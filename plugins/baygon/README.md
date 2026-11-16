# Baygon plugin for Claude Code

This plugin adds the `baygon` skill to [Claude Code](https://code.claude.com).
With it, Claude knows how to write, run and debug
[Baygon](https://github.com/heig-tin-info/baygon) functional tests: how to name
and find the configuration file (`baygon.yml`), describe tests with matchers,
filters, expressions and time limits, give points for grading, check source
code, run the `baygon` command and read its results.

Claude uses the skill on its own when a project holds a Baygon configuration,
or when you ask for functional tests of a command-line program.

## Install

```console
claude plugin marketplace add heig-tin-info/baygon
claude plugin install baygon@baygon
```

Baygon itself is installed with `pip install baygon` or `uv tool install baygon`.
The plugin version follows the Baygon releases.
