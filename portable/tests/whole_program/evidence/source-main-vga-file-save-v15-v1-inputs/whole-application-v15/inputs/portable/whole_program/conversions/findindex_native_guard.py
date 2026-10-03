"""Strict host-safety adaptation of the reviewed DOS FindIndex body.

The transformation preserves the reviewed binary search and its cursor-pointer
assignment, then returns NULL before reading index[count]. It is intentionally
not written into canonical source or the generated profile by this helper.
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

REVIEWED_PATH = "evidence/behavior/functions/FindIndex/module.c"
REVIEWED_MODULE_SHA256 = "1af5252fe8449eeca44b4099fe4a4bd1ff5ab24521c7a888253adfdd4554ac5a"
REVIEWED_BODY_SHA256 = "676aae0b691028a2a6fbe40ed5c0da91895bdf34a1615d7fc4ddea26812171f0"
CANONICAL_PATH = "src/root/m1986.c"
CANONICAL_MODULE_SHA256 = "c6278f0729f2c7e8c1b36c423c7c4ab081573b8c26a8604ab1ee78036365fc96"
GUARD = "if (fd_50F6_3956 == fd_50F6_3958[db].indexHeader.count) return 0L;"
CURSOR_ASSIGNMENT = "fd_50F6_3952 = &fd_50F6_3958[db].index[fd_50F6_3956];"
DOS_SIGNATURE = "IndexEntry far * far FindIndex(int db, int id, int kind)"
HOST_SIGNATURE = "IndexEntry *FindIndex(int16_t db, int16_t id, int16_t kind)"
CANONICAL_BODY_SHA256 = "d9d0a760a01225e6f6fa9cc79ac7ab73e260038d89d9c2ee721c7b0331a318ef"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _find_one_function(source: str) -> dict:
    # Import lazily: whole_program imports this adapter as part of its conversion
    # set, so a module-scope import would create a generator import cycle.
    from portable.tools.whole_program import function_heads

    found = [f for f in function_heads(source) if f["name"] == "FindIndex"]
    if len(found) != 1:
        raise ValueError(f"expected one code FindIndex definition, got {len(found)}")
    return found[0]


def _reviewed_body(source: str) -> tuple[dict, str]:
    head = _find_one_function(source)
    body = source[head["start"]:head["end"]]
    if digest(body.encode("latin1")) != REVIEWED_BODY_SHA256:
        raise ValueError("reviewed FindIndex code body hash changed")
    if head["signature"] != DOS_SIGNATURE:
        raise ValueError(f"reviewed FindIndex signature changed: {head['signature']!r}")
    if body.count(CURSOR_ASSIGNMENT) != 1:
        raise ValueError("expected the one-past cursor assignment exactly once")
    if "if (fd_50F6_3952->id == id && fd_50F6_3952->kind == kind)" not in body:
        raise ValueError("reviewed return predicate changed")
    return head, body


def adapt_whole_source(source: str, module_path: str = CANONICAL_PATH) -> tuple[str, dict]:
    """Guard FindIndex in a canonical TU after reviewed behavior overlays.

    The canonical file identity and the reviewed function-body identity are
    checked independently. Replacing the reviewed body with the canonical body
    must reproduce the exact pinned canonical module, proving that the input is
    precisely that TU plus the already reviewed overlay(s).
    """
    if module_path != CANONICAL_PATH:
        raise ValueError("only the pinned canonical root/m1986.c TU is accepted")
    canonical_path = ROOT / CANONICAL_PATH
    canonical_bytes = canonical_path.read_bytes()
    if digest(canonical_bytes) != CANONICAL_MODULE_SHA256:
        raise ValueError("canonical FindIndex translation-unit identity changed")
    canonical = canonical_bytes.decode("latin1")
    reviewed_head, reviewed_body = _reviewed_body(source)
    canonical_head = _find_one_function(canonical)
    canonical_body = canonical[canonical_head["start"]:canonical_head["end"]]
    if digest(canonical_body.encode("latin1")) != CANONICAL_BODY_SHA256:
        raise ValueError("canonical FindIndex body identity changed")
    restored = (source[:reviewed_head["start"]] + canonical_body +
                source[reviewed_head["end"]:])
    if digest(restored.encode("latin1")) != CANONICAL_MODULE_SHA256:
        raise ValueError("input TU is not the pinned canonical source plus reviewed FindIndex body")
    guarded = reviewed_body.replace(CURSOR_ASSIGNMENT,
                                    CURSOR_ASSIGNMENT + "\n    " + GUARD, 1)
    if guarded.count(GUARD) != 1:
        raise ValueError("guard insertion failed closed")
    output = source[:reviewed_head["start"]] + guarded + source[reviewed_head["end"]:]
    return output, {
        "lane": "whole-module native safety adaptation",
        "module_path": CANONICAL_PATH,
        "canonical_module_sha256": CANONICAL_MODULE_SHA256,
        "canonical_body_sha256": CANONICAL_BODY_SHA256,
        "reviewed_module_sha256": REVIEWED_MODULE_SHA256,
        "reviewed_body_sha256": REVIEWED_BODY_SHA256,
        "guard": GUARD,
        "only_findindex_body_changed": True,
    }


def adapt_dos_source(source: str, *, module_path: str = REVIEWED_PATH) -> tuple[str, dict]:
    """Return a whole-module candidate with only the reviewed target body replaced."""
    if module_path != REVIEWED_PATH:
        raise ValueError("only the pinned reviewed FindIndex module is accepted")
    if digest(source.encode("latin1")) != REVIEWED_MODULE_SHA256:
        raise ValueError("reviewed FindIndex module snapshot hash changed")
    _reviewed_head, body = _reviewed_body(source)
    guarded = body.replace(CURSOR_ASSIGNMENT,
                           CURSOR_ASSIGNMENT + "\n    " + GUARD, 1)
    if guarded.count(GUARD) != 1:
        raise ValueError("guard insertion failed closed")
    type_end = source.find("extern OpenDBRec far fd_50F6_3958[];")
    if type_end < 0:
        raise ValueError("reviewed OpenDBRec declarations missing")
    preamble = source[:type_end]
    declarations = (
        "extern OpenDBRec far fd_50F6_3958[];\n"
        "extern int far fd_50F6_3956;\n"
        "extern IndexEntry far * far fd_50F6_3952;\n\n"
    )
    # Compile only this entry for the DOS negative control, avoiding unrelated
    # module string constants/data while retaining source ABI declarations.
    output = preamble + declarations + guarded + "\n"
    return output, {
        "lane": "DOS-compiler negative control",
        "reviewed_module_sha256": REVIEWED_MODULE_SHA256,
        "reviewed_body_sha256": REVIEWED_BODY_SHA256,
        "guard": GUARD,
        "compiled_scope": "reviewed FindIndex body only; source ABI declarations retained",
    }


def adapt_host_source(source: str, *, module_path: str = REVIEWED_PATH) -> tuple[str, dict]:
    """Emit a native helper using shared host-width DB records and safe guard."""
    if module_path != REVIEWED_PATH:
        raise ValueError("only the pinned reviewed FindIndex module is accepted")
    if digest(source.encode("latin1")) != REVIEWED_MODULE_SHA256:
        raise ValueError("reviewed FindIndex module snapshot hash changed")
    _head, body = _reviewed_body(source)
    guarded = body.replace(CURSOR_ASSIGNMENT,
                           CURSOR_ASSIGNMENT + "\n    " + GUARD, 1)
    signature_end = guarded.find("{")
    if signature_end < 0:
        raise ValueError("function body opening brace missing")
    old_signature = guarded[:signature_end].strip()
    if old_signature != DOS_SIGNATURE:
        raise ValueError("cannot convert unexpected reviewed signature")
    guarded = HOST_SIGNATURE + "\n" + guarded[signature_end:]
    output = '#include "portable/whole_program/types/database.h"\n' + guarded + "\n"
    if output.count(GUARD) != 1 or output.count(CURSOR_ASSIGNMENT) != 1:
        raise ValueError("host guard output failed structural validation")
    terminal_compare = output.rfind("if (fd_50F6_3952->id == id")
    if output.index(CURSOR_ASSIGNMENT) > output.index(GUARD) or \
            terminal_compare < 0 or output.index(GUARD) > terminal_compare:
        raise ValueError("guard must follow cursor assignment and precede one-past field access")
    return output, {
        "lane": "native host safety adapter",
        "reviewed_module_sha256": REVIEWED_MODULE_SHA256,
        "reviewed_body_sha256": REVIEWED_BODY_SHA256,
        "shared_record_header": "portable/whole_program/types/database.h",
        "guard": GUARD,
        "cursor_assignment_preserved_before_guard": True,
        "native_addresses_unmodified": True,
    }


def adapt_file(source_path: Path, *, lane: str) -> tuple[str, dict]:
    source = source_path.read_text(encoding="latin1")
    if lane == "host":
        return adapt_host_source(source, module_path=source_path.relative_to(ROOT).as_posix())
    if lane == "dos":
        return adapt_dos_source(source, module_path=source_path.relative_to(ROOT).as_posix())
    raise ValueError(f"unknown lane: {lane}")
