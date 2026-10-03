"""Strict native handle typing for the yard cache globals and their consumers.

This adapter is intentionally independent of the historical sources and of the
central generator.  The central build may call ``adapt(text, source_rel)`` after
startup-global normalization.  It accepts only the known generated declarations
and stops if another stage has already changed their shape unexpectedly.
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
HEADER = 'portable/whole_program/state/yard_cache_globals_v1.h'
OWNER = 'portable/whole_program/state/yard_cache_globals_v1.c'

ROUTES = {
    'src/S13/m384C.c',
    'src/root/m00F8.c',
    'src/root/m1A96.c',
    'src/root/m015B.c',
    'src/S22/m39C7.c',
}


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode('latin1')).hexdigest()


def _replace_once(text: str, pattern: str, replacement: str, label: str) -> str:
    out, n = re.subn(pattern, replacement, text, count=1, flags=re.MULTILINE)
    if n != 1:
        raise ValueError(f'{label}: expected exactly one source-shaped match, found {n}')
    return out


def _include(text: str) -> str:
    line = f'#include "{HEADER}"'
    if line in text:
        raise ValueError('yard-cache owner header already included; refusing double conversion')
    return line + '\n' + text


def _rewrite_identifier(text: str, old: str, new: str, minimum: int) -> tuple[str, int]:
    out, count = re.subn(rf'\b{re.escape(old)}\b', new, text)
    if count < minimum:
        raise ValueError(f'{old}: expected at least {minimum} identifier uses, found {count}')
    return out, count


def _adapt_s13(text: str) -> tuple[str, dict[str, Any]]:
    out = text
    out = _include(out)
    out = _replace_once(
        out,
        r'(?m)^static\s+(?:long|int32_t)\s+g_2A36\s*=\s*0\s*;\s*$',
        'extern SimYardCacheHandle fd_55B3_2A36;', '2A36 source storage')
    out = _replace_once(
        out,
        r'(?m)^static\s+(?:long|int32_t)\s+g_2A3A\s*=\s*0\s*;\s*$',
        'extern SimYardCacheHandle fd_55B3_2A3A;', '2A3A source storage')
    out = _replace_once(
        out,
        r'(?m)^static\s+(?:int|int16_t)\s+g_2A42\s*\[\s*8\s*\]\s*=\s*\{[^\n]*\};\s*$',
        'extern int16_t fd_55B3_2A42[8];', '2A42 source storage')
    out = _replace_once(out,
        r'(?m)^typedef\s+char\s+(?:far\s*)?\*\s*(?:far\s*)?\*\s*Handle\s*;\s*$',
        'typedef SimYardCacheHandle Handle;', 'S13 Handle source alias')
    out = _replace_once(out,
        r'(?m)^extern\s+void\s+(?:far\s+)?f_171C_1C0A\((?:long|int32_t)\s+h\)\s*;\s*$',
        'extern void f_171C_1C0A(SimYardCacheHandle h);', 'handle free declaration')
    out = _replace_once(out,
        r'(?m)^extern\s+(?:long|int32_t)\s+(?:far\s+)?(?:f_1629_000C|MakeBalloon)\(char\s+(?:far\s*)?\*\s*msg,\s*(?:int|int16_t)\s+flags\)\s*;\s*$',
        'extern SimYardCacheHandle MakeBalloon(char *msg, int16_t flags);',
        'balloon producer declaration')
    out = _replace_once(out,
        r'(?m)^extern\s+(?:long|int32_t)\s+(?:far\s+)?f_24AB_0002\((?:long|int32_t)\s+text\)\s*;\s*$',
        'extern SimYardCacheHandle f_24AB_0002(char *text);',
        'font bitmap handle producer declaration')
    uses: dict[str, int] = {}
    for old, new, minimum in (
        ('g_2A36', 'fd_55B3_2A36', 6),
        ('g_2A3A', 'fd_55B3_2A3A', 4),
        ('g_2A42', 'fd_55B3_2A42', 10),
    ):
        out, count = _rewrite_identifier(out, old, new, minimum)
        uses[old] = count
    return out, {'rewritten_uses': uses, 'owner_header': HEADER, 'owner_source': OWNER}


def _adapt_m00f8(text: str) -> tuple[str, dict[str, Any]]:
    out = _include(text)
    removed = 0
    for symbol in ('fd_55B3_2A36', 'fd_55B3_2A3A'):
        pattern = rf'(?m)^extern\s+char\s+far\s*\*\s*far\s+{symbol}\s*;\s*$'
        out, count = re.subn(pattern, '', out)
        if count > 1:
            raise ValueError(f'{symbol}: duplicate obsolete cached-handle declarations')
        removed += count
    out = _replace_once(out,
        r'(?m)^char\s+(?:far\s*)?\*\s*(?:far\s+)?f_00F8_0543\((?:int|int16_t)\s+object,\s*(?:int|int16_t)\s+type\)\s*$',
        'SimYardCacheHandle f_00F8_0543(int16_t object, int16_t type)',
        'cached-handle producer return declaration')
    out = _replace_once(out,
        r'(?m)^extern\s+void\s+(?:far\s+)?ch_SetCacheHooks\(char\s+(?:far\s*)?\*\s*\(\s*(?:far\s*)?\*cache\)\((?:int|int16_t)\s+object,\s*(?:int|int16_t)\s+type\)\)\s*;\s*$',
        'extern void ch_SetCacheHooks(SimYardCacheHandle (*cache)(int16_t object, int16_t type));',
        'cache-hook declaration')
    return out, {'cached_handle_provider': 'f_00F8_0543', 'owner_header': HEADER,
                 'obsolete_externs_removed': removed}


def _adapt_m1a96(text: str) -> tuple[str, dict[str, Any]]:
    out = _include(text)
    substitutions = (
        (r'(?m)^\s*char\s+(?:far\s*)?\*h\s*;\s*$', '        SimYardCacheHandle h;', 'CacheEntry handle field'),
        (r'(?m)^extern\s+(?:unsigned\s+long|uint32_t)\s+(?:far\s+)?f_171C_14BE\(char\s+(?:far\s*)?\*handle\)\s*;\s*$',
         'extern uint32_t f_171C_14BE(SimYardCacheHandle handle);', 'handle age API'),
        (r'(?m)^extern\s+void\s+(?:far\s+)?f_171C_152C\(char\s+(?:far\s*)?\*handle\)\s*;\s*$',
         'extern void f_171C_152C(SimYardCacheHandle handle);', 'handle lock API'),
        (r'(?m)^extern\s+(?:int|int16_t)\s+(?:far\s+)?f_171C_1686\(char\s+(?:far\s*)?\*handle\)\s*;\s*$',
         'extern int16_t f_171C_1686(SimYardCacheHandle handle);', 'handle type API'),
        (r'(?m)^extern\s+(?:int|int16_t)\s+(?:far\s+)?f_171C_1794\(char\s+(?:far\s*)?\*handle\)\s*;\s*$',
         'extern int16_t f_171C_1794(SimYardCacheHandle handle);', 'handle discarded API'),
        (r'(?m)^extern\s+(?:int|int16_t)\s+(?:far\s+)?f_171C_1AD4\(char\s+(?:far\s*)?\*handle\)\s*;\s*$',
         'extern int16_t f_171C_1AD4(SimYardCacheHandle handle);', 'handle lock-count API'),
        (r'(?m)^char\s+(?:far\s*)?\*\s*\(\s*(?:far\s*)?\*g_3B7E\)\((?:int|int16_t)\s+object,\s*(?:int|int16_t)\s+type\)\s*=\s*0L\s*;\s*$',
         'SimYardCacheHandle (*g_3B7E)(int16_t object, int16_t type) = 0;', 'cache callback global'),
        (r'(?m)^char\s+(?:far\s*)?\*\s*\(\s*(?:far\s*)?\*g_3B82\)\((?:int|int16_t)\s+object,\s*(?:int|int16_t)\s+type\)\s*=\s*0L\s*;\s*$',
         'SimYardCacheHandle (*g_3B82)(int16_t object, int16_t type) = 0;', 'release callback global'),
        (r'(?m)^char\s+(?:far\s*)?\*\s+(?:far\s+)?ch_LookUpId\((?:int|int16_t)\s+object,\s*(?:int|int16_t)\s+type,\s*CacheHandle\s+table\)\s*;',
         'SimYardCacheHandle ch_LookUpId(int16_t object, int16_t type, CacheHandle table);', 'cache lookup prototype'),
        (r'(?m)^char\s+(?:far\s*)?\*\s+(?:far\s+)?ch_LookUpId\((?:int|int16_t)\s+object,\s*(?:int|int16_t)\s+type,\s*CacheHandle\s+table\)\s*$',
         'SimYardCacheHandle ch_LookUpId(int16_t object, int16_t type, CacheHandle table)', 'cache lookup definition'),
        (r'(?m)^(?:int|int16_t)\s+(?:far\s+)?ch_LookUpHandle\(char\s+(?:far\s*)?\*handle,\s*CacheHandle\s+table,\s*(?:int|int16_t)\s+(?:far\s*)?\*object,\s*(?:int|int16_t)\s+(?:far\s*)?\*type\)\s*$',
         'int16_t ch_LookUpHandle(SimYardCacheHandle handle, CacheHandle table, int16_t *object, int16_t *type)', 'handle lookup definition'),
        (r'(?m)^(?:int|int16_t)\s+(?:far\s+)?ch_AddEntry\((?:int|int16_t)\s+object,\s*(?:int|int16_t)\s+type,\s*CacheHandle\s+table,\s*char\s+(?:far\s*)?\*handle\)\s*$',
         'int16_t ch_AddEntry(int16_t object, int16_t type, CacheHandle table, SimYardCacheHandle handle)', 'cache insertion definition'),
        (r'(?m)^void\s+(?:far\s+)?ch_SetCacheHooks\(char\s+(?:far\s*)?\*\s*\(\s*(?:far\s*)?\*cache\)\((?:int|int16_t)\s+object,\s*(?:int|int16_t)\s+type\),\s*$',
         'void ch_SetCacheHooks(SimYardCacheHandle (*cache)(int16_t object, int16_t type),', 'cache-hook definition'),
        (r'(?m)^\s*char\s+(?:far\s*)?\*\s*\(\s*(?:far\s*)?\*release\)\((?:int|int16_t)\s+object,\s*(?:int|int16_t)\s+type\)\)\s*$',
         '                     SimYardCacheHandle (*release)(int16_t object, int16_t type))', 'release-hook definition'),
    )
    for pattern, replacement, label in substitutions:
        out = _replace_once(out, pattern, replacement, label)
    out = _replace_once(out,
        r'(?m)^\s*char\s+(?:far\s*)?\*handle\s*;\s*$',
        '    SimYardCacheHandle handle;', 'cache lookup local handle')
    return out, {'typed_handle_fields': 1, 'typed_cache_entry_apis': 5,
                 'owner_header': HEADER}


def adapt(source: str | bytes, rel: str) -> tuple[str | bytes, dict[str, Any] | None]:
    rel = Path(rel).as_posix()
    if rel not in ROUTES:
        return source, None
    is_bytes = isinstance(source, bytes)
    text = source.decode('latin1') if is_bytes else source
    before = _sha(text)
    if rel == 'src/S13/m384C.c':
        out, details = _adapt_s13(text)
    elif rel == 'src/root/m00F8.c':
        out, details = _adapt_m00f8(text)
    elif rel == 'src/root/m1A96.c':
        out, details = _adapt_m1a96(text)
    elif rel in ('src/root/m015B.c', 'src/S22/m39C7.c'):
        # Accept the two source-stage spellings from before/after
        # startup_globals_v1.  The narrow declaration is always removed; the
        # complete [8] native owner is provided by this adapter's header.
        if rel == 'src/root/m015B.c':
            if re.search(r'(?m)^extern\s+Point\s+far\s+fd_55B3_2A42\s*;\s*$', text):
                out = _replace_once(text,
                    r'(?m)^extern\s+Point\s+far\s+fd_55B3_2A42\s*;\s*$',
                    '', 'Point source declaration')
            else:
                out = text
            for field, index in (('x', 0), ('y', 1)):
                pattern = rf'\bfd_55B3_2A42\s*\.\s*{field}\b'
                if re.search(pattern, out):
                    out, n = re.subn(pattern, f'fd_55B3_2A42[{index}]', out)
                    if n != 1:
                        raise ValueError(f'expected one yard point {field} access, got {n}')
            if not ('fd_55B3_2A42[0]' in out and 'fd_55B3_2A42[1]' in out):
                raise ValueError('root yard origin consumer lacks x/y reads')
        else:
            out = text
        # Remove a remaining narrow declaration whether it is pre-word or
        # post-word.  If startup-global normalization already removed it, no
        # declaration is required here.
        narrow, n = re.subn(
            r'(?m)^extern\s+(?:(?:int16_t|int)\s+far\s+fd_55B3_2A42\s*\[\s*2\s*\]|Point\s+far\s+fd_55B3_2A42)\s*;\s*$',
            '', out)
        if n > 1:
            raise ValueError(f'expected at most one narrow point-table declaration, got {n}')
        out = narrow
        out = _include(out)
        if 'fd_55B3_2A42[0]' not in out or 'fd_55B3_2A42[1]' not in out:
            raise ValueError('yard point consumer is not normalized to the shared table')
        details = {'point_table_extent': 8, 'owner_header': HEADER,
                   'narrow_declarations_removed': n}
    else:
        raise AssertionError(rel)
    ledger = {
        'kind': 'YARD_CACHE_SHARED_HANDLE_V1', 'source': rel,
        'input_sha256': before, 'output_sha256': _sha(out),
        'owner_header': HEADER, 'owner_source': OWNER, 'details': details,
        'claim': 'Native yard cache cells are SimYardCacheHandle (char **); source handle producers, cache callbacks, and consumers share that nontruncating type. The four yard points use the full source eight-word table.',
    }
    return (out.encode('latin1') if is_bytes else out), ledger

