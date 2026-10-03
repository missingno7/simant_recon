"""Bind the original main counter and map-converter cells to native owners."""
import hashlib
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[3]
PINS = {
    'src/root/m15F8.c': 'd6d4daddab943ee3436ca0e9c8dbc866a9d67659f7448f3c307f858abe06b70a',
    'src/S06/m35F5.c': 'db35a96a492a6d36f6580222c17daca015aa9373b457b8758c751d3a70844a86',
    'src/S12/m384C.c': '584bf940832e3f8e975afdf85ed398fc82b6470e4a5c3ec46c1b4fcd15240002',
}

def sha(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

def adapt(source, rel):
    if rel not in PINS:
        return source, None
    if hashlib.sha256((ROOT / rel).read_bytes()).hexdigest() != PINS[rel]:
        raise ValueError('main/map source identity changed: ' + rel)
    before = source
    removed = []
    if rel != 'src/S12/m384C.c':
        names = ['fd_50F6_383A']
        patterns = [r'(?m)^extern\s+int32_t\s+fd_50F6_383A;\s*$']
        header = 'portable/whole_program/state/main_loop_counter.h'
    else:
        names = ['fd_50F6_38B8', 'fd_50F6_38BC', 'o00_3126_0000',
                 'o00_3126_0137', 'o00_3126_026A', 'o00_3126_03A9']
        patterns = [rf'(?m)^extern\s+void\s*\(\s*\*\s*{name}\)\(\);\s*$'
                    for name in names[:2]]
        patterns += [rf'(?m)^extern\s+void\s+{name}\(\);\s*$' for name in names[2:]]
        header = 'portable/whole_program/platform/map_transform_callbacks.h'
    for name, pattern in zip(names, patterns):
        source, count = re.subn(pattern, '', source)
        if count != 1:
            raise ValueError(f'expected one source extern for {name}: {count}')
        removed.append(name)
    source = f'#include "{header}"\n' + source
    return source, {'kind': 'NATIVE_ORIGINAL_MAIN_COUNTER_AND_MAP_CALLBACK_OWNERS',
        'source_sha256': PINS[rel], 'input_sha256': sha(before),
        'output_sha256': sha(source), 'removed_externs': removed,
        'header': header, 'changes': 'declarations only; original main counter updates and InitMapFunctions assignments retained'}
