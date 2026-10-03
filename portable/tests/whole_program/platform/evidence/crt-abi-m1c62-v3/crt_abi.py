"""Narrow source-name adapter for the native Microsoft CRT boundary.

This is deliberately separate from the whole-program driver. It rewrites only
reviewed DOS source spellings to the native provider API; it does not claim a
historical source change or emulate DOS INT 24 delivery.
"""
from __future__ import annotations

import hashlib
import re


SUPPORTED = {
    "src/root/m15F8.c", "src/root/m1A28.c", "src/root/m1C62.c",
    "src/S09/m35F5.c", "src/S20/m39F1.c", "src/S23/m39C7.c",
}


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("latin1")).hexdigest()


def adapt(source: str, module_path: str) -> tuple[str, dict]:
    """Convert exact known uses of CRT externals, rejecting shape drift."""
    if module_path not in SUPPORTED:
        raise ValueError(f"CRT ABI adapter is not admitted for {module_path!r}")
    before = _sha(source)
    changes: dict[str, int] = {}

    if "_ctype" in source:
        declaration = "extern unsigned char near _ctype[];"
        if source.count(declaration) != 1:
            raise ValueError("unexpected _ctype declaration shape")
        expected_uses = {"src/root/m1C62.c": 2, "src/S23/m39C7.c": 1}[module_path]
        if source.count("_ctype") != expected_uses + 1:
            raise ValueError("unexpected number of _ctype references")
        source = source.replace(declaration, "", 1)
        source = source.replace("(_ctype + 1)[buf[start]] & 2",
                                "sim_msc_ctype_is_lower_ascii((unsigned char)buf[start])")
        source = source.replace("(_ctype[c + 1] & 2)",
                                "(sim_msc_ctype_is_lower_ascii((unsigned char)c))")
        source = source.replace("_ctype[c + 1] & 2",
                                "sim_msc_ctype_is_lower_ascii((unsigned char)c)")
        if re.search(r"\b_ctype\b", source):
            raise ValueError("unsupported or remaining _ctype access")
        changes["ctype_lower_uses"] = expected_uses

    err_count = source.count("sys_errlist")
    nerr_count = source.count("sys_nerr")
    if err_count:
        source = re.sub(r"\bsys_errlist\b", "sim_sys_errlist", source)
        changes["sys_errlist_names"] = err_count
    if nerr_count:
        source = re.sub(r"\bsys_nerr\b", "sim_sys_nerr", source)
        changes["sys_nerr_names"] = nerr_count

    if "_harderr" in source:
        declaration = re.compile(
            r"(?m)^\s*extern\s+void\s+far\s+_harderr\([^;]*\);\s*$")
        source, removed = declaration.subn("", source, count=1)
        if removed != 1:
            raise ValueError("unexpected _harderr declaration shape")
        source, calls = re.subn(r"\b_harderr\s*\(",
                                "sim_crt_harderr_install(", source)
        if calls != 1:
            raise ValueError("expected one source _harderr registration call")
        changes["harderr_registration_calls"] = calls

    if changes:
        source = '#include "portable/whole_program/platform/crt_abi.h"\n' + source
    if re.search(r"\b(?:_ctype|sys_errlist|sys_nerr|_harderr)\b", source):
        raise ValueError("CRT adapter left an old runtime spelling unresolved")
    return source, {
        "kind": "NATIVE_CRT_ABI_NAME_ADAPTATION",
        "module_path": module_path,
        "input_source_sha256": before,
        "output_source_sha256": _sha(source),
        "changes": changes,
        "provider_header": "portable/whole_program/platform/crt_abi.h",
        "scope": "source-visible DOS error strings, ASCII _LOWER checks, and stored _harderr policy; INT 24 delivery remains retired",
    }
