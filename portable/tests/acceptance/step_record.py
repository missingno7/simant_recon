"""Record a bounded scenario once per executable; ordinary checks never run DOS."""
import argparse
import json
import subprocess
import sys
import time
from pathlib import Path
try:
    from .state_schema import ROOT, sha
    from .step_state import schema, read_hashes
except ImportError:
    from state_schema import ROOT, sha
    from step_state import schema, read_hashes


def record(scenario_path, target, build, observer, report, out=None, binding_dump=None, steps=None, cycles=None, scratch_root=None, host_seconds=1200):
    scenario = json.loads(scenario_path.read_text())
    exe = ROOT/'assets/SIMANT.EXE' if target=='original' else ROOT/json.loads(report.read_text())['link']['candidate_executable']['path']
    directory = out or ROOT/'build/reference'/scenario['id']/(sha(exe)+'-service-samples-v9')
    script = ROOT/scenario['script']
    observer_build=json.loads(observer.read_text())
    if observer_build.get('schema')!='simant-boundary-observer-build-v9':
        raise ValueError('Checkpoint recording requires a v9 observer build')
    observer_source=Path(__file__).with_name('compact_observer.inc').resolve()
    if observer_build.get('inputs',{}).get(str(observer_source))!=sha(observer_source):
        raise ValueError('Compact observer source changed; rebuild the observer before recording')
    identity = dict(executable_sha256=sha(exe), scenario_sha256=sha(scenario_path), script_sha256=sha(script))
    if scenario.get('saved_game'):
        identity['saved_game_sha256']=sha(ROOT/scenario['saved_game'])
        if identity['saved_game_sha256']!=scenario['saved_game_sha256']:
            raise ValueError('Scenario saved game identity differs')
    if (directory/'manifest.json').is_file():
        try:
            from .step_check import validate_reference
        except ImportError:
            from step_check import validate_reference
        validate_reference(directory, scenario_path)
        manifest=json.loads((directory/'manifest.json').read_text())
        if all(manifest.get(k)==v for k,v in identity.items()) and (steps is None or manifest['steps']==steps):
            boundary=json.loads((directory/'capture/boundary-manifest.json').read_text())
            if boundary['compact_observer'].get('order_contract')!='service-samples-v9':
                raise ValueError('Reference needs atomic service/input coordinates; retire it with tools/workspace.py and record again: '+str(directory))
            print(scenario['id']+' '+target+': cached reference', flush=True)
            return directory
        raise ValueError('Reference identity changed; move the old reference with tools/workspace.py before recording: '+str(directory))
    if directory.exists():
        raise ValueError('Incomplete or occupied reference directory: '+str(directory))
    directory.mkdir(parents=True)
    state=schema(build, report)
    state_path=directory/'schema.json';state_path.write_text(json.dumps(state,indent=2)+'\n')
    scratch=scratch_root or ROOT/'build/scratch/steps'
    scratch.mkdir(parents=True,exist_ok=True)
    if binding_dump is None:
        bootstrap=scratch/(scenario['id']+'-'+target+'-binding-'+str(time.time_ns()))
        bootstrap_script=bootstrap.with_suffix('.scr')
        # One ordinary timed memory observation establishes relocated addresses.
        # It is not a state checkpoint and never contributes a verdict.
        lines=[l for l in script.read_text().splitlines() if l.strip() and not l.startswith('#') and int(l.split()[0])<14000 and l.split()[1]!='exit']
        bootstrap_script.write_text('\n'.join(lines+['14000 dump 0 A0000 binding','14001 exit'])+'\n')
        cmd=[sys.executable,str(ROOT/'dos/run.py'),'--out',str(bootstrap),'--seconds','120','--fixed-clock','--cycles','10000','--input-script',str(bootstrap_script)]
        cmd+=['--original'] if target=='original' else ['--build-report',str(report)]
        subprocess.run(cmd,check=True,stdout=subprocess.DEVNULL,timeout=140)
        binding_dump=bootstrap/'dump-binding'
    count=steps or scenario['steps']
    cmd=[sys.executable,str(Path(__file__).with_name('capture_dos_steps.py')),str(scenario_path),
         '--out',str(directory/'capture'),'--reference-dump',str(binding_dump),
         '--compact-observer',str(observer),'--state-schema',str(state_path),
         '--steps',str(count),'--host-seconds',str(host_seconds),'--dump-every',str(scenario.get('dump_every',256)),
         '--cycles',str(cycles or scenario.get('cycles',10000))]
    cmd+=['--original'] if target=='original' else ['--build-report',str(report)]
    start=time.perf_counter()
    with (directory/'record.log').open('w') as log:
        run=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,timeout=host_seconds+60)
    elapsed=time.perf_counter()-start
    capture=directory/'capture'
    rows=read_hashes(capture/'observer.txt.hash',len(state['items']))
    try:
        from .full_inputs import parse_trace
    except ImportError:
        from full_inputs import parse_trace
    parse_trace(capture/'observer.txt',len(rows),require_quiet=True)
    boundary=json.loads((capture/'boundary-manifest.json').read_text())
    execution=json.loads((capture/'execution-report.json').read_text())
    if execution.get('keyboard_layout') != dict(language='us', layout='us'):
        raise ValueError('Reference effective keyboard layout is not pinned US')
    manifest=dict(schema='simant-step-reference-v1',input_contract='service-samples-v9',target=target,**identity,steps=len(rows),requested_steps=count,
                  schema_identity=state['identity'],speed=scenario.get('speed','normal (1)'),cycles=cycles or scenario.get('cycles',10000),
                  recording_seconds=elapsed,seconds_per_step=elapsed/max(1,len(rows)),command=cmd,
                  observer_sha256=sha(observer),observer_build=observer_build,
                  keyboard_layout=execution['keyboard_layout'],
                  keyboard_environment=execution['keyboard_environment'],
                  source_identity=json.loads(report.read_text()).get('input_pins') if target!='original' else None,
                  complete=run.returncode==0 and len(rows)==count,
                  boundary_manifest_sha256=sha(capture/'boundary-manifest.json'),
                  files={p.relative_to(directory).as_posix():sha(p) for p in
                         [state_path,capture/'observer.txt',capture/'observer.txt.order',capture/'observer.txt.hash',capture/'observer.txt.timer',capture/'observer.txt.audio',capture/'observer.txt.sound',capture/'observer.txt.sound-calls',*capture.glob('observer.txt.frame.*'),*capture.glob('observer.txt.screen.*')]},
                  frames=boundary['frames'])
    (directory/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(f'{scenario["id"]} {target}: {len(rows)}/{count} steps, {elapsed:.3f}s ({elapsed/max(1,len(rows)):.4f}s/step)',flush=True)
    if not manifest['complete']: raise RuntimeError('Recording ended before requested simulation entry; see '+str(directory/'record.log'))
    return directory


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('scenario',type=Path,nargs='*')
    ap.add_argument('--target',choices=('original','canonical','all'),default='all')
    ap.add_argument('--build',type=Path,default=ROOT/'build/current/portable')
    ap.add_argument('--observer',type=Path,required=True)
    ap.add_argument('--dos-report',type=Path,default=ROOT/'build/current/dos/build-report.json')
    ap.add_argument('--out',type=Path,help='Fresh scratch/reference path for one scenario/target (repeat control)')
    ap.add_argument('--binding-dump',type=Path)
    ap.add_argument('--steps',type=int)
    ap.add_argument('--host-seconds',type=int,default=1200,help='Host recording bound; does not change guest cycles or script timing')
    ap.add_argument('--cycles',type=int,help='Explicit recording-performance control; stored in the receipt')
    ap.add_argument('--scratch-root',type=Path,help='Worker directory for disposable binding captures')
    a=ap.parse_args()
    scenarios=a.scenario or sorted((ROOT/'dos/scenarios').glob('*.json'))
    targets=('original','canonical') if a.target=='all' else (a.target,)
    if a.out and (len(scenarios)!=1 or len(targets)!=1):ap.error('--out needs one scenario and target')
    for scenario_path in scenarios:
        for target in targets:
            record(scenario_path.resolve(),target,a.build.resolve(),a.observer.resolve(),a.dos_report.resolve(),
                   a.out.resolve() if a.out else None,a.binding_dump.resolve() if a.binding_dump else None,a.steps,a.cycles,
                   a.scratch_root.resolve() if a.scratch_root else None,a.host_seconds)

if __name__=='__main__':main()
