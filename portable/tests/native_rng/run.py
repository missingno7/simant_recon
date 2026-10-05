"""Actual current canonical native RNG vs hash-locked original DOS helpers.

Consume a completed portable/build.py report. No archived build, generator or
selected model RNG is imported. The fixture links the build's actual root0093
object and installed service objects, with dependency closure from their symbols.
"""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import argparse
import hashlib
import json
import os
import subprocess
import sys
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
SEEDS = [0,1,7,0x3751,0x7fff,0x8000,0xffff,0xace1]
OPS = [('SRand1',1),('SRand4',0),('SRand256',0),('SRand1',17),
       ('SRand2',0),('SRand128',0),('SRand1',65535),('SRand1',32768),
       ('SGIRand',127),('SGRand',127),('SGSRand',31),('RRand',32767),
       ('SRand8',0),('SRand16',0),('SRand32',0),('SRand64',0)]
SCENARIOS = [{'mode':0,'seed':s,'tick1':0,'tick2':0} for s in SEEDS] + [
    {'mode':1,'seed':s,'tick1':a,'tick2':z}
    for s,a,z in [(7,0,0),(7,1,1),(7,65535,65536),(0x12345678,0x12345678,0x12345679)]]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def execute(command):
    run = subprocess.run(command, capture_output=True, text=True)
    if run.returncode:
        raise RuntimeError('command failed: ' + str(command) + '\n' + run.stdout + run.stderr)
    return run


def row_path(value, report_path):
    path = Path(value)
    return path if path.is_absolute() else report_path.parent/path


def object_path(row, report_path):
    command = row['compile']['command']
    return row_path(command[command.index('-o')+1], report_path)


def native(report, report_path, out, nm):
    matches = [r for r in report['canonical_TUs'] if r['source']=='src/root/m0093.c']
    if len(matches)!=1 or not matches[0].get('compile',{}).get('passed'):
        raise ValueError('one compiled current canonical root:m0093 is required')
    root = matches[0]
    command = root['compile']['command'][:]
    source = row_path(root['generated'],report_path)
    # Preserve the build's width/packing/include options, replacing only its
    # source and object output for the test fixture.
    source_index = command.index(root['generated'])
    command[source_index] = str(HERE/'fixture.c')
    fixture_object = out/'fixture.o'
    command[command.index('-o')+1] = str(fixture_object)
    execute(command)
    services = [r for r in report['native_services'] if r.get('compile',{}).get('passed')]
    objects = [(r,object_path(r,report_path)) for r in [root]+services]
    def symbols(item):
        row,path = item
        output = execute([nm,'-g','--format=posix',str(path)]).stdout
        definitions,imports=set(),set()
        for line in output.splitlines():
            cells=line.split()
            if len(cells)>=2:
                (imports if cells[1]=='U' else definitions).add(cells[0])
        return path,row,definitions,imports
    with ThreadPoolExecutor(max_workers=8) as pool:
        inventory=list(pool.map(symbols,objects+[(dict(source='native RNG fixture'),fixture_object)]))
    providers={}
    for path,row,definitions,imports in inventory:
        for name in definitions:
            providers.setdefault(name,[]).append(path)
    lookup={p:(r,d,u) for p,r,d,u in inventory}
    chosen={fixture_object,object_path(root,report_path)}
    pending=list(chosen)
    while pending:
        path=pending.pop()
        for name in lookup[path][2]:
            candidates=providers.get(name,[])
            # Fixture TickCount is the deliberate controlled clock boundary.
            if any(x in chosen for x in candidates):
                continue
            if len(candidates)>1:
                raise ValueError('ambiguous actual object provider for '+name)
            if candidates and candidates[0] not in chosen:
                chosen.add(candidates[0]);pending.append(candidates[0])
    binary=out/('native-rng.exe' if os.name=='nt' else 'native-rng')
    execute([command[0],*map(str,sorted(chosen)),'-o',str(binary)])
    run=execute([str(binary)])
    (out/'native-trace.csv').write_text(run.stdout)
    rows=[[int(v) for v in line.split(',')] for line in run.stdout.splitlines()]
    zero=subprocess.run([str(binary),'--srand1-zero'],capture_output=True,text=True,timeout=10)
    receipts=[{'source':lookup[p][0]['source'],'object':str(p),'object_sha256':sha(p),
               'generated':lookup[p][0].get('generated'),
               'generated_sha256':sha(row_path(lookup[p][0]['generated'],report_path))
                    if lookup[p][0].get('generated') else sha(HERE/'fixture.c')}
              for p in sorted(chosen)]
    return rows,receipts,{'native_exit_code':zero.returncode,
                        'native_successful_zero_divisor_return_rejected':zero.returncode!=0}


def oracle(root, out):
    sys.path.insert(0,str(root/'tools'))
    import behavior as b
    import functions
    import exe
    pair=SimpleNamespace(function=functions.get('SRand1'),
                         vectors={exe.MANAGER_SEG*16+v.offset:v for v in exe.load().vectors})
    machine=b.Machine(pair)
    seed_at=b.symbol_address('g_8BA2')
    rows=[]
    for index,c in enumerate(SCENARIOS):
        machine.run(b.Case('CRT seed',args=[1],return_kind='void'),original_entry=b.symbol('srand'))
        tick_at=[0]
        def tick(machine,args):
            value=[c['tick1'],c['tick2']][tick_at[0]];tick_at[0]+=1
            return value&65535,value>>16
        if c['mode']:
            case=b.Case('SeedRRand',callbacks={'TickCount':b.Callback(0,tick)},return_kind='void')
            name='SeedRRand'
        else:
            case=b.Case('SetSRandSeed',args=[c['seed']],return_kind='void');name='SetSRandSeed'
        machine.run(case,preserve=True,original_entry=b.symbol(name))
        rows.append([index,-1,0,machine.word(seed_at),tick_at[0]])
        n=0
        for _ in range(16):
            for name,arg in OPS:
                case=b.Case(name,args=[arg] if name in {'SRand1','SGIRand','SGRand','SGSRand','RRand'} else [])
                result=machine.run(case,preserve=True,original_entry=b.symbol(name))
                rows.append([index,n,result['return'],machine.word(seed_at),tick_at[0]]);n+=1
        machine.write(0x46c0,c['seed'].to_bytes(4,'little'))
        result=machine.run(b.Case('GetRRandSeed',return_kind='u32'),preserve=True,original_entry=b.symbol('GetRRandSeed'))
        rows.append([index,99999,result['return'],machine.word(seed_at),tick_at[0]])
    # This existing zero-divisor control checks an actual excluded DOS domain;
    # it is not a mutated/modeled alternative RNG implementation.
    machine.run(b.Case('SetSRandSeed',args=[0xa55a],return_kind='void'),original_entry=b.symbol('SetSRandSeed'))
    fault=None
    try:
        machine.run(b.Case('SRand1 zero',args=[0]),preserve=True,original_entry=b.symbol('SRand1'))
    except b.ExecutionError as exc:
        fault=str(exc)
    zero={'original_fault':fault,'original_private_seed_after_fault':machine.word(seed_at),
          'original_divide_fault_observed':bool(fault and any(x in fault.lower() for x in
              ['divide','unmodeled interrupt 00','unmodeled interrupt 08']))}
    (out/'original-dos-trace.csv').write_text('\n'.join(','.join(map(str,r)) for r in rows)+'\n')
    return rows,zero,{'EXE_sha256':exe.EXPECTED_SHA256,'VM_source_sha256':sha(root/'tools/behavior.py')}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report',type=Path,required=True,help='Completed current native build report.json')
    parser.add_argument('--out',type=Path,default=HERE.parents[2]/'build/current/tests/rng')
    parser.add_argument('--nm',help='nm compatible with the report compiler')
    args=parser.parse_args()
    root=next(p for p in HERE.parents if (p/'src/program.json').is_file())
    report_path=args.report.resolve();out=args.out.absolute()
    sys.path.insert(0,str(root/'tools'))
    from workspace import prepare_output
    prepare_output(out,root/'build/current/tests/rng',root)
    report=json.loads(report_path.read_text())
    if report.get('schema')!='canonical-native-complete-attempt-v1':raise ValueError('unsupported current native build report')
    if not report.get('passed') or not report['input_stability']['at_end']:
        raise ValueError('successful stable current native build required')
    for name, expected_sha in report['input_pins'].items():
        if sha(root/name)!=expected_sha:raise ValueError('native build input changed: '+name)
    program=json.loads((root/'src/program.json').read_text())
    module=next(x for x in program['modules'] if x['source']=='src/root/m0093.c')
    if sha(root/module['source'])!=module['source_sha256']:raise ValueError('current canonical RNG source differs from program inventory')
    cc=next(r for r in report['canonical_TUs'] if r['source']==module['source'])['compile']['command'][0]
    nm=args.nm or str(Path(cc).with_name('nm.exe' if Path(cc).suffix.lower()=='.exe' else 'nm'))
    actual,objects,native_zero=native(report,report_path,out,nm)
    expected,original_zero,oracle_identity=oracle(root,out)
    mismatch=[{'row':i,'native':a,'original_DOS':z} for i,(a,z) in enumerate(zip(actual,expected)) if a!=z]
    negative={**native_zero,**original_zero,'origin':'SRand1 zero-divisor domain control retained in this current native/DOS fixture'}
    passed=(len(actual)==len(expected)==3096 and not mismatch and negative['original_divide_fault_observed']
            and negative['native_successful_zero_divisor_return_rejected'])
    result={'schema':'canonical-native-rng-original-dos-v1','passed':passed,
        'claim':'Bounded execution of actual current canonical game RNG and CRT objects against original DOS helpers; no world/frame equivalence claim.',
        'build_report':str(report_path),'build_report_sha256':sha(report_path),
        'canonical_source':module['source'],'canonical_source_sha256':module['source_sha256'],
        'runner_sha256':sha(Path(__file__)),'fixture_sha256':sha(HERE/'fixture.c'),
        'oracle':oracle_identity,'native_objects':objects,'scenarios':SCENARIOS,'operations':OPS,
        'repeats_per_scenario':16,'trace_rows':len(actual),'original_trace_rows':len(expected),
        'mismatches':mismatch,'existing_negative_domain_control':negative,
        'controlled_boundaries':['TickCount specified32-bit values','physical seed reader specified32-bit values'],
        'archived_build_dependencies':[],'selected_model_RNG_functions_execute':False}
    (out/'report.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'passed':passed,'trace_rows':len(actual),'mismatches':len(mismatch),
                      'negative_domain_control_passed':negative['original_divide_fault_observed'] and negative['native_successful_zero_divisor_return_rejected'],
                      'report':str(out/'report.json')},indent=2))
    return 0 if passed else 1


if __name__=='__main__':
    raise SystemExit(main())
