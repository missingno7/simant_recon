"""Read-only source ownership investigation; all generated files stay here.

No candidate definition is accepted. Dimensions41/42 below are deliberately
extern-only controls that expose the inability of consumer bytes to measure extent.
"""
from pathlib import Path
import hashlib,json,re,sys,subprocess,os
sys.dont_write_bytecode=True
OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[2]
sys.path.insert(0,str(ROOT/'tools'))
import csrc,compiler,exe
from omf import OmfReader
compiler.WORK=OUT/'cc'
def sha(b): return hashlib.sha256(b).hexdigest()
def pin(p):
 b=p.read_bytes(); return dict(path=str(p).replace('\\','/'),size=len(b),sha256=sha(b))
def write(name,data):
 (OUT/name).write_text(json.dumps(data,indent=2),encoding='utf-8')
TARGETS={'win_handles','g_9230'}
def census(rows):
 pins=[]; touches=[]; numerics=[]; errors=[]; count=0; asm=[]; defs=[]
 for row in rows:
  p=ROOT/row['generated_source']['path']; fact=pin(p)
  if fact['sha256']!=row['generated_source']['sha256']: raise ValueError('source drift '+str(p))
  fact.update(module=row['module'],lang=row['lang']); pins.append(fact)
  t=p.read_text(encoding='latin1')
  if row['lang']!='c':
   for no,line in enumerate(t.splitlines(),1):
    if re.search(r'\b(?:win_handles|g_9230|9230h|0x9230)\b',line): asm.append(dict(module=row['module'],line=no,text=line))
   continue
  try: s=csrc.Source(t); fs=s.functions()
  except Exception as e: errors.append(dict(module=row['module'],error=str(e))); continue
  count+=len(fs)
  for no,line in enumerate(t.splitlines(),1):
   if re.search(r'\b(?:0x9230|37424)\b',line): numerics.append(dict(module=row['module'],line=no,text=line))
   if re.search(r'\b(?:win_handles|g_9230)\b',line):
    owner=next((f.name for f in fs if t.count('\n',0,f.s)+1<=no<=t.count('\n',0,f.e)+1),None)
    touches.append(dict(module=row['module'],path=str(p).replace('\\','/'),line=no,function=owner,text=line.strip()))
    if owner is None: defs.append(dict(module=row['module'],line=no,declaration=line.strip()))
 return dict(schema='window-handles-complete-effective-census-v37',root_reviewed=False,admitted=False,
   effective_tu_count=len(rows),c_tu_count=sum(r['lang']=='c' for r in rows),parsed_c_functions=count,
   source_pins=pins,declarations=defs,direct_touches=touches,numeric_address_mentions=numerics,
   asm_target_mentions=asm,parser_failures=errors,
   limits=['Named-source and exact numeric spelling census; not whole-program alias or reachability proof.'])
def projection(o):
 names={s['name'] for s in o.segment_defs if s.get('class','').upper() not in {'DEBSYM','DEBTYP'}}
 return dict(segments={n:sha(bytes(b)) for n,b in o.segments.items() if n in names},
   lengths={n:v for n,v in o.segment_lengths.items() if n in names},
   publics=[p for p in o.publics if p['segment'] in names],
   ordered_fixups=[f for f in o.linker_fixups if f['segment'] in names],
   communals=o.communals)
def compile_one(label,t,profile,flags):
 d=OUT/'sources'; d.mkdir(exist_ok=True); p=d/(label+'.c'); p.write_text(t,encoding='ascii')
 r=compiler.compile_c(t,profile,flags,basename='UNIT')
 p.with_suffix('.compiler.log').write_text(r.log,encoding='utf-8')
 if not r.ok: raise ValueError(label+' '+r.log)
 p.with_suffix('.obj').write_bytes(r.obj); o=OmfReader(communals=True).read(r.obj)
 return dict(source=pin(p),object=pin(p.with_suffix('.obj')),compiler_log=pin(p.with_suffix('.compiler.log')),
   profile=profile,flags=flags,nondebug_projection=projection(o),segment_defs=o.segment_defs,
   external_scopes=o.external_scopes)
def controls(rows):
 out=[]
 for module in ('root:20E8','root:22BF','root:23AE','root:2505'):
  row=next(r for r in rows if r['module']==module); p=ROOT/row['generated_source']['path']
  src=p.read_text(encoding='latin1'); decl='extern char far * far * near win_handles[];'
  if src.count(decl)!=1: raise ValueError('declaration '+module)
  label='m'+module.split(':')[1]; base=compile_one(label+'_baseline',src,row['profile'],row['flags'])
  out.append(dict(module=module,case='baseline',**base)); print(module,'baseline',flush=True)
  for dimension in (41,42):
   t=src.replace(decl,decl.replace('[]','[%d]'%dimension))
   fact=compile_one(label+'_extern%d'%dimension,t,row['profile'],row['flags'])
   same=fact['nondebug_projection']==base['nondebug_projection']
   if not same: raise ValueError('unexpected dimension-dependent object '+module)
   out.append(dict(module=module,case='extern%d'%dimension,
     equal_complete_nondebug_code_data_publics_ordered_fixups_communals=same,**fact))
   print(module,'extern'+str(dimension),same,flush=True)
  t=src.replace(decl,'extern char far * far * far win_handles[];')
  fact=compile_one(label+'_far_outer',t,row['profile'],row['flags'])
  same=fact['nondebug_projection']==base['nondebug_projection']
  if same: raise ValueError('far-outer negative unexpectedly identical '+module)
  out.append(dict(module=module,case='far_outer_negative',
    equal_complete_nondebug_code_data_publics_ordered_fixups_communals=same,**fact))
  print(module,'far outer',same,flush=True)
 # This describes declaration ABI only. It is explicitly not a table owner.
 t='''typedef char far *WindowData;
typedef WindowData far *WindowHandle;
struct PointerABI {
 unsigned near_outer,far_outer,handle,window_data;
};
struct PointerABI probe = {sizeof(WindowHandle near *),sizeof(WindowHandle far *),sizeof(WindowHandle),sizeof(WindowData)};
'''
 fact=compile_one('pointer_abi',t,'msc600ax',['/AL','/Os','/Gs'])
 o=OmfReader(communals=True).read((OUT/'sources/pointer_abi.obj').read_bytes())
 fact['initialized_data_bytes_hex']=bytes(o.segments['_DATA']).hex()
 out.append(dict(module='declaration ABI only',case='pointer_abi',**fact))
 return dict(schema='window-handle-whole-consumer-omf-controls-v37',root_reviewed=False,admitted=False,
   cases=out,limits=['Extern41/42 do not define storage and cannot prove lower/maximal capacity.',
   'Far outer contrast changes actual whole consumer OMF and rejects an incorrect outer address space.',
   'Pointer ABI measured by natural sizeof expressions; no synthesized game reset/owner/runtime input.'])
def extracted(rows):
 result=[]
 wanted={'root:23AE':['win_LockInit','f_23AE_0069','win_UnlockWin'],
   'root:20E8':['win_LoadWindow','win_LoadAllWindows'],
   'root:22BF':['win_IsWinOpen'],'root:2505':['f_2505_0006','win_Recalc']}
 for module,names in wanted.items():
  p=ROOT/next(r for r in rows if r['module']==module)['generated_source']['path']; t=p.read_text(encoding='latin1'); s=csrc.Source(t)
  for f in s.functions():
   if f.name in names:
    result.append(dict(module=module,function=f.name,source=pin(p),first_line=t.count('\n',0,f.s)+1,
      exact_function_source=t[f.s:f.e],win_handles_occurrences=sum(tok.text=='win_handles' for tok in s.toks if f.s<=tok.s<f.e)))
 return result
def startup():
 # Original image bytes are research-only, never copied into compiler inputs.
 x=exe.load(); raw=x.read('S27',0x55b3*16+0x9230,164)
 sys.path.insert(0,'C:/tools/capstone-5.0.3')
 from capstone import Cs,CS_ARCH_X86,CS_MODE_16
 b=x.read('root',0x29f69,0x2a021-0x29f69)
 instructions=[dict(linear=hex(i.address),text=(i.mnemonic+' '+i.op_str).strip()) for i in Cs(CS_ARCH_X86,CS_MODE_16).disasm(b,0x29f69)]
 required={'mov di, 0x8b9e','mov cx, 0x94f0','sub cx, di','xor ax, ax','rep stosb byte ptr es:[di], al','lcall 0x15f8, 4'}
 if not required.issubset({i['text'] for i in instructions}): raise ValueError('startup disassembly unexpected')
 return dict(original_exe=pin(ROOT/'assets/SIMANT.EXE'),researched_proposed41_bytes=164,
   interval={'seg':0x55b3,'start':0x9230,'end_exclusive':0x92d4},
   loaded_image_bytes_present=len(raw),all_zero_image_view=(not any(raw)) if len(raw)==164 else None,
   image_view_sha256=sha(raw) if len(raw)==164 else None,
   image_scope='Near table is outside stored S27 payload. An empty slice is not a zero-state observation.',
   near_crt_clear_interval={'start':0x8b9e,'end_exclusive':0x94f0},
   startup_instructions=instructions,
   prior_independent_runtime_anchor_receipt=pin(ROOT/'work/source-only-dos/queue-lifetime-contract-v1.json'),
   scope='CRT broad zero interval establishes initial null representation where storage exists; it does not establish the producing Handle allocation or extent.')
def main():
 report=ROOT/'build/source-only-dos-v36/build-report.json'; rows=json.loads(report.read_text())['translation_units']
 write('source-census.json',census(rows)); write('source-extractions.json',extracted(rows))
 write('startup-observation.json',startup())
 write('full-omf-controls.json',controls(rows))
 write('input-pins.json',dict(build_report=pin(report),inputs=[pin(ROOT/p) for p in (
   'src/root/m23AE.c','src/root/m20E8.c','src/root/m22BF.c','src/root/m2505.c','layout/symbols.json','layout/toolchain.json',
   'tools/compiler.py','tools/csrc.py','tools/omf.py','tools/context.py',
   'work/source-only-dos/critical-error-selector-source-review-v18.md',
   'build/workers/dos_window_owner_v36/review-v36.md',
   'build/workers/dos_unlock_clobber_review_v19/clobber-review-v19.md',
   'build/workers/dos_unlock_event_closure_v20/source-review-v20.md',
   'build/workers/dos_event16_root_review_support_v25/root-review-support-v25.md')]))
 print('COMPLETE, negative ownership verdict remains',flush=True)
if __name__=='__main__': main()
