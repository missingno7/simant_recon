"""Verify preservation and write a compact current source-only DOS receipt.

This preservation audit is separate from the source-only compiler input process.
The DOS ZIP is explicitly the old hybrid package, never a standalone-build input.
"""
from pathlib import Path
import hashlib
import json
import re
from collections import Counter

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent


def pin(path):
    return {'path': path.relative_to(ROOT).as_posix(),
            'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'size': path.stat().st_size}


def main():
    migration_path = ROOT / 'build/whole-application-v17/migration.json'
    migration_pin = pin(migration_path)
    if migration_pin['sha256'] != '529c0988cf1bf18d76387566375f63444e305668493b1c3365251c67f4b37588':
        raise ValueError('v17 migration receipt changed')
    migration = json.loads(migration_path.read_text())
    provider_rows = []
    for row in migration['native_support']:
        archived = ROOT / 'build/whole-application-v17/inputs' / row['source']
        identity = pin(archived)
        if identity['sha256'] != row['source_sha256']:
            raise ValueError('v17 source snapshot changed: ' + row['source'])
        provider_rows.append({'source': row['source'], 'source_sha256': row['source_sha256'],
            'preserved_snapshot': identity, 'existing_receipt_role': row.get('module_kind'),
            'existing_receipt_admitted': row.get('admitted'),
            'dos_target_input': False,
            'consolidation_review': 'REVIEW_REQUIRED_BEFORE_REUSE',
            'reason': 'Preserve the specific v17 implementation and evidence. Its role label, '
                      'compilation and native replay do not themselves authorize a DOS semantic substitute.'})
    artifacts = [pin(ROOT / path) for path in (
        'build/whole-application-v17/report.json', 'build/whole-application-v17/simant-whole-sdl3.exe',
        'build/releases/simant-preview-v17/package-report.json',
        'build/releases/simant-preview-v17/simant-dos-oracle.zip',
        'build/releases/simant-preview-v17/simant-sdl3-preview.zip')]
    pause = {'schema': 'simant-portable-sdl3-pause-v1',
        'branch': 'codex/portable-sdl3', 'preserved_tag': 'portable-sdl3-v17-paused-20261003',
        'commit': 'c850830006e0b7d456bb500bf101dd432bbe8ee3',
        'status': 'PAUSED_PENDING_SOURCE_ONLY_DOS_HUMAN_ACCEPTANCE',
        'migration_receipt': migration_pin, 'artifacts': artifacts,
        'native_providers': provider_rows,
        'old_dos_package_proof': 'ORACLE_ASSISTED_HYBRID_ONLY',
        'scope': 'Preservation/provenance intake; no provider deleted, changed or admitted by this audit.'}
    pause_path = OUT / 'paused-sdl3-v17.json'
    if pause_path.exists():
        if json.loads(pause_path.read_text()) != pause:
            raise ValueError('preserved v17 receipt changed')
    else:
        pause_path.write_text(json.dumps(pause, indent=2) + '\n')
    report_path = ROOT / 'build/source-only-dos/build-report.json'
    report = json.loads(report_path.read_text())
    if any(report['original_exe_bytes_used'].values()) or report['denied_oracle_reads']:
        raise ValueError('source-only invariant failed')
    if len(report['translation_units']) != 151 or any('object' not in r for r in report['translation_units']):
        raise ValueError('not all TUs compiled')
    bound = [r for r in report['translation_units'] if r.get('source_binding')]
    if any(r.get('binding_verification', {}).get('status') != 'PASS' for r in bound):
        raise ValueError('source binding proof did not pass')
    providers = [r for r in report['translation_units'] if r.get('storage_provider')]
    if any(r.get('provider_verification', {}).get('status') != 'PASS' for r in providers):
        raise ValueError('source provider proof did not pass')
    if (report['function_dispositions']['BEHAVIOR_EXACT_CONFIRMED'] != 29
            or report['function_dispositions']['CONTRACT_EQUIVALENT']
            or report['function_dispositions']['UNRESOLVED']):
        raise ValueError('strict static function audit is incomplete')
    logs = [pin(ROOT / p) for p in ('build/source-only-dos-run-v16.log',
        'build/source-only-dos-tests-v16.log', 'build/source-only-dos-validation-v16.log')]
    test_log = (ROOT / logs[1]['path']).read_text().strip()
    if not re.search(r'(?m)^OK(?: \(skipped=2\))?$', test_log):
        raise ValueError('source-only tests did not finish successfully')
    test_counts = [int(n) for n in re.findall(r'Ran (\d+) tests', test_log)]
    if test_counts != [40, 314] or len(re.findall(r'(?m)^OK(?: \(skipped=2\))?$', test_log)) != 2:
        raise ValueError('split repository test boundary is incomplete')
    test_count = sum(test_counts)
    if not (ROOT / logs[2]['path']).read_text().strip().endswith('VALIDATION PASS'):
        raise ValueError('historical validation did not finish successfully')
    receipt = {'schema': 'simant-source-only-dos-compact-intake-v1',
        'source_only_base_checkpoint': 'bfe8fb7',
        'canonical_manifest': pin(ROOT / 'layout/manifest.json'),
        'full_local_report': pin(report_path),
        'reproduction': 'python tools/source_only_dos.py --compile --link --reuse --jobs 4',
        'status': report['status'], 'errors': report['errors'],
        'compiled_translation_units': len(report['translation_units']),
        'function_dispositions': report['function_dispositions'],
        'original_exe_bytes_used': report['original_exe_bytes_used'],
        'denied_oracle_reads': report['denied_oracle_reads'],
        'standalone_dos_executable': report['standalone_dos_executable'],
        'runnable': report['runnable'], 'human_acceptance': report['human_acceptance'],
        'unresolved_data_disposition_bytes': sum(r['size'] for r in report['unresolved_data']),
        'unresolved_symbols': len(report['unresolved_symbols']),
        'unresolved_symbol_categories': dict(Counter(r['required_resolution']
            for r in report['unresolved_symbols'])),
        'symbolic_aliases': len(report['symbolic_aliases']),
        'duplicate_publics': report['duplicate_publics'],
        'layout_dependencies': report['layout_dependencies'],
        'source_bindings': pin(OUT / 'source-bindings-v1.json'),
        'c_data_bindings': pin(OUT / 'c-data-bindings-v1.json'),
        'linker_alias_contract': pin(OUT / 'linker-alias-contract-v2.json'),
        'history_storage_bindings': pin(OUT / 'history-storage-bindings-v1.json'),
        'history_storage_contract': pin(OUT / 'history-storage-contract-v1.json'),
        'queue_storage_bindings': pin(OUT / 'queue-storage-bindings-v1.json'),
        'queue_storage_contract': pin(OUT / 'queue-storage-contract-v1.json'),
        'queue_lifetime_contract': pin(OUT / 'queue-lifetime-contract-v1.json'),
        'assembly_frame_bindings': pin(OUT / 'assembly-frame-bindings-v1.json'),
        'assembly_frame_contract': pin(OUT / 'assembly-frame-contract-v1.json'),
        'world_scalar_bindings': pin(OUT / 'world-scalar-bindings-v1.json'),
        'population_scalar_bindings': pin(OUT / 'population-owner-bindings-v1.json'),
        'lion_scalar_bindings': pin(OUT / 'lion-owner-bindings-v1.json'),
        'callback_table_bindings': pin(OUT / 'callback-table-bindings-v1.json'),
        'init_sim_scalar_bindings': pin(OUT / 'init-sim-scalar-bindings-v1.json'),
        'yellow_scalar_bindings': pin(OUT / 'yellow-scalar-bindings-v1.json'),
        'near_state_bindings': pin(OUT / 'near-state-bindings-v1.json'),
        'driver_ss_frame_bindings': pin(OUT / 'driver-ss-frame-bindings-v1.json'),
        'pattern_bank_bindings': pin(OUT / 'pattern-bank-bindings-v1.json'),
        'render_scalar_bindings': pin(OUT / 'render-scalar-bindings-v1.json'),
        'memory_far_storage_bindings': pin(OUT / 'memory-far-storage-bindings-v1.json'),
        'water_storage_bindings': pin(OUT / 'water-storage-bindings-v1.json'),
        'driver_local_frame_bindings': pin(OUT / 'driver-local-frame-bindings-v1.json'),
        'mono_pattern_prefix_bindings': pin(OUT / 'mono-pattern-prefix-bindings-v1.json'),
        'clip_pointer_bindings': pin(OUT / 'clip-pointer-bindings-v1.json'),
        'yard_scalar_bindings': pin(OUT / 'yard-scalar-bindings-v1.json'),
        'database_index_state_bindings': pin(OUT / 'database-index-state-bindings-v1.json'),
        'spider_counter_bindings': pin(OUT / 'spider-counter-bindings-v1.json'),
        'lion_array_storage_bindings': pin(OUT / 'lion-array-storage-bindings-v1.json'),
        'dgroup_rect_frame_bindings': pin(OUT / 'dgroup-rect-frame-bindings-v1.json'),
        'spider_control_storage_bindings': pin(OUT / 'spider-control-storage-bindings-v1.json'),
        'point_state_bindings': pin(OUT / 'point-state-bindings-v1.json'),
        'database_record_state_bindings': pin(OUT / 'database-record-state-bindings-v1.json'),
        'graphics_formula_bindings': pin(OUT / 'graphics-formula-bindings-v1.json'),
        'g2108_color_translation_bindings': pin(OUT / 'g2108-color-translation-bindings-v1.json'),
        'driver_indexed_address_bindings': pin(OUT / 'driver-indexed-address-bindings-v1.json'),
        'far_owner_admission_v15': pin(OUT / 'far-owner-admission-v15.md'),
        'ant_list_counts_bindings': pin(OUT / 'ant-list-counts-bindings-v1.json'),
        'colony_simulation_words_bindings': pin(OUT / 'colony-simulation-words-bindings-v1.json'),
        'player_locations_bindings': pin(OUT / 'player-locations-bindings-v1.json'),
        'ant_counters_timer_bindings': pin(OUT / 'ant-counters-timer-bindings-v1.json'),
        'language_string_list_pointers_bindings': pin(OUT / 'language-string-list-pointers-bindings-v1.json'),
        'dead_ant_coordinate_rings_bindings': pin(OUT / 'dead-ant-coordinate-rings-bindings-v1.json'),
        'ant_player_state_words_bindings': pin(OUT / 'ant-player-state-words-bindings-v1.json'),
        'display_mode_selector_bindings': pin(OUT / 'display-mode-selector-bindings-v1.json'),
        'display_mode_selector_admission': pin(OUT / 'display-mode-selector-admission-v16.md'),
        'resolved_source_state': report.get('resolved_source_state', []),
        'historical_data_debt_bytes': sum(r['size'] for r in report['historical_data_debt']),
        'resolved_initialized_data': report['resolved_initialized_data'],
        'strict_static_index': pin(OUT / 'static-completeness/index-v1.json'),
        'strict_static_audit': {name: {'status': row['status'], 'receipt': row['receipt']}
                               for name, row in report['strict_static_audit'].items()},
        'historical_behavior_registrations': report['historical_behavior_registrations'],
        'source_owned_history_arrays': [c for r in bound for c in r['source_binding'].get('communals', [])
                                       if c['kind'] == 'far' and c['length'] == 128],
        'source_owned_far_scalars': [c for r in bound for c in r['source_binding'].get('communals', [])
                                    if r['source_binding'].get('scalar_storage') and c['length'] == 2],
        'source_owned_water_arrays': [c for r in bound for c in r['source_binding'].get('communals', [])
                                     if r['source_binding'].get('array_storage') and c['length'] == 100],
        'storage_provider_proofs': [{'module': r['module'], 'source': r['source'], 'object': r['object'],
                                    **r['provider_verification']} for r in providers],
        'reviewed_data_aliases': [r for r in report['symbolic_aliases']
                                 if r['reason'] == 'reviewed source owner/interior view'],
        'binding_proofs': [{'module': r['module'], 'source': r['source'],
            'control_source': r['binding_control_source'], 'object': r['object'],
            **r['binding_verification']} for r in bound],
        'tool_inputs': [p for p in report['inputs'] if p['path'].startswith('tools')],
        'validation_logs': logs,
        'historical_validation': 'PASS',
        'source_only_tests': f'40 targeted tests included in {test_count} repository tests PASS (2 skips)',
        'claim_limit': 'Compile and symbolic binding proofs only; no complete link, runtime '
                       'equivalence or human acceptance. Full inventories are reproducible build output.'}
    (OUT / 'current-intake.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print('Verified preserved v17 hashes; wrote compact incomplete DOS intake (no source-tree copies).')


if __name__ == '__main__':
    main()
