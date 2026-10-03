"""Source-pinned preword owner adapter for root:m0250's EU tile cache."""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path

from portable.whole_program.conversions.simulation_state_50f6_preword import (
    replace_identifier_tokens,
)

SOURCE_RELATIVE = "src/root/m0250.c"
SOURCE_SHA256 = "bb8a325c543151e09cb173d2194844877805a9e1058d3b24362ff5a7cbd9f61b"
ROOT = Path(__file__).resolve().parents[3]
PLAN_RELATIVE = "portable/research/eu_map_cache_owner_v1.json"
PLAN_SHA256 = "c34c73313d13c9a97d6a73ddf88d0bf1522f4e84f92fa84f56bdac41688eabd5"
DECLARATION = "extern int far fd_50F6_15C4[30][40];\n"
OWNER = "portable_eu_map_cache.rows"
LINEAR = "portable_eu_map_cache.linear"


@dataclass(frozen=True)
class EuMapCacheReceipt:
    source_sha256: str
    output_sha256: str
    removed_extern_declarations: int
    row_view_references: int
    linear_i_views: int
    linear_idx_views: int


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_plan() -> dict:
    raw = (ROOT / PLAN_RELATIVE).read_bytes()
    if _sha(raw) != PLAN_SHA256:
        raise ValueError("fixed EU map cache owner plan identity mismatch")
    plan = json.loads(raw.decode("utf-8"))
    if (plan.get("schema") != "simant-source-shaped-eu-map-cache-owner-v1" or
            plan.get("source", {}).get("path") != SOURCE_RELATIVE or
            plan.get("source", {}).get("sha256") != SOURCE_SHA256 or
            plan.get("native_owner", {}).get("bytes") != 2400 or
            plan.get("native_owner", {}).get("dos_storage_claim") is not False):
        raise ValueError("fixed EU map cache owner plan fields changed")
    return plan


def render_owner(plan: dict | None = None) -> tuple[bytes, bytes]:
    """Render only the exact source shape in the fixed plan."""
    plan = load_plan() if plan is None else plan
    native = plan["native_owner"]
    if native.get("type") != "union { int16_t rows[30][40]; int16_t linear[1200]; }":
        raise ValueError("EU map cache native view shape changed")
    header = '''/* Source-shaped native owner for root:m0250's 30x40 signed edit tile cache.
 * The flat view represents source expressions [0][i], which linearly address
 * cache words beyond the first 40-word row in the DOS implementation. */
#ifndef SIMANT_WHOLE_EU_MAP_CACHE_H
#define SIMANT_WHOLE_EU_MAP_CACHE_H

#include <stdint.h>

typedef union PortableEuMapCache {
    int16_t rows[30][40];
    int16_t linear[30 * 40];
} PortableEuMapCache;

extern PortableEuMapCache portable_eu_map_cache;

_Static_assert(sizeof(PortableEuMapCache) == 2400,
               "EU map cache has exactly 30x40 DOS words");
_Static_assert(sizeof(((PortableEuMapCache *)0)->rows[0]) == 80,
               "EU map cache row stride is 40 DOS words");

#endif
'''.encode("utf-8")
    source = '''#include "eu_map_cache.h"

/* The recovered TU has only an extern source view; native C static storage
 * supplies its initial zero state. Source routines explicitly invalidate the
 * cache to -1 before redraw. No extra gap or padding bytes are modeled. */
PortableEuMapCache portable_eu_map_cache;
'''.encode("utf-8")
    return header, source


def adapt_source(source: bytes, rel: str) -> tuple[bytes, EuMapCacheReceipt]:
    """Remove the single frozen target extern and expose typed native views."""
    if rel.replace("\\", "/") != SOURCE_RELATIVE:
        raise ValueError(f"unexpected EU map cache source route: {rel}")
    load_plan()
    if _sha(source) != SOURCE_SHA256:
        raise ValueError("frozen root:m0250.c identity mismatch")
    try:
        text = source.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("root:m0250.c is not UTF-8") from exc
    if text.count(DECLARATION) != 1:
        raise ValueError("expected exactly one complete int[30][40] extern")
    text = text.replace(DECLARATION,
                        '#include "portable/whole_program/state/eu_map_cache.h"\n', 1)
    text, counts = replace_identifier_tokens(text, {"fd_50F6_15C4": OWNER})
    row_i = re.compile(r"\b" + re.escape(OWNER) + r"\s*\[\s*0\s*\]\s*\[\s*i\s*\]")
    row_idx = re.compile(r"\b" + re.escape(OWNER) + r"\s*\[\s*0\s*\]\s*\[\s*idx\s*\]")
    text, count_i = row_i.subn(f"{LINEAR}[i]", text)
    text, count_idx = row_idx.subn(f"{LINEAR}[idx]", text)
    if counts["fd_50F6_15C4"] != 8:
        raise ValueError(f"cache identifier use count changed: {counts}")
    if count_i != 4 or count_idx != 2:
        raise ValueError(f"linear source access shape changed: i={count_i}, idx={count_idx}")
    if OWNER + "[0][i]" in text or OWNER + "[0][idx]" in text:
        raise ValueError("an unsafe first-row linear access remains")
    output = text.encode("utf-8")
    return output, EuMapCacheReceipt(
        source_sha256=SOURCE_SHA256,
        output_sha256=_sha(output),
        removed_extern_declarations=1,
        row_view_references=counts["fd_50F6_15C4"] - count_i - count_idx,
        linear_i_views=count_i,
        linear_idx_views=count_idx,
    )


def adapt_generated(source: str, rel: str) -> tuple[str, dict[str, int]]:
    """Apply the identical typed-view lowering to one generated m0250 copy.

    The whole-program test pins the generated TU hash in its receipt; production
    composition uses adapt_source at the canonical preword stage above.
    """
    if rel.replace("\\", "/") != "src/root/m0250.c":
        raise ValueError("unexpected generated module route")
    extern = re.compile(r"(?m)^extern int16_t\s+fd_50F6_15C4\[30\]\[40\];\r?\n")
    source, removed = extern.subn(
        '#include "portable/whole_program/state/eu_map_cache.h"\n', source)
    if removed != 1:
        raise ValueError(f"expected one generated cache extern, got {removed}")
    source, counts = replace_identifier_tokens(source, {"fd_50F6_15C4": OWNER})
    row_i = re.compile(r"\b" + re.escape(OWNER) + r"\s*\[\s*0\s*\]\s*\[\s*i\s*\]")
    row_idx = re.compile(r"\b" + re.escape(OWNER) + r"\s*\[\s*0\s*\]\s*\[\s*idx\s*\]")
    source, count_i = row_i.subn(f"{LINEAR}[i]", source)
    source, count_idx = row_idx.subn(f"{LINEAR}[idx]", source)
    if count_i != 4 or count_idx != 2:
        raise ValueError("generated linear cache accesses changed")
    return source, {"removed_extern_declarations": removed,
                    "rewritten_identifier_tokens": counts["fd_50F6_15C4"],
                    "linear_i_views": count_i, "linear_idx_views": count_idx}
