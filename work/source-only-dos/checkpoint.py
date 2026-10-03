"""Verify preservation and write a compact current source-only DOS receipt.

This preservation audit is separate from the source-only compiler input process.
The DOS ZIP is explicitly the old hybrid package, never a standalone-build input.
"""
from pathlib import Path
import hashlib
import json
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
    if len(report['translation_units']) != 127 or any('object' not in r for r in report['translation_units']):
        raise ValueError('not all TUs compiled')
    bound = [r for r in report['translation_units'] if r.get('source_binding')]
    if any(r.get('binding_verification', {}).get('status') != 'PASS' for r in bound):
        raise ValueError('source binding proof did not pass')
    logs = [pin(ROOT / p) for p in ('build/source-only-dos-run-v3.log',
        'build/source-only-dos-tests-v3.log', 'build/source-only-dos-validation-v3.log')]
    if not (ROOT / logs[1]['path']).read_text().strip().endswith('OK'):
        raise ValueError('source-only tests did not finish successfully')
    if not (ROOT / logs[2]['path']).read_text().strip().endswith('VALIDATION PASS'):
        raise ValueError('historical validation did not finish successfully')
    receipt = {'schema': 'simant-source-only-dos-compact-intake-v1',
        'canonical_source_checkpoint': '556a80d',
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
        'linker_alias_contract': pin(OUT / 'linker-alias-contract-v1.json'),
        'reviewed_data_aliases': [r for r in report['symbolic_aliases']
                                 if r['reason'] == 'reviewed source owner/interior view'],
        'binding_proofs': [{'module': r['module'], 'source': r['source'],
            'control_source': r['binding_control_source'], 'object': r['object'],
            **r['binding_verification']} for r in bound],
        'tool_inputs': [p for p in report['inputs'] if p['path'].startswith('tools')],
        'validation_logs': logs,
        'historical_validation': 'PASS', 'source_only_tests': '11 tests PASS',
        'claim_limit': 'Compile and symbolic binding proofs only; no complete link, runtime '
                       'equivalence or human acceptance. Full inventories are reproducible build output.'}
    (OUT / 'current-intake.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print('Verified preserved v17 hashes; wrote compact incomplete DOS intake (no source-tree copies).')


if __name__ == '__main__':
    main()
