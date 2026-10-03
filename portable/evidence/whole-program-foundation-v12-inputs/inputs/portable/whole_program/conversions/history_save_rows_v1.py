"""Strict adapter for S09's ten SaveRec history-byte views into V6 owners."""
from __future__ import annotations
import hashlib
import json
import re
from pathlib import Path
from typing import Any

from portable.whole_program.conversions.simulation_state_50f6_preword import replace_identifier_tokens

ROOT = Path(__file__).resolve().parents[3]
PLAN_PATH = ROOT / "portable/research/history_save_rows_v1.json"
PLAN_SHA256 = "e28b89983769947611f13304f2c0b239169da568c47f6abb2e8a3ba7a52f8c15"
SOURCE_PATH = "src/S09/m35F5.c"
SOURCE_SHA256 = "028e1575990d5d45233f9102a0d2a060810349bd2f1297182c4af435ecbe912a"
V6_PLAN_PATH = ROOT / "portable/research/whole_program_simulation_state_50f6_v6.json"
V6_PLAN_SHA256 = "47a5940df5784fccd41b3bc4328d5a4c374d6c5693f6a1e34f65514049f045e5"
V6_HEADER_SHA256 = "5c87fe9e12f755eee3e1beeaab9b2478bb5ec95782b031b805ecb828c8c6de1f"
EXPECTED_ROWS = (
    ("fd_50F6_08F0", 2, 64), ("fd_50F6_0626", 2, 64), ("fd_50F6_073C", 2, 64),
    ("fd_50F6_0516", 2, 64), ("fd_50F6_0A0A", 2, 64), ("fd_50F6_0856", 2, 64),
    ("fd_50F6_0970", 2, 64), ("fd_50F6_06AE", 2, 64), ("fd_50F6_07CE", 2, 64),
    ("fd_50F6_05A0", 2, 64),
)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_plan() -> dict[str, Any]:
    raw = PLAN_PATH.read_bytes()
    if _sha(raw) != PLAN_SHA256:
        raise ValueError("fixed history SaveRec plan identity mismatch")
    plan = json.loads(raw.decode("utf-8-sig"))
    if (plan.get("schema") != "simant-source-bounded-history-save-table-v1" or
            plan.get("source", {}).get("path") != SOURCE_PATH or
            plan.get("source", {}).get("sha256") != SOURCE_SHA256 or
            plan.get("owner_plan", {}).get("path") != V6_PLAN_PATH.relative_to(ROOT).as_posix() or
            plan.get("owner_plan", {}).get("sha256") != V6_PLAN_SHA256 or
            plan.get("owner_plan", {}).get("header_sha256") != V6_HEADER_SHA256 or
            plan.get("save_table", {}).get("symbol") != "fd_4E4B_0000"):
        raise ValueError("fixed history SaveRec plan fields changed")
    rows = tuple((str(n), int(size), int(count)) for n, size, count in plan.get("save_table", {}).get("rows", ()))
    if rows != EXPECTED_ROWS:
        raise ValueError("fixed history SaveRec row list/order changed")
    if _sha(V6_PLAN_PATH.read_bytes()) != V6_PLAN_SHA256:
        raise ValueError("V6 history owner plan identity mismatch")
    v6 = json.loads(V6_PLAN_PATH.read_text(encoding="utf-8"))
    v6_histories = {item["symbol"] for item in v6["targets"] if item["kind"] == "history-64-signed-words"}
    if not set(name for name, _, _ in rows) <= v6_histories:
        raise ValueError("SaveRec target absent from V6 storage owners")
    return plan


def adapt(source: str | bytes, rel: str, original_source: bytes | None = None) -> tuple[str | bytes, dict[str, Any] | None]:
    """Retarget only the pinned ten source SaveRec byte-pointer views."""
    if Path(rel).as_posix() != SOURCE_PATH:
        raise ValueError(f"unexpected history SaveRec source route: {rel}")
    plan = load_plan()
    # `source` may already contain the separate, audited file-selector native
    # policy adapter; the canonical file hash below anchors its original TU.
    canonical = (ROOT / SOURCE_PATH).read_bytes()
    if _sha(canonical) != SOURCE_SHA256:
        raise ValueError("frozen S09 SaveRec source identity mismatch")
    raw = source.encode("latin1") if isinstance(source, str) else source
    pinned_original = raw if original_source is None else original_source
    if _sha(pinned_original) != SOURCE_SHA256:
        raise ValueError("input S09 source does not match the frozen SaveRec source")
    try:
        text = raw.decode("latin1")
    except UnicodeDecodeError as exc:
        raise ValueError("S09 source is not byte-preserving Latin-1") from exc

    decl_names = []
    for name, _, _ in EXPECTED_ROWS:
        declaration = f"extern unsigned char far {name}[];"
        if text.count(declaration) != 1:
            raise ValueError(f"expected exactly one exact S09 history extern: {name}")
        decl_names.append(name)
    row_pattern = re.compile(
        r"(?m)^\s*\{\s*(\d+)\s*,\s*(\d+)\s*,\s*\(void\s+far\s*\*\)\s*&([A-Za-z_]\w*)\s*\}\s*,\s*$"
    )
    rows = tuple((name, int(size), int(count)) for size, count, name in row_pattern.findall(text)
                 if name in {n for n, _, _ in EXPECTED_ROWS})
    if rows != EXPECTED_ROWS:
        raise ValueError(f"S09 SaveRec history rows/order changed: {rows}")
    for name in decl_names:
        pattern = re.compile(r"(?m)^extern unsigned char far " + re.escape(name) + r"\[\];\r?\n")
        text, removed = pattern.subn("", text)
        if removed != 1:
            raise ValueError(f"failed to remove exact S09 history extern: {name}")
    replacements = {name: f"native_sim_state_{name}.raw_bytes" for name, _, _ in EXPECTED_ROWS}
    converted, counts = replace_identifier_tokens(text, replacements)
    expected_counts = {name: 1 for name, _, _ in EXPECTED_ROWS}
    if counts != expected_counts:
        raise ValueError(f"unexpected S09 history-token uses after extern removal: {counts}")
    converted = '#include "simulation_state_50f6.h"\n' + converted
    output = converted.encode("latin1")
    receipt = {
        "kind": "SOURCE_BOUNDED_HISTORY_SAVE_ROWS_V1",
        "plan": PLAN_PATH.relative_to(ROOT).as_posix(),
        "plan_sha256": PLAN_SHA256,
        "source": SOURCE_PATH,
        "source_sha256": SOURCE_SHA256,
        "v6_owner_plan_sha256": V6_PLAN_SHA256,
        "v6_owner_header_sha256": V6_HEADER_SHA256,
        "save_table_symbol": "fd_4E4B_0000",
        "rows_in_source_order": [[n, s, c] for n, s, c in rows],
        "removed_exact_externs": decl_names,
        "rewritten_pointer_references": counts,
        "output_sha256": _sha(output),
        "claim": "The ten exact {2,64} S09 serialization rows now point at existing V6 raw-byte history owners; SaveRec order and one-owner storage are retained.",
        "nonclaims": ["No historical communal BSS size/gap is inferred.", "No full save-file equivalence or gameplay equivalence is asserted."],
    }
    return (converted if isinstance(source, str) else output), receipt
