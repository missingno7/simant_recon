"""Strict source-pinned native binding for S27's history pointer table.

The V6 owner plan already owns the ten complete history arrays. This adapter
only retargets d3D57's 20 static pointers to those owners' byte overlay view.
It intentionally preserves the table's member order and repeated aliases.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from portable.whole_program.conversions.simulation_state_50f6_preword import replace_identifier_tokens

ROOT = Path(__file__).resolve().parents[3]
PLAN_PATH = ROOT / "portable/research/history_pointer_table_v1.json"
PLAN_SHA256 = "d8589a822ba7aa6795c04c21fc8d63e02d3183cdd37c8e075c75aa36fe50a4ed"
SOURCE_PATH = "src/data/d3D57.c"
SOURCE_SHA256 = "983251ad55176050efcdea33c62f0a34a93686474b0de4b2bdde6c6c808716f5"
V6_PLAN_PATH = ROOT / "portable/research/whole_program_simulation_state_50f6_v6.json"
V6_PLAN_SHA256 = "47a5940df5784fccd41b3bc4328d5a4c374d6c5693f6a1e34f65514049f045e5"
V6_HEADER_SHA256 = "5c87fe9e12f755eee3e1beeaab9b2478bb5ec95782b031b805ecb828c8c6de1f"
TABLE_MEMBERS = (
    "fd_50F6_0516", "fd_50F6_0626", "fd_50F6_073C", "fd_50F6_0856", "fd_50F6_08F0",
    "fd_50F6_05A0", "fd_50F6_06AE", "fd_50F6_07CE", "fd_50F6_0970", "fd_50F6_0A0A",
    "fd_50F6_05A0", "fd_50F6_06AE", "fd_50F6_07CE", "fd_50F6_0856", "fd_50F6_0A0A",
    "fd_50F6_0516", "fd_50F6_0626", "fd_50F6_073C", "fd_50F6_0A0A", "fd_50F6_0970",
)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_plan() -> dict[str, Any]:
    raw = PLAN_PATH.read_bytes()
    if not PLAN_SHA256 or _sha(raw) != PLAN_SHA256:
        raise ValueError("fixed history pointer-table plan identity mismatch")
    plan = json.loads(raw.decode("utf-8-sig"))
    if plan.get("schema") != "simant-source-bounded-history-pointer-table-v1":
        raise ValueError("unexpected history pointer-table plan schema")
    if (plan.get("source", {}).get("path") != SOURCE_PATH or
            plan.get("source", {}).get("sha256") != SOURCE_SHA256 or
            plan.get("owner_plan", {}).get("path") != V6_PLAN_PATH.relative_to(ROOT).as_posix() or
            plan.get("owner_plan", {}).get("sha256") != V6_PLAN_SHA256 or
            plan.get("owner_plan", {}).get("header_sha256") != V6_HEADER_SHA256 or
            plan.get("table", {}).get("symbol") != "fd_3D57_082A" or
            tuple(plan.get("table", {}).get("members", ())) != TABLE_MEMBERS):
        raise ValueError("fixed history pointer-table plan fields changed")
    if _sha(V6_PLAN_PATH.read_bytes()) != V6_PLAN_SHA256:
        raise ValueError("V6 history owner plan identity mismatch")
    return plan


def adapt(source: str | bytes, rel: str) -> tuple[str | bytes, dict[str, Any] | None]:
    """Rewrite only d3D57's exact 20-member table to V6 raw-byte owner views."""
    if Path(rel).as_posix() != SOURCE_PATH:
        raise ValueError(f"unexpected history pointer-table route: {rel}")
    plan = load_plan()
    raw = source.encode("latin1") if isinstance(source, str) else source
    if _sha(raw) != SOURCE_SHA256 or _sha((ROOT / SOURCE_PATH).read_bytes()) != SOURCE_SHA256:
        raise ValueError("frozen src/data/d3D57.c identity mismatch")
    try:
        text = raw.decode("latin1")
    except UnicodeDecodeError as exc:
        raise ValueError("d3D57 source is not byte-preserving Latin-1") from exc

    members = plan["table"]["members"]
    table = re.compile(
        r"(?ms)^(?P<decl>void\s+far\s*\*\s*far\s+fd_3D57_082A\s*\[\s*20\s*\]\s*=\s*\{)"
        r"(?P<body>.*?)^(?P<end>\s*\};)"
    )
    match = table.search(text)
    if not match or len(table.findall(text)) != 1:
        raise ValueError("expected exactly one source-shaped fd_3D57_082A[20] table")
    body_names = tuple(re.findall(r"\bfd_50F6_[0-9A-Fa-f]{4}\b", match.group("body")))
    if body_names != TABLE_MEMBERS:
        raise ValueError(f"history pointer table member/order changed: {body_names}")

    externs = []
    for name in sorted(set(members)):
        pattern = re.compile(r"(?m)^extern\s+unsigned\s+char\s+far\s+" + re.escape(name) + r"\s*\[\s*\]\s*;\r?\n")
        text, count = pattern.subn("", text)
        if count != 1:
            raise ValueError(f"expected one exact extern for {name}, got {count}")
        externs.append(name)

    replacements = {name: f"native_sim_state_{name}.raw_bytes" for name in set(members)}
    converted, counts = replace_identifier_tokens(text, replacements)
    # One initializer reference per table member; declarations were removed above.
    expected_counts = {name: members.count(name) for name in replacements}
    if counts != expected_counts:
        raise ValueError(f"unexpected history-token use counts after extern removal: {counts}, expected {expected_counts}")
    converted = '#include "simulation_state_50f6.h"\n' + converted
    out_bytes = converted.encode("latin1")
    receipt = {
        "kind": "SOURCE_BOUNDED_HISTORY_POINTER_TABLE_V1",
        "plan": PLAN_PATH.relative_to(ROOT).as_posix(),
        "plan_sha256": _sha(PLAN_PATH.read_bytes()),
        "source": SOURCE_PATH,
        "source_sha256": SOURCE_SHA256,
        "v6_owner_plan_sha256": V6_PLAN_SHA256,
        "v6_owner_header_sha256": V6_HEADER_SHA256,
        "table_symbol": "fd_3D57_082A",
        "table_member_order": list(members),
        "table_member_counts": dict(sorted(expected_counts.items())),
        "removed_exact_externs": externs,
        "rewritten_table_references": counts,
        "output_sha256": _sha(out_bytes),
        "claim": "Source-declared static pointer table now refers to the existing V6 raw-byte history owners; order, duplicate aliases, and one-owner storage are preserved.",
        "nonclaims": ["No historical OMF communal size or gap is inferred.", "No pixel, gameplay, or DOS/native serialized-image equivalence is asserted."],
    }
    return (converted if isinstance(source, str) else out_bytes), receipt
