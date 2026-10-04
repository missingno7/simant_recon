"""Seal final parent evidence after validation and guarded intake joins."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
BASE = ROOT / 'work/source-only-dos/structural-audits-v36'

def pin(path):
    raw = path.read_bytes()
    return dict(path=str(path.relative_to(ROOT)).replace('\\', '/'),
                size=len(raw), sha256=hashlib.sha256(raw).hexdigest())

def write(path, value):
    assert not path.exists(), path
    path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')

log = (HERE / 'validate-rerun.log').read_text(encoding='utf-8', errors='replace')
assert 'VALIDATION PASS' in log and 'VALIDATION FAILED' not in log
discovery=json.loads((HERE/'suite-discovery.json').read_bytes())
assert discovery['repository_test_cases']==386
assert 'OK (skipped=2)' in log and 'codegen rules reproduced: 48' in log
report = json.loads((ROOT / 'build/source-only-dos-v36/build-report.json').read_bytes())
assert len(report['translation_units']) == 190 and len(report['unresolved_symbols']) == 12
assert sum(r['size'] for r in report['unresolved_data']) == 44
assert sum(r['size'] for r in report['historical_data_debt']) == 113
assert report['function_dispositions']['BEHAVIOR_EXACT_CONFIRMED'] == 29
assert report['function_dispositions']['CONTRACT_EQUIVALENT'] == 0
assert not any(report['original_exe_bytes_used'].values())
assert report['denied_oracle_reads'] == [] and not report['standalone_dos_executable']
assert json.loads((BASE / 'context.json').read_bytes())['guarded_reopen_denied_reads'] == []

paths = ['tools/source_only_dos.py', 'tools/dos_source_bindings.py', 'tools/dos_minimum_views.py',
    'tools/dos_startup_debt.py', 'tests/test_dos_minimum_views.py', 'layout/manifest.json',
    'work/source-only-dos/window-minimum-view-bindings-v36.json',
    'work/source-only-dos/selector-minimum-view-bindings-v36.json',
    'work/source-only-dos/window-minimum-view-contract-v36.json',
    'work/source-only-dos/selector-minimum-view-contract-v36.json',
    'work/source-only-dos/startup-tail-erasure-contract-v36.json',
    'work/source-only-dos/providers/window-initialized-views-v36.c',
    'work/source-only-dos/providers/critical-selector-byte-v36.c']
write(BASE / 'root/final-acceptance.json', dict(
    schema='simant-dos-parent-bounded-acceptance-v36', root_reviewed=True,
    verdict='SOURCE_VIEWS_AND_ORDINARY_STARTUP_ERASURE_ACCEPTED_WITH_OPEN_INTEGRATION_GATES',
    accepted_minimum_objects=['win_drawHooks[45]', 'win_offsets[45]', 'signed mutable g_8CCB byte'],
    functional_erasure=dict(id='common_tail_overlap_3', offset=1, size=2),
    historical_debt_unchanged=113, functional_data_debt=44, unresolved_imports=12,
    open_layout_gates=10, compiled_translation_units=190, source_providers=63,
    strict_behavior_confirmed=29, contract_only_algorithms=0,
    original_build_bytes=report['original_exe_bytes_used'], denied_oracle_reads=[],
    game_linked=False, game_executed=False, human_acceptance='PENDING',
    validation=dict(repository_tests=386, skipped=2, codegen_rules=48,
        runtime_members=90, runtime_code_bytes=12339, runtime_data_segments=38, runtime_data_bytes=2021,
        full_validation=pin(BASE / 'root/validate-rerun.log'),
        suite_cardinality=pin(BASE / 'root/suite-discovery.json'),
        initial_failure_retained=pin(BASE / 'root/validate.log'),
        integration_regression=pin(BASE / 'root/regression-test.log')),
    final_preflight=pin(ROOT / 'build/source-only-dos-v36/build-report.json'),
    accepted_inputs=[pin(ROOT / p) for p in paths],
    parent_corrections=[
        'Provider basename WINVIEW36 exceeded DOS 8.3 limit; final registry and binding use WINVW36.',
        'Tail contract explicitly includes the real pinned LibH runtime prerequisite.',
        'Legacy sparse test TU rows lack module; the new optional-module lookup preserves existing admission behavior.'],
    claim_limit='No defining historical TU/maximal extent, alias closure, complete game link, game execution or functional-source-oracle milestone. Actual linked-game startup review remains mandatory.'))

import shutil
target = BASE / 'root/seal_acceptance.py'
assert not target.exists()
shutil.copyfile(Path(__file__), target)
files = [pin(path) for path in sorted(BASE.rglob('*')) if path.is_file()
         and path.name != 'acceptance-index.json']
write(BASE / 'acceptance-index.json', dict(schema='simant-dos-parent-acceptance-byte-index-v36',
    frozen_worker_receipts_rewritten=False, files=files))
print('Sealed', len(files), 'archive file identities; 386 tests / 48 rules PASS.')
