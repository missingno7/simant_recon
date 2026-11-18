"""Reset/client geometry, live scaling, typed source hits and persisted CLI scale."""
import argparse,json,os,re,shutil,subprocess,sys,tempfile,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from portable.tests.enhanced.common import ROOT,check_build
from portable.tests.acceptance.state_schema import sha

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--build',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();build=a.build.resolve();out=a.out.resolve();out.mkdir(parents=True,exist_ok=False);report=check_build(build);cc=report['application_link']['command'][0]
 source=Path(__file__).with_name('ui_scale_probe.c');obj=out/'probe.o';r=subprocess.run([cc,'-std=c11','-O2','-g','-I'+str(ROOT),'-I'+str(ROOT/'build/deps/sdl3-sdk/SDL3-3.4.16/x86_64-w64-mingw32/include'),'-c',str(source),'-o',str(obj)],capture_output=True,text=True);(out/'compile.log').write_text(r.stdout+r.stderr);r.check_returncode()
 exe=out/'simant-ui-scale.exe';cmd=report['application_link']['command'][:];cmd[cmd.index('-o')+1]=str(exe);cmd[1:1]=[str(obj),*['-Wl,--wrap='+n for n in ('enhanced_execute_next','enhanced_source_poll','portable_m1b73_try_enqueue_command','GetMonitorInfoA','GetMonitorInfoW','__imp_GetMonitorInfoA','__imp_GetMonitorInfoW','native_windows_present')]]
 r=subprocess.run(cmd,cwd=build,capture_output=True,text=True);(out/'link.log').write_text(r.stdout+r.stderr);r.check_returncode()
 for name in ('SDL3.dll','simant-build-id.txt'):shutil.copyfile(build/name,out/name)
 shutil.copytree(build/'runtime-bios-fonts',out/'runtime-bios-fonts');begin=time.monotonic()
 with tempfile.TemporaryDirectory(prefix='assets-',dir=out) as folder:
  shutil.copytree(build/'runtime-assets',folder,dirs_exist_ok=True);env={k:v for k,v in os.environ.items() if not k.startswith(('SIMANT_ENHANCED','SIMANT_UI','SIMANT_WORKSPACE'))};env.update(SIMANT_UI_OUT=str(out),SIMANT_WORKSPACE_LAYOUT=str(out/'layout.txt'),SDL_AUDIODRIVER='dummy')
  cmd=[str(exe),'--windows','--ui-scale','125','--deterministic','--seed','0','--assets',folder,'--input-script',str(ROOT/'portable/tests/runtime/windows-quick.txt'),'--smoke-ms','180000','--diagnostics-dir='+str(out/'diagnostics')]
  with (out/'run.log').open('w') as log:
   try:code=subprocess.run(cmd,cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=210).returncode
   except subprocess.TimeoutExpired:code='timeout'
  persistence=[]
  for label,args,expected in [('saved',[],200),('auto',['--ui-scale','auto'],0),('override',['--ui-scale','250'],250)]:
   follow=cmd[:];del follow[follow.index('--ui-scale'):follow.index('--ui-scale')+2];follow[1:1]=args;env['SIMANT_UI_PERSISTED']=str(expected)
   with (out/(label+'.log')).open('w') as log:
    try:rc=subprocess.run(follow,cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=90).returncode
    except subprocess.TimeoutExpired:rc='timeout'
   found=re.findall(r'^UI_PERSIST_RESULT (.*)$',(out/(label+'.log')).read_text(),re.M);row=json.loads(found[-1]) if found else dict(passed=False);row.update(label=label,exit_code=rc);row['passed']&=rc==0;persistence.append(row)
 matches=re.findall(r'^UI_SCALE_RESULT (.*)$',(out/'run.log').read_text(),re.M);result=json.loads(matches[-1]) if matches else dict(passed=False,error='incomplete');result.update(exit_code=code,seconds=round(time.monotonic()-begin,2),probe_sha256=sha(source),executable_sha256=sha(exe));result['passed']&=code==0
 saved=(out/'layout.txt').read_text().splitlines();result['persisted']=saved[:2]==['SIMANT-WINDOWS 3','250'];result['persistence_lanes']=persistence;result['passed']&=result['persisted'] and all(r['passed'] for r in persistence)
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result));return int(not result['passed'])
if __name__=='__main__':raise SystemExit(main())
