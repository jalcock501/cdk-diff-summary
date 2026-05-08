#!/usr/bin/env python3
"""Thin script wrapper kept as the composite action entrypoint."""

from cdk_diff_summary.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
