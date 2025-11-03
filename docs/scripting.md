# Scripting

You can use Baygon as a library to write your own test runner. This is useful if you want to write your own test runner or if you want to use Baygon in a CI/CD pipeline.

Here is an example of a test runner using Baygon:

```python
from pathlib import Path
from baygon.suite import SuiteService

service = SuiteService()
report = service.run(
    data={
        'filters': {'uppercase': True},
        'tests': [{
            'args': ['--version'],
            'stderr': [{'contains': 'VERSION'}],
        }],
    },
    executable=Path('myapp'),
)

assert report.failures == 0
```

## Validation

You can validate a Baygon configuration file with the `baygon.Schema` function:

```python
import baygon

data = baygon.Schema({
    'version': 1,
    'tests': [{
        'name': 'Test',
        'exit': 0
    }]
})

assert(data['version'], 1)
```
