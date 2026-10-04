"""Preserve bounded ownership research; admit no provider or semantic change."""
import hashlib
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT / 'work/source-only-dos/structural-audits-v37'
assert not BASE.exists()
BASE.mkdir()

def pin(path):
    raw=path.read_bytes()
    return dict(path=str(path.relative_to(ROOT)).replace('\\', '/'), size=len(raw),
                sha256=hashlib.sha256(raw).hexdigest())

allowed={'.c','.py','.json','.md','.txt','.log','.map','.lnk','.bat','.conf','.cfg'}
copies=[]
for directory, kind in [('dos_icon_minimum_v37','icon'),('dos_icon_counterreview_v37','icon-independent'),
                        ('dos_window_handles_minimum_v37','handles'),('dos_bitmap_storage_owner_v37','bitmap')]:
    source=ROOT/'build/workers'/directory
    assert source.exists(),source
    for path in sorted(source.rglob('*')):
        if not path.is_file() or path.suffix.lower() not in allowed or '__pycache__' in path.parts:
            continue
        target=BASE/kind/path.relative_to(source)
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(path,target)
        old,new=pin(path),pin(target)
        assert old['size']==new['size'] and old['sha256']==new['sha256']
        copies.append(dict(original=old,archived=new))
target=BASE/'preserve_research_v37.py'
shutil.copyfile(Path(__file__),target)
context=dict(schema='simant-bounded-source-ownership-research-v37', root_reviewed=True,
    provider_admitted=False, canonical_or_production_changed=False,
    current_preflight=pin(ROOT/'build/source-only-dos-v36/build-report.json'),
    compiled_TUs=190, unresolved_imports=12, functional_data_bytes=44, historical_data_bytes=113,
    aliases=193, open_layout_gates=10, original_game_bytes_in_build=0,
    icon='Minimum mutable four-byte Handle-shaped access view independently supported; no production admission. Producer, valid cell/payload lifetime, maximal extent, activation and menu/computed aliases remain unresolved.',
    handles='No table reset or extent41 owner. Only lock-cache/depth arrays reset45; guard0..40 is not table capacity.',
    bitmap='Header-plus-pixels declaration and full payload extent absent. Mode1/6 and unassigned spider divisor remain source integration facts; conditional6276/3532/1572 spans and6316 adjacency are not capacity.',
    integrity_limit='Icon worker pins an earlier live v36 report;733 stable pins/1 report drift. Original report bytes unavailable. Independent current190 source/object join passes. Old worker receipt remains unchanged.',
    worker_gate_spelling_note='Handle worker shorthand critical-selector denotes the existing critical-selector-computed-alias-layout integration obligation; it adds no differently named production gate.',
    game_linked=False, game_executed=False, human_acceptance='PENDING')
(BASE/'context.json').write_text(json.dumps(context,indent=2)+'\n',encoding='utf-8')
files=[pin(path) for path in sorted(BASE.rglob('*')) if path.is_file()]
(BASE/'preservation-index.json').write_text(json.dumps(dict(schema='simant-immutable-ownership-research-v37',
    frozen_worker_receipts_rewritten=False,copies=copies,archive_only=[pin(BASE/'context.json'),pin(target)]),indent=2)+'\n',encoding='utf-8')
print('Preserved research-only text artifacts:',len(copies))
