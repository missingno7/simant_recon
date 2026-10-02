#!/usr/bin/env python3
"""Controlled original-DOS versus native next5 NewGame flow probe."""
from __future__ import annotations
import ctypes as ct, gzip, hashlib, json, sys
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'tools'))
import behavior, exe, functions
PROFILE=ROOT/'build/workers/recovered_source_next5/generated'
OUT=ROOT/'build/workers/behavior_newgame_next5/flow'
LIB=ROOT/'build/workers/behavior_newgame_next5/native.dll'
FIELDS=['MapPlane','MePlane','MeLocX','MeLocY','fd_50F6_0EAC','fd_50F6_105E','fd_50F6_0354','fd_50F6_07C8','fd_3D57_07A4','fd_3D57_07A6','fd_3D57_02C2']
IDS={n:i for i,n in enumerate(FIELDS)}
EVENTS={i:n for i,n in enumerate(['','OpenCasteWindow','OpenModeWindow','SetEditWinTitle','f_015B_053C','win_IsWinOpen','YardToMap','SetMapTitle','OpenEditWindow','DoScenario','o09_35F5_0000','EndLifeTransferMode','EndTargetMode','SetDefaultWindPrompt','RandYard','WinPrintf','win_Open','f_22BF_0A65','o26_39C7_0000','CenterEdit','UpdateEdit'])}
sha=lambda b:hashlib.sha256(b).hexdigest()
canon=lambda v:json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode('utf-8')

def build():
 import shutil,subprocess
 compiler=shutil.which('gcc') or 'C:/msys64/mingw64/bin/gcc.exe'; OUT.mkdir(parents=True,exist_ok=True)
 cmd=[compiler,'-std=c11','-O0','-Wall','-Wextra','-Werror','-shared','-I',str(PROFILE),str(ROOT/'portable/tests/recovered/newgame_flow_probe.c'),str(PROFILE/'recovered_state.c'),str(PROFILE/'root_m384C_newgame.c'),'-o',str(LIB)]
 subprocess.run(cmd,cwd=ROOT,check=True); lib=ct.CDLL(str(LIB))
 lib.newgame_flow_state_create.restype=ct.c_void_p; lib.newgame_flow_state_destroy.argtypes=[ct.c_void_p]
 lib.newgame_flow_state_set.argtypes=[ct.c_void_p,ct.c_uint,ct.c_int16]; lib.newgame_flow_state_get.argtypes=[ct.c_void_p,ct.c_uint]; lib.newgame_flow_state_get.restype=ct.c_int16
 lib.newgame_flow_configure.argtypes=[ct.POINTER(ct.c_int16),ct.c_uint,ct.POINTER(ct.c_int16),ct.c_uint,ct.c_int16,ct.c_int16,ct.c_int16,ct.c_int16,ct.c_int16,ct.c_int16,ct.c_int16]
 lib.newgame_flow_run.argtypes=[ct.c_void_p,ct.c_int]; lib.newgame_flow_run.restype=ct.c_int; lib.newgame_flow_setdefault.argtypes=[ct.c_void_p]
 lib.newgame_flow_event_count.restype=ct.c_uint; lib.newgame_flow_events.argtypes=[ct.POINTER(ct.c_int16)]
 return lib,cmd

def spec(sc,files=(),flag=0,mode=0,opened=1,confirm=1,start=(2,17,29),yard=(3,41,23)):
 return dict(scenarios=list(sc),files=list(files),flag=flag,mode=mode,opened=opened,confirm=confirm,start=start,yard=yard)

def initial(s): return dict(zip(FIELDS,[s['start'][0],s['start'][0],s['start'][1],s['start'][2],0,s['mode'],0,0,0,0,0x3456]))

def dos(s,name):
 calls=[]; si={'v':0}; fi={'v':0}; callbacks={}
 def reg(n,stack=0,regs=(),value=None):
  def h(m,a): calls.append([n,list(a)]); return value
  callbacks[n]=behavior.Callback(stack,h,regs)
 def scenario(m,a):
  i=si['v'];si['v']+=1;v=s['scenarios'][min(i,len(s['scenarios'])-1)];calls.append(['DoScenario',list(a),v]);return v
 def file(m,a):
  i=fi['v'];fi['v']+=1;v=s['files'][min(i,len(s['files'])-1)];calls.append(['o09_35F5_0000',list(a),v]);return v
 def yard(m,a):
  calls.append(['RandYard',list(a)])
  for n,v in zip(('MePlane','MeLocX','MeLocY'),s['yard']):m.write(behavior.symbol_address(n),behavior.words(v))
 callbacks['DoScenario']=behavior.Callback(1,scenario);callbacks['o09_35F5_0000']=behavior.Callback(2,file)
 for n,st,rg,val in [('OpenCasteWindow',0,(),None),('OpenModeWindow',0,(),None),('SetEditWinTitle',2,(),None),('f_015B_053C',1,(),None),('win_IsWinOpen',0,('ax',),s['opened']),('YardToMap',0,(),None),('SetMapTitle',0,(),None),('OpenEditWindow',0,(),None),('EndLifeTransferMode',0,(),None),('EndTargetMode',0,(),None),('SetDefaultWindPrompt',1,(),None),('win_Open',1,(),1),('f_22BF_0A65',0,('ax',),s['confirm']),('o26_39C7_0000',0,('ax',),None),('CenterEdit',2,(),None),('UpdateEdit',0,(),None)]:reg(n,st,rg,val)
 def fmt_project(m,a):
  off,seg=a[:2]; data=m.read((seg<<4)+off,64).split(b'\0',1)[0]
  return [data.decode('latin1'),a[2]]
 def winprintf(m,a): calls.append(['WinPrintf',fmt_project(m,a)]); return 0
 callbacks['WinPrintf']=behavior.Callback(3,winprintf,project=fmt_project)
 callbacks['RandYard']=behavior.Callback(0,yard)
 def zoom_query(m,a): calls.append(['f_22BF_0A65',list(a),s['confirm']]); return s['confirm']
 callbacks['f_22BF_0A65']=behavior.Callback(0,zoom_query,('ax',))
 def zoom(m,a): calls.append(['o26_39C7_0000',list(a)])
 callbacks['o26_39C7_0000']=behavior.Callback(0,zoom,('ax',))
 pair=SimpleNamespace(function=functions.get(name),vectors={exe.MANAGER_SEG*16+v.offset:v for v in exe.load().vectors},candidate=False,sequence_targets=set(),sequence_function=lambda n:functions.get(n))
 machine=behavior.Machine(pair); writes=[(behavior.symbol_address(n),behavior.words(v)) for n,v in initial(s).items()]
 writes += [(behavior.symbol_address('g_8BA2'),behavior.words(0x6A31)),
            (behavior.match.DGROUP_SEG*16+0x7BBE,bytes.fromhex('78563412'))]
 args=[] if name=='SetDefaultWindows' else [s['flag']]
 case=behavior.Case(label='flow',args=args,writes=writes,callbacks=callbacks,observe=[behavior.Range(n,behavior.symbol_address(n),2) for n in FIELDS],return_kind='s16',max_instructions=4000000,max_blocks=200000)
 result=machine.run(case,function=name); fields={n:machine.read(behavior.symbol_address(n),2).hex() for n in FIELDS}
 rng={'s':machine.read(behavior.symbol_address('g_8BA2'),2).hex(),
      'c':machine.read(behavior.match.DGROUP_SEG*16+0x7BBE,4).hex()}
 return dict(rv=result['return'],fields=fields,calls=calls,rng=rng,trace=result['trace'],raw_trace=result['raw_trace'],case=case)

def native(lib,s,name,entry_ax=(0,0)):
 state=lib.newgame_flow_state_create(); sc=(ct.c_int16*max(1,len(s['scenarios'])))(*(s['scenarios'] or [0x202])); fs=(ct.c_int16*max(1,len(s['files'])))(*(s['files'] or [1]))
 lib.newgame_flow_configure(sc,len(s['scenarios']),fs,len(s['files']),s['opened'],s['confirm'],*s['yard'],*entry_ax)
 for n,v in initial(s).items():lib.newgame_flow_state_set(state,IDS[n],v)
 rv=lib.newgame_flow_setdefault(state) if name=='SetDefaultWindows' else lib.newgame_flow_run(state,s['flag'])
 fields={n:int(lib.newgame_flow_state_get(state,IDS[n])) for n in FIELDS}; count=lib.newgame_flow_event_count();raw=(ct.c_int16*(count*14))();lib.newgame_flow_events(raw)
 calls=[]; entry_states=[]
 for i in range(count):
  row=list(map(int,raw[i*14:i*14+14]));ident,a,b=row[:3];name=EVENTS[ident]
  entry_states.append(row[3:])
  if ident==9: calls.append([name,[a],b])
  elif ident==10: calls.append([name,[a,0],b])
  elif ident==3: calls.append([name,[0,0]])
  elif ident==15: calls.append([name,['MePLane=%d',b]])
  elif ident in (4,5,13,16): calls.append([name,[a]])
  elif ident==17: calls.append([name,[a],b])
  elif ident==18: calls.append([name,[a]])
  elif ident==19: calls.append([name,[a,b]])
  else: calls.append([name,[]])
 lib.newgame_flow_state_destroy(state);return dict(rv=rv,fields=fields,calls=calls,entry_states=entry_states)

def compare(lib,s,name):
 a=dos(s,name)
 entry_values={"f_22BF_0A65":0,"o26_39C7_0000":0}
 for call in a['calls']:
  if call[0] in entry_values: entry_values[call[0]]=call[1][0]
 b=native(lib,s,name,(entry_values['f_22BF_0A65'],entry_values['o26_39C7_0000']))
 expected={k:int.from_bytes(bytes.fromhex(v),'little',signed=True) for k,v in a['fields'].items()};diff={}
 if name=='NewGame' and a['rv']!=b['rv']:diff['return']=[a['rv'],b['rv']]
 if a['calls']!=b['calls']:diff['calls']=[a['calls'],b['calls']]
 dos_entries=[]
 for item in a['trace']:
  dos_entries.append([int.from_bytes(bytes.fromhex(item['state_at_entry'][n]),'little',signed=True) for n in FIELDS])
 if dos_entries!=b['entry_states']:diff['callback_entry_state_order']=[dos_entries,b['entry_states']]
 if expected!=b['fields']:diff['fields']={k:[expected[k],b['fields'][k]] for k in FIELDS if expected[k]!=b['fields'][k]}
 if a['rng']!={'s':'316a','c':'78563412'}:diff['rng_changed']={"initial":{"s":"316a","c":"78563412"},"final":a['rng']}
 return dict(equal=not diff,diff=diff,dos=a,native=b)

def main():
 lib,cmd=build();cases=[spec([x],flag=f,mode=m,opened=o,confirm=c) for x in (0x202,0x203,0x204,0x206,0x205) for f in (0,1) for m in (0,10,11) for o in (0,1) for c in (0,1)]
 cases += [spec([0x207,0x202],[0,1],flag=f,mode=m) for f in (0,1) for m in (0,10,11)]+[spec([0x207],[1],flag=f) for f in (0,1)]
 results=[]
 for i,s in enumerate(cases):
  r=compare(lib,s,'NewGame');r['id']=f'newgame-{i:03}';r['input']=s;results.append(r)
  if not r['equal']:break
 direct=[]
 for o in (0,1):
  s=spec([0x202],opened=o);r=compare(lib,s,'SetDefaultWindows');r['id']=f'setdefault-{o}';r['input']=s;direct.append(r)
 allok=all(x['equal'] for x in results+direct);profile=json.loads((PROFILE/'provenance.json').read_text());selected=next(x for x in profile['modules'] if x['name']=='root_m384C_newgame')
 rows=[]
 for r in results+direct:
  original={'return':r['dos']['rv'],'fields':r['dos']['fields'],'calls':r['dos']['calls'],'callback_entry_states':[[int.from_bytes(bytes.fromhex(item['state_at_entry'][n]),'little',signed=True) for n in FIELDS] for item in r['dos']['trace']],'rng':r['dos']['rng']}
  candidate={'return':r['native']['rv'],'fields':r['native']['fields'],'calls':r['native']['calls'],'callback_entry_states':r['native']['entry_states']}
  rows.append({'case_id':r['id'],'lane':'directed','input':r['input'],'equal':r['equal'],'diff':r['diff'],
      'original_observation_sha256':sha(canon(original)),'candidate_observation_sha256':sha(canon(candidate)),
      'original':original,'native':candidate})
 ledger_raw=b''.join(canon(row)+b'\n' for row in rows)
 ledger_path=OUT/'cases.jsonl.gz';ledger_path.write_bytes(gzip.compress(ledger_raw,mtime=0))
 report={'schema':'portable-next5-newgame-controlled-dos-differential-v1','status':'DIAGNOSTIC_ONLY_NOT_BEHAVIOR_ACCEPTANCE','oracle_sha256':behavior.exe.load().sha256,'harness_sha256':sha(behavior.HARNESS_SOURCE),'source':{'path':'src/S15/m384C.c','sha256':sha((ROOT/'src/S15/m384C.c').read_bytes())},'next5':{'wrapper':'portable/tools/recover_source_next5.py','wrapper_sha256':sha((ROOT/'portable/tools/recover_source_next5.py').read_bytes()),'profile_provenance_sha256':sha((PROFILE/'provenance.json').read_bytes()),'selected_source_sha256':sha((PROFILE/'root_m384C_newgame.c').read_bytes()),'state_header_sha256':sha((PROFILE/'recovered_state.h').read_bytes()),'state_source_sha256':sha((PROFILE/'recovered_state.c').read_bytes()),'native_probe_sha256':sha((ROOT/'portable/tests/recovered/newgame_flow_probe.c').read_bytes()),'native_library_sha256':sha(LIB.read_bytes()),'selected_source_provenance':selected},'ledger':{'schema':'portable-next5-newgame-flow-ledger-v1','path':ledger_path.relative_to(ROOT).as_posix(),'sha256':sha(ledger_path.read_bytes()),'row_count':len(rows),'lane_counts':{'directed':len(rows)}},'domain':{'newgame_cases':len(results),'direct_setdefault_cases':len(direct),'scenario_ids':[0x202,0x203,0x204,0x206,0x205,0x207],'modes':[0,10,11],'flags':[0,1],'file_207':['retry then success','success'],'randyard_boundary':{'mutates':['MePlane','MeLocX','MeLocY'],'rng':'original S/C RNG sentinels checked unchanged; no service consumes RNG','whole_randyard_claim':False},'implicit_ax':{'helpers':['f_22BF_0A65','o26_39C7_0000'],'native_service_input_records_replay_actual_original_entry_AX':True}},'compared':['return','ordered typed service calls and LoadGame outcomes','11 named S15 fields','S15 field values at every controlled callback entry','original RNG sentinel preservation'],'boundary':'Oracle runs NewGame/SetDefaultWindows from DOS; native runs selected next5 C. Modal selection, windows, LoadGame, RandYard, and window/UI calls are controlled typed services. The native boundary trace replays the entry AX captured by the original VM for f_22BF_0A65/o26_39C7_0000; those volatile register values are not claimed as independently generated by native C. Controlled RandYard writes only MePlane/MeLocX/MeLocY sentinels; this checks post-call flow, not RandWorld semantics.','newgame_results':[{'id':x['id'],'equal':x['equal'],'diff':x['diff']} for x in results],'setdefault_results':[{'id':x['id'],'equal':x['equal'],'diff':x['diff']} for x in direct],'native_build_command':cmd,'all_equal':allok}
 OUT.mkdir(parents=True,exist_ok=True);p=OUT/'report.json';p.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps({'report':str(p),'newgame':len(results),'setdefault':len(direct),'all_equal':allok,'sha256':sha(p.read_bytes())},indent=2))
 if not allok:raise SystemExit(1)
if __name__=='__main__':main()
