from __future__ import annotations
import hashlib
CANONICAL_PATH = 'src/root/m1986.c'
GUARD = 'if (fd_50F6_3956 == fd_50F6_3958[db].indexHeader.count) return 0L;'
CURSOR_ASSIGNMENT = 'fd_50F6_3952 = &fd_50F6_3958[db].index[fd_50F6_3956];'
DOS_SIGNATURE = 'IndexEntry far * far FindIndex(int db, int id, int kind)'

def _find_one_function(source: str) -> dict:
    from .lexical import function_heads
    found = [f for f in function_heads(source) if f['name'] == 'FindIndex']
    if len(found) != 1:
        raise ValueError(f'expected one code FindIndex definition, got {len(found)}')
    return found[0]

def _reviewed_body(source: str) -> tuple[dict, str]:
    head = _find_one_function(source)
    body = source[head['start']:head['end']]
    if head['signature'] != DOS_SIGNATURE:
        raise ValueError(f"reviewed FindIndex signature changed: {head['signature']!r}")
    if body.count(CURSOR_ASSIGNMENT) != 1:
        raise ValueError('expected the one-past cursor assignment exactly once')
    if 'if (fd_50F6_3952->id == id && fd_50F6_3952->kind == kind)' not in body:
        raise ValueError('reviewed return predicate changed')
    return (head, body)

def adapt_whole_source(source: str, module_path: str=CANONICAL_PATH) -> tuple[str, dict]:
    """Apply the existing native one-past guard to the supplied whole TU."""
    if module_path != CANONICAL_PATH:
        raise ValueError('only canonical root/m1986.c is accepted')
    (head, body) = _reviewed_body(source)
    guarded = body.replace(CURSOR_ASSIGNMENT, CURSOR_ASSIGNMENT + '\n    ' + GUARD, 1)
    if guarded.count(GUARD) != 1:
        raise ValueError('guard insertion failed closed')
    output = source[:head['start']] + guarded + source[head['end']:]
    return (output, {'lane': 'whole-module native safety adaptation', 'module_path': module_path, 'input_sha256': hashlib.sha256(source.encode('latin1')).hexdigest(), 'output_sha256': hashlib.sha256(output.encode('latin1')).hexdigest(), 'guard': GUARD, 'only_findindex_body_changed': True})
