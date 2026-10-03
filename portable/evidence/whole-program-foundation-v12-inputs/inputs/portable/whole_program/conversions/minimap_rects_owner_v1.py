"""Fixed source adapter for the two persistent minimap Rect runtime views."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
PLAN = ROOT / "portable/research/minimap_rects_owner_v1.json"
PLAN_SHA256 = "3de0722dc337ee401f5e403ca2d4073ba9fe51e50b77ee669f3e4a2519bdebb7"
HEADER = '#include "portable/whole_program/state/minimap_rects.h"'


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _load_plan() -> dict:
    raw = PLAN.read_bytes()
    if _sha(raw) != PLAN_SHA256:
        raise ValueError("fixed minimap Rect plan identity mismatch")
    return json.loads(raw.decode("utf-8"))


def adapt_source(source: str | bytes, rel: str) -> str:
    raw = source.encode("utf-8") if isinstance(source, str) else source
    plan = _load_plan()
    spec = plan["source"]
    if rel != spec["path"] or _sha(raw) != spec["sha256"]:
        raise ValueError("frozen minimap Rect source identity mismatch")
    return _replace(raw.decode("utf-8"), plan)


def adapt_reviewed(source: str, rel: str) -> tuple[str, dict]:
    plan = _load_plan()
    spec = plan["source"]
    if rel != spec["path"] or _sha((ROOT / rel).read_bytes()) != spec["sha256"]:
        raise ValueError("frozen minimap Rect source identity mismatch")
    output = _replace(source, plan)
    return output, {
        "kind": "SOURCE_TYPED_MINIMAP_RECT_PAIR",
        "plan_sha256": PLAN_SHA256,
        "frozen_source_sha256": spec["sha256"],
        "input_sha256": _sha(source.encode("utf-8")),
        "output_sha256": _sha(output.encode("utf-8")),
        "declaration_replacements": 2,
        "references": {name: row["references"] for name, row in spec["declarations"].items()},
    }


def _replace(source: str, plan: dict) -> str:
    spec = plan["source"]
    if _sha((ROOT / spec["path"]).read_bytes()) != spec["sha256"]:
        raise ValueError("frozen minimap Rect source changed")
    replacements = 0
    for name, row in spec["declarations"].items():
        anchor = row["anchor"]
        if source.count(anchor) != 1:
            raise ValueError(f"expected one source Rect declaration: {name}")
        if source.count(name) != row["references"]:
            raise ValueError(f"minimap Rect reference count drift: {name}")
        source = source.replace(anchor, "" if replacements else HEADER, 1)
        replacements += 1
    if replacements != 2:
        raise ValueError("expected exactly two source Rect aliases")
    return source
