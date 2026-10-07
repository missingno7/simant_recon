"""Capture canonical DoAntSim entries and startup clocks without guest changes."""
import argparse,json,subprocess,sys
from pathlib import Path
if __package__:
    from .native_acceptance import ROOT,acceptance,memory_base,sha
else:
    from native_acceptance import ROOT,acceptance,memory_base,sha


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('scenario',type=Path)
    ap.add_argument('--build-report',type=Path,default=ROOT/'build/current/dos/build-report.json')
    ap.add_argument('--reference-dump',type=Path,required=True)
    ap.add_argument('--saved-game',type=Path)
    ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--steps',type=int,default=8)
    ap.add_argument('--until-ms',type=int,help='Optional diagnostic input-prefix bound; never full-scenario acceptance')
    ap.add_argument('--host-seconds',type=int,default=600)
    args=ap.parse_args()
    if not 1<=args.steps<=64 or not 1<=args.host_seconds<=7200: ap.error('Bound steps to 1..64 and host seconds to 1..7200')
    report=json.loads(args.build_report.read_text());scenario=json.loads(args.scenario.read_text())
    exe=ROOT/report['link']['candidate_executable']['path']
    if sha(exe)!=report['link']['candidate_executable']['sha256']: raise ValueError('DOS executable identity differs')
    reference=args.reference_dump.resolve()
    prior=json.loads((reference.parent/'execution-report.json').read_text())
    if not any(i.get('sha256')==sha(exe) for i in prior.get('inputs',[])): raise ValueError('Reference dump is not from the canonical executable')
    addresses=acceptance.record_addresses(exe.with_name('SOURCE.MAP'))
    base=memory_base(reference.read_bytes(),addresses)
    out=args.out.resolve()
    if out.exists(): raise ValueError('Explicit DOS observation output must be fresh')
    out.parent.mkdir(parents=True,exist_ok=True)
    original=(ROOT/scenario['script']).read_text()
    lines=[l for l in original.splitlines() if l.strip() and not l.lstrip().startswith('#')]
    if args.until_ms:
        lines=[l for l in lines if int(l.split()[0])<args.until_ms and l.split()[1]!='exit']
        lines.append(f'{args.until_ms} exit')
    lines += [f'0 on_exec lin {base+addresses["DoAntSim"]:X} {args.steps} dump 0 A0000 simstep']
    for name in ('main','f_00DF_0004','f_28BC_03CC'):
        lines.append(f'0 on_exec lin {base+addresses[name]:X} 1 dump 46C 4 startup-{name}')
    for ms in (0,250,500,750,1000,1250,1500,2000,5000,7000,9000,14000):
        if args.until_ms is None or ms<args.until_ms: lines.append(f'{ms} dump 46C 4 clock{ms}')
    lines.sort(key=lambda l:int(l.split()[0]))
    script=out.with_suffix('.scr');script.write_text('\n'.join(lines)+'\n')
    command=[sys.executable,str(ROOT/'dos/run.py'),'--build-report',str(args.build_report.resolve()),
             '--out',str(out),'--seconds',str(args.host_seconds),'--fixed-clock','--input-script',str(script)]
    for arg in scenario.get('arguments',[]): command+=['--argument',arg]
    if scenario.get('saved_game'): command+=['--saved-game',str((args.saved_game or ROOT/scenario['saved_game']).resolve())]
    run=subprocess.run(command,cwd=ROOT)
    manifest=dict(schema='simant-dos-step-observations-v1',boundary='DoAntSim:entry',steps=args.steps,
                  executable_sha256=sha(exe),reference_dump_sha256=sha(reference),runtime_base=base,
                  scenario_sha256=sha(args.scenario),input_script_sha256=sha(ROOT/scenario['script']),
                  observation_script_sha256=sha(script),until_ms=args.until_ms,
                  scope='Original inputs plus read-only observations; prefix-only if until_ms is set.',
                  command=command,returncode=run.returncode,
                  snapshots={p.name:sha(p) for p in sorted(out.glob('exec-simstep.*.bin'))})
    (out/'boundary-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps(manifest,indent=2))
    return run.returncode
if __name__=='__main__': raise SystemExit(main())
