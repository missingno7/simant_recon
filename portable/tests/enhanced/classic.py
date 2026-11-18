"""Classic/Native typography, full captions, reachable cascades and readbacks."""
import argparse,json,os,re,shutil,subprocess,sys,tempfile,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from portable.tests.enhanced.common import ROOT,check_build
from portable.tests.acceptance.state_schema import sha
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--build',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();build=a.build.resolve();out=a.out.resolve();out.mkdir(parents=True,exist_ok=False);report=check_build(build);cc=report['application_link']['command'][0]
 source=Path(__file__).with_name('classic_probe.c');obj=out/'probe.o';r=subprocess.run([cc,'-std=c11','-O2','-g','-I'+str(ROOT),'-I'+str(ROOT/'build/deps/sdl3-sdk/SDL3-3.4.16/x86_64-w64-mingw32/include'),'-include',str(ROOT/'portable/whole_program/enhanced/assets.h'),'-c',str(source),'-o',str(obj)],capture_output=True,text=True);(out/'compile.log').write_text(r.stdout+r.stderr);r.check_returncode()
 exe=out/'simant-classic.exe';cmd=report['application_link']['command'][:];cmd[cmd.index('-o')+1]=str(exe);cmd[1:1]=[str(obj),*['-Wl,--wrap='+n for n in ('enhanced_execute_next','enhanced_source_poll','portable_m1b73_try_enqueue_command','GetMonitorInfoA','GetMonitorInfoW','__imp_GetMonitorInfoA','__imp_GetMonitorInfoW','native_windows_present')]]
 r=subprocess.run(cmd,cwd=build,capture_output=True,text=True);(out/'link.log').write_text(r.stdout+r.stderr);r.check_returncode()
 for name in ('SDL3.dll','simant-build-id.txt'):shutil.copyfile(build/name,out/name)
 shutil.copytree(build/'runtime-bios-fonts',out/'runtime-bios-fonts');begin=time.monotonic()
 with tempfile.TemporaryDirectory(prefix='assets-',dir=out) as folder:
  shutil.copytree(build/'runtime-assets',folder,dirs_exist_ok=True);env={k:v for k,v in os.environ.items() if not k.startswith(('SIMANT_ENHANCED','SIMANT_UI','SIMANT_WORKSPACE'))};env.update(SIMANT_UI_OUT=str(out),SIMANT_WORKSPACE_LAYOUT=str(out/'layout.txt'),SDL_AUDIODRIVER='dummy')
  cmd=[str(exe),'--windows','--deterministic','--seed','0','--assets',folder,'--input-script',str(ROOT/'portable/tests/runtime/windows-quick.txt'),'--smoke-ms','180000','--diagnostics-dir='+str(out/'diagnostics')]
  with (out/'run.log').open('w') as log:
   try:code=subprocess.run(cmd,cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=210).returncode
   except subprocess.TimeoutExpired:code='timeout'
 matches=re.findall(r'^CLASSIC_RESULT (.*)$',(out/'run.log').read_text(),re.M);result=json.loads(matches[-1]) if matches else dict(passed=False,error='incomplete');result.update(exit_code=code,seconds=round(time.monotonic()-begin,2),probe_sha256=sha(source),executable_sha256=sha(exe),scope='Both looks, all scales, DPI 96/120/144: actual top-level menu rectangles and every submenu measure, independent FONT2/Tahoma extents, fixed child bounds/no overlap, 1280/1080p/1440p caption access at 100/200/300, full source-neutral matrix and all fixed-panel readbacks.');result['passed']&=code==0
 result['look_persisted']=(out/'layout.txt').read_text().splitlines()[:2]==['SIMANT-WINDOWS 4','200 1'];result['passed']&=result['look_persisted']
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result));return int(not result['passed'])
if __name__=='__main__':raise SystemExit(main())
