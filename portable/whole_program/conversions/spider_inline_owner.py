"""Strict standalone conversion for root:m0250's inline DrawSpider image."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

SOURCE_RELATIVE = "src/root/m0250.c"
SOURCE_SHA256 = "bb8a325c543151e09cb173d2194844877805a9e1058d3b24362ff5a7cbd9f61b"
GENERATED_RELATIVE = "build/workers/whole_program/generated/root_m0250.c"
GENERATED_SHA256 = "4221b4666a2d152a851d17c20c78dab1979fa696156e4879dca0220888309418"
OWNER = "portable_line16b5_source_buffer"
DECL = re.compile(r"^extern Pnt\s+fd_50F6_1F26;\s*$", re.MULTILINE)
F2662_DECL = re.compile(
    r"^extern void\s+f_2662_1120\(int16_t x, int16_t y, Pnt\s+\*buf, int16_t id\);\s*$",
    re.MULTILINE,
)


@dataclass(frozen=True)
class ConversionReceipt:
    source_sha256: str
    generated_sha256: str
    output_sha256: str
    owner_symbol: str
    owner_size: int
    pixel_offset: int
    removed_declarations: int
    replaced_references: int
    corrected_f2662_prototype: int


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def convert(source_path: str, generated_path: str, source: bytes,
            generated: bytes) -> tuple[bytes, ConversionReceipt]:
    """Bind the generated m0250 TU to one typed inline owner, failing closed.

    The two paths and both input identities are intentionally pinned. This is
    a reviewed conversion for one generated output, not a general source
    rewrite. Re-run source review before updating either pin.
    """
    if source_path.replace("\\", "/") != SOURCE_RELATIVE:
        raise ValueError("unexpected frozen source path")
    if generated_path.replace("\\", "/") != GENERATED_RELATIVE:
        raise ValueError("unexpected generated TU path")
    source_digest = verify_source_identity(source)
    generated_digest = _sha(generated)
    if generated_digest != GENERATED_SHA256:
        raise ValueError(f"generated m0250 identity mismatch: {generated_digest}")

    text = generated.decode("utf-8")
    if text.count("fd_50F6_1F26") != 17:
        raise ValueError("m0250 inline-buffer reference count changed")
    text, removed = DECL.subn("", text)
    if removed != 1:
        raise ValueError("expected exactly one incompatible Pnt extern")
    text, prototype = F2662_DECL.subn(
        "extern void f_2662_1120(int16_t x, int16_t y, char *buf, int16_t id);",
        text,
    )
    if prototype != 1:
        raise ValueError("expected exactly one m2662 byte-buffer ABI prototype")

    # Each address-taking use enters a byte-oriented ABI: f_1B4E_003B's inline
    # blitter, f_16B5_0033's prefix adapter, f_2662_1120's source definition,
    # and the two generic image callbacks. A char* preserves the same address
    # while avoiding an incompatible external Pnt object type.
    replaced_refs = text.count("fd_50F6_1F26")
    text = re.sub(r"\bfd_50F6_1F26\b", OWNER, text)
    if text.count(OWNER) != replaced_refs:
        raise ValueError("owner symbol replacement count mismatch")
    text = text.replace("&" + OWNER, "(char *)&" + OWNER)
    text = '#include "portable/whole_program/algorithms/line16b5.h"\n' + text
    output = text.encode("utf-8")
    receipt = ConversionReceipt(
        source_sha256=source_digest,
        generated_sha256=generated_digest,
        output_sha256=_sha(output),
        owner_symbol=OWNER,
        owner_size=6276,
        pixel_offset=4,
        removed_declarations=removed,
        replaced_references=replaced_refs,
        corrected_f2662_prototype=prototype,
    )
    return output, receipt


def verify_source_identity(source: bytes) -> str:
    digest = _sha(source)
    if digest != SOURCE_SHA256:
        raise ValueError(f"frozen m0250 source identity mismatch: {digest}")
    if source.count(b"extern Pnt far fd_50F6_1F26;") != 1:
        raise ValueError("source Pnt external declaration anchor changed")
    if source.count(b"p = (char far *)&fd_50F6_1F26 + 4;") != 1:
        raise ValueError("source inline payload offset anchor changed")
    return digest
