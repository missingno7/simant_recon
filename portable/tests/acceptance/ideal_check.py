"""Compare tick-scripted, unpaced native runs with ideal-v1 DOS observations.

No clock values, service order, IRQ schedule/context, sound-call boundaries or
device answers are replayed. Expected state is read only after the run exits.
"""
import argparse,json,os,shutil,struct,subprocess,sys,tempfile,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
from portable.tests.acceptance.state_schema import sha,differences
from portable.tests.acceptance.step_state import schema,bind_reference_policy,read_hashes,split_frame
from portable.tests.acceptance.ideal_reference import validate,script_path
from portable.tests.acceptance.native_build import build_observer
from portable.tests.acceptance.native_schema import symbols_for
from portable.tests.acceptance.frame_check import compare_frames
from portable.tests.acceptance.audio_commands import compare_commands,read_commands
from portable.tests.acceptance.audio_content import compare_content
from portable.tests.acceptance.sound_off import select_config
from portable.tests.acceptance.ideal_observation import prepare_schema,configuration,context_views,identity_views


def native_script(source,destination):
    lines=['# clock: bios-ticks']
    for line in source.read_text().splitlines():
        parts=line.split('#',1)[0].split()
        if not parts:continue
        tick,operation,*args=parts
        if operation in ('keydown','keyup'):row=[tick,'down' if operation=='keydown' else 'up',*args]
        elif operation=='mouse_move':row=[tick,'relative',*args]
        elif operation=='mouse_button':row=[tick,'button-'+args[1],['Left','Right','Middle'][int(args[0])]]
        elif operation=='exit':row=[tick,'exit']
        else:raise ValueError('Unsupported tick input: '+line)
        lines.append(' '.join(row))
    destination.write_text('\n'.join(lines)+'\n')

def lane(scenario,reference,build,exe,out,timeout=600,steps=None,prepared=None,scratch_root=None,dump_entry=None,playback=False,trace_reads=False,playback_tolerance_ns=None):
    lane_started=time.perf_counter();timings={};mark=lane_started
    def elapsed(name):
        nonlocal mark
        now=time.perf_counter();timings[name]=now-mark;mark=now
    manifest=validate(reference,scenario);recipe=json.loads(scenario.read_text())
    sound_off=manifest.get('variant')=='sound-off'
    elapsed('reference_validation')
    out=out.resolve();out.mkdir(parents=True,exist_ok=False)
    if prepared:
        native=json.loads(prepared.read_text())
        if native['executable_sha256']!=sha(exe) or native['sound_off']!=sound_off:
            raise ValueError('Prepared native observer identity differs')
        state=native['state'];anchor=native['anchor'];palette=native['palette']
    else:
        state=prepare_schema(schema(build,executable=exe))
        syms=symbols_for(exe);anchor=syms.addresses['portable_test_observer_anchor'];palette=syms.expression('app.palette')[0]
    state=bind_reference_policy(state,json.loads((reference/'schema.json').read_text()))
    elapsed('schema')
    items=state['items'];count=len(items);stop=min(steps or manifest['steps'],manifest['steps'])
    profile=json.loads((reference/'machine-profile.json').read_text())
    config=out/'observer.config'
    # First line is intentionally not an expected-state file. Ideal observation
    # mode never opens it. All remaining lines describe output and native views.
    lines=['unused',str(out/'native.hash'),str(out/'native-result.json'),str(out/'native.frame'),f'{count} {stop}']
    for item in items:
        lines.append(f'{2 if item["category"]=="audio" else int(item["verdict"])} {item["bytes"]} {int(item["sentinel"])} {len(item["slices"])}')
        lines.extend(f'{at-anchor} {size}' for at,size in item['slices'])
    config.write_text('\n'.join(lines)+'\n')
    context=context_views(state);identities=identity_views(state)
    with config.open('a') as target:target.write(configuration(state,grouped=True))
    checkpoints=[s for s in manifest['frames']['entries'] if s<=stop]
    frames=out/'frames.config';frames.write_text(str(out)+'\n'+f'{palette-anchor} {len(checkpoints)}\n'+' '.join(map(str,checkpoints))+'\n')
    script=out/'input.txt';native_script(script_path(scenario),script)
    env={k:v for k,v in os.environ.items() if not k.startswith(('SIMANT_TEST_','SIMANT_IDEAL','SIMANT_AUDIO_TRACE'))}
    # BUG is the canonical startup's sole getenv query. PATH/COMSPEC in the
    # profile describe DOS loading, not the host runtime loader's namespace.
    env.pop('BUG',None)
    for variable in profile.get('dos_environment',[]):
        name,separator,value=variable.partition('=')
        if separator and name.upper()=='BUG':env['BUG']=value
    env.update(SIMANT_TEST_IDEAL='1',SIMANT_TEST_IDEAL_DGROUP=str(profile['irq09_dgroup']),
        SIMANT_TEST_STEP_CONFIG=str(config),SIMANT_TEST_FRAME_CONFIG=str(frames),
        SIMANT_TEST_AUDIO_COMMANDS=str(out/'audio-commands.txt'),SIMANT_TEST_AUDIO_CONTENT=str(out/'audio-content.txt'))
    if trace_reads:env['SIMANT_TEST_READ_TRACE']=str(out/'charged-reads.txt')
    if playback:
        env['SIMANT_TEST_PLAYBACK']='1'
    if dump_entry:
        if not 1<=dump_entry<=stop:raise ValueError('Dump entry outside observed prefix')
        env['SIMANT_TEST_DUMP_ENTRY']=str(dump_entry)
    elapsed('observer_configuration')
    scratch=scratch_root or ROOT/'build/scratch/ideal';scratch.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='a',dir=scratch) as resource:
        assets=Path(resource).resolve()
        if len(str(assets/'A.ANT'))>67:raise ValueError('Original FileSelect path domain exceeded')
        shutil.copytree(build/'runtime-assets',assets,dirs_exist_ok=True)
        if sound_off:
            config_file=assets/'SIMANT.CFG'
            config_file.write_bytes(select_config(config_file.read_bytes()))
            if sha(config_file)!=manifest['sound_configuration']['selected_sha256']:
                raise ValueError('Native/DOS no-sound config bytes differ')
        if recipe.get('saved_game'):shutil.copyfile(ROOT/recipe['saved_game'],assets/Path(recipe['saved_game']).name)
        command=[str(exe),'--headless','--deterministic','--assets',str(assets),'--input-script',str(script),*recipe.get('arguments',[])]
        elapsed('assets')
        started=time.perf_counter();timed_out=False
        with (out/'native.log').open('w') as log:
            try:
                if os.environ.get('SIMANT_IDEAL_SAMPLE'):
                    from portable.tests.acceptance.native_sampling import sampled_run
                    code=sampled_run(command,ROOT,env,log,timeout,out/'samples.json')
                else:code=subprocess.run(command,cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=timeout).returncode
            except subprocess.TimeoutExpired:code=None;timed_out=True
        seconds=time.perf_counter()-started
        elapsed('native_process')
        for saved in assets.glob('*.ANT'):shutil.copyfile(saved,out/saved.name)
    elapsed('asset_cleanup')
    expected=read_hashes(reference/'capture/observer.txt.hash',count)
    actual=read_hashes(out/'native.hash',count) if (out/'native.hash').exists() else []
    raw_expected,raw_actual=expected,actual
    expected=read_hashes(reference/'capture/observer.txt.hash.ideal-state-v2',count)
    actual=read_hashes(out/'native.hash.ideal-state-v2',count)
    if len(raw_expected)!=len(expected) or len(raw_actual)!=len(actual):
        raise ValueError('Raw/semantic observation coverage differs')
    first=None;separate={};equal=0;rows=[]
    for entry,(left,right) in enumerate(zip(expected[:stop],actual),1):
        changed=[]
        for item,a,b in zip(items,left,right):
            if a==b:continue
            delta=dict(name=item['name'],category=item['category'],reference_hash=a,native_hash=b)
            if item['verdict']:changed.append(delta)
            else:separate.setdefault(item['name'],dict(entry=entry,**delta))
        if changed and first is None:first=dict(entry=entry,views=changed)
        equal+=not changed;rows.append(dict(entry=entry,equal=not changed,changed=[v['name'] for v in changed]))
    complete=code==0 and len(actual)==stop and not timed_out
    result=dict(contract='ideal-v1',scenario=recipe['id'],target=manifest['target'],
        state='STATE_DIFFERENCE' if first else 'STATE_EQUAL' if complete else 'STATE_INCOMPLETE',
        requested_entries=stop,entries=len(actual),equal_entries=equal,first_difference=first,separate_differences=separate,
        seconds=seconds,recording_seconds=manifest['recording_seconds'],code=code,timed_out=timed_out,
        command=command,environment={k:v for k,v in env.items() if k.startswith('SIMANT_')},machine_profile=profile,
        no_tapes=True,policy_changes=state['policy_changes'])
    observer=json.loads((out/'native-result.json').read_text()) if (out/'native-result.json').exists() else {}
    ideal_rows=[line.split() for line in (reference/'capture/observer.txt.ideal').read_text().splitlines() if line.startswith('S ')]
    expected_clock=[int(row[2]) for row in ideal_rows[:stop]]
    clock_bytes=(out/'native.hash.machine').read_bytes()
    if len(clock_bytes)%8:raise ValueError('Truncated machine timestamps')
    native_clock=list(struct.unpack('<'+'Q'*(len(clock_bytes)//8),clock_bytes))
    clock_first=next((i for i,(a,b) in enumerate(zip(expected_clock,native_clock),1) if a!=b),None)
    clock_equal=len(native_clock)==stop and len(expected_clock)==stop and clock_first is None
    result['clock']=dict(status='CLOCK_EQUAL' if clock_equal else 'CLOCK_DIFFERENCE',entries=len(native_clock),first_differing_entry=clock_first,
        diagnostic_only=True,scope='Entry-time diagnostic, separate from the existing state/frame observer contract')
    if len(native_clock)!=stop:result['state']='STATE_INCOMPLETE'
    simulated_seconds=(native_clock[-1]/1e9) if native_clock else 0
    result['rates']=dict(simulation_entries_per_second=len(actual)/seconds,simulated_seconds=simulated_seconds,simulated_to_wall=simulated_seconds/seconds)
    result['event_context_rule']=manifest['event_context_rule']
    result['animation_identity_rule']=manifest['animation_identity_rule']
    result['raw_event_differences']={}
    for entry,(left,right) in enumerate(zip(raw_expected[:stop],raw_actual),1):
        for item,a,b,qualified_a,qualified_b in zip(items,left,right,expected[entry-1],actual[entry-1]):
            if item['name'] not in context and item['name'] not in identities:
                if a!=qualified_a or b!=qualified_b:raise ValueError('Observer rule changed an unlisted view')
            elif item['name'] in context and a!=b:
                result['raw_event_differences'].setdefault(item['name'],dict(entry=entry,raw_reference_hash=a,raw_native_hash=b,qualified_equal=qualified_a==qualified_b))
    from portable.tests.acceptance.animation_identity import compare_raw
    result['raw_animation_ids']=compare_raw(reference/'capture/observer.txt.anim-ids',out/'native.hash.anim-ids',identities,stop)
    if sound_off:
        result['variant']='sound-off'
        result['sound_configuration']=manifest['sound_configuration']
        first_dos=split_frame(reference/'capture/observer.txt.frame.1',items)
        first_native=split_frame(out/'native.frame.1',items)
        globals_={}
        for name in ('snd_requested_driver_mode','snd_interface_initialized'):
            globals_[name]=dict(dos=first_dos[name].hex(),native=first_native[name].hex())
            if any(first_dos[name]) or any(first_native[name]):raise ValueError('Game did not select the no-sound branch')
        pit=[int(line.split()[4]) for line in (reference/'capture/observer.txt.ideal').read_text().splitlines() if line.startswith('S ')]
        if observer.get('audio_rendered_frames')!=0 or observer.get('physical_audio_open')!=0:
            raise ValueError('Sound-off deterministic run rendered audio or opened playback')
        if len(pit)!=manifest['steps'] or set(pit)!={65536}:raise ValueError('Sound-off PIT is not at BIOS rate')
        # Every observed ISR entry adds 1 or 16 positive fast periods. A zero
        # content endpoint therefore proves exactly zero sound ISR entries,
        # including in the retained captures made before explicit count stats.
        from portable.tests.acceptance.audio_content import read_content
        endpoint=read_content(reference/'capture/observer.txt.content')['end']
        dos_periods=endpoint.get('isr_tick',endpoint['tick'])
        if dos_periods!=0:raise ValueError('Sound-off DOS ran a sound ISR')
        if observer.get('audio_content_isr_periods')!=0:raise ValueError('Sound-off native ran a sound ISR')
        writes={label:len(read_commands(path)[0]) for label,path in [('dos',reference/'capture/observer.txt.audio'),('native',out/'audio-commands.txt')]}
        if any(writes.values()):raise ValueError('Sound-off run emitted device commands')
        result['sound_off_verification']=dict(game_globals=globals_,dos_pit_divisor=65536,dos_pit_entries=len(pit),sound_isrs=0,isr_observation="Positive-period sum at complete content endpoint",audio_writes=writes)
    elapsed('state_comparison')
    result['frames']=compare_frames(reference,out,checkpoints,hash_first=True);result['frames']['complete']=complete
    if sound_off:
        result['audio']=dict(status='SOUND_OFF_CONFIRMED',separate_verification=True)
        result['audio_content_diagnostic']=dict(status='NOT_REQUESTED_SOUND_OFF')
    else:
        result['audio']=compare_commands(reference/'capture/observer.txt.audio',out/'audio-commands.txt',out,entries=stop,replay_complete=complete)
        result['audio_content_diagnostic']=compare_content(reference/'capture/observer.txt.content',out/'audio-content.txt',stop,
            tolerance=16,replay_complete=complete,out=out,raw_dos_path=reference/'capture/observer.txt.audio',raw_native_path=out/'audio-commands.txt',
            progress_names=[i['name'] for i in items if i['category']=='audio'],playback=playback,playback_tolerance_ns=playback_tolerance_ns)
    elapsed('frame_comparison')
    result['timings']=timings
    result['observer']=observer
    if first:
        result['first_differing_field']=first['views'][0]['name']
        result['dump_hint']='Rerun with --dump-entry '+str(first['entry'])+'; native.frame.N contains complete named-view bytes in schema order. Record a DOS prefix ending at N for a full reference dump when N is not already a stored checkpoint.'
    (out/'state-rows.json').write_text(json.dumps(rows,indent=2)+'\n')
    elapsed('serialization')
    timings['lane_total']=time.perf_counter()-lane_started
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print(f'{recipe["id"]} {manifest["target"]}: {result["state"]} {equal}/{stop} first={first["entry"] if first else "-"} frames={result["frames"]["status"]} audio={result["audio"]["status"]} {seconds:.2f}s {len(actual)/seconds:.1f} steps/s {simulated_seconds/seconds:.1f}x simulated/wall',flush=True)
    return result

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('scenario',type=Path,nargs='*')
    ap.add_argument('--build',type=Path,default=ROOT/'build/current/portable');ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--reference-root',type=Path);ap.add_argument('--timeout',type=int,default=600)
    ap.add_argument('--trace-reads',action='store_true',help='Record every charged service, machine time and native call stack')
    ap.add_argument('--steps',type=int);ap.add_argument('--jobs',type=int,default=1,choices=range(1,5))
    ap.add_argument('--scratch-root',type=Path,default=ROOT/'build/scratch/ideal',help='Short disposable asset directory')
    ap.add_argument('--dump-entry',type=int,help='Write full diagnostic state at this entry (all view hashes are always observed)')
    ap.add_argument('--sample-native',action='store_true',help='Optional 10 ms Windows native instruction-pointer profile')
    ap.add_argument('--sound-off',action='store_true',help='Select separately recorded Sound Mode: 0 references')
    a=ap.parse_args();a.build=a.build.resolve();a.out=a.out.resolve();a.out.mkdir(parents=True,exist_ok=False)
    if a.reference_root is None:a.reference_root=ROOT/'build/reference'/('sound-off-identity' if a.sound_off else 'sound-on-identity-v1')
    elif a.sound_off and a.reference_root.resolve()==(ROOT/'build/reference').resolve():a.reference_root=a.reference_root/'sound-off-identity'
    all_started=time.perf_counter();exe=build_observer(a.build,a.out/'test-build');build_seconds=time.perf_counter()-all_started;jobs=[]
    prepare_started=time.perf_counter()
    state=prepare_schema(schema(a.build,executable=exe))
    syms=symbols_for(exe)
    prepared=a.out/'native-views.json'
    prepared.write_text(json.dumps(dict(executable_sha256=sha(exe),sound_off=a.sound_off,state=state,
        anchor=syms.addresses['portable_test_observer_anchor'],palette=syms.expression('app.palette')[0])))
    prepare_seconds=time.perf_counter()-prepare_started
    if a.sample_native:os.environ['SIMANT_IDEAL_SAMPLE']='1'

    for path in a.scenario or sorted((ROOT/'dos/scenarios').glob('*.json')):
        refs={}
        for manifest in (a.reference_root/path.stem).glob(('*-ideal-v1-sound-off' if a.sound_off else '*-ideal-v1')+'/manifest.json'):
            data=json.loads(manifest.read_text());refs[data['target']]=manifest.parent
        if not refs:
            for target in ('original','canonical'):
                manifest=a.reference_root/path.stem/target/'manifest.json'
                if manifest.is_file():refs[target]=manifest.parent
        if set(refs)!={'original','canonical'}:raise ValueError('Both ideal-v1 references required: '+str(path))
        jobs.extend((path.resolve(),reference,target) for target,reference in refs.items())
    # Resolve this executable once; every independent lane still validates its
    # pinned reference and binds its policy. Children own all mutable state.
    from concurrent.futures import ThreadPoolExecutor
    def work(job):
        path,reference,target=job;destination=a.out/path.stem/target
        command=[sys.executable,'-c','from pathlib import Path; import sys; from portable.tests.acceptance.ideal_check import lane; lane(*[Path(p) for p in sys.argv[1:6]],timeout=int(sys.argv[6]),steps=int(sys.argv[7]) or None,prepared=Path(sys.argv[8]),scratch_root=Path(sys.argv[9]),dump_entry=int(sys.argv[10]) or None,trace_reads=bool(int(sys.argv[11])))',
            str(path),str(reference),str(a.build),str(exe),str(destination),str(a.timeout),str(a.steps or 0),str(prepared),str(a.scratch_root.resolve()),str(a.dump_entry or 0),str(int(a.trace_reads))]
        destination.parent.mkdir(parents=True,exist_ok=True)
        log=destination.with_suffix('.log')
        with log.open('w') as output:run=subprocess.run(command,cwd=ROOT,stdout=output,stderr=subprocess.STDOUT,timeout=a.timeout+180)
        if run.returncode:raise RuntimeError('Lane failed: '+str(log))
        result=json.loads((destination/'result.json').read_text());print(log.read_text().strip(),flush=True);return result
    with ThreadPoolExecutor(max_workers=a.jobs) as pool:results=list(pool.map(work,jobs))
    summary=[{k:r[k] for k in ('scenario','target','state','entries','equal_entries','seconds','recording_seconds','first_difference')}|dict(frames=r['frames']['status'],audio=r['audio']['status'],audio_content=r['audio_content_diagnostic']['status']) for r in results]
    (a.out/'timings.json').write_text(json.dumps(dict(wall_seconds=time.perf_counter()-all_started,observer_build_seconds=build_seconds,native_schema_prepare_seconds=prepare_seconds,lanes=[dict(scenario=r['scenario'],target=r['target'],timings=r['timings'],observer=r['observer']) for r in results]),indent=2)+'\n')
    (a.out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    return int(any(r['state']!='STATE_EQUAL' or r['frames']['status']!='FRAME_EQUAL' or r['audio']['status'] not in ('AUDIO_COMMANDS_EQUAL','SOUND_OFF_CONFIRMED') for r in results))
if __name__=='__main__':raise SystemExit(main())
