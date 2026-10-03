"""Restore source-proven DOS AX=0 fastcall arguments in generated NewGame."""
from __future__ import annotations

import hashlib
import re


SOURCE_PATH = "src/S15/m384C.c"
SOURCE_SHA256 = "01b51eecedcd28e2213819572c846a9754039f4a527e6da5e56e57783398bdd5"


def adapt_postword(source: str, rel: str,
                   original_source: str | bytes) -> tuple[str, dict]:
    """Correct only S15 NewGame's two zero-argument fastcall calls.

    SetDefaultWindows opens edit window 0. SetMapPlane ends in UpdateEdit;
    UpdateEdit's open-window path ends in clip_Off, whose original assembly
    explicitly zeros AX. NewGame therefore enters f_22BF_0A65 with AX=0. The
    predicate result is tested at 050D/050F; when it is zero, OR/JNE preserve
    AX=0 into o26 at 0511. Native no-argument calls leave the host's first
    argument register unspecified instead.
    """
    original = (original_source.encode("utf-8") if isinstance(original_source, str)
                else original_source)
    if rel != SOURCE_PATH:
        raise ValueError(f"unregistered NewGame caller: {rel}")
    if hashlib.sha256(original).hexdigest() != SOURCE_SHA256:
        raise ValueError("canonical S15 NewGame source identity drift")

    output = source
    declaration_counts = {}
    call_counts = {}
    for name, result_type in (("f_22BF_0A65", "int16_t"),
                              ("o26_39C7_0000", "void")):
        declaration = re.compile(
            r"(?m)^(\s*extern\s+" + result_type + r"\s+)" +
            re.escape(name) + r"\s*\(\s*void\s*\)\s*;")
        output, declaration_counts[name] = declaration.subn(
            r"\1" + name + r"(int16_t win);", output)
        if name == "f_22BF_0A65":
            call = re.compile(r"(?<![\w])" + re.escape(name) + r"\s*\(\s*\)")
            output, call_counts[name] = call.subn(name + "(0)", output)
        else:
            call = re.compile(r"(?m)^(\s*)" + re.escape(name) +
                              r"\s*\(\s*\)\s*;")
            output, call_counts[name] = call.subn(r"\1" + name + r"(0);", output)
    expected = {"f_22BF_0A65": 1, "o26_39C7_0000": 1}
    if declaration_counts != expected or call_counts != expected:
        raise ValueError("NewGame fastcall call/prototype inventory changed: "
                         f"declarations={declaration_counts} calls={call_counts}")
    if "f_22BF_0A65()" in output or "o26_39C7_0000()" in output:
        raise ValueError("untyped zero-argument window call remains")
    expected_control = ("if (r == 0 && !f_22BF_0A65(0))\n"
                        "        o26_39C7_0000(0);")
    if expected_control not in output:
        raise ValueError("NewGame zero-result control flow changed")
    return output, {
        "kind": "NEWGAME_FASTCALL_WINDOW_ARGUMENTS",
        "source": SOURCE_PATH,
        "canonical_source_sha256": SOURCE_SHA256,
        "changed_declarations": declaration_counts,
        "changed_calls": call_counts,
        "dos_callsite": {
            "function": "NewGame",
            "offsets": {"predicate_call": "0508", "test_ax": "050D",
                         "branch_if_nonzero": "050F", "zoom_call": "0511"},
            "arguments": {"f_22BF_0A65": 0, "o26_39C7_0000": 0},
            "reason": "SetDefaultWindows opens edit window 0. SetMapPlane returns the AX=0 left by UpdateEdit's clip_Off. The predicate's zero result falls through OR AX,AX/JNE, preserving zero into the zoom call.",
        },
        "native_change": "Use the actual int16_t fastcall parameter type and pass the source-proven zero only at these two NewGame call sites.",
        "output_sha256": hashlib.sha256(output.encode("utf-8")).hexdigest(),
    }
