"""MAP press/release, held drag, Esc and outside cancellation on a private desktop."""
import argparse,json,os,re,shutil,subprocess,sys,tempfile,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from portable.tests.enhanced.common import ROOT,check_build
from portable.tests.acceptance.state_schema import sha
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--build',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--cases',default='click,drag,escape,outside,drag-outside,drag-away,edge-right,edge-bottom,edge-corner,edge-left,edge-top');p.add_argument('--planes',default='surface,black,red');p.add_argument('--ui-scale',default='100');p.add_argument('--modes',default='quick,full,experimental');a=p.parse_args();started=time.monotonic()
    build=a.build.resolve();out=a.out.resolve();out.mkdir(parents=True,exist_ok=False);report=check_build(build);cc=report['application_link']['command'][0]
    source=Path(__file__).with_name('minimap_probe.c');obj=out/'probe.o';r=subprocess.run([cc,'-std=c11','-O2','-g','-I'+str(ROOT),'-I'+str(ROOT/'build/deps/sdl3-sdk/SDL3-3.4.16/x86_64-w64-mingw32/include'),'-c',str(source),'-o',str(obj)],capture_output=True,text=True);(out/'compile.log').write_text(r.stdout+r.stderr);r.check_returncode()
    exe=out/'simant-minimap.exe';cmd=report['application_link']['command'][:];cmd[cmd.index('-o')+1]=str(exe);cmd[1:1]=[str(obj),*['-Wl,--wrap='+n for n in ('enhanced_execute_next','enhanced_source_poll','native_workspace_minimap','CenterEdit')]]
    r=subprocess.run(cmd,cwd=build,capture_output=True,text=True);(out/'link.log').write_text(r.stdout+r.stderr);r.check_returncode()
    for name in ('SDL3.dll','simant-build-id.txt'):shutil.copyfile(build/name,out/name)
    shutil.copytree(build/'runtime-bios-fonts',out/'runtime-bios-fonts');rows=[]
    with tempfile.TemporaryDirectory(prefix='assets-',dir=out) as folder:
        assets=Path(folder);shutil.copytree(build/'runtime-assets',assets,dirs_exist_ok=True)
        for mode in a.modes.split(','):
            base=out/mode;base.mkdir();script=base/'input.txt';script.write_text((ROOT/'portable/tests/runtime/windows-quick.txt').read_text().replace('207 58',{'quick':'207 58','full':'133 126','experimental':'50 190'}[mode]))
            targets=[]
            for plane in a.planes.split(','):
                plane_dir=base/plane;plane_dir.mkdir()
                for case in a.cases.split(',')+([] if plane=='surface' else ['gutter-left','gutter-right']):
                    lane=plane_dir/case;lane.mkdir();targets.append((plane,case,lane))
            plan=base/'plan.txt';plan.write_text(''.join(f"{case} {dict(surface=1,black=2,red=3)[plane]} {lane/'popup.bmp'}\n" for plane,case,lane in targets))
            env={k:v for k,v in os.environ.items() if not k.startswith(('SIMANT_ENHANCED','SIMANT_MINIMAP','SIMANT_WORKSPACE'))};env.update(SIMANT_MINIMAP_CASE='plan',SIMANT_MINIMAP_PLANE='1',SIMANT_MINIMAP_PLAN=str(plan),SIMANT_WORKSPACE_LAYOUT=str(base/'layout.txt'),SDL_AUDIODRIVER='dummy')
            cmd=[str(exe),'--windows','--ui-scale',a.ui_scale,'--deterministic','--seed','0','--assets',str(assets),'--input-script',str(script),'--smoke-ms',str(60000*len(targets)),'--diagnostics-dir='+str(base/'diagnostics')]
            begin=time.monotonic()
            with (base/'run.log').open('w') as log:
                try:r=subprocess.run(cmd,cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=90*len(targets));code=r.returncode
                except subprocess.TimeoutExpired:code='timeout'
            matches=re.findall(r'^MINIMAP_RESULT (.*)$',(base/'run.log').read_text(),re.M)
            for i,(plane,case,lane) in enumerate(targets):
                row=json.loads(matches[i]) if i<len(matches) else dict(passed=False,error='incomplete');row.update(mode=mode,plane=plane,case=case,exit_code=code);row['passed']=row['passed'] and code==0;rows.append(row);print(mode,plane,case,'PASS' if row['passed'] else 'FAIL',flush=True)
                (lane/'result.json').write_text(json.dumps(row,indent=2)+'\n')
            print(mode,'shared startup seconds',round(time.monotonic()-begin,2),flush=True)
    result=dict(seconds=round(time.monotonic()-started,2),startups=len(a.modes.split(',')),passed=all(r['passed'] for r in rows),cases=rows,executable_sha256=sha(exe),probe_sha256=sha(source));(out/'result.json').write_text(json.dumps(result,indent=2)+'\n');return int(not result['passed'])
if __name__=='__main__':raise SystemExit(main())
