"""Build and run deterministic platform controls; no game-state writes."""
import argparse,json,os,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--out',type=Path,default=Path('build/current/tests/virtual-clock'))
    parser.add_argument('--sdk',type=Path,required=True)
    args=parser.parse_args()
    sys.path.insert(0,str(ROOT/'tools'))
    from workspace import prepare_output
    out=(ROOT/args.out).resolve()
    prepare_output(out,ROOT/'build/current/tests/virtual-clock',ROOT)
    sdk=args.sdk.resolve()
    exe=out/'virtual-clock.exe'
    command=['C:/msys64/mingw64/bin/gcc.exe','-std=c11','-Wall','-Wextra','-Werror','-O0','-g',
             '-I'+str(sdk/'include'),str(ROOT/'portable/whole_program/platform/sdl3/host.c'),
             str(ROOT/'portable/whole_program/platform/pit_clock.c'),str(Path(__file__).with_name('virtual_clock_test.c')),
             '-L'+str(sdk/'lib'),'-lSDL3','-o',str(exe)]
    subprocess.run(command,check=True,timeout=60)
    env=dict(os.environ,PATH=str(sdk/'bin')+os.pathsep+os.environ.get('PATH',''))
    run=subprocess.run([str(exe)],env=env,capture_output=True,text=True,timeout=30)
    (out/'report.json').write_text(json.dumps(dict(command=command,returncode=run.returncode,
                                                 stdout=run.stdout,stderr=run.stderr),indent=2)+'\n')
    print(run.stdout,end='');print(run.stderr,end='',file=sys.stderr)
    return run.returncode
if __name__=='__main__': raise SystemExit(main())
