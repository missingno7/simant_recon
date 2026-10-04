"""Append finalized reviews without altering worker receipts or old archives."""
import hashlib
import json
import shutil
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
BASE=ROOT/'work/source-only-dos/structural-audits-v36'
sys.path.insert(0,str(ROOT/'tools'))
import compiler

def pin(p):
    b=p.read_bytes()
    return dict(path=str(p.relative_to(ROOT)).replace('\\','/') if p.is_relative_to(ROOT) else str(p),
                size=len(b),sha256=hashlib.sha256(b).hexdigest())
def write(p,d):p.write_text(json.dumps(d,indent=2)+'\n',encoding='utf-8')
def walk(d):
    if isinstance(d,dict):
        if 'path' in d and 'sha256' in d:yield d
        for v in d.values():yield from walk(v)
    elif isinstance(d,list):
        for v in d:yield from walk(v)
index=json.loads((BASE/'preservation-index.json').read_bytes())
for directory,kind,names in [
 ('dos_window_owner_v36','window',['review-v36.md','candidate-index.json']),
 ('dos_receipt_inventory_v36','inventory',['inventory.py','inventory.json','inventory-report.md','context-receipt.json']),
 ('dos_tail_admission_review_v36','tail-independent',['review.json','review.md','reopened.json','full-dos-replay.json','audit_reopen.py','audit_full_dos.py'])]:
    for name in names:
        source=ROOT/'build/workers'/directory/name;target=BASE/kind/name
        assert not target.exists(),target
        target.parent.mkdir(exist_ok=True);shutil.copyfile(source,target)
        index['files'].append(dict(original=pin(source),archived=pin(target)))
write(BASE/'preservation-index.json',index)
redirects={str((ROOT/r['original']['path']).resolve()).casefold():r['archived'] for r in index['files']}
receipts={name:pin(BASE/'tail'/name) for name in ['functional-tail-candidate.json',
 'pre-clear-prefix-review.json','stock-crt-controls.json','full-dos-execution.json']}
receipts['independent-review.json']=pin(BASE/'tail-independent/review.json')
rows={}
for r in list(receipts.values()):
    p=ROOT/r['path'];rows[str(p.resolve()).casefold()]=r
    for item in walk(json.loads(p.read_bytes())):
        q=Path(item['path']);q=q if q.is_absolute() else ROOT/q
        if ROOT/'assets' in q.parents or q.name.lower() in ('simant.exe','simanth.exe','simant.hybrid.exe'):continue
        key=str(q.resolve()).casefold()
        if key in redirects:item=redirects[key]
        else:
            b=q.read_bytes();assert hashlib.sha256(b).hexdigest()==item['sha256'],q
            item=dict(item,size=len(b))
        rows[key]=item
tc=compiler.toolchain()
for tool in [tc['profiles']['msc600ax']] if 'profiles' in tc else []:
    for name,digest in tool['files'].items():
        p=Path(tool['directory'])/name;r=pin(p);assert r['sha256']==digest;rows[str(p.resolve()).casefold()]=r
for tool in [tc['linkers'][p] for p in ('rtlink400','rtlink610')]:
    for name,digest in tool['files'].items():
        p=Path(tool['directory'])/name;r=pin(p);assert r['sha256']==digest;rows[str(p.resolve()).casefold()]=r
runner=tc['runners']['dosbox-x'];r=pin(Path(runner['path']));assert r['sha256']==runner['sha256'];rows[r['path'].casefold()]=r
contract=dict(schema='simant-dos-bounded-startup-erasure-v36',root_reviewed=True,admitted=True,
    scope='ordinary_tracked_loader_crt_dos_api',disposition=dict(id='common_tail_overlap_3',offset=1,size=2),
    residual=[dict(offset=0,size=1)],historical_ledger_bytes=113,historical_data_debt_modified=False,
    new_owner_or_field_claim=False,added_storage_bytes=0,original_build_bytes=0,
    member_sha256='2e9a254b9bd00ea59884089e78e951f0e40343e11d24976f32d9582f4ded259d',
    actual_game_entry_review_required=True,game_link_or_execution_claimed=False,
    receipts=receipts,control_pins=list(rows.values()),
    inputs=[r for r in rows.values() if Path(r['path']).is_absolute() and not Path(r['path']).is_relative_to(ROOT)],
    decision='Only recovery of the two prior file values is discharged; actual game startup/clear dominance must be reverified at independent link boundary.')
write(ROOT/'work/source-only-dos/startup-tail-erasure-contract-v36.json',contract)
print('Final worker reports and independent counter-review preserved; bounded tail decision packaged.')
