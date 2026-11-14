"""Check stored original/canonical step references in native code, without GDB."""
import argparse
import json
import os
import shutil
import struct
import subprocess
import sys
import time
import tempfile
from pathlib import Path
try:
    from .state_schema import ROOT, sha, differences
    from .step_state import schema, read_hashes, split_frame
    from .full_inputs import full_tape, InputCoverageError
except ImportError:
    from state_schema import ROOT, sha, differences
    from step_state import schema, read_hashes, split_frame
    from full_inputs import full_tape, InputCoverageError

HERE=Path(__file__).resolve().parent


def test_build(build, out):
    """Link observation hooks, profiling two unchanged converted input-reader TUs."""
    report=json.loads((build/'report.json').read_text())
    profiled=[r for r in report['canonical_TUs'] if r['module'] in ('root:0250','root:1FD2')]
    if len(profiled)!=2:raise ValueError('Missing input-reader/scroll translation units')
    inputs={str(p):sha(p) for p in [build/'simant-canonical.exe',build/'report.json',HERE/'step_check.py',HERE/'native_observer.c',
            ROOT/'portable/whole_program/platform/sdl3/host.c',
            ROOT/'portable/whole_program/platform/sdl3/test_observer.inc',
            ROOT/'portable/whole_program/platform/sdl3/input_time_host.c',
            ROOT/'portable/whole_program/platform/m1b73_events.c',
            ROOT/'portable/whole_program/platform/m1b73_queue_runtime.c',
            ROOT/'portable/whole_program/platform/input_time.h',ROOT/'portable/whole_program/platform/input_time.c',ROOT/'portable/whole_program/platform/m1b73_main_input.c']}
    inputs.update({r['generated']:sha(Path(r['generated'])) for r in profiled})
    exe=out/'simant-step.exe';receipt=out/'observer-build.json'
    if receipt.is_file() and exe.is_file():
        old=json.loads(receipt.read_text())
        if old['inputs']==inputs and old['executable_sha256']==sha(exe): return exe
    out.mkdir(parents=True,exist_ok=True)
    # Refresh the optional platform hooks. The two profiled whole TUs below
    # keep their exact generated source; GCC adds entry/exit observations.
    response=(build/'application-objects.rsp').read_text()
    for filename in ('/sdl3/host.c','/sdl3/input_time_host.c','/m1b73_events.c','/input_time.c','/m1b73_main_input.c','/m1b73_queue_runtime.c'):
        host=next(r for r in report['native_services'] if r['source'].endswith(filename))
        obj=out/(Path(host['source']).stem+'.o')
        command=host['compile']['command'][:]
        command[command.index('-o')+1]=str(obj)
        subprocess.run(command,check=True,capture_output=True,timeout=60)
        response=response.replace(Path(host['object']).as_posix(),obj.as_posix())
    for unit in profiled:
        obj=out/(Path(unit['generated']).stem+'.o')
        command=unit['compile']['command'][:]+['-finstrument-functions']
        command[command.index('-o')+1]=str(obj)
        subprocess.run(command,check=True,capture_output=True,timeout=60)
        response=response.replace(Path(unit['object']).as_posix(),obj.as_posix())
    (out/'objects.rsp').write_text(response)
    observer_object=out/'native_observer.o'
    observer_compile=[report['application_link']['command'][0],'-std=c11','-O2','-g','-fno-lto','-c',str(HERE/'native_observer.c'),'-o',str(observer_object)]
    subprocess.run(observer_compile,check=True,capture_output=True,timeout=60)
    command=report['application_link']['command'][:]
    command=[('-Wl,@'+str(out/'objects.rsp')) if arg=='-Wl,@application-objects.rsp' else arg for arg in command]
    command[command.index('-o')+1]=str(exe)
    command[1:1]=[str(observer_object),'-Wl,--wrap=DoAntSim','-Wl,--wrap=MacTickCount']
    run=subprocess.run(command,cwd=build,capture_output=True,text=True,timeout=120)
    (out/'link.log').write_text(run.stdout+run.stderr)
    if run.returncode:raise RuntimeError('Observer link failed: '+run.stderr[-3000:])
    for filename in ('SDL3.dll','simant-build-id.txt'):
        shutil.copyfile(build/filename,out/filename)
    shutil.copytree(build/'runtime-bios-fonts',out/'runtime-bios-fonts',dirs_exist_ok=True)
    receipt.write_text(json.dumps(dict(inputs=inputs,executable_sha256=sha(exe),command=command,observer_compile=observer_compile,instrumented_units=[dict(module=r['module'],source=r['generated'],sha256=sha(Path(r['generated'])),flag='-finstrument-functions') for r in profiled]),indent=2)+'\n')
    return exe


def validate_reference(directory, scenario):
    manifest=json.loads((directory/'manifest.json').read_text())
    recipe=json.loads(scenario.read_text())
    if manifest['scenario_sha256']!=sha(scenario) or manifest['script_sha256']!=sha(ROOT/recipe['script']):
        raise ValueError('Stale reference scenario/script: '+str(directory))
    if not manifest['complete']:raise ValueError('Incomplete reference: '+str(directory))
    boundary=directory/'capture/boundary-manifest.json'
    if sha(boundary)!=manifest['boundary_manifest_sha256']:raise ValueError('Changed capture receipt')
    execution=directory/'capture/execution-report.json'
    if sha(execution)!=json.loads(boundary.read_text())['execution_report_sha256']:
        raise ValueError('Changed execution receipt')
    inputs=json.loads(execution.read_text())['inputs']
    for item in inputs:
        source=ROOT/item['path']
        if item['path'].startswith('assets/') or manifest['target']=='canonical' and item['path'].endswith('build-report.json'):
            if sha(source)!=item['sha256']:raise ValueError('Reference input changed: '+item['path'])
    for name, expected in manifest['files'].items():
        if sha(directory/name)!=expected:raise ValueError('Reference file hash differs: '+str(directory/name))
    return manifest


def step_inputs(receipt, destination):
    """Encode each actual IRQ at its completed global service position."""
    lines=[]
    for event in receipt['inputs']:
        op=event['description'].split();a=b=0;arg='-'
        if op[0] in ('key_down','key_up'):
            operation=op[0].replace('_','');arg=op[1]
        elif op[0]=='mouse_move':operation=op[0];a,b=map(int,op[1:3])
        elif op[0]=='mouse_button':operation=op[0];a=int(op[1]);arg=op[2]
        else:raise ValueError('Unsupported transition: '+str(op))
        position=event['pump']+event['clock_reads']+event.get('queries',0)+2*event['step']-event['phase']
        registers=event.get('registers',{})
        if event.get('delivery_kind')=='K' and any(k not in registers or not 0<=registers[k]<=65535 for k in ('cx','dx')):
            raise ValueError('Keyboard IRQ lacks captured CX/DX; re-record reference')
        cx,dx=(registers['cx'],registers['dx']) if event.get('delivery_kind')=='K' else (0,0)
        lines.append(f'{position} {event["step"]} {event["phase"]} {operation} {arg} {a} {b} {cx} {dx}\n')
    destination.write_text(''.join(lines))


def run_lane(scenario_path, reference, build, exe, out, timeout=180, disable=None,
             max_steps=None):
    """Compare native only with the executable whose own inputs it replays."""
    recipe=json.loads(scenario_path.read_text());manifest=validate_reference(reference,scenario_path)
    if out.exists():
        from tools.workspace import retire
        retire(out)
    out.mkdir(parents=True)
    if __package__:
        from .native_schema import symbols_for
    else:
        from native_schema import symbols_for
    state=schema(build,executable=exe);items=state['items'];count=len(items)
    if state['identity']!=manifest['schema_identity']:raise ValueError('Reference schema changed')
    expected=read_hashes(reference/'capture/observer.txt.hash',count)
    stop=min(manifest['steps'],max_steps or manifest['steps']);gap=None
    try:
        clocks,_,tape=full_tape(reference/'capture',exe,out,sha(scenario_path),sha(ROOT/recipe['script']),stop)
    except InputCoverageError as error:
        if error.step<1:raise
        gap=dict(step=error.step,reason=str(error));stop=min(stop,error.step)
        clocks,_,tape=full_tape(reference/'capture',exe,out,sha(scenario_path),sha(ROOT/recipe['script']),stop)
    if not tape.get('service_order'):raise ValueError('Reference lacks chronological service/input coordinates; re-record with the current observer')
    events=out/'inputs.txt';step_inputs(tape,events)
    anchor=symbols_for(exe).addresses['portable_test_clock_read']
    config=out/'observer.config'
    lines=[str(reference/'capture/observer.txt.hash'),str(out/'native.hash'),str(out/'native-result.json'),str(out/'native.frame'),f'{count} {stop}']
    for item in items:
        lines.append(f'{int(item["verdict"])} {item["bytes"]} {int(item["sentinel"])} {len(item["slices"])}')
        lines.extend(f'{address-anchor} {size}' for address,size in item['slices'])
    config.write_text('\n'.join(lines)+'\n')
    replay=out/'idle.txt';replay.write_text('18446744073709551615 exit\n')
    env={k:v for k,v in os.environ.items() if not k.startswith('SIMANT_TEST_')}
    env.update(SIMANT_TEST_STEP_CONFIG=str(config),SIMANT_TEST_FULL_CLOCK=str(clocks),
               SIMANT_TEST_SERVICE_INPUT=str(events))
    if tape.get('service_order'):env['SIMANT_TEST_SERVICE_ORDER']=tape['service_order']
    if os.environ.get('SIMANT_ADMISSION_TRACE'):env['SIMANT_TEST_ORDER_OUTPUT']=str(out/'native.order')
    if disable=='input':env.pop('SIMANT_TEST_SERVICE_INPUT')
    if disable=='clock':env['SIMANT_TEST_DISABLE_CLOCK']='1'
    if disable=='irq-context':env['SIMANT_TEST_DISABLE_IRQ_CONTEXT']='1'
    if disable=='clock':
        import re
        text=subprocess.check_output(['C:/msys64/mingw64/bin/objdump.exe','-d','--disassemble=dos_game_main',str(exe)],text=True)
        calls=[int(a,16)+len(raw.split()) for a,raw in re.findall(r'^\s*([0-9a-f]+):\s+((?:[0-9a-f]{2} )+)\s*call\s+[^\n]*<__wrap_MacTickCount>',text,re.M)]
        if len(calls)!=3:raise ValueError('Expected the three source pacing calls in main')
        env['SIMANT_TEST_PACING_CALLS']=','.join(str(pc-anchor) for pc in calls)
    command=[str(exe),'--headless','--deterministic','--poll-ns','1',
             '--assets','{assets}','--input-script',str(replay),*recipe.get('arguments',[])]
    # The original FileSelect path domain is 67 characters, including filename.
    # Keep disposable resources short even when diagnostic output is deeply nested.
    with tempfile.TemporaryDirectory(prefix='a',dir=ROOT/'build/workers/admission') as resource_dir:
        assets=Path(resource_dir).resolve()
        if not assets.is_relative_to(ROOT/'build/workers/admission') or len(str(assets/'a.ant'))>67:
            raise ValueError('Disposable assets exceed original FileSelect path domain')
        shutil.copytree(build/'runtime-assets',assets,dirs_exist_ok=True)
        command[command.index('{assets}')]=str(assets)
        start=time.perf_counter();timed_out=False
        with (out/'native.log').open('w') as log:
            try:r=subprocess.run(command,cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=timeout);code=r.returncode
            except subprocess.TimeoutExpired:timed_out=True;code=None
        elapsed=time.perf_counter()-start
        for saved in assets.glob('*.ANT'):shutil.copyfile(saved,out/saved.name)
    actual=read_hashes(out/'native.hash',count) if (out/'native.hash').is_file() else []
    result=dict(scenario=recipe['id'],reference_target=manifest['target'],status='INCOMPLETE',
        steps_compared=len(actual),reference_steps=manifest['steps'],requested_steps=stop,
        first_differing_step=None,game_differences=[],separate_differences={},
        native_seconds=elapsed,command=command,exit_code=code,timed_out=timed_out,
        negative_control=disable,excluded=state['excluded'])
    if gap:result['input_coverage_gap']=gap
    if (out/'native-result.json').is_file() and (out/'native-result.json').stat().st_size:result['diagnostics']=json.loads((out/'native-result.json').read_text())
    for step,native in enumerate(actual,1):
        for item,e,n in zip(items,expected[step-1],native):
            if e==n:continue
            row=dict(step=step,name=item['name'],reference_hash=e,native_hash=n)
            if item['verdict']:
                if result['first_differing_step'] is None:result['first_differing_step']=step
                if step==result['first_differing_step']:result['game_differences'].append(row)
            else:result['separate_differences'].setdefault(item['name'],dict(row,category=item['category']))
        if result['first_differing_step'] is not None:break
    if result['game_differences']:
        result['status']='STATE_DIFFERENCE'
        frames=list((reference/'capture').glob('observer.txt.frame.*'))
        nearest=min(frames,key=lambda p:abs(int(p.name.rsplit('.',1)[1])-result['first_differing_step']))
        baseline=split_frame(nearest,items);observed=split_frame(out/'native.frame',items)
        for row in result['game_differences']:
            row['nearest_reference_dump']=dict(step=int(nearest.name.rsplit('.',1)[1]),diff=differences(baseline[row['name']],observed[row['name']]))
    elif len(actual)==stop and code==0 and not gap:result['status']='REFERENCE_EQUAL'
    else:result['first_missing_step']=len(actual)+1
    import re
    extra=re.search(r'Observer extra clock read: (\w) (-?\d+)',(out/'native.log').read_text())
    if extra:
        result['replay_failure']=next((b for b in tape['bindings'] if b['kind']==extra[1] and b['native_delta']==int(extra[2])),dict(kind=extra[1],delta=int(extra[2])))
    admissions={}
    for line in (out/'native.log').read_text().splitlines():
        p=line.split()
        if p[:2]==['Observer','phase']:
            admissions[int(p[2])]=dict(step=int(p[3]),phase=int(p[4]),queries=int(p[5]),services=int(p[6]),clock_reads=int(p[7]),pump=int(p[8]),position={})
        elif p[:2]==['Observer','position']:
            admissions[int(p[2])]['position'][p[3]+':'+p[4]]=int(p[5])
    phase_errors=[];position_errors=[]
    for sequence,observed in admissions.items():
        expected_input=tape['inputs'][sequence-1]
        observed['expected']=dict(step=expected_input['step'],phase=expected_input['phase'],position=expected_input['position'],queries=expected_input.get('queries',0),clock_reads=expected_input['clock_reads'],pump=expected_input['pump'])
        if tape.get('service_order'):
            expected_service=expected_input['clock_reads']+expected_input['pump']+expected_input.get('queries',0)+2*expected_input['step']-expected_input['phase']
            if (observed['services']!=expected_service or observed['clock_reads']!=expected_input['clock_reads'] or
                observed['pump']!=expected_input['pump'] or observed['queries']!=expected_input.get('queries',0) or
                any(observed['position'].get(k,0)!=v for k,v in expected_input['position'].items())):
                position_errors.append(sequence)
        if (observed['step'],observed['phase'])!=(expected_input['step'],expected_input['phase']):
            phase_errors.append(dict(sequence=sequence,observed_step=observed['step'],observed_phase=observed['phase'],
                expected_step=expected_input['step'],expected_phase=expected_input['phase']))
    (out/'input-admission.json').write_text(json.dumps(admissions,indent=2)+'\n')
    result['input_phase_differences']=phase_errors
    result['input_position_differences']=position_errors
    if phase_errors or position_errors:result['status']='INCOMPLETE'
    service_error=re.search(r'Observer service order mismatch at ([^\n]+)',(out/'native.log').read_text())
    if service_error:result['service_order_failure']=service_error[1]
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    return result


def attribute(original,canonical):
    if canonical['status']=='STATE_DIFFERENCE':return 'PORT_INTRODUCED'
    if canonical['status']=='REFERENCE_EQUAL' and original['status']=='STATE_DIFFERENCE':return 'RECONSTRUCTION_INTRODUCED'
    if original['status']==canonical['status']=='REFERENCE_EQUAL':return 'ORIGINAL_EQUAL_ALL'
    return 'UNATTRIBUTED'


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('scenario',type=Path,nargs='*')
    default=ROOT/'build/workers/admission/native-final'
    if not (default/'report.json').is_file():default=ROOT/'build/current/portable'
    ap.add_argument('--build',type=Path,default=default)
    ap.add_argument('--reference-root',type=Path,default=ROOT/'build/reference')
    ap.add_argument('--original',type=Path);ap.add_argument('--canonical',type=Path)
    ap.add_argument('--out',type=Path,default=ROOT/'build/workers/admission/check')
    ap.add_argument('--timeout',type=int,default=30)
    ap.add_argument('--steps',type=int,help='Explicit prefix control; default is the complete reference')
    ap.add_argument('--disable',choices=('clock','input','irq-context'))
    a=ap.parse_args();scenarios=a.scenario or sorted((ROOT/'dos/scenarios').glob('*.json'))
    if not (ROOT/'assets/SIMANT.EXE').is_file() or not (a.build/'report.json').is_file():
        for p in scenarios:print(p.stem+': no reference (assets/native build absent)')
        return 0
    exe=None;failed=False
    for path in scenarios:
        refs={'original':a.original,'canonical':a.canonical}
        if refs['original'] is None:
            for p in (a.reference_root/path.stem).glob('*/manifest.json'):
                m=json.loads(p.read_text())
                boundary=p.parent/'capture/boundary-manifest.json'
                if (m['target'] in refs and boundary.is_file() and
                    json.loads(boundary.read_text())['compact_observer'].get('order_contract')=='service-samples-v4'):
                    refs[m['target']]=p.parent
        if not all(refs.values()):print(path.stem+': no reference');continue
        try:
            for ref in refs.values():validate_reference(ref,path)
        except (ValueError,FileNotFoundError) as error:
            print(path.stem+': no reference ('+str(error)+')');continue
        if exe is None:exe=test_build(a.build.resolve(),a.out.resolve()/'test-build')
        lanes={}
        for target,ref in refs.items():
            try:lanes[target]=run_lane(path.resolve(),ref.resolve(),a.build.resolve(),exe,a.out.resolve()/path.stem/target,a.timeout,a.disable,a.steps)
            except ValueError as error:lanes[target]=dict(status='INCOMPLETE',steps_compared=0,tape_error=str(error))
        verdict=attribute(lanes['original'],lanes['canonical'])
        row=dict(scenario=path.stem,verdict=verdict,lanes=lanes)
        destination=a.out.resolve()/path.stem;destination.mkdir(parents=True,exist_ok=True)
        (destination/'result.json').write_text(json.dumps(row,indent=2)+'\n')
        detail=[]
        for target,lane in lanes.items():
            names=','.join(d['name'] for d in lane.get('game_differences',[])[:5]) or '-'
            if lane['status']=='INCOMPLETE':
                failure=lane.get('replay_failure',{})
                cause=('clock='+failure['name']+'['+str(failure.get('call_index','?'))+']') if failure.get('name') else 'timeout' if lane.get('timed_out') else 'service order: '+lane['service_order_failure'] if lane.get('service_order_failure') else 'input/binding coverage'
                detail.append(f'{target}={lane["steps_compared"]}/{lane.get("reference_steps","?")} INCOMPLETE missing={lane.get("first_missing_step","?")} {cause}')
            else:
                detail.append(f'{target}={lane["steps_compared"]}/{lane.get("reference_steps","?")} {lane["status"]} first={lane.get("first_differing_step") or "-"} {names}')

        print(path.stem+': '+verdict+' '+ '; '.join(detail),flush=True)
        failed|=verdict!='ORIGINAL_EQUAL_ALL'
    return int(failed)

if __name__=='__main__':raise SystemExit(main())
