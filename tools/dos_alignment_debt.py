"""The reviewed twelve-byte FAR_DATA paragraph gap, without a padding owner."""
from pathlib import Path

from omf import OmfReader


def require_contract(contract, profile=None, components=()):
    accepted = contract.get('accepted_module', {})
    rows = contract.get('controls', {}).get('linker_results', [])
    expected = {(p, n) for p in ('rtlink400', 'rtlink610') for n in (100, 112)}
    if (contract.get('root_reviewed') is not True
            or contract.get('all_required_checks_pass') is not True
            or accepted.get('module') != 'root:1F80'
            or accepted.get('profile') != 'msc600ax'
            or accepted.get('manifest_placement') != {'seg': 0x50EF, 'off': 0, 'size': 100}
            or accepted.get('far_data_segdef') != {'name': 'UNIT5_DATA', 'class': 'FAR_DATA',
                'alignment': 'paragraph', 'combine': 'public', 'length': 100}
            or len(rows) != 4 or {(r['linker'], r['array_size']) for r in rows} != expected
            or contract.get('extra_storage_bytes') != 0):
        raise ValueError('FAR_DATA lacks the reviewed paragraph-fill contract')
    for row in rows:
        data, bss = row['far_data'], row['far_bss']
        if (row.get('linker_diagnostics') != [] or row['gap_bytes'] != (12 if row['array_size'] == 100 else 0)
                or data['length'] != row['array_size']
                or data['end_exclusive_offset'] != data['start_offset'] + data['length']
                or bss['start_offset'] % 16 or bss['start_offset'] - data['end_exclusive_offset'] != row['gap_bytes']
                or row.get('outputs', {}).get('exe_size', 0) <= 0
                or len(row.get('map_rows_asserted', [])) != 2):
            raise ValueError('FAR_DATA paragraph-fill control or clean map changed')
    for linker in ('rtlink400', 'rtlink610'):
        pair = [r for r in rows if r['linker'] == linker]
        if pair[0]['far_bss']['start_offset'] != pair[1]['far_bss']['start_offset']:
            raise ValueError('FAR_DATA extent contrast moved the following paragraph')
    if profile is not None:
        import dos_source_bindings as bindings
        identities = {bindings.runtime_component_path(p['path']): p['sha256']
                      for p in contract['inputs'] + contract['pinned_tool_inputs']}
        if profile not in ('rtlink400', 'rtlink610') or any(
                identities.get(bindings.runtime_component_path(path)) != digest for path, digest in components):
            raise ValueError('FAR_DATA lacks the selected linker/runtime paragraph-fill proof')


def verify_source_object(root, report):
    """Recheck the actual generated TU; basename changes are harmless."""
    contract = report['far_data_alignment_contract']
    require_contract(contract)
    accepted = contract['accepted_module']
    rows = [r for r in report['translation_units'] if r['module'] == 'root:1F80']
    if len(rows) != 1:
        raise ValueError('FAR_DATA source owner changed')
    row = rows[0]
    if (row['source']['sha256'] != accepted['manifest_source_sha256']
            or row['generated_source']['sha256'] != row['source']['sha256']
            or row['flags'] != accepted['flags'] or row['profile'] != accepted['profile']
            or row.get('source_binding') or row.get('reviewed_bodies')):
        raise ValueError('FAR_DATA generated source or compile context changed')
    import hashlib
    object_path = Path(row['object']['path'])
    raw = (object_path if object_path.is_absolute() else root / object_path).read_bytes()
    if hashlib.sha256(raw).hexdigest() != row['object']['sha256']:
        raise ValueError('FAR_DATA generated object pin changed')
    obj = OmfReader(communals=True).read(raw)
    far_data = [s for s in obj.segment_defs if s['class'] == 'FAR_DATA']
    if len(far_data) != 1 or {k: far_data[0][k] for k in ('class', 'alignment', 'combine', 'length')} != {
            'class': 'FAR_DATA', 'alignment': 'paragraph', 'combine': 'public', 'length': 100}:
        raise ValueError('FAR_DATA current OMF extent/alignment changed')
    return {'status': 'PASS', 'module': row['module'], 'object': row['object'],
            'functional_fill_bytes': 12, 'extra_storage_bytes': 0,
            'historical_byte_identity_claimed': False}
