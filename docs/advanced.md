# Advanced

## Test on source files

You may want to run checks on the source files. This is possible by using `cat` as executable, with the file as argument:

```yaml
version: 1
tests:
  - name: Function foo is defined
    executable: cat
    args: [foo.c]
    stdout:
      - regex: void\s+foo\s*\(\s*int\s+\w+\)
```

See [Checking the source code](source-checks.md) for more recipes: program header, include guards, forbidden functions, compiler warnings, formatting...

