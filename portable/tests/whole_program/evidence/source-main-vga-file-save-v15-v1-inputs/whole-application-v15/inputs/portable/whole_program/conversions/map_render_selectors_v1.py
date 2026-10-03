"""Strict shared-owner binding for root m0250 map-render selectors."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PLAN = ROOT / "portable/research/map_render_selectors_v1.json"
PLAN_SHA256 = "3092f77ab391af98961df4cb618eedccd7b621c51e8837bea3141d4610cf4bc5"


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _plan() -> dict:
    raw = PLAN.read_bytes()
    if _sha(raw) != PLAN_SHA256:
        raise ValueError("map-render selector plan identity mismatch")
    return json.loads(raw.decode("utf-8"))


def adapt_reviewed(source: str, rel: str) -> tuple[str, dict]:
    plan = _plan()
    original = plan["source"]
    if rel != original["path"]:
        raise ValueError("unexpected translation unit for selector binding")
    if _sha((ROOT / rel).read_bytes()) != original["sha256"]:
        raise ValueError("canonical selector source changed")

    text = source
    replacements = 0
    expected = {
        "g_94E4": ("extern uint8_t  g_94E4;", original["declarations"]["g_94E4"]),
        "g_9126": ("extern uint16_t  g_9126;", original["declarations"]["g_9126"]),
    }
    for name, (native_decl, historical_decl) in expected.items():
        # Counts include comments in both frozen and transformed source. That
        # intentionally makes unexpected edits fail closed.
        if text.count(name) != original["active_references"][name]:
            raise ValueError(f"selector reference count changed for {name}")
        if text.count(native_decl) != 1:
            raise ValueError(f"expected one unsigned native declaration for {name}")
        # Confirm the frozen declaration itself remains the exact unsigned
        # source spelling; signed declarations are never silently accepted.
        frozen = (ROOT / rel).read_text(encoding="utf-8")
        if frozen.count(historical_decl) != 1:
            raise ValueError(f"historical unsigned declaration changed for {name}")
        text = text.replace(native_decl, "", 1)
        replacements += 1

    include = '#include "portable/whole_program/state/map_render_selectors.h"'
    if text.count(include) > 1:
        raise ValueError("duplicate map selector owner include")
    if include not in text:
        text = include + "\n" + text
    return text, {
        "kind": "SHARED_UNSIGNED_MAP_RENDER_SELECTOR_OWNERS",
        "plan_sha256": PLAN_SHA256,
        "frozen_source_sha256": original["sha256"],
        "input_sha256": _sha(source.encode("utf-8")),
        "output_sha256": _sha(text.encode("utf-8")),
        "declarations_replaced": replacements,
        "active_reference_counts": dict(original["active_references"]),
        "owner_widths": {name: spec["width"] for name, spec in plan["native"]["owners"].items()},
    }


def validate_negative_controls(source: str, rel: str) -> dict:
    """Small converter self-check: signed-width drift must be rejected."""
    cases = {}
    for name, signed, unsigned in (
        ("g_94E4", "int8_t", "uint8_t"),
        ("g_9126", "int16_t", "uint16_t"),
    ):
        mutated = source.replace(f"extern {unsigned}  {name};",
                                 f"extern {signed}  {name};", 1)
        try:
            adapt_reviewed(mutated, rel)
        except ValueError:
            cases[name] = "rejected"
        else:
            raise AssertionError(f"signed selector mutant accepted: {name}")
    return cases
