"""Census and bounded interaction of every live native panel control/menu item.

Quick, Full and Experimental inventories are taken from their actual HWND/HMENU
trees. Each enabled item runs in a fresh game. Modal completion is tested through
real native Esc/outside messages, followed by a second actual Pause button input.
"""
import argparse,json,os,re,shutil,subprocess,sys,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from portable.tests.enhanced.common import ROOT,check_build
from portable.tests.acceptance.state_schema import sha
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--build',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--modes',default='quick,full,experimental');p.add_argument('--ids',help='Preflight subset; full registration omits this');a=p.parse_args()
    build=a.build.resolve();out=a.out.resolve();out.mkdir(parents=True,exist_ok=False);report=check_build(build);cc=report['application_link']['command'][0]
    source=Path(__file__).with_name('sweep_probe.c');obj=out/'probe.o';r=subprocess.run([cc,'-std=c11','-O2','-g','-I'+str(ROOT),'-I'+str(ROOT/'build/deps/sdl3-sdk/SDL3-3.4.16/x86_64-w64-mingw32/include'),'-c',str(source),'-o',str(obj)],capture_output=True,text=True);(out/'compile.log').write_text(r.stdout+r.stderr);r.check_returncode()
    exe=out/'simant-sweep.exe';cmd=report['application_link']['command'][:];cmd[cmd.index('-o')+1]=str(exe);cmd[1:1]=[str(obj),*['-Wl,--wrap='+n for n in ('enhanced_execute_next','enhanced_source_poll','native_workspace_proximity')]]
    r=subprocess.run(cmd,cwd=build,capture_output=True,text=True);(out/'link.log').write_text(r.stdout+r.stderr);r.check_returncode()
    for name in ('SDL3.dll','simant-build-id.txt'):shutil.copyfile(build/name,out/name)
    shutil.copytree(build/'runtime-bios-fonts',out/'runtime-bios-fonts');rows=[];inventories={}
    def run(mode,lane,item):
        lane.mkdir();env={k:v for k,v in os.environ.items() if not k.startswith(('SIMANT_ENHANCED','SIMANT_SWEEP','SIMANT_WORKSPACE'))};env.update(SIMANT_SWEEP_KIND=item['kind'],SIMANT_SWEEP_SETUP=item.get('setup',''),SIMANT_SWEEP_PARENT=item['parent'],SIMANT_SWEEP_ID=str(item['id']),SIMANT_SWEEP_X=str(item.get('x',0)),SIMANT_SWEEP_Y=str(item.get('y',0)),SIMANT_SWEEP_PATH=','.join(hex(n) for n in item.get('path',[])),SIMANT_SWEEP_OUTSIDE=str(item.get('outside',0)),SIMANT_WORKSPACE_LAYOUT=str(lane/'layout.txt'),SDL_AUDIODRIVER='dummy')
        script=lane/'input.txt';text=(ROOT/'portable/tests/runtime/windows-quick.txt').read_text();point={'quick':'207 58','full':'133 126','experimental':'50 190'}[mode];script.write_text(text.replace('207 58',point))
        with tempfile.TemporaryDirectory(prefix='assets-',dir=lane) as folder:
            assets=Path(folder);shutil.copytree(build/'runtime-assets',assets,dirs_exist_ok=True)
            cmd=[str(exe),'--windows','--deterministic','--seed','0','--assets',str(assets),'--input-script',str(script),'--smoke-ms','90000','--diagnostics-dir='+str(lane/'diagnostics')]
            with (lane/'run.log').open('w') as log:
                try:r=subprocess.run(cmd,cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=110);code=r.returncode
                except subprocess.TimeoutExpired:code='timeout'
        log=(lane/'run.log').read_text();matches=re.findall(r'^SWEEP_RESULT (.*)$',log,re.M);result=json.loads(matches[-1]) if matches else dict(passed=False,result='incomplete');result.update(exit_code=code);result['passed']=result['passed'] and code==0
        result['popup_items']=[json.loads(s) for s in re.findall(r'^SWEEP_POPUP (.*)$',log,re.M)]
        return result,[json.loads(s) for s in re.findall(r'^SWEEP_CONTROL (.*)$',log,re.M)]
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
    result=dict(passed=bool(rows) and all(r['passed'] for r in rows),complete=a.ids is None,inventories=inventories,items=rows,executable_sha256=sha(exe),probe_sha256=sha(source),scope='Live HWND child controls and recursive HMENU commands in each game mode; separate game per enabled target; actual native messages, modal visibility/size/placement/cancel and subsequent native Pause delivery. Custom painted hit regions remain covered by action_equivalence and menus registrations.')
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');return int(not result['passed'])
if __name__=='__main__':raise SystemExit(main())
