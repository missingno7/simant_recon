"""Strict source-pinned owners for m0798's runtime-assigned triangle dimensions."""
from __future__ import annotations
import hashlib, json, re
from pathlib import Path
from typing import Any
from portable.whole_program.conversions.simulation_state_50f6_preword import replace_identifier_tokens

ROOT = Path(__file__).resolve().parents[3]
PLAN_PATH = ROOT / "portable/research/triangle_runtime_state_v1.json"
PLAN_SHA256 = "6a254a76e08e5d9febbb189474baac68c92de696ba81a6853f1d5f8159de7106"
SOURCE_PATH = "src/root/m0798.c"
SOURCE_SHA256 = "ecf807dc3159f583f6ee3ea8a9f5422650a64bb557d4551e9c97b5dcc7b6a1b8"
OWNER_NAMES = {
    "triWidth": "native_triangle_triWidth_v1",
    "triWidthR": "native_triangle_triWidthR_v1",
    "triWidthL": "native_triangle_triWidthL_v1",
    "triHeight": "native_triangle_triHeight_v1",
}
DECLARATIONS = {
    "triWidth": "extern unsigned far triWidth;",
    "triWidthR": "extern unsigned far triWidthR;",
    "triWidthL": "extern unsigned far triWidthL;",
    "triHeight": "extern unsigned far triHeight;",
}
EXPECTED_USES = {"triWidth": 4, "triWidthR": 1, "triWidthL": 3, "triHeight": 6}

def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def load_plan() -> dict[str, Any]:
    raw = PLAN_PATH.read_bytes()
    if _sha(raw) != PLAN_SHA256:
        raise ValueError("fixed triangle dimensions plan identity mismatch")
    plan = json.loads(raw.decode("utf-8-sig"))
    if (plan.get("schema") != "simant-source-assigned-triangle-dimensions-v1" or
            plan.get("source", {}).get("path") != SOURCE_PATH or
            plan.get("source", {}).get("sha256") != SOURCE_SHA256):
        raise ValueError("fixed triangle dimensions plan fields changed")
    if {row["symbol"]: row["declaration"] for row in plan.get("targets", [])} != DECLARATIONS:
        raise ValueError("fixed triangle dimension declaration inventory changed")
    if plan.get("owner_names") != OWNER_NAMES:
        raise ValueError("fixed triangle dimension owner names changed")
    if plan.get("expected_uses") != EXPECTED_USES:
        raise ValueError("fixed triangle dimension reference counts changed")
    return plan

def _check_plan(plan: dict[str, Any]) -> None:
    if plan != load_plan():
        raise ValueError("caller-supplied triangle dimension plan differs from fixed plan")

def render_owners(plan: dict[str, Any] | None = None) -> tuple[str, str]:
    """Render one zero-initialized native object per uint16_t symbol.

    Static initialization is a C runtime implementation detail; this owner
    plan makes no source initial-zero requirement or historical storage claim.
    """
    plan = load_plan() if plan is None else plan
    _check_plan(plan)
    header = ["/* Runtime-assigned source-shaped dimensions from root:m0798.c. */",
              "#ifndef SIMANT_TRIANGLE_DIMENSIONS_V1_H", "#define SIMANT_TRIANGLE_DIMENSIONS_V1_H",
              "#include <stdint.h>"]
    source = ['/* One native owner per InitTriVars dimension output. */', '#include "triangle_dimensions_v1.h"']
    for target in plan["targets"]:
        name = target["symbol"]
        if target.get("native_type") != "uint16_t":
            raise ValueError(f"unexpected triangle dimension type: {name}")
        header.append(f"extern uint16_t {OWNER_NAMES[name]};")
        source.append(f"uint16_t {OWNER_NAMES[name]};")
    header += ["#endif", ""]
    source.append("")
    return "\n".join(header), "\n".join(source)

def adapt(source: str | bytes, rel: str, plan: dict[str, Any] | None = None) -> tuple[str | bytes, dict[str, Any] | None]:
    """Remove exact m0798 externs and bind the producer/consumers to native words."""
    if Path(rel).as_posix() != SOURCE_PATH:
        raise ValueError(f"unexpected triangle dimensions source route: {rel}")
    plan = load_plan() if plan is None else plan
    _check_plan(plan)
    if _sha((ROOT / SOURCE_PATH).read_bytes()) != SOURCE_SHA256:
        raise ValueError("frozen m0798 source identity mismatch")
    raw = source.encode("latin1") if isinstance(source, str) else source
    if _sha(raw) != SOURCE_SHA256:
        raise ValueError("input m0798 source does not match frozen triangle source")
    text = raw.decode("latin1")
    removed, replacements = {}, {}
    for name, declaration in DECLARATIONS.items():
        pattern = re.compile(r"(?m)^" + re.escape(declaration) + r"\r?\n")
        text, count = pattern.subn("", text)
        if count != 1:
            raise ValueError(f"expected exactly one pinned triangle extern for {name}, got {count}")
        removed[name] = count
        replacements[name] = OWNER_NAMES[name]
    converted, counts = replace_identifier_tokens(text, replacements)
    if counts != EXPECTED_USES:
        raise ValueError(f"m0798 triangle reference counts changed: {counts}")
    converted = '#include "triangle_dimensions_v1.h"\n' + converted
    output = converted.encode("latin1")
    ledger = {
        "kind": "SOURCE_ASSIGNED_TRIANGLE_DIMENSIONS_V1",
        "plan": PLAN_PATH.relative_to(ROOT).as_posix(), "plan_sha256": PLAN_SHA256,
        "source": SOURCE_PATH, "source_sha256": SOURCE_SHA256,
        "removed_extern_declarations": removed,
        "owner_views": replacements, "rewritten_identifier_tokens": counts,
        "output_sha256": _sha(output),
        "claim": "Complete m0798 dimension outputs/consumers now use one typed native uint16_t owner per source variable; no historical zero or communal extent is claimed.",
    }
    return (converted if isinstance(source, str) else output), ledger
