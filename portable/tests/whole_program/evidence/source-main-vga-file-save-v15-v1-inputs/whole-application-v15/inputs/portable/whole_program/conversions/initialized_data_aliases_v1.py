"""Apply the reviewed d3D57 initialized-owner views before scalar lowering.

This source-phase adapter is deliberately fixed to the four reviewed aliases.
It does not consult whole-program migration output and never allocates an owner.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PLAN_PATH = ROOT / "portable/research/initialized_data_aliases_v1.json"


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _load_plan() -> dict:
    plan = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
    if plan.get("schema") != "simant-initialized-data-alias-plan-v1":
        raise ValueError("unrecognized initialized DATA alias plan")
    for rel, expected in plan["pins"].items():
        path = ROOT / rel
        if not path.is_file() or _sha(path.read_bytes()) != expected:
            raise ValueError(f"initialized DATA alias pin changed: {rel}")
    manifest = json.loads((ROOT / "layout/manifest.json").read_text(encoding="utf-8"))
    symbols = json.loads((ROOT / "layout/symbols.json").read_text(encoding="utf-8"))
    if manifest.get("oracle_sha256") != plan["oracle_sha256"]:
        raise ValueError("initialized DATA alias oracle identity changed")
    manifest_sources = {row.get("source"): row.get("source_sha256")
                        for row in manifest.get("modules", {}).values()}
    for rel, spec in plan["units"].items():
        if manifest_sources.get(rel) != spec["source_sha256"]:
            raise ValueError(f"manifest source identity mismatch: {rel}")
    for name, address in plan["addresses"].items():
        row = symbols.get("data", {}).get(name)
        if row is None or [row.get("seg"), row.get("off")] != address:
            raise ValueError(f"manifested DATA address changed: {name}")
    for alias, owner, offset in [
        ("fd_3D57_07B6", "ExpSubStates", 0),
        ("fd_3D57_07CE", "fd_3D57_07CC", 2),
        ("fd_3D57_0852", "fd_3D57_082A", 40),
        ("fd_3D57_0C1C", "fd_3D57_0C1A", 2),
    ]:
        a, o = symbols["data"][alias], symbols["data"][owner]
        if a["seg"] != o["seg"] or a["off"] != o["off"] + offset:
            raise ValueError(f"source alias no longer lies at reviewed owner offset: {alias}")
    if symbols["data"]["fd_3D57_07B6"].get("alias_of") != "ExpSubStates":
        raise ValueError("signed-byte owner alias relationship changed")
    return plan


def _lexical_replace(source: str, replacements: dict[str, str]) -> tuple[str, dict[str, int]]:
    """Replace C identifiers in code only, preserving comments and literals."""
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


def _replace_exact(source: str, old: str, new: str, expected: int = 1) -> str:
    count = source.count(old)
    if count != expected:
        raise ValueError(f"expected {expected} exact declaration(s), found {count}: {old!r}")
    return source.replace(old, new)


def _adapt(source: str, source_path: str, spec: dict, plan: dict) -> tuple[str, dict]:
    """Apply exact declarator edits, then identifier replacements once."""
    out = source
    for old, new in spec.get("exact_declarations", []):
        out = _replace_exact(out, old, new)
    for old, new in spec.get("exact_expressions", []):
        out = _replace_exact(out, old, new)
    for declaration in spec.get("remove_lines", []):
        out = _replace_exact(out, declaration + "\n", "")
    for declaration in spec.get("replace_lines", []):
        old, new = declaration
        out = _replace_exact(out, old + "\n", new + "\n")
    out, token_counts = _lexical_replace(out, spec.get("tokens", {}))
    if spec.get("prelude"):
        out = spec["prelude"] + out
    for token, expected in spec.get("output_token_counts", {}).items():
        if token_counts.get(token, 0) != expected:
            raise ValueError(f"{source_path}: {token} rewritten {token_counts.get(token, 0)}, expected exactly {expected}")
    if _sha(out.encode("utf-8")) == _sha(source.encode("utf-8")):
        raise ValueError(f"pinned adapter produced no change: {source_path}")
    return out, {
        "kind": "REVIEWED_INITIALIZED_DATA_ALIAS_VIEWS",
        "plan": PLAN_PATH.relative_to(ROOT).as_posix(),
        "plan_sha256": _sha(PLAN_PATH.read_bytes()),
        "source": source_path,
        "source_sha256": spec["source_sha256"],
        "input_sha256": _sha(source.encode("utf-8")),
        "output_sha256": _sha(out.encode("utf-8")),
        "identifier_rewrites": token_counts,
        "lexical_passes": 1,
        "claim": "source-backed native typed views; no historical matching or behavioral proof claim",
    }


def adapt(source: str, source_path: str) -> tuple[str, dict | None]:
    """Adapt one unmodified pinned original source TU; unmapped paths pass through."""
    plan = _load_plan()
    spec = plan["units"].get(source_path)
    if spec is None:
        return source, None
    if _sha(source.encode("utf-8")) != spec["source_sha256"]:
        raise ValueError(f"initialized DATA alias source changed: {source_path}")
    return _adapt(source, source_path, spec, plan)


def adapt_reviewed(source: str, source_path: str) -> tuple[str, dict | None]:
    """Adapt after pinned source-aware overlays while requiring source anchors.

    The canonical original file remains hash-pinned on disk. The supplied text
    may contain earlier reviewed transformations (startup/history/body
    overlays); exact alias declarations, save-table expressions, and required
    code identifiers must still be present before this adapter can run.
    """
    plan = _load_plan()
    spec = plan["units"].get(source_path)
    if spec is None:
        return source, None
    for declaration in spec.get("exact_declarations", []):
        if source.count(declaration[0]) != 1:
            raise ValueError(f"{source_path}: reviewed initialized owner declaration anchor changed")
    for expression in spec.get("exact_expressions", []):
        if source.count(expression[0]) != 1:
            raise ValueError(f"{source_path}: reviewed save-table expression anchor changed")
    for declaration in spec.get("remove_lines", []):
        if source.count(declaration + "\n") != 1:
            raise ValueError(f"{source_path}: reviewed alias declaration anchor changed: {declaration}")
    _, anchor_counts = _lexical_replace(source, {name: name for name in spec.get("tokens", {})})
    for token, expected in spec.get("anchor_token_counts", {}).items():
        if anchor_counts.get(token, 0) != expected:
            raise ValueError(f"{source_path}: reviewed alias use count changed for {token}: {anchor_counts.get(token, 0)} != {expected}")
    return _adapt(source, source_path, spec, plan)
