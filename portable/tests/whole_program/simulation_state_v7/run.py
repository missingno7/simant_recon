#!/usr/bin/env python3
"""Strict V7 source-bounded SaveRec and CountAnts probe."""
from __future__ import annotations
import hashlib,json,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT))
from portable.whole_program.conversions.source_bounded_simulation_state_v7 import load_plan,render_owners,adapt,_fixed,ROOT as SOURCE_ROOT
GEN=ROOT/'build/workers/whole_program/generated'
WORK=ROOT/'build/workers/whole_program/simulation_state_v7'
REPORT=ROOT/'portable/research/whole_program_simulation_state_50f6_v7_production_v2.json'
V1=ROOT/'portable/whole_program/conversions/source_bounded_access_probe.py'
PLAN_GEN=ROOT/'portable/whole_program/conversions/simulation_state_50f6_plan_v7.py'
ADAPTER=ROOT/'portable/whole_program/conversions/source_bounded_simulation_state_v7.py'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def run(cmd):
 p=subprocess.run(cmd,cwd=ROOT,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
 if p.returncode: raise RuntimeError(f'command failed {cmd}\n{p.stdout}')
 return p.stdout
def brace_end(s,i):
 d=0
 for j in range(i,len(s)):
  if s[j]=='{': d+=1
  elif s[j]=='}':
   d-=1
   if d==0:return j+1
 raise ValueError('unclosed body')
def patch_file_select(s):
 m=re.search(r'(?m)^int16_t\s+FileSelect\s*\([^;]*\)\s*\{',s)
 if not m: raise ValueError('FileSelect missing')
 i=s.find('{',m.start())
 return s[:i]+'{ (void)title; (void)verb; (void)save; strcpy(name,"bounded.v7"); return 1; }'+s[brace_end(s,i):]
def extract(s,ret,name):
 m=re.search(r'(?m)^'+ret+r'\s+'+re.escape(name)+r'\s*\([^;]*\)\s*\{',s)
 if not m: raise ValueError('consumer absent '+name)
 i=s.find('{',m.start())
 return s[:m.start()],s[m.start():brace_end(s,i)]
def main():
 if REPORT.exists(): raise SystemExit('refusing to overwrite '+str(REPORT))
 plan=load_plan(); header,owner_src=render_owners(plan)
 s09p=GEN/'S09_m35F5.c'; rootp=GEN/'root_m0BE8.c'; ownerp=GEN/'native_owners.c'; ownerh=GEN/'native_owners.h'
 for p in (s09p,rootp,ownerp,ownerh):
  if not p.is_file():raise SystemExit('missing generated input '+str(p))
 WORK.mkdir(parents=True,exist_ok=True)
 hp=WORK/'simulation_state_50f6_v7.h'; cp=WORK/'simulation_state_50f6_v7.c'
 hp.write_text(header,encoding='utf-8',newline='\n');cp.write_text(owner_src,encoding='utf-8',newline='\n')
 s09_input=s09p.read_text(encoding='utf-8')
 s09,meta1=(s09_input,{'already_centrally_adapted':True}) if '#include "simulation_state_50f6_v7.h"' in s09_input else adapt(s09_input,'src/S09/m35F5.c',plan)
 table=re.search(r'(?s)struct SaveRec\s+fd_4E4B_0000\[308\]\s*=\s*\{(.*?)\n\};',s09)
 if not table:raise ValueError('actual SaveRec table missing')
 names={t['symbol'] for t in plan['targets']}; rows={}; order=[]
 for line in table.group(1).splitlines():
  hit=next((n for n in names if re.search(r'&native_sim_state_'+re.escape(n)+r'\.(?:raw_bytes|unsigned_values)',line)),None)
  if hit: rows[hit]=line;order.append(hit)
 if set(rows)!=names or len(order)!=len(names):raise ValueError(f'exact V7 SaveRec rows mismatch {set(rows)^names}')
 s09=s09[:table.start(1)]+'\n'+'\n'.join(rows[n] for n in order)+'\n    { 0, 0, 0 },'+s09[table.end(1):]
 s09=patch_file_select(s09)
 sf=WORK/'S09_fixture.c';sf.write_text(s09,encoding='utf-8',newline='\n')
 # Actual generated CountAnts function after exact V7 source-view rewrites.
 root_input=rootp.read_text(encoding='utf-8')
 rt,meta2=(root_input,{'already_centrally_adapted':True}) if '#include "simulation_state_50f6_v7.h"' in root_input else adapt(root_input,'src/root/m0BE8.c',plan)
 prefix,fn=extract(rt,'void','CountAnts')
 cf=WORK/'CountAnts_consumer.c';cf.write_text(prefix+fn+'\n',encoding='utf-8',newline='\n')
 vals={
 'fd_50F6_0F46':[0x80+i for i in range(50)],'fd_50F6_0FC6':[0x90+i for i in range(50)],
 'fd_50F6_0F84':[0xA0+i for i in range(50)],'fd_50F6_1008':[0xB0+i for i in range(50)],
 'fd_50F6_0256':[0x10+i for i in range(100)],'fd_50F6_02C0':[0x30+i for i in range(100)],
 'fd_50F6_0334':[0x1101+i for i in range(12)],'fd_50F6_0AEC':[0x1201+i for i in range(6)],
 'fd_50F6_0AFA':[0x1301+i for i in range(6)],'fd_50F6_0B12':[0x1401+i for i in range(6)],
 'fd_50F6_0C2A':[0x1501+i for i in range(6)],'casteLevels':[0x1601,0x1602,0x1603],
 'modeLevels':[0x1701,0x1702,0x1703]}
 sizes={}
 expected=[]
 for n in order:
  m=re.search(r'\{\s*(\d+)\s*,\s*(\d+)\s*,',rows[n])
  size,count=map(int,m.groups());sizes[n]=size
  if count!=len(vals[n]):raise ValueError('fixture count mismatch '+n)
  for x in vals[n]:expected.extend([x&255] if size==1 else [x&255,(x>>8)&255])
 # Reuse reviewed V1 host I/O boundaries; replace the harness main only.
 old=V1.read_text(encoding='utf-8');m=re.search(r"harness\.write_text\(r'''(.*?)''',encoding='utf-8',newline='\\n'\)",old,re.S)
 if not m:raise ValueError('V1 harness template missing')
 harness=m.group(1).replace('#include "native_owners.h"','#include "native_owners.h"\n#include "simulation_state_50f6_v7.h"').replace('static uint8_t wire[8];','static uint8_t wire[2048];')
 harness=harness.replace('int16_t dos_errno=0;','int16_t dos_errno=0;\nchar *sim_sys_errlist[1]={"controlled I/O error"};')
 mm=re.search(r'int main\(void\)\s*\{',harness)
 if not mm:raise ValueError('V1 main missing')
 mend=brace_end(harness,harness.find('{',mm.start()))
 init=[];snap=[];mutate=[];checks=[]
 for t in plan['targets']:
  n=t['symbol']; v=vals[n]
  if n in ('casteLevels','modeLevels'):
   for i,field in enumerate(('frac','mid','weight')):init.append(f'native_sim_state_{n}.tri.{field}=0x{v[i]:04X};')
  else:
   member='signed_values' if n.startswith('fd_50F6_0F') or n in ('fd_50F6_0334','fd_50F6_0AEC','fd_50F6_0AFA','fd_50F6_0B12','fd_50F6_0C2A') else 'unsigned_values'
   for i,x in enumerate(v):init.append(f'native_sim_state_{n}.{member}[{i}]=0x{x:04X};')
  ext=t['extent_bytes']
  snap.append(f'uint8_t snap_{n}[{ext}]; memcpy(snap_{n},native_sim_state_{n}.raw_bytes,{ext});')
  mutate.append(f'memset(native_sim_state_{n}.raw_bytes,0xEE,{ext});')
  checks.append(f'if(memcmp(snap_{n},native_sim_state_{n}.raw_bytes,{ext}))return 40;')
 mainbody='int main(void){\n'+'\n'.join(' '+x for x in init+snap)+f'''
 if(o09_35F5_0188(1)!=1)return 10;
 {{const uint8_t expected[]={{ {','.join(f'0x{x:02X}' for x in expected)} }}; if(wire_len!=sizeof expected||memcmp(wire,expected,sizeof expected))return 11;}}
'''+ '\n'.join(' '+x for x in mutate)+'''
 if(LoadGame()!=1)return 12;
'''+ '\n'.join(' '+x for x in checks)+'''
 puts("PASS: actual generated S09 SaveGame/LoadGame round-trip 13 exact V7 rows"); return 0;
}
'''
 harness=harness[:mm.start()]+mainbody+harness[mend:]
 hf=WORK/'save_load_probe.c';hf.write_text(harness,encoding='utf-8',newline='\n')
 # Bounded CountAnts test: nonzero ant type inputs; hooks held outside this behavior.
 ch=WORK/'count_ants_probe.c'
 ch.write_text(r'''#include <stdint.h>
#include <stdio.h>
#include "native_owners.h"
#include "source_bounded_additive.h"
#include "simulation_state_50f6_v7.h"
uint8_t AlistT[500],BlistT[500],RlistT[500];
int16_t ListIndexA=0,ListIndexB=0,ListIndexR=0;
int16_t fd_50F6_0354=0,fd_50F6_04C2=0,fd_50F6_0A06=1,fd_50F6_0EAC=0,fd_50F6_0EB6[32];
int16_t BpopT=0,RpopT=0; uint8_t fd_3D57_0184[16][16];
void myBeginSong(int16_t a,int16_t b){(void)a;(void)b;}
void o14_384C_0B6A(int16_t a,int16_t b,int16_t c){(void)a;(void)b;(void)c;}
void PictStrnDialog(int16_t a,int16_t b,int16_t c){(void)a;(void)b;(void)c;}
int16_t SRand1(int16_t n){(void)n;return 0;}
void CountAnts(void);
int main(void){
 ListIndexA=12; AlistT[0]=8; AlistT[1]=16; AlistT[2]=32; AlistT[3]=40;
 AlistT[4]=64; AlistT[5]=72; AlistT[6]=80; AlistT[7]=128; AlistT[8]=144;
 AlistT[9]=152; AlistT[10]=168; AlistT[11]=136;
 ListIndexB=3; BlistT[0]=184; BlistT[1]=176; BlistT[2]=200;
 ListIndexR=3; RlistT[0]=160; RlistT[1]=192; RlistT[2]=224;
 native_state_ListIndexB.signed_value=3; native_state_ListIndexR.signed_value=3;
 native_sim_state_fd_50F6_0AEC.signed_values[5]=0;
 native_sim_state_fd_50F6_0AFA.signed_values[5]=0;
 CountAnts();
 if(native_sim_state_fd_50F6_0AEC.signed_values[0]!=0)return 21;
 if(native_sim_state_fd_50F6_0AEC.signed_values[1]!=3)return 22;
 if(native_sim_state_fd_50F6_0AEC.signed_values[2]!=1)return 23;
 if(native_sim_state_fd_50F6_0AEC.signed_values[3]!=1)return 24;
 if(native_sim_state_fd_50F6_0AEC.signed_values[4]!=1)return 25;
 if(native_sim_state_fd_50F6_0AEC.signed_values[5]!=0)return 26;
 if(native_sim_state_fd_50F6_0AFA.signed_values[0]!=1||native_sim_state_fd_50F6_0AFA.signed_values[1]!=4||native_sim_state_fd_50F6_0AFA.signed_values[2]!=3||native_sim_state_fd_50F6_0AFA.signed_values[3]!=1||native_sim_state_fd_50F6_0AFA.signed_values[4]!=1||native_sim_state_fd_50F6_0AFA.signed_values[5]!=1)return 27;
 if(native_state_BpopT.signed_value!=6||native_state_RpopT.signed_value!=10)return 28;
 puts("PASS: actual generated CountAnts aggregates explicit nonzero source ant types");return 0;
}
''',encoding='utf-8',newline='\n')
 gcc=Path(r'C:\msys64\mingw64\bin\gcc.exe'); version=run([str(gcc),'--version']).splitlines()[0]
 flags=['-std=c11','-fsigned-char','-fno-builtin','-fno-common','-Wall','-Wextra','-Werror','-Wno-builtin-declaration-mismatch','-Wno-sequence-point','-Wno-address','-Wno-unused-variable','-ffunction-sections','-fdata-sections','-DSIMANT_NATIVE_LITTLE_ENDIAN=1','-I'+str(WORK),'-I'+str(GEN),'-I'+str(ROOT)]
 save_objs=[]
 addp=GEN/'source_bounded_additive.c'
 for src in (sf,ownerp,addp,cp,hf):
  obj=WORK/(src.stem+'_save.o');run([str(gcc),*flags,'-c',str(src),'-o',str(obj)]);save_objs.append(obj)
 saveexe=WORK/'save_load_probe.exe';run([str(gcc),*[str(o) for o in save_objs],'-Wl,--gc-sections','-o',str(saveexe)])
 saveout=run([str(saveexe)]).strip()
 count_objs=[]
 v6p=GEN/'simulation_state_50f6.c'
 for src in (cf,ownerp,addp,v6p,cp,ch):
  obj=WORK/(src.stem+'_count.o');run([str(gcc),*flags,'-c',str(src),'-o',str(obj)]);count_objs.append(obj)
 countexe=WORK/'count_ants_probe.exe';run([str(gcc),*[str(o) for o in count_objs],'-Wl,--gc-sections','-o',str(countexe)])
 countout=run([str(countexe)]).strip()
 if not saveout.startswith('PASS:') or not countout.startswith('PASS:'):raise ValueError(saveout+' / '+countout)
 neg={}
 try:_fixed(SOURCE_ROOT/'src/root/m0BE8.c','0'*64,'negative control');neg['wrong_original_source_hash_rejected']=False
 except ValueError:neg['wrong_original_source_hash_rejected']=True
 try:adapt(rootp.read_text(encoding='utf-8'),'src/root/m0BE8.c',{**plan,'targets':[]});neg['caller_plan_mutation_rejected']=False
 except ValueError:neg['caller_plan_mutation_rejected']=True
 if not all(neg.values()):raise ValueError('strict negative controls failed '+str(neg))
 pins=[PLAN_GEN,ADAPTER,V1,s09p,rootp,ownerp,ownerh,addp,v6p,hp,cp,sf,cf,hf,ch,*save_objs,*count_objs,saveexe,countexe]
 report={'schema':'simant-source-bounded-simulation-state-v7-test','claim':'DIAGNOSTIC_ONLY: fixed V7 converter owns 13 source-declared SaveRec-backed simulation arrays/triples; actual generated selected-row SaveGame/LoadGame and actual generated CountAnts pass controlled fixtures.','plan':{'path':'portable/research/whole_program_simulation_state_50f6_v7.json','sha256':sha(ROOT/'portable/research/whole_program_simulation_state_50f6_v7.json')},'inputs':{p.relative_to(ROOT).as_posix():sha(p) for p in pins},'source_hash_closure':plan['source_hashes'],'compiler':{'path':str(gcc),'version':version,'sha256':sha(gcc)},'selected_save_rec_order':order,'selected_actual_rows':{n:rows[n].strip() for n in order},'expected_serialized_bytes':len(expected),'positive':{'13_exact_rows_present_once':True,'actual_savegame_expected_bytes':True,'actual_loadgame_restores_all_13_extents':True,'actual_countants_nonzero_counts':True,'wrong_original_source_hash_rejected':neg['wrong_original_source_hash_rejected'],'caller_plan_mutation_rejected':neg['caller_plan_mutation_rejected']},'controlled_boundaries':['Only the 13 real rows and original zero terminator are kept in scratch S09 copy.','FileSelect and DOS file operations use pinned V1 harness controls.','Existing LoadGame post-load services are controlled stubs.','CountAnts uses explicit nonzero type vectors and controlled callbacks.'],'limitations':['Diagnostic evidence only; not centrally selected or full game acceptance.','Not full 307-row save compatibility.','Little-endian serialization path only.','No preset-data, rendering, UI or pixel claim.'],'outputs':{'save_load':saveout,'countants':countout},'summary':{'owners':len(plan['targets']),'records':len(order),'serialized_bytes':len(expected),'passed':True}}
 REPORT.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
 print(saveout);print(countout);print(REPORT.relative_to(ROOT),sha(REPORT))
if __name__=='__main__':main()

