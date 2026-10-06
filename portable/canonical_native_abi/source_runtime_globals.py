import re

def _text(value):
    return value.decode('utf-8') if isinstance(value, bytes) else value

def _once(text, pattern, replacement, label):
    (text, n) = re.subn(pattern, replacement, text, count=1, flags=re.M)
    if n != 1:
        raise ValueError(f'expected one {label}, found {n}')
    return text

def adapt_transformed(source, rel, original_source=None):
    if rel != 'src/root/m1E57.c':
        raise ValueError('unregistered source memory module: ' + rel)
    text = _text(source)
    if rel == 'src/root/m1E57.c':
        text = _once(text, '^extern struct Rect(?:\\s+far)?\\s+fd_50F6_3C14\\[\\];$', 'extern struct Rect far *fd_50F6_3C14;\nextern int sim_source_runtime_reserve_clip_rects(size_t bytes);', 'clip declaration')
        if '#include <stddef.h>' not in text:
            text = '#include <stddef.h>\n' + text
        old = '_fmemcpy(fd_50F6_3C14, p, size);'
        if text.count(old) != 2:
            raise ValueError('clip snapshot copy anchor changed')
        text = text.replace(old, 'if (size <= 0 || !sim_source_runtime_reserve_clip_rects((size_t)size))\n            Punt("Cannot allocate clip rectangle snapshot");\n        ' + old)
        old = '_fmemcpy(fd_50F6_3C14, g_5AAC, size);'
        if text.count(old) != 1:
            raise ValueError('clip stack copy anchor changed')
        text = text.replace(old, 'if (size <= 0 || !sim_source_runtime_reserve_clip_rects((size_t)size))\n            Punt("Cannot allocate clip rectangle snapshot");\n        ' + old)
        dynamic_copy = '    g_5AAC = fd_50F6_3C14;\n    _fmemcpy(g_5AAC,'
        if text.count(dynamic_copy) != 4:
            raise ValueError('runtime-sized clip producer anchors changed')
        reserve_guard = '    if (n < 0 || !sim_source_runtime_reserve_clip_rects(((size_t)n + 1u) * sizeof(struct Rect)))\n        Punt("Cannot allocate clip rectangle output");\n'
        text = text.replace(dynamic_copy, reserve_guard + dynamic_copy)
        old = '        g_5AAC = fd_50F6_3C14;\n        f_1D8E_003F(r, &g_5A9C, fd_50F6_3C14, 0L);'
        if text.count(old) != 1:
            raise ValueError('clip output producer anchor changed')
        text = text.replace(old, '        if (!sim_source_runtime_reserve_clip_rects(5u * sizeof(struct Rect)))\n            Punt("Cannot allocate clip rectangle output");\n' + old)
    return text
