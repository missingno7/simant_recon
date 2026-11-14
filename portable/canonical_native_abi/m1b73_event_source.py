from __future__ import annotations
import hashlib
import re
import json
from pathlib import Path
from functools import lru_cache
SOURCE_MODULES = {'src/ui/game_events.c', 'src/window/menu_tracking.c'}
CONTEXT_MODULES = {'src/startup/main.c', 'src/ui/view_dialog_helpers.c'}
HEADER = '#include "portable/whole_program/platform/m1b73_event_enqueue.h"\n'
ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / 'evidence/canonical/event-omitted-word/caller-frames.json'
CONTRACT_SHA256 = '0df92e8b8004e1f5e526c4de0e839bc7f6140029b000cdfc30426828e335a5ca'

@lru_cache(maxsize=1)
def _contracts():
    blob = CONTRACT.read_bytes()
    if hashlib.sha256(blob).hexdigest() != CONTRACT_SHA256:
        raise ValueError('event caller-frame evidence changed; recompile and review the contract')
    return json.loads(blob)

def receipt(source_path):
    if source_path not in SOURCE_MODULES | CONTEXT_MODULES:
        return None
    contracts = _contracts()
    selected = [r for r in contracts['modules'] if r['source'] == source_path]
    if not selected:
        return None
    row = selected[0]
    if hashlib.sha256((ROOT / source_path).read_bytes()).hexdigest() != row['source_sha256']:
        raise ValueError('event caller-frame source changed: ' + source_path)
    return dict(evidence='evidence/canonical/event-omitted-word/caller-frames.json',
                evidence_sha256=CONTRACT_SHA256,
                module=row['module'], profile=row['profile'], flags=row['flags'],
                object_sha256=row['object_sha256'], sites=row['sites'])

def _replace(source, old, new, count=1):
    if source.count(old) != count:
        raise ValueError('event caller context anchor changed: ' + old)
    return source.replace(old, new)

def adapt_caller_context(source, source_path):
    """Transport only the incoming SI needed by the omitted-word contract.

    Runs at the typed frontend boundary, after scalar/startup conversion. The
    two enqueue owners themselves were adapted before scalar conversion.
    """
    record = receipt(source_path)
    if source_path == 'src/startup/main.c':
        source = _replace(source, 'ui_pump_events_edge_scroll(void)',
                          'ui_pump_events_edge_scroll(int16_t portable_event_incoming_si)')
        source = _replace(source, 'ui_pump_events_edge_scroll();',
                          'ui_pump_events_edge_scroll(frames);', 2)
    elif source_path == 'src/ui/view_dialog_helpers.c':
        source = _replace(source, 'ui_pump_events_edge_scroll(void)',
                          'ui_pump_events_edge_scroll(int16_t portable_event_incoming_si)', 2)
        # This entry has no references in the canonical source inventory. Its
        # incoming SI is not a local value; retain an explicit open normalization.
        source = _replace(source, 'ui_pump_events_edge_scroll();',
                          'ui_pump_events_edge_scroll(0); /* Unbound periodic-entry SI: explicit normalization. */')
        source = _replace(source, 'DoEvent(void)', 'DoEvent(int16_t portable_event_incoming_si)')
        source = _replace(source, 'DoEvent();', 'DoEvent(portable_event_incoming_si);')
    return source, record

def _sha(source: str) -> str:
    return hashlib.sha256(source.encode('utf-8')).hexdigest()

def _skip_space_comments(source: str, pos: int) -> int:
    while pos < len(source):
        if source[pos].isspace():
            pos += 1
        elif source.startswith('//', pos):
            end = source.find('\n', pos + 2)
            return len(source) if end < 0 else _skip_space_comments(source, end + 1)
        elif source.startswith('/*', pos):
            end = source.find('*/', pos + 2)
            if end < 0:
                raise ValueError('unterminated C block comment')
            pos = end + 2
        else:
            break
    return pos

def _call_end_and_arity(source: str, open_pos: int) -> tuple[int, int]:
    depth = 0
    commas = 0
    saw_token = False
    i = open_pos
    while i < len(source):
        i = _skip_space_comments(source, i)
        if i >= len(source):
            break
        ch = source[i]
        if ch in '"\'':
            quote = ch
            saw_token = True
            i += 1
            while i < len(source):
                if source[i] == '\\':
                    i += 2
                elif source[i] == quote:
                    i += 1
                    break
                else:
                    i += 1
            continue
        if ch == '(':
            depth += 1
            if depth > 1:
                saw_token = True
        elif ch == ')':
            depth -= 1
            if depth == 0:
                return (i + 1, commas + (1 if saw_token else 0))
        elif depth == 1 and ch == ',':
            commas += 1
        elif depth == 1 and (not ch.isspace()):
            saw_token = True
        i += 1
    raise ValueError('unterminated input_enqueue_event_args call')

def _calls(source: str) -> list[tuple[int, int, int, int]]:
    result = []
    i = 0
    while i < len(source):
        if source.startswith('//', i):
            end = source.find('\n', i + 2)
            i = len(source) if end < 0 else end + 1
            continue
        if source.startswith('/*', i):
            end = source.find('*/', i + 2)
            if end < 0:
                raise ValueError('unterminated C block comment')
            i = end + 2
            continue
        if source[i] in '"\'':
            quote = source[i]
            i += 1
            while i < len(source):
                if source[i] == '\\':
                    i += 2
                elif source[i] == quote:
                    i += 1
                    break
                else:
                    i += 1
            continue
        if source.startswith('input_enqueue_event_args', i):
            before = source[i - 1] if i else ' '
            after_name = i + len('input_enqueue_event_args')
            after = source[after_name] if after_name < len(source) else ' '
            if (before.isalnum() or before == '_') or (after.isalnum() or after == '_'):
                i += 1
                continue
            open_pos = _skip_space_comments(source, after_name)
            if open_pos < len(source) and source[open_pos] == '(':
                (end, arity) = _call_end_and_arity(source, open_pos)
                result.append((i, after_name, end, arity))
                i = end
                continue
        i += 1
    return result

def adapt(source: str, source_path: str, enabled: bool = True) -> tuple[str, dict[str, object]]:
    if source_path not in SOURCE_MODULES:
        raise ValueError(f'unsupported m1B73 event callsite source: {source_path}')
    digest = _sha(source)
    old_proto = re.compile('(?m)^extern\\s+void\\s+far\\s+input_enqueue_event_args\\s*\\(\\s*\\)\\s*;\\s*\\n')
    (source, proto_count) = old_proto.subn('', source, count=1)
    if proto_count != 1:
        raise ValueError('expected one old-style input_enqueue_event_args prototype')
    calls = _calls(source)
    expected_arities = [4, 5] if source_path == 'src/ui/game_events.c' else [4, 5, 4]
    if [arity for (_, _, _, arity) in calls] != expected_arities:
        raise ValueError(f'unexpected enqueue callsite arities: {[x[3] for x in calls]}')
    record = receipt(source_path)
    expressions = iter(['portable_event_incoming_si'] if source_path == 'src/ui/game_events.c'
                       else ['portable_menu_saved_si', 'portable_menu_saved_si'])
    plans = [(call, next(expressions)) for call in calls if call[3] == 4]
    for ((start, name_end, end, arity), expression) in reversed(plans):
        if arity == 4:
            source = (source[:start] + 'portable_m1b73_event_enqueue_four_word_command' +
                      source[name_end:end - 1] + ', ' + (expression if enabled else '0') + source[end - 1:])
    if source_path == 'src/window/menu_tracking.c':
        source = _replace(source, 'menu_track_popup(char far *sel, char far * far *items)',
                          'menu_track_popup(char far *sel, char far * far *items, int portable_menu_saved_si)', 2)
        source = _replace(source, 'menu_track_popup(&sel, menu_resource_tables[m + 1])',
                          'menu_track_popup(&sel, menu_resource_tables[m + 1], m * 4)')
    else:
        source = _replace(source, 'input_dispatch_game_key(void)',
                          'input_dispatch_game_key(int portable_event_incoming_si)', 2)
        source = _replace(source, 'DoEvent(void)', 'DoEvent(int portable_event_incoming_si)')
        source = _replace(source, 'input_dispatch_game_key();',
                          'input_dispatch_game_key(portable_event_incoming_si);')
        source = _replace(source, 'if ((dx == 0 && dy == 0)',
                          'portable_event_incoming_si = dy;\n        if ((dx == 0 && dy == 0)')
    if HEADER.strip() not in source:
        source = HEADER + source
    return (source, {'kind': 'SOURCE_M1B73_TYPED_EVENT_CALLS', 'source_path': source_path, 'input_sha256': digest, 'output_sha256': _sha(source), 'callsite_arities': expected_arities, 'four_word_calls': len(plans), 'five_word_calls': len(calls) - len(plans), 'caller_frames': record, 'status': 'EXPLICIT_CALLER_WORD' if enabled else 'DISABLED_NEGATIVE_CONTROL', 'normalization': 'Menu callers pass saved SI = 4*m. Keyboard dispatch transports main frames or DoEvent dy; the unreferenced periodic entry still normalizes unbound incoming SI explicitly to zero.'})
