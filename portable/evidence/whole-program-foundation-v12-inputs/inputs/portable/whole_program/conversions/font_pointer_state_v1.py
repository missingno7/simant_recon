"""Strict source adapter for the S20 loaded font pointer globals."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
PLAN_PATH = ROOT / "portable/research/font_pointer_state_v1.json"
PLAN_SHA256 = "de14723d20b9ad1b45fbe1c664440ea760c18291c32e5f5f48c74b7c7bf9c1da"
SOURCE_PATH = "src/S20/m39C7.c"
GENERATED_PATH = ROOT / "portable/tests/whole_program/font_pointer_state_v1/inputs/S20_m39C7.generated.c"
OWNER_HEADER = "portable/whole_program/state/font_pointer_state_v1.h"
OWNER_SOURCE = "portable/whole_program/state/font_pointer_state_v1.c"


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_plan() -> dict[str, Any]:
    raw = PLAN_PATH.read_bytes()
    if _sha(raw) != PLAN_SHA256:
        raise ValueError("fixed source-font-pointer plan identity mismatch")
    plan = json.loads(raw.decode("utf-8"))
    for key in ("source", "generated_source", "asm_initializer"):
        item = plan["inputs"][key]
        if _sha((ROOT / item["path"]).read_bytes()) != item["sha256"]:
            raise ValueError(f"pinned font pointer input changed: {item['path']}")
    if plan.get("native_owner") != OWNER_SOURCE or plan.get("native_header") != OWNER_HEADER:
        raise ValueError("font pointer owner route changed")
    return plan


def render_owners(plan: dict[str, Any] | None = None) -> tuple[str, str]:
    plan = load_plan() if plan is None else plan
    if plan != load_plan():
        raise ValueError("caller-supplied font-pointer plan differs from fixed plan")
    header = (ROOT / OWNER_HEADER).read_text(encoding="utf-8")
    source = (ROOT / OWNER_SOURCE).read_text(encoding="utf-8")
    return header, source


def adapt(source: str | bytes, rel: str, plan: dict[str, Any] | None = None,
          original_source: bytes | None = None) -> tuple[str | bytes, dict[str, Any] | None]:
    if Path(rel).as_posix() != SOURCE_PATH:
        raise ValueError(f"unexpected font-pointer source route: {rel}")
    plan = load_plan() if plan is None else plan
    if plan != load_plan():
        raise ValueError("caller-supplied font-pointer plan differs from fixed plan")
    raw = source.encode("latin1") if isinstance(source, str) else source
    generated_pin = raw if original_source is None else original_source
    generated_hash = plan["inputs"]["generated_source"]["sha256"]
    if _sha(generated_pin) != generated_hash:
        raise ValueError("generated S20 source does not match pinned font-loader module")
    text = raw.decode("latin1")
    decls = {
        "db_LoadObject": re.compile(
            r"(?m)^extern char\s+\*\s+\*\s+db_LoadObject\(int16_t object, int16_t kind\);\s*$"),
        "g_3DA8": re.compile(r"(?m)^extern char\s+\*\s+g_3DA8;\s*$"),
        "g_3DA4": re.compile(r"(?m)^extern char\s+\*\s+g_3DA4;\s*$"),
    }
    replacements = {
        "db_LoadObject": "extern SimHandle db_LoadObject(int16_t object, int16_t kind);",
        "g_3DA8": "",
        "g_3DA4": "",
    }
    counts = {}
    for name, pattern in decls.items():
        text, count = pattern.subn(replacements[name], text, count=1)
        if count != 1:
            raise ValueError(f"expected exactly one generated S20 {name} declaration")
        counts[name] = count
    if text.count("db_LoadObject(") < 8 or text.count("g_3DA8 =") != 6 or text.count("g_3DA4 =") != 5:
        raise ValueError("generated S20 loader assignment sites changed")
    prefix = ('#include "portable/whole_program/platform/handles.h"\n'
              f'#include "{OWNER_HEADER}"\n')
    if prefix not in text:
        text = prefix + text
    output = text.encode("latin1")
    ledger = {
        "kind": "SOURCE_FONT_POINTER_STATE_V1",
        "plan": PLAN_PATH.relative_to(ROOT).as_posix(),
        "plan_sha256": PLAN_SHA256,
        "source": SOURCE_PATH,
        "source_sha256": plan["inputs"]["source"]["sha256"],
        "generated_source": GENERATED_PATH.relative_to(ROOT).as_posix(),
        "generated_source_sha256": generated_hash,
        "asm_initializer_sha256": plan["inputs"]["asm_initializer"]["sha256"],
        "removed_source_globals": ["g_3DA4", "g_3DA8"],
        "database_handle_type": "SimHandle (char **); dereference retains the source payload pointer",
        "native_owner": OWNER_SOURCE,
        "native_view_hook": plan["native_driver_view_hook"],
        "output_sha256": _sha(output),
        "claim": plan["claim"],
    }
    return (output if isinstance(source, bytes) else output.decode("latin1")), ledger
