"""Native content windows: original transactions, passive repaint and owner captures."""
import argparse,json,os,re,shutil,subprocess,sys,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from portable.tests.enhanced.common import ROOT,check_build
from portable.tests.acceptance.state_schema import sha
CASES=['undocked','docked','map','yard','house','strategic','graphic','behavior','caste','history','info','status','triangle-edit','values','map-centre','info-follow','queued-value-map','history-held','steady-controls','camera-follow','exchange-prompt','world-help','placement-edges']
def run(cmd,**kwargs):
 p=subprocess.run(cmd,capture_output=True,text=True,timeout=120,**kwargs)
 if p.returncode:raise RuntimeError(p.stdout[-2000:]+p.stderr[-2000:])
 return p

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--build',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--screens',type=Path);ap.add_argument('--cases');a=ap.parse_args();build=a.build.resolve();out=a.out.resolve();out.mkdir(parents=True,exist_ok=False);report=check_build(build);cc=report['application_link']['command'][0]
 source=Path(__file__).with_name('content_probe.c');obj=out/'content-probe.o';run([cc,'-std=c11','-O2','-g','-I'+str(ROOT),'-I'+str(ROOT/'build/deps/sdl3-sdk/SDL3-3.4.16/x86_64-w64-mingw32/include'),'-c',str(source),'-o',str(obj)])
 exe=out/'simant-content.exe';command=report['application_link']['command'][:];command[command.index('-o')+1]=str(exe);command[1:1]=[str(obj),'-Wl,--wrap=enhanced_execute_next','-Wl,--wrap=enhanced_source_poll','-Wl,--wrap=enhanced_publish','-Wl,--wrap=native_workspace_present'];run(command,cwd=build)
 for name in ('SDL3.dll','simant-build-id.txt'):shutil.copyfile(build/name,out/name)
 shutil.copytree(build/'runtime-bios-fonts',out/'runtime-bios-fonts');results=[];cases=a.cases.split(',') if a.cases else CASES
 scratch=ROOT/'build/workers/enhanced-menus/temporary';scratch.mkdir(parents=True,exist_ok=True)
 with tempfile.TemporaryDirectory(prefix='content',dir=scratch) as folder:
  assets=Path(folder);shutil.copytree(build/'runtime-assets',assets,dirs_exist_ok=True)
  for case in cases:
   lane=out/case;lane.mkdir();env={k:v for k,v in os.environ.items() if not k.startswith(('SIMANT_ENHANCED','SIMANT_WORKSPACE','SIMANT_CONTENT','SIMANT_TEST_'))};env.update(SIMANT_ENHANCED_CONTRACTS='1',SIMANT_ENHANCED_WORKSPACE='1',SIMANT_WORKSPACE_LAYOUT=str(lane/'layout.txt'),SIMANT_CONTENT_CASE=case,SIMANT_CONTENT_CAPTURE=str(lane/'frame.bmp'),SDL_AUDIODRIVER='dummy')
   cmd=[str(exe),'--deterministic','--windows','--seed','0','--assets',str(assets),'--input-script',str(ROOT/'portable/tests/runtime/windows-quick.txt'),'--smoke-ms','30000','--diagnostics-dir='+str(lane/'diagnostics')]
   with (lane/'run.log').open('w') as log:
    try:p=subprocess.run(cmd,cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=90);code=p.returncode
    except subprocess.TimeoutExpired:code='timeout'
   log=(lane/'run.log').read_text();observations=re.findall(r'^CONTENT_RESULT (.*)$',log,re.M);result=json.loads(observations[-1]) if observations else dict(passed=False,case=case,error='incomplete');completed=re.findall(r'^CONTENT_COMPLETED (.*)$',log,re.M);result['completion']=json.loads(completed[-1]) if completed else None;result['exit_code']=code;result['passed']=result['passed'] and code==0 and bool(result['completion'] and result['completion']['passed'])
   bounds=re.findall(r'^CONTENT_BOUNDS (.*)$',log,re.M);origin=re.findall(r'^CONTENT_ORIGIN (.*)$',log,re.M)
   if bounds and origin:
    x,y=map(int,origin[-1].split());l,t,r,b=map(int,bounds[-1].split());result['crop']=[l-x,t-y,r-x,b-y]
   results.append(result);print(case,'PASS' if result['passed'] else 'FAIL',flush=True)
 if a.screens:
  from PIL import Image
  screens=a.screens.resolve();screens.mkdir(parents=True,exist_ok=False)
  for row in results:
   path=out/row['case']/'frame.bmp'
   if not path.exists():continue
   with Image.open(path) as source_image:
    im=source_image.convert('RGB')
    if row.get('crop'):im=im.crop(tuple(row['crop']))
    im.resize((1280,round(im.height*1280/im.width)),Image.Resampling.LANCZOS).save(screens/(row['case']+'.png'))
  (screens/'README.md').write_text('# Enhanced build B: native window readbacks\n\n'+ '\n\n'.join(f"- [{r['case']}]({r['case']}.png): {'PASS' if r['passed'] else 'FAIL'}; see the associated content receipt for its action assertion." for r in results)+'\n\nAll PNGs are 1280 pixels wide, captured from real windows. GDI clients use native text, semantic snapshots and independently owned shipped art. Full layouts composite native window readbacks; this is not a desktop/GPU identity or physical mixed-DPI certificate. No mockup is substituted. The source renderer continues hidden.\n')
 result=dict(passed=bool(results) and all(r['passed'] for r in results),cases=results,executable_sha256=sha(exe),probe_sha256=sha(source));(out/'result.json').write_text(json.dumps(result,indent=2)+'\n');return int(not result['passed'])
if __name__=='__main__':raise SystemExit(main())
