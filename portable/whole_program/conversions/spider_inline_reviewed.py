"""Post-overlay repair for references reintroduced by reviewed m0250 bodies."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path

from portable.whole_program.conversions.spider_inline_source import (
    OWNER,
    SOURCE_RELATIVE,
    SOURCE_SHA256,
    _replace_identifier_c_lexically,
    adapt,
)

ROOT = Path(__file__).resolve().parents[3]
OVERLAY_CATALOG_RELATIVE = "portable/research/whole_program_behavior_sources.json"
OVERLAY_CATALOG_SHA256 = "e29f4fb8aa736c7adca105f846a6928954d95d6fa7b57d45dfcdfd8646d34c81"
EXPECTED_OVERLAYS = {
    "f_0250_1018": ("evidence/behavior/functions/f_0250_1018/contracts/logical-render-v2/module.c",
                    "e41a4ab8c56c0d4923ace8b02027f2471feee049aabe0577588e206e930b4db2"),
    "f_0250_129E": ("evidence/behavior/functions/f_0250_129E/contracts/logical-render-v2/module.c",
                    "e41a4ab8c56c0d4923ace8b02027f2471feee049aabe0577588e206e930b4db2"),
    "DrawBalloons": ("evidence/behavior/functions/DrawBalloons/contracts/logical-render-v1/module.c",
                     "e41a4ab8c56c0d4923ace8b02027f2471feee049aabe0577588e206e930b4db2"),
}


@dataclass(frozen=True)
class ReviewedAdaptReceipt:
    frozen_source_sha256: str
    overlay_catalog_sha256: str
    incoming_reviewed_source_sha256: str
    output_sha256: str
    overlay_count: int
    reintroduced_active_references: int
    resulting_owner_references: int
    owner_symbol: str = OWNER


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _function_span(source: str, name: str) -> tuple[int, int]:
    head = re.compile(r"\bvoid\s+far\s+" + re.escape(name) + r"\s*\([^)]*\)")
    matches = []
    for candidate in head.finditer(source):
        brace_candidate = candidate.end()
        while brace_candidate < len(source) and source[brace_candidate].isspace():
            brace_candidate += 1
        if brace_candidate < len(source) and source[brace_candidate] == "{":
            matches.append(candidate)
    if len(matches) != 1:
        raise ValueError(f"expected one function head for reviewed body {name}")
    start = matches[0].start()
    brace = source.find("{", matches[0].end())
    if brace < 0:
        raise ValueError(f"missing body brace for {name}")
    depth = 0
    i = brace
    state = "code"
    while i < len(source):
        c = source[i]
        n = source[i + 1] if i + 1 < len(source) else ""
        if state == "code":
            if c == "/" and n == "*": state = "block"; i += 2; continue
            if c == "/" and n == "/": state = "line"; i += 2; continue
            if c == '"': state = "string"; i += 1; continue
            if c == "'": state = "char"; i += 1; continue
            if c == "{": depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0: return start, i + 1
            i += 1; continue
        if state == "block":
            if c == "*" and n == "/": state = "code"; i += 2; continue
            i += 1; continue
        if state == "line":
            if c == "\n": state = "code"
            i += 1; continue
        if c == "\\": i += 2; continue
        if (state == "string" and c == '"') or (state == "char" and c == "'"):
            state = "code"
        i += 1
    raise ValueError(f"unterminated function body: {name}")


def _apply_reviewed_overlays(base: str, entries: list[dict]) -> tuple[str, list[dict]]:
    current = base
    rows: list[dict] = []
    selected = [entry for entry in entries
                if entry.get("canonical_translation_unit", {}).get("path") == SOURCE_RELATIVE]
    if {entry.get("function") for entry in selected} != set(EXPECTED_OVERLAYS):
        raise ValueError("m0250 reviewed overlay set changed")
    for entry in selected:
        function = entry["function"]
        expected_path, expected_hash = EXPECTED_OVERLAYS[function]
        canonical = entry["canonical_translation_unit"]
        reviewed = entry["reviewed_tested_source"]
        if canonical.get("file_sha256") != SOURCE_SHA256:
            raise ValueError("overlay catalog canonical source pin changed")
        if (reviewed.get("path") != expected_path or
                reviewed.get("sha256_registered") != expected_hash or
                reviewed.get("body_name") != function):
            raise ValueError(f"reviewed source identity changed for {function}")
        reviewed_path = ROOT / expected_path
        reviewed_bytes = reviewed_path.read_bytes()
        if _sha(reviewed_bytes) != expected_hash:
            raise ValueError(f"reviewed source bytes changed for {function}")
        tested = reviewed_bytes.decode("utf-8")
        t0, t1 = _function_span(tested, function)
        c0, c1 = _function_span(current, function)
        current = current[:c0] + tested[t0:t1] + current[c1:]
        rows.append({"function": function, "path": expected_path,
                     "sha256": expected_hash, "canonical_sha256": SOURCE_SHA256})
    return current, rows


def adapt_reviewed(source: str, rel: str) -> tuple[str, ReviewedAdaptReceipt]:
    """Validate the actual reviewed-overlay stage and repair its two stale refs.

    This is called after reviewed_overlays and before state adaptation. It
    independently re-reads and pins the canonical source, reapplies the
    frozen pre-word adapter and the three registered m0250 overlays, and
    requires byte-for-byte identity with the supplied pipeline result.
    """
    if rel.replace("\\", "/") != SOURCE_RELATIVE:
        raise ValueError("unexpected source route")
    canonical_path = ROOT / SOURCE_RELATIVE
    canonical_raw = canonical_path.read_bytes()
    canonical_hash = _sha(canonical_raw)
    if canonical_hash != SOURCE_SHA256:
        raise ValueError(f"frozen canonical source identity mismatch: {canonical_hash}")

    catalog_path = ROOT / OVERLAY_CATALOG_RELATIVE
    catalog_raw = catalog_path.read_bytes()
    catalog_hash = _sha(catalog_raw)
    if catalog_hash != OVERLAY_CATALOG_SHA256:
        raise ValueError(f"reviewed overlay catalog identity mismatch: {catalog_hash}")
    entries = json.loads(catalog_raw.decode("utf-8"))["entries"]
    base_bytes, base_receipt = adapt(canonical_raw, SOURCE_RELATIVE)
    if base_receipt.source_sha256 != canonical_hash:
        raise ValueError("base source adapter did not retain independent canonical identity")
    expected, overlay_rows = _apply_reviewed_overlays(base_bytes.decode("utf-8"), entries)
    if source != expected:
        raise ValueError("supplied source is not the exact reviewed-overlays pipeline result")
    if len(overlay_rows) != 3:
        raise ValueError("expected the three m0250 registered overlays")

    # The actual DrawBalloons replacement restores exactly two historical
    # symbol tokens after the base adapter renamed the 16 canonical uses.
    source, replaced = _replace_identifier_c_lexically(source, "fd_50F6_1F26", OWNER)
    if replaced != 2:
        raise ValueError(f"reviewed body reintroduced-reference count changed: {replaced}")
    count_owner = source.count(OWNER)
    if count_owner != 16:
        raise ValueError(f"typed owner reference count changed after overlay repair: {count_owner}")
    for anchor in (
        "extern Pnt far fd_50F6_1F26;",
        "extern void far f_2662_1120(int x, int y, Pnt far *buf, int id);",
        "extern void far f_16B5_0033(Pnt far *buf, int mode);",
    ):
        if anchor in source:
            raise ValueError("overlay repair restored an incompatible original declaration")
    return source, ReviewedAdaptReceipt(
        frozen_source_sha256=canonical_hash,
        overlay_catalog_sha256=catalog_hash,
        incoming_reviewed_source_sha256=_sha(expected.encode("utf-8")),
        output_sha256=_sha(source.encode("utf-8")),
        overlay_count=len(overlay_rows),
        reintroduced_active_references=replaced,
        resulting_owner_references=count_owner,
    )
