"""Fixed native owner alias for the S12 map-cursor source Rect."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
PLAN = ROOT / "portable/research/map_cursor_rect_owner_v1.json"
PLAN_SHA256 = "5676b5afff3531bc29b22323f38a72903912e3eb7e836c7c3271c9cb0cd94812"
HEADER = '#include "portable/whole_program/state/map_cursor_rect.h"'


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _plan() -> dict:
    data = PLAN.read_bytes()
    if _sha(data) != PLAN_SHA256:
        raise ValueError("fixed map cursor Rect plan identity mismatch")
    return json.loads(data.decode("utf-8"))


def adapt_source(source: str | bytes, rel: str) -> str:
    raw = source.encode("utf-8") if isinstance(source, str) else source
    plan = _plan()
    spec = plan["source"]
    if rel != spec["path"] or _sha(raw) != spec["sha256"]:
        raise ValueError("frozen map cursor source identity mismatch")
    return _replace(raw.decode("utf-8"), spec)


def adapt_reviewed(source: str, rel: str) -> tuple[str, dict]:
    plan = _plan()
    spec = plan["source"]
    if rel != spec["path"] or _sha((ROOT / rel).read_bytes()) != spec["sha256"]:
        raise ValueError("frozen map cursor source identity mismatch")
    output = _replace(source, spec)
    return output, {
        "kind": "SOURCE_TYPED_MAP_CURSOR_RECT",
        "plan_sha256": PLAN_SHA256,
        "frozen_source_sha256": spec["sha256"],
        "input_sha256": _sha(source.encode("utf-8")),
        "output_sha256": _sha(output.encode("utf-8")),
        "extern_anchor_replacements": 1,
        "active_reference_count": spec["active_references"],
    }


def _replace(source: str, spec: dict) -> str:
    anchor = f"extern struct Rect far {spec['symbol']};"
    if source.count(anchor) != 1:
        raise ValueError("expected exact map cursor Rect declaration")
    if source.count(spec["symbol"]) != spec["active_references"]:
        raise ValueError("map cursor Rect reference count changed")
    return source.replace(anchor, HEADER, 1)
