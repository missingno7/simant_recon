"""Pre-word native owner adaptation for the frozen root:m0250 source."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

SOURCE_RELATIVE = "src/root/m0250.c"
SOURCE_SHA256 = "bb8a325c543151e09cb173d2194844877805a9e1058d3b24362ff5a7cbd9f61b"
OWNER = "portable_line16b5_source_buffer"

_DECL = re.compile(r"^extern Pnt far fd_50F6_1F26;\r?$", re.MULTILINE)
_F2662_PROTO = "extern void far f_2662_1120(int x, int y, Pnt far *buf, int id);"
_F16B5_PROTO = "extern void far f_16B5_0033(Pnt far *buf, int mode);"
_F0008_PROTO = "extern void far f_16B5_0008(int x0, int y0, int x1, int y1, int color);"
_F2662_NATIVE_PROTO = "extern void far f_2662_1120(int x, int y, char far *buf, int id);"
_F16B5_NATIVE_PROTO = "extern void far f_16B5_0033(void far *buf, int16_t mode);"
_F0008_NATIVE_PROTO = "extern void far f_16B5_0008(int16_t x0, int16_t y0, int16_t x1, int16_t y1, int16_t color);"


@dataclass(frozen=True)
class SourceAdaptReceipt:
    source_sha256: str
    output_sha256: str
    removed_extern_count: int
    replaced_code_identifiers: int
    corrected_f2662_prototype_count: int
    corrected_f16b5_prototype_count: int
    corrected_f0008_prototype_count: int
    f2662_bytecasts: int
    f16b5_bytecasts: int
    owner: str = OWNER
    owner_size: int = 6276
    pixel_offset: int = 4


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _replace_identifier_c_lexically(text: str, old: str, new: str) -> tuple[str, int]:
    """Replace an identifier only in C code, preserving comments/literals."""
    out: list[str] = []
    i = 0
    count = 0
    state = "code"
    while i < len(text):
        ch = text[i]
        nxt = text[i + 1] if i + 1 < len(text) else ""
        if state == "code":
            if ch == "/" and nxt == "*":
                out.extend((ch, nxt)); i += 2; state = "block"; continue
            if ch == "/" and nxt == "/":
                out.extend((ch, nxt)); i += 2; state = "line"; continue
            if ch == '"':
                out.append(ch); i += 1; state = "string"; continue
            if ch == "'":
                out.append(ch); i += 1; state = "char"; continue
            if ch == "_" or ch.isalpha():
                j = i + 1
                while j < len(text) and (text[j] == "_" or text[j].isalnum()):
                    j += 1
                token = text[i:j]
                if token == old:
                    out.append(new); count += 1
                else:
                    out.append(token)
                i = j
                continue
            out.append(ch); i += 1; continue
        if state == "block":
            if ch == "*" and nxt == "/":
                out.extend((ch, nxt)); i += 2; state = "code"; continue
            out.append(ch); i += 1; continue
        if state == "line":
            out.append(ch); i += 1
            if ch == "\n": state = "code"
            continue
        # C string and character literal; preserve escaped characters exactly.
        out.append(ch); i += 1
        if ch == "\\" and i < len(text):
            out.append(text[i]); i += 1; continue
        if (state == "string" and ch == '"') or (state == "char" and ch == "'"):
            state = "code"
    if state in ("block", "string", "char"):
        raise ValueError(f"unterminated C lexical state: {state}")
    return "".join(out), count


def adapt(source: bytes, rel: str) -> tuple[bytes, SourceAdaptReceipt]:
    """Adapt only pinned historical m0250 to the typed native inline owner.

    This API runs before whole-program word conversion. It leaves comments and
    literals unchanged, removes the old undersized object declaration, and
    turns only byte-consuming f_2662/f_16B5 calls into explicit byte pointers.
    """
    if rel.replace("\\", "/") != SOURCE_RELATIVE:
        raise ValueError("unexpected source route")
    digest = _sha(source)
    if digest != SOURCE_SHA256:
        raise ValueError(f"frozen m0250 source identity mismatch: {digest}")
    text = source.decode("utf-8")
    for anchor, label in ((_F2662_PROTO, "f_2662_1120 Pnt prototype"),
                          (_F16B5_PROTO, "f_16B5_0033 Pnt prototype"),
                          (_F0008_PROTO, "f_16B5_0008 DOS-word prototype")):
        if text.count(anchor) != 1:
            raise ValueError(f"expected one {label}")
    decl_matches = list(_DECL.finditer(text))
    if len(decl_matches) != 1:
        raise ValueError("expected exactly one source Pnt object extern")
    text = _DECL.sub("", text)
    text = text.replace(_F2662_PROTO, _F2662_NATIVE_PROTO)
    text = text.replace(_F16B5_PROTO, _F16B5_NATIVE_PROTO)
    text = text.replace(_F0008_PROTO, _F0008_NATIVE_PROTO)

    # Convert active references only after validating the complete file hash.
    # The one old extern was removed, so 16 code references remain.
    text, refs = _replace_identifier_c_lexically(text, "fd_50F6_1F26", OWNER)
    if refs != 16:
        raise ValueError(f"expected 16 active references, got {refs}")

    # The raster and image APIs consume bytes. Keep the source header address
    # as a byte pointer for those consumers, including the two typed DOS
    # prototypes whose original Pnt declarations mismatched their definitions.
    f2662_pattern = re.compile(r"(f_2662_1120\([^;]*?)(?<![\w])&" + OWNER)
    text, cast2662 = f2662_pattern.subn(r"\1(char far *)&" + OWNER, text)
    f16b5_pattern = re.compile(r"(f_16B5_0033\()&" + OWNER)
    text, cast16b5 = f16b5_pattern.subn(r"\1(char far *)&" + OWNER, text)
    if cast2662 != 3 or cast16b5 != 3:
        raise ValueError(f"byte consumer call anchors changed: f2662={cast2662}, f16b5={cast16b5}")
    text = '#include "portable/whole_program/algorithms/line16b5.h"\n' + text
    out = text.encode("utf-8")
    return out, SourceAdaptReceipt(
        source_sha256=digest,
        output_sha256=_sha(out),
        removed_extern_count=1,
        replaced_code_identifiers=refs,
        corrected_f2662_prototype_count=1,
        corrected_f16b5_prototype_count=1,
        corrected_f0008_prototype_count=1,
        f2662_bytecasts=cast2662,
        f16b5_bytecasts=cast16b5,
    )


def _lexical_control() -> bool:
    sample = '/* fd_50F6_1F26 */ "fd_50F6_1F26\\\"" fd_50F6_1F26 // fd_50F6_1F26\n'
    converted, count = _replace_identifier_c_lexically(sample, "fd_50F6_1F26", OWNER)
    return (count == 1 and converted.startswith('/* fd_50F6_1F26 */ "fd_50F6_1F26\\\"" ')
            and converted.endswith("// fd_50F6_1F26\n") and OWNER in converted)
