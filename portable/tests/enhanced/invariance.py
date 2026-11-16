"""Passive off/on/repaint comparison using the established acceptance observer.

No expected state enters a child. Compare every raw named view (including every
SaveRec slice, RNG, logical stack and UI state), not just gameplay verdict views.
The ideal-state-v2 sidecar is retained for diagnosis but does not mask this check.
"""
import argparse, json, os, re, shutil, subprocess, sys, tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from portable.tests.enhanced.common import ROOT,check_build,probe_link
from portable.tests.acceptance.native_build import build_observer
from portable.tests.acceptance.step_state import schema,read_hashes,split_frame
from portable.tests.acceptance.native_schema import symbols_for
from portable.tests.acceptance.ideal_observation import prepare_schema,configuration
from portable.tests.acceptance.ideal_reference import validate
from portable.tests.acceptance.audio_commands import compare_commands

def differences(left,right,items):
    return [dict(entry=n,views=[v['name'] for v,a,b in zip(items,x,y) if a!=b])
            for n,(x,y) in enumerate(zip(left,right),1) if x!=y]

def observe(build,exe,state,out,mode,steps,hosted=False,workspace=False):
    out.mkdir();items=state['items'];anchor=symbols_for(exe).addresses['portable_test_observer_anchor']
    config=out/'observer.config'
    lines=['unused',str(out/'native.hash'),str(out/'observer.json'),str(out/'native.frame'),f'{len(items)} {steps}']
    for item in items:
        lines.append(f'1 {item["bytes"]} {int(item["sentinel"])} {len(item["slices"])}')
        lines.extend(f'{at-anchor} {size}' for at,size in item['slices'])
    config.write_text('\n'.join(lines)+'\n'+configuration(state,grouped=True))
    # One independently validated fixed machine profile; no time/state tape.
    refs=ROOT/'build/reference/sound-on-identity-v1/quick-game'
    candidates=sorted(refs.rglob('manifest.json'))
    reference=next(p.parent for p in candidates if json.loads(p.read_text()).get('target')=='original')
    validate(reference,ROOT/'dos/scenarios/quick-game.json')
    profile=json.loads((reference/'machine-profile.json').read_text())
    env={k:v for k,v in os.environ.items() if not k.startswith(('SIMANT_TEST_','SIMANT_ENHANCED','SIMANT_AUDIO_TRACE','SIMANT_IDEAL'))}
    env.pop('BUG',None)
    env.update(SIMANT_TEST_IDEAL='1',SIMANT_TEST_IDEAL_DGROUP=str(profile['irq09_dgroup']),
        SIMANT_TEST_STEP_CONFIG=str(config),SIMANT_TEST_AUDIO_COMMANDS=str(out/'audio.txt'),
        SIMANT_TEST_AUDIO_CONTENT=str(out/'content.txt'),SIMANT_TEST_DUMP_ENTRY='3')
    if mode!='off' or hosted:env['SIMANT_ENHANCED_CONTRACTS']='1'
    if hosted:env['SIMANT_ENHANCED_WORLD']='0' if mode=='off' else '1'
    env['SIMANT_ENHANCED_WORKSPACE']='0'
    if workspace:
        env.update(SIMANT_ENHANCED_CONTRACTS='1',SIMANT_ENHANCED_WORLD='1',SIMANT_ENHANCED_WORKSPACE='1',
            SIMANT_WORKSPACE_LAYOUT=str(out/'workspace.txt'),SDL_AUDIODRIVER='dummy')
        if mode=='stress':env.update(SIMANT_ENHANCED_LAYOUT_STRESS='1',SIMANT_ENHANCED_LAYOUT_ROUNDTRIP=str(out/'layout-roundtrip.txt'))
    if mode=='stress':env['SIMANT_ENHANCED_TEST']='stress'
    script=ROOT/'portable/tests/runtime/windows-quick.txt'
    scratch=ROOT/'build/workers/enhanced-build-a/temporary';scratch.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='a',dir=scratch) as folder:
        assets=Path(folder);shutil.copytree(build/'runtime-assets',assets,dirs_exist_ok=True)
        command=[str(exe),*([] if workspace else ['--headless']),'--deterministic','--seed','0','--assets',str(assets),
            '--input-script',str(script),'--diagnostics-dir='+str(out/'diagnostics'),
            '--smoke-ms','1000000']
        # Both use the exact same startup owner/pointer transform. Only the
        # world compositor is added in on/stress, as in the existing modern test.
        if hosted:command+=['--windows']
        else:command+=['--windows=200']
        with (out/'run.log').open('w') as log:
            run=subprocess.run(command,cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=180)
    actual=read_hashes(out/'native.hash',len(items)) if (out/'native.hash').is_file() else []
    if run.returncode or len(actual)!=steps:raise RuntimeError('Incomplete passive lane '+str(out))
    return actual

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--build',type=Path,default=ROOT/'build/current/portable')
    ap.add_argument('--out',type=Path,required=True);ap.add_argument('--steps',type=int,default=128)
    a=ap.parse_args();build=a.build.resolve();out=a.out.resolve();out.mkdir(parents=True,exist_ok=False)
    check_build(build);observer=build_observer(build,out/'observer-build')
    exe=probe_link(build,out/'test-build',observer)
    state=prepare_schema(schema(build,executable=exe))
    syms=symbols_for(exe)
    for field in ('logical_flags','object_counts','logical_rects','object_flags','menu_state'):
        address,size,pointer=syms.expression('enhanced_test_ui.'+field)
        if pointer:raise ValueError('UI projection contains native addresses')
        state['items'].append(dict(name='source-ui:'+field,bytes=size,verdict=True,category='game_state',
            slices=[[address,size]],sentinel=False,provenance='Test-only copy at the existing acceptance step seam; window reference registry and canonical menu bytes.'))
    (out/'views.json').write_text(json.dumps(state,indent=2)+'\n')
    groups=[]
    for name,hosted,workspace in (('contracts',False,False),('native-world',True,False),('workspace',True,True)):
        lanes={mode:observe(build,exe,state,out/(name+'-'+mode),mode,a.steps,hosted,workspace) for mode in ('off','on','stress')}
        lanes['repeat-off']=observe(build,exe,state,out/(name+'-repeat-off'),'off',a.steps,hosted,workspace)
        for mode in ('repeat-off','on','stress'):
            diffs=differences(lanes['off'],lanes[mode],state['items'])
            semantic=differences(read_hashes(out/(name+'-off/native.hash.ideal-state-v2'),len(state['items'])),
                read_hashes(out/(name+'-'+mode+'/native.hash.ideal-state-v2'),len(state['items'])),state['items'])
            audio=compare_commands(out/(name+'-off/audio.txt'),out/(name+'-'+mode+'/audio.txt'),out/(name+'-'+mode),
                entries=a.steps,replay_complete=True)
            clock_equal=(out/(name+'-off/native.hash.machine')).read_bytes()==(out/(name+'-'+mode+'/native.hash.machine')).read_bytes()
            observation=json.loads((out/(name+'-'+mode+'/observer.json')).read_text())
            first_values={}
            for entry in (1,3):
                left=split_frame(out/(name+f'-off/native.frame.{entry}'),state['items'])
                right=split_frame(out/(name+'-'+mode+f'/native.frame.{entry}'),state['items'])
                for field in left:
                    if left[field]==right[field]:continue
                    first_values.setdefault(field,dict(entry=entry,bytes=len(left[field]),
                        first_changed_byte=next(n for n,(a,b) in enumerate(zip(left[field],right[field])) if a!=b),
                        off_prefix=left[field][:64].hex(),other_prefix=right[field][:64].hex()))
            observed=(mode=='repeat-off' or observation.get('enhanced_generation',0)>0) and observation.get('enhanced_copy_errors')==0
            if mode=='stress':observed=observed and observation.get('enhanced_repaint_copies',0)>0 and observation.get('enhanced_repaint_renders',0)>0
            if workspace and mode=='stress':observed=observed and observation.get('enhanced_layout_operations',0)>=10 and observation.get('enhanced_native_layout_operations')==observation.get('enhanced_layout_operations') and observation.get('enhanced_layout_roundtrips')==observation.get('enhanced_layout_operations') and observation.get('enhanced_layout_errors')==0
            groups.append(dict(group=name,mode=mode,passed=not diffs and audio['status']=='AUDIO_COMMANDS_EQUAL' and clock_equal,
                differing_entries=len(diffs),first_difference=diffs[0] if diffs else None,
                all_differences=diffs,existing_projection_differences=semantic,audio=audio,clock_equal=clock_equal,
                observed=observed,observation=observation,first_values=first_values))
    # Detector control changes one observed SaveRec fingerprint offline.
    mutated=list(lanes['off']);row=list(mutated[0]);row[0]^=1;mutated[0]=tuple(row)
    negative=differences(lanes['off'],mutated,state['items'])
    detector_ok=bool(negative) and negative[0]['entry']==1 and negative[0]['views']==[state['items'][0]['name']]
    result=dict(passed=all(g['passed'] and g['observed'] for g in groups) and detector_ok,groups=groups,negative_control=detector_ok,
        entries=a.steps,views=len(state['items']),save_records=sum(i['name'].startswith('save:') for i in state['items']),
        exclusions=state['excluded'],layout='Workspace stationary/repeated controls and real Win32 edge attach/detach/move/resize/zoom/reset plus persistence roundtrips at source seams. UI input isolation and HWND keyboard checks are independently exercised by workspace.py. No masks added.',
        scope='Raw acceptance views, SaveRec projection, RNG, source UI/stack, clock and sound commands; unavailable private views stay explicit.')
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('groups','exclusions')},indent=2))
    for group in groups:print(group['group'],group['mode'],'PASS' if group['passed'] else 'DIFFERENCE',group['first_difference'])
    return int(not result['passed'])
if __name__=='__main__':raise SystemExit(main())
