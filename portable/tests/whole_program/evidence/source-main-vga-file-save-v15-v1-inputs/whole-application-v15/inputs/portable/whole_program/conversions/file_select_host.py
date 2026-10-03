"""Pinned preword retirement of S09's BIOS floppy-equipment policy.

The Win16 physical equipment byte at 0040:0010 has no native analogue. This
adapter removes only the read and its B-to-A override; drive enumeration and
directory availability remain the responsibility of source FileSelect and
the native f_1F66_00AF provider.
"""

from __future__ import annotations

import hashlib

SOURCE_RELATIVE = "src/S09/m35F5.c"
SOURCE_SHA256 = "028e1575990d5d45233f9102a0d2a060810349bd2f1297182c4af435ecbe912a"

_DECLARATION = "static char oneFloppy;\n"
_POLICY = (
    "    oneFloppy = (*(unsigned char far *)0x00000410L & 0xC0) == 0;\n"
    "    if (s_2966 == 'B' && oneFloppy)\n"
    "        s_2966 = 'A';\n"
)


def adapt(source: bytes, rel: str) -> bytes:
    """Validate frozen S09 input and remove its physical BIOS-only policy."""
    if rel.replace("\\", "/") != SOURCE_RELATIVE:
        raise ValueError(f"unexpected source route: {rel}")
    actual = hashlib.sha256(source).hexdigest()
    if actual != SOURCE_SHA256:
        raise ValueError(f"frozen S09 source identity mismatch: {actual}")
    try:
        text = source.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("S09 source is not UTF-8") from exc
    if text.count(_DECLARATION) != 1:
        raise ValueError("expected exactly one oneFloppy source declaration")
    if text.count(_POLICY) != 1:
        raise ValueError("expected exactly one frozen BIOS-equipment policy block")
    adapted = text.replace(_DECLARATION, "", 1).replace(_POLICY, "", 1)
    if "oneFloppy" in adapted or "0x00000410L" in adapted:
        raise ValueError("BIOS equipment read/policy remains after preword adaptation")
    return adapted.encode("utf-8")
