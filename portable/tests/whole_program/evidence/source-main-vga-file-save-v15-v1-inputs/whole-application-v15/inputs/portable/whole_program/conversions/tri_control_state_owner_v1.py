"""Fixed native owner aliases for the complete source triangle-control types."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
PLAN = ROOT / "portable/research/tri_control_state_owner_v1.json"
PLAN_SHA256 = "2dd6d3cb3b74ba8d37466bd024f594a6d1602d0aad1a17216d0116346dd98d02"
HEADER = '#include "portable/whole_program/state/tri_control_state.h"'


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _plan() -> dict:
    data = PLAN.read_bytes()
    if _sha(data) != PLAN_SHA256:
        raise ValueError("fixed triangle-control owner plan identity mismatch")
    return json.loads(data.decode("utf-8"))


def _adapt(text: str, plan: dict) -> str:
    names = plan["source"]["aliases"]
    for index, (name, spec) in enumerate(names.items()):
        if text.count(name) != spec["references"]:
            raise ValueError(f"triangle-control reference count changed: {name}")
        if name in {"fd_50F6_3816", "fd_50F6_3822"}:
            anchor = f"extern struct TriPoints far {name};"
        else:
            anchor = f"extern struct Pt far {name};"
        if text.count(anchor) != 1:
            raise ValueError(f"expected exact source declaration: {name}")
        text = text.replace(anchor, HEADER if index == 0 else "", 1)
    return text


def adapt_source(source: str | bytes, rel: str) -> str:
    raw = source.encode("utf-8") if isinstance(source, str) else source
    plan = _plan()
    spec = plan["source"]
    if rel != spec["path"] or _sha(raw) != spec["sha256"]:
        raise ValueError("frozen triangle-control source identity mismatch")
    return _adapt(raw.decode("utf-8"), plan)


def adapt_reviewed(source: str, rel: str) -> tuple[str, dict]:
    plan = _plan()
    spec = plan["source"]
    if rel != spec["path"] or _sha((ROOT / rel).read_bytes()) != spec["sha256"]:
        raise ValueError("frozen triangle-control source identity mismatch")
    output = _adapt(source, plan)
    return output, {
        "kind": "SOURCE_TYPED_TRIANGLE_CONTROL_STATE",
        "plan_sha256": PLAN_SHA256,
        "frozen_source_sha256": spec["sha256"],
        "input_sha256": _sha(source.encode("utf-8")),
        "output_sha256": _sha(output.encode("utf-8")),
        "exact_alias_declaration_replacements": 5,
        "active_reference_counts": {n: row["references"] for n, row in spec["aliases"].items()},
    }
