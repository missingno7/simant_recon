"""Reviewed symbolic bindings for an independently laid out DOS image.

Changes apply to generated whole TUs only. No new storage, object edits or oracle
bytes are allowed. Verify assembled contributions against canonical source builds.
"""
from collections import Counter


def apply_binding(text, binding):
    for edit in binding['edits']:
        if text.count(edit['before']) != edit['count']:
            raise ValueError('DOS binding source context changed: ' + binding['module'])
        text = text.replace(edit['before'], edit['after'])
    return text


def review_addresses(binding, module, symbols):
    """Join source-owned relative locations to already reviewed symbol anchors."""
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
    for spec in binding.get('relocations', []):
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
    if (original.segment_lengths != generated.segment_lengths
            or set(original.segments) != set(generated.segments)
            or original.segment_defs != generated.segment_defs or original.groups != generated.groups):
        raise ValueError('DOS binding changed segment extents')
    public_key = lambda p: (p['name'], p['segment'], p['offset'])
    expected_publics = Counter(public_key(p) for p in original.publics)
    expected_publics.update(public_key(p) for p in binding.get('exports', []))
    if expected_publics != Counter(public_key(p) for p in generated.publics):
        raise ValueError('DOS binding changed an existing public or exported wrong storage')
    old_fixups = Counter(fixup_key(f) for f in original.linker_fixups)
    new_fixups = Counter(fixup_key(f) for f in generated.linker_fixups)
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
            if not segment.endswith('_TEXT'):
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
        before, after = original.segment_bytes(segment), generated.segment_bytes(segment)
        if len(before) != len(after) or any(a != b and (segment, i) not in fields
                                          for i, (a, b) in enumerate(zip(before, after))):
            raise ValueError('DOS binding changed bytes outside reviewed address operands')
    return {'status': 'PASS', 'segment_extents_unchanged': True,
            'existing_publics_and_relocations_unchanged': True,
            'storage_bytes_unchanged': True, 'added_exports': binding.get('exports', []),
            'symbolic_operand_checks': checks}
