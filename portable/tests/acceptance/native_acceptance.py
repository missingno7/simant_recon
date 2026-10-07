"""Deterministic native-vs-canonical-DOS observations; no similarity acceptance.

The original scenario inputs are retained. Equal-time snapshots are diagnostics;
step-aligned snapshots require an observed common simulation boundary.
"""
from __future__ import annotations
import argparse, hashlib, json, os, re, shutil, subprocess, sys
from pathlib import Path

TOOL_DIR = Path(__file__).resolve().parent
ROOT = TOOL_DIR.parents[2]
sys.path.insert(0,str(ROOT))
from dos import acceptance
if __package__:
    from .canonical_dos_layout import canonical_layout
    from .state_policy import state_prefix, G5702_STACK_RESIDUE_TAIL
else:
    from canonical_dos_layout import canonical_layout
    from state_policy import state_prefix, G5702_STACK_RESIDUE_TAIL
DESCRIPTOR_OWNERS=('db_handles','fd_50F6_10D0')

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def input_operations(path):
    return [tuple(p) for line in path.read_text().splitlines()
            if (p:=line.split('#',1)[0].split()) and p[1] in
            ('key','keydown','keyup','mouse_move','mouse_button','exit')]

def oracle_provenance(directory,exe_sha,original_script=None):
    receipt_path=directory/'execution-report.json'
    receipt=json.loads(receipt_path.read_text())
    if not any(i.get('sha256')==exe_sha and i.get('path','').upper().endswith('SOURCE.EXE')
               for i in receipt.get('inputs',[])):
        raise ValueError('DOS observation executable identity differs: '+str(directory))
    script=directory/'INPUT.SCR'
    if original_script and input_operations(script)!=input_operations(original_script):
        raise ValueError('DOS/native scenario input operations differ: '+str(directory))
    return dict(execution_report_sha256=sha(receipt_path),executable_sha256=exe_sha,
                observation_script_sha256=sha(script),
                original_input_operations_verified=bool(original_script),
                saved_game_sha256=receipt.get('staged_saved_game',{}).get('source',{}).get('sha256'))

def inventory(project=ROOT, oracle_root=ROOT, dos_report=None):
    if len({sha(p/'src/program.json') for p in (project,oracle_root,ROOT)})!=1:
        raise ValueError('canonical program inventories differ; no cross-generation observation')
    program = json.loads((project/'src/program.json').read_text())
    symbols, errors = canonical_layout(oracle_root,dos_report or oracle_root/'build/current/dos/build-report.json')
    if errors: raise ValueError('unresolved canonical DOS data placement: '+str(errors))
    aliases = {s['alias'].lstrip('_@'):s for s in program['aliases'] if s['kind']!='code'}
    lengths = {}
    for module in program['modules']:
        for c in module.get('storage_contract',{}).get('communals',[]):
            lengths[c['name'].lstrip('_@')] = c['length']
    result = {}
    for name, spec in sorted(symbols.items()):
        item = dict(spec)
        if '::' in name and not item.get('native_expr'):
            item['native_file']=re.sub(r'[:@]','_',spec['module'])+'.c'
        if name in aliases:
            alias = aliases[name]
            item.update(owner=alias.get('target',alias.get('owner')).lstrip('_@'),offset=alias.get('offset',0))
        if name in lengths: item.setdefault('bytes',lengths[name])
        result[name] = item
    for name,alias in aliases.items():
        target=alias.get('target',alias.get('owner')).lstrip('_@')
        if name not in result and target in result:
            item=dict(result[target],owner=target,offset=alias.get('offset',0))
            item['dos_address']+=alias.get('offset',0)
            item['address_evidence']='src/program.json reviewed alias + canonical target address'
            if alias.get('view',{}).get('DOS_view_extent_bytes') is not None:
                item['bytes']=alias['view']['DOS_view_extent_bytes']
            result[name]=item
    return result

KEYS = {'enter':'Return','space':'Space','esc':'Escape','backspace':'Backspace',
        'kp_5':'Keypad 5','down':'Down','up':'Up','left':'Left','right':'Right'}

def replay(scenario,project,out,checkpoints):
    rows = []
    # DOSBox mouse_move supplies relative mickeys. VGA BIOS 8 mickeys/8
    # horizontal pixels, 16 mickeys/8 vertical pixels; DOSBox's script hook
    # scales the supplied movement. This mapping is a premise to be tested.
    for line in (project/scenario['script']).read_text().splitlines():
        parts = line.split('#',1)[0].split()
        if not parts: continue
        ms,op = int(parts[0]),parts[1]
        if op in ('key','keydown','keyup'):
            key = KEYS.get(parts[2],parts[2])
            if parts[2].startswith('kp_'): key='Keypad '+parts[2][3:]
            if op in ('key','keydown'): rows.append((ms,'down '+key))
            if op == 'key': rows.append((ms+50,'up '+key))
            elif op == 'keyup': rows.append((ms,'up '+key))
        elif op == 'mouse_move':
            rows.append((ms,f'relative {parts[2]} {parts[3]}'))
        elif op == 'mouse_button':
            button={'0':'Left','1':'Right','2':'Middle'}[parts[2]]
            rows.append((ms,f'button-{parts[3]} {button}'))
        elif op == 'exit': rows.append((ms,'exit'))
        else: raise ValueError('Unsupported scenario operation: '+op)
    rows.extend((ms,'checkpoint') for ms in checkpoints)
    rows.sort(key=lambda r:r[0])
    path = out/'replay.txt'
    path.write_text('\n'.join(f'{ms} {op}' for ms,op in rows)+'\n')
    return path

def differences(a,b):
    if len(a)!=len(b): return dict(status='SIZE_MISMATCH',sizes=[len(a),len(b)])
    positions=[i for i,(x,y) in enumerate(zip(a,b)) if x!=y]
    if not positions: return dict(status='EQUAL',bytes=len(a))
    first=positions[0]
    result=dict(status='DIFFERS',bytes=len(a),differing_bytes=len(positions),
                first_offset=first,dos_byte=a[first],native_byte=b[first],
                max_byte_delta=max(abs(a[i]-b[i]) for i in positions),
                examples=[dict(offset=i,dos=a[i],native=b[i]) for i in positions[:8]])
    if len(a) in (1,2,4):
        da,nb=int.from_bytes(a,'little'),int.from_bytes(b,'little')
        result.update(dos_unsigned=da,native_unsigned=nb,unsigned_delta=nb-da)
    return result

def save_differences(a,b):
    result=acceptance.compare_saves(a,b)
    for row in result.get('differences',[]):
        _,offset,length,_,_=acceptance.save_schema()[row['record']]
        row['detail']=differences(a[offset:offset+length],b[offset:offset+length])
        if length in (1,2,4):
            row.update(dos_unsigned=int.from_bytes(a[offset:offset+length],'little'),
                       native_unsigned=int.from_bytes(b[offset:offset+length],'little'))
    return result

def memory_base(memory,addresses):
    hits=[m.start() for m in re.finditer(re.escape(acceptance.SCREEN_CLIP_PATTERN),memory)]
    bases={h-addresses['g_5A9C'] for h in hits}
    if len(bases)!=1: raise ValueError('nonunique canonical DOS runtime base: '+str(bases))
    return bases.pop()

def compare_checkpoint(native,dump,addresses,specs,raw_state):
    exclusions,unavailable={},{}
    if not native.is_file() or not dump.is_file():
        return dict(status='MISSING',present=[dump.is_file(),native.is_file()]),exclusions,unavailable
    snapshot=json.loads(native.read_text());memory=dump.read_bytes();base=memory_base(memory,addresses)
    dsave=acceptance.virtual_save(memory,addresses)
    save_path=native.with_suffix('.sav');raw_path=native.with_suffix('.raw-save.sav')
    save_delta=save_differences(dsave,save_path.read_bytes()) if save_path.exists() else dict(
        status='PROJECTION_UNAVAILABLE',errors=snapshot.get('save_projection_errors',[]))
    native.with_name(native.stem+'-dos.sav').write_bytes(dsave)
    row=dict(save=save_delta,raw_save=save_differences(dsave,raw_path.read_bytes()) if raw_path.exists() else None,
             symbols={},clocks=snapshot['clocks'],partial_exclusions={},flagged_address_words={},
             dos_bios_ticks=int.from_bytes(memory[0x46c:0x470],'little'),
             dos_dump=dict(path=str(dump.resolve()),sha256=sha(dump)))
    for name,observed in snapshot['symbols'].items():
        if specs[name].get('owner',name) in DESCRIPTOR_OWNERS:
            exclusions[name]=dict(status='EXCLUDED_HANDLE',owner=specs[name].get('owner',name),
                reason='Canonical database and startup resource file descriptors identify platform-owned slots.')
            continue
        status=observed['status']
        if status.startswith('EXCLUDED_'):
            exclusions[name]=observed; continue
        if status!='OK' or name not in specs:
            unavailable[name]=observed if status!='OK' else dict(status='DOS_MAP_MISSING');continue
        length=observed['bytes']; start=base+specs[name]['dos_address']
        if start<0 or start+length>len(memory):
            unavailable[name]=dict(status='DOS_EXTENT_OUTSIDE_DUMP');continue
        a,b=memory[start:start+length],bytes.fromhex(observed['data'])
        da,nb,policy=state_prefix(name,a,b,raw_state)
        row['symbols'][name]=differences(da,nb)
        if policy: row['partial_exclusions'][name]=dict(policy,raw_difference=differences(a,b))
        if name in ('fd_55B3_6B9C','fd_55B3_6B9E','fd_55B3_74AD','fd_55B3_74AF','fd_55B3_74B1',
                    'fd_55B3_74B3','fd_55B3_74B5','fd_55B3_74B7','fd_55B3_74B9'):
            row['flagged_address_words'][name]=dict(reason='src/root/m28BC.asm OFFSET word; native asm_data.py preserves symbolic address metadata. Raw address equality is not handler/state identity.',
                                                    raw_difference=row['symbols'][name])
    row['differing_symbols']=[name for name,r in row['symbols'].items() if r['status']!='EQUAL']
    row['compared_symbols']=len(row['symbols'])
    row['status']='DIFFERS' if row['differing_symbols'] or row['save']['status']!='EQUAL' or \
        row['raw_save'] and row['raw_save']['status']!='EQUAL' else 'EQUAL_SUBSET'
    return row,exclusions,unavailable


def compare_steps(directory,out,addresses,specs,raw_state,run,exe_sha):
    manifest=json.loads((directory/'boundary-manifest.json').read_text())
    if manifest.get('boundary')!='DoAntSim:entry' or manifest.get('executable_sha256')!=exe_sha or \
            manifest.get('input_script_sha256')!=run.get('script_sha256') or \
            manifest.get('scenario_sha256')!=run.get('scenario_sha256'):
        raise ValueError('DOS/native step provenance differs')
    replay_rows=[l.split(maxsplit=1) for l in (out/'replay.txt').read_text().splitlines()]
    inputs=lambda rows:[r for r in rows if r[1].split()[0] not in ('checkpoint','exit')]
    rows={}
    for step in range(1,manifest['steps']+1):
        dump=directory/f'exec-simstep.{step}.bin';native=out/'checkpoints'/f'step{step}.json'
        if dump.exists() and manifest['snapshots'].get(dump.name)!=sha(dump):
            raise ValueError('DOS step dump identity differs: '+dump.name)
        row,_,_=compare_checkpoint(native,dump,addresses,specs,raw_state)
        if dump.exists():
            meta=json.loads(dump.with_suffix('.json').read_text())
            if meta.get('hit')!=step or meta.get('dump_address')!='0x00000000': raise ValueError('DOS step observation shape differs')
            memory=dump.read_bytes();base=memory_base(memory,addresses);at=base+specs['Cycle']['dos_address']
            cycle=int.from_bytes(memory[at:at+2],'little')
            at=base+specs['fd_50F6_0C26']['dos_address']
            calls=int.from_bytes(memory[at:at+4],'little')
            row['dos_boundary']=dict(ordinal=step,milliseconds=meta['emulated_ms'],cycle=cycle,simulation_calls=calls,
                                     dump_sha256=sha(dump))
        if row['status']!='MISSING':
            snapshot=json.loads(native.read_text())
            dos_prefix=sum(int(r[0])<=meta['emulated_ms'] for r in inputs(replay_rows))
            native_prefix=len(inputs(replay_rows[:snapshot['replay_next']]))
            row['alignment']=dict(boundary='DoAntSim:entry',ordinal=step,dos_ms=meta['emulated_ms'],
                native_ms=snapshot['milliseconds'],input_prefix_counts=[dos_prefix,native_prefix],
                cycle=[cycle,snapshot['clocks']['cycle']],
                simulation_calls=[calls,snapshot['clocks']['simulation_calls']],
                status='COMMON_BOUNDARY' if dos_prefix==native_prefix and cycle==snapshot['clocks']['cycle'] and calls==snapshot['clocks']['simulation_calls'] else 'ALIGNMENT_PREMISE_FAILED')
        rows[str(step)]=row
    return dict(boundary='DoAntSim:entry',checkpoints=rows,
                first_diverging_step=next((int(n) for n,r in rows.items() if r['status']=='DIFFERS'),None),
                first_missing_step=next((int(n) for n,r in rows.items() if r['status']=='MISSING'),None),
                first_alignment_failed_step=next((int(n) for n,r in rows.items() if r.get('alignment',{}).get('status')=='ALIGNMENT_PREMISE_FAILED'),None),
                status='FAIL' if any(r['status']!='EQUAL_SUBSET' or r['alignment']['status']!='COMMON_BOUNDARY' for r in rows.values()) else 'INCOMPLETE_EQUAL_SUBSET')


def compare(scenario,out,dos,map_path,specs,checkpoints,extra_dos=(),raw_state=False,dos_steps=None,exe_sha=None):
    addresses=acceptance.record_addresses(map_path)
    result=dict(schema='simant-native-dos-differential-v1',scenario=scenario['id'],
                clock_mapping='1 ms per guarded outer platform poll; DOS computation cost unmodelled',
                closure_eligible=False,checkpoints={},saves={},exclusions={},unavailable={},
                state_exclusion_policy=[] if raw_state else [G5702_STACK_RESIDUE_TAIL])
    run_path=out/'run.json'
    if run_path.exists():
        result['run']=json.loads(run_path.read_text())
        result['clock_mapping']=str(result['run']['poll_ns'])+' ns per guarded outer platform poll; DOS computation cost unmodelled'
    result['dos_provenance']=oracle_provenance(dos,exe_sha,ROOT/scenario['script'])
    result['extra_dos_provenance']=[oracle_provenance(p,exe_sha) for p in extra_dos]
    saved_input=out/'save-input.json'
    if scenario.get('saved_game') and (not saved_input.exists() or
            json.loads(saved_input.read_text())['sha256']!=result['dos_provenance']['saved_game_sha256']):
        raise ValueError('DOS/native original saved-game identities differ')
    first=None;missing=None
    for ms in checkpoints:
        native=out/'checkpoints'/f'cp{ms}.json'; dump=dos/f'dump-cp{ms}'
        if not dump.is_file():
            dump=next((p/f'dump-cp{ms}' for p in extra_dos if (p/f'dump-cp{ms}').is_file()),dump)
        row,excluded,unavailable=compare_checkpoint(native,dump,addresses,specs,raw_state)
        result['exclusions'].update(excluded);result['unavailable'].update(unavailable)
        if first is None and row['status']=='DIFFERS': first=ms
        if missing is None and row['status']=='MISSING': missing=ms
        result['checkpoints'][str(ms)]=row
    result['steps']=compare_steps(dos_steps,out,addresses,specs,raw_state,result['run'],exe_sha) if dos_steps else dict(
        status='UNCOMPARED',boundary='DoAntSim:entry',native_entries=len(list((out/'checkpoints').glob('step*.json'))),
        reason='Provide --dos-steps with matching execution-triggered DOS observations; equal milliseconds are diagnostic only.')
    for name in scenario['saves']:
        a=dos/name; b=out/'assets'/name
        if a.is_file() and b.is_file(): result['saves'][name]=save_differences(a.read_bytes(),b.read_bytes())
        else: result['saves'][name]=dict(status='MISSING',present=[a.is_file(),b.is_file()])
    result['first_diverging_checkpoint']=first
    result['first_missing_checkpoint']=missing
    exit_path=out/'checkpoints/exit.json'
    result['native_exit']=json.loads(exit_path.read_text()) if exit_path.exists() else None
    result['pointer_and_handle_exclusions']=sorted(result['exclusions'])
    exit_failed=result['native_exit'] is None or result['native_exit']['exit_code']!=0 or result.get('run',{}).get('timed_out',False)
    result['status']='FAIL' if first is not None or missing is not None or exit_failed or result['steps']['status']=='FAIL' or any(r['status']!='EQUAL' for r in result['saves'].values()) else 'INCOMPLETE_EQUAL_SUBSET'
    (out/'excluded-fields.json').write_text(json.dumps(result['exclusions'],indent=2)+'\n')
    (out/'acceptance.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(status=result['status'],first_checkpoint=first,
                         differing_symbols={ms:r.get('differing_symbols',[])[:20] for ms,r in result['checkpoints'].items()},
                         saves={name:r['status'] for name,r in result['saves'].items()}),indent=2))
    return result

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('scenario',type=Path)
    ap.add_argument('--project',type=Path,default=ROOT)
    ap.add_argument('--build',type=Path,default=ROOT/'build/current/portable')
    ap.add_argument('--oracle-root',type=Path,default=ROOT,help='Project containing the linked canonical DOS inputs')
    ap.add_argument('--dos-build-report',type=Path)
    ap.add_argument('--dos',type=Path,required=True,help='Retained canonical DOS scenario output directory')
    ap.add_argument('--dos-steps',type=Path,help='Execution-triggered observations from capture_dos_steps.py')
    ap.add_argument('--saved-game',type=Path,help='Explicit copy of the scenario original save, for isolated checkouts')
    ap.add_argument('--extra-dos',type=Path,action='append',default=[])
    ap.add_argument('--out',type=Path,default=ROOT/'build/current/tests/native-acceptance')
    ap.add_argument('--gdb',default='C:/msys64/mingw64/bin/gdb.exe')
    ap.add_argument('--poll-ns',type=int,default=1000000)
    ap.add_argument('--timeout',type=int,default=600)
    ap.add_argument('--compare-only',action='store_true')
    ap.add_argument('--raw-state',action='store_true',help='Diagnose all bytes, including the named stack-residue tail')
    ap.add_argument('--step-count',type=int,default=8,help='Observe the first N DoAntSim entries, independently of milliseconds')
    args=ap.parse_args();scenario=json.loads(args.scenario.read_text())
    if not 0<=args.step_count<=64 or not 1<=args.poll_ns<=1000000 or args.timeout<1:
        ap.error('step-count must be 0..64, poll-ns 1..1000000 and timeout positive')
    oracle_root=args.oracle_root.resolve()
    dos_report=(args.dos_build_report or oracle_root/'build/current/dos/build-report.json').resolve()
    receipt=json.loads(dos_report.read_text())
    map_path=(oracle_root/receipt['link']['candidate_executable']['path']).with_name('SOURCE.MAP')
    out=args.out.resolve(); project=args.project.resolve();build=args.build.resolve()
    dos=args.dos.resolve()
    checkpoints=scenario.get('checkpoints',[]) or [14000,22000,40000,49000]
    specs=inventory(project,oracle_root,dos_report)
    if not args.compare_only:
        sys.path.insert(0,str(ROOT/'tools'))
        from workspace import prepare_output
        prepare_output(out,ROOT/'build/current/tests/native-acceptance',ROOT)
        shutil.copytree(build/'runtime-assets',out/'assets')
        if scenario.get('saved_game'):
            source_save=(args.saved_game or oracle_root/scenario['saved_game']).resolve()
            shutil.copyfile(source_save,out/'assets/A.ANT')
            (out/'save-input.json').write_text(json.dumps(dict(path=str(source_save),sha256=sha(source_save)),indent=2))
        script=replay(scenario,project,out,checkpoints)
        cfg=out/'observe.json';cfg.write_text(json.dumps(dict(out=str(out/'checkpoints'),symbols=specs,save_schema=acceptance.save_schema(),step_count=args.step_count)))
        (out/'symbol-inventory.json').write_text(json.dumps(specs,indent=2)+'\n')
        gdbscript=out/'observe.gdb'
        gdbscript.write_text('python\nimport sys\nsys.path.insert(0,'+repr(str(TOOL_DIR))+')\nCONFIG_PATH='+repr(str(cfg))+'\nexec(compile(open('+repr(str(TOOL_DIR/'observe_gdb.py'))+').read(), "observe_gdb.py", "exec"))\nend\n')
        cmd=[args.gdb,'-batch','-x',str(gdbscript),'--args',str(build/'simant-canonical.exe'),
             '--headless','--deterministic','--poll-ns',str(args.poll_ns),'--assets',str(out/'assets'),'--input-script',str(script),
             *scenario.get('arguments',[])]
        timed_out=False
        with (out/'native.log').open('w') as log:
            run=subprocess.Popen(cmd,cwd=project,stdout=log,stderr=subprocess.STDOUT)
            try: run.wait(timeout=args.timeout)
            except subprocess.TimeoutExpired:
                timed_out=True
                # Own the GDB process handle; taskkill /T needs restricted WMI
                # enumeration here. Windows terminates its debuggee when the
                # debugger exits, and the bounded control verifies both stop.
                run.kill()
                run.wait(timeout=30)
        (out/'run.json').write_text(json.dumps(dict(command=cmd,returncode=run.returncode,timed_out=timed_out,executable_sha256=sha(build/'simant-canonical.exe'),
                                                  source_arguments=scenario.get('arguments',[]),dos_executable_sha256=receipt['link']['candidate_executable']['sha256'],
                                                  poll_ns=args.poll_ns,scenario_sha256=sha(args.scenario),script_sha256=sha(project/scenario['script'])),indent=2))
    status=compare(scenario,out,dos,map_path,specs,checkpoints,args.extra_dos,args.raw_state,args.dos_steps,
                   receipt['link']['candidate_executable']['sha256'])['status']
    return 1 if status=='FAIL' else 2 # A matching incomplete subset is never acceptance.
if __name__=='__main__': raise SystemExit(main())
