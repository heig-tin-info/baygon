# Baygon Demo

This is a minimal demo of Baygon. It shows how to use Baygon to create simple functional tests.

```console
.
├── Makefile
├── main.c
└── tests.yml
```

To run the tests, simply run `make test`.

You can simply run `baygon` followed by the executable name, or add `exectuable: ./a.out` in `tests.yml` to run Baygon without specifying the executable name.
