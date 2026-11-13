"""Capture original/canonical DoAntSim entries and seed clock returns read-only."""
import argparse,json,subprocess,sys,time
from pathlib import Path
if __package__:
    from .native_acceptance import ROOT,acceptance,memory_base,sha
else:
    from native_acceptance import ROOT,acceptance,memory_base,sha


def capture_addresses(original, exe):
    if not original:
        return acceptance.record_addresses(exe.with_name('SOURCE.MAP'))
    symbols=json.loads((ROOT/'layout/symbols.json').read_text())
    return {name:row['seg']*16+row['off'] for group in ('code','data')
            for name,row in symbols[group].items() if row.get('unit','root')=='root'}


def seed_returns(memory,base,addresses):
    """Disassemble each independent DOS view, binding the actual relocated CALL."""
    from capstone import Cs,CS_ARCH_X86,CS_MODE_16
    sites={}
    # Complete extents of these two functions in the exact RNG module.
    for name,length in [('SeedSRand',19),('SeedRRand',55)]:
        start=base+addresses[name]
        calls=[]
        for ins in Cs(CS_ARCH_X86,CS_MODE_16).disasm(memory[start:start+length],start):
            raw=bytes(ins.bytes)
            if len(raw)==5 and raw[0]==0x9a and \
                    int.from_bytes(raw[1:3],'little')+16*int.from_bytes(raw[3:5],'little')==base+addresses['TickCount']:
                calls.append(ins.address+ins.size)
        if len(calls)!=1: raise ValueError('Expected one independently bound TickCount call in '+name)
        sites[name]=calls[0]
    return sites


def countdown_points(memory,base,addresses,sites):
    """Bind actual ES countdown operands (small displacements print decimal)."""
    from capstone import Cs,CS_ARCH_X86,CS_MODE_16
    from capstone.x86 import X86_OP_MEM,X86_REG_ES
    decoder=Cs(CS_ARCH_X86,CS_MODE_16);decoder.detail=True
    points=[];countdown=set()
    for name in ('timer_wait_countdown','timer_countdown_done'):
        start=base+addresses[name]
        for ins in decoder.disasm(memory[start:start+64],start):
            if ins.mnemonic=='retf':break
            reads=[op for op in ins.operands if op.type==X86_OP_MEM and op.mem.segment==X86_REG_ES]
            if ins.mnemonic=='cmp' and len(reads)==1:
                countdown.add(reads[0].mem.disp);points.append(('C',ins.address))
    if len(countdown)!=1 or len(points)!=2:raise ValueError('Countdown read binding is not unique: '+str(countdown))
    tick_cs=int.from_bytes(memory[sites['SeedSRand']-2:sites['SeedSRand']],'little')
    return points+[('D',16*tick_cs+countdown.pop())]


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('scenario',type=Path)
    ap.add_argument('--build-report',type=Path,default=ROOT/'build/current/dos/build-report.json')
    ap.add_argument('--original',action='store_true',help='Use original symbol anchors and original executable identity')
    ap.add_argument('--reference-dump',type=Path,required=True)
    ap.add_argument('--saved-game',type=Path)
    ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--steps',type=int,default=8)
    ap.add_argument('--until-ms',type=int,help='Optional diagnostic input-prefix bound; never full-scenario acceptance')
    ap.add_argument('--host-seconds',type=int,default=600)
    ap.add_argument('--compact-observer',type=Path,help='Read-only compact observer build receipt; capture all clock returns and pump ordinals')
    ap.add_argument('--pump-source',choices=('both','window','queue'),default='both',help='Ordinal boundaries: window event pump entry and completed queue read (single-boundary modes are diagnostic controls)')
    args=ap.parse_args()
    if not 1<=args.steps<=64 or not 1<=args.host_seconds<=7200: ap.error('Bound steps to 1..64 and host seconds to 1..7200')
    report=None if args.original else json.loads(args.build_report.read_text())
    scenario=json.loads(args.scenario.read_text())
    exe=ROOT/'assets/SIMANT.EXE' if args.original else ROOT/report['link']['candidate_executable']['path']
    expected=json.loads((ROOT/'layout/oracle.lock.json').read_text())['inputs']['SIMANT.EXE']['sha256'] if args.original else report['link']['candidate_executable']['sha256']
    if sha(exe)!=expected: raise ValueError('DOS executable identity differs')
    reference=args.reference_dump.resolve()
    prior=json.loads((reference.parent/'execution-report.json').read_text())
    if not any(i.get('sha256')==sha(exe) for i in prior.get('inputs',[])): raise ValueError('Reference dump is not from the selected executable')
    addresses=capture_addresses(args.original,exe)
    base=memory_base(reference.read_bytes(),addresses)
    sites=seed_returns(reference.read_bytes(),base,addresses)
    out=args.out.resolve()
    if out.exists(): raise ValueError('Explicit DOS observation output must be fresh')
    out.parent.mkdir(parents=True,exist_ok=True)
    original=(ROOT/scenario['script']).read_text()
    lines=[l for l in original.splitlines() if l.strip() and not l.lstrip().startswith('#')]
    if args.until_ms:
        lines=[l for l in lines if int(l.split()[0])<args.until_ms and l.split()[1]!='exit']
        lines.append(f'{args.until_ms} exit')
    lines += [f'0 on_exec lin {base+addresses["DoAntSim"]:X} {args.steps} dump 0 A0000 simstep']
    lines += [f'{ms} dump 0 A0000 cp{ms}' for ms in scenario.get('checkpoints',[]) or [14000,22000,40000,49000]
              if args.until_ms is None or ms<args.until_ms]
    # Metadata records returned DX:AX before the caller changes either word.
    # Exactly two SeedSRand calls (direct initStuff, then SeedRRand) and one
    # SeedRRand read are expected in the normal launch, not arbitrary max hits.
    for name,hits in [('SeedSRand',2),('SeedRRand',1)]:
        lines.append(f'0 on_exec lin {sites[name]:X} {hits} dump 46C 4 seed-{name}')
    for name in ('main','snd_init_driver_once','snd_start_sample_timer'):
        lines.append(f'0 on_exec lin {base+addresses[name]:X} 1 dump 46C 4 startup-{name}')
    for ms in (0,250,500,750,1000,1250,1500,2000,5000,7000,9000,14000):
        if args.until_ms is None or ms<args.until_ms: lines.append(f'{ms} dump 46C 4 clock{ms}')
    lines.sort(key=lambda l:int(l.split()[0]))
    script=out.with_suffix('.scr');script.write_text('\n'.join(lines)+'\n')
    command=[sys.executable,str(ROOT/'dos/run.py'),
             '--out',str(out),'--seconds',str(args.host_seconds),'--fixed-clock','--input-script',str(script)]
    command+=['--original'] if args.original else ['--build-report',str(args.build_report.resolve())]
    compact_spec=None
    if args.compact_observer:
        from capstone import Cs,CS_ARCH_X86,CS_MODE_16
        memory=reference.read_bytes(); decoder=Cs(CS_ARCH_X86,CS_MODE_16);decoder.detail=True
        points=[]
        for name,kind in [('TickCount','T'),('timer_bios_tick_count','B')]:
            start=base+addresses[name]
            ins=list(decoder.disasm(memory[start:start+32],start))
            ret=next(i.address for i in ins if i.mnemonic=='retf')
            points.append((kind,ret))
        if args.pump_source in ('both','queue'):
            start=base+addresses['input_event_count']
            pump_pc=next(i.address for i in decoder.disasm(memory[start:start+16],start) if i.mnemonic=='retf')
            points.append(('P',pump_pc))
        if args.pump_source in ('both','window'):points.append(('P',base+addresses['f_1B28_0069']))
        points.append(('S',base+addresses['DoAntSim']))
        points += [('K',base+addresses['kbd_process_scan']),('M',base+addresses['mouse_event_callback'])]
        start=base+addresses['input_enqueue_event']
        stamps=[i.address for i in decoder.disasm(memory[start:start+200],start)
                if i.mnemonic=='mov' and i.op_str=='bx, word ptr es:[0x6c]']
        if len(stamps)!=1: raise ValueError('Event BIOS timestamp read is not unique')
        points.append(('V',stamps[0]))
        # Countdown reads in the two source helpers, before the instruction.
        points+=countdown_points(memory,base,addresses,sites)
        compact_spec=out.with_suffix('.observer')
        compact_spec.write_text(str(out/'observer.txt')+'\n'+''.join(f'{k} {pc:X}\n' for k,pc in points))
        command += ['--capture-observer',str(args.compact_observer.resolve()),'--observer-config',str(compact_spec)]
    for arg in scenario.get('arguments',[]): command+=['--argument',arg]
    if scenario.get('saved_game'): command+=['--saved-game',str((args.saved_game or ROOT/scenario['saved_game']).resolve())]
    started=time.monotonic()
    run=subprocess.run(command,cwd=ROOT,timeout=args.host_seconds+60)
    manifest=dict(schema='simant-dos-step-observations-v1',boundary='DoAntSim:entry',steps=args.steps,
                  executable_sha256=sha(exe),reference_dump_sha256=sha(reference),runtime_base=base,
                  target='original' if args.original else 'canonical_dos',seed_return_sites=sites,
                  host_elapsed_seconds=time.monotonic()-started,
                  scenario_sha256=sha(args.scenario),input_script_sha256=sha(ROOT/scenario['script']),
                  observation_script_sha256=sha(script),until_ms=args.until_ms,
                  execution_report_sha256=sha(out/'execution-report.json'),
                  installed_script_sha256=sha(out/'INPUT.SCR'),
                  scope='Original inputs plus read-only observations; prefix-only if until_ms is set.',
                  command=command,returncode=run.returncode,
                  snapshots={p.name:sha(p) for p in sorted(out.glob('exec-*.bin'))},
                  metadata={p.name:sha(p) for p in sorted(out.glob('exec-*.json'))})
    if compact_spec:
        manifest['compact_observer']=dict(specification_sha256=sha(compact_spec),points=points,pump_source=args.pump_source,
            trace_sha256=sha(out/'observer.txt'),trace_bytes=(out/'observer.txt').stat().st_size,
            runner_receipt_sha256=sha(args.compact_observer))
    (out/'boundary-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps(manifest,indent=2))
    return run.returncode
if __name__=='__main__': raise SystemExit(main())
