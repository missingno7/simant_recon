#!/usr/bin/env python3
"""Focused integration probe for V3 SaveRec union access and one source consumer.

Uses the current generated S09 SaveGame/LoadGame bodies and the actual generated
root:m004A MapPlane consumer. The source copy keeps only two real SaveRec rows;
modal file selection, low-level file calls, RandYard, post-load UI/game services
are explicit controlled boundaries. This is not full Save/Load or game acceptance.
"""
from __future__ import annotations
import hashlib,json,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
PLAN=ROOT/'portable/research/whole_program_source_bounded_owners_v3.json'
GEN=ROOT/'build/workers/whole_program/generated'
WORK=ROOT/'build/workers/whole_program/source_bounded_access_v1'
REPORT=ROOT/'portable/research/whole_program_source_bounded_access_v1.json'

def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def run(cmd:list[str],cwd:Path=ROOT)->str:
 p=subprocess.run(cmd,cwd=cwd,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
 if p.returncode:raise RuntimeError(f'command failed ({p.returncode}): {cmd}\n{p.stdout}')
 return p.stdout

def brace_end(text:str,open_i:int)->int:
 depth=0;i=open_i;state='code'
 while i<len(text):
  if state=='code':
   if text.startswith('//',i):state='line';i+=2;continue
   if text.startswith('/*',i):state='block';i+=2;continue
   if text[i] in "\"'":state='str' if text[i]=='\"' else 'char';i+=1;continue
   if text[i]=='{':depth+=1
   elif text[i]=='}':
    depth-=1
    if depth==0:return i+1
  elif state=='line':
   if text[i]=='\n':state='code'
  elif state=='block':
   if text.startswith('*/',i):state='code';i+=2;continue
  elif state in ('str','char'):
   if text[i]=='\\':i+=2;continue
   if (state=='str' and text[i]=='\"') or (state=='char' and text[i]=="'"):state='code'
  i+=1
 raise ValueError('unmatched C brace')

def patch_function(text:str,name:str,body:str)->str:
 m=re.search(r'(?m)^int16_t\s+'+re.escape(name)+r'\s*\([^;]*\)\s*\{',text)
 if not m:raise ValueError(f'function not found: {name}')
 open_i=text.find('{',m.start());end=brace_end(text,open_i)
 return text[:open_i]+body+text[end:]

def main()->int:
 if REPORT.exists():raise SystemExit(f'refusing to overwrite {REPORT.relative_to(ROOT)}')
 plan=json.loads(PLAN.read_text(encoding='utf-8'))
 source=GEN/'S09_m35F5.c'; root_source=GEN/'root_m004A.c'; owners=GEN/'native_owners.c';header=GEN/'native_owners.h'
 for p in (source,root_source,owners,header):
  if not p.exists():raise SystemExit(f'missing generated input: {p}')
 # Select two real records: a 16-bit scalar and 32-bit scalar, both overlaid
 # through the reviewed raw-byte union member in the generated S09 table.
 wanted=['HealthR','fd_50F6_0220']; rows={}
 text=source.read_text(encoding='utf-8')
 table=re.search(r'(?s)struct SaveRec\s+fd_4E4B_0000\[308\]\s*=\s*\{(.*?)\n\};',text)
 if not table:raise ValueError('current generated SaveRec table not found')
 table_lines=table.group(1).splitlines()
 for name in wanted:
  hits=[line for line in table_lines if re.search(r'&native_state_'+re.escape(name)+r'\.raw_bytes',line)]
  if len(hits)!=1:raise ValueError(f'expected one generated raw SaveRec row for {name}: {hits}')
  rows[name]=hits[0]
 assert re.search(r'\{\s*2\s*,\s*1\s*,',rows['HealthR'])
 assert re.search(r'\{\s*4\s*,\s*1\s*,',rows['fd_50F6_0220'])
 fixture_table='\n'+rows['HealthR']+'\n'+rows['fd_50F6_0220']+'\n    { 0, 0, 0 },'
 text=text[:table.start(1)]+fixture_table+text[table.end(1):]
 # File selection is a declared UI boundary for LoadGame; keep both save/load
 # routine bodies and the real SaveRec iteration untouched.
 text=patch_function(text,'FileSelect','{\n    (void)title; (void)verb; (void)save;\n    strcpy(name, "bounded.v3");\n    return 1;\n}')
 WORK.mkdir(parents=True,exist_ok=True)
 test_s09=WORK/'S09_fixture.c';test_s09.write_text(text,encoding='utf-8',newline='\n')
 # Compile the exact generated MapPlane consumer function, extracted from its
 # current TU, so its behavior does not depend on unrelated map-view functions.
 consumer_text=root_source.read_text(encoding='utf-8')
 match=re.search(r'(?m)^void\s+f_004A_02AD\s*\(void\)\s*\{',consumer_text)
 if not match:raise ValueError('actual generated f_004A_02AD consumer missing')
 copen=consumer_text.find('{',match.start()); cend=brace_end(consumer_text,copen)
 consumer_func=consumer_text[match.start():cend]
 consumer=WORK/'MapPlane_consumer.c'
 consumer.write_text('''#include <stdint.h>\n#include \"native_owners.h\"\ntypedef struct { int16_t x,y; } Point;\nextern int16_t fd_50F6_0FB6,fd_50F6_0FFA;\nextern Point fd_50F6_0596,fd_50F6_06A6,fd_50F6_072E,fd_50F6_0508;\nextern void UpdateEdit(void); extern void f_0250_0ED2(void);\n'''+consumer_func+'\n',encoding='utf-8',newline='\n')
 harness=WORK/'probe.c'
 harness.write_text(r'''#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <stdarg.h>
#include "native_owners.h"
#include "portable/whole_program/platform/graphics.h"
int16_t LoadGame(void);
int16_t o09_35F5_0188(int16_t useLast);
void f_004A_02AD(void);
int16_t fd_3D57_02C2=0, fd_50F6_0EAC=0, fd_3D57_07AA=1;
char fd_50F6_3862[100]="bounded.v3";
int16_t fd_50F6_0354=0, TERRAINset=1, CurGndTileID=0;
int32_t fd_50F6_0214=0,fd_50F6_0204=0,fd_50F6_0472=0;
uint8_t LifeA[128][64],LifeB[64][64],LifeR[64][64];
int16_t ListIndexA=-1,ListIndexB=-1,ListIndexR=-1;
uint8_t AlistX[500],AlistY[500],AlistT[500],BlistX[500],BlistY[500],BlistT[500],RlistX[500],RlistY[500],RlistT[500];
int16_t fd_50F6_0A06=1,fd_50F6_0496=0,fd_50F6_04C2=0,MeLocY=0,MeLocX=0,MePlane=0;
struct TestPoint { int16_t x,y; };
struct TestPoint fd_50F6_0508={6,8},fd_50F6_0596={0,0},fd_50F6_06A6={0,0},fd_50F6_072E={0,0};
int16_t fd_50F6_0FB6=20,fd_50F6_0FFA=14;
static uint8_t wire[8]; static size_t wire_len=0,wire_pos=0; static int open_count=0;
int16_t dos_open(char *path,int16_t flags,...){(void)path;if(flags&0x0100){open_count++;wire_len=wire_pos=0;return 3;}if((flags&0x0002)!=0){open_count++;return -1;}wire_pos=0;return 3;}
int16_t dos_write(int16_t fd,void *p,uint16_t n){(void)fd;if(wire_len+n>sizeof wire)return -1;memcpy(wire+wire_len,p,n);wire_len+=n;return n;}
int16_t dos_read(int16_t fd,void *p,uint16_t n){(void)fd;size_t avail=wire_len-wire_pos;if(n>avail)n=(uint16_t)avail;memcpy(p,wire+wire_pos,n);wire_pos+=n;return n;}
int16_t dos_close(int16_t fd){(void)fd;return 0;}
int16_t dos_remove(char *p){(void)p;return 0;}
int16_t dos_sprintf(char *p,const char *fmt,...){va_list a;va_start(a,fmt);int n=vsprintf(p,fmt,a);va_end(a);return (int16_t)n;}
char *_fstrcpy(char *d,const char *s){return strcpy(d,s);}
void WinPrintf(char *fmt,...){(void)fmt;}
void f_1C62_00AC(char *s){(void)s;}
void f_1C62_00C0(char *s){(void)s;}
int16_t f_1C62_0415(char *s,int16_t x){(void)s;(void)x;return 1;}
void f_15D9_009C(void *p,int32_t a,int16_t b){(void)p;(void)a;(void)b;}
int16_t o15_384C_0239(int16_t a){(void)a;return 2;}
void EditMessage(void *p,int32_t a,int16_t b){(void)p;(void)a;(void)b;}
void SetMenuEntries(void){}
void PauseGame(int16_t a){(void)a;}
int16_t dos_errno=0;
void o11_35F5_0000(void){}
void o11_35F5_0088(int16_t x){(void)x;}
void RandYard(void){}
void StopSong(void){}
void OverlayTileSet(int16_t t,int16_t id){(void)t;(void)id;}
void SetMyLife(int16_t p,int16_t x,int16_t y,int16_t t,int16_t d,int16_t l){(void)p;(void)x;(void)y;(void)t;(void)d;(void)l;}
void FullCount(void){}
void SetDefaultWindows(void){}
void CenterEdit(int16_t x,int16_t y){(void)x;(void)y;}
void SetDefaultWindPrompt(int16_t m){(void)m;}
void UpdateEdit(void){}
void f_0250_0ED2(void){}
int main(void){
    native_state_HealthR.signed_value=(int16_t)0x1234;
    native_state_fd_50F6_0220.signed_value=(int32_t)0x12345678;
    if(o09_35F5_0188(1)!=1) return 10;
    {const uint8_t expected[]={0x34,0x12,0x78,0x56,0x34,0x12};
     if(wire_len!=sizeof expected||memcmp(wire,expected,sizeof expected)!=0)return 11;}
    native_state_HealthR.signed_value=0;native_state_fd_50F6_0220.signed_value=0;
    native_state_MapPlane.signed_value=2;
    f_004A_02AD();
    if(fd_50F6_06A6.x!=16||fd_50F6_06A6.y!=15)return 12;
    if(LoadGame()!=1)return 13;
    if(native_state_HealthR.signed_value!=(int16_t)0x1234||native_state_fd_50F6_0220.signed_value!=(int32_t)0x12345678)return 14;
    if(native_state_HealthR.raw_bytes[0]!=0x34||native_state_HealthR.raw_bytes[1]!=0x12)return 15;
    puts("PASS: actual generated S09 SaveGame/LoadGame record loops round-trip two V3 union owners; generated root:m004A MapPlane consumer observes scalar member");
    return 0;
}
''',encoding='utf-8',newline='\n')
 # Separate function/data sections let the test retain actual SaveGame,
 # LoadGame, reset/rebuild functions while discarding unrelated FileSelect code.
 flags=['-std=c11','-fsigned-char','-fno-builtin','-fno-common','-Wall','-Wextra','-Werror','-Wno-builtin-declaration-mismatch','-Wno-sequence-point','-Wno-address','-Wno-unused-variable','-ffunction-sections','-fdata-sections','-I'+str(GEN),'-I'+str(ROOT)]
 s09_o=WORK/'S09_fixture.o';consumer_o=WORK/'MapPlane_consumer.o';owners_o=WORK/'native_owners.o';harness_o=WORK/'probe.o';exe=WORK/'probe.exe'
 for src,obj in [(test_s09,s09_o),(consumer,consumer_o),(owners,owners_o),(harness,harness_o)]:
  run(['gcc',*flags,'-c',str(src),'-o',str(obj)])
 linklog=run(['gcc',str(harness_o),str(s09_o),str(consumer_o),str(owners_o),'-Wl,--gc-sections','-o',str(exe)])
 output=run([str(exe)])
 if 'PASS:' not in output:raise RuntimeError(output)
 inputs={p.relative_to(ROOT).as_posix():sha(p) for p in [PLAN,source,root_source,owners,header,test_s09,consumer,harness,s09_o,consumer_o,owners_o,harness_o,exe]}
 report={'schema':'simant-source-bounded-save-access-v1','claim':'DIAGNOSTIC_ONLY: actual current generated S09 SaveGame/LoadGame loops and a generated root:m004A scalar consumer exercise two reviewed source-bounded union owners; only selected SaveRec rows and explicitly listed host/game boundaries are covered.','inputs':inputs,'selected_actual_rows':{k:v.strip() for k,v in rows.items()},'controlled_boundaries':['FileSelect modal UI replaced in scratch copy to return a fixed path','dos_open/read/write/close/remove use bounded in-memory byte stream','RandYard is stubbed','OverlayTileSet, SetMyLife, FullCount, SetDefaultWindows, CenterEdit, SetDefaultWindPrompt are stubs','StopSong, post-load callbacks, message/UI services are stubs','SaveRec table in scratch copy contains two original rows plus original count==0 terminator'],'positive':{'savegame_actual_loop_writes_six_little_endian_bytes':True,'loadgame_actual_loop_restores_typed_values_and_raw_bytes':True,'source_consumer_f004A02AD_uses_MapPlane_scalar_member':True,'save_record_order_preserved':True},'limitations':['Not a full 307-row file compatibility test.','The tested generated S09 source includes other current migration changes; source hash is recorded for this run.','No native big-endian conversion is tested; this verifies current little-endian host bytes only.','No claim is made about RandYard or post-load rebuild services.'],'observed_output':output.strip(),'summary':{'records':2,'bytes':6,'passed':True}}
 REPORT.parent.mkdir(parents=True,exist_ok=True)
 REPORT.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
 print(output.strip());print(REPORT.relative_to(ROOT),sha(REPORT))
 return 0
if __name__=='__main__':raise SystemExit(main())
