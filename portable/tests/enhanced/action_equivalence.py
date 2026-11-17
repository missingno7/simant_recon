"""Compare original event delivery with actual picture buttons and keyboard input.

Retains every raw view. The existing acceptance policy identifies gameplay views;
no new masks, expected states, or debugger memory writes are introduced.
"""
import argparse,json,os,re,shutil,subprocess,sys,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from portable.tests.enhanced.common import ROOT,check_build
from portable.tests.acceptance.step_state import schema,split_frame
from portable.tests.acceptance.native_schema import symbols_for

# Independent original control census from the approved relocation table.
CONTROLS=[(4,n) for n in [5,6,7,8,9,10,11,12,13,14,15,16,*range(0x105,0x119),0xe310,0xe311,*range(0xfd43,0xfd47)]]+[(0,0xe400)]+[(5,n) for n in [0x1907,0x1908,0xfd22,0x1909,0x190a,0x190b,0x1910,0x1911,0x190d,0x190e]]
# Both ordinary panels expose warning meters; exercise each HWND independently.
CONTROLS += [(5,0xe310),(5,0xe311)]
# Original Map/triangle/world/Yard hit transactions, including a 300% world.
CONTROLS += [(6,n) for n in range(0xe500,0xe508)]+[(6,n) for n in range(0xe510,0xe518)]
CONTROLS += [(6,n) for n in range(0xe518,0xe51c)] # queen wait and Info link/Previous/Top
CONTROLS += [(p,base+i) for p,base in ((8,0x1200),(9,0x1300)) for i in (3,4,5,6,7,8,15)]
CONTROLS += [(10,n) for n in range(0x1503,0x150d)]
CONTROLS += [(20,n) for n in range(0xfd31,0xfd37)] # menu-only source options
MENUS={8:0xfd26,9:0xfd27,10:0xfd28,15:0xfd41,0x10f:0xfd13,0x111:0xfd14,0x113:0xfd15,0x114:0xfd17,0x115:0xfd16,0x1909:0xfd23,0x190a:0xfd24,0xfd22:0xfd22,**{n:n for n in range(0xfd43,0xfd47)}}

def command(cmd,**kw):
 r=subprocess.run(cmd,capture_output=True,text=True,timeout=120,**kw)
 if r.returncode:raise RuntimeError(r.stdout[-1000:]+r.stderr[-2000:])
 return r

def differing(a,b,items):return [item['name'] for item in items if a[item['name']]!=b[item['name']]]

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--build',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--events');a=ap.parse_args();build=a.build.resolve();out=a.out.resolve();out.mkdir(parents=True,exist_ok=False);report=check_build(build);cc=report['application_link']['command'][0]
 obj=out/'action-probe.o';command([cc,'-std=c11','-O2','-g','-I'+str(ROOT),'-I'+str(ROOT/'build/deps/sdl3-sdk/SDL3-3.4.16/x86_64-w64-mingw32/include'),'-c',str(Path(__file__).with_name('action_probe.c')),'-o',str(obj)])
 exe=out/'simant-actions.exe';link=report['application_link']['command'][:];link[link.index('-o')+1]=str(exe);link[1:1]=[str(obj),'-Wl,--wrap=enhanced_execute_next','-Wl,--wrap=enhanced_source_poll','-Wl,--wrap=myButton','-Wl,--wrap=processExp','-Wl,--wrap=YellowCommand'];command(link,cwd=build)
 for n in ('SDL3.dll','simant-build-id.txt'):shutil.copyfile(build/n,out/n)
 shutil.copytree(build/'runtime-bios-fonts',out/'runtime-bios-fonts');state=schema(build,executable=exe);anchor=symbols_for(exe).addresses['action_observer_anchor'];items=state['items'];(out/'views.json').write_text(json.dumps(state,indent=2)+'\n');results=[];baseline_for_negative=None
 chosen={int(n,0) for n in a.events.split(',')} if a.events else None
 scratch=ROOT/'build/workers/enhanced-menus/temporary';scratch.mkdir(parents=True,exist_ok=True)
 with tempfile.TemporaryDirectory(prefix='eq',dir=scratch) as folder:
  assets=Path(folder);shutil.copytree(build/'runtime-assets',assets,dirs_exist_ok=True)
  for panel,event in CONTROLS:
   if chosen is not None and event not in chosen:continue
   case=out/(f'{event:04x}'+('-yard' if panel==5 and event in (0xe310,0xe311) else ''));case.mkdir();lanes={};errors=[]
   for mode in (['original','menu'] if panel==20 else ['original','panel'] if event==0xe400 or 0xe500<=event<=0xe51b else ['original','panel','keyboard'])+(['menu'] if event in MENUS else [])+(['coalesced'] if event==0xe514 else []):
    lane=case/mode;lane.mkdir();config=lane/'config.txt';lines=[str(lane/'state'),str(len(items))]
    for item in items:
     lines.append(str(len(item['slices'])));lines.extend(f'{address-anchor} {size}' for address,size in item['slices'])
    config.write_text('\n'.join(lines)+'\n');actual=MENUS.get(event,event) if mode=='menu' else event
    env={k:v for k,v in os.environ.items() if not k.startswith(('SIMANT_ENHANCED','SIMANT_ACTION','SIMANT_WORKSPACE','SIMANT_TEST_'))};env.update(SIMANT_ENHANCED_CONTRACTS='1',SIMANT_ENHANCED_WORKSPACE='1',SIMANT_WORKSPACE_LAYOUT=str(lane/'layout.txt'),SIMANT_ACTION_CONFIG=str(config),SIMANT_ACTION_EVENT=hex(actual),SIMANT_ACTION_PANEL=str(panel),SIMANT_ACTION_MODE=mode,SDL_AUDIODRIVER='dummy',SIMANT_ENHANCED_PROXIMITY='0')
    cmd=[str(exe),'--deterministic','--windows','--seed','0','--assets',str(assets),'--input-script',str(ROOT/'portable/tests/runtime/windows-quick.txt'),'--smoke-ms','30000','--diagnostics-dir='+str(lane/'diagnostics')]
    with (lane/'run.log').open('w') as log:
     try:r=subprocess.run(cmd,cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=45)
     except subprocess.TimeoutExpired:errors.append(mode+':timeout');continue
    observations=re.findall(r'^ACTION_RESULT (.*)$',(lane/'run.log').read_text(),re.M)
    if r.returncode or not observations or not (lane/'state.1').is_file():errors.append(mode+':incomplete');continue
    lanes[mode]=dict(before=split_frame(lane/'state.0',items),after=split_frame(lane/'state.1',items),observation=json.loads(observations[-1]))
   comparisons=[]
   if 'original' in lanes:
    baseline_for_negative=lanes['original']['after']
    for mode,data in lanes.items():
     if mode in ('original','coalesced'):continue
     before=differing(lanes['original']['before'],data['before'],items);after=differing(lanes['original']['after'],data['after'],items);game=[v['name'] for v in items if v['verdict'] and v['name'] in before];game_after=[v['name'] for v in items if v['verdict'] and v['name'] in after]
     comparisons.append(dict(mode=mode,passed=not game and not game_after,before_raw_differences=before,after_raw_differences=after,before_gameplay_differences=game,after_gameplay_differences=game_after,observation=data['observation']))
   coalescing=None
   if event==0xe514 and 'original' in lanes and 'coalesced' in lanes:
    delta=differing(lanes['original']['after'],lanes['coalesced']['after'],items);coalescing=dict(passed=any(v['name'] in delta and v['name'].startswith('save:') for v in items),raw_differences=delta)
   row=dict(coalescing_negative_control=coalescing,event=f'{event:04x}',panel=panel,passed=(event!=0xe514 or bool(coalescing and coalescing['passed'])) and not errors and len(comparisons)==(1 if panel==20 or event==0xe400 or 0xe500<=event<=0xe51b else 3 if event in MENUS else 2) and all(c['passed'] for c in comparisons),errors=errors,comparisons=comparisons,menu_equivalent='registered original menu command' if event in MENUS or panel==20 else 'no corresponding game menu item');results.append(row);(case/'result.json').write_text(json.dumps(row,indent=2)+'\n');print(row['event'],'PASS' if row['passed'] else 'DIFFERENCE / INCOMPLETE',errors,flush=True)
 negative=False
 if baseline_for_negative:
  first=next(v for v in items if v['name'].startswith('save:'));mutated=dict(baseline_for_negative);data=bytearray(mutated[first['name']]);data[0]^=1;mutated[first['name']]=bytes(data);negative=differing(baseline_for_negative,mutated,items)==[first['name']]
 menu_result=None
 if chosen is None:
  menu_out=out/'proximity-menus'
  with (out/'proximity-menus.log').open('w') as log:
   menu_run=subprocess.run([sys.executable,str(Path(__file__).with_name('menus.py')),'--build',str(build),'--out',str(menu_out)],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
  menu_result=json.loads((menu_out/'result.json').read_text()) if (menu_out/'result.json').exists() else dict(passed=False,error='incomplete',code=menu_run.returncode)
 result=dict(passed=bool(results) and all(r['passed'] for r in results) and negative and (menu_result is None or menu_result['passed']),proximity_menus=menu_result,controls=results,views=len(items),save_records=sum(v['name'].startswith('save:') for v in items),negative_control=negative,
  scope='Native current-source original event paths versus real native HWND controls and keyboard. This is not execution of the original DOS executable. All raw differences retained.',
  missing_coverage=['File/About lifecycle menu transactions remain the step C compatibility path; no original-executable action matrix is claimed.']);(out/'result.json').write_text(json.dumps(result,indent=2)+'\n');return int(not result['passed'])
if __name__=='__main__':raise SystemExit(main())
