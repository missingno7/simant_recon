"""Make two unused DOS argument slots explicit at the native boundary.

OpenMapYard never reads its named unused word. The cache release callback is
stored but never read anywhere in the frozen game. The native representation
of that unprovided callback is NULL; its historical stack value is not claimed.
"""
import hashlib
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[3]
PINS = {
    'src/root/m00F8.c': '4ee148ec616e199f61b671df89da8a21f1789c4177d3dbc7b76a478acb98184a',
    'src/root/m1A96.c': 'c57124b9d75ea77eb30158c09a71550862cf7081ceed625a2550a26a262bfdfa',
}


def adapt(text, rel):
    if rel != 'src/root/m00F8.c':
        return text, None
    for path, identity in PINS.items():
        if hashlib.sha256((ROOT / path).read_bytes()).hexdigest() != identity:
            raise ValueError('unused-argument source contract changed: ' + path)
    references = []
    for path in (ROOT / 'src').rglob('*'):
        if path.suffix in {'.c', '.asm'}:
            for line in path.read_text(encoding='utf-8').splitlines():
                if re.search(r'\b_?g_3B82\b', line):
                    references.append((path.relative_to(ROOT).as_posix(), line.strip()))
    if references != [
        ('src/root/m1A96.c', 'char far * (far *g_3B82)(int object, int type) = 0L;'),
        ('src/root/m1A96.c', 'g_3B82 = release;'),
    ]:
        raise ValueError('release callback gained an observable source consumer')
    before = hashlib.sha256(text.encode()).hexdigest()
    anchors = {
        'void  OpenMapYard(int16_t unused)': 'void  OpenMapYard(void)',
        'extern void ch_SetCacheHooks(SimYardCacheHandle (*cache)(int16_t object, int16_t type));':
            'extern void ch_SetCacheHooks(SimYardCacheHandle (*cache)(int16_t object, int16_t type), '
            'SimYardCacheHandle (*release)(int16_t object, int16_t type));',
        'ch_SetCacheHooks(f_00F8_0543);': 'ch_SetCacheHooks(f_00F8_0543, 0);',
    }
    for old, new in anchors.items():
        if text.count(old) != 1:
            raise ValueError('unused-argument conversion anchor changed: ' + old)
        text = text.replace(old, new, 1)
    return text, dict(kind='UNUSED_DOS_ARGUMENT_SLOTS_NATIVE_V1', source=rel,
        input_sha256=before, output_sha256=hashlib.sha256(text.encode()).hexdigest(),
        canonical_inputs=PINS, release_callback_references=references,
        claim='Native unused word removed; unread unprovided callback explicitly null. '
              'Historical private callback bytes are not asserted to match.')
