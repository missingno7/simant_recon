#!/usr/bin/env python3
"""Run actual generated S09 SaveGame on the 13 V5 rows in a bounded fixture."""
from __future__ import annotations
import ast,hashlib,json,re,subprocess
from pathlib import Path
from portable.whole_program.conversions.source_bounded_additive_v5 import ROOT,load_plan,render_owners,adapt

GEN=ROOT/'build/workers/whole_program/generated'
V1=ROOT/'portable/whole_program/conversions/source_bounded_access_probe.py'
WORK=ROOT/'build/workers/whole_program/source_bounded_v5_save'
REPORT=ROOT/'portable/research/whole_program_source_bounded_save_v5.json'
WANTED=['Cycle','ListIndexB','ListIndexR','LionListM','LionListS','LionListT','LionListX','LionListY','SowX','SowY','SowDir','SowSave','PillarMap']
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def run(cmd):
 p=subprocess.run(cmd,cwd=ROOT,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
 if p.returncode:raise RuntimeError(f'command failed {cmd}\n{p.stdout}')
 return p.stdout
def brace_end(text,start):
 depth=0
 for i in range(start,len(text)):
  if text[i]=='{':depth+=1
  elif text[i]=='}':
   depth-=1
   if depth==0:return i+1
 raise ValueError('unmatched braces')
def patch_file_select(text):
 m=re.search(r'(?m)^int16_t\s+FileSelect\s*\([^;]*\)\s*\{',text)
 if not m: raise ValueError('FileSelect boundary not found')
 i=text.find('{',m.start());end=brace_end(text,i)
 body='''{\n    (void)title; (void)verb; (void)save;\n    strcpy(name, "bounded.v5");\n    return 1;\n}'''
 return text[:i]+body+text[end:]
def main():
 if REPORT.exists():raise SystemExit(f'refusing to overwrite {REPORT.relative_to(ROOT)}')
 plan=load_plan(); h,c=render_owners(plan)
 src=GEN/'S09_m35F5.c';v3c=GEN/'native_owners.c';v3h=GEN/'native_owners.h'
 text=src.read_text(encoding='utf-8');text,_=adapt(text,'src/S09/m35F5.c',plan)
 table=re.search(r'(?s)struct SaveRec\s+fd_4E4B_0000\[308\]\s*=\s*\{(.*?)\n\};',text)
 if not table:raise ValueError('generated SaveRec table not found')
 lines=table.group(1).splitlines(); selected=[];row_names=[]
 for line in lines:
  for name in WANTED:
   if re.search(r'&native_state_'+re.escape(name)+r'\.',line):
    selected.append(line);row_names.append(name);break
 if sorted(row_names)!=sorted(WANTED) or len(row_names)!=len(WANTED):raise ValueError(f'expected exactly all V5 rows: {row_names}')
 text=text[:table.start(1)]+'\n'+'\n'.join(selected)+'\n    { 0, 0, 0 },'+text[table.end(1):]
 text=patch_file_select(text)
 WORK.mkdir(parents=True,exist_ok=True)
 fixture=WORK/'S09_fixture.c';fixture.write_text(text,encoding='utf-8',newline='\n')
 addh=WORK/'source_bounded_additive.h';addc=WORK/'source_bounded_additive.c'
 addh.write_text(h,encoding='utf-8',newline='\n');addc.write_text(c,encoding='utf-8',newline='\n')
 # Reuse the pinned V1 controlled DOS-file host harness, replacing only its
 # test main and extending its bounded byte buffer. It keeps the actual DOS
 # SaveGame body and callback ABI stubs already reviewed in V1.
 old=V1.read_text(encoding='utf-8')
 match=re.search(r"harness\.write_text\(r'''(.*?)''',encoding='utf-8',newline='\\n'\)",old,re.S)
 if not match:raise ValueError('V1 pinned harness template not found')
 harness=match.group(1).replace('#include "native_owners.h"','#include "native_owners.h"\n#include "source_bounded_additive.h"')
 harness=harness.replace('static uint8_t wire[8];','static uint8_t wire[256];')
 mainmatch=re.search(r'int main\(void\)\s*\{',harness)
 if not mainmatch:raise ValueError('V1 harness main not found')
 mainend=brace_end(harness,harness.find('{',mainmatch.start()))
 # Deterministic independent typed sentinels, with the expected wire generated
 # from source SaveRec row order rather than from the codec's traversal.
 vals={'Cycle':0x1234,'ListIndexB':0x2233,'ListIndexR':0x4455}
 arrays={
  'LionListM':list(range(0x10,0x1a)),'LionListS':list(range(0x20,0x2a)),
  'LionListT':list(range(0x30,0x3a)),'LionListX':list(range(0x40,0x4a)),
  'LionListY':list(range(0x50,0x5a)),
  'SowX':[0x1001,0x1002,0x1003],'SowY':[0x2001,0x2002,0x2003],
  'SowDir':[0x3001,0x3002,0x3003],'SowSave':[0x4001,0x4002,0x4003],
  'PillarMap':[0x5001,0x5002,0x5003,0x5004,0x5005,0x5006]}
 expected=[]
 for name in row_names:
  seq=[vals[name]] if name in vals else arrays[name]
  for value in seq:
   expected.extend([value&255,(value>>8)&255] if name in vals or name.startswith(('Sow','Pillar')) else [value])
 expected_literal=','.join(f'0x{x:02X}' for x in expected)
 init='\n'.join([f'    native_state_{name}.signed_value=0x{value:04X};' for name,value in vals.items()]+[
  f'    for(int i=0;i<10;i++) native_state_{name}.values[i]=(uint8_t)(0x{seq[0]:02X}+i);' for name,seq in arrays.items() if name.startswith('LionList')]+[
  f'    for(int i=0;i<{len(seq)};i++) native_state_{name}.signed_values[i]=(int16_t)0x{value:04X};' for name,seq in arrays.items() if not name.startswith('LionList') for i,value in []])
 # Expand numeric array initializers without deriving expectations from actual output.
 lines_init=[]
 for name,value in vals.items():lines_init.append(f'    native_state_{name}.signed_value=(int16_t)0x{value:04X};')
 for name,seq in arrays.items():
  for i,value in enumerate(seq):
   member='values' if name.startswith('LionList') else 'signed_values'
   ctype='uint8_t' if member=='values' else 'int16_t'
   lines_init.append(f'    native_state_{name}.{member}[{i}]=({ctype})0x{value:04X};')
 newmain='''int main(void){\n'''+ '\n'.join(lines_init)+f'''
    if(native_state_Cycle.raw_bytes[0]!=0x34||native_state_Cycle.raw_bytes[1]!=0x12)return 20;
    if(o09_35F5_0188(1)!=1)return 21;
    {{const uint8_t expected[]={{{expected_literal}}};
     if(wire_len!=sizeof expected||memcmp(wire,expected,sizeof expected)!=0)return 22;}}
    puts("PASS: actual generated S09 SaveGame writes all 13 V5 SaveRec rows in DOS little-endian order; Cycle raw byte alias agrees");
    return 0;
}}
'''
 harness=harness[:mainmatch.start()]+newmain+harness[mainend:]
 harnessfile=WORK/'probe.c';harnessfile.write_text(harness,encoding='utf-8',newline='\n')
 flags=['-std=c11','-fsigned-char','-fno-builtin','-fno-common','-Wall','-Wextra','-Werror','-Wno-builtin-declaration-mismatch','-Wno-sequence-point','-Wno-address','-Wno-unused-variable','-ffunction-sections','-fdata-sections','-DSIMANT_NATIVE_LITTLE_ENDIAN=1','-I'+str(WORK),'-I'+str(GEN),'-I'+str(ROOT)]
 objects=[]
 for path in (fixture,addc,GEN/'native_owners.c',harnessfile):
  obj=WORK/(path.stem+'.o');run(['gcc',*flags,'-c',str(path),'-o',str(obj)]);objects.append(obj)
 exe=WORK/'probe.exe';run(['gcc',*[str(o) for o in objects],'-Wl,--gc-sections','-o',str(exe)])
 output=run([str(exe)]).strip()
 if not output.startswith('PASS:'):raise ValueError(output)
 inputs={p.relative_to(ROOT).as_posix():sha(p) for p in [V1,src,v3c,v3h,fixture,addh,addc,harnessfile,*objects,exe]}
 report={'schema':'simant-source-bounded-save-v5','claim':'DIAGNOSTIC_ONLY: actual current generated S09 SaveGame body serializes 13 V5 source-bounded records into a controlled byte stream; not a full SaveGame/LoadGame or production codec claim.','plan':{'path':'portable/research/whole_program_source_bounded_owners_v5.json','sha256':sha(ROOT/'portable/research/whole_program_source_bounded_owners_v5.json')},'inputs':inputs,'rows_in_source_order':row_names,'expected_bytes':expected,'controlled_boundaries':['V1 pinned harness callback stubs','DOS byte stream is in-memory','S09 table reduced in scratch copy to the 13 exact original rows plus zero terminator','little-endian target is compile-time required'],'positive':{'actual_savegame_body_executed':True,'all_13_v5_rows_written_exactly':True,'typed_array_and_scalar_values_match_independent_expected_bytes':True,'cycle_source_byte_alias_matches_low_word_byte':True},'limitations':['No LoadGame/round-trip, only actual SaveGame write path.','The expected output uses controlled sentinels and does not prove broad game-state correctness.','Cycle byte alias is restricted to little-endian native targets.'],'output':output,'summary':{'records':len(row_names),'bytes':len(expected),'passed':True}}
 REPORT.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
 print(output);print(REPORT.relative_to(ROOT),sha(REPORT))
if __name__=='__main__':main()
