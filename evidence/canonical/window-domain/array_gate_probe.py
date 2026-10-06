"""Compose admitted window IDs and palette bounds with hook/Rect storage."""
from pathlib import Path
from types import SimpleNamespace
import hashlib, importlib.util, json, struct, sys

ROOT=next(p for p in Path(__file__).resolve().parents if (p/'src/program.json').is_file())
sys.path.insert(0,str(ROOT/'tools'))
import behavior as b, exe, functions
if not __debug__:raise RuntimeError('proof checks require Python without -O')

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,ROOT/path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module

def support():
    module=load('window_array_inventory','evidence/canonical/icon-handle-view/vga_probe.py')
    module.TARGETS={'win_drawHooks','win_offsets','win_numOfWindows','win_numOfColors'}
    return module

PROTECTED={'win_drawHooks':180,'win_offsets':360,'win_numOfWindows':2,'win_numOfColors':2}

def save_ranges(texts,raw=None):
    db=load('window_array_database','evidence/canonical/database-domain/replay.py')
    db.save_table_proof(texts)
    m=db.oracle_machine('OpenDB')
    if raw is None:raw=m.read(b.symbol_address('fd_4E4B_0000'),308*8)
    for i in range(307):
        size,count,off,seg=struct.unpack_from('<HHHH',raw,i*8)
        start=seg*16+off
        for name,length in PROTECTED.items():
            at=b.symbol_address(name)
            if start<at+length and at<start+size*count:
                raise ValueError('save overlaps window arrays/counts: '+name)
    return dict(records=307,descriptor_sha256=hashlib.sha256(raw).hexdigest(),
                protected=PROTECTED,intersections=0)

def hook_store(index):
    oracle=exe.load()
    machine=b.Machine(SimpleNamespace(function=functions.get('win_SetWinDrawHook'),
        vectors={exe.MANAGER_SEG*16+v.offset:v for v in oracle.vectors}))
    base=b.symbol_address('win_drawHooks');writes=[]
    def observe(cpu,access,address,size,value,data):
        if base-4<=address<base+184:writes.append([address-base,size,value])
    machine.cpu.hook_add(b.uc.UC_HOOK_MEM_WRITE,observe)
    machine.run(b.Case('hook-store',args=[0x1234,0x5678],
        registers={'ax':(index<<8)&0xffff},callee_pop=4,return_kind='void'))
    assert machine.read(base+4*index,4)==b.words(0x1234,0x5678)
    assert writes
    return dict(index=index,writes=writes,within_45=0<=index<45)

def collect():
    shared=support();texts,program,registry=shared.inventory()
    guard=load('window_array_ids','evidence/canonical/window-domain/handle_ids_guard.py')
    ids=guard.check()
    assert ids==json.loads((ROOT/'evidence/canonical/window-domain/handle-id-facts.json').read_text())
    palette=load('window_array_palette','evidence/canonical/window-domain/palette_probe.py').collect()
    expected=json.loads((ROOT/'evidence/canonical/window-domain/palette-facts.json').read_text())
    palette.pop('source_inventory_count');expected.pop('source_inventory_count')
    assert palette==expected
    return dict(schema='simant-window-array-domain-v1',
        scope='Specified hook/Rect/palette cross-owner accesses in the existing supported domain; no general object-index, graphics-copy, heap or native-window acceptance.',
        inventory=shared.inventory_pins(texts,program,registry),
        census=shared.census(texts,program,registry),save_ranges=save_ranges(texts),
        original_hook_stores=[hook_store(i) for i in [0,33,45,-1]],
        premises={'handle_ids':ids,'palette_status':palette['status'],
            'window_indices':[0,33],'hook_entries':45,'rect_entries':45,
            'hook_reset_bytes':180,'rect_copy_bytes':320,'rect_owner_bytes':360,
            'palette_bytes':96,'preload_and_purge_count':34})

def check():
    result=collect()
    if result!=json.loads(Path(__file__).with_name('array-gate-facts.json').read_text()):
        raise ValueError('window array composition differs from reviewed facts')
    return result

if __name__=='__main__':
    check();print('PASS: window hook/Rect/palette cross-owner domain')
