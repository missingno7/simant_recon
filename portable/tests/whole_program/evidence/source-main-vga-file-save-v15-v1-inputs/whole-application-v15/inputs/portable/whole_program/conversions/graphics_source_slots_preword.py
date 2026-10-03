"""Bind source graphics callback/state views to one native owner.

This adapter is intended for generated whole-module TUs before compilation.
It edits declarations only: source algorithm bodies, ordering and expressions
remain unchanged. The owner source is graphics_source_slots.c.
"""
from __future__ import annotations

import re


HEADER = '#include "portable/whole_program/platform/graphics_source_slots.h"\n'
OWNER_SOURCE = "portable/whole_program/platform/graphics_source_slots.c"
OWNER_HEADER = "portable/whole_program/platform/graphics_source_slots.h"

_VIEWS = {
    "root_m205F.c": {
        "fd_50F6_37EE", "fd_50F6_37EA", "fd_50F6_3B58", "fd_50F6_37E6",
    },
    "root_m0250.c": {
        "fd_50F6_37D6", "fd_50F6_37DE", "fd_50F6_37EA",
        "fd_50F6_37E6", "fd_50F6_37EE",
    },
    "root_m2662.c": {
        "fd_50F6_37EE", "fd_50F6_37EA", "fd_50F6_3B58",
    },
    "root_m1CE2.c": {"fd_50F6_37EA"},
    "root_m0798.c": {
        "fd_50F6_37F2", "fd_50F6_37F6", "fd_50F6_37FC", "fd_50F6_37FA",
    },
}

_SOURCE_FILES = {
    "src/root/m205F.c": "root_m205F.c",
    "src/root/m0250.c": "root_m0250.c",
    "src/root/m2662.c": "root_m2662.c",
    "src/root/m1CE2.c": "root_m1CE2.c",
    "src/root/m0798.c": "root_m0798.c",
}

_CALLBACK_PROTOTYPES = {
    "o00_35A6_02FD": "extern void o00_35A6_02FD(void *, void *, void *, void *);",
    "o01_32B5_0152": "extern void o01_32B5_0152(void *, void *, void *, void *);",
    "o03_3258_05A7": "extern void o03_3258_05A7(void *, void *, void *, void *);",
    "o00_35A6_0007": "extern void o00_35A6_0007(void *, void *, int16_t, int16_t);",
    "o01_32B5_000F": "extern void o01_32B5_000F(void *, void *, int16_t, int16_t);",
    "o03_3258_040D": "extern void o03_3258_040D(void *, void *, int16_t, int16_t);",
    "o00_35A6_0177": "extern void o00_35A6_0177(void *, void *, int16_t, int16_t);",
    "o01_32B5_00AA": "extern void o01_32B5_00AA(void *, void *, int16_t, int16_t);",
    "o03_3258_04CE": "extern void o03_3258_04CE(void *, void *, int16_t, int16_t);",
    "o00_35A6_0406": "extern void o00_35A6_0406(void *, int16_t);",
    "o01_32B5_024F": "extern void o01_32B5_024F(void *, int16_t);",
    "o03_3258_175F": "extern void o03_3258_175F(void *, int16_t);",
}


def adapt_generated_tu(filename: str, source: str) -> str:
    """Replace source-local extern views with the canonical typed owner view."""
    normalized = _SOURCE_FILES.get(filename, filename)
    if normalized not in _VIEWS:
        return source
    lines = source.splitlines(keepends=True)
    required = set(_VIEWS[normalized])
    removed: set[str] = set()
    kept: list[str] = []
    for line in lines:
        match = re.match(r"\s*extern\b[^\n]*\b(fd_50F6_[0-9A-Fa-f]{4})\b[^\n]*;\s*(?:\r?\n)?$", line)
        if match and match.group(1) in required:
            removed.add(match.group(1))
            continue
        kept.append(line)
    missing = required - removed
    if missing:
            raise ValueError(f"{filename}: expected source declarations not found: {sorted(missing)}")
    text = "".join(kept)
    if normalized == "root_m205F.c":
        for symbol, prototype in _CALLBACK_PROTOTYPES.items():
            pattern = re.compile(
                rf"(?m)^extern\s+void\s+(?:far\s+)?{re.escape(symbol)}\s*\([^;]*\);$"
            )
            text, count = pattern.subn(prototype, text, count=1)
            if count != 1:
                raise ValueError(f"{filename}: callback declaration missing/changed: {symbol}")
    if HEADER not in text:
        text = HEADER + text
    if normalized in _VIEWS:
        from portable.tools.whole_program import function_heads

        before_order = [head["name"] for head in function_heads(source)]
        after_order = [head["name"] for head in function_heads(text)]
        if before_order != after_order:
            raise ValueError(f"{filename}: callback adaptation changed source function order")
    return text


def adapt_generated_modules(sources: dict[str, str]) -> dict[str, str]:
    """Adapt source or generated modules and pass unrelated text through."""
    return {name: adapt_generated_tu(name, source) for name, source in sources.items()}


def adapt(source: str, rel: str) -> tuple[str, dict | None]:
    """Central-generator adapter API: source/rel -> adapted source + ledger."""
    output = adapt_generated_tu(rel, source)
    if output == source:
        return source, None
    normalized = _SOURCE_FILES.get(rel, rel)
    return output, {
        "kind": "NATIVE_SOURCE_GRAPHICS_CALLBACK_AND_RESOURCE_SLOTS",
        "owner_header": OWNER_HEADER,
        "owner_source": OWNER_SOURCE,
        "module": normalized,
        "replaced_source_extern_views": sorted(_VIEWS[normalized]),
        "callback_prototypes": sorted(_CALLBACK_PROTOTYPES) if normalized == "root_m205F.c" else [],
        "source_bodies_and_order_preserved": True,
        "changes": "One native typed callback/handle/Rect owner; source selection and calls remain in original module bodies",
        "claim": "Native pointer representation and owner binding only; no new DOS or renderer-equivalence claim",
    }


def render_native_owner_sources() -> list[str]:
    """Return the one source file that must be compiled to provide these globals."""
    return [OWNER_SOURCE]


def render_native_owner_headers() -> list[str]:
    """Return shared declarations required before compiling adapted consumers."""
    return [OWNER_HEADER]
