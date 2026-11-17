"""First source world, first allocation frame, masked icons and editable percentages."""
import argparse,json,os,re,shutil,subprocess,sys,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from portable.tests.enhanced.common import ROOT,check_build
from portable.tests.enhanced.assets import records
from portable.tests.acceptance.state_schema import sha
CASES=['startup','startup-tutorial','startup-load','first-frame','reopen','icons','numeric','slow-paint']
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--build',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--cases');p.add_argument('--stack-after',type=int,help='Diagnostic only: attach GDB to this runner\'s own child after N seconds');a=p.parse_args();build=a.build.resolve();out=a.out.resolve();out.mkdir(parents=True,exist_ok=False);report=check_build(build)
    cc=report['application_link']['command'][0];obj=out/'presentation-probe.o';source=Path(__file__).with_name('presentation_probe.c')
    compiled=subprocess.run([cc,'-std=c11','-O2','-g','-I'+str(ROOT),'-I'+str(ROOT/'build/deps/sdl3-sdk/SDL3-3.4.16/x86_64-w64-mingw32/include'),'-c',str(source),'-o',str(obj)],capture_output=True,text=True);(out/'compile.log').write_text(compiled.stdout+compiled.stderr);compiled.check_returncode()
    exe=out/'simant-presentation.exe';command=report['application_link']['command'][:];command[command.index('-o')+1]=str(exe);command[1:1]=[str(obj),*['-Wl,--wrap='+name for name in ('native_windows_present','enhanced_source_poll','enhanced_execute_next','portable_m1b73_try_enqueue_command')]]
    linked=subprocess.run(command,cwd=build,capture_output=True,text=True);(out/'link.log').write_text(linked.stdout+linked.stderr);linked.check_returncode()
    for name in ('SDL3.dll','simant-build-id.txt'):shutil.copyfile(build/name,out/name)
    shutil.copytree(build/'runtime-bios-fonts',out/'runtime-bios-fonts');art=out/'art.txt';art.write_text('\n'.join(str(id) for kind,id in sorted(records()[1]) if kind==2)+'\n');rows=[]
    scratch=ROOT/'build/workers/enhanced-menus/temporary';scratch.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='presentation',dir=scratch) as folder:
        assets=Path(folder);shutil.copytree(build/'runtime-assets',assets,dirs_exist_ok=True)
        for case in a.cases.split(',') if a.cases else CASES:
            lane=out/case;lane.mkdir();env={k:v for k,v in os.environ.items() if not k.startswith(('SIMANT_ENHANCED','SIMANT_PRESENT','SIMANT_WORKSPACE'))};env.update(SIMANT_WORKSPACE_LAYOUT=str(lane/'layout.txt'),SIMANT_PRESENT_CASE=case,SIMANT_PRESENT_OUT=str(lane),SIMANT_PRESENT_ART=str(art),SDL_AUDIODRIVER='dummy')
            script=ROOT/'portable/tests/runtime/windows-quick.txt'
            if case=='startup-load':script=lane/'input.txt';script.write_text((ROOT/'portable/tests/runtime/windows-quick.txt').read_text().replace('207 58','207 190'))
            if case=='startup-tutorial':script=lane/'input.txt';script.write_text((ROOT/'portable/tests/runtime/windows-quick.txt').read_text().replace('207 58','50 58'))
            cmd=[str(exe),'--windows','--deterministic','--seed','0','--assets',str(assets),'--input-script',str(script),'--smoke-ms','60000','--diagnostics-dir='+str(lane/'diagnostics')]
            with (lane/'run.log').open('w') as log:
                with subprocess.Popen(cmd,cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT) as run:
                    try:code=run.wait(timeout=a.stack_after or 100)
                    except subprocess.TimeoutExpired:
                        if a.stack_after:
                            with (lane/'stack.log').open('w') as stack:
                                subprocess.run(['C:/msys64/mingw64/bin/gdb.exe','-q','-batch',str(exe),'-p',str(run.pid),'-ex','thread apply all bt',*sum((['-ex','p '+name] for name in ('phase','numeric_step','main_iteration_count','GamePaused','CurGameTool','ledger','count','head','highest_serial','frames[current].panels')),[]),'-ex','detach'],stdout=stack,stderr=subprocess.STDOUT,timeout=30)
                            try:code=run.wait(timeout=100)
                            except subprocess.TimeoutExpired:run.kill();run.wait();code='timeout'
                        else:run.kill();run.wait();code='timeout'
            matches=re.findall(r'^PRESENT_RESULT (.*)$',(lane/'run.log').read_text(),re.M);result=json.loads(matches[-1]) if matches else dict(passed=False,error='incomplete');result.update(case=case,exit_code=code);result['passed']=result['passed'] and code==0;rows.append(result);print(case,'PASS' if result['passed'] else 'FAIL',flush=True)
    result=dict(passed=all(row['passed'] for row in rows),cases=rows,executable_sha256=sha(exe),probe_sha256=sha(source),scope='Real source startup and original event delivery. First-show captures precede all allocation input; every shipped art mask is checked over a non-paper destination; typed input observes actual source triangle events, levels, presets and IdealCaste.')
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');return int(not result['passed'])
if __name__=='__main__':raise SystemExit(main())
