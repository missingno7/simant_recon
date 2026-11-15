"""Native workspace model, HWND keyboard/lifecycle, UIA and phone captures.

Every child is bounded and joined. Uses shipped startup in disposable assets;
test callbacks only mutate the production host layout, never source state.
"""
import argparse,json,os,re,shutil,subprocess,sys,tempfile,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from portable.tests.enhanced.common import ROOT,check_build
from portable.tests.acceptance.state_schema import sha

def run(command,**kwargs):
    result=subprocess.run(command,capture_output=True,text=True,timeout=120,**kwargs)
    if result.returncode:raise RuntimeError(result.stdout[-3000:]+result.stderr[-3000:])
    return result

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build',type=Path,required=True);parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--screens',type=Path)
    args=parser.parse_args();build=args.build.resolve();out=args.out.resolve();out.mkdir(parents=True,exist_ok=False)
    report=check_build(build);cc=report['application_link']['command'][0]
    source=Path(__file__).parent
    model=out/'workspace-model.exe'
    run([cc,'-std=c11','-O2','-I'+str(ROOT),str(source/'workspace_model.c'),str(ROOT/'portable/whole_program/enhanced/workspace.c'),'-o',str(model)])
    model_result=json.loads(run([str(model),str(out/'roundtrip.tmp')],cwd=ROOT).stdout)
    obj=out/'workspace-probe.o'
    run([cc,'-std=c11','-O2','-g','-I'+str(ROOT),'-I'+str(ROOT/'build/deps/sdl3-sdk/SDL3-3.4.16/x86_64-w64-mingw32/include'),'-c',str(source/'workspace_probe.c'),'-o',str(obj)])
    exe=out/'simant-workspace.exe';command=report['application_link']['command'][:]
    command[command.index('-o')+1]=str(exe);command[1:1]=[str(obj),'-Wl,--wrap=enhanced_execute_next','-Wl,--wrap=enhanced_source_poll']
    result=run(command,cwd=build);(out/'link.txt').write_text(result.stdout+result.stderr)
    for name in ('SDL3.dll','simant-build-id.txt'):shutil.copyfile(build/name,out/name)
    shutil.copytree(build/'runtime-bios-fonts',out/'runtime-bios-fonts')
    scratch=ROOT/'build/scratch/enhanced';scratch.mkdir(parents=True,exist_ok=True)
    results=[];captions=[
        ('default','Play preset: native workspace, primary world and named empty panels.'),
        ('inspectors','One primary plus live Surface and Black nest inspectors in three document splits.'),
        ('tabs','World and two live inspectors stacked in one native tab group.'),
        ('floating','Read-only inspector in an owned native tool window over its workspace.'),
        ('dock-targets','Real mid-drag workspace-edge and group-edge/stack target HWNDs; Escape cancels.'),
        ('narrow','740 x 520 physical frame; side groups collapse to expandable strips.'),
        ('scale-150','144-DPI metrics, world raster and native text after WM_DPICHANGED (150%).'),
        ('scale-200','192-DPI metrics, world raster and native text after WM_DPICHANGED (200%).')]
    with tempfile.TemporaryDirectory(prefix='w',dir=scratch) as folder:
        assets=Path(folder);shutil.copytree(build/'runtime-assets',assets,dirs_exist_ok=True)
        for index,(name,caption) in enumerate(captions):
            lane=out/name;lane.mkdir();layout=lane/'layout.txt';ready=lane/'ready.txt'
            env={k:v for k,v in os.environ.items() if not k.startswith(('SIMANT_ENHANCED','SIMANT_WORKSPACE','SIMANT_TEST_'))}
            env.update(SIMANT_ENHANCED_CONTRACTS='1',SIMANT_ENHANCED_WORKSPACE='1',SIMANT_WORKSPACE_LAYOUT=str(layout),
                SIMANT_WORKSPACE_SCENE=str(index),SIMANT_WORKSPACE_CAPTURE=str(lane/'frame.bmp'),SDL_AUDIODRIVER='dummy')
            if index==0:env.update(SIMANT_WORKSPACE_READY=str(ready),SIMANT_WORKSPACE_MODAL_TEST='1')
            cmd=[str(exe),'--deterministic','--windows','--seed','0','--assets',str(assets),
                '--input-script',str(source/'rebirth.txt') if index==0 else str(ROOT/'portable/tests/runtime/windows-quick.txt'),'--smoke-ms','40000' if index==0 else '18000',
                '--diagnostics-dir='+str(lane/'diagnostics')]
            with (lane/'run.log').open('w') as log:
                process=subprocess.Popen(cmd,cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT)
                try:
                    if index==0:
                        deadline=time.monotonic()+90
                        while not ready.is_file() and process.poll() is None and time.monotonic()<deadline:time.sleep(.1)
                        if not ready.is_file():raise RuntimeError('Native workspace did not reach UIA checkpoint')
                        try:
                            access=subprocess.run(['powershell','-NoProfile','-ExecutionPolicy','Bypass','-File',str(source/'workspace_accessibility.ps1'),
                                '-TaskProcess',str(process.pid),'-OutputPath',str(out/'accessibility.json')],capture_output=True,text=True,timeout=35)
                            (out/'accessibility.log').write_text(access.stdout+access.stderr)
                        finally:ready.unlink(missing_ok=True)
                    process.wait(timeout=120)
                finally:
                    if process.poll() is None:process.kill()
                    process.wait(timeout=10)
            text=(lane/'run.log').read_text();rows=re.findall(r'^WORKSPACE_UI (.*)$',text,re.M)
            if process.returncode or not rows:raise RuntimeError('Incomplete HWND workspace lane '+name)
            data=json.loads(rows[-1]);data.update(name=name,caption=caption);results.append(data)
            environment=re.findall(r'^WORKSPACE_ENV (.*)$',text,re.M)
            if environment:data['environment']=json.loads(environment[-1])
            if index==0:
                modal=re.findall(r'^WORKSPACE_MODAL (.*)$',text,re.M)
                if not modal or not json.loads(modal[-1])['passed']:raise RuntimeError('Source-modal layout/Prompt control not reached or failed')
                data['modal_layout']=json.loads(modal[-1])
            if not data['passed']:raise RuntimeError('HWND checks failed: '+str(data))
    accessibility=json.loads((out/'accessibility.json').read_text(encoding='utf-8-sig'))
    if args.screens:
        from PIL import Image
        screens=args.screens.resolve();screens.mkdir(parents=True,exist_ok=False)
        for name,caption in captions:
            with Image.open(out/name/'frame.bmp') as picture:
                picture.convert('RGB').resize((1280,round(picture.height*1280/picture.width)),Image.Resampling.LANCZOS).save(screens/(name+'.png'))
        (screens/'README.md').write_text('# Phase 2 native workspace captures\n\n'+
            '\n\n'.join(f'![{caption}]({name}.png)\n\n{caption}' for name,caption in captions)+
            '\n\n1280 px phone copies of PrintWindow captures of simultaneously live native HWNDs, composited at their actual positions. No source VGA panels or desktop pixels are added. Floating tools and docking targets are separate native windows. DPI cases deliver WM_DPICHANGED with 144/192 DPI; this exercises the layout/render path, not physical monitor hot-plug or OS text-scale changes. The machine baseline is reported by the native window.\n')
    result=dict(passed=model_result['passed'] and accessibility['passed'] and all(r['passed'] for r in results),model=model_result,scenes=results,
        accessibility='accessibility.json',executable_sha256=sha(exe),command=command,
        limits=['DPI-change message coverage is not a physical mixed-DPI/hot-unplug test.','Primary discrete plane actions are available; tile gestures remain phase 3.'])
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2));return int(not result['passed'])
if __name__=='__main__':raise SystemExit(main())
