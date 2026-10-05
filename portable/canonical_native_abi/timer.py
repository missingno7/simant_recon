from __future__ import annotations
import hashlib
import re
SOURCE_PATH = 'src/root/m1FD2.c'
HEADER = '#include "portable/whole_program/types/timer.h"\n'

def adapt(source: str) -> tuple[str, dict[str, object]]:
    """Return source with only the source Rect/Timer declarations lifted."""
    source_hash = hashlib.sha256(source.encode('utf-8')).hexdigest()
    rect_pattern = re.compile('struct Rect\\s*\\{\\s*int left;\\s*int top;\\s*int right;\\s*int bottom;\\s*\\};\\s*', re.S)
    timer_pattern = re.compile('struct Timer\\s*\\{\\s*struct Rect r;\\s*void\\s*\\(far\\s*\\*fn\\)\\(\\);\\s*int ticks;\\s*char a;\\s*char b;\\s*char c;\\s*char d;\\s*\\};\\s*', re.S)
    (text, rect_count) = rect_pattern.subn('', source, count=1)
    (text, timer_count) = timer_pattern.subn('', text, count=1)
    if rect_count != 1 or timer_count != 1:
        raise ValueError('expected exactly one source Rect and Timer declaration')
    if 'struct Timer g_5FF2 =' not in text:
        raise ValueError('source Timer owner initializer was unexpectedly removed')
    if HEADER.strip() not in text:
        text = HEADER + text
    ledger: dict[str, object] = {'source_path': SOURCE_PATH, 'source_sha256': source_hash, 'shared_header': 'portable/whole_program/types/timer.h', 'lifted_declarations': {'struct Rect': rect_count, 'struct Timer': timer_count}, 'source_owner_preserved': 'struct Timer g_5FF2 initializer remains in m1FD2 TU', 'function_bodies_rewritten': 0}
    return (text, ledger)
