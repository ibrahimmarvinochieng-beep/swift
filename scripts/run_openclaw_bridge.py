#!/usr/bin/env python3
"""Convenience script to run the OpenClaw bridge from the project root."""

import sys
from pathlib import Path

_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_root))

from openclaw_integration.cli import main

if __name__ == "__main__":
    main()
