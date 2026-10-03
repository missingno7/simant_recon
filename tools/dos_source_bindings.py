"""Reviewed symbolic bindings for an independently laid out DOS image.

Changes apply to generated whole TUs only. Storage needs an explicit reviewed
communal contract; object edits and oracle bytes are forbidden. Compare whole
contributions against the same source before the reviewed edits.
"""
from collections import Counter
import hashlib
import json


# Each family was reviewed against the complete owner and every direct consumer,
# including the persistent byte-address views. This is not a declaration scanner.
SCALAR_FAMILIES = {
    'health': ('S08:35F5', ('HealthB', 'HealthR'), 'health_storage_contract'),
    'food_cycle': ('S08:35F5', ('FoodB', 'FoodR', 'Cycle'), 'food_cycle_storage_contract'),
    'population': ('root:0BE8', ('BpopT', 'RpopT'), 'population_storage_contract'),
    'lion': ('root:0AD9', ('AntsEatenByLions', 'InitialLions'), 'lion_storage_contract'),
}


def rtlink_alias_delta(offset):
    # RTLink interprets unsuffixed numeric DEFINE operands as hexadecimal.
    # In particular, writing decimal "12" would select byte 18, not byte 12.
    if not isinstance(offset, int) or offset < 0:
        raise ValueError('invalid RTLink alias offset')
    return f' + 0{offset:X}h' if offset else ''


def debug_fingerprint(obj, segment):
    """Account for an entire compiler debug contribution, including every fixup."""
    packet = {'definition': [s for s in obj.segment_defs if s['name'] == segment],
              'bytes_sha256': hashlib.sha256(obj.segment_bytes(segment)).hexdigest(),
              'fixups': sorted(fixup_key(f) for f in obj.linker_fixups if f['segment'] == segment)}
    return hashlib.sha256(json.dumps(packet, sort_keys=True).encode('ascii')).hexdigest()


def apply_binding(text, binding):
    for edit in binding['edits']:
        if text.count(edit['before']) != edit['count']:
            raise ValueError('DOS binding source context changed: ' + binding['module'])
        text = text.replace(edit['before'], edit['after'])
    return text


def review_addresses(binding, module, symbols):
    """Join source-owned relative locations to already reviewed symbol anchors."""
    scalar_names = set()
    if binding.get('scalar_storage'):
        families = binding['scalar_storage']['families']
        if not families or len(families) != len(set(families)):
            raise ValueError('unreviewed scalar storage family')
        for family in families:
            spec = SCALAR_FAMILIES.get(family)
            if not spec or binding['module'] != spec[0]:
                raise ValueError('unreviewed scalar source owner')
            scalar_names.update('_' + name for name in spec[1])
        if {c['name'] for c in binding.get('communals', [])} != scalar_names:
            raise ValueError('scalar storage member set changed')
    for communal in binding.get('communals', []):
        if binding.get('queue_storage'):
            if (binding['module'] != 'root:1FD2' or communal !=
                    {'name': '_input_queue', 'kind': 'near', 'length': 112}):
                raise ValueError('unreviewed near queue storage')
            continue
        anchor = symbols['data'][communal['name'][1:]]
        if (anchor['seg'], anchor['off']) != tuple(communal['historical_address']):
            raise ValueError('DOS communal symbol address changed')
        expected = ('far', 2, 1, 2) if communal['name'] in scalar_names else ('far', 64, 2, 128)
        if (communal['kind'], communal['count'], communal['element_size'], communal['length']) != expected:
            raise ValueError('unreviewed communal type or extent')
        if anchor['seg'] != 0x50F6 or any(s['seg'] == anchor['seg'] and
                anchor['off'] < s['off'] < anchor['off'] + communal['length']
                for s in symbols['data'].values()):
            raise ValueError('communal contains another registered storage view')
    for public in binding.get('exports', []):
        if public['segment'] in module['placements']:
            placement = module['placements'][public['segment']]
            segment, offset = placement['seg'], placement['off'] + public['offset']
        elif public['segment'].endswith('_TEXT'):
            segment = module['seg']
            offset = module['extent']['start'] - segment * 16 + public['offset']
        else:
            raise ValueError('unanchored DOS storage export')
        anchor = symbols['data'][public.get('registry_symbol', public['name'][1:])]
        if (segment, offset) != (anchor['seg'], anchor['off']):
            raise ValueError('DOS storage export conflicts with reviewed symbol address')
    for spec in binding.get('reframes', []):
        if (binding['module'] != 'root:1B73' or spec['target'] not in ('_g_9120', '_g_9122', '_g_9124')
                or symbols['data'][spec['target'][1:]]['seg'] != 0x55B3
                or (spec['old_frame_kind'], spec['old_frame'], spec['frame_kind'], spec['frame']) !=
                   ('segment', '_DATA', 'group', 'DGROUP')):
            raise ValueError('unreviewed assembly segment/group frame correction')
    for spec in binding.get('relocations', []):
        if spec.get('storage_pointer'):
            view = symbols['data']['g_5FFE']
            placement = module['placements']['_DATA']
            if (binding.get('queue_storage') != {'slots': 7, 'stride': 16, 'pointer_view': '_g_5FFE'}
                    or spec['target'] != '_input_queue' or spec['original_value'] != 0x91B0
                    or (placement['seg'], placement['off'] + spec['offset']) != (view['seg'], view['off'])
                    or (spec['segment'], spec['offset'], spec['owner'], spec['owner_offset'], spec['field_offset']) !=
                       ('_DATA', 24, '_g_5FF2', 12, 12)):
                raise ValueError('queue pointer is not its reviewed descriptor field')
            continue
        table = 'code' if spec.get('target_label') else 'data'
        name = spec.get('target_label', spec['target'])[1:]
        anchor = symbols[table][name]
        if spec['original_value'] != anchor['off']:
            raise ValueError('DOS operand conflicts with reviewed symbol address')
        if table == 'code' and (anchor['seg'] != module['seg'] or
                anchor.get('unit', 'root') != module['unit']):
            raise ValueError('DOS near callback targets another frame')


def fixup_key(fixup):
    # OMF indices can shift when an external/public is introduced. Compare the
    # resolved symbolic identities, location, width, frame and addend instead.
    return tuple(fixup[k] for k in ('segment', 'offset', 'width', 'loc',
        'self_relative', 'target_kind', 'target', 'displacement',
        'frame_kind', 'frame', 'encoded_addend'))


def communal_key(row):
    return tuple(row.get(k) for k in ('name', 'kind', 'count', 'element_size', 'length'))


def review_provider_source(text, provider):
    """Admit one recovered object, never an arbitrary generated stub module."""
    if (provider.get('module') != 'source-owned:driver-callback-table'
            or provider.get('owner') != '_driver_callback_table'
            or provider.get('communals') != [{'name': '_driver_callback_table', 'kind': 'near', 'length': 100}]
            or ' '.join(text.split()) != 'void (far * near driver_callback_table[25])();'):
        raise ValueError('unreviewed functional storage provider')


def verify_provider(obj, provider):
    expected = Counter(communal_key(c) for c in provider['communals'])
    if (Counter(communal_key(c) for c in obj.communals) != expected
            or obj.publics or obj.local_publics or obj.linker_fixups
            or any(obj.segment_lengths.values()) or any(obj.segments.values())
            or obj.externals != ['_driver_callback_table']
            or obj.external_scopes != ['communal']):
        raise ValueError('functional storage provider introduced code/data/extra allocation')
    return {'status': 'PASS', 'data_only': True, 'live_initialized_bytes': 0,
            'code_bytes': 0, 'communals': provider['communals'], 'publics': [], 'fixups': []}


def bind_communal_alias(spec, obj, row, symbols):
    provider = row.get('storage_provider', {})
    source = row['source']
    offset = spec['offset']
    if (provider.get('module') != 'source-owned:driver-callback-table'
            or spec['owner'] != '_driver_callback_table'
            or spec['source'].replace('\\', '/') != source['path'].replace('\\', '/')
            or spec['source_sha256'] != source['sha256']
            or spec['owner_size'] != 100 or spec['view_size'] != 4
            or not isinstance(offset, int) or offset % 4 or not 0 <= offset <= 96):
        raise ValueError('unreviewed communal slot view or source owner')
    verify_provider(obj, provider)
    historical = [0x55B3, 0x9128 + offset]
    anchor = symbols['data'][spec['alias'][1:]]
    if historical != [anchor['seg'], anchor['off']]:
        raise ValueError('communal slot view conflicts with reviewed registry address')
    return {'alias': spec['alias'], 'owner': spec['owner'], 'offset': offset,
            'kind': 'data', 'reason': 'reviewed source communal slot view',
            'module': row['module'], 'address': historical,
            'owner_size': 100, 'view_size': 4, 'source_anchor': spec['source_anchor']}


def require_callback_storage_contract(report, profile, tool):
    if not any(row.get('storage_provider') for row in report['translation_units']):
        return
    contract = report.get('callback_storage_contract', {})
    required = contract.get('required_cases', {})
    cases = [r for r in contract.get('cases', []) if r['linker'] == profile]
    identities = {p['path'].replace('\\', '/'): p['sha256'] for p in contract.get('inputs', [])}
    from pathlib import Path
    components = [(str(Path(tool['directory']) / name), digest) for name, digest in tool['files'].items()]
    components += [(r['path'], r['sha256']) for r in report['runtime_components']]
    if (not contract.get('all_required_checks_pass') or contract.get('root_reviewed') is not True
            or contract.get('slots') != 25 or contract.get('slot_bytes') != 4
            or contract.get('owner_bytes') != 100
            or Counter(required.values()) != Counter({'PASS': 1, 'FAIL': 3})
            or len(cases) != 4 or {r['case'] for r in cases} != set(required)
            or not all(r['passed'] and r['expected'] == r['actual'] == required[r['case']] for r in cases)
            or any(identities.get(path.replace('\\', '/')) != digest for path, digest in components)):
        raise ValueError('callback table lacks the selected linker/MSC startup contract')


def require_history_startup_contract(report, profile, tool):
    """Require the proven MSC-startup path for any admitted far history storage."""
    if not any(any(c['kind'] == 'far' and c.get('length') == 128 for c in r.get('source_binding', {}).get('communals', [])) for r in report['translation_units']
               if r.get('source_binding')):
        return
    contract = report.get('history_storage_contract', {})
    required = {'crt_overlay_zero_communal': 'CRT', 'crt_overlay_nonzero_contrast': 'CRT',
                'crt_byte_and_word_views': 'BYTE', 'crt_byte_and_word_nonzero_contrast': 'BYTE'}
    cases = [r for r in contract.get('cases', []) if r['linker'] == profile and r['case'] in required]
    identities = {p['path'].replace('\\', '/'): p['sha256'] for p in contract.get('inputs', [])}
    from pathlib import Path
    components = [(str(Path(tool['directory']) / name), digest) for name, digest in tool['files'].items()]
    components += [(r['path'], r['sha256']) for r in report['runtime_components']]
    if (not contract.get('all_required_checks_pass') or len(cases) != 4
            or {r['case'] for r in cases} != set(required)
            or not all(r['passed'] and r['startup'] == required[r['case']] for r in cases)
            or any(identities.get(path.replace('\\', '/')) != digest for path, digest in components)):
        raise ValueError('far history storage lacks the selected linker/MSC startup contract')


def require_scalar_startup_contracts(report, profile, tool):
    """Check the selected runtime and both address-view positives for each family."""
    families = {family for row in report['translation_units']
                for family in (row.get('source_binding') or {}).get('scalar_storage', {}).get('families', [])}
    from pathlib import Path
    components = [(str(Path(tool['directory']) / name), digest) for name, digest in tool['files'].items()]
    components += [(r['path'], r['sha256']) for r in report['runtime_components']]
    for family in families:
        _, members, key = SCALAR_FAMILIES[family]
        contract = report.get(key, {})
        required = contract.get('required_cases', {})
        cases = [r for r in contract.get('cases', []) if r['linker'] == profile]
        identities = {p['path'].replace('\\', '/'): p['sha256'] for p in contract.get('inputs', [])}
        if (not contract.get('all_required_checks_pass') or contract.get('root_reviewed') is not True
                or contract.get('members') != list(members)
                or contract.get('dos_type') != 'int far' or contract.get('word_bytes') != 2
                or Counter(required.values()) != Counter({'PASS': 2, 'FAIL': 4})
                or len(cases) != 6 or {r['case'] for r in cases} != set(required)
                or not all(r['passed'] and r['expected'] == r['actual'] == required[r['case']] for r in cases)
                or any(identities.get(path.replace('\\', '/')) != digest for path, digest in components)):
            raise ValueError(f'{family} scalar storage lacks the selected linker/MSC startup contract')


def require_queue_startup_contract(report, profile, tool):
    """Near queue storage requires the actual assembly/MSC startup ABI controls."""
    if not any(r.get('source_binding', {}).get('queue_storage') for r in report['translation_units']
               if r.get('source_binding')):
        return
    contract = report.get('queue_storage_contract', {})
    cases = [r for r in contract.get('cases', []) if r['linker'] == profile]
    required = {'canonical_source_positive': 'PASS', 'reviewed_dgroup_positive': 'PASS',
                'data_segment_frame_contrast': 'FAIL', 'queue_initializer_nonzero': 'FAIL',
                'buffer_pointer_plus_one': 'FAIL', 'capacity_eight': 'FAIL'}
    identities = {p['path'].replace('\\', '/'): p['sha256'] for p in contract.get('inputs', [])}
    from pathlib import Path
    components = [(str(Path(tool['directory']) / name), digest) for name, digest in tool['files'].items()]
    components += [(r['path'], r['sha256']) for r in report['runtime_components']]
    if (not contract.get('all_required_checks_pass') or len(cases) != len(required)
            or {r['case'] for r in cases} != set(required)
            or not all(r['passed'] and r['expected'] == r['actual'] == required[r['case']] for r in cases)
            or contract.get('contract') != {'ring_slots': 7, 'stride': 16, 'copy_bytes': 16, 'usable_capacity': 6}
            or any(identities.get(path.replace('\\', '/')) != digest for path, digest in components)):
        raise ValueError('near queue storage lacks the selected linker/MSC startup contract')


def require_assembly_frame_contract(report, profile, tool):
    if not any(r.get('source_binding', {}).get('reframes') for r in report['translation_units']
               if r.get('source_binding')):
        return
    contract = report.get('assembly_frame_contract', {})
    cases = [r for r in contract.get('cases', []) if r['linker'] == profile]
    identities = {p['path'].replace('\\', '/'): p['sha256'] for p in contract.get('inputs', [])}
    from pathlib import Path
    components = [(str(Path(tool['directory']) / name), digest) for name, digest in tool['files'].items()]
    components += [(r['path'], r['sha256']) for r in report['runtime_components']]
    expected = {'canonical_data_frame': 'FAIL', 'reviewed_dgroup_frame': 'PASS'}
    if (not contract.get('all_required_checks_pass') or len(cases) != 2
            or {r['case'] for r in cases} != set(expected)
            or not all(r['passed'] and r['expected'] == r['actual'] == expected[r['case']] for r in cases)
            or any(identities.get(path.replace('\\', '/')) != digest for path, digest in components)):
        raise ValueError('assembly frame correction lacks the selected linker/shifted DGROUP contract')


def bind_data_alias(spec, obj, row, module, symbols):
    """Bind a reviewed consumer view to a public in its one source owner."""
    if (module['source'] != spec['source'] or
            module['source_sha256'] != spec['source_sha256']):
        raise ValueError('data alias source owner changed')
    placement = module['placements'][spec['segment']]
    segment = (spec['segment'].replace('UNIT', row['basename'], 1)
               if spec['segment'].startswith('UNIT') else spec['segment'])
    public = [p for p in obj.publics if p['name'] == spec['owner']]
    if len(public) != 1 or (public[0]['segment'], public[0]['offset']) != (segment, spec['owner_offset']):
        raise ValueError('data alias public does not match its reviewed source location')
    if obj.segment_length(segment) != placement['size']:
        raise ValueError('data alias contribution extent changed')
    if not (0 <= spec['offset'] < spec['owner_size'] and spec['view_size'] > 0
            and spec['offset'] + spec['view_size'] <= spec['owner_size']
            and spec['owner_offset'] + spec['owner_size'] <= placement['size']):
        raise ValueError('data alias view extends outside its existing source object')
    address = symbols['data'][spec['alias'][1:]]
    historical = (placement['seg'], placement['off'] + spec['owner_offset'] + spec['offset'])
    if historical != (address['seg'], address['off']):
        raise ValueError('data alias view conflicts with reviewed consumer address')
    return {'alias': spec['alias'], 'owner': spec['owner'], 'offset': spec['offset'],
            'kind': 'data', 'reason': 'reviewed source owner/interior view',
            'module': row['module'], 'address': list(historical),
            'object_public': public[0], 'owner_size': spec['owner_size'],
            'view_size': spec['view_size'], 'source_anchor': spec['source_anchor']}


def verify_objects(original, generated, binding):
    debug = binding.get('debug_contributions', {})
    for segment, contract in debug.items():
        if (not binding.get('queue_storage') or segment not in ('$$SYMBOLS', '$$TYPES')
                or debug_fingerprint(original, segment) != contract['control']
                or debug_fingerprint(generated, segment) != contract['generated']):
            raise ValueError('unreviewed compiler debug contribution or relocation')
    defs = lambda obj: [s for s in obj.segment_defs if s['name'] not in debug]
    lengths = lambda obj: {s: n for s, n in obj.segment_lengths.items() if s not in debug}
    expected_communals = Counter(communal_key(c) for c in original.communals)
    expected_communals.update(communal_key(c) for c in binding.get('communals', []))
    if expected_communals != Counter(communal_key(c) for c in generated.communals):
        raise ValueError('DOS binding changed communal type, extent or ownership')
    if binding.get('scalar_storage'):
        names = {c['name'] for c in binding['communals']}
        expected_scopes = ['communal' if name in names else scope
                           for name, scope in zip(original.externals, original.external_scopes)]
        if (original.externals != generated.externals
                or expected_scopes != generated.external_scopes
                or not names <= {name for name, scope in zip(original.externals, original.external_scopes)
                                 if scope == 'external'}
                or [fixup_key(f) for f in original.linker_fixups] !=
                   [fixup_key(f) for f in generated.linker_fixups]):
            raise ValueError('scalar storage changed external scope or ordered relocations')
    if (lengths(original) != lengths(generated)
            or set(original.segments) != set(generated.segments)
            or defs(original) != defs(generated) or original.groups != generated.groups):
        raise ValueError('DOS binding changed segment extents')
    public_key = lambda p: (p['name'], p['segment'], p['offset'])
    expected_publics = Counter(public_key(p) for p in original.publics)
    expected_publics.update(public_key(p) for p in binding.get('exports', []))
    if expected_publics != Counter(public_key(p) for p in generated.publics):
        raise ValueError('DOS binding changed an existing public or exported wrong storage')
    original_fixups = [dict(f) for f in original.linker_fixups if f['segment'] not in debug]
    frame_checks = []
    for spec in binding.get('reframes', []):
        matches = [f for f in original_fixups if f['segment'] == spec['segment']
                   and f['offset'] == spec['offset'] and f['target_kind'] == 'external'
                   and f['target'] == spec['target']]
        if (binding['module'] != 'root:1B73' or len(matches) != 1
                or (spec['target'], spec['offset']) not in
                   (('_g_9120', 0xCBB), ('_g_9122', 0xCC0), ('_g_9124', 0xCC5))):
            raise ValueError('unreviewed assembly frame correction location')
        f = matches[0]
        if ((f['width'], f['loc'], f['self_relative'], f['frame_kind'], f['frame'],
                f['displacement'], f['encoded_addend']) !=
                (2, 'offset16', False, spec['old_frame_kind'], spec['old_frame'], 0, '0000')):
            raise ValueError('assembly frame correction changed a different operand')
        if (spec['frame_kind'], spec['frame']) != ('group', 'DGROUP'):
            raise ValueError('assembly frame correction is not DGROUP')
        f.update(frame_kind=spec['frame_kind'], frame=spec['frame'])
        frame_checks.append(spec)
    old_fixups = Counter(fixup_key(f) for f in original_fixups)
    new_fixups = Counter(fixup_key(f) for f in generated.linker_fixups if f['segment'] not in debug)
    if old_fixups - new_fixups:
        raise ValueError('DOS binding changed an existing relocation')
    additions = new_fixups - old_fixups
    actual = [f for f in generated.linker_fixups if additions[fixup_key(f)]]
    if len(actual) != sum(s['count'] for s in binding.get('relocations', [])):
        raise ValueError('DOS binding added unexpected relocations')
    remaining = actual[:]
    fields = set()
    checks = []
    for spec in binding.get('relocations', []):
        matches = [f for f in remaining if f['target_kind'] == spec['target_kind']
                   and f['target'] == spec['target']
                   and f['encoded_addend'] == spec['encoded_addend']
                   and f['displacement'] == spec['displacement']]
        if len(matches) != spec['count']:
            raise ValueError('DOS binding relocation target/addend mismatch')
        for f in matches:
            if (f['width'] != 2 or f['loc'] != 'offset16' or f['self_relative']
                    or f['frame_kind'] != spec['frame_kind']
                    or f['frame'] != spec['frame']):
                raise ValueError('DOS binding relocation frame/width mismatch')
            segment, offset = f['segment'], f['offset']
            if spec.get('storage_pointer'):
                owner = [p for p in generated.publics if p['name'] == spec['owner']]
                if (not binding.get('queue_storage') or len(owner) != 1
                        or (segment, offset) != (spec['segment'], spec['offset'])
                        or (owner[0]['segment'], owner[0]['offset']) != (segment, spec['owner_offset'])
                        or offset != spec['owner_offset'] + spec['field_offset']):
                    raise ValueError('DOS queue pointer replaced another storage field')
            elif not segment.endswith('_TEXT'):
                raise ValueError('DOS binding attempted to replace a storage field')
            raw = original.segment_bytes(segment)[offset:offset+2]
            if int.from_bytes(raw, 'little') != spec['original_value']:
                raise ValueError('DOS binding replaced a different historical operand')
            if spec.get('target_label'):
                public = next(p for p in generated.publics if p['name'] == spec['target_label'])
                if (public['segment'] != f['target'] or public['offset'] !=
                        f['displacement'] + int.from_bytes(bytes.fromhex(f['encoded_addend']), 'little')):
                    raise ValueError('DOS binding callback does not address its existing procedure')
            fields.update((segment, offset+i) for i in range(2))
            checks.append({'segment': segment, 'offset': offset,
                           'old_operand': spec['original_value'], 'target': f['target'],
                           'frame': f['frame'], 'displacement': f['displacement'],
                           'addend': f['encoded_addend']})
            remaining.remove(f)
    for segment in original.segments:
        if segment in debug:
            continue  # Entire bytes/definitions/fixups already checked by exact fingerprints.
        before, after = original.segment_bytes(segment), generated.segment_bytes(segment)
        if len(before) != len(after) or any(a != b and (segment, i) not in fields
                                          for i, (a, b) in enumerate(zip(before, after))):
            raise ValueError('DOS binding changed bytes outside reviewed address operands')
    return {'status': 'PASS', 'segment_extents_unchanged': not bool(debug),
            'live_segment_extents_unchanged': True,
            'existing_publics_and_relocations_unchanged': not bool(debug or frame_checks),
            'live_existing_publics_and_relocations_unchanged': not bool(frame_checks),
            'reviewed_frame_corrections': frame_checks,
            'storage_bytes_unchanged': not any(s.get('storage_pointer') for s in binding.get('relocations', [])),
            'reviewed_debug_contributions': debug, 'added_exports': binding.get('exports', []),
            'added_communals': binding.get('communals', []),
            'symbolic_operand_checks': checks}
