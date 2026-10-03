#!/usr/bin/env python3
"""Plan a bounded second batch of SaveRec-backed simulation state."""
from __future__ import annotations
import hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'portable/research/whole_program_simulation_state_50f6_v7.json'
TARGETS={
 'fd_50F6_0F46':('byte-table-signed-view',50),'fd_50F6_0FC6':('byte-table-signed-view',50),
 'fd_50F6_0F84':('byte-table-signed-view',50),'fd_50F6_1008':('byte-table-signed-view',50),
 'fd_50F6_0256':('byte-table',100),'fd_50F6_02C0':('byte-table',100),
 'fd_50F6_0334':('word-array',12),'fd_50F6_0AEC':('word-array-prefix-scalar',6),
 'fd_50F6_0AFA':('word-array',6),'fd_50F6_0B12':('word-array',6),
 'fd_50F6_0C2A':('word-array',6),'casteLevels':('tri-level-struct',3),'modeLevels':('word-array',3),
}
EXCLUDED={'fd_50F6_037C':'already-owned V3 100-byte ring array','fd_50F6_0404':'already-owned V3 100-byte ring array',
 'fd_50F6_0508':'V6 point owner','fd_50F6_0596':'V6 point owner','fd_50F6_06A6':'V6 point owner','fd_50F6_072E':'V6 point owner','fd_50F6_07BC':'V6 point owner','fd_50F6_07CA':'V6 point owner',
 'fd_50F6_0516':'V6 history owner','fd_50F6_05A0':'V6 history owner','fd_50F6_0626':'V6 history owner','fd_50F6_06AE':'V6 history owner','fd_50F6_073C':'V6 history owner','fd_50F6_07CE':'V6 history owner','fd_50F6_0856':'V6 history owner','fd_50F6_08F0':'V6 history owner','fd_50F6_0970':'V6 history owner','fd_50F6_0A0A':'V6 history owner',
 'PillarMap':'V5 owner','SowX':'V5 owner','SowY':'V5 owner','SowDir':'V5 owner','SowSave':'V5 owner',
 'MapA':'existing data owner','MapB':'existing data owner','MapR':'existing data owner','ExitMapB':'existing data owner','ExitMapR':'existing data owner',
 'PherMapA':'existing data owner','PherMapBN':'existing data owner','PherMapBT':'existing data owner','PherMapRN':'existing data owner','PherMapRT':'existing data owner'}
def sha(b:bytes)->str:return hashlib.sha256(b).hexdigest()
def pin(path:Path)->dict[str,str]:return {'path':path.relative_to(ROOT).as_posix(),'sha256':sha(path.read_bytes())}
def overlap(a:str,an:int,b:str,bn:int)->bool:
 sa,oa=(int(x,16) for x in a.split(':'));sb,ob=(int(x,16) for x in b.split(':'))
 return sa==sb and oa<ob+bn and ob<oa+an
def main()->None:
 if OUT.exists():raise SystemExit(f'refusing to overwrite immutable report {OUT.relative_to(ROOT)}')
 sym=json.loads((ROOT/'layout/symbols.json').read_text(encoding='utf-8'))['data']
 save_source=ROOT/'src/S09/m35F5.c';save_text=save_source.read_text(encoding='latin1')
 rows={}
 for size,count,name in re.findall(r'\{\s*(\d+)\s*,\s*(\d+)\s*,\s*\(void\s+far\s*\*\)\s*&([A-Za-z_]\w*)\s*\}',save_text):
  rows.setdefault(name,[]).append({'element_bytes':int(size),'count':int(count),'serialized_bytes':int(size)*int(count)})
 targets=[];source_hashes={};source_rows={}
 for name,(kind,count) in TARGETS.items():
  if name not in sym:raise ValueError(f'missing symbol address for {name}')
  expected=(1,count) if kind.startswith('byte-') else (2,count)
  rec=rows.get(name,[])
  if rec!=[{'element_bytes':expected[0],'count':expected[1],'serialized_bytes':expected[0]*expected[1]}]:raise ValueError(f'{name} SaveRec row mismatch: {rec}')
  declarations=[];definitions=[]
  for path in sorted((ROOT/'src').rglob('*.c')):
   content=path.read_text(encoding='latin1')
   for lineno,line in enumerate(content.splitlines(),1):
    if not re.search(r'\b'+re.escape(name)+r'\b',line):continue
    if re.search(r'\bextern\b',line) and re.search(r'(?:struct\s+\w+|(?:unsigned|signed)?\s*(?:char|short|int))',line):
     declarations.append({'source':path.relative_to(ROOT).as_posix(),'line':lineno,'text':line.strip()})
     source_hashes[path.relative_to(ROOT).as_posix()]=sha(path.read_bytes())
     source_rows.setdefault(path.relative_to(ROOT).as_posix(),[]).append({'line':lineno,'text':line.strip(),'symbol':name})
    elif re.search(r'^\s*(?:(?:unsigned|signed)\s+)?(?:char|short|int|struct\s+\w+)\b.*\b'+re.escape(name)+r'\b',line):
     definitions.append({'source':path.relative_to(ROOT).as_posix(),'line':lineno,'text':line.strip()})
  if not declarations:raise ValueError(f'{name} has no source view declaration')
  if definitions:raise ValueError(f'{name} already has a source object definition; do not duplicate: {definitions}')
  if kind=='tri-level-struct' and not any('struct TriLevel' in d['text'] for d in declarations):raise ValueError('casteLevels lacks TriLevel view')
  if kind=='word-array-prefix-scalar':
   if not any(re.search(r'fd_50F6_0AEC\s*;',d['text']) for d in declarations) or not any(re.search(r'fd_50F6_0AEC\s*\[\s*6\s*\]',d['text']) for d in declarations):raise ValueError('0AEC scalar/array alias set incomplete')
  address=f"{sym[name]['seg']:04X}:{sym[name]['off']:04X}"
  byte_extent=expected[0]*expected[1]
  target={'symbol':name,'address':address,'kind':kind,'count':count,'extent_bytes':byte_extent,'save_rec_rows':rec,'source_declarations':declarations,'source_definitions':definitions,
    'native_view':('union { int8_t signed_values[N]; uint8_t unsigned_values[N]; uint8_t raw_bytes[N]; }' if kind=='byte-table-signed-view' else
      'union { uint8_t unsigned_values[N]; uint8_t raw_bytes[N]; }' if kind=='byte-table' else
      'union { struct TriLevel tri; int16_t signed_values[3]; uint16_t unsigned_values[3]; uint8_t raw_bytes[6]; }' if kind=='tri-level-struct' else
      f'union {{ int16_t signed_values[{count}]; uint16_t unsigned_values[{count}]; uint8_t raw_bytes[{byte_extent}]; }}'),
    'extent_basis':'Exact S09 SaveRec row size*count; additionally complete fixed-size source array or struct view where present. No communal-gap or neighboring-address extent.'}
  targets.append(target)
 pins={}
 for rel in ['layout/manifest.json','layout/symbols.json','src/S09/m35F5.c','src/root/m0BE8.c','src/root/m0894.c','src/root/m0798.c','src/root/m0E2E.c','src/root/m1383.c','src/S13/m384C.c',
  'portable/research/whole_program_unprovided_owners_v2.json','portable/research/whole_program_source_bounded_owners_v3.json','portable/research/whole_program_source_bounded_owners_v5.json',
  'portable/research/whole_program_simulation_state_50f6_v6.json','portable/research/whole_program_simulation_state_50f6_consumer_v6.json']:
  p=ROOT/rel
  if p.exists():pins[rel]=pin(p)
 ranges=[]
 for rel in ['portable/research/whole_program_source_bounded_owners_v3.json','portable/research/whole_program_source_bounded_owners_v5.json']:
  for o in json.loads((ROOT/rel).read_text(encoding='utf-8'))['owners']:
   width=o.get('width_bytes')
   if width and o.get('address'):ranges.append((o['address'],int(width),rel+':'+str(o.get('owner',o.get('name',o.get('owner_c_name'))))))
 v2=json.loads((ROOT/'portable/research/whole_program_unprovided_owners_v2.json').read_text(encoding='utf-8'))
 for o in v2.get('bss_owner_candidates',[]):
  width=o.get('owner_extent_bytes',o.get('extent_bytes',o.get('width_bytes')))
  if width and o.get('address'):ranges.append((o['address'],int(width),'V2:'+str(o.get('owner',o.get('unprovided_members',['?'])[0]))))
 collisions=[{'symbol':t['symbol'],'other':who} for t in targets for a,n,who in ranges if overlap(t['address'],t['extent_bytes'],a,n)]
 internal=[]
 for i,a in enumerate(targets):
  for b in targets[i+1:]:
   if overlap(a['address'],a['extent_bytes'],b['address'],b['extent_bytes']):internal.append([a['symbol'],b['symbol']])
 if collisions or internal:raise ValueError(f'V7 range collision: prior={collisions}, internal={internal}')
 report={'schema':'simant-whole-program-simulation-state-plan-v7','claim':'DIAGNOSTIC_ONLY: proposed shared owners for source-declared/save-record-backed simulation arrays and typed triples; no production selection.',
  'scope':{'target_count':len(targets),'excluded_existing_owners':EXCLUDED,'data_audio_ui_out_of_scope':True},
  'targets':targets,'source_hashes':dict(sorted(source_hashes.items())),'source_declaration_rows':source_rows,'input_hashes':pins,
  'collision_check':{'existing_v2_v3_v5_overlap_count':len(collisions),'candidate_internal_overlap_count':len(internal),'overlaps':collisions+internal},
  'initialized_data_review':{'casteLevels_has_source_definition':False,'modeLevels_has_source_definition':False,'original_source_definitions':[],
    'presets_are_separate_initialized_C_DATA':'fd_3D57_07EC and fd_3D57_080A defaults plus fd_3D57_07F2/fd_3D57_0810 preset tables remain their existing source definitions and are excluded; they are not aliases of the F6 mutable triples.'},
  'alias_policy':{'byte_tables':'signed-char and unsigned-char views use signed_values/unsigned_values members respectively; SaveRec uses raw_bytes overlay.','word_arrays':'signed and unsigned source views use same word slots; raw bytes exist solely for exact S09 serialization.','casteLevels':'source TriLevel view preserved; no zero initializer or copied defaults added.','modeLevels':'signed/unsigned three-word indexing views share one six-byte object.','fd_50F6_0AEC':'six-element array is primary storage view; lone scalar view maps only to element zero.'},
  'nonclaims':['No 50F6 original MSC COMDEF extent artifact used.','No SaveGame compatibility is established until actual SaveGame/LoadGame test receipt passes.','No rendering/UI, audio, pixel, or full-game behavior claim.','No edits to original sources, existing plans, generated providers, or central generator.']}
 OUT.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
 print(f'WROTE {OUT.relative_to(ROOT)} targets={len(targets)} source_files={len(source_hashes)} prior_overlaps=0 internal_overlaps=0')
if __name__=='__main__':main()
