"""Exact-source adapter for the shared menu-bar Rect runtime owner."""

from __future__ import annotations

import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
PLAN = ROOT / "portable/research/menu_bar_rect_owner_v1.json"
PLAN_SHA256 = "49a7771ed35fbdf2dd8e1c6ebd579a0e5cbad8b8a35b9ea847acb60017c1648f"
HEADER = '#include "portable/whole_program/state/menu_bar_rect.h"'


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def adapt_source(source: str | bytes, rel: str) -> str:
    raw = source.encode("utf-8") if isinstance(source, str) else source
    if _sha256(PLAN.read_bytes()) != PLAN_SHA256:
        raise ValueError("fixed menu Rect plan identity mismatch")
    plan = __import__("json").loads(PLAN.read_text(encoding="utf-8"))
    entry = plan["source_modules"].get(rel)
    if entry is None:
        raise ValueError(f"unregistered menu Rect source: {rel}")
    if _sha256(raw) != entry["sha256"]:
        raise ValueError(f"frozen source identity mismatch: {rel}")
    text = raw.decode("utf-8")
    anchor = "extern struct Rect far fd_50F6_393C;"
    if text.count(anchor) != 1:
        raise ValueError(f"expected exactly one Rect declaration: {rel}")
    if text.count("fd_50F6_393C") < entry["minimum_references"]:
        raise ValueError(f"source reference count drift: {rel}")
    text = text.replace(anchor, HEADER, 1)
    return text


def adapt_reviewed(source: str, rel: str) -> tuple[str, dict]:
    """Apply the exact alias rewrite after earlier source adapters.

    The supplied text may contain upstream native conversions, so it is not
    required to equal the frozen TU. Its route is still tied to the frozen raw
    source and this fixed plan; the exact extern and total active-name count
    must remain as expected at this pipeline boundary.
    """
    if _sha256(PLAN.read_bytes()) != PLAN_SHA256:
        raise ValueError("fixed menu Rect plan identity mismatch")
    plan = __import__("json").loads(PLAN.read_text(encoding="utf-8"))
    if rel not in plan["source_modules"]:
        raise ValueError(f"unregistered menu Rect source: {rel}")
    frozen = (ROOT / rel).read_bytes()
    if _sha256(frozen) != plan["source_modules"][rel]["sha256"]:
        raise ValueError(f"frozen source identity mismatch: {rel}")
    spec = plan["source_modules"][rel]
    anchor = "extern struct Rect far fd_50F6_393C;"
    if source.count(anchor) != 1:
        raise ValueError(f"expected exactly one reviewed-stage Rect declaration: {rel}")
    if source.count("fd_50F6_393C") != spec["minimum_references"]:
        raise ValueError(f"reviewed-stage source reference count drift: {rel}")
    output = source.replace(anchor, HEADER, 1)
    if output.count("fd_50F6_393C") != spec["minimum_references"] - 1:
        raise ValueError(f"unexpected alias rewrite count: {rel}")
    return output, {
        "kind": "SOURCE_TYPED_MENU_RECT_SINGLETON",
        "plan_sha256": PLAN_SHA256,
        "frozen_source_sha256": spec["sha256"],
        "input_sha256": _sha256(source.encode("utf-8")),
        "output_sha256": _sha256(output.encode("utf-8")),
        "extern_anchor_replacements": 1,
        "active_symbol_reference_count": spec["minimum_references"],
    }

