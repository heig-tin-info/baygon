# Todo and planned features for the project

## To Do

- [ ] Support GDB unit test
- [ ] Support Builtin unit test

- [ ] Eval filter
  - [ ] Input/Output filters
  - [ ] EvalInputFilter
  - [ ] Iter class
- [ ] Short test summary info

## New Features

### Standalone Unit test

```python
from baygon import UnitTest

class Test(UnitTest):
    def test_version(self):
        res = self.functions.add(2, 3)
        self.assert_equal(res, 5)
```

### Presentation

```text

---- 1.2.1 Test blabla --------------------------------- (green or red)
$ ./a.out 1 2
3

Assert stdout is 3 .............................. PASSED
Assert stderr is empty .......................... PASSED
Assert exit status is 0 ......................... PASSED

==== Short Test Summary Info ===========================

========================================================

29 failed, 63 passed, 4 skipped, 96 total tests
Baygon ran 96 tests in 0.01s on 2022-11-10 12:00:00
```
