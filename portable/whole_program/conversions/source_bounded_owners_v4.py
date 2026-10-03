#!/usr/bin/env python3
"""Derive a small additive owner proposal from source views and SaveRec rows.

V4 is a diagnostic successor to V3. It addresses named source/serialization
clusters omitted by V3's narrower selectors. It makes no historical communal
extent claim and does not select production state.
"""
from __future__ import annotations
import argparse, hashlib, json, re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
V2=ROOT/'portable/research/whole_program_unprovided_owners_v2.json'
V3=ROOT/'portable/research/whole_program_source_bounded_owners_v3.json'
MAN=ROOT/'layout/manifest.json'; SYM=ROOT/'layout/symbols.json'
SAVE=ROOT/'src/S09/m35F5.c'; TERRAIN=ROOT/'src/root/m0AD9.c'; CYCLE_VIEW=ROOT/'src/S25/m3BA4.c'
OUT=ROOT/'portable/research/whole_program_source_bounded_owners_v4.json'
TARGETS={
 'Cycle':('50F6:0F08','word-union',2),
 'ListIndexB':('50F6:0DA8','word-union',2),
 'ListIndexR':('50F6:0EAA','word-union',2),
 'LionListM':('50F6:0ABA','byte-array',10),
 'LionListS':('50F6:0ACC','byte-array',10),
 'LionListT':('50F6:0ADE','byte-array',10),
 'LionListX':('50F6:0A92','byte-array',10),
 'LionListY':('50F6:0AA8','byte-array',10),
 'SowX':('50F6:0EAE','word-array-union',3),
 'SowY':('50F6:0F00','word-array-union',3),
 'SowDir':('50F6:0F1A','word-array-union',3),
 'SowSave':('50F6:0F28','word-array-union',3),
 'PillarMap':('50F6:0D9C','word-array-union',6),
}
def sha(b): return hashlib.sha256(b).hexdigest()
def parse_save(text):
 rx=re.compile(r'\{\s*(\d+)\s*,\s*(\d+)\s*,\s*\(void\s+far\s*\*\)\s*&([A-Za-z_]\w*)\s*\}')
 out={}
 for size,count,name in rx.findall(text): out.setdefault(name,[]).append({'size':int(size),'count':int(count),'bytes':int(size)*int(count)})
 return out
def valid_save(name, kind, count, rows):
 expected=(1,10) if kind=='byte-array' else (2,1) if kind=='word-union' else (2,count)
 return len(rows)==1 and (rows[0]['size'],rows[0]['count'])==expected
def valid_address(name, got): return TARGETS[name][0]==got
def overlap(start, extent, other_start, other_extent):
 a,off=(int(x,16) for x in start.split(':')); b,boff=(int(x,16) for x in other_start.split(':'))
 return a==b and off<boff+other_extent and boff<off+extent
def main():
 ap=argparse.ArgumentParser(); mode=ap.add_mutually_exclusive_group(required=True); mode.add_argument('--write',action='store_true'); mode.add_argument('--verify',action='store_true'); args=ap.parse_args()
 v2raw=V2.read_bytes();v2=json.loads(v2raw);v3raw=V3.read_bytes();v3=json.loads(v3raw)
 manraw=MAN.read_bytes();man=json.loads(manraw);symraw=SYM.read_bytes();sym=json.loads(symraw)
 saveraw=SAVE.read_bytes();save=parse_save(saveraw.decode('latin1'))
 groups={n:[] for n in TARGETS}
 for g in v2['groups']:
  for name in TARGETS:
   if name in g.get('registered_address_members',[]) or name in g.get('unprovided_members',[]): groups[name].append(g)
 existing={o['address'] for o in v3['owners']}
 owners=[]; source_pins={}
 for name,(address,kind,count) in TARGETS.items():
  gs=groups[name]
  if len(gs)!=1: raise ValueError(f'{name}: expected one address group, found {len(gs)}')
  g=gs[0]
  if not valid_address(name,g['address']): raise ValueError(f'{name}: address {g["address"]} != {address}')
  if g['provided_members_at_address']: raise ValueError(f'{name}: already has a provider')
  views=g['assessment']['view_rows']
  if not views: raise ValueError(f'{name}: missing source views')
  scalar=[]; words=[]; bytes_views=[]
  for row in views:
   view=row['view']; typ=row['type']; base=typ['base']; dims=view.get('dims',[])
   if (view.get('layout_address') != [int(address.split(':')[0],16),int(address.split(':')[1],16)]): raise ValueError(f'{name}: bad view address {view}')
   path=view['module']; module=next((m for m in man['modules'].values() if m.get('source')==path),None)
   if not module: raise ValueError(f'{name}: unmanifested source {path}')
   raw=(ROOT/path).read_bytes(); digest=sha(raw)
   if digest!=module['source_sha256']: raise ValueError(f'{name}: source hash mismatch {path}')
   source_pins[path]={'sha256':digest,'manifest_source_sha256':module['source_sha256']}
   symbol=sym['data'].get(view['name'])
   if symbol is None or (symbol['seg'],symbol['off'])!=tuple(view['layout_address']): raise ValueError(f'{name}: layout symbol address mismatch {view["name"]}')
   if base in ('int','unsigned','unsigned int') and typ['bytes']==2 and (not dims or dims==[str(count)]):
    (scalar if not dims else words).append(row)
   elif base in ('char','unsigned char') and typ['bytes']==1 and dims in ([],[''],[str(count)]):
    bytes_views.append(row)
   else: raise ValueError(f'{name}: unsupported/conflicting source view {row}')
  entries=save.get(name,[])
  if len(entries)!=1: raise ValueError(f'{name}: expected unique SaveRec row, got {entries}')
  rec=entries[0]
  expected=(1,10) if kind=='byte-array' else (2,1) if kind=='word-union' else (2,count)
  if not valid_save(name,kind,count,entries): raise ValueError(f'{name}: SaveRec {rec} != {expected}')
  if kind=='byte-array':
   if not bytes_views or words or scalar: raise ValueError(f'{name}: byte-array source shape mismatch')
   mappings=[]
   for r in views:
    v=r['view']; mappings.append({'source':v['module'],'name':v['name'],'expression':f'native_state_{name}.values','view':'byte-array'})
   owner={'name':name,'address':address,'kind':kind,'native_declaration':f'uint8_t values[{count}]','width_bytes':count,'save_rec':rec,'source_mappings':mappings,'basis':'source index is bounded by LionIndex < 10; S09 SaveRec is 1x10; declarations are byte-array views'}
  elif kind=='word-union':
   if not scalar or words or (name=='Cycle' and not bytes_views) or (name!='Cycle' and bytes_views): raise ValueError(f'{name}: scalar/raw views incomplete')
   mappings=[]
   for r in views:
    v=r['view']; byte=(r['type']['bytes']==1)
    expr=f'native_state_{name}.raw_bytes[0]' if byte and not v.get('dims') else f'native_state_{name}.raw_bytes'
    if not byte: expr=f'native_state_{name}.signed_value'
    mappings.append({'source':v['module'],'name':v['name'],'expression':expr,'view':'raw-byte' if byte else 'word-scalar'})
   owner={'name':name,'address':address,'kind':kind,'native_declaration':'union { int16_t signed_value; uint8_t raw_bytes[2]; }','width_bytes':2,'save_rec':rec,'source_mappings':mappings,'serialized_byte_view':'Cycle has an explicit S09 raw array plus S25 byte scalar; ListIndexB/R serialization uses the same storage address through the S09 SaveRec pointer.','basis':'complete 16-bit scalar declaration and exact S09 SaveRec 2x1; any same-address byte aliases are explicit raw views'}
  else:
   if not words or scalar or not bytes_views: raise ValueError(f'{name}: word-array/raw views incomplete')
   mappings=[]
   for r in views:
    v=r['view']; byte=(r['type']['bytes']==1)
    mappings.append({'source':v['module'],'name':v['name'],'expression':f'native_state_{name}.raw_bytes' if byte else f'native_state_{name}.signed_values','view':'serialized-bytes' if byte else 'word-array'})
   owner={'name':name,'address':address,'kind':kind,'native_declaration':f'union {{ int16_t signed_values[{count}]; uint8_t raw_bytes[{count*2}]; }}','count':count,'width_bytes':count*2,'save_rec':rec,'source_mappings':mappings,'basis':f'complete int[{count}] source array and exact S09 SaveRec 2x{count}; S09 byte view is serialized overlay'}
  owner['source_group_modules']=sorted({r['view']['module'] for r in views})
  owners.append(owner)
 addresses={o['address'] for o in owners}
 if len(addresses)!=len(owners): raise ValueError('duplicate owner starts')
 if addresses & existing: raise ValueError('overlap with V3 owner start')
 # Source-confirmed extents must not overlap one another or an existing V3 span.
 intervals=[]
 for o in owners:
  seg,off=(int(x,16) for x in o['address'].split(':')); end=off+o['width_bytes']
  if end>0x10000: raise ValueError('owner crosses segment')
  if any(seg==s and off<e and a<end for s,a,e in intervals): raise ValueError(f'overlap at {o["address"]}')
  intervals.append((seg,off,end))
 v3_overlaps=[(o['name'],p['owner']) for o in owners for p in v3['owners'] if overlap(o['address'],o['width_bytes'],p['address'],p['width_bytes'])]
 if v3_overlaps: raise ValueError(f'overlap with V3 owner intervals: {v3_overlaps}')
 controls={
  'positive':{'all_13_named_groups_resolve_once':len(owners)==13,'save_rows_match_source_shapes':True,'same_address_aliases_agree':True,'no_v3_interval_overlap':not v3_overlaps,'all_extents_nonoverlapping':True},
  'negative':{'duplicate_save_record_rejected':not valid_save('LionListM','byte-array',10,save['LionListM']*2),'save_extent_mutation_rejected':not valid_save('SowX','word-array-union',3,[{'size':2,'count':4,'bytes':8}]),'known_source_address_conflict_rejected':not valid_address('Cycle','FFFF:FFFF'),'interior_interval_collision_detected':overlap('50F6:0A92',10,'50F6:0A98',2)},
 }
 # Explicitly record the one endian-sensitive byte alias: Cycle's S25 byte view
 # aliases byte zero of the DOS little-endian word, so this proposal assumes a
 # little-endian native host (or requires an explicit accessor before BE use).
 report={'schema':'simant-native-source-bounded-owners-v4','claim':'DIAGNOSTIC_ONLY: additive native owners from exact source declarations and S09 SaveRec extents; historical FAR_BSS communal gaps are not used as object bounds; no production selection.','inputs':{'v2_owner_report':{'path':V2.relative_to(ROOT).as_posix(),'sha256':sha(v2raw)},'v3_plan':{'path':V3.relative_to(ROOT).as_posix(),'sha256':sha(v3raw)},'manifest':{'path':MAN.relative_to(ROOT).as_posix(),'sha256':sha(manraw)},'symbols':{'path':SYM.relative_to(ROOT).as_posix(),'sha256':sha(symraw)},'save_source':{'path':SAVE.relative_to(ROOT).as_posix(),'sha256':sha(saveraw)},'producer':{'path':Path(__file__).relative_to(ROOT).as_posix(),'sha256':sha(Path(__file__).read_bytes())},'source_files':source_pins},'owners':owners,'controls':controls,'limitations':['No historical communal/gap extent claim.','Cycle byte-zero alias and native word overlap are little-endian-host specific; big-endian use needs an explicit DOS-little-endian accessor.','Proposal is diagnostic and not integrated into the production adapter.','SaveRec serialization endianness remains the separately documented host-codec boundary.'],'summary':{'owners':len(owners),'native_bytes':sum(o['width_bytes'] for o in owners),'by_kind':{k:sum(o['kind']==k for o in owners) for k in sorted({o['kind'] for o in owners})}}}
 if not all(controls['positive'].values()) or not all(controls['negative'].values()): raise ValueError(f'control failed: {controls}')
 rendered=json.dumps(report,indent=2)+'\n'
 if args.write:
  if OUT.exists(): raise SystemExit(f'refusing to overwrite immutable report: {OUT.relative_to(ROOT)}')
  OUT.write_text(rendered,encoding='utf-8')
 elif not OUT.exists() or OUT.read_text(encoding='utf-8')!=rendered:
  raise SystemExit('V4 proposal does not reproduce the pinned report')
 print(OUT.relative_to(ROOT),sha(OUT.read_bytes()))
 print(json.dumps(report['summary'],indent=2))
if __name__=='__main__': main()
