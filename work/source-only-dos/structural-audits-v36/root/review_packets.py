"""Parent read-only reopening of v36 evidence before production admission."""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'tools'))
from omf import OmfReader

def pin(path):
    raw = path.read_bytes()
    return dict(path=str(path), size=len(raw), sha256=hashlib.sha256(raw).hexdigest())

def walk(value):
    if isinstance(value, dict):
        if 'path' in value and 'sha256' in value:
            yield value
        for child in value.values():
            yield from walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk(child)

names = {
    'tail': ('dos_tail_clear_v36', ['functional-tail-candidate.json', 'pre-clear-prefix-review.json',
                                 'stock-crt-controls.json', 'full-dos-execution.json']),
    'window': ('dos_window_owner_v36', ['worker-contract.json', 'runtime-normalized.json',
                                      'loadall-extraction.json', 'source-census.json']),
    'selector': ('dos_critical_selector_v36', ['proposal-v36.json', 'fixture-receipt-v36.json',
                                            'whole-tu-v36.json']),
    'database': ('dos_database_exit_v36', ['receipt.json']),
    'clip': ('dos_clip_owner_v36', ['ownership-review.json', 'extent-controls.json']),
}
checks = {}
for kind, (directory, files) in names.items():
    packets = [json.loads((ROOT / 'build/workers' / directory / name).read_bytes()) for name in files]
    pins = list(walk(packets)); unique = {}
    for row in pins:
        path = Path(row['path'])
        if not path.is_absolute():
            path = ROOT / path
        actual = pin(path)
        assert actual['sha256'] == row['sha256'], (kind, path, 'hash drift')
        assert row.get('size', actual['size']) == actual['size'], (kind, path, 'size drift')
        unique[str(path).casefold()] = actual
    checks[kind] = dict(pin_occurrences=len(pins), unique_files=len(unique), all_pins_exact=True,
                        receipt_pins=[pin(ROOT / 'build/workers' / directory / name) for name in files])

selector = json.loads((ROOT / 'build/workers/dos_critical_selector_v36/fixture-receipt-v36.json').read_bytes())
assert selector['denied_oracle_reads'] == [] and selector['all_required_checks_pass'] is True
expected = {'byte_view': 'SELECTOR PASS width=1 signed=-128 entries=14 init=0',
            'initialized_one': 'SELECTOR FAIL init=1', 'word_width': 'SELECTOR FAIL width=2',
            'shifted_dgroup': 'SELECTOR PASS width=1 signed=-128 entries=14 init=0'}
assert {(r['linker'], r['case']) for r in selector['runtime_cases']} == {
    (p, c) for p in ('rtlink400', 'rtlink610') for c in expected}
for row in selector['runtime_cases']:
    assert row['stdout'] == expected[row['case']] + '\n'
    assert row['passed'] and row['clean_link'] and not row['diagnostics'] and row['emulator_exit'] == 0
obj = OmfReader(communals=True).read_file(ROOT / selector['compiler_controls']['SELVIEW']['object']['path'])
assert [{k: c[k] for k in ('name', 'kind', 'length')} for c in obj.communals] == [
    dict(name='_g_8CCB', kind='near', length=1)]
assert not obj.publics and not obj.linker_fixups and not any(obj.segment_lengths.values())

window = json.loads((ROOT / 'build/workers/dos_window_owner_v36/runtime-normalized.json').read_bytes())
assert {(r['profile'], r['case']) for r in window['cases']} == {
    (p,c) for p in ('rtlink400','rtlink610') for c in
    ('view45-root','view45-overlay','view46-counterexample','nonzero-initializer')}
for row in window['cases']:
    marker = 'FAIL_INITIAL_FAR_HOOKS\n' if row['case'] == 'nonzero-initializer' else (
        'PASS_SIGNED_WINDOW_INDEX\nPASS_45_VIEW_RESET_40_COPY_CALLBACK\n')
    assert row['run_log'] == marker and row['runner_returncode'] == 0 and row['link_diagnostics'] == []
    if row['case'].startswith('view45'):
        assert all(r['zero_before_crt'] and r['relocated_word_offsets'] == []
                   for r in row['unrelocated_mz_far_bytes_and_relocations'])
obj = OmfReader(communals=True).read_file(ROOT / 'build/workers/dos_window_owner_v36/window-functional-provider45.obj')
assert [{k:c[k] for k in ('name','kind','count','element_size','length')} for c in obj.communals] == [
    dict(name='_win_drawHooks',kind='far',count=45,element_size=4,length=180),
    dict(name='_win_offsets',kind='far',count=45,element_size=8,length=360)]
assert not obj.publics and not obj.linker_fixups and not any(obj.segment_lengths.values())
extraction = json.loads((ROOT / 'build/workers/dos_window_owner_v36/loadall-extraction.json').read_bytes())
assert extraction['canonical_and_effective_view_effects_equal']
assert extraction['extractions'][0]['view_effects'] == extraction['extractions'][1]['view_effects']
assert all('for (i = 0; i < 45; i++) win_offsets[i] = g_635C;' in r['function']
           and '_fmemset(win_drawHooks, 0, 0xb4);' in r['function'] for r in extraction['extractions'])

vm = json.loads((ROOT / 'build/workers/dos_tail_clear_v36/stock-crt-controls.json').read_bytes())
full = json.loads((ROOT / 'build/workers/dos_tail_clear_v36/full-dos-execution.json').read_bytes())
assert vm['controls_pass'] and len(vm['runs']) == 18 and vm['denied_original_reads'] == []
assert full['original_build_bytes'] == 0 and full['denied_original_reads'] == []
assert len(full['cases']) == 6 and all(r['result'] == 'PASS' for r in full['cases'])
checks['parent_review'] = dict(natural_providers_reparsed=True, window_minimum_spans_source_proven=True,
    selector_mutable_signed_byte_only=True, tail_vm_controls=18, tail_full_crt_fixture_runs=6,
    computed_alias_gates_required=True, standalone_game_linked=False, original_build_bytes=0)
(OUT / 'raw-review.json').write_text(json.dumps(checks, indent=2) + '\n')
print(json.dumps({kind: {k:v for k,v in row.items() if k!='receipt_pins'} for kind,row in checks.items()}, indent=2))
