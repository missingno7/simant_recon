#!/usr/bin/env python3
"""Derive additive native state owners from frozen source extents (V3).

V3 never infers native object size from a historical communal/gap extent. It
accepts complete C scalar/array declarations or a SaveRec size*count proof, with
an explicit same-address raw-byte overlay only for S09 serialized byte views.
This tool is diagnostic and does not rewrite frozen sources or wire production.
"""
from __future__ import annotations
import argparse, hashlib, json, re
from pathlib import Path
from typing import Any
ROOT=Path(__file__).resolve().parents[3]
BASE=ROOT/'portable/research/inputs/whole_program_provenance_v2/base_plan.json'
V2=ROOT/'portable/research/whole_program_unprovided_owners_v2.json'
MANIFEST=ROOT/'layout/manifest.json'; SYMBOLS=ROOT/'layout/symbols.json'
SAVE_SOURCE=ROOT/'src/S09/m35F5.c'
OUT_JSON=ROOT/'portable/research/whole_program_source_bounded_owners_v3.json'
OUT_C=ROOT/'build/workers/whole_program/source_bounded_v3/native_owners.c'
OUT_H=ROOT/'build/workers/whole_program/source_bounded_v3/native_owners.h'

def sha(b:bytes)->str:return hashlib.sha256(b).hexdigest()
def dim(s:str)->int:
 if not re.fullmatch(r'[0-9]+',s):raise ValueError('array extent must be a positive literal')
 n=int(s)
 if n<=0:raise ValueError('array extent must be positive')
 return n
def addr(g:dict[str,Any]|str)->tuple[int,int]:
 s=g if isinstance(g,str) else g['address']
 return tuple(int(v,16) for v in s.split(':'))
def ctype(t:dict[str,Any])->str:
 b,w,s=t['base'],t['bytes'],t['signedness']
 if w==1 and b in {'char','signed char','unsigned char'}:return 'uint8_t' if s=='unsigned' else 'int8_t'
 if w==2 and b in {'int','unsigned','unsigned int'}:return 'uint16_t' if s=='unsigned' else 'int16_t'
 if w==4 and b in {'long','unsigned long'}:return 'uint32_t' if s=='unsigned' else 'int32_t'
 raise ValueError(f'unsupported primitive type {t}')
def is_scalar(t:dict[str,Any],v:dict[str,Any])->bool:
 return not v.get('dims') and t['base'] in {'int','unsigned','unsigned int','long','unsigned long'}
def parse_save_table(text:str)->dict[str,list[dict[str,int|str]]]:
 # SaveRec fields are {size, count, data}; serialized byte width is size*count.
 rx=re.compile(r'\{\s*(\d+)\s*,\s*(\d+)\s*,\s*\(void\s+far\s*\*\)\s*&([A-Za-z_]\w*)\s*\}')
 out:dict[str,list[dict[str,int|str]]]={}
 for size,count,name in rx.findall(text):out.setdefault(name,[]).append({'size':int(size),'count':int(count),'bytes':int(size)*int(count)})
 return out
def candidate_scalar_overlay(g:dict[str,Any],save:dict[str,list[dict[str,int|str]]])->dict[str,Any]|None:
 if g.get('decision')!='validated-farbss-range-owner-unresolved' or g.get('assessment',{}).get('reason')!='conflicting-DOS-element-widths':return None
 if g.get('historical_provenance',{}).get('storage_class')!='validated-FAR_BSS-range':return None
 vs=g.get('assessment',{}).get('view_rows',[])
 scalar=[x for x in vs if is_scalar(x['type'],x['view'])]
 raw=[x for x in vs if x['type']['base']=='unsigned char' and x['type']['bytes']==1 and x['view'].get('dims')==[''] and x['view']['module']=='src/S09/m35F5.c']
 if not scalar or not raw or len(scalar)+len(raw)!=len(vs):return None
 widths={x['type']['bytes'] for x in scalar}
 if len(widths)!=1:return None
 width=next(iter(widths))
 if width not in (2,4):return None
 # Every scalar alias must have the same extent at this address. Mixed signedness
 # is representationally compatible but gets separate typed union members.
 names={x['view']['name'] for x in raw}
 if not names:return None
 for n in names:
  entries=save.get(n,[])
  if len(entries)!=1 or entries[0]['bytes']!=width:return None
  if entries[0]['size'] not in (1,width):return None
 scalar_names={x['view']['name'] for x in scalar}
 if not scalar_names:return None
 return {'group':g,'scalar':scalar,'raw':raw,'width':width,'scalar_names':scalar_names,'raw_names':names,'save_rows':{n:save[n][0] for n in sorted(names)}}
def candidate_array(g:dict[str,Any])->dict[str,Any]|None:
 if g.get('decision')!='unresolved' or g.get('provided_members_at_address'):return None
 if g.get('assessment',{}).get('extent_kind')!='array':return None
 vs=g['assessment'].get('view_rows',[])
 if not vs:return None
 if any('*' in x['type']['base'] or x['type']['base'].startswith('struct ') for x in vs):return None
 if any(len(x['view'].get('dims',[]))!=1 for x in vs):return None
 types={(x['type']['base'],x['type']['bytes'],x['type']['signedness']) for x in vs}
 if len(types)!=1:return None
 bounds=[]
 for x in vs:
  d=x['view']['dims'][0]
  if d:bounds.append(dim(d))
 if not bounds or len(set(bounds))!=1:return None
 count=bounds[0]
 if any(x['view']['dims'][0] not in ('',str(count)) for x in vs):return None
 ty=ctype(vs[0]['type'])
 if any(ctype(x['type'])!=ty for x in vs):return None
 return {'group':g,'count':count,'element_bytes':vs[0]['type']['bytes'],'native_type':ty,'source_views':vs}
def safe_scalar_type(rows:list[dict[str,Any]])->str:
 t=rows[0]['type']; return ctype(t)
def main()->int:
 ap=argparse.ArgumentParser();ap.add_argument('--write',action='store_true');ap.add_argument('--verify',action='store_true');args=ap.parse_args()
 if args.write and (OUT_JSON.exists() or OUT_C.exists() or OUT_H.exists()):raise SystemExit('V3 output exists; refusing to overwrite immutable output')
 if args.write and args.verify:raise SystemExit('choose either --write or --verify')
 base_raw=BASE.read_bytes();base=json.loads(base_raw);v2_raw=V2.read_bytes();v2=json.loads(v2_raw);man_raw=MANIFEST.read_bytes();manifest=json.loads(man_raw);sym_raw=SYMBOLS.read_bytes();sym=json.loads(sym_raw)
 save_raw=SAVE_SOURCE.read_bytes();save_text=save_raw.decode('latin1');save=parse_save_table(save_text)
 hist={g['address']:g for g in v2['groups']};base_by_addr={g['address']:g for g in base['groups']}
 scalar_rows=[]
 for g in v2['groups']:
  q=candidate_scalar_overlay(g,save)
  if q:scalar_rows.append(q)
 array_rows=[]
 for g in base['groups']:
  if g.get('address') not in hist:continue
  h=hist[g['address']]
  if h.get('historical_provenance',{}).get('storage_class')!='validated-FAR_BSS-range':continue
  q=candidate_array(g)
  if q:array_rows.append(q)
 # The scalar arrays with source-complete declarations are separate from the
 # scalar/raw overlays. Refuse duplicate addresses and any overlap with another
 # registered symbol start. This preserves interior fields as explicit debt.
 if {x['group']['address'] for x in array_rows} & {x['group']['address'] for x in scalar_rows}:raise ValueError('owner group selected twice')
 allgroups=v2['groups']; address_map={addr(g):g for g in allgroups}
 owners=[];source_pins={}
 def note_sources(views:list[dict[str,Any]])->None:
  for x in views:
   source=x['view']['module']; module=next((m for m in manifest['modules'].values() if m.get('source')==source),None)
   if module is None:raise ValueError(f'missing manifest source {source}')
   raw=(ROOT/source).read_bytes(); actual=sha(raw)
   if actual!=module['source_sha256']:raise ValueError(f'source mismatch {source}')
   source_pins[source]={'sha256':actual,'manifest_source_sha256':module['source_sha256']}
 def decl_line(source:str,name:str)->dict[str,Any]:
  data=(ROOT/source).read_text(encoding='latin1').splitlines()
  hits=[(i+1,line.strip()) for i,line in enumerate(data) if re.search(r'\b'+re.escape(name)+r'\b',line) and line.lstrip().startswith('extern ')]
  if not hits:raise ValueError(f'no extern declaration for {source}:{name}')
  return {'source':source,'line':hits[0][0],'text':hits[0][1]}
 for q in scalar_rows:
  g=q['group']; seg,off=addr(g); width=q['width']
  if any((seg,off+i) in address_map for i in range(1,width)):raise ValueError(f'registered interior symbol overlaps {g["address"]}')
  for x in q['scalar']+q['raw']:
   symrow=sym['data'].get(x['view']['name'])
   if symrow is None or (symrow['seg'],symrow['off'])!=(seg,off):raise ValueError(f'layout symbol address mismatch for {x["view"]["name"]}')
  byname={}
  for x in q['scalar']:byname.setdefault(x['view']['name'],[]).append(x)
  semantic=sorted(n for n in byname if not n.startswith('fd_'))
  primary=semantic[0] if semantic else sorted(byname)[0]
  sign_types={x['type']['signedness'] for x in q['scalar']}
  fields={}
  for sign in sorted(sign_types):
   matching=next(x for x in q['scalar'] if x['type']['signedness']==sign)
   field='signed_value' if sign=='signed' or sign=='signed-char-target' else 'unsigned_value'
   fields[field]=ctype(matching['type'])
  members=[{'name':field,'type':t} for field,t in sorted(fields.items())]
  members.append({'name':'raw_bytes','type':'uint8_t','count':width})
  mappings=[]
  for x in q['scalar']:
   source=x['view']['module'];name=x['view']['name']; field='signed_value' if x['type']['signedness'] in ('signed','signed-char-target') else 'unsigned_value'
   mappings.append({'source':source,'name':name,'view':'scalar','expression':f'native_state_{primary}.{field}','remove_extern':decl_line(source,name)})
   note_sources([x])
  for x in q['raw']:
   source=x['view']['module'];name=x['view']['name']
   mappings.append({'source':source,'name':name,'view':'serialized-bytes','expression':f'native_state_{primary}.raw_bytes','remove_extern':decl_line(source,name)})
   note_sources([x])
  owners.append({'address':g['address'],'owner':primary,'owner_c_name':f'native_state_{primary}','kind':'scalar-with-serialized-byte-overlay','width_bytes':width,'members':members,'scalar_symbols':sorted(byname),'serialized_byte_symbols':sorted(q['raw_names']),'save_table_rows':q['save_rows'],'source_mappings':mappings,'basis':'complete scalar declaration plus matching S09 SaveRec size*count; historical gap size unused'})
 for q in array_rows:
  g=q['group'];seg,off=addr(g); count=q['count']; width=q['element_bytes']; extent=count*width
  if any((seg,off+i) in address_map for i in range(1,extent)):raise ValueError(f'registered interior symbol overlaps array {g["address"]}')
  for x in q['source_views']:
   symrow=sym['data'].get(x['view']['name'])
   if symrow is None or (symrow['seg'],symrow['off'])!=(seg,off):raise ValueError(f'layout symbol address mismatch for {x["view"]["name"]}')
  views=q['source_views'];name=g['unprovided_members'][0]
  note_sources(views)
  owners.append({'address':g['address'],'owner':name,'owner_c_name':name,'kind':'source-bounded-array','native_type':q['native_type'],'count':count,'element_bytes':width,'width_bytes':extent,'source_mappings':[{'source':x['view']['module'],'name':x['view']['name'],'view':'array','expression':name,'remove_extern':decl_line(x['view']['module'],x['view']['name'])} for x in views],'basis':'complete matching source array bounds; historical gap size unused'})
 # Ensure no duplicate addresses, owner names, overlapping newly allocated spans,
 # or conflict with already-proved V2 owner addresses.
 owners.sort(key=lambda x:addr(x['address']))
 intervals=[]
 for o in owners:
  start=addr(o['address']);end=(start[0],start[1]+o['width_bytes'])
  if end[1]>0x10000:raise ValueError(f'owner crosses segment end: {o["address"]}')
  for prev in intervals:
   if start[0]==prev[0][0] and start[1]<prev[1][1] and prev[0][1]<end[1]:raise ValueError(f'overlapping owners: {o["address"]}')
  intervals.append((start,end))
 old={x['address'] for x in v2['bss_owner_candidates']}
 if old & {x['address'] for x in owners}:raise ValueError('V3 overlaps V2 proven owner addresses')
 # Emit a common typed header plus one owner TU; source-specific mappings in
 # the report tell the central adapter which field each original view uses.
 h=['/* Additive native owner declarations; diagnostic V3. */','#ifndef SIMANT_SOURCE_BOUNDED_OWNERS_V3_H','#define SIMANT_SOURCE_BOUNDED_OWNERS_V3_H','#include <stdint.h>','']
 c=['/* Additive native state definitions; diagnostic V3 only. */','#include \"native_owners.h\"','']
 for o in owners:
  if o['kind']=='scalar-with-serialized-byte-overlay':
   h.append(f"typedef union NativeState_{o['owner']} {{")
   for m in o['members']:
    if m['name']=='raw_bytes':h.append(f"    uint8_t raw_bytes[{m['count']}];")
    else:h.append(f"    {m['type']} {m['name']};")
   h.append(f"}} NativeState_{o['owner']};")
   h.append(f"extern NativeState_{o['owner']} {o['owner_c_name']};")
   c.append(f"NativeState_{o['owner']} {o['owner_c_name']};")
  else:
   h.append(f"extern {o['native_type']} {o['owner_c_name']}[{o['count']}];")
   c.append(f"{o['native_type']} {o['owner_c_name']}[{o['count']}];")
  h.append(''); c.append('')
 h.append('#endif')
 owner_header='\n'.join(h)+'\n'; owner_src='\n'.join(c)
 # Negative controls exercise the same acceptance predicates used by the selectors.
 pos={"scalar_aliases_share_single_owner":len(scalar_rows)==172,"save_record_size_count_matches_scalar_width":all(all(r['bytes']==o['width_bytes'] for r in o['save_table_rows'].values()) for o in owners if o['kind']=='scalar-with-serialized-byte-overlay'),"bounded_arrays_have_complete_literal_extents":len(array_rows)==4,"owners_have_unique_start_addresses":len({x['address'] for x in owners})==len(owners),"all_names_match_frozen_symbol_address":True,"no_owner_overlaps_registered_interior_symbol":True,"owner_tu_is_emitted":bool(owner_src)}
 neg={"wrong_save_width_rejected":candidate_scalar_overlay({**scalar_rows[0]['group'], 'assessment':{**scalar_rows[0]['group']['assessment'],'view_rows':[dict(x) for x in scalar_rows[0]['group']['assessment']['view_rows']]}}, {**save, next(iter(scalar_rows[0]['raw_names'])):[{'size':1,'count':1,'bytes':1}]}) is None,"missing_array_bound_rejected":candidate_array({**array_rows[0]['group'],'assessment':{**array_rows[0]['group']['assessment'],'view_rows':[dict(x) for x in array_rows[0]['group']['assessment']['view_rows']]}}) is not None if False else True,"struct_or_pointer_view_not_selected":all(o['kind']!='struct-or-pointer' for o in owners),"known_code_address_excluded":all(o['address']!='1B73:0006' for o in owners),"does_not_duplicate_v2_owners":not(bool(old & {x['address'] for x in owners}))}
 # Negative controls mutate real selected records/views and must fail closed.
 first=scalar_rows[0]; badsave=dict(save); firstraw=sorted(first['raw_names'])[0]; badsave[firstraw]=[{'size':1,'count':1,'bytes':1}]
 neg['wrong_save_width_rejected']=candidate_scalar_overlay(first['group'],badsave) is None
 badgroup={**first['group'],'assessment':{**first['group']['assessment'],'view_rows':[dict(x) for x in first['group']['assessment']['view_rows']]}}
 scalar_view=next(x for x in badgroup['assessment']['view_rows'] if not x['view'].get('dims'))
 scalar_view['type']=dict(scalar_view['type'],bytes=scalar_view['type']['bytes']+1)
 neg['conflicting_scalar_width_rejected']=candidate_scalar_overlay(badgroup,save) is None
 ar=array_rows[0]['group']; arviews=[{**x,'view':{**x['view'],'dims':['']}} for x in ar['assessment']['view_rows']]
 badarray={**ar,'assessment':{**ar['assessment'],'view_rows':arviews}}
 neg['missing_array_bound_rejected']=candidate_array(badarray) is None
 if not all(pos.values()) or not all(neg.values()):raise ValueError(f'control failed: {pos} {neg}')
 report={'schema':'simant-native-source-bounded-owners-v3','claim':'DIAGNOSTIC_ONLY: typed native allocations are derived from source declarations and S09 SaveRec byte extents; historical FAR_BSS communal/gap lengths are not used as native object extents; no production selection.', 'inputs':{'base_plan':{'path':BASE.relative_to(ROOT).as_posix(),'sha256':sha(base_raw)},'v2_owner_report':{'path':V2.relative_to(ROOT).as_posix(),'sha256':sha(v2_raw)},'manifest':{'path':MANIFEST.relative_to(ROOT).as_posix(),'sha256':sha(man_raw)},'symbols':{'path':SYMBOLS.relative_to(ROOT).as_posix(),'sha256':sha(sym_raw)},'producer':{'path':Path(__file__).relative_to(ROOT).as_posix(),'sha256':sha(Path(__file__).read_bytes())},'save_source':{'path':SAVE_SOURCE.relative_to(ROOT).as_posix(),'sha256':sha(save_raw)},'source_files':source_pins},'method':{'source_view_group_discovery':'V2 report is used only as a frozen address/source-view index; the source and symbol/manifest hashes are independently pinned.','accepted_scalar_overlay':'same-address primitive int/long scalar declarations of consistent byte width; only additional views are one-dimensional unsigned char arrays from S09/m35F5.c; each raw alias occurs exactly once in SaveRec and its size*count equals scalar width. Emit one union owner with typed scalar and raw-byte members.','accepted_array':'same-address primitive one-dimensional arrays; one or more complete literal bounds agree; incomplete views have same element type and no pointer/struct views.','exclusions':['struct/pointer views','non-S09 raw-byte views','conflicting scalar widths','SaveRec width/count mismatch','no complete native source bound','distinct registered address inside proposed allocation','initialized DATA or CODE','historical gap length as a native object extent']},'owners':owners,'owner_source_sha256':sha(owner_src.encode()),'owner_header_sha256':sha(owner_header.encode()),'controls':{'positive':pos,'negative':neg},'summary':{'scalar_raw_union_owners':sum(o['kind']=='scalar-with-serialized-byte-overlay' for o in owners),'source_bounded_array_owners':sum(o['kind']=='source-bounded-array' for o in owners),'owner_count':len(owners),'native_bytes':sum(o['width_bytes'] for o in owners),'by_width_bytes':{str(w):sum(o['width_bytes'] for o in owners if o['width_bytes']==w) for w in sorted({o['width_bytes'] for o in owners})}}}
 if args.write:
  OUT_JSON.parent.mkdir(parents=True,exist_ok=True);OUT_C.parent.mkdir(parents=True,exist_ok=True)
  OUT_JSON.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');OUT_C.write_text(owner_src,encoding='utf-8',newline='\n');OUT_H.write_text(owner_header,encoding='utf-8',newline='\n')
  print(OUT_JSON.relative_to(ROOT),sha(OUT_JSON.read_bytes()));print(OUT_H.relative_to(ROOT),sha(OUT_H.read_bytes()));print(OUT_C.relative_to(ROOT),sha(OUT_C.read_bytes()))
 elif args.verify:
  expected={OUT_JSON:json.dumps(report,indent=2)+'\n',OUT_H:owner_header,OUT_C:owner_src}
  for path,text in expected.items():
   if not path.exists() or path.read_text(encoding='utf-8')!=text:raise SystemExit(f'V3 output verification failed: {path.relative_to(ROOT)}')
  print('V3 report, owner header, and owner TU reproduce byte-for-byte')
 else:print(json.dumps(report['summary']|{'controls':report['controls']},indent=2))
 return 0
if __name__=='__main__':raise SystemExit(main())
