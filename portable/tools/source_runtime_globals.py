"""Strict source-owned dynamic-state adapters.

Call adapt_transformed at the final pre-word stage. `original_source` must be
the canonical frozen TU; composed source can include earlier reviewed overlays.
"""
import hashlib
import re

PINNED = {
    "src/root/m1FD2.c": "f4359bdaf4cfc0fe326a54cf8a1eacb9ba3098b710bf2a561b3d0f48569bf6d8",
    "src/root/m1E57.c": "812e8ec90bcf25c56adf073e753bf72f8f6a3bc108055e112c43f894e9d8d0c3",
    "src/S15/m384C.c": "01b51eecedcd28e2213819572c846a9754039f4a527e6da5e56e57783398bdd5",
    "src/S10/m35F5.c": "69be1d6a9649e99102131c702e1920b6e84acc0c1b4cd737d2a047552f917ed5",
}

def _text(value):
    return value.decode("utf-8") if isinstance(value, bytes) else value

def _once(text, pattern, replacement, label):
    text, n = re.subn(pattern, replacement, text, count=1, flags=re.M)
    if n != 1:
        raise ValueError(f"expected one {label}, found {n}")
    return text

def adapt_transformed(source, rel, original_source):
    if rel not in PINNED:
        raise ValueError(f"unregistered source module: {rel}")
    original = original_source.encode() if isinstance(original_source, str) else original_source
    if hashlib.sha256(original).hexdigest() != PINNED[rel]:
        raise ValueError(f"canonical source identity drift: {rel}")
    text = _text(source)
    if rel == "src/root/m1FD2.c":
        text = _once(text, r"^extern int(?:16_t)?(?:\s+far)?\s+fd_50F6_46A8\[\];$", "extern int far *fd_50F6_46A8;", "46A8 declaration")
        text = _once(text, r"^extern int(?:16_t)?(?:\s+far)?\s+fd_50F6_46BC\[\];$", "extern int far *fd_50F6_46BC;", "46BC declaration")
        if "#include <stddef.h>" not in text:
            text = "#include <stddef.h>\n" + text
        text = text.replace("extern int far *fd_50F6_46A8;", "extern int far *fd_50F6_46A8;\nextern int sim_source_runtime_reserve_menu_titles(size_t count);")
        text = _once(text, r"^\s*int total;\s*$", "    int total;\n    int menuCount;", "menuCount local")
        anchor = """    i = 0;
    total = 0;
    for (t = g_6054->titles; *t; t++) {
"""
        repl = """    menuCount = 0;
    for (t = g_6054->titles; *t; t++)
        menuCount++;
    if (!sim_source_runtime_reserve_menu_titles((size_t)menuCount))
        Punt(\"Cannot allocate menu title geometry\");
    i = 0;
    total = 0;
    for (t = g_6054->titles; *t; t++) {
"""
        if text.count(anchor) != 1:
            raise ValueError("menu producer anchor missing or ambiguous")
        text = text.replace(anchor, repl)
    elif rel == "src/root/m1E57.c":
        text = _once(text, r"^extern struct Rect(?:\s+far)?\s+fd_50F6_3C14\[\];$", "extern struct Rect far *fd_50F6_3C14;\nextern int sim_source_runtime_reserve_clip_rects(size_t bytes);", "clip declaration")
        if "#include <stddef.h>" not in text:
            text = "#include <stddef.h>\n" + text
        old = "_fmemcpy(fd_50F6_3C14, p, size);"
        if text.count(old) != 2:
            raise ValueError("clip snapshot copy anchor changed")
        text = text.replace(old, "if (size <= 0 || !sim_source_runtime_reserve_clip_rects((size_t)size))\n            Punt(\"Cannot allocate clip rectangle snapshot\");\n        " + old)
        old = "_fmemcpy(fd_50F6_3C14, g_5AAC, size);"
        if text.count(old) != 1:
            raise ValueError("clip stack copy anchor changed")
        text = text.replace(old, "if (size <= 0 || !sim_source_runtime_reserve_clip_rects((size_t)size))\n            Punt(\"Cannot allocate clip rectangle snapshot\");\n        " + old)
        dynamic_copy = "    g_5AAC = fd_50F6_3C14;\n    _fmemcpy(g_5AAC,"
        if text.count(dynamic_copy) != 4:
            raise ValueError("runtime-sized clip producer anchors changed")
        reserve_guard = "    if (n < 0 || !sim_source_runtime_reserve_clip_rects(((size_t)n + 1u) * sizeof(struct Rect)))\n        Punt(\"Cannot allocate clip rectangle output\");\n"
        text = text.replace(dynamic_copy, reserve_guard + dynamic_copy)
        old = "        g_5AAC = fd_50F6_3C14;\n        f_1D8E_003F(r, &g_5A9C, fd_50F6_3C14, 0L);"
        if text.count(old) != 1:
            raise ValueError("clip output producer anchor changed")
        text = text.replace(old, "        if (!sim_source_runtime_reserve_clip_rects(5u * sizeof(struct Rect)))\n            Punt(\"Cannot allocate clip rectangle output\");\n" + old)
    elif rel == "src/S15/m384C.c":
        text = _once(text, r"^extern unsigned char(?:\s+near)?\s+g_8ED8\[\];$", "extern unsigned char *g_8ED8;\nextern int sim_source_runtime_reserve_mono_patterns(size_t bytes);", "mono pattern declaration")
        if "#include <stddef.h>" not in text:
            text = "#include <stddef.h>\n" + text
        old = "    n = (*h)[1] << 3;\n"
        if text.count(old) != 1:
            raise ValueError("mono resource extent anchor changed")
        text = text.replace(old, old + "    if (n < 0 || !sim_source_runtime_reserve_mono_patterns((size_t)n))\n        Punt(\"Cannot allocate monochrome patterns.\");\n")
    elif rel == "src/S10/m35F5.c":
        text = _once(text, r"^extern int(?:16_t)?(?:\s+far)?\s+fd_55B3_5AA0\[2\];$", "extern struct Rect far g_5A9C;", "display dimensions alias")
        text = text.replace("fd_55B3_5AA0[0]", "g_5A9C.right")
        text = text.replace("fd_55B3_5AA0[1]", "g_5A9C.bottom")
    return text

def adapt(source, rel):
    """Strict raw-source form for isolated tests."""
    raw = source.encode() if isinstance(source, str) else source
    if hashlib.sha256(raw).hexdigest() != PINNED.get(rel):
        raise ValueError(f"source identity drift: {rel}")
    return adapt_transformed(source, rel, raw)

