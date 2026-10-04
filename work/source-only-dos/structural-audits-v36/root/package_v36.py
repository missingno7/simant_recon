"""Parent packaging: immutable worker bytes and separate bounded decisions."""
import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
BASE = ROOT / 'work/source-only-dos/structural-audits-v36'

def pin(path):
    raw = path.read_bytes()
    return dict(path=str(path.relative_to(ROOT)).replace('\\', '/'), size=len(raw),
                sha256=hashlib.sha256(raw).hexdigest())

def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')

def walk(value):
    if isinstance(value, dict):
        if 'path' in value and 'sha256' in value:
            yield value
        for child in value.values(): yield from walk(child)
    elif isinstance(value, list):
        for child in value: yield from walk(child)

selection = {
 'tail': ('dos_tail_clear_v36', ['review.md','functional-tail-candidate.json','pre-clear-prefix-review.json',
   'stock-crt-controls.json','full-dos-execution.json','inspect_startup.py','probe_stock_crt.py','run_fixture_dos.py',
   'original-manager-selected-analysis.txt','original-cinit-analysis.txt','runtime-startup-rows.json',
   'cinit-object-analysis.json','bss_two.c','bss_shift.c','file_seed.c']),
 'window': ('dos_window_owner_v36', ['worker-contract.json','runtime-normalized.json','runtime-facts.json',
   'review-facts.json','full-omf-projections.json','functional-view-proposal.json','source-census.json',
   'loadall-extraction.json','tool-pins.json','resource-followup.json','window-functional-provider45.c',
   'runtime_probe.py','review_probe.py','source_review.py','normalize_runtime.py','package_proposal.py']),
 'selector': ('dos_critical_selector_v36', ['proposal-v36.md','proposal-v36.json','fixture-receipt-v36.json',
   'receipt-v36.json','whole-tu-v36.json','selector-view.c','selector-consumer.c','selector-shift-consumer.c',
   'selector-width-consumer.c','selector-width-contrast.c','selector-initialized-contrast.c',
   'selector-unsigned-diagnostic.c','context-storage.c','audit_v36.py','fixture_v36.py','make_review_packet.py']),
 'ctype': ('dos_ctype_sequence_v36', ['review.md','audit.json','packet-index.json','probe.py']),
 'database': ('dos_database_exit_v36', ['REPORT.md','receipt.json','review_exit_v36.py']),
 'clip': ('dos_clip_owner_v36', ['ownership-report.md','ownership-review.json','extent-controls.json']),
}
assert not BASE.exists(), 'single-shot archive already exists'
BASE.mkdir(parents=True)
preserved = []
redirects = {}
for kind, (directory, files) in selection.items():
    for name in files:
        source = ROOT / 'build/workers' / directory / name
        target = BASE / kind / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        original = pin(source); archived = pin(target)
        assert original['sha256'] == archived['sha256'] and original['size'] == archived['size']
        preserved.append(dict(original=original, archived=archived))
        redirects[str(source.resolve()).casefold()] = archived
for name in ('source_only_dos.py','dos_source_bindings.py'):
    source = ROOT / 'tools' / name
    target = BASE / 'context' / name
    target.parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(source, target)
    original=pin(source); archived=pin(target)
    preserved.append(dict(original=original,archived=archived))
    redirects[str(source.resolve()).casefold()] = archived
for name in ('review_packets.py','raw-review.json','package_v36.py'):
    source=HERE/name;target=BASE/'root'/name;target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(source,target)
    preserved.append(dict(original=pin(source),archived=pin(target)))
write(BASE/'preservation-index.json', dict(schema='simant-dos-immutable-evidence-preservation-v36',
    repinned_worker_receipts=False, files=preserved))

def evidence_pins(files):
    rows={}
    for file in files:
        rows[str(file.resolve()).casefold()]=pin(file)
        for row in walk(json.loads(file.read_bytes())):
            p=Path(row['path']);p=p if p.is_absolute() else ROOT/p
            # Research asset identities stay in the immutable research packets;
            # source build only reopens source-created fixtures/tools/evidence.
            if ROOT/'assets' in p.parents or p.name.lower() in ('simant.exe','simanth.exe','simant.hybrid.exe'):
                continue
            key=str(p.resolve()).casefold()
            if key in redirects: row=redirects[key]
            else:
                raw=p.read_bytes();assert hashlib.sha256(raw).hexdigest()==row['sha256'],p
                row=dict(row,size=len(raw))
            rows[key]=row
    return list(rows.values())

root_decision=dict(schema='simant-dos-parent-minimum-views-admission-v36',root_reviewed=True,
    review=pin(BASE/'root/raw-review.json'),
    accepted_minimum_views=[dict(module='source-owned:window-initialized-views',
        owners=['_win_drawHooks','_win_offsets'],bytes=[180,360],
        proof='Unconditional 45-entry reset effects, full-TU unchanged live contributions, far common initial-zero/ABI controls on both linkers.',
        gate='window-index-resource-cross-owner-layout'),
      dict(module='source-owned:critical-selector-byte',owners=['_g_8CCB'],bytes=[1],
        proof='Original and current exact signed-byte consumer; mutable near communal, genuine CRT startup and shifted-group controls.',
        gate='critical-selector-computed-alias-layout')],
    historical_defining_TU_or_maximum_extent_claimed=False,computed_aliases_closed=False,
    game_linked=False,game_executed=False,original_build_bytes=0,
    kept_open=['ctype_heap_state_and_relocated_prefix','clip_destination_capacity','returning_Punt_database_paths'])
write(BASE/'root/minimum-views-admission.json',root_decision)
sources={
 'window':('source-owned:window-initialized-views','WINVIEW36','window-initialized-views-v36.c',
     (BASE/'window/window-functional-provider45.c').read_text()),
 'selector':('source-owned:critical-selector-byte','CRITBY36','critical-selector-byte-v36.c',
     '/* Mutable minimum signed-byte view; computed alias gate remains open. */\nchar near g_8CCB;\n')}
shapes={
 'window':[dict(name='_win_drawHooks',kind='far',length=180,count=45,element_size=4),
           dict(name='_win_offsets',kind='far',length=360,count=45,element_size=8)],
 'selector':[dict(name='_g_8CCB',kind='near',length=1)]}
for kind,(module,basename,filename,text) in sources.items():
    source=ROOT/'work/source-only-dos/providers'/filename
    assert not source.exists();source.write_text(text,encoding='ascii')
    receipts = {'window': ['runtime-normalized.json','loadall-extraction.json','functional-view-proposal.json','tool-pins.json'],
                'selector':['fixture-receipt-v36.json','whole-tu-v36.json','proposal-v36.json']}[kind]
    files=[BASE/kind/name for name in receipts]
    control_pins=evidence_pins(files)
    external=[row for row in control_pins if not Path(row['path']).is_relative_to(ROOT)
              and Path(row['path']).is_absolute()]
    contract=dict(schema='simant-dos-minimum-source-view-contract-v36',module=module,
        root_reviewed=True,admitted=True,all_required_checks_pass=True,communals=shapes[kind],
        historical_producer_or_placement_claimed=False,maximal_extent_claimed=False,
        computed_aliases_closed=False,game_lifecycle_claimed=False,original_game_bytes_used=0,
        required_unresolved_gate=root_decision['accepted_minimum_views'][0 if kind=='window' else 1]['gate'],
        probe_source=pin(BASE/kind/('runtime_probe.py' if kind=='window' else 'fixture_v36.py')),
        root_admission=pin(BASE/'root/minimum-views-admission.json'),
        receipts={Path(f).name:pin(f) for f in files},inputs=external,control_pins=control_pins)
    contract_path=ROOT/f'work/source-only-dos/{kind}-minimum-view-contract-v36.json'
    write(contract_path,contract)
    binding=dict(schema='simant-dos-reviewed-minimum-view-bindings-v36',category='REVIEWED_SOURCE_STORAGE_BINDING',
        root_reviewed=True,bindings=[],providers=[dict(module=module,basename=basename,owner=None,profile='msc600ax',
        flags=['/AL','/Os','/Gs'],source=pin(source),communals=shapes[kind])],
        review_sources=[pin(BASE/'root/minimum-views-admission.json'),pin(source)],
        runtime_contract=pin(contract_path),runtime_contract_key=kind+'_minimum_view_contract')
    write(ROOT/f'work/source-only-dos/{kind}-minimum-view-bindings-v36.json',binding)
print('Immutable evidence archived; two separately scoped minimum-view providers packaged.')
