#!/usr/bin/env python3
"""Emit a source-bounded, diagnostic owner proposal for selected 50F6 state."""
from __future__ import annotations
import hashlib, json, re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'portable/research/whole_program_simulation_state_50f6_v6.json'
POINTS=['0508','0596','06A6','072E','07BC','07CA','0852','08DE','08EC','09F2','0A02','0A8A','0AA2','0AB2']
HISTORY=['0516','05A0','0626','06AE','073C','07CE','0856','08F0','0970','0A0A']
SAVED_POINTS={'0508','0596','06A6','072E','07BC','07CA'}
def sha(b:bytes)->str:return hashlib.sha256(b).hexdigest()
def pin(path:Path)->dict[str,str]:return {'path':path.relative_to(ROOT).as_posix(),'sha256':sha(path.read_bytes())}
def span_overlap(a:str,aw:int,b:str,bw:int)->bool:
    sa,oa=(int(x,16) for x in a.split(':')); sb,ob=(int(x,16) for x in b.split(':'))
    return sa==sb and oa<ob+bw and ob<oa+aw
def main()->None:
    if OUT.exists(): raise SystemExit(f'refusing to overwrite immutable report {OUT}')
    sym=json.loads((ROOT/'layout/symbols.json').read_text(encoding='utf-8'))['data']
    save=(ROOT/'src/S09/m35F5.c').read_text(encoding='latin1')
    rx=re.compile(r'\{\s*(\d+)\s*,\s*(\d+)\s*,\s*\(void\s+far\s*\*\)\s*&([A-Za-z_]\w*)\s*\}')
    rows={n:[] for n in [f'fd_50F6_{x}' for x in SAVED_POINTS|set(HISTORY)]}
    for size,count,name in rx.findall(save):
        if name in rows: rows[name].append({'element_bytes':int(size),'count':int(count),'serialized_bytes':int(size)*int(count)})
    targets=[]; source_pins={}
    for off in POINTS:
        name=f'fd_50F6_{off}'; s=sym[name]; addr=f"{s['seg']:04X}:{s['off']:04X}"
        extent=4; save_rows=rows.get(name,[])
        if off in SAVED_POINTS and save_rows!=[{'element_bytes':4,'count':1,'serialized_bytes':4}]: raise ValueError(f'{name} SaveRec mismatch: {save_rows}')
        if off not in SAVED_POINTS and save_rows: raise ValueError(f'unexpected SaveRec row for {name}: {save_rows}')
        declarations=[]
        for p in sorted((ROOT/'src').rglob('*.c')):
            text=p.read_text(encoding='latin1')
            for no,line in enumerate(text.splitlines(),1):
                if name in line and re.search(r'\bextern\b',line) and re.search(r'(?:Point|Pnt|int|unsigned|struct\s+\w+)',line):
                    declarations.append({'source':p.relative_to(ROOT).as_posix(),'line':no,'text':line.strip()})
                    source_pins[p.relative_to(ROOT).as_posix()]=sha(p.read_bytes())
        if not declarations: raise ValueError(f'missing source declarations for {name}')
        target={'symbol':name,'address':addr,'extent_bytes':extent,'kind':'point-two-word-overlay','saved':off in SAVED_POINTS,'save_rec_rows':save_rows,'declarations':declarations,
                'proposed_native_type':'union { struct { int16_t x, y; } xy; struct { int16_t v, h; } vh; int16_t words[2]; uint8_t raw_bytes[4]; }',
                'alias_rule':'Per-source field order/view only: x/y and v/h spellings share two storage words; neither label is globally privileged.'}
        targets.append(target)
    for off in HISTORY:
        name=f'fd_50F6_{off}'; s=sym[name]; addr=f"{s['seg']:04X}:{s['off']:04X}"
        save_rows=rows[name]
        if save_rows!=[{'element_bytes':2,'count':64,'serialized_bytes':128}]: raise ValueError(f'{name} SaveRec mismatch: {save_rows}')
        declarations=[]
        for p in sorted((ROOT/'src').rglob('*.c')):
            text=p.read_text(encoding='latin1')
            for no,line in enumerate(text.splitlines(),1):
                if name in line and re.search(r'\bextern\b',line) and re.search(r'int\s+(?:far\s+)?'+re.escape(name),line):
                    declarations.append({'source':p.relative_to(ROOT).as_posix(),'line':no,'text':line.strip()})
                    source_pins[p.relative_to(ROOT).as_posix()]=sha(p.read_bytes())
        if not declarations: raise ValueError(f'missing history declarations for {name}')
        targets.append({'symbol':name,'address':addr,'extent_bytes':128,'kind':'history-64-signed-words','saved':True,'save_rec_rows':save_rows,'declarations':declarations,
            'proposed_native_type':'union { int16_t signed_values[64]; uint8_t raw_bytes[128]; }','alias_rule':'Typed word indexing is the source view; raw bytes are an explicit S09 serialization overlay. Byte compatibility assumes the native little-endian target.'})
    # Complete declarations and SaveRec rows, not neighboring symbols, ground these sizes.
    intervals=[]
    for t in targets:
        a=t['address']; n=t['extent_bytes']
        if any(span_overlap(a,n,b,m) for b,m in intervals): raise ValueError(f'candidate overlap at {a}')
        intervals.append((a,n))
    pins={}
    for rel in ['layout/manifest.json','layout/symbols.json','src/S09/m35F5.c','src/root/m0250.c','src/root/m0894.c','src/root/m004A.c','src/root/m015B.c',
                'portable/research/whole_program_unprovided_owners_v2.json','portable/research/whole_program_source_bounded_owners_v3.json','portable/research/whole_program_source_bounded_owners_v5.json',
                'build/workers/whole_program/generated/migration.json','build/workers/whole_program/generated/native_owners.h','build/workers/whole_program/generated/native_owners.c',
                'build/workers/whole_program/generated/root_m004A.c','build/workers/whole_program/generated/S14_m384C.c']:
        p=ROOT/rel
        if p.exists():pins[rel]=pin(p)
    # Compare only against the existing candidate ranges; retain reports unchanged.
    ranges=[]
    for rel,field,widthfield in [('portable/research/whole_program_source_bounded_owners_v3.json','owners','width_bytes'),('portable/research/whole_program_source_bounded_owners_v5.json','owners','width_bytes')]:
        d=json.loads((ROOT/rel).read_text(encoding='utf-8'))
        for o in d[field]:
            if o.get('address') and o.get(widthfield): ranges.append((o['address'],int(o[widthfield]),rel+':'+o.get('name','?')))
    v2=json.loads((ROOT/'portable/research/whole_program_unprovided_owners_v2.json').read_text(encoding='utf-8'))
    for o in v2.get('bss_owner_candidates',[]):
        width=o.get('owner_extent_bytes',o.get('extent_bytes',o.get('width_bytes')))
        if width and o.get('address'): ranges.append((o['address'],int(width),'V2:'+str(o.get('owner',o.get('unprovided_members',['?'])[0]))))
    collisions=[{'candidate':t['symbol'],'other':other} for t in targets for a,n,other in ranges if span_overlap(t['address'],t['extent_bytes'],a,n)]
    report={'schema':'simant-whole-program-simulation-state-plan-v6','claim':'DIAGNOSTIC_ONLY: source-bounded typed ownership proposal; no historical communal-gap size inference, no provider selection, no production integration.',
      'scope':{'point_objects':len(POINTS),'history_arrays':len(HISTORY),'data_audio_ui_excluded':True,'root171c_excluded_by_parent_scope':True},
      'extent_basis':'Fourteen complete two-word Point/Pnt/int[2] declarations (4 bytes each); ten complete int[64] declarations plus exact S09 SaveRec {2,64} rows (128 bytes each); six points additionally have exact SaveRec {4,1} rows. No extent is inferred from a neighboring address or communal gap.',
      'targets':targets,'source_hashes':dict(sorted(source_pins.items())),'input_hashes':pins,
      'collision_check':{'against_v3_v5_and_v2_candidate_ranges':True,'overlap_count':len(collisions),'collisions':collisions},
      'proposed_ownership':{'canonical_owner':'one native shared-state translation unit defining one owner object for each candidate symbol','source_adapters':'pre-word C identifier rewrite plus removal of only target extern declaration lines; x/y, v/h, word-array and raw serialized views are per-source aliases','serialized_overlays':'points retain four raw bytes; histories retain 128 raw bytes; direct byte-overlay equivalence is restricted to little-endian native ABI; other endian targets require explicit codec'},
      'nonclaims':['No 50F6 original MSC COMDEF extent artifact is available or used in this proposal.','No pixel/rendering equivalence is asserted.','The plan does not alter V2, V3, V5, historical source, providers, generated output, or the mechanical generator.']}
    if collisions: raise ValueError(f'overlap collisions: {collisions}')
    OUT.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(f'WROTE {OUT.relative_to(ROOT)} targets={len(targets)} points={len(POINTS)} histories={len(HISTORY)} source_pins={len(source_pins)} collisions=0')
if __name__=='__main__':main()
