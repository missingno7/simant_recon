"""Native proximity menus: real native selection versus original source choices."""
import argparse,json,os,re,shutil,subprocess,sys,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from portable.tests.enhanced.common import ROOT,check_build
from portable.tests.acceptance.state_schema import sha
from portable.tests.acceptance.step_state import schema,split_frame
from portable.tests.acceptance.native_schema import symbols_for

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--build',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--cases',default='ant:-2,ant:-1,ant:0,ant:1,ant-shift:1,ant:2,ant:3,ant:4,ant-keyboard:4,ant:5,scent:-1,scent:0,scent:1,scent:2,scent:3,scent:4,scent:5,tools:-1,tools:0,full-tools:-1,spider:-1,spider:0,spider:1,spider-alt:1,spider:2,spider:3,queen:-1,queen:0,queen:1,queen:2,magnify:-1');a=ap.parse_args();build=a.build.resolve();out=a.out.resolve();out.mkdir(parents=True,exist_ok=False);report=check_build(build);cc=report['application_link']['command'][0]
    source=Path(__file__).with_name('menu_probe.c');obj=out/'menu-probe.o';subprocess.run([cc,'-std=c11','-O2','-g','-I'+str(ROOT),'-I'+str(ROOT/'build/deps/sdl3-sdk/SDL3-3.4.16/x86_64-w64-mingw32/include'),'-c',str(source),'-o',str(obj)],check=True,capture_output=True)
    exe=out/'simant-menus.exe';link=report['application_link']['command'][:];link[link.index('-o')+1]=str(exe);link[1:1]=[str(obj),*['-Wl,--wrap='+n for n in ('enhanced_execute_next','enhanced_source_poll','native_workspace_proximity','native_workspace_manage_window','YellowCommand')]];p=subprocess.run(link,cwd=build,capture_output=True,text=True);(out/'link.log').write_text(p.stdout+p.stderr);p.check_returncode()
    for name in ('SDL3.dll','simant-build-id.txt'):shutil.copyfile(build/name,out/name)
    shutil.copytree(build/'runtime-bios-fonts',out/'runtime-bios-fonts');state=schema(build,executable=exe);anchor=symbols_for(exe).addresses['menu_observer_anchor'];items=state['items'];(out/'views.json').write_text(json.dumps(state,indent=2)+'\n');rows=[]
    with tempfile.TemporaryDirectory(prefix='m',dir=out) as folder:
        assets=Path(folder);shutil.copytree(build/'runtime-assets',assets,dirs_exist_ok=True)
        for case in a.cases.split(','):
            kind,choice=case.split(':');keyboard_cancel=kind.endswith('-keyboard');modifiers=2 if kind.endswith('-shift') else 8 if kind.endswith('-alt') else 0;case_dir=out/(kind+'-'+choice);kind=kind.removesuffix('-shift').removesuffix('-alt').removesuffix('-keyboard');case_dir.mkdir();lanes={};errors=[]
            for mode in ('original','native'):
                lane=case_dir/mode;lane.mkdir();config=lane/'config.txt';lines=[str(lane/'state'),str(len(items))]
                for item in items:lines.append(str(len(item['slices'])));lines.extend(f'{address-anchor} {size}' for address,size in item['slices'])
                config.write_text('\n'.join(lines)+'\n');env={k:v for k,v in os.environ.items() if not k.startswith(('SIMANT_ENHANCED','SIMANT_MENU','SIMANT_WORKSPACE','SIMANT_TEST_'))};env.update(SIMANT_WORKSPACE_LAYOUT=str(lane/'layout.txt'),SIMANT_MENU_KIND=kind,SIMANT_MENU_CHOICE=choice,SIMANT_MENU_MODIFIERS=str(modifiers),SIMANT_MENU_KEYBOARD_CANCEL=str(int(keyboard_cancel)),SIMANT_MENU_MODE=mode,SIMANT_MENU_CONFIG=str(config),SIMANT_MENU_CAPTURE=str(lane/'frame.bmp'),SDL_AUDIODRIVER='dummy')
                if mode=='original':env['SIMANT_ENHANCED_PROXIMITY']='0'
                script=ROOT/'portable/tests/runtime/windows-quick.txt'
                if kind in ('queen','full-tools'):script=lane/'input.txt';script.write_text((ROOT/'portable/tests/runtime/windows-quick.txt').read_text().replace('207 58','133 126'))
                cmd=[str(exe),'--deterministic','--windows','--seed','0','--assets',str(assets),'--input-script',str(script),'--smoke-ms','40000','--diagnostics-dir='+str(lane/'diagnostics')]
                with (lane/'run.log').open('w') as log:
                    try:p=subprocess.run(cmd,cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=55);code=p.returncode
                    except subprocess.TimeoutExpired:code='timeout'
                log=(lane/'run.log').read_text();results=re.findall(r'^MENU_RESULT (.*)$',log,re.M);observation=json.loads(results[-1]) if results else {'passed':False};opening=re.findall(r'^MENU_OPEN (.*)$',log,re.M)
                lanes[mode]=dict(code=code,observation=observation,opening=json.loads(opening[-1]) if opening else None)
                if code!=0 or not observation['passed'] or not (lane/'state.1').exists():errors.append(mode+':incomplete');continue
                lanes[mode]['before']=split_frame(lane/'state.0',items);lanes[mode]['after']=split_frame(lane/'state.1',items)
            comparisons={}
            if all('after' in lanes[m] for m in lanes):
                for slot in ('before','after'):
                    delta=[v['name'] for v in items if lanes['original'][slot][v['name']]!=lanes['native'][slot][v['name']]];comparisons[slot]=dict(raw_differences=delta,gameplay_differences=[v['name'] for v in items if v['verdict'] and v['name'] in delta])
            cancellation=None
            if int(choice)<0 and all('after' in data for data in lanes.values()):
                cancellation={mode:dict(save_changes=[v['name'] for v in items if v['name'].startswith('save:') and data['before'][v['name']]!=data['after'][v['name']]],command=data['observation'].get('command')) for mode,data in lanes.items()}
            for data in lanes.values():data.pop('before',None);data.pop('after',None)
            cancel_ok=cancellation is None or all(not data['save_changes'] and data['command']==-1 for data in cancellation.values())
            row=dict(case=case,passed=not errors and bool(comparisons) and cancel_ok and not any(c['gameplay_differences'] for c in comparisons.values()),errors=errors,comparisons=comparisons,cancellation=cancellation,lanes=lanes);rows.append(row);print(case,'PASS' if row['passed'] else 'FAIL',errors,flush=True)
    result=dict(passed=all(r['passed'] for r in rows),cases=rows,views=len(items),save_records=sum(v['name'].startswith('save:') for v in items),executable_sha256=sha(exe),scope='Current canonical source menu choices versus native Win32 menu input; every raw difference retained.');(out/'result.json').write_text(json.dumps(result,indent=2)+'\n');return int(not result['passed'])
if __name__=='__main__':raise SystemExit(main())
