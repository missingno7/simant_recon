"""Census and bounded interaction of every live native panel control/menu item.

Quick, Full and Experimental inventories are taken from their actual HWND/HMENU
trees. A session is reused only when the tested transaction left source state unchanged. Modal completion is tested through
real native Esc/outside messages, followed by a second actual Pause button input.
"""
import argparse,json,os,re,shutil,subprocess,sys,tempfile,time,queue,threading
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from portable.tests.enhanced.common import ROOT,check_build
from portable.tests.acceptance.state_schema import sha
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--build',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--modes',default='quick,full,experimental');p.add_argument('--ids',help='Preflight subset; full registration omits this');a=p.parse_args();started=time.monotonic()
    build=a.build.resolve();out=a.out.resolve();out.mkdir(parents=True,exist_ok=False);report=check_build(build);cc=report['application_link']['command'][0]
    source=Path(__file__).with_name('sweep_probe.c');obj=out/'probe.o';r=subprocess.run([cc,'-std=c11','-O2','-g','-I'+str(ROOT),'-I'+str(ROOT/'build/deps/sdl3-sdk/SDL3-3.4.16/x86_64-w64-mingw32/include'),'-c',str(source),'-o',str(obj)],capture_output=True,text=True);(out/'compile.log').write_text(r.stdout+r.stderr);r.check_returncode()
    exe=out/'simant-sweep.exe';cmd=report['application_link']['command'][:];cmd[cmd.index('-o')+1]=str(exe);cmd[1:1]=[str(obj),*['-Wl,--wrap='+n for n in ('enhanced_execute_next','enhanced_source_poll','native_workspace_proximity','enhanced_submit_pointer')]]
    r=subprocess.run(cmd,cwd=build,capture_output=True,text=True);(out/'link.log').write_text(r.stdout+r.stderr);r.check_returncode()
    for name in ('SDL3.dll','simant-build-id.txt'):shutil.copyfile(build/name,out/name)
    shutil.copytree(build/'runtime-bios-fonts',out/'runtime-bios-fonts');rows=[];inventories={}
    sessions=[];active=None
    class Session:
        def __init__(self,mode,lane,item):
            self.mode=mode;self.lane=lane;lane.mkdir();self.queue=queue.Queue();self.packets=[];self.start=time.monotonic();self.closed=False
            env={k:v for k,v in os.environ.items() if not k.startswith(('SIMANT_ENHANCED','SIMANT_SWEEP','SIMANT_WORKSPACE'))};env.update(SIMANT_SWEEP_SESSION='1',SIMANT_SWEEP_KIND=item['kind'],SIMANT_SWEEP_SETUP=item.get('setup',''),SIMANT_SWEEP_PARENT=item['parent'],SIMANT_SWEEP_ID=str(item['id']),SIMANT_SWEEP_X=str(item.get('x',0)),SIMANT_SWEEP_Y=str(item.get('y',0)),SIMANT_SWEEP_PATH=','.join(hex(n) for n in item.get('path',[])),SIMANT_SWEEP_OUTSIDE=str(item.get('outside',0)),SIMANT_WORKSPACE_LAYOUT=str(lane/'layout.txt'),SDL_AUDIODRIVER='dummy')
            script=lane/'input.txt';text=(ROOT/'portable/tests/runtime/windows-quick.txt').read_text();script.write_text(text.replace('207 58',{'quick':'207 58','full':'133 126','experimental':'50 190'}[mode]))
            self.assets=tempfile.TemporaryDirectory(prefix='assets-',dir=lane);shutil.copytree(build/'runtime-assets',self.assets.name,dirs_exist_ok=True)
            cmd=[str(exe),'--windows','--ui-scale','100','--deterministic','--seed','0','--assets',self.assets.name,'--input-script',str(script),'--smoke-ms','36000000','--diagnostics-dir='+str(lane/'diagnostics')]
            self.log=(lane/'run.log').open('w');self.process=subprocess.Popen(cmd,cwd=ROOT,env=env,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,bufsize=1)
            def reader():
                for line in self.process.stdout:self.log.write(line);self.log.flush();self.queue.put(line)
                self.queue.put(None)
            self.reader=threading.Thread(target=reader);self.reader.start();sessions.append(self)
        def read(self):
            controls=[];popups=[];deadline=time.monotonic()+110
            while True:
                try:line=self.queue.get(timeout=max(.01,deadline-time.monotonic()))
                except queue.Empty:self.close(kill=True);return dict(passed=False,result='timeout',exit_code='timeout'),controls
                if line is None:self.close();return dict(passed=False,result='incomplete',exit_code=self.process.returncode),controls
                if line.startswith('SWEEP_CONTROL '):controls.append(json.loads(line.split(' ',1)[1]))
                if line.startswith('SWEEP_POPUP '):popups.append(json.loads(line.split(' ',1)[1]))
                if line.startswith('SWEEP_RESULT '):
                    result=json.loads(line.split(' ',1)[1]);result.update(popup_items=popups,session=str(self.lane.relative_to(out)),exit_code=0)
                    if not result.get('reusable'):self.close();result['exit_code']=self.process.returncode;result['passed']&=self.process.returncode==0
                    return result,controls
        def send(self,item):
            fields=[item['kind'],item.get('setup',''),item['parent'],str(item['id']),str(item.get('x',0)),str(item.get('y',0)),','.join(hex(n) for n in item.get('path',[])),str(item.get('outside',0))]
            self.process.stdin.write('\t'.join(fields)+'\n');self.process.stdin.flush()
        def close(self,kill=False):
            if self.closed:return
            self.closed=True
            if kill:self.process.kill()
            else:
                try:self.process.stdin.close()
                except (BrokenPipeError,OSError):pass
            try:self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:self.process.kill();self.process.wait()
            self.reader.join();self.process.stdout.close();self.log.close();self.assets.cleanup();self.seconds=round(time.monotonic()-self.start,2)
    def run(mode,lane,item):
        nonlocal active
        if active and (active.closed or active.mode!=mode):active.close();active=None
        if active:active.send(item)
        else:active=Session(mode,lane,item)
        return active.read()
    for mode in a.modes.split(','):
        base=out/mode;base.mkdir();result,items=run(mode,base/'inventory',dict(kind='inventory',parent='',id=0));inventories[mode]=dict(result=result,items=items)
        if not result['passed']:rows.append(dict(mode=mode,kind='inventory',**result));continue
        selected={int(s,0) for s in a.ids.split(',')} if a.ids else None
        cases=list(items)
        for i,item in enumerate(cases):
            if selected is not None and item['id'] not in selected:continue
            if not item['enabled'] and not item.get('setup'):
                row=dict(mode=mode,**item,passed=True,result='disabled by source',exit_code=None)
            else:
                result,_=run(mode,base/(f'{i:03d}-{item["id"]:04x}'),item);row=dict(mode=mode,**item,**result)
            rows.append(row);print(mode,item['kind'],hex(item['id']),item['label'],row['result'],'PASS' if row['passed'] else 'FAIL',flush=True)
            path=item.get('path',[])
            for popup in row.get('popup_items',[]):
                if popup.get('depth',0)!=len(path) or len(path)>=8:continue
                child=dict(item,path=[*path,popup['id']],label=item['label']+' / '+popup['label'])
                if not popup['enabled']:rows.append(dict(mode=mode,**child,passed=True,result='disabled by source',exit_code=None));continue
                if popup['id'] not in path:
                    cases.append(child)
                    if popup['id'] in (0x706,0x2002,0x2004):cases.append(dict(child,outside=1,label=child['label']+' / outside cancel'))
        (out/'progress.json').write_text(json.dumps(dict(inventories=inventories,items=rows),indent=2)+'\n')
    if active:active.close()
    result=dict(seconds=round(time.monotonic()-started,2),startups=len(sessions),sessions=[dict(mode=s.mode,path=str(s.lane.relative_to(out)),seconds=s.seconds,exit_code=s.process.returncode) for s in sessions],passed=bool(rows) and all(r['passed'] for r in rows),complete=a.ids is None,inventories=inventories,items=rows,executable_sha256=sha(exe),probe_sha256=sha(source),scope='Live HWND child controls and recursive HMENU commands in each game mode; source-state-unchanged transactions reuse a session (all SaveRec bytes, source command/settings state, experimental substates and RNG); fresh game after a changed row; actual native messages, modal visibility/size/placement/cancel and subsequent native Pause delivery. Custom painted hit regions remain covered by action_equivalence and menus registrations.')
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');return int(not result['passed'])
if __name__=='__main__':raise SystemExit(main())
