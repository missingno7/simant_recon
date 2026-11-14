"""Production caller-word controls, plus the live entry-21 disabled control."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).parent
sys.path[:0]=[str(ROOT),str(ROOT/'portable')]
from canonical_native_abi import m1b73_event_source as adapter
from portable.tests.acceptance import step_check
from portable.tests.acceptance.step_state import schema, split_frame

WRAPS=['portable_m1b73_event_enqueue_four_word_command','kbd_read_key_code',
       'CheatKeys','kbd_scan_state','WinPrintf','win_Events','kbd_poll_bios_key',
       'kbd_scroll_lock_state','win_NoWindowsShouldBeLocked','edit_scroll_and_redraw']

def execute(command,cwd,log,env=None):
    r=subprocess.run(command,cwd=cwd,env=env,capture_output=True,text=True,timeout=120)
    log.write_text(r.stdout+r.stderr)
    if r.returncode:raise ValueError(str(command)+'\n'+r.stdout[-1000:]+r.stderr[-3000:])
    return r

def fixture(report,out,disabled=False):
    out.mkdir()
    objects=report['core_link']['object_inputs'][:]
    for row in report['canonical_TUs']:
        if row['source'] not in adapter.SOURCE_MODULES:continue
        record=row['integer_expressions']['event_caller_frames']
        assert record==adapter.receipt(row['source'])
        generated=Path(row['generated']).read_text()
        word='portable_menu_saved_si' if row['source'].endswith('menu_tracking.c') else 'portable_event_incoming_si'
        old=', '+word+');'
        assert generated.count(old)==(2 if word=='portable_menu_saved_si' else 1)
        if disabled:
            generated=generated.replace(old,', 0);')
        if word=='portable_menu_saved_si':
            # Test-only access to canonical static storage. Both production
            # menu function bodies remain exactly the generated source.
            generated+='\nvoid test_set_menu(int16_t v) { curMenu = v; }\n'
        elif not disabled:
            continue
        changed=out/Path(row['generated']).name
        changed.write_text(generated)
        obj=changed.with_suffix('.o')
        command=row['compile']['command'][:]
        command[command.index('-c')+1]=str(changed)
        command[command.index('-o')+1]=str(obj)
        execute(command,out,out/(changed.stem+'-compile.log'))
        objects=[str(obj) if p==row['object'] else p for p in objects]
    rsp=out/'objects.rsp'
    rsp.write_text(''.join('"'+Path(p).as_posix()+'"\n' for p in objects))
    exe=out/'fixture.exe'
    hosting=[a for a in report['application_link']['command'] if a.startswith('-Wl,--wrap=') and a!='-Wl,--wrap=exit']
    command=[report['core_link']['command'][0],'-fno-lto','-g',str(HERE/'fixture.c'),'-Wl,@'+str(rsp),
             *hosting,*['-Wl,--wrap='+n for n in WRAPS],'-static','-lstdc++',
             str(Path(report['sdk']['path'])/'lib/libSDL3.dll.a'),'-o',str(exe)]
    execute(command,out,out/'link.log')
    env=dict(os.environ);env['PATH']=str(Path(report['sdk']['path'])/'bin')+os.pathsep+env.get('PATH','')
    r=execute([str(exe)],out,out/'trace.txt',env)
    return [[int(w) for w in line.split()] for line in r.stdout.splitlines()]

def live_control(build,out):
    positive=out/'step-build'
    exe=step_check.test_build(build,positive)
    receipt=json.loads((positive/'observer-build.json').read_text())
    report=json.loads((build/'report.json').read_text())
    service=next(r for r in report['native_services'] if r['source'].endswith('/m1b73_events.c'))
    source=(ROOT/service['source']).read_text()
    old='input_enqueue_event_args(bx, es, ax, cx, caller_word);'
    assert source.count(old)==1
    changed=out/'zero-service.c';changed.write_text(source.replace(old,'input_enqueue_event_args(bx, es, ax, cx, 0);'))
    obj=out/'zero-service.o';command=service['compile']['command'][:]
    command[command.index('-c')+1]=str(changed);command[command.index('-o')+1]=str(obj)
    # This C file uses a relative include in its original directory.
    command.extend(['-I',str(ROOT/'portable/whole_program/platform')])
    execute(command,out,out/'zero-service-compile.log')
    response=(positive/'objects.rsp').read_text().replace((positive/'m1b73_events.o').as_posix(),obj.as_posix())
    rsp=out/'zero-objects.rsp';rsp.write_text(response)
    command=receipt['command'][:]
    command=[('-Wl,@'+str(rsp)) if a=='-Wl,@'+str(positive/'objects.rsp') else a for a in command]
    negative=positive/'zero-step.exe';command[command.index('-o')+1]=str(negative)
    execute(command,build,out/'zero-step-link.log')
    scenario=ROOT/'dos/scenarios/quick-game.json'
    reference=next(p.parent for p in (ROOT/'build/reference/quick-game').glob('*/manifest.json')
                   if json.loads(p.read_text())['target']=='canonical')
    good=step_check.run_lane(scenario,reference,build,exe,out/'live-positive',max_steps=21,timeout=20)
    bad=step_check.run_lane(scenario,reference,build,negative,out/'live-zero',max_steps=21,timeout=20)
    assert good['status']=='REFERENCE_EQUAL',good
    assert bad['first_differing_step']==21,bad
    assert [r['name'] for r in bad['game_differences']]==['window_current_event'],bad
    items=schema(build,executable=exe)['items']
    good_event=split_frame(out/'live-positive/native.frame',items)['window_current_event']
    bad_event=split_frame(out/'live-zero/native.frame',items)['window_current_event']
    assert good_event[:10]+good_event[12:]==bad_event[:10]+bad_event[12:]
    assert int.from_bytes(good_event[10:12],'little')==20 and bad_event[10:12]==b'\0\0'
    return dict(positive=good,disabled=bad,positive_event_hex=good_event.hex(),disabled_event_hex=bad_event.hex())

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--build',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args();build=a.build.resolve();out=a.out.resolve()
    out.mkdir(parents=True,exist_ok=False)
    report=json.loads((build/'report.json').read_text())
    assert report['passed'] and report['input_stability']['at_end']
    def current_inputs():
        return {p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in report['input_pins']}
    assert current_inputs()==report['input_pins'],'Build inputs changed; rebuild first'
    positive=fixture(report,out/'production')
    disabled=fixture(report,out/'disabled',True)
    assert [r[1] for r in positive]==[20,0x1212,0x1234,-21555,1234,-1,2345],positive
    assert [r[1] for r in disabled]==[0]*7,disabled
    assert [r[0] for r in positive]==[r[0] for r in disabled]
    live=live_control(build,out)
    assert current_inputs()==report['input_pins'],'Build inputs changed during regression'
    result=dict(passed=True,production=positive,disabled=disabled,entry21=live,
                build_report_sha256=hashlib.sha256((build/'report.json').read_bytes()).hexdigest())
    (out/'report.json').write_text(json.dumps(result,indent=2)+'\n')
    print('PASS: seven production caller-context checks; disabled sites pass zero; live entry 21 positive equal / zero differs')

if __name__=='__main__':main()
