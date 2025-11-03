#!/usr/bin/env python3
import sys


def main() -> int:
    sys.stdout.buffer.write(b"\xff")
    sys.stdout.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
