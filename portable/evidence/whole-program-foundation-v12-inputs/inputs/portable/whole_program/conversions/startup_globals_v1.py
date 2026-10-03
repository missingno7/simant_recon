"""Strict multi-TU adapter for source-derived fresh startup state."""
from __future__ import annotations
import hashlib, json, re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
PLAN_PATH = ROOT / "portable/research/startup_globals_v1.json"
PLAN_SHA256 = "f5ba13c392b7cac658dd0506ff9619e04ccbd8b3067ad4dc2a5773c039b4eb17"
HEADER = "portable/whole_program/state/startup_globals_v1.h"
SOURCE = "portable/whole_program/state/startup_globals_v1.c"
MODULES = {
    "src/root/m00F8.c": {
        "fd_55B3_2A36": (r"extern\s+char\s+\*\s+fd_55B3_2A36\s*;", 1),
        "fd_55B3_2A3A": (r"extern\s+char\s+\*\s+fd_55B3_2A3A\s*;", 1),
    },
    "src/root/m015B.c": {"fd_55B3_2A42": (r"extern\s+Point\s+fd_55B3_2A42\s*;", 1)},
    "src/S22/m39C7.c": {"fd_55B3_2A42": (r"extern\s+int16_t\s+fd_55B3_2A42\s*\[\s*2\s*\]\s*;", 1)},
    "src/S07/m35F5.c": {"fd_50F6_0B0A": (r"extern\s+char\s+fd_50F6_0B0A\s*\[\s*\]\s*;", 1)},
    "src/root/m0250.c": {"fd_50F6_0F7A": (r"extern\s+int16_t\s+fd_50F6_0F7A\s*;", 1)},
    "src/S22/m3BBD.c": {"fd_50F6_106C": (r"extern\s+uint8_t\s+fd_50F6_106C\s*;", 1)},
    "src/root/m1C62.c": {"g_8CCB": (r"extern\s+char\s+g_8CCB\s*;", 1)},
}

def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def load_plan() -> dict[str, Any]:
    raw = PLAN_PATH.read_bytes()
    if _sha(raw) != PLAN_SHA256:
        raise ValueError("fixed startup-global plan identity mismatch")
    plan = json.loads(raw.decode("utf-8"))
    for rel, expected in plan["inputs"]["modules"].items():
        if _sha((ROOT / rel).read_bytes()) != expected:
            raise ValueError(f"pinned startup-global source changed: {rel}")
    init = plan["inputs"]["asm_initializer"]
    if _sha((ROOT / init["path"]).read_bytes()) != init["sha256"]:
        raise ValueError("pinned startup-global original ASM changed")
    if plan.get("owner_header") != HEADER or plan.get("owner_source") != SOURCE:
        raise ValueError("startup-global owner route changed")
    return plan

def render_owners(plan: dict[str, Any] | None = None) -> tuple[str, str]:
    plan = load_plan() if plan is None else plan
    if plan != load_plan():
        raise ValueError("caller-supplied startup-global plan differs from fixed plan")
    return ((ROOT / HEADER).read_text(encoding="ascii"),
            (ROOT / SOURCE).read_text(encoding="ascii"))

def adapt(source: str | bytes, rel: str, plan: dict[str, Any] | None = None,
          original_source: bytes | None = None) -> tuple[str | bytes, dict[str, Any]]:
    rel = Path(rel).as_posix()
    if rel not in MODULES:
        raise ValueError(f"unexpected startup-global module route: {rel}")
    plan = load_plan() if plan is None else plan
    if plan != load_plan():
        raise ValueError("caller-supplied startup-global plan differs from fixed plan")
    canonical = (ROOT / rel).read_bytes()
    pinned = canonical if original_source is None else original_source
    if _sha(pinned) != plan["inputs"]["modules"][rel]:
        raise ValueError(f"original source module does not match startup-global pin: {rel}")
    raw = source.encode("latin1") if isinstance(source, str) else source
    text = raw.decode("latin1")
    removed: dict[str, int] = {}
    for symbol, (decl_pattern, expected_count) in MODULES[rel].items():
        text, count = re.subn(r"(?m)^" + decl_pattern + r"\s*$", "", text)
        if count != expected_count:
            raise ValueError(f"expected {expected_count} generated declaration for {symbol} in {rel}; got {count}")
        removed[symbol] = count
    if rel == "src/root/m015B.c":
        for field, index in (("x", 0), ("y", 1)):
            text, count = re.subn(r"\bfd_55B3_2A42\s*\.\s*" + field + r"\b",
                                  f"fd_55B3_2A42[{index}]", text)
            if count != 1:
                raise ValueError(f"expected one Point.{field} origin consumer; got {count}")
    if rel == "src/S22/m39C7.c":
        if text.count("fd_55B3_2A42[0]") != 1 or text.count("fd_55B3_2A42[1]") != 1:
            raise ValueError("expected the two indexed shared-origin consumers")
    out = '#include "portable/whole_program/state/startup_globals_v1.h"\n' + text
    result = out.encode("latin1") if isinstance(source, bytes) else out
    ledger = {
        "kind": "SOURCE_STARTUP_GLOBALS_V1", "plan": PLAN_PATH.relative_to(ROOT).as_posix(),
        "plan_sha256": PLAN_SHA256, "source": rel,
        "source_sha256": plan["inputs"]["modules"][rel],
        "removed_source_externs": removed,
        "native_header": HEADER, "native_owner": SOURCE,
        "native_views": {"fd_55B3_2A42": "one int16_t[2] storage; root Point.x/y accesses become indices"},
        "initial_values": plan["values"],
        "claim": plan["claim"], "output_sha256": _sha(out.encode("latin1")),
    }
    return result, ledger
