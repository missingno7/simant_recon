"""Lift four source-owned DGROUP words to one native external C owner each."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PLAN_PATH = ROOT / "portable/research/private_data_lifts_v1.json"


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _lexical_replace(source: str, replacements: dict[str, str]) -> tuple[str, dict[str, int]]:
    out: list[str] = []
    counts = {name: 0 for name in replacements}
    i, n, state = 0, len(source), "code"
    while i < n:
        ch = source[i]
        nxt = source[i + 1] if i + 1 < n else ""
        if state == "code":
            if ch == "/" and nxt in ("*", "/"):
                state = "block_comment" if nxt == "*" else "line_comment"
                out.extend((ch, nxt)); i += 2; continue
            if ch == '"':
                state = "string"; out.append(ch); i += 1; continue
            if ch == "'":
                state = "char"; out.append(ch); i += 1; continue
            if ch == "_" or ch.isalpha():
                j = i + 1
                while j < n and (source[j] == "_" or source[j].isalnum()):
                    j += 1
                token = source[i:j]
                replacement = replacements.get(token)
                if replacement is None:
                    out.append(token)
                else:
                    out.append(replacement)
                    counts[token] += 1
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
        out.append(ch); i += 1
        if ch == "\\" and i < n:
            out.append(source[i]); i += 1; continue
        if (state == "string" and ch == '"') or (state == "char" and ch == "'"):
            state = "code"
    if state in {"block_comment", "string", "char"}:
        raise ValueError(f"unterminated C lexical state: {state}")
    return "".join(out), counts


def _replace_once(source: str, old: str, new: str, *, newline: bool = False) -> str:
    if newline:
        old += "\n"; new += "\n"
    count = source.count(old)
    if count != 1:
        raise ValueError(f"expected one pinned source anchor, found {count}: {old!r}")
    return source.replace(old, new, 1)


def _load_plan() -> dict:
    plan = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
    if plan.get("schema") != "simant-private-data-lift-plan-v1":
        raise ValueError("unrecognized private DATA lift plan")
    for rel, expected in plan["pins"].items():
        path = ROOT / rel
        if not path.is_file() or _sha(path.read_bytes()) != expected:
            raise ValueError(f"private DATA lift input changed: {rel}")
    manifest = json.loads((ROOT / "layout/manifest.json").read_text(encoding="utf-8"))
    symbols = json.loads((ROOT / "layout/symbols.json").read_text(encoding="utf-8"))
    if manifest.get("oracle_sha256") != plan["oracle_sha256"]:
        raise ValueError("private DATA lift oracle identity changed")
    manifest_modules = manifest.get("modules", {})
    for owner in plan["owners"]:
        row = symbols.get("data", {}).get(owner["dos_symbol"])
        address = owner["address"]
        if row is None or [row.get("seg"), row.get("off")] != address:
            raise ValueError(f"private DATA symbol address changed: {owner['dos_symbol']}")
        module = manifest_modules.get(owner["manifest_module"])
        if module is None or module.get("source") != owner["source"]:
            raise ValueError(f"private DATA owner module changed: {owner['source']}")
        if module.get("source_sha256") != plan["pins"][owner["source"]]:
            raise ValueError(f"private DATA owner source hash differs from manifest: {owner['source']}")
        placement = module.get("placements", {}).get("_DATA")
        if placement is None:
            raise ValueError(f"private DATA owner has no validated _DATA contribution: {owner['source']}")
        start = placement["seg"] * 16 + placement["off"]
        target = address[0] * 16 + address[1]
        if not (start <= target and target + owner["width"] <= start + placement["size"]):
            raise ValueError(f"private DATA address is outside owner placement: {owner['dos_symbol']}")
        source_text = (ROOT / owner["source"]).read_text(encoding="utf-8")
        if source_text.count(owner["definition"]) != 1:
            raise ValueError(f"private DATA owner definition changed: {owner['owner']}")
        if target - start != owner["placement_offset"]:
            raise ValueError(f"private DATA owner offset changed: {owner['owner']}")
    for rel, spec in plan["units"].items():
        module = next((m for m in manifest_modules.values() if m.get("source") == rel), None)
        if module is None or module.get("source_sha256") != spec["source_sha256"]:
            raise ValueError(f"private DATA consumer identity missing from manifest: {rel}")
    return plan


def _adapt(source: str, source_path: str, spec: dict, plan: dict) -> tuple[str, dict | None]:
    out = source
    for old, new in spec.get("replace_lines", []):
        out = _replace_once(out, old, new, newline=True)
    out, counts = _lexical_replace(out, spec.get("tokens", {}))
    for token, expected in spec.get("output_token_counts", {}).items():
        if counts.get(token, 0) != expected:
            raise ValueError(f"{source_path}: rewritten use count mismatch for {token}: {counts.get(token, 0)} != {expected}")
    if out == source:
        return source, None
    return out, {
        "kind": "SOURCE_PRIVATE_DATA_OWNER_LIFT",
        "plan": PLAN_PATH.relative_to(ROOT).as_posix(),
        "plan_sha256": _sha(PLAN_PATH.read_bytes()),
        "source": source_path,
        "source_sha256": spec["source_sha256"],
        "input_sha256": _sha(source.encode("utf-8")),
        "output_sha256": _sha(out.encode("utf-8")),
        "identifier_rewrites": counts,
        "lexical_passes": 1,
        "claim": "one source-owned C object is externally visible to native consumers; no DOS behavior or historical acceptance claim",
    }


def adapt(source: str, source_path: str) -> tuple[str, dict | None]:
    """Adapt one unmodified pinned original TU; other paths are unchanged."""
    plan = _load_plan()
    spec = plan["units"].get(source_path)
    if spec is None:
        return source, None
    if _sha(source.encode("utf-8")) != spec["source_sha256"]:
        raise ValueError(f"private DATA lift source changed: {source_path}")
    return _adapt(source, source_path, spec, plan)


def adapt_reviewed(source: str, source_path: str) -> tuple[str, dict | None]:
    """Adapt after earlier reviewed transforms, preserving exact alias anchors."""
    plan = _load_plan()
    spec = plan["units"].get(source_path)
    if spec is None:
        return source, None
    for old, _new in spec.get("replace_lines", []):
        if source.count(old + "\n") != 1:
            raise ValueError(f"{source_path}: source owner/extern anchor changed: {old}")
    _, anchors = _lexical_replace(source, {name: name for name in spec.get("tokens", {})})
    for token, expected in spec.get("anchor_token_counts", {}).items():
        if anchors.get(token, 0) != expected:
            raise ValueError(f"{source_path}: source alias-use count changed for {token}: {anchors.get(token, 0)} != {expected}")
    return _adapt(source, source_path, spec, plan)
