#!/usr/bin/env python3
"""Validate fixed v2 historical source and archived fixture hashes."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "portable/tools"))
import source_state_aliases_v2 as aliases  # noqa: E402


def main() -> int:
    plan = aliases.load_plan()
    failures = aliases.validate_historical_pins(plan)
    failures.extend(aliases.validate_source_declarations(plan))
    if failures:
        print("historical pin validation failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print(f"historical pins pass: {len(plan['pinned_source_hashes'])} source/layout inputs, "
          f"{len(plan['fixture_hashes'])} archived fixtures; migration not consulted")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
