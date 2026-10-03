#!/usr/bin/env python3
"""Compile/run the actual generated AddAntLion body against V5 lion owners."""
from __future__ import annotations
import hashlib,json,re,subprocess
from pathlib import Path
from portable.whole_program.conversions.source_bounded_additive_v5 import ROOT,load_plan,render_owners,adapt

GEN=ROOT/'build/workers/whole_program/generated'
WORK=ROOT/'build/workers/whole_program/source_bounded_v5_consumer'
REPORT=ROOT/'portable/research/whole_program_source_bounded_consumer_v5.json'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def run(cmd):
 p=subprocess.run(cmd,cwd=ROOT,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
 if p.returncode: raise RuntimeError(f'command failed {cmd}\n{p.stdout}')
 return p.stdout
def endbrace(s,start):
 depth=0
 for i in range(start,len(s)):
  if s[i]=='{':depth+=1
  elif s[i]=='}':
   depth-=1
   if depth==0:return i+1
 raise ValueError('unmatched braces')
def main():
 if REPORT.exists(): raise SystemExit(f'refusing to overwrite {REPORT.relative_to(ROOT)}')
 plan=load_plan(); h,c=render_owners(plan)
 src=GEN/'root_m0AD9.c'
 if not src.exists(): raise SystemExit(f'missing generated source {src}')
 text,_=adapt(src.read_text(encoding='utf-8'),'src/root/m0AD9.c',plan)
 m=re.search(r'(?m)^void\s+AddAntLion\s*\(int16_t x,\s*int16_t y\)\s*\{',text)
 if not m: raise ValueError('source-generated AddAntLion body not found')
 body=text[m.start():endbrace(text,text.find('{',m.start()))]
 ring=re.search(r'(?m)^static\s+uint8_t\s+lionRing\[8\]\s*=\s*\{[^\n]+\};',text)
 if not ring: raise ValueError('source-generated private lionRing initializer not found')
 WORK.mkdir(parents=True,exist_ok=True)
 hp=WORK/'source_bounded_additive.h';cp=WORK/'source_bounded_additive.c';fp=WORK/'AddAntLion.c';tp=WORK/'probe.c'
 hp.write_text(h,encoding='utf-8',newline='\n');cp.write_text(c,encoding='utf-8',newline='\n')
 fp.write_text('''#include <stdint.h>\n#include "source_bounded_additive.h"\nextern int16_t LionIndex; extern int8_t Dx8[8],Dy8[8];\nextern int16_t IsClearTile(int16_t,int16_t,int16_t);\nextern void SetMap(int16_t,int16_t,int16_t,int16_t);\n'''+ring.group(0)+'\n'+body+'\n',encoding='utf-8',newline='\n')
 tp.write_text(r'''#include <stdint.h>
#include <stdio.h>
#include "source_bounded_additive.h"
void AddAntLion(int16_t,int16_t);
int16_t LionIndex=0; int8_t Dx8[8]={0,1,1,1,0,-1,-1,-1}; int8_t Dy8[8]={-1,-1,0,1,1,1,0,-1};
int16_t IsClearTile(int16_t p,int16_t x,int16_t y){(void)p;(void)x;(void)y;return 0;}
void SetMap(int16_t p,int16_t x,int16_t y,int16_t v){(void)p;(void)x;(void)y;(void)v;}
int main(void){
 AddAntLion(23,41);
 if(LionIndex!=1)return 1;
 if(native_state_LionListX.values[0]!=23||native_state_LionListY.values[0]!=41)return 2;
 if(native_state_LionListM.values[0]!=0||native_state_LionListS.values[0]!=0||native_state_LionListT.values[0]!=0)return 3;
 if(native_state_LionListX.values[9]!=0)return 4;
 puts("PASS: actual generated AddAntLion writes its six source-owned list fields through V5 native owner views");
 return 0;
}
'''.replace('\n+','\n'),encoding='utf-8',newline='\n')
 flags=['-std=c11','-fsigned-char','-fno-builtin','-fno-common','-Wall','-Wextra','-Werror','-ffunction-sections','-fdata-sections','-DSIMANT_NATIVE_LITTLE_ENDIAN=1','-I'+str(WORK)]
 objs=[]
 for path in (cp,fp,tp):
  obj=path.with_suffix('.o');run(['gcc',*flags,'-c',str(path),'-o',str(obj)]);objs.append(obj)
 exe=WORK/'probe.exe';run(['gcc',*[str(x) for x in objs],'-Wl,--gc-sections','-o',str(exe)])
 out=run([str(exe)]).strip()
 if 'PASS:' not in out:raise ValueError(out)
 pins={p.relative_to(ROOT).as_posix():sha(p) for p in [REPORT,src,hp,cp,fp,tp,*objs,exe] if p.exists()}
 report={'schema':'simant-source-bounded-native-consumer-v5','claim':'DIAGNOSTIC_ONLY: the actual current generated AddAntLion body writes V5 native lion-list views. This does not prove the DOS SaveGame wire format or full game behavior.','plan':{'path':'portable/research/whole_program_source_bounded_owners_v5.json','sha256':sha(ROOT/'portable/research/whole_program_source_bounded_owners_v5.json')},'inputs':pins,'controls':{'actual_add_ant_lion_body_extracted':True,'actual_five_v5_lion_views_mutated':True,'little_endian_target_macro_required':True,'compile_and_run':out},'limitations':['No SaveGame/LoadGame execution in this probe.','SetMap and IsClearTile are controlled to isolate AddAntLion writes; placement behavior is outside this state-access probe.','Only first list slot and one call are exercised.'],'summary':{'passed':True,'mutated_fields':['LionListX[0]','LionListY[0]','LionListM[0]','LionListS[0]','LionListT[0]']}}
 REPORT.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
 print(out);print(REPORT.relative_to(ROOT),sha(REPORT))
if __name__=='__main__':main()
