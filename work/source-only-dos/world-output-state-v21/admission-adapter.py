#!/usr/bin/env python3
"""Read-only root-admission adapter for the world-output v21 scratch receipt.

This translates the worker receipt into the v20 source-only storage contract
shape. It never edits production tools, contracts, bindings, or probe outputs.
The one output is created exclusively so an existing receipt cannot be replaced.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / 'layout/manifest.json').is_file())
WORKER = ROOT / 'build/workers/dos_world_output_words_v21'
RUNTIME = WORKER / 'runtime'
PROBE_PATH = RUNTIME / 'probe-v21.json'
CANDIDATE_PATH = RUNTIME / 'candidate-v21.json'
AUDIT_PATH = WORKER / 'source-audit-v21.json'
NUMERIC_PATH = WORKER / 'numeric-alias-asm-review-v21.json'
OUTPUT = RUNTIME / 'admission-adapter-v21-compact.json'
V20_CONTRACT = ROOT / 'work/source-only-dos/sound-control-words-contract-v1.json'
V20_BINDINGS = ROOT / 'work/source-only-dos/sound-control-words-bindings-v1.json'
V20_REPLAY = ROOT / 'work/source-only-dos/sound-control-words-v20/replay.py'

sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / 'tools'))
import source_only_dos as dos  # noqa: E402
from omf import OmfReader  # noqa: E402


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def path_of(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def identity(path: Path) -> dict:
    raw = path.read_bytes()
    try:
        shown = path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        shown = str(path.resolve()).replace('\\', '/')
    return {'path': shown, 'sha256': digest(raw), 'size': len(raw)}


def check_pin(pin: dict) -> dict:
    path = path_of(pin['path'])
    if not path.is_file():
        return {'path': pin['path'], 'expected_sha256': pin['sha256'],
                'expected_size': pin['size'], 'exists': False, 'matches': False}
    actual = identity(path)
    matches = actual['sha256'] == pin['sha256'] and actual['size'] == pin['size']
    return {'path': pin['path'], 'expected_sha256': pin['sha256'],
            'expected_size': pin['size'], 'actual_sha256': actual['sha256'],
            'actual_size': actual['size'], 'exists': True, 'matches': matches}


def unique_pin_rows(rows: list[dict]) -> list[dict]:
    by_key = {}
    for row in rows:
        key = (row['path'].replace('\\', '/').lower(), row['sha256'], row['size'])
        by_key[key] = row
    return list(by_key.values())


def parse_map(raw: bytes) -> dict[str, dict[str, str]]:
    text = raw.decode('latin1')
    headings = list(re.finditer(r'(?im)^\s*Address\s+Publics by (Name|Value)\s*$', text))
    found: dict[str, dict[str, str]] = {'Name': {}, 'Value': {}}
    for index, heading in enumerate(headings):
        section = heading.group(1)
        end = headings[index + 1].start() if index + 1 < len(headings) else len(text)
        body = text[heading.end():end]
        for line in body.splitlines():
            row = re.match(r'\s*([0-9A-Fa-f]+:[0-9A-Fa-f]+)\s+(?:Res|Abs)\s+(\S+)', line)
            if row:
                found[section][row.group(2).lower()] = row.group(1).upper()
    return found


def address_pair(value: str) -> tuple[int, int]:
    segment, offset = value.split(':')
    return int(segment, 16), int(offset, 16)


def omf_summary(raw: bytes) -> dict:
    obj = OmfReader(communals=True).read(raw)
    live_segments = {'_DATA', 'CONST', '_BSS', 'FAR_DATA', 'FAR_BSS'}
    return {
        'communals': sorted(obj.communals, key=lambda row: row['name'].lower()),
        'publics': obj.publics,
        'segment_lengths': dict(sorted(obj.segment_lengths.items())),
        'segment_data_bytes': {name: len(data) for name, data in sorted(obj.segments.items())},
        'live_storage_fixups': [row for row in obj.fixups if row.get('segment') in live_segments],
        'nonempty_code_segments': {name: length for name, length in obj.segment_lengths.items()
                                   if name.endswith('_TEXT') and length},
        'groups': obj.groups,
    }


def case_artifacts(case: dict) -> dict[str, dict]:
    return {Path(row['path']).name.upper(): row for row in case['case_artifacts']}


def map_case(case: dict, pin_checks: list[dict]) -> dict:
    artifacts = case_artifacts(case)
    required_files = ('LINK.LOG', 'RUN.LOG', 'PROBE.MAP', 'PROBE.EXE')
    if any(name not in artifacts for name in required_files):
        raise ValueError(f"{case['linker']}/{case['case']}: raw runtime artifacts incomplete")
    paths = {name: path_of(artifacts[name]['path']) for name in required_files}
    raw = {name: path.read_bytes() for name, path in paths.items()}
    artifact_pin_results = {name: check_pin(artifacts[name]) for name in required_files}
    pin_checks.extend(artifact_pin_results.values())

    run_text = raw['RUN.LOG'].decode('latin1')
    link_text = raw['LINK.LOG'].decode('latin1')
    map_sections = parse_map(raw['PROBE.MAP'])
    expected_marker = case['expected_marker']
    marker_ok = (run_text == expected_marker + '\r\n'
                 and run_text == case['actual_marker_verbatim'])
    clean_tokens = ('unresolved external', 'undefined symbol', 'warning wrt', 'link error', 'fatal error')
    link_clean = bool(link_text.strip()) and not any(token in link_text.lower() for token in clean_tokens)
    required = sorted(set(case['required_publics']))
    public_matrix = {}
    all_required = True
    for section in ('Name', 'Value'):
        addresses = {name: map_sections[section].get(name.lower()) for name in required}
        missing = [name for name, address in addresses.items() if address is None]
        all_required &= not missing
        reported = case['both_public_sections'][section]
        if (reported.get('heading_present') is not True
                or reported.get('missing_required_publics') != []
                or reported.get('required_public_addresses') != addresses):
            all_required = False
        public_matrix[section] = {'heading_present': bool(map_sections[section]),
                                  'missing_required_publics': missing,
                                  'required_public_addresses': addresses}

    relations = []
    all_relations = True
    for relation in case['alias_target_address_relations']:
        alias, target = relation['alias'].lower(), relation['target'].lower()
        displacement = relation['expected_displacement_bytes']
        actuals = {}
        passed = True
        for section in ('Name', 'Value'):
            alias_address = map_sections[section].get(alias)
            target_address = map_sections[section].get(target)
            delta_ok = False
            if alias_address and target_address:
                a_seg, a_off = address_pair(alias_address)
                t_seg, t_off = address_pair(target_address)
                delta_ok = a_seg == t_seg and a_off == t_off + displacement
            actuals[f'{section.lower()}_alias_address'] = alias_address
            actuals[f'{section.lower()}_target_address'] = target_address
            actuals[f'{section.lower()}_passed'] = delta_ok
            passed &= delta_ok
        reported_addresses = {
            'name_alias_address': relation['name_alias_address'],
            'name_target_address': relation['name_target_address'],
            'value_alias_address': relation['value_alias_address'],
            'value_target_address': relation['value_target_address'],
        }
        if (passed is not relation['passed'] or reported_addresses != {
                'name_alias_address': actuals['name_alias_address'],
                'name_target_address': actuals['name_target_address'],
                'value_alias_address': actuals['value_alias_address'],
                'value_target_address': actuals['value_target_address']}):
            passed = False
        all_relations &= passed
        relations.append({'alias': alias, 'target': target,
                          'expected_offset_delta': displacement,
                          **actuals, 'passed': passed})

    actual_marker = run_text.rstrip('\r\n')
    runner_ok = case['runner_returncode'] == 0 and not case['timed_out']
    passed = (marker_ok and actual_marker == expected_marker and runner_ok
              and case['exe_created'] is True and link_clean and all_required
              and all_relations and case['expected_outcome_passed'] is True)
    if not passed:
        raise ValueError(f"{case['linker']}/{case['case']}: raw receipt validation failed")

    owner_names = sorted(name for name in required if name.startswith('_fd_50f6_'))
    alias_relations = [{
        'alias': row['alias'], 'target': row['target'],
        'expected_offset_delta': row['expected_offset_delta'],
        'alias_address_name_section': row['name_alias_address'],
        'target_address_name_section': row['name_target_address'],
        'alias_address_value_section': row['value_alias_address'],
        'target_address_value_section': row['value_target_address'],
        'passed': row['passed'],
    } for row in relations]

    case_names = {'typed_raw_saverec_zero_crt': 'typed_raw_positive',
                  'wrong_unsigned_long_consumer': 'wrong_signedness_unsigned_view',
                  'initialized_nonzero_owner': 'initialized_nonzero_owner',
                  'shifted_saverec_base': 'shifted_alias_base'}
    contract_case = {
        'linker': case['linker'], 'case': case_names[case['case']],
        'expected': expected_marker, 'actual': actual_marker, 'passed': True,
        'timed_out': False, 'runner_returncode': case['runner_returncode'],
        'linker_diagnostics': [], 'linker_produced_executable': True,
        'linker_produced_map': True, 'expected_owner_publics': owner_names,
        'owner_publics_found_in_map': sorted(name for name in map_sections['Name']
                                             if name.startswith('_fd_50f6_') and name in owner_names),
        'required_publics': required, 'both_public_sections': public_matrix,
        'map_public_sections': public_matrix,
        'all_required_publics_in_both_sections': all_required,
        'alias_map_relations': alias_relations,
    }
    if contract_case['expected_owner_publics'] != contract_case['owner_publics_found_in_map']:
        raise ValueError(f"{case['linker']}/{case['case']}: owner map public set differs")

    return {
        'linker': case['linker'], 'case': case['case'],
        '_normalized_contract_case': contract_case,
        'expected_marker': expected_marker, 'actual_marker_verbatim': run_text,
        'marker_matches_verbatim_bytes': marker_ok, 'runner_returncode': case['runner_returncode'],
        'actual_link_log_clean': link_clean, 'actual_executable_present': True,
        'actual_public_address_matrix': public_matrix,
        'alias_target_address_matrix': relations,
        'raw_artifacts': {name: {'path': artifacts[name]['path'],
                                 'sha256': artifacts[name]['sha256'],
                                 'size': artifacts[name]['size']}
                          for name in required_files},
        'validated': passed,
    }


def main() -> None:
    if OUTPUT.exists():
        raise FileExistsError(f'refusing to overwrite existing adapter receipt: {OUTPUT}')
    denied = dos.install_input_guard()
    probe = json.loads(PROBE_PATH.read_text(encoding='utf-8'))
    candidate = json.loads(CANDIDATE_PATH.read_text(encoding='utf-8'))
    audit = json.loads(AUDIT_PATH.read_text(encoding='utf-8'))
    numeric = json.loads(NUMERIC_PATH.read_text(encoding='utf-8'))
    v20 = json.loads(V20_CONTRACT.read_text(encoding='utf-8'))
    v20_bindings = json.loads(V20_BINDINGS.read_text(encoding='utf-8'))

    if (probe.get('root_reviewed') is not False or candidate.get('root_reviewed') is not False
            or audit.get('status') != 'research_only_candidate_pending_root_review'
            or candidate.get('all_required_checks_pass') is not True
            or probe.get('acceptance_checks', {}).get('all_156_pinned_source_paths_match') is not True
            or probe.get('acceptance_checks', {}).get('all_runtime_markers_match_under_both_linkers') is not True
            or probe.get('acceptance_checks', {}).get('all_required_publics_and_alias_addresses_match_in_both_map_sections') is not True
            or probe.get('runtime', {}).get('all_expected_outcomes_pass') is not True):
        raise ValueError('worker receipt is stale, incomplete, or not root-review-pending')

    # Recheck durable source and output identities. Tool/build observations from
    # execution are carried verbatim below; mutable tool hashes are not repinned.
    pin_checks: list[dict] = []
    source_pin_checks = [check_pin({'path': pin['path'], 'sha256': pin['expected_sha256'],
                                    'size': pin['size_expected']})
                         for pin in audit['source_pins']]
    pin_checks.extend(source_pin_checks)
    input_rows = unique_pin_rows(probe['source_tool_artifact_inputs'])
    mutable_tool_paths = {
        'tools/compiler.py', 'tools/omf.py', 'tools/source_only_dos.py',
        'tools/dos_source_bindings.py',
    }
    evidence_inputs = []
    executed_tool_observations = []
    for pin in input_rows:
        normalized = pin['path'].replace('\\', '/').lower()
        is_tool = (normalized.startswith('c:/tools/') or normalized in mutable_tool_paths
                   or normalized.startswith('tools/'))
        if is_tool:
            executed_tool_observations.append({**pin,
                'identity_role': 'captured by the executed probe; preserved verbatim',
                'current_hash_recheck': 'not required for mutable tools'})
        else:
            result = check_pin(pin)
            pin_checks.append(result)
            evidence_inputs.append(result)
    generated_pins = unique_pin_rows(probe['generated_artifacts'])
    generated_checks = [check_pin(pin) for pin in generated_pins]
    pin_checks.extend(generated_checks)

    if any(row['matches'] is False for row in pin_checks):
        raise ValueError('a source/evidence/output artifact pin no longer matches; executed observations preserved')
    if not all(row['match'] for row in audit['source_pins']):
        raise ValueError('the source audit itself recorded a mismatch')
    if numeric.get('all_source_pins_match') is not True or numeric.get('pinned_source_paths') != 156:
        raise ValueError('numeric/ASM audit does not cover the same 156 pinned sources')

    # Validate the v20 wrapper's durable reference without reinterpreting its
    # historical build/tool observations as current facts.
    v20_durable = [v20['probe_source'], v20['research_receipt'], v20['root_admission']]
    v20_provider = next(p for p in v20['inputs']
                        if p['path'] == 'work/source-only-dos/sound-control-words-v20/provider.c')
    v20_durable.append(v20_provider)
    v20_reference_checks = [check_pin(pin) for pin in v20_durable]
    v20_reference_checks.extend(identity(path) for path in (V20_CONTRACT, V20_BINDINGS, V20_REPLAY))
    if any(row.get('matches') is False for row in v20_reference_checks):
        raise ValueError('durable v20 contract/wrapper reference changed')

    owner_source_pin = probe['candidate_owner']['source']
    owner_obj_pin = probe['candidate_owner']['object']
    owner_raw = path_of(owner_obj_pin['path']).read_bytes()
    owner_omf = omf_summary(owner_raw)
    expected_communals = []
    owner_members = []
    for member in probe['candidate_owner']['members']:
        row = member['omf_communal']
        expected = {'name': row['name'], 'kind': 'far', 'length': member['source_derived_bytes'],
                    'count': member['source_derived_bytes'], 'element_size': 1}
        expected_communals.append(expected)
        if {k: row.get(k) for k in ('name', 'kind', 'length', 'count', 'element_size')} != expected:
            raise ValueError('candidate owner report has a noncanonical communal shape')
        owner_members.append({
            'symbol': member['symbol'], 'linker_name': row['name'],
            'source_type_views': member['source_typed_views'],
            'source_extent_bytes': member['source_derived_bytes'],
            'SaveRec_byte_view': member['SaveRec_view'], 'measured_omf': row,
        })
    actual_owner_shapes = [{k: row[k] for k in ('name', 'kind', 'length', 'count', 'element_size')}
                           for row in owner_omf['communals']]
    if actual_owner_shapes != sorted(expected_communals, key=lambda row: row['name'].lower()):
        raise ValueError('raw WORLDOUT OMF communals differ from the exact member set')
    if (owner_omf['publics'] or owner_omf['live_storage_fixups']
            or owner_omf['nonempty_code_segments']
            or any(owner_omf['segment_data_bytes'].get(name, 0)
                   for name in ('_DATA', 'CONST', '_BSS', 'FAR_DATA', 'FAR_BSS'))):
        raise ValueError('raw WORLDOUT OMF has live code/data/public/fixup contributions')
    if probe['candidate_owner']['source_function_definitions'] != 0:
        raise ValueError('candidate provider is not data-only')

    # Independently validate OMF-only extent controls and controls with actual
    # runtime negative markers. Width mismatches never become fabricated runs.
    contrasts = probe['contrasts']
    width = contrasts['wrong_width']
    width_results = []
    for field, expected_name, expected_len in (
            ('wide_object', '_fd_50F6_0200', 4),
            ('narrow_object', '_fd_50F6_1068', 2)):
        pin = width[field]
        raw = path_of(pin['path']).read_bytes()
        parsed = omf_summary(raw)
        found = next((row for row in parsed['communals'] if row['name'].lower() == expected_name.lower()), None)
        if found is None or found['length'] != expected_len:
            raise ValueError(f'wrong-width OMF control did not measure {expected_name} at {expected_len} bytes')
        width_results.append({'object': pin, 'measured_communal': found,
                              'expected_measured_bytes': expected_len,
                              'runtime_linked': False, 'runtime_failure_claimed': False})
    if width.get('runtime_linked') is not False or width.get('runtime_failure_claimed') is not False:
        raise ValueError('wrong width control must stay OMF-only')

    unsigned = contrasts['signedness']
    unsigned_obj = path_of(unsigned['unsigned_provider_object']['path']).read_bytes()
    unsigned_omf = omf_summary(unsigned_obj)
    signed_target = next(row for row in owner_omf['communals'] if row['name'] == '_fd_50F6_1068')
    unsigned_target = next(row for row in unsigned_omf['communals'] if row['name'] == '_fd_50F6_1068')
    if {k: signed_target[k] for k in ('kind', 'count', 'element_size', 'length')} != {
            k: unsigned_target[k] for k in ('kind', 'count', 'element_size', 'length')}:
        raise ValueError('signed/unsigned OMF shape comparison changed')

    init = contrasts['initializer']
    init_omf = omf_summary(path_of(init['owner_object']['path']).read_bytes())
    target_name = '_fd_50F6_0200'
    if (target_name in {row['name'] for row in init_omf['communals']}
            or target_name not in {row['name'] for row in init_omf['publics']}
            or init.get('initialized_data_payloads') != {'INITOWN7_DATA': '0100'}):
        raise ValueError('initialized owner OMF contrast differs')

    source_objects = audit['objects']
    expected_addresses = [f"50F6:{member['symbol'].rsplit('_', 1)[-1]}"
                          for member in probe['candidate_owner']['members']]
    if [row['address'] for row in source_objects] != expected_addresses:
        raise ValueError('provider/source-audit member ordering or identity differs')
    source_anchors = []
    for index, row in enumerate(source_objects):
        source_anchors.append({
            'source_audit_object_index': index, 'address': row['address'], 'symbol': row['token'],
            'complete_typed_declarations': row['typed_declaration_forms'],
            'complete_view_bytes': max(row['complete_view_bytes']),
            'producer_count': len(row['producer_receipts']),
            'producer_receipts': [{'function': r.get('function'), 'path': r['path'],
                                   'line': r['line'], 'text': r['text']}
                                  for r in row['producer_receipts']],
            'consumer_count': len(row['consumer_receipts']),
            'consumer_functions': sorted({r.get('function') for r in row['consumer_receipts']}),
            'SaveRec_rows': [{'path': r.get('path'), 'line': r.get('line'),
                              'bytes': r.get('size'), 'count': r.get('count'),
                              'table_index': r.get('table_index')}
                             for r in row['save_rec_rows']],
            'exact_base_aliases': row['exact_base_aliases'],
            'registered_interiors': row['registered_interiors'],
            'non_SaveRec_address_escapes': row['non_save_address_escape_receipts'],
            'ASM_identifier_occurrences': len(row['asm_token_occurrences']),
            'numeric_address_cue_occurrences': len(row['numeric_address_cue_occurrences']),
            'route_status': row['route_status'],
        })
    row0472 = next(row for row in source_objects if row['address'] == '50F6:0472')
    writes0472 = row0472['producer_receipts']
    if (len(writes0472) != 4 or row0472['consumer_receipts']
            or row0472['save_rec_rows'] or row0472['non_save_address_escape_receipts']
            or any(not re.search(r'=\s*0(?:L)?\s*;', row['text']) for row in writes0472)):
        raise ValueError('0472 zero-only closure evidence changed')

    cases = [map_case(case, pin_checks) for case in probe['runtime']['cases']]
    normalized_by_linker = {}
    for case in cases:
        normalized_by_linker.setdefault(case['linker'], []).append(case['_normalized_contract_case'])
    raw_case_receipts = [{key: value for key, value in case.items()
                          if key != '_normalized_contract_case'} for case in cases]
    required_cases = {
        'typed_raw_positive': 'PASS_TYPED_RAW_SAVEREC_ZERO_CRT',
        'wrong_signedness_unsigned_view': 'WRONG_UNSIGNED_VIEW_DETECTED',
        'initialized_nonzero_owner': 'INITIALIZED_NONZERO_OWNER_DETECTED',
        'shifted_alias_base': 'SHIFTED_SAVEREC_BASE_DETECTED',
    }
    for linker in ('rtlink400', 'rtlink610'):
        rows = normalized_by_linker.get(linker, [])
        if len(rows) != len(required_cases) or {row['case'] for row in rows} != set(required_cases):
            raise ValueError(f'{linker} runtime case matrix is incomplete')
        for row in rows:
            if row['expected'] != required_cases[row['case']] or row['actual'] != row['expected']:
                raise ValueError(f'{linker}/{row["case"]}: marker does not match normalized contract')

    owner_contract_rows = [
        {'name': row['name'], 'kind': row['kind'], 'length': row['length'],
         'count': row['count'], 'element_size': row['element_size']}
        for row in expected_communals]
    provider_spec = {
        'module': 'source-owned:world-output-state', 'basename': 'WORLDOUT', 'owner': None,
        'profile': 'msc600ax', 'flags': ['/AL', '/Os', '/Gs'],
        'research_probe_profile': probe['profile'], 'research_probe_flags': probe['flags'],
        'source': owner_source_pin, 'object': owner_obj_pin,
        'communals': owner_contract_rows,
        'historical_owner_module_claimed': False,
        'source_view_note': ('50F6:0472 has complete signed and unsigned long source views; '
                             'the provider uses a natural union over the proven four-byte extent.'),
    }

    # Preserve exactly what the prior root contract called historical mutable
    # build/tool observations. They are not refreshed from current files here.
    historical_observations = v20.get('historical_executed_driver_and_build_observations', [])
    preserved_history = json.loads(json.dumps(historical_observations))
    if preserved_history != historical_observations:
        raise ValueError('historical observations were transformed')

    all_ok = (all(row.get('matches') is True for row in pin_checks)
              and all(case['validated'] for case in cases)
              and not denied
              and all(value == 0 for value in probe['original_bytes_build_inputs'].values()))
    report = {
        'schema': 'simant-dos-world-output-admission-adapter-v21',
        'status': 'SCRATCH_ONLY_ADAPTER_VALIDATED_ROOT_REVIEW_PENDING' if all_ok else 'ADAPTER_VALIDATION_FAILED',
        'root_reviewed': False,
        'scope': 'Bounded adapter for source-owned world-output storage only; no production binding or contract file is changed.',
        'candidate': {'module': provider_spec['module'], 'basename': provider_spec['basename'],
                      'root_reviewed': False, 'all_required_checks_pass': all_ok,
                      'source_audit_status': audit['status'],
                      'candidate_status': candidate['status']},
        'provider_spec': provider_spec,
        'source_audit_receipt': {
            'path': str(AUDIT_PATH.relative_to(ROOT)).replace('\\', '/'),
            **identity(AUDIT_PATH),
            'numeric_alias_asm_report': {**identity(NUMERIC_PATH),
                'source_paths': numeric['pinned_source_paths'],
                'all_source_pins_match': numeric['all_source_pins_match'],
                'asm_source_paths': numeric['asm_source_path_count'],
                'asm_identifier_occurrences': numeric['assembly_target_identifier_occurrences'],
                'explicit_50f6_far_segment_hits': numeric['explicit_50F6_far_segment_numeric_hits'],
                'explicit_hex_offset_hit_rows': numeric['explicit_hex_offset_hit_rows'],
                'registered_interiors': 0},
            'canonical_TUs': 127, 'effective_strict_sources': 29,
            'unique_pinned_paths': 156, 'matched_pinned_paths': sum(row['matches'] for row in source_pin_checks),
            'objects': source_anchors,
            '0472_resolution': {
                'source_views': ['long far', 'unsigned long far'], 'source_derived_bytes': 4,
                'observed_store_count': len(writes0472), 'all_observed_values_are_zero': True,
                'direct_reads': 0, 'SaveRec_rows': 0, 'address_escapes': 0,
                'signedness_observable_in_pinned_graph': False,
                'claim_limit': 'Storage/view only; purpose, nonzero range, lifetime and persistence remain unknown.'},
        },
        'compiler_controls': {
            'research_provider_compile': {
                'profile': probe['profile'], 'flags': probe['flags'],
                'object': owner_obj_pin, 'measured_communals': owner_omf['communals'],
                'data_only': not owner_omf['publics'] and not owner_omf['live_storage_fixups']
                    and not owner_omf['nonempty_code_segments']
                    and not any(owner_omf['segment_data_bytes'].get(n, 0)
                                for n in ('_DATA', 'CONST', '_BSS', 'FAR_DATA', 'FAR_BSS')),
                'live_code_definitions': 0},
            'source_only_provider_profile': {'profile': 'msc600ax', 'flags': ['/AL', '/Os', '/Gs'],
                'expected_measured_communals': owner_contract_rows,
                'basis': 'Matches the v20 reviewed source-only provider compiler context; root build must measure this exact shape.'},
            'wrong_width_controls_omf_only': width_results,
            'wrong_width_runtime_failure_claimed': False,
            'signedness': {'unsigned_provider_object': unsigned['unsigned_provider_object'],
                'raw_signed_owner_omf_shape': {k: signed_target[k] for k in ('kind','count','element_size','length')},
                'raw_unsigned_owner_omf_shape': {k: unsigned_target[k] for k in ('kind','count','element_size','length')},
                'same_omf_shape': True,
                'runtime_negative_case': 'wrong_signedness_unsigned_view',
                'marker': required_cases['wrong_signedness_unsigned_view'],
                'limit': 'OMF carries no C signedness; the 0472 source-proven union is not the wrong-signedness control.'},
            'initialized_owner_negative': {'source': init['owner_source'], 'object': init['owner_object'],
                'target_communal_absent': init['target_communal_absent'],
                'target_initialized_public_present': init['target_initialized_public_present'],
                'initialized_data_payloads': init['initialized_data_payloads'],
                'runtime_marker': required_cases['initialized_nonzero_owner']},
            'shifted_SaveRec_base_negative': {'alias': contrasts['shifted_SaveRec_base']['shifted_alias'],
                'measured_displacement_bytes': contrasts['shifted_SaveRec_base']['map_displacement_bytes'],
                'runtime_marker': required_cases['shifted_alias_base']},
        },
        'required_cases': required_cases,
        'normalized_cases_by_linker': normalized_by_linker,
        'raw_runtime_receipts': raw_case_receipts,
        'pins': {
            'source_pin_checks': source_pin_checks,
            'additional_evidence_input_pin_checks': evidence_inputs,
            'generated_artifact_pin_checks': generated_checks,
            'executed_tool_input_observations_verbatim': executed_tool_observations,
            'all_nonmutable_source_and_artifact_pins_match': all(row.get('matches') is True for row in pin_checks),
            'probe_source_tool_artifact_inputs': input_rows,
        },
        'historical_reference': {
            'v20_contract': identity(V20_CONTRACT), 'v20_bindings': identity(V20_BINDINGS),
            'v20_replay_wrapper': identity(V20_REPLAY),
            'v20_durable_reference_checks': v20_reference_checks,
            'historical_executed_driver_and_build_observations_preserved_verbatim': preserved_history,
            'mutable_observations_rechecked_or_repinned': False,
            'wrapper_pattern': 'Validate durable admitted provider/probe pins, then create a fresh unadmitted unique replay directory.'},
        'oracle_boundary': {'source_only_input_guard_installed': True, 'denied_reads': denied,
            'original_bytes_build_inputs': probe['original_bytes_build_inputs']},
        'semantic_limits': probe['semantic_limits'],
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(report, stream, indent=2, ensure_ascii=False)
        stream.write('\n')
    print(json.dumps({'adapter': str(OUTPUT.relative_to(ROOT)), 'status': report['status'],
        'root_reviewed': False, 'source_pins_matched': report['source_audit_receipt']['matched_pinned_paths'],
        'generated_artifacts_revalidated': len(generated_checks),
        'runtime_cases_revalidated': len(cases), 'all_alias_matrix_relations_pass': all(
            r['passed'] for case in cases for r in case['alias_target_address_matrix']),
        'wrong_width_controls_omf_only': report['compiler_controls']['wrong_width_runtime_failure_claimed'] is False,
        'provider_spec': {'module': provider_spec['module'], 'basename': provider_spec['basename'],
                          'members': len(provider_spec['communals'])}}, indent=2))


if __name__ == '__main__':
    main()
