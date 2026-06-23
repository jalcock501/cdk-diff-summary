#!/usr/bin/env python3
"""Thin script wrapper kept as the composite action entrypoint."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from cdk_diff_summary.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
