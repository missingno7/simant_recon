"""Strictly scoped source storage views; computed layout effects stay gated.

No historical extent/placement inference and no original-image reads occur here.
The immutable worker receipts remain unadmitted; a separate parent contract
authorizes the minimal source-owned objects after raw artifact review.
"""
import hashlib
import json
from pathlib import Path
import re
import struct

WINDOW = 'source-owned:window-initialized-views'
SELECTOR = 'source-owned:critical-selector-byte'
SHAPES = {
    WINDOW: [dict(name='_win_drawHooks', kind='far', length=180, count=45, element_size=4),
             dict(name='_win_offsets', kind='far', length=360, count=45, element_size=8)],
    SELECTOR: [dict(name='_g_8CCB', kind='near', length=1)]}
CONTRACTS = {WINDOW: 'window_minimum_view_contract', SELECTOR: 'selector_minimum_view_contract'}
GATES = {WINDOW: 'window-index-resource-cross-owner-layout',
         SELECTOR: 'critical-selector-computed-alias-layout'}

def need(condition, message):
    if not condition:
        raise ValueError(message)

def read_pin(root, row):
    p = Path(row['path'])
    p = p if p.is_absolute() else root / p
    try:
        raw = p.read_bytes()
    except FileNotFoundError:
        raw = b''
    if len(raw) != row['size'] or hashlib.sha256(raw).hexdigest() != row['sha256']:
        # Worker paths remain exactly as observed. Use a hash-identical archived
        # artifact when scratch has been cleaned or a later experiment replaced
        # it. This is evidence preservation, not repinning to the new value.
        index = root / 'work/source-only-dos/structural-audits-v36/preservation-index.json'
        if index.exists():
            copies = json.loads(index.read_bytes())['files']
            matches = [r['archived'] for r in copies
                       if (root / r['original']['path']).resolve() == p.resolve()
                       and r['original']['sha256'] == row['sha256']]
            if len(matches) == 1:
                raw = (root / matches[0]['path']).read_bytes()
    need(len(raw) == row['size'] and hashlib.sha256(raw).hexdigest() == row['sha256'],
         'minimum-view evidence pin changed: ' + str(p))
    return raw

def load_pin(root, row):
    return json.loads(read_pin(root, row))

def path_key(path):
    return str(Path(path)).replace('\\', '/').casefold()

def file_named(rows, name):
    found = [row for row in rows if Path(row['path']).name.casefold() == name.casefold()]
    need(len(found) == 1, 'minimum-view control file missing/duplicated: ' + name)
    return found[0]

def map_publics(raw):
    found = {}
    for line in raw.decode('latin1').splitlines():
        match = re.match(r'\s*([0-9A-Fa-f]{4}):([0-9A-Fa-f]{4})\s+(?:Res\s+)?(\S+)', line)
        if match:
            found.setdefault(match[3], set()).add((int(match[1],16), int(match[2],16)))
    return found

def validate_window(root, runtime, extraction, proposal):
    expected = {'view45-root': 'PASS_SIGNED_WINDOW_INDEX\nPASS_45_VIEW_RESET_40_COPY_CALLBACK\n',
                'view45-overlay': 'PASS_SIGNED_WINDOW_INDEX\nPASS_45_VIEW_RESET_40_COPY_CALLBACK\n',
                'view46-counterexample': 'PASS_SIGNED_WINDOW_INDEX\nPASS_45_VIEW_RESET_40_COPY_CALLBACK\n',
                'nonzero-initializer': 'FAIL_INITIAL_FAR_HOOKS\n'}
    rows = runtime['cases']
    need(len(rows) == 8 and {(r['profile'], r['case']) for r in rows} == {
        (p,c) for p in ('rtlink400','rtlink610') for c in expected}, 'window control matrix changed')
    for row in rows:
        marker = expected[row['case']]
        need(row['runner_returncode'] == 0 and row['link_diagnostics'] == [] and row['run_log'] == marker,
             'window control outcome changed')
        artifacts = row['artifacts']
        need(read_pin(root, file_named(artifacts, 'RUN.LOG')).decode('ascii').replace('\r\n','\n') == marker,
             'window raw output differs from independent expectation')
        maps = map_publics(read_pin(root, file_named(artifacts, 'PROBE.MAP')))
        for name, addresses in row['map_owner_locations'].items():
            need(maps.get(name) == {tuple(a) for a in addresses}, 'window owner map addresses changed')
        image = read_pin(root, file_named(artifacts, 'PROBE.EXE'))
        need(image[:2] == b'MZ', 'window fixture is not MZ')
        count, header = struct.unpack_from('<HH', image, 6)
        relocation_table = struct.unpack_from('<H', image, 24)[0]
        relocations = {seg*16+off for off,seg in
                       (struct.unpack_from('<HH', image, relocation_table+4*i) for i in range(count))}
        if row['case'].startswith('view45') and row['owner_in_overlay'] is False:
            for shape in SHAPES[WINDOW]:
                address = next(iter(maps[shape['name']]))
                start = address[0]*16 + address[1]; size = shape['length']
                payload = image[header*16+start:header*16+start+size]
                need(len(payload)==size and payload==bytes(size) and not any(
                    r<start+size and r+2>start for r in relocations),
                    'window far initial-zero proof invalidated by payload/relocation')
    need(extraction['canonical_and_effective_view_effects_equal'] is True, 'window extraction changed')
    effects = dict(hook_clear='_fmemset(win_drawHooks, 0, 0xb4)',
        offset_reset_loop='for (i = 0; i < 45; i++) win_offsets[i] = g_635C;',
        offset_copy='_fmemcpy(win_offsets, f_171C_1B84(h), 0x140)')
    need(len(extraction['extractions'])==2 and all(r['view_effects']==effects
        for r in extraction['extractions']), 'window reset/copy spans changed')
    drafts = proposal['drafts']
    need(len(drafts)==2 and all(r['nondebug_code_data_publics_ordered_fixups_equal_baseline'] is True
        for r in drafts), 'window full-TU isolation proof changed')
    need(proposal['functional_view45_bytes']==dict(win_drawHooks=180,win_offsets=360),
         'window proposal source spans changed')

def validate_selector(root, runtime, whole):
    expected = {'byte_view':'SELECTOR PASS width=1 signed=-128 entries=14 init=0',
                'initialized_one':'SELECTOR FAIL init=1','word_width':'SELECTOR FAIL width=2',
                'shifted_dgroup':'SELECTOR PASS width=1 signed=-128 entries=14 init=0'}
    rows = runtime['runtime_cases']
    need(runtime['denied_oracle_reads']==[] and runtime['all_required_checks_pass'] is True,
         'selector fixture provenance changed')
    need(len(rows)==8 and {(r['linker'],r['case']) for r in rows} == {
        (p,c) for p in ('rtlink400','rtlink610') for c in expected}, 'selector control matrix changed')
    for row in rows:
        marker = expected[row['case']]
        need(row['expected']==marker and row['stdout']==marker+'\n' and row['passed'] is True
             and row['emulator_exit']==0 and row['clean_link'] is True and row['diagnostics'] is False,
             'selector control outcome changed')
        need(read_pin(root,file_named(row['files'],'RUN.LOG'))==(marker+'\r\n').encode('ascii'),
             'selector raw output differs from independent expectation')
        maps = map_publics(read_pin(root,file_named(row['files'],'PROBE.MAP')))
        owner = row['owner_map_public']
        need(maps.get('_g_8CCB') == {(owner['segment'],owner['offset'])}
             and {'__astart','_errno','_sys_nerr','_sys_errlist'} <= set(maps),
             'selector linked owner/CRT publics changed')
    need(len(runtime['shifted_DGROUP_controls'])==2 and all(r['owner_offset_changed'] is True
        and r['base']['offset']!=r['shifted']['offset'] for r in runtime['shifted_DGROUP_controls']),
         'selector shifted-layout positive missing')
    rule = whole['selector_binding']
    need(rule['exact'] is True and rule['candidate_extent']==54 and rule['unbound']==[]
         and rule['reloc_order']=='EXACT' and len(rule['fixups'])==6
         and rule['candidate_sha256']=='4f78c1abb0b4264afb395c29b5d8731a30874c54095d1af322f846dec72f2740',
         'selector full-generated-TU contribution proof changed')

def require_contract(root, contract, module, components=()):
    literals = dict(schema='simant-dos-minimum-source-view-contract-v36',module=module,
        root_reviewed=True,admitted=True,all_required_checks_pass=True,communals=SHAPES[module],
        historical_producer_or_placement_claimed=False,maximal_extent_claimed=False,
        computed_aliases_closed=False,game_lifecycle_claimed=False,original_game_bytes_used=0,
        required_unresolved_gate=GATES[module])
    need(all(contract.get(k)==v for k,v in literals.items()), 'minimum-view admission/type/scope changed')
    need(contract.get('control_pins') and contract.get('inputs'), 'minimum-view evidence missing')
    for row in contract['control_pins']:
        read_pin(root,row)
    admission = load_pin(root,contract['root_admission'])
    need(admission['root_reviewed'] is True and admission['computed_aliases_closed'] is False
         and admission['game_linked'] is False and admission['original_build_bytes']==0,
         'minimum-view parent decision changed')
    identities = {path_key(row['path']):row['sha256'] for row in contract['inputs']}
    need(all(identities.get(path_key(path))==digest for path,digest in components),
         'minimum-view selected runtime/linker identities changed')
    packets = {name:load_pin(root,row) for name,row in contract['receipts'].items()}
    if module==WINDOW:
        validate_window(root,packets['runtime-normalized.json'],packets['loadall-extraction.json'],
                        packets['functional-view-proposal.json'])
    else:
        validate_selector(root,packets['fixture-receipt-v36.json'],packets['whole-tu-v36.json'])
    return dict(status='PASS',module=module,minimum_source_view_bytes=sum(r['length'] for r in SHAPES[module]),
                computed_alias_gate=GATES[module],historical_maximum_extent_claimed=False)

def require_all(root, report, profile, tool):
    components=[(str(Path(tool['directory'])/name),digest) for name,digest in tool['files'].items()]
    components += [(r['path'],r['sha256']) for r in report['runtime_components']]
    modules={r.get('module') for r in report['translation_units']}
    for module,key in CONTRACTS.items():
        if module in modules:
            require_contract(root,report[key],module,components)
            gates=[r for r in report['layout_dependencies'] if r['id']==GATES[module]]
            need(len(gates)==1, 'minimum-view computed alias gate missing')
            gate=gates[0]
            if gate['status']=='RESOLVED':
                # A later, separately reviewed integration proof may close this
                # gate. The minimal storage admission cannot close it itself.
                closure=gate.get('root_reviewed_resolution',{})
                need(closure.get('status')=='PASS' and closure.get('root_reviewed') is True
                     and closure.get('evidence_pins'), 'minimum storage view silently waived its alias gate')
                for row in closure['evidence_pins']:read_pin(root,row)
            else:
                need(gate['status']=='UNRESOLVED', 'minimum-view alias gate status changed')
