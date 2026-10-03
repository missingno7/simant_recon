#!/usr/bin/env python3
"""Apply the frozen v2 state alias plan in one lexical pass.

This pass is intentionally narrow: four scalar symbol renames and two
interior pointer-table views. The canonical pointer-table base is never
rewritten here.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PLAN = ROOT / "portable/tests/recovered/whole_program_asm_state/plan_v2.json"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_plan(path: Path = DEFAULT_PLAN) -> dict:
    plan = json.loads(path.read_text(encoding="utf-8"))
    if plan.get("schema") != "simant-whole-program-asm-state-plan-v2":
        raise ValueError("unrecognized frozen alias plan")
    return plan


def validate_historical_pins(plan: dict, root: Path = ROOT) -> list[str]:
    """Validate only immutable planned source/fixture pins; never read migration."""
    mismatches = []
    for mapping in (plan["pinned_source_hashes"], plan["fixture_hashes"]):
        for rel, expected in mapping.items():
            path = root / rel
            if not path.exists() or digest(path) != expected:
                mismatches.append(rel)
    parent = root / plan["parent_receipt"]["path"]
    if not parent.exists() or digest(parent) != plan["parent_receipt"]["sha256"]:
        mismatches.append(plan["parent_receipt"]["path"])
    return mismatches


def validate_source_declarations(plan: dict, root: Path = ROOT) -> list[str]:
    failures = []
    for rel, declarations in plan["source_declarations_exact"].items():
        lines = (root / rel).read_text(encoding="utf-8").splitlines()
        for expected in declarations:
            if expected not in lines:
                failures.append(f"{rel}: missing exact declaration/initializer {expected}")
    return failures


def transform(source: str, plan: dict) -> tuple[str, dict]:
    """Rewrite extern declarations/references in one left-to-right lexical pass."""
    scalar = {r["alias"]: r["target"] for r in plan["alias_rewrites"]
              if r["kind"] == "scalar-lvalue"}
    interior = {r["alias"]: r["target"] for r in plan["alias_rewrites"]
                if r["kind"] == "interior-pointer-table-lvalue"}
    targets = {**scalar, **interior}
    replacement_counts = {name: 0 for name in targets}
    removed_externs = {name: 0 for name in interior}
    out: list[str] = []
    i = 0
    n = len(source)
    state = "code"
    while i < n:
        # Interior views are not standalone objects. Remove their exact extern
        # declaration lines; the already-owned table declaration stays intact.
        line_start = i == 0 or source[i - 1] == "\n"
        if line_start and state == "code":
            end = source.find("\n", i)
            end = n if end < 0 else end
            line = source[i:end]
            if line.lstrip().startswith("extern "):
                for alias in interior:
                    if (re.search(rf"\b{re.escape(alias)}\b", line)
                            and line.strip().endswith(";")):
                        out.append("\n" if end < n else "")
                        removed_externs[alias] += 1
                        i = end + (1 if end < n else 0)
                        break
                if i > end:
                    continue
        ch = source[i]
        nxt = source[i + 1] if i + 1 < n else ""
        if state == "code":
            if ch == "/" and nxt == "*":
                state = "block_comment"; out.extend((ch, nxt)); i += 2; continue
            if ch == "/" and nxt == "/":
                state = "line_comment"; out.extend((ch, nxt)); i += 2; continue
            if ch == '"':
                state = "string"; out.append(ch); i += 1; continue
            if ch == "'":
                state = "char"; out.append(ch); i += 1; continue
            if ch == "_" or ch.isalpha():
                j = i + 1
                while j < n and (source[j] == "_" or source[j].isalnum()):
                    j += 1
                token = source[i:j]
                target = targets.get(token)
                if target is None:
                    out.append(token)
                else:
                    replacement_counts[token] += 1
                    if token in interior:
                        out.append(f"({target})")
                    else:
                        out.append(target)
                i = j; continue
            out.append(ch); i += 1; continue
        if state == "block_comment":
            out.append(ch)
            if ch == "*" and nxt == "/":
                out.append(nxt); i += 2; state = "code"; continue
            i += 1; continue
        if state == "line_comment":
            out.append(ch); i += 1
            if ch == "\n": state = "code"
            continue
        if state in {"string", "char"}:
            out.append(ch); i += 1
            if ch == "\\" and i < n:
                out.append(source[i]); i += 1; continue
            if (state == "string" and ch == '"') or (state == "char" and ch == "'"):
                state = "code"
            continue
    if state in {"block_comment", "string", "char"}:
        raise ValueError(f"unterminated lexical state: {state}")
    return "".join(out), {"replacement_counts": replacement_counts,
                          "removed_externs": removed_externs,
                          "storage_owners_created": 0,
                          "canonical_table_base_rewritten": False,
                          "lexical_passes": 1}

