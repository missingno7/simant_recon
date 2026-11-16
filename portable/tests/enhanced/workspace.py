"""Ordinary enhanced windows: attachment, persistence, input and native captures."""
import argparse,json,os,re,shutil,subprocess,sys,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from portable.tests.enhanced.common import ROOT,check_build
from portable.tests.acceptance.state_schema import sha

def run(cmd,**kw):
 p=subprocess.run(cmd,capture_output=True,text=True,timeout=180,**kw)
 if p.returncode:raise RuntimeError(p.stdout[-3000:]+p.stderr[-3000:])
 return p

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--build',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--screens',type=Path);ap.add_argument('--scene',type=int)
 a=ap.parse_args()
 if a.screens and a.screens.resolve().exists():raise FileExistsError('Fresh screenshots directory required: '+str(a.screens.resolve()))
 build=a.build.resolve();out=a.out.resolve();out.mkdir(parents=True,exist_ok=False);report=check_build(build);cc=report['application_link']['command'][0];source=Path(__file__).parent
 model=out/'workspace-model.exe';run([cc,'-std=c11','-O2','-I'+str(ROOT),str(source/'workspace_model.c'),str(ROOT/'portable/whole_program/enhanced/workspace.c'),'-o',str(model)]);model_result=json.loads(run([str(model),str(out/'roundtrip.tmp')],cwd=ROOT).stdout)
 obj=out/'workspace-probe.o';run([cc,'-std=c11','-O2','-g','-I'+str(ROOT),'-I'+str(ROOT/'build/deps/sdl3-sdk/SDL3-3.4.16/x86_64-w64-mingw32/include'),'-c',str(source/'workspace_probe.c'),'-o',str(obj)])
 exe=out/'simant-workspace.exe';command=report['application_link']['command'][:];command[command.index('-o')+1]=str(exe);command[1:1]=[str(obj),'-Wl,--wrap=enhanced_execute_next'];linked=run(command,cwd=build);(out/'link.txt').write_text(linked.stdout+linked.stderr)
 for name in ('SDL3.dll','simant-build-id.txt'):shutil.copyfile(build/name,out/name)
 shutil.copytree(build/'runtime-bios-fonts',out/'runtime-bios-fonts');scratch=ROOT/'build/workers/enhanced-build-a/temporary';scratch.mkdir(parents=True,exist_ok=True)
 captions=[('undocked','Ordinary floating game, Map and allocation windows; original picture controls in two separate windows.'),('docked','The same windows attached to main-client edges, retaining their captions and capabilities.'),('menu','The real Options popup mirrors the game checks; all five game menus remain on the frame.'),('ant-panel','Map / Ant Control Panel, shipped picture buttons and native numeric health/population.'),('yard-panel','Yard Control Panel, shipped picture buttons, queen drop choice and health/population.'),('zoom-in','Primary native world at 300%; host zoom does not issue a gameplay action.'),('zoom-out','The same native world at 50%; host zoom does not issue a gameplay action.'),('edge-drag','Title-drag edge preview in progress: thin attachment outline, without targets or compass.'),('tooltip','Native tooltip on the Go to Yellow Ant picture button.'),('persistence','Separate process restores saved attachment, floating bounds, visibility and host zoom.')]
 results=[]
 with tempfile.TemporaryDirectory(prefix='w',dir=scratch) as folder:
  assets=Path(folder);shutil.copytree(build/'runtime-assets',assets,dirs_exist_ok=True)
  for index,(name,caption) in enumerate(captions):
   if a.scene is not None and index!=a.scene:continue
   lane=out/name;lane.mkdir();env={k:v for k,v in os.environ.items() if not k.startswith(('SIMANT_ENHANCED','SIMANT_WORKSPACE','SIMANT_TEST_'))};env.update(SIMANT_ENHANCED_CONTRACTS='1',SIMANT_ENHANCED_WORKSPACE='1',SIMANT_WORKSPACE_LAYOUT=str(lane/'layout.txt'),SIMANT_WORKSPACE_SCENE=str(index),SIMANT_WORKSPACE_ACTIVATION='1',SIMANT_WORKSPACE_CAPTURE=str(lane/'frame.bmp'),SDL_AUDIODRIVER='dummy')
   if index==9:
    seed=out/'docked/layout.txt';shutil.copyfile(seed,lane/'layout.txt');env['SIMANT_WORKSPACE_EXPECT_LAYOUT']=str(seed)
   cmd=[str(exe),'--deterministic','--windows','--seed','0','--assets',str(assets),'--input-script',str(ROOT/'portable/tests/runtime/windows-quick.txt'),'--smoke-ms','20000','--diagnostics-dir='+str(lane/'diagnostics')]
   with (lane/'run.log').open('w') as log:p=subprocess.run(cmd,cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=180)
   log=(lane/'run.log').read_text();rows=re.findall(r'^WORKSPACE_UI (.*)$',log,re.M)
   if p.returncode or not rows:raise RuntimeError('Incomplete ordinary-window scene: '+str(lane))
   activation=re.findall(r'^WORKSPACE_ACTIVATION (.*)$',log,re.M);result=json.loads(rows[-1]);result['activation']=json.loads(activation[-1]) if activation else {'passed':False};result['passed']=result['passed'] and result['activation']['passed'];restore=re.findall(r'^WORKSPACE_RESTORE (.*)$',log,re.M);result['restore']=json.loads(restore[-1]) if restore else None;result['passed']=result['passed'] and (index!=9 or bool(result['restore'] and result['restore']['passed']));result.update(name=name,caption=caption);crop=re.findall(r'WORKSPACE_CROP (-?\d+) (-?\d+) (-?\d+) (-?\d+)',log);result['crop']=[int(v) for v in crop[-1]] if crop else None;results.append(result)
 if a.screens:
  from PIL import Image
  screens=a.screens.resolve();screens.mkdir(parents=True,exist_ok=False)
  for row in results:
   if row['name']=='persistence':continue
   with Image.open(out/row['name']/'frame.bmp') as raw:
    im=raw.convert('RGB');im=im.crop(tuple(row['crop'])) if row['crop'] else im;im.resize((1280,round(im.height*1280/im.width)),Image.Resampling.LANCZOS).save(screens/(row['name']+'.png'))
  (screens/'README.md').write_text('# Enhanced build A: actual native-window readbacks\n\n'+'\n\n'.join(f"![{r['caption']}]({r['name']}.png)\n\n{r['caption']}" for r in results if r['name']!='persistence')+'\n\n1280 px phone copies. Native GDI readbacks, with retained SDL clients taken from their last uploaded textures, at the actual HWND/client bounds and ownership/z-order. These are not a full desktop or GPU pixel-equality certificate. Retained step B clients (Map, allocation editors and other content windows) still use their existing presentation. No mock-up art is substituted.\n')
 result=dict(passed=model_result['passed'] and all(r['passed'] for r in results),model=model_result,scenes=results,command=command,executable_sha256=sha(exe));(out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2));return int(not result['passed'])
if __name__=='__main__':raise SystemExit(main())
