"""Exercise real native admission with a queued SDL key and an omitted-guard negative."""
import argparse,json,os,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
def run(out):
 out=out.resolve();out.mkdir(parents=True,exist_ok=False)
 sdk=ROOT/'build/deps/sdl3-sdk/SDL3-3.4.16/x86_64-w64-mingw32';platform=ROOT/'portable/whole_program/platform';source=platform/'sdl3/input_time_host.c'
 base=['C:/msys64/mingw64/bin/gcc.exe','-std=c11','-O0','-g','-I'+str(ROOT),'-I'+str(sdk/'include'),'-I'+str(platform/'sdl3')]
 common=[str(platform/'input_time.c'),str(platform/'pit_clock.c'),str(platform/'sdl3/host.c'),str(ROOT/'portable/tests/acceptance/ideal_internal_refresh_test.c')]
 env=dict(os.environ,PATH=str(sdk/'bin')+os.pathsep+os.environ.get('PATH',''));rows=[]
 for name,src,expected in [('positive',source,0),('negative',out/'negative.c',71)]:
  if name=='negative':
   text=source.read_text();needle='if (!charge) return PORTABLE_INPUT_TIME_OK;'
   if text.count(needle)!=1:raise ValueError('Internal guard changed')
   src.write_text(text.replace(needle,''))
  exe=out/(name+'.exe');cmd=[*base,*common,str(src),'-L'+str(sdk/'lib'),'-lSDL3','-o',str(exe)]
  subprocess.run(cmd,check=True,capture_output=True,timeout=60)
  r=subprocess.run([str(exe)],env=env,capture_output=True,text=True,timeout=10)
  rows.append(dict(name=name,command=cmd,code=r.returncode,stdout=r.stdout,stderr=r.stderr))
  if r.returncode!=expected:raise RuntimeError(str(rows[-1]))
 (out/'report.json').write_text(json.dumps(dict(status='PASS',results=rows),indent=2)+'\n');print('PASS: internal admission and old-code negative')
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);run(p.parse_args().out)
