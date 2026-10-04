from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
PROBE_PATH = ROOT / 'build/workers/dos_control_flag_words/probe-report.json'
V18_PATH = ROOT / 'work/source-only-dos/control-flag-words-v18/source-review-v18.json'
PROVIDER_PATH = ROOT / 'work/source-only-dos/control-flag-words-v18/provider.c'
INDEX_PATH = ROOT / 'work/source-only-dos/static-completeness/index-v1.json'
SYMBOLS_PATH = ROOT / 'layout/symbols.json'
TOOLCHAIN_PATH = ROOT / 'layout/toolchain.json'
TARGETS = {
    '_fd_50F6_0468': {'offset': 0x0468, 'offset_text': '0468'},
    '_fd_50F6_0370': {'offset': 0x0370, 'offset_text': '0370'},
    '_fd_50F6_024E': {'offset': 0x024E, 'offset_text': '024E'},
}
EXPECTED_OFFSETS = {'_fd_50F6_0468': '0000', '_fd_50F6_0370': '0002',
                    '_fd_50F6_024E': '0004'}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pin(path: Path, rel: str | None = None) -> dict:
    return {'path': rel or path.relative_to(ROOT).as_posix(),
            'sha256': sha(path), 'size': path.stat().st_size}


def resolve_repo_path(value: str) -> Path:
    path = Path(value.replace('\\', '/'))
    return path if path.is_absolute() else ROOT / path


def verify_pin(row: dict, label: str) -> Path:
    path = resolve_repo_path(row['path'])
    if not path.is_file():
        raise RuntimeError(f'missing pin ({label}): {row["path"]}')
    actual_sha = sha(path)
    actual_size = path.stat().st_size
    if actual_sha != row['sha256']:
        raise RuntimeError(f'hash changed ({label}): {row["path"]}')
    if 'size' in row and actual_size != row['size']:
        raise RuntimeError(f'size changed ({label}): {row["path"]}')
    return path


def expected_runtime(row: dict) -> str:
    output = row['expected_output']
    if row['program_nonzero_marker_expected']:
        output += '\nPROGRAM_NONZERO'
    return output


def audit_case(row: dict) -> dict:
    map_path = resolve_repo_path(row['map_path'])
    case_dir = map_path.parent
    log_path = case_dir / 'LINK.LOG'
    exe_path = case_dir / 'PASS.EXE'
    run_path = case_dir / 'RUN.LOG'
    for path in (map_path, log_path, exe_path, run_path):
        if not path.is_file() or path.stat().st_size == 0:
            raise RuntimeError(f'missing/empty raw build artifact: {path.relative_to(ROOT).as_posix()}')

    map_text = map_path.read_bytes().decode('latin1')
    map_lines = [line.strip() for line in map_text.splitlines()]
    target_rows = {}
    target_segments = set()
    for name, expected_offset in EXPECTED_OFFSETS.items():
        matches = [line for line in map_lines if line.lower().endswith(name.lower())]
        if len(matches) != 2 or set(matches) != {row['target_map_rows'][name]}:
            raise RuntimeError(f'{row["linker"]}/{row["case"]}: {name} has {len(matches)} map rows')
        actual_row = row['target_map_rows'][name]
        address = actual_row.split()[0]
        if ':' not in address:
            raise RuntimeError(f'{row["linker"]}/{row["case"]}: malformed public address: {actual_row}')
        segment, offset = address.split(':', 1)
        if offset.upper() != expected_offset:
            raise RuntimeError(f'{row["linker"]}/{row["case"]}: {name} resolved at {offset}')
        target_segments.add(segment.upper())
        target_rows[name] = actual_row
    if len(target_segments) != 1:
        raise RuntimeError(f'{row["linker"]}/{row["case"]}: target publics use multiple segments')

    bss_rows = [line for line in map_lines if 'FAR_BSS' in line and '00006H' in line]
    if bss_rows != row['far_bss_six_byte_map_rows']:
        raise RuntimeError(f'{row["linker"]}/{row["case"]}: FAR_BSS map row changed')
    guard_rows = [line for line in map_lines if line.lower().endswith('_zzguard')]
    if row['guard_word_map_row'] is None:
        if guard_rows:
            raise RuntimeError(f'{row["linker"]}/{row["case"]}: unexpected guard public')
    elif len(guard_rows) != 2 or set(guard_rows) != {row['guard_word_map_row']}:
        raise RuntimeError(f'{row["linker"]}/{row["case"]}: guard public row changed')

    log_text = log_path.read_bytes().decode('latin1')
    diagnostic_lines = [line.strip() for line in log_text.splitlines()
                        if re.search(r'^\s*(?:\*\*\s*)?(?:ERROR|WARNING|UNRESOLVED)\b',
                                     line, re.IGNORECASE)]
    if diagnostic_lines:
        raise RuntimeError(f'{row["linker"]}/{row["case"]}: linker diagnostics: {diagnostic_lines}')
    if 'OUTPUT PASS' not in log_text:
        raise RuntimeError(f'{row["linker"]}/{row["case"]}: full LINK.LOG lacks OUTPUT PASS')

    runtime_output = (run_path.read_bytes().decode('latin1')
                      .replace('\r\n', '\n').replace('\r', '\n').strip())
    expected_output = expected_runtime(row)
    if runtime_output != row['runtime_output'] or runtime_output != expected_output:
        raise RuntimeError(f'{row["linker"]}/{row["case"]}: runtime output normalization mismatch')
    if row['passed'] is not True:
        raise RuntimeError(f'{row["linker"]}/{row["case"]}: existing case result is not passed')

    return {
        'linker': row['linker'],
        'case': row['case'],
        'linker_diagnostics': diagnostic_lines,
        'linker_produced_executable': True,
        'linker_produced_map': True,
        'expected_owner_publics': sorted(TARGETS),
        'owner_publics_found_in_map': sorted(target_rows),
        'target_map_rows': target_rows,
        'target_public_segment': next(iter(target_segments)),
        'far_bss_six_byte_map_rows': bss_rows,
        'guard_word_map_row': guard_rows[0] if guard_rows else None,
        'expected_runtime_output': expected_output,
        'actual_runtime_output': runtime_output,
        'passed': True,
        'raw_build_artifact_source_pins': [
            {**pin(log_path), 'kind': 'full_linker_log', 'binary_payload_included': False},
            {**pin(map_path), 'kind': 'full_linker_map', 'binary_payload_included': False},
            {**pin(exe_path), 'kind': 'linked_test_executable_hash_only', 'binary_payload_included': False},
            {**pin(run_path), 'kind': 'full_runtime_log', 'binary_payload_included': False},
        ],
        'full_link_log_line_count': len(log_text.splitlines()),
        'full_map_line_count': len(map_lines),
    }


def main() -> None:
    probe = json.loads(PROBE_PATH.read_text(encoding='utf-8'))
    v18 = json.loads(V18_PATH.read_text(encoding='utf-8'))
    if v18['root_claimed'] or v18['admitted']:
        raise RuntimeError('V18 review is no longer an unadmitted candidate')

    source_inventory = v18['source_inventory']
    source_rows = source_inventory['source_hashes']
    if len(source_rows) != 156 or len({row['path'] for row in source_rows}) != 156:
        raise RuntimeError('V18 source graph is not 156 distinct source files')
    for row in source_rows:
        path = verify_pin(row, 'source graph')
        if path.suffix.lower() not in {'.c', '.asm'}:
            raise RuntimeError(f'non-source in source graph: {row["path"]}')

    canonical = {p.relative_to(ROOT).as_posix(): p for p in (ROOT / 'src').rglob('*')
                 if p.is_file() and p.suffix.lower() in {'.c', '.asm'}}
    if len(canonical) != 127 or not set(canonical).issubset({r['path'] for r in source_rows}):
        raise RuntimeError('canonical TU inventory differs from the pinned 156-source graph')

    strict_index = json.loads(INDEX_PATH.read_text(encoding='utf-8'))['entries']
    strict_pins = source_inventory['strict_receipt_pins']
    if len(strict_pins) != 29 or set(strict_index) != {r['name'] for r in strict_pins}:
        raise RuntimeError('strict receipt set is not 29 entries matching the source graph')
    source_hashes = {r['path']: r['sha256'] for r in source_rows}
    strict_sources = {}
    for row in strict_pins:
        receipt_path = verify_pin(row, 'strict receipt')
        entry = strict_index[row['name']]
        if entry['path'].replace('\\', '/') != row['path']:
            raise RuntimeError(f'strict receipt index path changed: {row["name"]}')
        receipt = json.loads(receipt_path.read_text(encoding='utf-8'))
        effective = receipt.get('source_override') if row['name'] == 'DrawBalloons' else receipt['registered_source']
        if not effective:
            raise RuntimeError(f'missing effective strict source: {row["name"]}')
        source_path = effective['path'].replace('\\', '/')
        source_pin = {'path': source_path, 'sha256': effective['sha256']}
        verify_pin(source_pin, 'effective strict source')
        if source_hashes.get(source_path) != effective['sha256']:
            raise RuntimeError(f'strict source is absent/different in 156-source graph: {source_path}')
        strict_sources[source_path] = effective['sha256']
    if len(strict_sources) != 29 or set(canonical) | set(strict_sources) != set(source_hashes):
        raise RuntimeError('canonical and strict source sets do not flatten to exactly 156 files')

    metadata_pins = source_inventory['metadata_pins']
    if len(metadata_pins) != 2:
        raise RuntimeError('expected strict-index and symbol-registry metadata pins')
    for row in metadata_pins:
        verify_pin(row, 'source metadata')
    verify_pin({'path': 'layout/symbols.json', 'sha256': sha(SYMBOLS_PATH)}, 'symbol registry')

    provider_hash = sha(PROVIDER_PATH)
    if provider_hash != v18['functional_owner']['provider_sha256']:
        raise RuntimeError('existing provider source differs from V18 pin')
    provider_definitions = v18['functional_owner']['definitions']
    if len(provider_definitions) != 3 or any(d['type'] != 'signed int far' or d['bytes'] != 2
                                               for d in provider_definitions):
        raise RuntimeError('provider does not describe exactly three signed two-byte far scalars')

    probe_pin = pin(PROBE_PATH)
    probe_pin['role'] = 'existing probe report; used as case index only'
    v18_pin = pin(V18_PATH)
    v18_pin['role'] = 'existing source review; unadmitted input'
    if not probe['all_checks_passed'] or len(probe['clean_link_runtime_cases']) != 8:
        raise RuntimeError('existing report does not describe eight passing runtime cases')

    tool_runtime_inputs = []
    for row in probe['tool_and_runtime_inputs']:
        path = resolve_repo_path(row['path'])
        if not path.is_file() or sha(path) != row['sha256']:
            raise RuntimeError(f'tool/runtime pin missing or changed: {row["path"]}')
        if path.stat().st_size != row['size']:
            raise RuntimeError(f'tool/runtime size changed: {row["path"]}')
        if row.get('expected_sha256') and row['sha256'] != row['expected_sha256']:
            raise RuntimeError(f'tool/runtime expected hash mismatch: {row["path"]}')
        tool_runtime_inputs.append(row)

    toolchain = json.loads(TOOLCHAIN_PATH.read_text(encoding='utf-8'))
    compiler_profile = toolchain['profiles']['msc600ax']
    include_dir = Path(compiler_profile['include_directory'])
    header_inputs = []
    for name, expected_hash in sorted(compiler_profile['include_files'].items()):
        path = include_dir / name
        if not path.is_file() or sha(path) != expected_hash:
            raise RuntimeError(f'pinned compiler header missing or changed: {path}')
        header_inputs.append({'path': str(path), 'sha256': expected_hash,
                              'size': path.stat().st_size, 'referenced_by_probe_sources': False})
    if len(header_inputs) != 55:
        raise RuntimeError(f'expected 55 pinned MSC headers, saw {len(header_inputs)}')
    source_texts = [resolve_repo_path(row['path']).read_text(encoding='latin1')
                    for row in probe['test_source_inputs']]
    included_names = {m.group(2).replace('\\', '/') for text in source_texts
                      for m in re.finditer(r'^\s*#\s*include\s*[<"]([^>"]+)[>"]', text, re.M)}
    if included_names:
        raise RuntimeError(f'probe sources unexpectedly include headers: {sorted(included_names)}')

    source_input_pins = []
    for row in probe['test_source_inputs']:
        path = verify_pin(row, 'probe source input')
        source_input_pins.append({**row, 'path': path.relative_to(ROOT).as_posix()})

    runtime_rows = []
    for row in probe['clean_link_runtime_cases']:
        runtime_rows.append(audit_case(row))
    if len(runtime_rows) != 8 or {(r['linker'], r['case']) for r in runtime_rows} != {
            (linker, case) for linker in ('rtlink400', 'rtlink610')
            for case in ('positive', 'wrong_type', 'wrong_extent', 'wrong_base')}:
        raise RuntimeError('direct artifact audit did not cover both profiles and all four cases')

    normalized_cases = {row['case']: row['expected_runtime_output'] for row in runtime_rows[:4]}
    if any({row['case']: row['expected_runtime_output'] for row in runtime_rows[i:i + 4]} != normalized_cases
           for i in (4,)):
        raise RuntimeError('the two linker profiles differ in normalized full runtime output')

    targets = []
    symbols = json.loads(SYMBOLS_PATH.read_text(encoding='utf-8'))['data']
    for name, spec in TARGETS.items():
        bare = name[1:]
        entry = symbols.get(bare)
        if not entry or entry.get('seg') != 0x50F6 or entry.get('off') != spec['offset']:
            raise RuntimeError(f'registered storage anchor changed: {name}')
        definition = next(d for d in provider_definitions if '_' + d['name'] == name)
        targets.append({'public': name, 'source_name': definition['name'],
                        'type': definition['type'], 'bytes': definition['bytes'],
                        'offset': spec['offset_text'],
                        'registered_segment': '50F6',
                        'registered_offset': spec['offset_text']})

    proposed_contract = {
        'module': 'source-owned:control-flag-words',
        'contract_key': 'control_flag_words_contract',
        'root_reviewed': False,
        'all_required_checks_pass': False,
        'communals': [
            {'name': name, 'kind': 'far', 'length': 2, 'count': 2, 'element_size': 1}
            for name in ('_fd_50F6_0468', '_fd_50F6_0370', '_fd_50F6_024E')
        ],
        'required_cases': normalized_cases,
        'inputs': tool_runtime_inputs,
        'expected_owner_publics': sorted(TARGETS),
        'case_count_per_profile': 4,
        'profiles': ['rtlink400', 'rtlink610'],
        'expected_contract_case_fields': {
            'expected': 'full runtime_output verbatim, including PROGRAM_NONZERO where present',
            'actual': 'full runtime_output verbatim, including PROGRAM_NONZERO where present',
            'linker_diagnostics': [],
            'linker_produced_executable': True,
            'linker_produced_map': True,
            'expected_owner_publics': sorted(TARGETS),
            'owner_publics_found_in_map': sorted(TARGETS),
        },
        'observed_case_matrix': runtime_rows,
    }

    report = {
        'schema': 'simant-dos-control-flag-words-source-review-v19',
        'status': 'SOURCE_BINDING_PROPOSAL_UNREVIEWED',
        'root_claimed': False,
        'root_reviewed': False,
        'admitted': False,
        'build_report_used_as_authority': False,
        'original_game_bytes_or_objects_used': False,
        'binary_artifacts_copied_or_embedded': False,
        'inputs': {'existing_probe_report': probe_pin, 'existing_v18_source_review': v18_pin},
        'source_inventory': {
            'canonical_translation_units': source_inventory['canonical_translation_units'],
            'canonical_c': source_inventory['canonical_c'],
            'canonical_asm': source_inventory['canonical_asm'],
            'effective_strict_sources': source_inventory['effective_strict_sources'],
            'draw_balloons_reviewed_correction': source_inventory['draw_balloons_reviewed_correction'],
            'distinct_source_files': len(source_rows),
            'source_hashes': source_rows,
            'strict_receipt_pins': strict_pins,
            'metadata_pins': metadata_pins,
            'named_reference_count': source_inventory['named_reference_count'],
            'numeric_address_candidate_count': source_inventory['numeric_address_candidate_count'],
            'computed_address_candidate_count': source_inventory['computed_address_candidate_count'],
            'assembly_numeric_candidate_count': source_inventory['assembly_numeric_candidate_count'],
            'verification': {'all_156_current_hashes_match': True,
                             'all_29_strict_receipts_and_effective_sources_match': True,
                             'canonical_tu_count_rechecked': len(canonical)},
        },
        'binding_proposal': {
            'provider': PROVIDER_PATH.relative_to(ROOT).as_posix(),
            'provider_sha256': provider_hash,
            'module': 'source-owned:control-flag-words',
            'storage_kind': 'three separate tentative far scalar definitions',
            'targets': targets,
            'no_storage_ownership_acceptance': True,
            'no_lifecycle_or_domain_claim': True,
            'dos_source_bindings_fragment': 'dos_source_bindings_v19.proposal.py.txt',
            'dos_source_bindings_fragment_sha256': sha(OUT / 'dos_source_bindings_v19.proposal.py.txt'),
            'contract': proposed_contract,
        },
        'scalar_omf_controls_unchanged': {
            'probe_report_path': PROBE_PATH.relative_to(ROOT).as_posix(),
            'owner_communal_rows': probe['owner_communal_rows'],
            'expected_communal_lengths': probe['expected_communal_lengths'],
            'positive_communal_shape_passed': probe['positive_communal_shape_passed'],
            'negative_controls': probe['negative_controls'],
            'all_three_controls_detected': all(row['detected'] for row in probe['negative_controls']),
        },
        'compiler_linker_header_and_runtime_inputs': {
            'tool_and_runtime_inputs': tool_runtime_inputs,
            'tool_and_runtime_input_count': len(tool_runtime_inputs),
            'msc600ax_header_pins': header_inputs,
            'msc600ax_header_count': len(header_inputs),
            'headers_referenced_by_probe_sources': sorted(included_names),
            'probe_source_inputs': source_input_pins,
        },
        'direct_original_build_artifact_audit': {
            'artifact_source_root': 'build/workers/dos_control_flag_words',
            'artifact_source_is_original_build_output': True,
            'source_is_work_raw_copy': False,
            'case_count': len(runtime_rows),
            'linker_profiles': ['rtlink400', 'rtlink610'],
            'cases_per_profile': ['positive', 'wrong_type', 'wrong_extent', 'wrong_base'],
            'all_full_linker_logs_clean': True,
            'all_full_maps_have_three_resolved_publics': True,
            'all_executables_exist_and_are_hash_pinned_only': True,
            'all_runtime_outputs_match_full_expected_strings': True,
            'missing_pins': [],
            'dirty_maps': [],
            'runtime_cases': runtime_rows,
        },
        'scope_limits': [
            'This is a source-binding and contract proposal for root review only; root_reviewed is false and no admission is claimed.',
            'The proposal records type, width, registered addresses, OMF controls, map rows and runtime fixture outputs; it makes no ownership acceptance or flag meaning, lifecycle, scheduling or domain claim.',
            'The compiler negatives are the existing OMF observations: byte-sized communal, four-byte long communal and initialized FAR_DATA public controls; their source results are reproduced unchanged.',
            'Every runtime expected/actual value is the full report runtime_output string, including PROGRAM_NONZERO for the three failing-program controls.',
            'Original ignored PASS.EXE files are represented only by direct build-path hash/size pins. No EXE/OBJ/LIB payload is copied or required by this proposal.',
        ],
    }
    out_path = OUT / 'source-review-v19.json'
    out_path.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'output': out_path.relative_to(ROOT).as_posix(),
                      'sources': len(source_rows), 'strict_receipts': len(strict_pins),
                      'headers': len(header_inputs), 'tool_runtime_inputs': len(tool_runtime_inputs),
                      'runtime_cases': len(runtime_rows),
                      'resolved_public_rows': sum(len(r['target_map_rows']) for r in runtime_rows),
                      'raw_artifact_pins': sum(len(r['raw_build_artifact_source_pins']) for r in runtime_rows),
                      'missing_pins': 0, 'dirty_maps': 0, 'root_reviewed': False,
                      'admitted': False}, indent=2))


if __name__ == '__main__':
    main()
