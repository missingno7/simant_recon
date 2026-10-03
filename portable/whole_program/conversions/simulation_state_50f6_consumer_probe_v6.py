#!/usr/bin/env python3
"""Compile actual generated point/history consumers against a diagnostic owner set."""
from __future__ import annotations
import hashlib,json,re,shutil,subprocess
from pathlib import Path
from portable.whole_program.conversions.simulation_state_50f6_preword import adapt_generated_consumer

ROOT=Path(__file__).resolve().parents[3]
GEN=ROOT/'build/workers/whole_program/generated'
PLAN=ROOT/'portable/research/whole_program_simulation_state_50f6_v6.json'
WORK=ROOT/'build/workers/whole_program/simulation_state_50f6_v6_consumer'
REPORT=ROOT/'portable/research/whole_program_simulation_state_50f6_consumer_v6.json'
TARGETS=[f'fd_50F6_{x}' for x in ['0508','0596','06A6','072E','07BC','07CA','0852','08DE','08EC','09F2','0A02','0A8A','0AA2','0AB2','0516','05A0','0626','06AE','073C','07CE','0856','08F0','0970','0A0A']]
def sha(b:bytes)->str:return hashlib.sha256(b).hexdigest()
def filepin(p:Path)->dict[str,str]:return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p.read_bytes())}
def run(args:list[str])->str:
    p=subprocess.run(args,cwd=ROOT,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    if p.returncode:raise RuntimeError(f'command failed ({p.returncode}): {args}\n{p.stdout}')
    return p.stdout.strip()
def function(text:str,name:str)->str:
    m=re.search(r'(?m)^\s*(?:void|int32_t)\s+'+re.escape(name)+r'\s*\([^;]*\)\s*\{',text)
    if not m:raise ValueError(f'function body not found: {name}')
    start=text.find('{',m.start());depth=0
    for i in range(start,len(text)):
        if text[i]=='{':depth+=1
        elif text[i]=='}':
            depth-=1
            if depth==0:return text[m.start():i+1]
    raise ValueError(f'unclosed function body: {name}')
def make_owner_files()->None:
    h=['#ifndef SIMULATION_STATE_50F6_V6_H','#define SIMULATION_STATE_50F6_V6_H','#include <stdint.h>']
    c=['#include "simulation_state_50f6.h"']
    point=set(TARGETS[:14])
    for n in TARGETS:
        if n in point:
            h.append(f'typedef union {{ struct {{ int16_t x, y; }} xy; struct {{ int16_t v, h; }} vh; int16_t words[2]; uint8_t raw_bytes[4]; }} SimState_{n};')
        else:
            h.append(f'typedef union {{ int16_t signed_values[64]; uint8_t raw_bytes[128]; }} SimState_{n};')
        h.append(f'extern SimState_{n} native_sim_state_{n};')
        c.append(f'SimState_{n} native_sim_state_{n};')
    h.append('#endif')
    (WORK/'simulation_state_50f6.h').write_text('\n'.join(h)+'\n',encoding='utf-8',newline='\n')
    (WORK/'simulation_state_50f6.c').write_text('\n'.join(c)+'\n',encoding='utf-8',newline='\n')
def main()->None:
    if REPORT.exists():raise SystemExit(f'refusing to overwrite immutable report {REPORT.relative_to(ROOT)}')
    if not PLAN.exists():raise SystemExit('source-bounded v6 plan missing; run its planner first')
    WORK.mkdir(parents=True,exist_ok=True);make_owner_files()
    gen_point=GEN/'root_m004A.c';gen_score=GEN/'S14_m384C.c';owner_h=GEN/'native_owners.h';owner_c=GEN/'native_owners.c'
    point_src=gen_point.read_text(encoding='utf-8');score_src=gen_score.read_text(encoding='utf-8')
    # Use the actual generated function bodies, not re-created model code.
    point_type=re.search(r'typedef struct\s*\{\s*int16_t\s+x;\s*int16_t\s+y;\s*\}\s*Point\s*;',point_src)
    if not point_type:raise ValueError('generated Point type view not found')
    point_body=function(point_src,'f_004A_02AD')
    point_map={f'fd_50F6_{x}':f'native_sim_state_fd_50F6_{x}.xy' for x in ['0508','0596','06A6','072E']}
    point_body,point_adapt=adapt_generated_consumer(point_body,point_map)
    score_body=function(score_src,'CalcScore')
    score_prefix=re.search(r'static char weights\[8\]\s*=\s*\{[^}]+\};',score_src)
    if not score_prefix:raise ValueError('generated CalcScore weights not found')
    score_map={f'fd_50F6_{x}':f'native_sim_state_fd_50F6_{x}.signed_values' for x in ['073C','0626','06AE']}
    score_body,score_adapt=adapt_generated_consumer(score_body,score_map)
    pfile=WORK/'point_consumer.c';sfile=WORK/'score_consumer.c'
    pfile.write_text('''#include <stdint.h>\n#include <stdio.h>\n#include "simulation_state_50f6.h"\n#include "native_owners.h"\ntypedef struct { int16_t x; int16_t y; } Point;\nextern int16_t fd_50F6_0FB6, fd_50F6_0FFA;\nstatic int update_calls, reset_calls;\nvoid UpdateEdit(void){++update_calls;}\nvoid f_0250_0ED2(void){++reset_calls;}\n'''+point_body+'''\nint16_t fd_50F6_0FB6, fd_50F6_0FFA;\nint main(void){\n    _Static_assert(sizeof(SimState_fd_50F6_0508)==4, "point extent");\n    _Static_assert(sizeof(SimState_fd_50F6_073C)==128, "history extent");\n    native_state_MapPlane.signed_value=2;\n    native_sim_state_fd_50F6_0508.xy.x=100; native_sim_state_fd_50F6_0508.xy.y=200;\n    fd_50F6_0FB6=20; fd_50F6_0FFA=40;\n    f_004A_02AD();\n    if(native_sim_state_fd_50F6_06A6.xy.x!=110 || native_sim_state_fd_50F6_06A6.xy.y!=220) return 31;\n    if(update_calls!=1 || reset_calls!=1) return 33;\n    native_sim_state_fd_50F6_08EC.vh.v=-3; native_sim_state_fd_50F6_08EC.vh.h=0x1234;\n    if(native_sim_state_fd_50F6_08EC.raw_bytes[0]!=0xFD || native_sim_state_fd_50F6_08EC.raw_bytes[1]!=0xFF || native_sim_state_fd_50F6_08EC.raw_bytes[2]!=0x34 || native_sim_state_fd_50F6_08EC.raw_bytes[3]!=0x12) return 32;\n    puts("PASS: generated map-center consumer mutates selected XY owner; point raw overlay matches little-endian words"); return 0;\n}\n''',encoding='utf-8',newline='\n')
    sfile.write_text('''#include <stdint.h>\n#include <stdio.h>\n#include "simulation_state_50f6.h"\n#include "native_owners.h"\nint16_t fd_3D57_0828=4;\nint16_t fd_50F6_0EAC=1;\nuint8_t fd_3D57_00A4[12][16];\n'''+score_prefix.group(0)+'\n'+score_body+'''\nint main(void){\n    int16_t scores[8]={0};\n    native_state_fd_50F6_04F4.signed_value=5;\n    native_state_fd_50F6_0C26.signed_value=5000;\n    native_state_MeHealth.signed_value=100;\n    for(int i=0;i<4;i++){int k=(1+i)&63; native_sim_state_fd_50F6_073C.signed_values[k]=(int16_t)(10*(i+1)); native_sim_state_fd_50F6_0626.signed_values[k]=(int16_t)(i+1); native_sim_state_fd_50F6_06AE.signed_values[k]=(int16_t)(2*(i+1));}\n    if(CalcScore(scores)<=0) return 41;\n    if(scores[0]!=25 || scores[1]!=33) return 42;\n    if(native_sim_state_fd_50F6_073C.raw_bytes[2]!=10 || native_sim_state_fd_50F6_073C.raw_bytes[3]!=0) return 43;\n    puts("PASS: generated CalcScore reads history owners across indexed samples; history raw overlay agrees"); return 0;\n}\n''',encoding='utf-8',newline='\n')
    cc=shutil.which('gcc')
    if not cc:raise RuntimeError('gcc not found on PATH')
    flags=['-std=c11','-fsigned-char','-fno-common','-Wall','-Wextra','-Werror','-Wno-unused-variable','-Wno-unused-parameter','-I'+str(WORK),'-I'+str(GEN),'-I'+str(ROOT)]
    point_exe=WORK/'point_consumer.exe';score_exe=WORK/'score_consumer.exe'
    point_cmd=[cc,*flags,str(pfile),str(WORK/'simulation_state_50f6.c'),str(owner_c),'-o',str(point_exe)]
    score_cmd=[cc,*flags,str(sfile),str(WORK/'simulation_state_50f6.c'),str(owner_c),'-o',str(score_exe)]
    point_compile=run(point_cmd);point_run=run([str(point_exe)])
    score_compile=run(score_cmd);score_run=run([str(score_exe)])
    pinned=[PLAN,gen_point,gen_score,owner_h,owner_c,ROOT/'portable/whole_program/conversions/simulation_state_50f6_preword.py',ROOT/'portable/whole_program/conversions/simulation_state_50f6_plan_v6.py',pfile,sfile,WORK/'simulation_state_50f6.h',WORK/'simulation_state_50f6.c']
    compiler=Path(cc).resolve()
    report={'schema':'simant-whole-program-simulation-state-consumer-v6','claim':'DIAGNOSTIC_ONLY: finite compile/run checks against actual generated consumer bodies and proposed state aliases; no DOS state/pixel equivalence claim.',
      'inputs':[filepin(p) for p in pinned],'compiler':{'path':str(compiler),'sha256':sha(compiler.read_bytes()),'version':run([cc,'--version']).splitlines()[0]},
      'commands':{'point':point_cmd,'score':score_cmd},'results':{'point':{'compile_output':point_compile,'run_output':point_run,'positive_controls':['generated f_004A_02AD writes the plane-2 centre from origin plus half edit dimensions','point object is four bytes','little-endian raw byte overlay corresponds to typed x/y and v/h views'],'negative_controls':['source field aliases are separate xy/vh members with two-word storage, so test rejects extent mismatch']},
      'history':{'compile_output':score_compile,'run_output':score_run,'positive_controls':['generated CalcScore reads all three history arrays using its original ring indices','chosen samples produce exact independently calculated scores[0]=25 and scores[1]=33','history object is 128 bytes and raw bytes match typed words'],'negative_controls':['zeroed/dummy history would not produce the expected 25 and 33']},
      'adapter_controls':{'point':point_adapt,'history':score_adapt}},
      'nonclaims':['The consumer bodies are generated native output, not execution of the DOS executable.','Serialized byte overlay is directly checked only for little-endian host layout.','This proof does not establish all uses, no runtime integration, and no rendering equivalence.']}
    if REPORT.exists():raise SystemExit(f'refusing to overwrite immutable report {REPORT.relative_to(ROOT)}')
    REPORT.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(point_run);print(score_run);print(f'WROTE {REPORT.relative_to(ROOT)}')
if __name__=='__main__':main()
