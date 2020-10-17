#!/usr/bin/env python
import sys

if len(argv) > 1 and argv[1] == '--version': 
    print('Version 0.1.1')
    exit(0)

if len(argv) != 2 + 1:
    exit(1)

print(int(argv[1]) + int(argv[2])
