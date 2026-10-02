"""Reproduce bounded raw-address wrapper/empty-entry comparisons.

Run from repository root with the pinned tools/behavior.py dependencies available.
This writes only under build/workers/behavior_gap_repro and the accompanying
archive when explicitly invoked with --archive. No DOS EXE bytes are copied.
"""
from __future__ import annotations
import argparse, hashlib, json, random, sys, struct, shutil
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT/'tools'))
import behavior, exe, modctx, match, modules, functions
from behavior import Case, Callback, Range
OUT=ROOT/'build/workers/behavior_gap_repro'
ARCH=ROOT/'work/takeover/behavioral-oracle/debt-audit'
CANDIDATES=[]

def sha(b): return hashlib.sha256(b).hexdigest()
def addr(name):
 s=behavior.symbol(name); return s['seg']*16+s['off']
def far(off,seg): return behavior.words(off,seg)
def compile_candidate(ctxfn, source_rel, target_name, off, size, insertion):
 source=ROOT/source_rel
 text=source.read_text(encoding='latin1')
 anchor, fragment=insertion
 if anchor is None: text += fragment
 else:
  if text.count(anchor)!=1: raise RuntimeError(f'{source_rel}: anchor not unique: {anchor!r}')
  text=text.replace(anchor,fragment+anchor,1)
 ctx=modctx.resolve(func=ctxfn,source=source)
 original=exe.load().read(ctx.unit,ctx.seg*16+off,size)
 claim={'name':target_name,'unit':ctx.unit,'seg':ctx.seg,'off':off,'size':size,'target_sha256':sha(original),'kind':'C'}
 collected={}; result=modules.verify_module(text,ctx.module_dict(),list(ctx.claims)+[claim],collect=collected)
 if not result.get('compile_ok'): raise RuntimeError(f'{target_name}: compile failed {result.get("log")}')
 if not result.get('claims',{}).get(target_name,{}).get('exact'): raise RuntimeError(f'{target_name}: target not exact {result["claims"].get(target_name)}')
 obj=modctx.read_obj(collected['object']); pub,prec=match.public_in(obj,target_name)
 if not prec: raise RuntimeError(f'{target_name}: missing candidate public')
 OUT.mkdir(parents=True,exist_ok=True)
 (OUT/f'{target_name}.c').write_text(text,encoding='latin1')
 (OUT/f'{target_name}.obj').write_bytes(collected['object'])
 item={'function':target_name,'ctx':ctx,'text':text,'obj':obj,'obj_bytes':collected['object'],'public':prec,
  'source_rel':source_rel,'source_sha256':sha(source.read_bytes()),'compiled_source_sha256':sha(text.encode('latin1')),
  'object_sha256':sha(collected['object']),'target_sha256':sha(original),'target_size':size,
  'target_exact':True,'accepted_peer_failures':{n:r.get('reasons',[]) for n,r in result['claims'].items() if n!=target_name and not r.get('exact')},
  'data_failures':{n:r.get('reasons',[]) for n,r in result.get('data',{}).items() if not r.get('exact')},
  'all_other_claims_exact':all(r.get('exact') for n,r in result['claims'].items() if n!=target_name),
  'profile':ctx.profile,'flags':ctx.flags,'module':ctx.key}
 CANDIDATES.append({k:item[k] for k in ('function','source_rel','source_sha256','compiled_source_sha256','object_sha256','target_sha256','target_size','target_exact','accepted_peer_failures','data_failures','all_other_claims_exact','profile','flags','module')})
 return item

def make_pair(item, target):
 obj=item['obj']; ctx=item['ctx']; raw=obj.segments['UNIT_TEXT']
 bound=behavior.ExecutionBinder(match.Target(target['unit'],behavior.CODE_SEG,0,len(raw)),obj,'UNIT_TEXT',None,ctx.placements_bind,span=(0,len(raw))).bind()
 if bound.unbound: raise RuntimeError(f'{item["function"]}: unbound {bound.unbound}')
 entries={};delegate={}
 for p in obj.publics+getattr(obj,'local_publics',[]):
  if p['segment']!='UNIT_TEXT': continue
  name=p['name'][1:] if p['name'].startswith(('_','@')) else p['name']; location=behavior.CODE_SEG*16+p['offset'];entries[name]=location
  if p['offset']!=item['public']['offset']:
   try: delegate[location]=behavior.symbol(name)
   except KeyError: pass
 pair=SimpleNamespace(function=target,code=bound.candidate,candidate_entry=(behavior.CODE_SEG,item['public']['offset']),candidate_entries=entries,
   delegate=delegate,vectors={exe.MANAGER_SEG*16+v.offset:v for v in exe.load().vectors},sequence_targets=frozenset(),
   sequence_function=lambda n:functions.get(n))
 pair.original_machine=behavior.Machine(pair); pair.candidate_machine=behavior.Machine(pair,True)
 return pair

def compare(pair,case):
 a=pair.original_machine.run(case); b=pair.candidate_machine.run(case)
 return behavior.PreparedPair._comparison(pair,case,a,b)

def wrapper_cases():
 cases=[]
 # root 1C62:069E invokes the real dispatcher; only its optional callback is a trace boundary.
 t={'name':'f_1C62_069E','unit':'root','seg':0x1C62,'off':0x069e,'size':8}
 src=compile_candidate('f_1C62_06A6','src/root/m1C62.c',t['name'],t['off'],t['size'],
   ('char far * far f_1C62_06A6(int err)','int far f_1C62_069E(void) { f_1C62_0090(); return 1; }\n\n'))
 p=make_pair(src,t); flag=addr('_fd_55B3_6262'); g=addr('_g_9178')
 for on in (0,1):
  case=Case(f'1C62:069E gate={on}',writes=[(flag,behavior.words(on)),(g,far(0x00A1,0x1C62))],observe=[Range('callback_enable',flag,2),Range('callback_ptr',g,4)],callbacks={'f_1C62_00A1':Callback(0,lambda m,a:m.state.update(callbacks=m.state.get('callbacks',0)+1))},return_kind='u16')
  case.metadata['modeled_boundaries']=['f_1C62_00A1 callback body']
  cases.append(('f_1C62_069E',case,compare(p,case)))
 # root 1E57:0EB0 executes both real clip helpers; only allocator/handle services are modeled.
 t={'name':'f_1E57_0EB0','unit':'root','seg':0x1E57,'off':0x0eb0,'size':9}
 insertion=('void far clip_Pop(void)','void far f_1E57_0EB0(void) { clip_Push(); clip_Off(); }\n\n')
 src=compile_candidate('clip_Push','src/root/m1E57.c',t['name'],t['off'],t['size'],insertion)
 p=make_pair(src,t)
 handle=(0x5000,0x55B3); node=(0x3000,0x55B3); clip=(0x2f00,0x55b3)
 def alloc(m,a):m.state.setdefault('alloc_calls',[]).append(a);return handle
 def lock(m,a):m.state.setdefault('lock_calls',[]).append(a);return node
 def unlock(m,a):m.state.setdefault('unlock_calls',[]).append(a);return None
 callbacks={'f_171C_1A9E':Callback(5,alloc),'f_171C_1B84':Callback(2,lock),'f_171C_1BBA':Callback(2,unlock)}
 for nonempty in (False,True):
  words=[10,20,30,40,0,0x8000,0,0] if nonempty else [0]*8
  clip_addr=clip[1]*16+clip[0]
  writes=[(addr('g_5756'),behavior.words(0)),(addr('g_5758'),behavior.words(0)),(addr('_fd_50F6_3B5C'),far(0,0)),(addr('g_5AAC'),far(clip[0] if nonempty else 0,clip[1] if nonempty else 0)),(clip_addr,behavior.words(*words)),(node[1]*16+node[0],b'\0'*32)]
  observed=[Range('clip_current',addr('g_5AAC'),4),Range('clip_stack',addr('_fd_50F6_3B5C'),4),Range('stack_depth',addr('g_5756'),2),Range('stack_size',addr('g_5758'),2),Range('saved_node',node[1]*16+node[0],32)]
  case=Case(f'1E57:0EB0 clip-list-nonempty={nonempty}',writes=writes,observe=observed,callbacks=callbacks,return_kind='void')
  case.metadata['modeled_boundaries']=['f_171C_1A9E heap allocation','f_171C_1B84 handle-to-pointer','f_171C_1BBA unlock'];case.metadata['actual_helpers']=['clip_Push','clip_Off','_fmemcpy when list nonempty']
  cases.append(('f_1E57_0EB0',case,compare(p,case)))
 # S04 toggle calls natural Draw/Erase bodies; the renderer is a trace boundary.
 t={'name':'o04_35F5_0980','unit':'S04','seg':0x35F5,'off':0x0980,'size':24}
 src=compile_candidate('DrawMiniMapCursor','src/S04/m35F5.c',t['name'],t['off'],t['size'],(None,'\nvoid far o04_35F5_0980(void) { if (miniCursorOn) EraseMiniMapCursor(); else DrawMiniMapCursor(); }\n'))
 p=make_pair(src,t); mini=0x55b3*16+0x2338; rect=addr('_fd_50F6_384A')
 def inv(m,a):m.state.setdefault('rect_calls',[]).append({'args':a[2:],'rect':m.read(a[0]+a[1]*16,8).hex()});return None
 for initial in (0,1):
  writes=[(addr('_fd_50F6_0508'),behavior.words(3,4)),(addr('_fd_50F6_3842'),behavior.words(10,20,110,220)),(addr('_fd_50F6_3852'),behavior.words(2)),(addr('_fd_50F6_10DE'),behavior.words(5)),(addr('_fd_50F6_10E0'),behavior.words(6)),(addr('g_8BD2'),behavior.words(2)),(addr('g_8BD4'),behavior.words(3)),(mini,behavior.words(initial))]
  case=Case(f'S04:0980 miniCursorOn={initial}',writes=writes,observe=[Range('rect',rect,8),Range('miniCursorOn',mini,2)],callbacks={'f_1CE2_0410':Callback(3,inv)},return_kind='void')
  case.metadata['modeled_boundaries']=['f_1CE2_0410 rendering helper'];case.metadata['actual_helpers']=['o04_35F5_0980','DrawMiniMapCursor','EraseMiniMapCursor']
  cases.append(('o04_35F5_0980',case,compare(p,case)))
 # Empty far functions under /Gs: compare raw entry behavior over directed caller-register canaries.
 empty_specs=[
  ('f_1E57_0009','src/root/m1E57.c','f_1E57_0008',0x0008,1,'extern struct Rect far * near g_5AAC;','void far f_1E57_0008(void) {}\n\n'),
  ('win_LockWin','src/root/m23AE.c','f_23AE_037E',0x037e,1,'void _fastcall win_LockWin(int win)\n{\n    f_23AE_0069(win, 0);\n}','void far f_23AE_037E(void) {}\n\n'),
  ('StopSong','src/root/m284A.c','f_284A_0137',0x0137,1,'/* SCAFFOLD BEGIN: context only, not reconstruction.','void far f_284A_0137(void) {}\n\n')]
 for ctxfn,source,name,off,size,anchor,fragment in empty_specs:
  if ctxfn=='win_LockWin': insertion=(None,'\n'+fragment)
  else: insertion=(anchor,fragment+anchor)
  item=compile_candidate(ctxfn,source,name,off,size,insertion)
  target={'name':name,'unit':item['ctx'].unit,'seg':item['ctx'].seg,'off':off,'size':size}
  pair=make_pair(item,target)
  for i,values in enumerate(({}, {'ax':0,'bx':0xffff,'cx':0x1357,'dx':0x2468}, {'ax':0xa55a,'bx':0x5aa5,'cx':0xffff,'dx':0}, {'ax':0x1234,'bx':0x5678,'cx':0x9abc,'dx':0xdef0})):
   case=Case(f'{name} empty-retf register-canary={i}',registers=values,return_kind='void')
   result=compare(pair,case)
   # Include volatile and preserved post-call registers; the regular comparator separately enforces ABI.
   result.original['registers_after']={r:pair.original_machine.reg(r) for r in ('ax','bx','cx','dx','si','di','bp','sp','ds','es')}
   result.candidate['registers_after']={r:pair.candidate_machine.reg(r) for r in ('ax','bx','cx','dx','si','di','bp','sp','ds','es')}
   if result.original['registers_after']!=result.candidate['registers_after']:
    result.equal=False;result.diff['registers_after']={'oracle':result.original['registers_after'],'candidate':result.candidate['registers_after']}
   cases.append((name,case,result))
 return cases

def main():
 OUT.mkdir(parents=True,exist_ok=True)
 cases=wrapper_cases(); report={'schema':'supplemental-address-proof-v2','oracle_sha256':exe.load().sha256,'manifest_sha256':sha((ROOT/'layout/manifest.json').read_bytes()),'candidates':CANDIDATES,
  'harness_sha256':sha(behavior.HARNESS_SOURCE),'components':{'producer_sha256':sha(Path(__file__).read_bytes()),'behavior.py':sha((ROOT/'tools/behavior.py').read_bytes()),'compiler.py':sha((ROOT/'tools/compiler.py').read_bytes()),'modules.py':sha((ROOT/'tools/modules.py').read_bytes()),'modctx.py':sha((ROOT/'tools/modctx.py').read_bytes()),'match.py':sha((ROOT/'tools/match.py').read_bytes()),'toolchain.json':sha((ROOT/'layout/toolchain.json').read_bytes())},'runs':[]}
 for name,case,result in cases:
  report['runs'].append({'function':name,'case':case.label,'equal':result.equal,'diff':result.diff,'modeled_boundaries':case.metadata.get('modeled_boundaries',[]),'actual_helpers':case.metadata.get('actual_helpers',[]),'original':result.original,'candidate':result.candidate})
 if not all(r['equal'] for r in report['runs']):raise SystemExit('mismatch; inspect full report before any claim')
 (OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n')
 archive=ARCH/'reproducible-wrapper-proof'; archive.mkdir(parents=True,exist_ok=True)
 shutil.copy2(OUT/'report.json',archive/'report.json')
 shutil.copy2(Path(__file__),archive/'reproduce_wrapper_proofs.py')
 for item in CANDIDATES:
  for suffix in ('.c','.obj'):
   p=OUT/(item['function']+suffix)
   if p.exists(): shutil.copy2(p,archive/p.name)
 print(json.dumps({'run_count':len(report['runs']),'equal':all(r['equal'] for r in report['runs']),'report':str(OUT/'report.json')},indent=2))
if __name__=='__main__': main()

