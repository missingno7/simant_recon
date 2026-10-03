"""Archive the incomplete source-only checkpoint and preserved v17 identities.

This preservation audit is separate from the source-only compiler input process.
The DOS ZIP is explicitly the old hybrid package, never a standalone-build input.
"""
from pathlib import Path
import hashlib
import json
import shutil

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
    (OUT / 'paused-sdl3-v17.json').write_text(json.dumps(pause, indent=2) + '\n')
    for original, archived in (
        ('build/source-only-dos/build-report.json', 'compile-and-intake-v1.json'),
        ('build/source-only-dos-run.log', 'compile-and-intake-v1.log'),
        ('build/source-only-dos-validation.log', 'historical-validation-v1.log'),
        ('build/source-only-dos-hybrid-diagnostic.log', 'hybrid-diagnostic-v1.log'),
        ('docs/progress.json', 'historical-progress-v1.json'),
        ('docs/progress.md', 'historical-progress-v1.md')):
        if original.startswith('docs/progress') and (OUT / archived).exists():
            continue
        shutil.copyfile(ROOT / original, OUT / archived)
    report = json.loads((OUT / 'compile-and-intake-v1.json').read_text())
    if any(report['original_exe_bytes_used'].values()) or report['denied_oracle_reads']:
        raise ValueError('source-only invariant failed')
    if len(report['translation_units']) != 127 or any('object' not in r for r in report['translation_units']):
        raise ValueError('not all TUs compiled')
    print('Preserved v17 package/source hashes; archived incomplete DOS compile intake.')


if __name__ == '__main__':
    main()
