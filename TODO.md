# Todo and planned features for the project

## To Do

- [ ] Support GDB unit test
- [ ] Support Builtin unit test

## New Features

### Standalone Unit test

```python
from baygon import UnitTest

class Test(UnitTest):
    def test_version(self):
        res = self.functions.add(2, 3)
        self.assert_equal(res, 5)
```
