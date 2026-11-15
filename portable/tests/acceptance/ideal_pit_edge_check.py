"""Compile the recorder's real PIT class/event; reject a duplicate reload edge."""
import argparse,json,subprocess
from pathlib import Path
from portable.tests.acceptance.ideal_build import SOURCE,apply_patch,sha
HERE=Path(__file__).resolve().parent

def run(out):
 out=out.resolve();out.mkdir(parents=True,exist_ok=False)
 source=SOURCE/'src/hardware/timer.cpp';patch=HERE/'ideal/timer.cpp.patch'
 text=apply_patch(source.read_text(),patch.read_text())
 block=text[text.index('struct PIT_Block {'):text.index('static bool counter_output(')]
 prefix=r'''
#include <cassert>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
using Bitu=unsigned;using pic_tickindex_t=double;
extern unsigned long PIT_TICK_RATE;
static bool IdealActive=true,VGA_PITsync=false;
static double vga_fps=60,now_ms,next_ms;
static unsigned edges;static bool line_high;
#define IDEAL_PIT_RATE (IdealActive ? (14318180.0/12.0) : (double)PIT_TICK_RATE)
#define PIT_TICK_RATE_IBM 1193182
static double PIC_FullIndex(){return now_ms;}
static double PIC_GetCurrentEventTime(){return now_ms;}
static double pic_tickfmod(double a,double b){return fmod(a,b);}
static void PIC_DeActivateIRQ(unsigned){line_high=false;}
static void PIC_ActivateIRQ(unsigned){if(!line_high)++edges;line_high=true;}
static void PIC_AddEvent(void(*)(Bitu),double delay){next_ms=now_ms+delay;}
static double VGA_PITSync_delay(){return 1;}
'''
 suffix=r'''
int main(){
 // The real scheduled rising edge followed by the driver's mode-3 reload.
 // Old arithmetic says cycle=1 (OUT low) at this exact one-period instant.
 for(double base: {3956.0,0.0,10000.0,13457.0,193063.0}) {
  pit[0]=PIT_Block{};pit[0].mode=3;pit[0].cntr=214;
  pit[0].latch_next_counter();pit[0].reset_count_at(base);
  now_ms=base+pit[0].delay;edges=0;line_high=false;
  PIT0_Event(0);
  pit[0].track_time(now_ms);
  pit[0].update_output_from_counter(pit[0].read_counter());
  if(pit[0].output)PIC_ActivateIRQ(0);else PIC_DeActivateIRQ(0);
  pit[0].cntr=3424;pit[0].reset_count_at(now_ms);pit[0].latch_next_counter();
  pit[0].update_output_from_counter(pit[0].read_counter());
  if(pit[0].output)PIC_ActivateIRQ(0);else PIC_DeActivateIRQ(0);
  if(edges!=1){fprintf(stderr,"Duplicate edge at %.0f: %u\n",base,edges);return 71;}
 }
 puts("PASS: actual recorder PIT rising phase and same-instant slow reload");
}
'''
 prefix+='#include <initializer_list>\n'
 commands=[];results=[]
 def execute(label,body,expected):
  cpp=out/(label+'.cpp');exe=out/(label+'.exe');cpp.write_text(prefix+body+suffix)
  cmd=['C:/msys64/mingw64/bin/g++.exe','-std=c++17',str(cpp),'-o',str(exe)]
  r=subprocess.run(cmd,capture_output=True,text=True,timeout=60)
  if r.returncode:raise RuntimeError(r.stderr)
  r=subprocess.run([str(exe)],capture_output=True,text=True,timeout=10)
  results.append(dict(label=label,code=r.returncode,stdout=r.stdout,stderr=r.stderr,command=cmd))
  if r.returncode!=expected:raise RuntimeError(str(results[-1]))
 execute('positive',block,0)
 # Remove only the phase establishment, retaining the same real PIT code.
 negative=block.replace('pit[0].start = pit[0].now = PIC_FullIndex();','').replace('pit[0].cycle_base = 0;','')
 execute('negative',negative,71)
 (out/'report.json').write_text(json.dumps(dict(status='PASS',source_sha256=sha(source),patch_sha256=sha(patch),results=results),indent=2)+'\n')
 print('PASS: recorder PIT edge regression and old-code negative')
if __name__=='__main__':
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();run(a.out)

