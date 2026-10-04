"""Pinned complete effective TU census and whole-module functional-view proposal.

No original executable/resource payload enters compiler inputs. This is a worker
proposal only; owner declarations never assert historical full array capacities.
"""
import hashlib,json,re,sys
from pathlib import Path
sys.dont_write_bytecode=True
OUT=Path(__file__).resolve().parent; ROOT=OUT.parents[2]
sys.path.insert(0,str(ROOT/'tools'))
import csrc,compiler
from omf import OmfReader
compiler.WORK=OUT/'cc'
def sha(b): return hashlib.sha256(b).hexdigest()
def pin(p):
 b=p.read_bytes(); return {'path':str(p).replace('\\','/'),'size':len(b),'sha256':sha(b)}
NAMES=set('''win_colors win_drawHooks win_offsets win_handles
win_SetColorNum win_SetColorFromObj win_SetColorFromObjNum
win_SetObjSelectedStateI win_SetObjSelectedState win_SetGroupSelectedState
win_MakeObjSelected win_MakeObjUnselected win_MakeGroupSelected win_MakeGroupUnselected
win_SetObjSelectableState win_SetGroupSelectableState win_MakeObjSelectable
win_SetWinDrawHook f_22BF_094F DrawControlLevels OpenModeWindow
win_ModeControlChanged win_DrawModeWindow ProcModeEvent f_218D_000C'''.split())
TABLES=set('win_colors win_drawHooks win_offsets win_handles'.split())
def source_census(rows):
 pins=[]; calls=[]; accesses=[]; defs=[]; errors=[]; asm_mentions=[]; nfn=0
 for row in rows:
  p=ROOT/row['generated_source']['path']; fact=pin(p)
  if fact['sha256']!=row['generated_source']['sha256']: raise ValueError('source drift '+str(p))
  fact.update(module=row['module'],lang=row['lang']); pins.append(fact)
  text=p.read_text(encoding='latin1')
  if row['lang']!='c':
   for no,line in enumerate(text.splitlines(),1):
    if any(re.search(r'\b'+re.escape(n)+r'\b',line) for n in NAMES):
     asm_mentions.append({'module':row['module'],'path':str(p),'line':no,'text':line})
   continue
  try: s=csrc.Source(text); funcs=s.functions()
  except Exception as e:
   errors.append({'module':row['module'],'error':str(e),'target_names_present':sorted(NAMES&set(re.findall(r'\b\w+\b',text)))}); continue
  nfn+=len(funcs)
  for fn in funcs:
   if fn.name in NAMES:
    defs.append({'module':row['module'],'function':fn.name,'path':str(p),'line':text.count('\n',0,fn.s)+1})
   for node in csrc.walk(fn.body):
    if isinstance(node,csrc.Call) and isinstance(node.f,csrc.Id) and node.f.name in NAMES:
     calls.append({'module':row['module'],'function':fn.name,'callee':node.f.name,'path':str(p),
      'line':text.count('\n',0,node.s)+1,'arguments':[text[a.s:a.e] for a in node.args],
      'call':text[node.s:node.e]})
   for tok in s.toks:
    if fn.body.s<=tok.s<fn.body.e and tok.kind=='id' and tok.text in TABLES:
     line=text.count('\n',0,tok.s)+1
     accesses.append({'module':row['module'],'function':fn.name,'name':tok.text,'path':str(p),'line':line,
      'text':text.splitlines()[line-1].strip()})
 return {'schema':'window-complete-effective-source-census-v36','root_reviewed':False,'admitted':False,
  'effective_tu_count':len(rows),'c_tu_count':sum(r['lang']=='c' for r in rows),'parsed_c_functions':nfn,
  'source_pins':pins,'parser_failures':errors,'asm_target_mentions':asm_mentions,
  'definitions':defs,'calls':calls,'table_accesses':accesses,
  'limits':['Direct source calls and named storage accesses only; not whole-program reachability or pointer-alias exclusion.',
   'No-caller claims refer to this pinned effective source set; opaque function pointers and data-driven dispatch remain separate.']}
def object_facts(o):
 names={s['name'] for s in o.segment_defs if s.get('class','').upper() not in {'DEBSYM','DEBTYP'}}
 return {'segments':{n:bytes(b) for n,b in o.segments.items() if n in names},
  'segment_lengths':{n:v for n,v in o.segment_lengths.items() if n in names},
  'publics':[p for p in o.publics if p['segment'] in names],
  'fixups':[f for f in o.linker_fixups if f['segment'] in names]}
def proposal(row):
 base=(OUT/'sources/m20E8_baseline.c').read_text(encoding='latin1')
 bo=OmfReader(communals=True).read((OUT/'sources/m20E8_baseline.obj').read_bytes())
 outputs=[]
 for n in (45,46):
  text=base.replace('extern struct Rect far win_offsets[];','struct Rect far win_offsets[%d];'%n)
  text=text.replace('extern void (far * far win_drawHooks[])(int phase);',
   'void (far * far win_drawHooks[%d])(int phase);'%n)
  if text==base or 'extern struct Rect far win_offsets[];' in text or 'win_drawHooks[]' in text:
   raise ValueError('declaration transformation failure')
  p=OUT/'sources'/('m20E8_functional_view%d.c'%n); p.write_text(text,encoding='ascii')
  r=compiler.compile_c(text,row['profile'],row['flags'],basename='UNIT')
  p.with_suffix('.compiler.log').write_text(r.log,encoding='utf-8')
  if not r.ok: raise ValueError(r.log)
  p.with_suffix('.obj').write_bytes(r.obj); o=OmfReader(communals=True).read(r.obj)
  outputs.append({'source':pin(p),'object':pin(p.with_suffix('.obj')),'communals':o.communals,
   'nondebug_code_data_publics_ordered_fixups_equal_baseline':object_facts(o)==object_facts(bo),
   'scope':'Functional initialized views; no historical defining TU, maximal extent, order or placement claim.'})
 result={'schema':'window-functional-view-worker-proposal-v36','root_reviewed':False,'admitted':False,
  'proposed_owner_module':'root:20E8','functional_view45_bytes':{'win_drawHooks':180,'win_offsets':360},
  'drafts':outputs,'scope':['Initialization writes independently prove these source-owned spans.',
   'Installed window IDs0..33 and intended lock-admitted IDs0..40 fit; all named access forms retained.',
   'Zero far common initial bytes require verified source linker allocation before CRT, not near BSS clear.',
   'Malformed/unrestricted IDs, resource lengths, menu/palette computed aliases and their placement effects remain hard gates.',
   'The proposal closes no historical full-capacity, whole-pool or alias-free layout assertion.']}
 (OUT/'functional-view-proposal.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
 return result
def main():
 report=json.loads((ROOT/'build/source-only-dos-v35/build-report.json').read_text()); rows=report['translation_units']
 census=source_census(rows); (OUT/'source-census.json').write_text(json.dumps(census,indent=2),encoding='utf-8')
 prop=proposal(next(r for r in rows if r['module']=='root:20E8'))
 print(json.dumps({'census_counts':{k:census[k] for k in ('effective_tu_count','c_tu_count','parsed_c_functions')},
  'parser_failures':census['parser_failures'],'asm_mentions':census['asm_target_mentions'],
  'direct_selection_calls':[c for c in census['calls'] if 'Selected' in c['callee']],
  'drafts':prop['drafts']},indent=2))
if __name__=='__main__': main()
