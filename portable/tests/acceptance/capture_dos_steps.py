"""Record original/canonical step fingerprints, clock streams and input positions."""
import argparse,json,subprocess,sys,time
from pathlib import Path
if __package__:
    from .state_schema import ROOT,acceptance,memory_base,sha
else:
    from state_schema import ROOT,acceptance,memory_base,sha


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
    ap.add_argument('--host-seconds',type=int,default=600)
    ap.add_argument('--compact-observer',type=Path,required=True,help='Read-only compact observer build receipt')
    ap.add_argument('--state-schema',type=Path,required=True,help='Ordered step fingerprint views (step_state.py)')
    ap.add_argument('--dump-every',type=int,default=256)
    ap.add_argument('--cycles',type=int,default=10000)
    args=ap.parse_args()
    if not 1<=args.steps<=20000 or not 1<=args.host_seconds<=7200: ap.error('Bound steps to 1..20000 and host seconds to 1..7200')
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
    # One binding frame, then compact fingerprints and periodic state frames.
    lines += [f'0 on_exec lin {base+addresses["DoAntSim"]:X} 1 dump 0 100000 simstep']
    lines.sort(key=lambda l:int(l.split()[0]))
    script=out.with_suffix('.scr');script.write_text('\n'.join(lines)+'\n')
    command=[sys.executable,str(ROOT/'dos/run.py'),
             '--out',str(out),'--seconds',str(args.host_seconds),'--fixed-clock','--input-script',str(script),'--cycles',str(args.cycles)]
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
        start=base+addresses['input_event_count']
        sample=next(decoder.disasm(memory[start:start+4],start))
        if sample.mnemonic!='mov' or not sample.op_str.startswith('ax, word ptr ['):raise ValueError('Queue count sample binding differs')
        pump_pc=sample.address
        points.append(('P',pump_pc))
        points.append(('W',base+addresses['f_1B28_0069']))
        points.append(('S',base+addresses['DoAntSim']))
        for name,kind in [('kbd_poll_bios_key','A'),('kbd_read_bios_char','G')]:
            start=base+addresses[name]
            ret=next(i.address for i in decoder.disasm(memory[start:start+80],start) if i.mnemonic=='retf')
            points.append((kind,ret))
        # Actual INT16 callback sample, not the later public-function RETF.
        bios_entry=int.from_bytes(memory[0x58:0x5a],'little')+16*int.from_bytes(memory[0x5a:0x5c],'little')
        if bios_entry<0xf0000:raise ValueError('Unbound BIOS INT16 callback vector')
        points.append(('F',bios_entry+1))
        for name,kind in [('kbd_poll_bios_key','p'),('kbd_read_bios_char','q')]:
            start=base+addresses[name]
            calls=[i.address+2 for i in decoder.disasm(memory[start:start+34],start)
                   if i.mnemonic=='int' and i.op_str=='0x16']
            if len(calls)!=1:raise ValueError('Expected one source INT16 in '+name)
            points.append((kind,calls[0]))
        # Input operands read while source loops execute without clock reads.
        # Each routine has exactly one byte MOV into AL before its RETF.
        from capstone.x86 import X86_OP_REG,X86_OP_MEM,X86_REG_AL
        for name,kind,length in [('StillDown','b',61),('kbd_scan_state','c',16),('kbd_scroll_lock_state','d',14)]:
            start=base+addresses[name]
            samples=[i.address for i in decoder.disasm(memory[start:start+length],start)
                     if i.mnemonic=='mov' and len(i.operands)==2 and i.operands[0].type==X86_OP_REG
                     and i.operands[0].reg==X86_REG_AL and i.operands[1].type==X86_OP_MEM]
            if len(samples)!=1:raise ValueError('Input operand sample is ambiguous: '+name)
            points.append((kind,samples[0]))
        points.append(('a',base+addresses['edit_scroll_and_redraw']))
        points += [('K',base+addresses['kbd_process_scan']),('M',base+addresses['mouse_event_callback'])]
        points.append(('Y',base+addresses['kbd_int15_scan_hook']))
        from capstone.x86 import X86_OP_MEM,X86_OP_REG,X86_REG_CS,X86_REG_BL
        start=base+addresses['kbd_disable_mouse_emulation']
        flags=[op.mem.disp for ins in decoder.disasm(memory[start:start+32],start)
               if ins.mnemonic=='mov' and len(ins.operands)==2 and ins.operands[1].type==X86_OP_REG and ins.operands[1].reg==X86_REG_BL for op in ins.operands[:1]
               if op.type==X86_OP_MEM and op.mem.segment==X86_REG_CS]
        if len(flags)!=1:raise ValueError('Keyboard-hook flag binding is not unique')
        tick_segment=int.from_bytes(memory[sites['SeedSRand']-2:sites['SeedSRand']],'little')
        points.append(('O',tick_segment*16+flags[0]))
        start=base+addresses['input_enqueue_event']
        stamps=[i.address for i in decoder.disasm(memory[start:start+200],start)
                if i.mnemonic=='mov' and i.op_str=='bx, word ptr es:[0x6c]']
        if len(stamps)!=1: raise ValueError('Event BIOS timestamp read is not unique')
        points.append(('V',stamps[0]))
        # Countdown reads in the two source helpers, before the instruction.
        points+=countdown_points(memory,base,addresses,sites)
        compact_spec=out.with_suffix('.observer')
        compact_spec.write_text(str(out/'observer.txt')+'\n'+''.join(f'{k} {pc:X}\n' for k,pc in points))
        if args.state_schema:
            state=json.loads(args.state_schema.read_text())
            side='original_address' if args.original else 'canonical_address'
            with compact_spec.open('a') as config:
                config.write(f'L {args.steps} {args.dump_every}\n')
                for item in state['items']:
                    config.write(f'H {base+item[side]:X} {item["bytes"]} {int(item["sentinel"])}\n')
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
                  observation_script_sha256=sha(script),
                  execution_report_sha256=sha(out/'execution-report.json'),
                  installed_script_sha256=sha(out/'INPUT.SCR'),
                  scope='Original input script; read-only step hashes, periodic frames, all per-site clock values and actual input positions.',
                  command=command,returncode=run.returncode,
                  snapshots={p.name:sha(p) for p in sorted(out.glob('exec-*.bin'))},
                  metadata={p.name:sha(p) for p in sorted(out.glob('exec-*.json'))})
    if args.state_schema:
        manifest['state_schema_sha256']=sha(args.state_schema)
    if compact_spec:
        captured=(out/'exec-simstep.1.bin').read_bytes()
        actual=int.from_bytes(captured[0x58:0x5a],'little')+16*int.from_bytes(captured[0x5a:0x5c],'little')
        stub=captured[actual:actual+6]
        if actual!=bios_entry or len(stub)!=6 or stub[:3]!=bytes.fromhex('fb fe 38') or stub[5]!=0xcf:
            raise ValueError('Captured BIOS INT16 callback differs from its bound vector/CB_INT16 opcode')
        manifest['bios_keyboard_sample']=dict(vector=actual,callback_pc=actual+1,stub_sha256=__import__('hashlib').sha256(stub).hexdigest(),
            peek_return=next(pc for kind,pc in points if kind=='p'),read_return=next(pc for kind,pc in points if kind=='q'))
        manifest['compact_observer']=dict(specification_sha256=sha(compact_spec),points=points,pump_source='both',
            order_sha256=sha(out/'observer.txt.order'),order_contract='service-samples-v4',
            trace_sha256=sha(out/'observer.txt'),trace_bytes=(out/'observer.txt').stat().st_size,
            runner_receipt_sha256=sha(args.compact_observer))
    (out/'boundary-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps(manifest,indent=2))
    return run.returncode
if __name__=='__main__': raise SystemExit(main())
