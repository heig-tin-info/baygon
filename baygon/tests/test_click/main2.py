#!/usr/bin/env python3
import sys

if len(sys.argv) > 1 and sys.argv[1] == '--version':
    print('Version 0.1.1', file=sys.stderr)
    exit(0)

if len(sys.argv) != 2 + 1:
    exit(1)

print(f'a+b = {sys.argv[1]} + {sys.argv[2]}')
