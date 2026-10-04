"""Reopen frozen whole-module/runtime evidence and verify the current frame binding."""
from pathlib import Path
import hashlib,json,re,sys
ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).parent
sys.path.insert(0,str(ROOT/'tools'))
import dos_source_bindings as b
from omf import OmfReader

def walk(value):
    if isinstance(value,dict):
        if isinstance(value.get('path'),str) and isinstance(value.get('sha256'),str):yield value
        for item in value.values():yield from walk(item)
    elif isinstance(value,list):
        for item in value:yield from walk(item)
def path_for(value):
    path=Path(value.replace('\\','/'))
    path=path if path.is_absolute() else ROOT/path
    assert not path.is_relative_to(ROOT/'assets'),path
    return path
def check(item):
    raw=path_for(item['path']).read_bytes()
    assert hashlib.sha256(raw).hexdigest()==item['sha256'],item
    assert len(raw)==item['size'],item
    return raw

main=json.loads((HERE/'worker-whole-module.json').read_bytes())
runtime=json.loads((HERE/'worker-runtime-fixture.json').read_bytes())
observations={'build/source-only-dos/build-report.json','build/source-only-dos/sources/U087.asm',
              'build/source-only-dos/objects/U087.OBJ'}
seen=set()
for item in walk([main,runtime]):
    key=(item['path'],item['sha256'])
    if key in seen or item['path'].replace('\\','/') in observations:continue
    check(item);seen.add(key)
baseline=next(v for v in main['whole_module_variants'] if v['form']=='baseline_generated')
old=OmfReader(communals=True).read(check(baseline['object']))
report=json.loads((ROOT/'build/source-only-dos/build-report.json').read_bytes())
row=next(r for r in report['translation_units'] if r['module']=='root:1B73')
new=OmfReader(communals=True).read(check(row['object']))
packet=json.loads((ROOT/'work/source-only-dos/mouse-code-offset-frame-bindings-v1.json').read_bytes())
binding=packet['bindings'][0]
proof=b.verify_objects(old,new,binding)
assert len(proof['reviewed_frame_corrections'])==5
normalize=lambda raw:raw.decode('latin1').replace('\r\n','\n')
assert b.apply_binding(normalize(check(baseline['source'])),binding)==normalize(check(row['generated_source']))
contract=json.loads(check(packet['runtime_contract']))
for case in contract['cases']:
    for kind,identity in case['artifacts'].items():
        raw=check(identity)
        if kind=='run_log':assert raw.decode('latin1')==case['run_log_text']
        if kind=='link_log':assert raw.decode('latin1')==case['link_log_text']
import compiler
for profile in ('rtlink400','rtlink610'):
    b.require_mouse_code_offset_contract(report,profile,compiler.toolchain()['linkers'][profile])
print('PASS:',len(seen),'frozen artifact identities; five current frame-only changes; four complete raw runtime cases')
