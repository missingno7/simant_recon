"""Trace production AddRandAntLion; disable only sequencing for the control."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[3];HERE=Path(__file__).parent
sys.path[:0]=[str(ROOT/'portable'),str(ROOT/'tools')]
from canonical_native_abi import integer_frontend as f
from workspace import prepare_output


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def execute(command,out,log):
    run=subprocess.run(command,cwd=out,capture_output=True,text=True,timeout=120)
    (out/log).write_text(run.stdout+run.stderr)
    if run.returncode:raise RuntimeError(str(command)+'\n'+run.stderr[-4000:])
    return run


def lane(report,out,row,control=False):
    out.mkdir();objects=list(report['core_link']['object_inputs']);cc=report['core_link']['command'][0]
    if control:
        # The builder retains its exact pre-expression whole TU; disable only
        # sequencing and keep every integer/type lowering and compile flag.
        input_path=Path(row['integer_expression_input'])
        source=input_path.read_text(encoding='latin1')
        if hashlib.sha256(source.encode('latin1')).hexdigest()!=row['integer_expressions']['input_sha256']:
            raise ValueError('pre-expression source differs from production receipt')
        build=Path(row['generated']).parent
        dirs=[build/'include',ROOT/'include',ROOT,build,ROOT/'portable/whole_program']
        text,receipt=f.convert(source,Path(row['generated']).as_posix(),cc,dirs,
                               canonical_source=row['source'],sequence_effects=False)
        changed=out/'unsequenced.c';changed.write_text(text,encoding='latin1')
        obj=out/'unsequenced.o';args=list(row['compile']['command'])
        args[args.index('-c')+1]=str(changed);args[args.index('-o')+1]=str(obj)
        execute(args,out,'control-compile.log')
        objects=[str(obj) if p==row['object'] else p for p in objects]
        (out/'control-receipt.json').write_text(json.dumps(receipt['evaluation_order'],indent=2)+'\n')
    rsp=out/'objects.rsp';rsp.write_text(''.join('"'+Path(p).as_posix()+'"\n' for p in objects))
    binary=out/'rng-order.exe'
    hosting_wraps=[arg for arg in report['application_link']['command']
                   if arg.startswith('-Wl,--wrap=') and arg!='-Wl,--wrap=exit']
    command=[cc,'-fno-lto','-g',str(HERE/'fixture.c'),'-Wl,@objects.rsp',
             *hosting_wraps,'-Wl,--wrap=SRand1','-Wl,--wrap=IsClear3x3','-static','-lstdc++',
             str(Path(report['sdk']['path'])/'lib/libSDL3.dll.a'),'-o',str(binary)]
    execute(command,out,'link.log')
    env=dict(os.environ);env['PATH']=str(Path(report['sdk']['path'])/'bin')+os.pathsep+env.get('PATH','')
    run=subprocess.run([str(binary)],cwd=out,env=env,capture_output=True,text=True,timeout=30)
    (out/'trace.txt').write_text(run.stdout+run.stderr)
    if run.returncode:raise ValueError('production fixture failed: '+str(run.returncode))
    return dict(trace=[int(s) for s in run.stdout.splitlines()],executable_sha256=sha(binary),command=command)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--report',type=Path,default=ROOT/'build/current/portable/report.json')
    ap.add_argument('--out',type=Path,required=True)
    args=ap.parse_args();report=json.loads(args.report.read_text())
    if not report['passed'] or not report['input_stability']['at_end']:raise ValueError('successful stable build required')
    for name,pin in report['input_pins'].items():
        if sha(ROOT/name)!=pin:raise ValueError('native input changed: '+name)
    out=prepare_output(args.out.absolute(),ROOT/'build/current/tests/evaluation-order',ROOT)
    row=next(r for r in report['canonical_TUs'] if r['source']=='src/simulation/yard_creatures.c')
    pins={p:sha(p) for p in report['core_link']['object_inputs']}
    positive=lane(report,out/'production',row);control=lane(report,out/'disabled',row,True)
    passed=positive['trace']==[0x41,0x40,0x21,0x20] and control['trace']==[0x40,0x41,0x20,0x21]
    if any(sha(p)!=pin for p,pin in pins.items()):raise ValueError('production object changed')
    result=dict(passed=passed,production=positive,disabled_control=control,objects=pins,
                build_report_sha256=sha(args.report),fixture_sha256=sha(HERE/'fixture.c'))
    (out/'report.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(passed=passed,production=positive['trace'],disabled=control['trace']),indent=2))
    return int(not passed)


if __name__=='__main__':raise SystemExit(main())
