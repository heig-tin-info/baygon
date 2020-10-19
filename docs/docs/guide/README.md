# Introduction

Baygon is a minimalistic test framework for any types of executables. It provides a simple way of testing code with a [JSON](https://en.wikipedia.org/wiki/JSON) or a [YAML](https://en.wikipedia.org/wiki/YAML) description of tests.

## Getting started

Let's say you have this C program that you want to test:

```c
#include <stdio.h>
#include <string.h>
#include <stdlib.h>

int main(int argc, char *argv[]) {
    if (argc > 1 && strcmp(argv[1], "--version") == 0) {
        fprintf(stderr, "Version 0.1.1\n");
        return 0;
    }
    if (argc != 2 + 1) return 1;
    printf("%d", atoi(argv[1]) + atoi(argv[2]));
}
```

You then need to write a test file that can be named `t.yaml`, `t.json`, `test.yaml`, `test.json`, `tests.yml` or `test.json`. Baygon is gonna find it. Inside this file you describe each individual functional test:

```yaml
version: 1
tests:
  - name: Arguments check
    tests:
      - name: No errors if two arguments
        args: [1, 2]
        exit: 0
      - name: Error if less than two arguments
        args: [1]
        exit: 1
  - name: Stdout is the sum of arguments
    args: [1, 2]
    stdout: []
  - name: Version on stderr
    args: ['--version']
    stderr:
      - regex: '\b\d\.\d\.\d\b'
      - contains: 'Version'
```

To be able to run the tests, simply install [Baygon](https://pypi.org/project/baygon/):

```
pip install baygon
```

Then build and test you application:

```
cc app.c -o a.out
baygon -v ./a.out
Test 1: Arguments check
  Test 1.1: No errors if two arguments.......... PASSED
  Test 1.2: Error if less than two arguments.... PASSED
Test 2: Stdout is the sum of arguments.......... PASSED
Test 3: Version on stderr....................... PASSED

Ran 4 tests in 0.01s.

ok.
```