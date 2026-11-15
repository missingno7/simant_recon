"""Tape-free mode-6 playback corpus. Record both DOS executables once; compare native after execution."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
from portable.tests.acceptance.state_schema import sha
from portable.tests.acceptance.audio_content import read_content


def coverage(capture):
    from collections import Counter
    events=capture['events'];voices=capture['voices']
    overlap=any(max(a['output'][0][2],b['output'][0][2])<=min(a['output'][-1][2],b['output'][-1][2])
                for i,a in enumerate(voices) if a['output'] for b in voices[i+1:] if b['output'])
    return dict(events=dict(Counter(e['kind'] for e in events)),
        songs=sorted({e['arguments'][0] for e in events if e['kind']=='song_start'}),
        effects=sorted({e['arguments'][0] for e in events if e['kind']=='effect'}),
        samples=sorted({v['object'] for v in voices}),sample_starts=len(voices),
        looping_voices=sum(bool(v['flags']&128) for v in voices),overlap=overlap,
        loop_wraps=sum(sum(u[0]>v[0] for u,v in zip(s['output'],s['output'][1:])) for s in voices),
        emitted_bytes=sum(len(v['output']) for v in voices),
        stops=dict(Counter(v['stop']['reason'] for v in voices)))


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('scenario',type=Path,nargs='*')
    ap.add_argument('--build',type=Path,default=ROOT/'build/current/portable')
    ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--reference-root',type=Path,default=ROOT/'build/reference/audio-playback-v1')
    ap.add_argument('--record',action='store_true')
    ap.add_argument('--observer',type=Path)
    ap.add_argument('--native-observer',type=Path,help='Pinned existing observer-build.json, useful while another worker builds the runtime')
    ap.add_argument('--dos-report',type=Path,default=ROOT/'build/current/dos/build-report.json')
    ap.add_argument('--binding-root',type=Path,default=ROOT/'build/workers/dos-clock/binding-v2')
    ap.add_argument('--jobs',type=int,choices=range(1,5),default=3)
    ap.add_argument('--timeout',type=int,default=600)
    a=ap.parse_args();a.out=a.out.resolve();a.out.mkdir(parents=True,exist_ok=False)
    a.build=a.build.resolve();a.reference_root=a.reference_root.resolve()
    if (a.build/'runtime-assets/SIMANT.CFG').read_bytes()!=(ROOT/'assets/SIMANT.CFG').read_bytes():raise ValueError('Changed shipped configuration')
    if (ROOT/'assets/SIMANT.CFG').read_text().splitlines()[-1]!='Sound Mode: 6':raise ValueError('Playback requires shipped mode 6')
    corpus=sorted((ROOT/'dos/scenarios').glob('*.json'))+sorted((ROOT/'dos/scenarios/audio-playback').glob('*.json'))
    jobs=[(p.resolve(),t) for p in a.scenario or corpus for t in ('original','canonical')]
    started=time.perf_counter()
    if a.record:
        if not a.observer:ap.error('--record requires --observer')
        from portable.tests.acceptance.step_record import record
        def work(job):
            p,t=job
            return str(record(p,t,a.build,a.observer.resolve(),a.dos_report.resolve(),
                out=a.reference_root/p.stem/t,binding_dump=a.binding_root/t/'exec-simstep.1.bin',host_seconds=a.timeout,playback=True))
        with ThreadPoolExecutor(max_workers=a.jobs) as pool:references=list(pool.map(work,jobs))
        (a.out/'recording.json').write_text(json.dumps(dict(wall_seconds=time.perf_counter()-started,references=references),indent=2)+'\n')
        return 0
    from portable.tests.acceptance.step_check import test_build
    from portable.tests.acceptance.step_state import schema
    from portable.tests.acceptance.native_schema import symbols_for
    if a.native_observer:
        native_receipt=json.loads(a.native_observer.read_text())
        exe=a.native_observer.resolve().parent/'simant-step.exe'
        if sha(exe)!=native_receipt['executable_sha256']:raise ValueError('Changed observer executable')
        if native_receipt['inputs'][str(a.build/'report.json')]!=sha(a.build/'report.json'):raise ValueError('Mixed native build/observer')
    else:exe=test_build(a.build,a.out/'test-build')
    build_seconds=time.perf_counter()-started
    state=schema(a.build,executable=exe);syms=symbols_for(exe)
    prepared=a.out/'native-views.json'
    prepared.write_text(json.dumps(dict(executable_sha256=sha(exe),sound_off=False,state=state,
        anchor=syms.addresses['portable_test_clock_read'],palette=syms.expression('app.palette')[0])))
    def work(job):
        path,target=job;ref=a.reference_root/path.stem/target;out=a.out/path.stem/target
        manifest=json.loads((ref/'manifest.json').read_text())
        if manifest.get('audio_playback')!='audio-playback-v1':raise ValueError('Reference omits playback observations')
        from portable.tests.acceptance.audio_playback import validate_reference
        validate_reference(ref,manifest)
        out.parent.mkdir(parents=True,exist_ok=True)
        command=[sys.executable,'-c','from pathlib import Path; import sys; from portable.tests.acceptance.ideal_check import lane; lane(*map(Path,sys.argv[1:6]),prepared=Path(sys.argv[6]),timeout=int(sys.argv[7]),playback=True)',
            str(path),str(ref),str(a.build),str(exe),str(out),str(prepared),str(a.timeout)]
        with out.with_suffix('.log').open('w') as log:
            run=subprocess.run(command,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,timeout=a.timeout+180)
        if run.returncode:raise RuntimeError('Playback process failed: '+str(out.with_suffix('.log')))
        full=json.loads((out/'result.json').read_text());audio=full['audio_content_diagnostic']
        result=dict(scenario=path.stem,target=target,status=audio['status'],first_difference=audio['first_difference'],
            seconds=full['timings']['lane_total'],no_tapes=full['no_tapes'],code=full['code'],
            capture_errors=audio['capture_errors'],maximum_tick_distance=audio.get('maximum_tick_distance'),
            maximum_event_ns=audio.get('playback_events',{}).get('maximum_ns'),
            coverage={label:coverage(read_content(p,manifest['steps'])) for label,p in
                [('dos',ref/'capture/observer.txt.content'),('native',out/'audio-content.txt')]},
            reference_manifest_sha256=sha(ref/'manifest.json'),native_executable_sha256=sha(exe))
        (out/'playback-result.json').write_text(json.dumps(result,indent=2)+'\n')
        print(f'{path.stem}/{target}: {audio["status"]} first={audio["first_difference"]} {result["seconds"]:.2f}s',flush=True)
        return result
    with ThreadPoolExecutor(max_workers=a.jobs) as pool:results=list(pool.map(work,jobs))
    receipt=dict(contract='audio-playback-v1',wall_seconds=time.perf_counter()-started,observer_build_seconds=build_seconds,
        lanes=results,configuration_sha256=sha(ROOT/'assets/SIMANT.CFG'))
    (a.out/'playback-results.json').write_text(json.dumps(receipt,indent=2)+'\n')
    return int(any(r['status']!='AUDIO_EQUAL' for r in results))


if __name__=='__main__':raise SystemExit(main())
