"""Exact source adapter for the shared native elevator thumb-size point."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
PLAN = ROOT / "portable/research/elevator_thumb_size_owner_v1.json"
HEADER = '#include "portable/whole_program/state/elevator_thumb_size.h"'


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _load_plan() -> dict:
    plan_bytes = PLAN.read_bytes()
    if _sha(plan_bytes) != "a6bbe99d6569cdfcea36e7cd7c0ef387c9ab7c65a1e61f8a329f05cf98bbf3cb":
        raise ValueError("fixed elevator-size plan identity mismatch")
    return json.loads(plan_bytes.decode("utf-8"))


def adapt_source(source: str | bytes, rel: str) -> str:
    raw = source.encode("utf-8") if isinstance(source, str) else source
    plan = _load_plan()
    spec = plan["source_modules"].get(rel)
    if spec is None:
        raise ValueError(f"unregistered elevator-size source: {rel}")
    if _sha(raw) != spec["sha256"]:
        raise ValueError(f"frozen source identity mismatch: {rel}")
    return _replace(raw.decode("utf-8"), rel, spec)


def adapt_reviewed(source: str, rel: str) -> tuple[str, dict]:
    plan = _load_plan()
    spec = plan["source_modules"].get(rel)
    if spec is None:
        raise ValueError(f"unregistered elevator-size source: {rel}")
    if _sha((ROOT / rel).read_bytes()) != spec["sha256"]:
        raise ValueError(f"frozen source identity mismatch: {rel}")
    output = _replace(source, rel, spec)
    return output, {
        "kind": "SOURCE_TYPED_ELEVATOR_THUMB_SIZE",
        "plan_sha256": _sha(PLAN.read_bytes()),
        "frozen_source_sha256": spec["sha256"],
        "input_sha256": _sha(source.encode("utf-8")),
        "output_sha256": _sha(output.encode("utf-8")),
        "extern_anchor_replacements": 1,
        "active_symbol_reference_count": spec["active_reference_count"],
    }


def _replace(text: str, rel: str, spec: dict) -> str:
    anchor = "extern struct Pt far fd_50F6_47DA;"
    if text.count(anchor) != 1:
        raise ValueError(f"expected exactly one Pt declaration: {rel}")
    if text.count("fd_50F6_47DA") != spec["active_reference_count"]:
        raise ValueError(f"elevator-size reference count drift: {rel}")
    return text.replace(anchor, HEADER, 1)

