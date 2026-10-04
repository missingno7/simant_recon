"""Four source-only monochrome base fixups; deliberately no buffer owner."""
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
SITES = [14, 161, 304, 473]
SOURCE_SHA = '610b108145bbf912a6c1b11b454eaf54a7c6053624db8b7de8f2c672dce34351'
EDITS = [
    {'before': "_DATA\tsegment word public 'DATA'\n_DATA\tends",
     'after': "_DATA\tsegment word public 'DATA'\n\textrn\t_g_8ED8:byte\n_DATA\tends", 'count': 1},
    {'before': '\tadd bx, 8ED8h', 'after': '\tadd bx, offset DGROUP:_g_8ED8', 'count': 4},
]
RELOCATION = dict(segment='S01B_TEXT', offsets=SITES, count=4, target_kind='external',
                  target='_g_8ED8', encoded_addend='0000', displacement=0,
                  frame_kind='group', frame='DGROUP', original_value=0x8ED8,
                  mono_base_operand=True)
EXPECTED = {'DGROUP': '35', 'LITERAL': 'a5', 'DATA': 'c7', 'TARGET': 'd3'}
# Root parsed the actual objects and independently rebuilt each from its literal
# recipe. These complete model identities include every contribution and fixup.
FIXTURE_MODELS = {
    'owner': '0eb26930e45b99add61a9643e5aa235337eeaae7f8614b89a0091f7eecdc750c',
    'crt': 'abaf535254dfa44adf9fe933faa15f5cbfe08e3917a2ff92c49341c1fea15b3e',
    'DGROUP': '7933b513adccf6e14f6bf20cf57d70db64acdfbd25b9ebe6108d7a8614990d6d',
    'LITERAL': 'f26e263d03d53ee0e7339e0e1eb144db7a8122e6afd966f631cf22ee7fd2ad88',
    'DATA': '47c0ce9c883c1149b54e05458c8d877a5a2bcf066237c8db86a9d5e444e1ec4b',
    'TARGET': '7f7f3229e14035064494fd5699445edcc64ea111fc8ffb4e31eaa59e694a25c5',
}
ENTRY_SS_PROOFS = {
    'work/source-only-dos/structural-audits-v30/mono-entry-ss-v32/receipt.json':
        '5b9d53561f06cdea646b503e063674cd9ba547d2256f64a06cc12c13b8a5859f',
    'work/source-only-dos/structural-audits-v30/mono-entry-ss-v32/correction-addendum-v1.json':
        'de293c2aac4569155d717d6c58fa3db39bb6a77d004cfab8d0640596fe020737',
    'work/source-only-dos/structural-audits-v30/root-frontier-review.json':
        'd96d9207e0f656c56a5b68ce11ef55507c56b5c8869189579d9831b61036c3dd',
}
OWNER_SOURCE = """NULL segment word public 'BEGDATA'
db 0
NULL ends
PREFIX segment word public 'DATA'
public FrameMarker, LiteralMarker
db 0AEh dup (?)
FrameMarker db 0C7h
db 8ED7h dup (?)
LiteralMarker db 0A5h
PREFIX ends
_DATA segment para public 'DATA'
public _g_8ED8, _g_8EC0
_g_8ED8 label byte
db 4 dup (?)
_g_8EC0 label byte
db 0FCh dup (?)
db 35h
db 3 dup (?)
db 0D3h
_DATA ends
DGROUP group NULL, PREFIX, _DATA
end
"""


def checker_source(variant):
    expression = {'DGROUP': 'OFFSET DGROUP:_g_8ED8', 'DATA': 'OFFSET _DATA:_g_8ED8',
                  'TARGET': 'OFFSET DGROUP:_g_8EC0', 'LITERAL': '8ED8h'}[variant]
    return """_DATA segment para public 'DATA'
extrn _g_8ED8:byte
extrn _g_8EC0:byte
_DATA ends
DGROUP group _DATA
CHECK_TEXT segment word public 'CODE'
assume cs:CHECK_TEXT, ds:DGROUP
public _FrameProbe
_FrameProbe proc far
push bx
push ds
mov ax, seg DGROUP
mov dx, ss
cmp ax, dx
jne BadStack
mov dx, ds
cmp ax, dx
jne BadStack
mov bx, 100h
add bx, """ + expression + """
mov al, byte ptr ss:[bx]
jmp HaveResult
BadStack:
mov al, 0EEh
HaveResult:
mov byte ptr cs:Observed, al
push ds
push cs
pop ds
mov dx, offset Observed
mov cx, 1
mov bx, 1
mov ah, 40h
int 21h
pop ds
pop ds
pop bx
retf
_FrameProbe endp
Observed db 0
CHECK_TEXT ends
end
"""


def need(ok, detail):
    if not ok:
        raise ValueError('monochrome symbolic base: ' + detail)


def review(binding, module=None, symbols=None):
    if binding.get('module') != 'S01:328E' and not binding.get('mono_base_operands'):
        return
    need(binding.get('module') == 'S01:328E' and binding.get('mono_base_operands') is True
         and binding.get('source') == 'src/S01/m328E.asm'
         and binding.get('source_sha256') == SOURCE_SHA
         and binding.get('edits') == EDITS and binding.get('relocations') == [RELOCATION]
         and binding.get('exports') == [] and not binding.get('communals')
         and not any(binding.get(k) for k in ('reframes', 'local_reframes', 'segment_corrections',
                                             'code_offset_reframes', 'debug_contributions')),
         'unreviewed source edits, storage or exact four-site set')
    if module is not None:
        need(module['source'] == 'src/S01/m328E.asm' and module['seg'] == 0x328E,
             'canonical module changed')
    if symbols is not None:
        anchor = symbols['data']['g_8ED8']
        need((anchor['seg'], anchor['off']) == (0x55B3, 0x8ED8), 'registry anchor changed')


def read_pin(item):
    path = Path(item['path'])
    if not path.is_absolute():
        path = ROOT / path
    raw = path.read_bytes()
    need(len(raw) == item['size'] and hashlib.sha256(raw).hexdigest() == item['sha256'],
         'raw evidence identity changed: ' + item['path'])
    return raw


def parse_map(text):
    """Independent parser of both public tables and physical segment origins."""
    segments, publics = {}, {'name': {}, 'value': {}}
    table, origin = None, None
    for line in text.splitlines():
        segment = re.fullmatch(r'\s*([0-9A-F]+)H\s+([0-9A-F]+)H\s+([0-9A-F]+)H\s+'
                               r'(\S+)\s+(\S+)(?:\s+(\S+))?\s*', line, re.I)
        if segment:
            a, b, n, name, cls, group = segment.groups()
            need(name not in segments, 'duplicate map segment')
            segments[name] = dict(start=int(a, 16), stop=int(b, 16), length=int(n, 16),
                                  cls=cls, group=group)
        if 'Publics by Name' in line:
            table = 'name'
        elif 'Publics by Value' in line:
            table = 'value'
        group = re.fullmatch(r'\s*([0-9A-F]+):([0-9A-F]+)\s+DGROUP\s*', line, re.I)
        if group and table is None:
            need(origin is None, 'duplicate group origin')
            origin = int(group[1], 16) * 16 + int(group[2], 16)
        public = re.fullmatch(r'\s*([0-9A-F]+):([0-9A-F]+)\s+(\S+)\s*', line, re.I)
        if public and table:
            name = public[3].upper()
            need(name not in publics[table], 'duplicate map public')
            publics[table][name] = int(public[1], 16) * 16 + int(public[2], 16)
    need(origin is not None and '_DATA' in segments and 'PREFIX' in segments, 'map frames absent')
    data = segments['_DATA']['start'] - origin
    expected = {'FRAMEMARKER': 0x100, 'LITERALMARKER': 0x8FD8,
                '_G_8ED8': data, '_G_8EC0': data + 4}
    need(origin > 0 and data > 0x8ED8 and data % 16 == 0
         and all(segments[n]['group'] == 'DGROUP' for n in ('PREFIX', '_DATA')),
         'fixture is not shifted and paragraph aligned')
    for table in publics.values():
        need(all(table.get(name, -1) - origin == offset for name, offset in expected.items()),
             'map public origin or Name/Value table changed')
    return dict(group_origin=origin, data_group_offset=data, public_offsets=expected)


def require_contract(report, profile, tool):
    """Fresh link/runtime consequences supplement the static entry-SS proof."""
    rows = [r for r in report['translation_units'] if r.get('module') == 'S01:328E']
    if not rows:
        return
    need(len(rows) == 1 and rows[0].get('source_binding'), 'generated binding missing')
    review(rows[0]['source_binding'])
    c = report.get('mono_base_contract', {})
    need(c.get('root_reviewed') is True and c.get('all_required_checks_pass') is True
         and c.get('storage_provider') is False and c.get('owner_extent') is None
         and c.get('game_execution') is False and c.get('required_cases') == EXPECTED,
         'bounded admission scope changed')
    identities = {}
    from dos_source_bindings import runtime_component_path
    for p in c.get('inputs', []):
        key = runtime_component_path(p['path'])
        need(key not in identities or identities[key] == p['sha256'], 'conflicting evidence identities')
        identities[key] = p['sha256']
        read_pin(p)
    components = [(str(Path(tool['directory']) / name), digest) for name, digest in tool['files'].items()]
    components += [(r['path'], r['sha256']) for r in report['runtime_components']]
    need(all(identities.get(runtime_component_path(p)) == digest for p, digest in components),
         'selected linker/runtime component missing')
    need(all(identities.get(runtime_component_path(p)) == digest for p, digest in ENTRY_SS_PROOFS.items()),
         'static game entry-SS proof or its correction absent')
    sources = c.get('fixture_sources', {})
    need(set(sources) == {'owner', 'crt', *EXPECTED}, 'fixture source set changed')
    expected_sources = {'owner': OWNER_SOURCE, 'crt': 'extern void far FrameProbe(void);\n'
                        'int main(void) { FrameProbe(); return 0; }\n'}
    expected_sources.update({v: checker_source(v) for v in EXPECTED})
    for name, source in expected_sources.items():
        need(read_pin(sources[name]).decode('ascii').split() == source.split(),
             'fixture source changed (guard, frame, marker, read or call): ' + name)
        need(identities.get(runtime_component_path(sources[name]['path'])) == sources[name]['sha256'],
             'fixture source outside admitted evidence set')
    models = c.get('fixture_models', {})
    need(set(models) == set(FIXTURE_MODELS), 'complete fixture model set absent')
    for name, digest in FIXTURE_MODELS.items():
        need(models[name]['sha256'] == digest
             and identities.get(runtime_component_path(models[name]['path'])) == digest,
             'complete fixture object changed')
        need(json.loads(read_pin(models[name]))['independently_recompiled_equal'] is True,
             'fresh fixture object comparison absent')
    cases = c.get('cases', [])
    need(len(cases) == 8 and {(r['linker'], r['variant']) for r in cases} ==
         {(p, v) for p in ('rtlink400', 'rtlink610') for v in EXPECTED}, 'eight-case matrix changed')
    for row in cases:
        need(row['passed'] is True and row['dosbox_exit'] == 0
             and row['expected'] == row['actual'] == EXPECTED[row['variant']], 'predicted byte or execution changed')
        need(set(row['raw']) == {'observation', 'run_log', 'link_log', 'map'}, 'raw case evidence absent')
        need(all(identities.get(runtime_component_path(p['path'])) == p['sha256'] for p in row['raw'].values()),
             'runtime case outside admitted evidence set')
        raw = {name: read_pin(p) for name, p in row['raw'].items()}
        need(raw['observation'] == bytes.fromhex(EXPECTED[row['variant']])
             and raw['run_log'] == b'EXECUTED\r\n', 'raw observation or run missing')
        link_text = raw['link_log'].decode('latin1')
        need(not re.search(r'\bwrt\d{4}\b|\b(?:warnings?|errors?|fatal|undefined|unresolved|aborted)\b'
                           r'|cannot\s+open', link_text, re.I), 'link emitted diagnostics')
        need(parse_map(raw['map'].decode('latin1')) == row['root_map'], 'raw map differs from root review')
    proof = c.get('whole_tu_proof', {})
    need(proof == dict(status='PASS', segment_extents_unchanged=True, live_segment_extents_unchanged=True,
                       existing_publics_and_relocations_unchanged=True,
                       live_existing_publics_and_relocations_unchanged=True, reviewed_frame_corrections=[],
                       storage_bytes_unchanged=True, reviewed_debug_contributions={}, added_exports=[], added_communals=[],
                       symbolic_operand_checks=[dict(segment='S01B_TEXT', offset=offset, old_operand=0x8ED8,
                                                     target='_g_8ED8', frame='DGROUP', displacement=0, addend='0000')
                                                for offset in SITES])
         and c.get('negative_object_controls') == ['wrong_frame', 'wrong_target', 'incomplete_sites',
                                                   'changed_loop', 'extra_storage'], 'whole-object controls absent')
