#!/usr/bin/env python
import sys

print("an apple", file=sys.stdout)
print("an orange", file=sys.stderr)

sys.exit(42)
