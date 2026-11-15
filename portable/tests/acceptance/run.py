"""Upper-layer regression: sound-off gameplay, sound-on gameplay and playback."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[3]


def run(build,out,jobs=3):
    sys.path.insert(0,str(ROOT/'tools'))
    from workspace import prepare_output
    out=prepare_output(out.resolve(),ROOT/'build/current/tests/acceptance',ROOT)
    started=time.perf_counter();results=[]
    for name,module,options,expected in (
        ('sound-off','ideal_check',['--sound-off'],18),
        ('sound-on','ideal_check',[],18),
        ('playback','playback_check',['--timing-tolerance-ns','1'],22)):
        destination=out/name
        command=[sys.executable,'-m','portable.tests.acceptance.'+module,
                 '--build',str(build.resolve()),'--out',str(destination),'--jobs',str(jobs),*options]
        lane_start=time.perf_counter()
        # Each child joins its bounded lane pool before returning. A failure
        # still leaves the other independent sound variant's evidence visible.
        with (out/(name+'.log')).open('w') as log:
            process=subprocess.run(command,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
        elapsed=time.perf_counter()-lane_start
        summary=destination/('playback-results.json' if name=='playback' else 'summary.json')
        data=json.loads(summary.read_text()) if summary.exists() else None
        lanes=data['lanes'] if name=='playback' and data else data
        equal=sum(row['status']=='AUDIO_EQUAL' if name=='playback' else
                  row['state']=='STATE_EQUAL' and row['frames']=='FRAME_EQUAL' and
                  row['audio'] in ('SOUND_OFF_CONFIRMED','AUDIO_COMMANDS_EQUAL') for row in lanes or [])
        passed=process.returncode==0 and len(lanes or [])==expected and equal==expected
        results.append(dict(name=name,passed=passed,expected=expected,equal=equal,
                            code=process.returncode,seconds=elapsed,command=command))
        print(f'{name}: {equal}/{expected} {"PASS" if passed else "FAIL"} {elapsed:.2f}s',flush=True)
    receipt=dict(passed=all(r['passed'] for r in results),seconds=time.perf_counter()-started,results=results)
    (out/'result.json').write_text(json.dumps(receipt,indent=2)+'\n')
    return receipt


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build',type=Path,default=ROOT/'build/current/portable')
    parser.add_argument('--out',type=Path,default=ROOT/'build/current/tests/acceptance')
    parser.add_argument('--jobs',type=int,choices=range(1,5),default=3)
    args=parser.parse_args()
    return int(not run(args.build,args.out,args.jobs)['passed'])


if __name__=='__main__':raise SystemExit(main())
