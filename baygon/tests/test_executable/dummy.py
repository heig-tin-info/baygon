#!/usr/bin/env python3
import sys

print("an apple", file=sys.stdout)
print("an orange", file=sys.stderr)

sys.exit(42)
