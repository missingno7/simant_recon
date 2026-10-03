"""Lift the root:m1FD2 Rect/Timer declarations into the shared native type.

Only the exact frozen source declaration shape is accepted.  No Timer global
or function body is regenerated here: the original g_5FF2 initializer and
all m1FD2 function bodies remain in their original TU/order.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import re


SOURCE_PATH = "src/root/m1FD2.c"
SOURCE_SHA256 = "f4359bdaf4cfc0fe326a54cf8a1eacb9ba3098b710bf2a561b3d0f48569bf6d8"
HEADER = '#include "portable/whole_program/types/timer.h"\n'


@dataclass
class TimerConversion:
    text: str
    replacements: dict[str, int] = field(default_factory=dict)
    unresolved: list[str] = field(default_factory=list)


def adapt(source: str) -> tuple[str, dict[str, object]]:
    """Return source with only the source Rect/Timer declarations lifted."""
    source_hash = hashlib.sha256(source.encode("utf-8")).hexdigest()
    if source_hash != SOURCE_SHA256:
        raise ValueError(f"unexpected {SOURCE_PATH} source hash: {source_hash}")

    rect_pattern = re.compile(
        r"struct Rect\s*\{\s*int left;\s*int top;\s*int right;\s*int bottom;\s*\};\s*",
        re.S)
    timer_pattern = re.compile(
        r"struct Timer\s*\{\s*struct Rect r;\s*"
        r"void\s*\(far\s*\*fn\)\(\);\s*int ticks;\s*"
        r"char a;\s*char b;\s*char c;\s*char d;\s*\};\s*",
        re.S)
    text, rect_count = rect_pattern.subn("", source, count=1)
    text, timer_count = timer_pattern.subn("", text, count=1)
    if rect_count != 1 or timer_count != 1:
        raise ValueError("expected exactly one source Rect and Timer declaration")
    if "struct Timer g_5FF2 =" not in text:
        raise ValueError("source Timer owner initializer was unexpectedly removed")
    if HEADER.strip() not in text:
        text = HEADER + text
    ledger: dict[str, object] = {
        "source_path": SOURCE_PATH,
        "source_sha256": source_hash,
        "shared_header": "portable/whole_program/types/timer.h",
        "lifted_declarations": {"struct Rect": rect_count, "struct Timer": timer_count},
        "source_owner_preserved": "struct Timer g_5FF2 initializer remains in m1FD2 TU",
        "function_bodies_rewritten": 0,
    }
    return text, ledger
