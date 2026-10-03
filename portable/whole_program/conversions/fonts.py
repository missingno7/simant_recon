"""Shared FONT runtime views; allocation follows native pointer-bearing size.

The file-read prefix stays thirteen DOS words. Bitmap storage has one native
owner and S13's same-address scalar view explicitly reads its first member.
No font algorithm, bitmap wire payload size, or glyph argument is changed.
"""
import re

def adapt(unit: str, source: str) -> tuple[str, dict | None]:
    if unit not in {"src/root/m25E7.c", "src/root/m24AB.c", "src/S13/m384C.c"}:
        return source, None
    changes = []
    if unit in {"src/root/m25E7.c", "src/root/m24AB.c"}:
        source, count = re.subn(r"struct Bitmap\s*\{[^{}]*\};", "", source)
        if count != 1: raise ValueError("Bitmap source family changed")
        changes.append("common native Bitmap definition")
    if unit == "src/root/m25E7.c":
        source, count = re.subn(r"struct Font\s*\{[^{}]*\};", "", source)
        if count != 1: raise ValueError("Font source definition changed")
        old = 'f_171C_2190(0x2a, "FontHeader")'
        if source.count(old) != 1: raise ValueError("Font runtime allocation changed")
        source = source.replace(old, 'f_171C_2190(sizeof(struct Font), "FontHeader")')
        changes.extend(["common Font definition; 26-byte wire-read prefix retained",
                        "runtime FontHeader allocation 0x2a -> sizeof(struct Font), native pointers"])
    if unit == "src/S13/m384C.c":
        old = "extern int far fd_50F6_392C;"
        if source.count(old) != 1: raise ValueError("S13 Bitmap width view changed")
        source = source.replace(old, "")
        source, count = re.subn(r"\bfd_50F6_392C\b", "fd_50F6_392C.width", source)
        if count != 1: raise ValueError("S13 Bitmap width use count changed")
        changes.append("same-address S13 scalar width view -> Bitmap.width")
    source = '#include "portable/whole_program/types/fonts.h"\n' + source
    return source, {"kind": "NATIVE_FONT_RUNTIME_LAYOUT", "source": unit, "changes": changes,
                    "limits": "source algorithms retained; glyph raster/platform buffers require separate providers"}
