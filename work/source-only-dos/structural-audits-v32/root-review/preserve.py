"""Preserve frozen bounded investigations without admitting source or layout."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'work/source-only-dos/structural-audits-v32'
OUT.mkdir(exist_ok=True)

def pin(path):
    raw = path.read_bytes()
    return dict(path=path.relative_to(ROOT).as_posix(), sha256=hashlib.sha256(raw).hexdigest(), size=len(raw))

copies = []
def copy(source, destination):
    target = OUT / destination
    target.parent.mkdir(parents=True, exist_ok=True)
    raw = source.read_bytes()
    if target.exists():
        assert target.read_bytes() == raw, target
    else:
        target.write_bytes(raw)
    copies.append(dict(original=pin(source), archived=pin(target)))

for name in ('census_v38.py', 'extdef-census-v38.json', 'review-v38.md'):
    copy(ROOT / 'build/workers/dos_fdata_extdef_selection_v38' / name, 'heap-v38/' + name)
for name in ('run_order_v39.py', 'finalize_v39.py', 'file-order-v39.json', 'review-v39.md'):
    copy(ROOT / 'build/workers/dos_fdata_file_order_v39' / name, 'heap-v39/' + name)
for plan in ('baseline_current_order', 'root_171c_first'):
    for profile in ('rtlink400', 'rtlink610'):
        folder = Path(plan) / profile
        for name in ('T.LNK', 'LINK.LOG', 'SOURCE.MAP', 'RTLINK.CFG', 'RUN.BAT', 'dosbox.conf'):
            copy(ROOT / 'build/workers/dos_fdata_file_order_v39' / folder / name,
                 'heap-v39/' + folder.as_posix() + '/' + name)
for name in ('receipt.json', 'review.md', 'verify_receipt.py'):
    copy(ROOT / 'build/workers/dos_database_terminal_closure_v32' / name, 'database-v32/' + name)
folder = ROOT / 'build/workers/dos_historical_residue_forensics_v32'
index = json.loads((folder / 'stable-artifacts.json').read_bytes())
for item in index['artifacts']:
    source = Path(item['path'])
    assert pin(source)['sha256'] == item['sha256']
    if source.suffix.lower() in ('.obj', '.exe', '.lib'):
        continue
    copy(source, 'forensics-v32/' + source.relative_to(folder).as_posix())
copy(folder / 'stable-artifacts.json', 'forensics-v32/stable-artifacts.json')
for name in ('review_heap.py', 'review_forensics.py', 'preserve.py'):
    copy(Path(__file__).resolve().parent / name, 'root-review/' + name)
copy(ROOT / 'build/source-only-dos-forensics-root-v32.log', 'root-review/forensics.log')
copy(ROOT / 'build/source-only-dos-heap-root-v32.log', 'root-review/heap.log')
copy(ROOT / 'build/source-only-dos-database-root-v32.log', 'root-review/database.log')

report_path = ROOT / 'build/source-only-dos/build-report.json'
report = json.loads(report_path.read_bytes())
context = dict(schema='simant-v32-bounded-investigation-context', report=pin(report_path),
    accepted_source_only_checkpoint='e4227d5', status=report['status'],
    translation_units=[{k:r[k] for k in ('module','unit','basename','source','generated_source','object')}
                       for r in report['translation_units']],
    symbolic_aliases=report['symbolic_aliases'],
    function_dispositions=report['function_dispositions'],
    unresolved_imports=len(report['unresolved_symbols']),
    functional_data_bytes=sum(r['size'] for r in report['unresolved_data']),
    historical_data_bytes=sum(r['size'] for r in report['historical_data_debt']),
    open_layout_gates=sum(r['status']=='UNRESOLVED' for r in report['layout_dependencies']),
    original_exe_bytes_used=report['original_exe_bytes_used'],
    standalone_dos_executable=report['standalone_dos_executable'],
    new_source_admission=False, new_layout_admission=False, new_exact_function=False)
(OUT / 'context.json').write_bytes((json.dumps(context, indent=2) + '\n').encode())
root_review = dict(schema='simant-v32-root-bounded-review', root_reviewed=True,
    heap=dict(objects_reopened=188, live_external_fixups=22101, external_declarations=5949,
        partial_links_reopened=4, selected_runtime_models_reopened=454,
        conclusions=['No application __fheap EXTDEF or live external fixup.',
                     'Moving only root:171C first does not change either archive selection sequence.'],
        extraction_cause='UNRESOLVED', historical_79f0_owner='UNRESOLVED'),
    database=dict(verdict='UNRESOLVED', source_order_reviewed=True,
        facts=['At most three pre-display database calls precede callback initialization.',
               'The first early Punt uses zero g_9128, and its ordinary continuation uses zero g_9154.',
               'Source exit closure applies only after ordinary control-preserving callback returns.'],
        limit='Invalid zero-target execution may corrupt control or state or resume startup; no accepted contract excludes later fifth-call hazards.'),
    forensics=dict(fresh_parent_whole_TU_compiles=3, objects_identical=True,
        accepted_peers=[7,6,57], byte_residue=[2,3,6], private_data_fixups_and_relocations='PASS',
        new_hypothesis_families=0, expansion=False, exact_candidate=False,
        limit='Remaining stack-home/branch decisions do not establish a missing declaration, width, ABI, or physical owner.'),
    worker_receipts_unchanged=True, binary_artifacts_archived=False,
    production_or_canonical_changes=False, debt_discharged=0, game_executed=False)
(OUT / 'root-review.json').write_bytes((json.dumps(root_review, indent=2) + '\n').encode())
(OUT / 'preservation-index.json').write_bytes((json.dumps(dict(schema='simant-v32-preservation',
    copies=copies, observations=[pin(report_path)],
    archive_only=[pin(OUT/'context.json'),pin(OUT/'root-review.json')]), indent=2)+'\n').encode())
print(f'Preserved {len(copies)} unchanged text artifacts; no binaries, source admission or debt change')
