#!/usr/bin/env python
import sys

if len(sys.argv) > 1 and sys.argv[1] == '--version':
    print('Version 0.1.1', file=sys.stderr)
    sys.exit(0)

if len(sys.argv) != 2 + 1:
    sys.exit(1)

print(int(sys.argv[1]) + int(sys.argv[2]))
