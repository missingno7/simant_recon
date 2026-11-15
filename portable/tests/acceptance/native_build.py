"""Observation-only native link shared by gameplay and playback checks."""
import json
import shutil
import subprocess
from pathlib import Path
from .state_schema import ROOT,sha
HERE=Path(__file__).resolve().parent


def build_observer(build, out):
    """Link read-only state, frame, voice, music and provider-time observations."""
    report=json.loads((build/'report.json').read_text())
    if any(sha(ROOT/path)!=expected for path,expected in report['input_pins'].items()):
        raise ValueError('Production build inputs changed; rebuild before observing')
    observed_sources=('src/sound/midi_player.c','src/sound/opl2_voices.c',
                      'src/sound/midi_voices.c','src/sound/sample_voices.c')
    observed_units=[r for r in report['canonical_TUs'] if r.get('compile') and r['source'] in observed_sources]
    if len(observed_units)!=len(observed_sources):raise ValueError('Missing audio observation translation units')
    inputs={str(p):sha(p) for p in [HERE/'animation_identity.h',HERE/'event_context_rule.h',HERE/'native_audio_content.inc',HERE/'audio_content.py',HERE/'audio_playback.py',build/'simant-canonical.exe',build/'report.json',Path(__file__),HERE/'native_observer.c',
            ROOT/'portable/whole_program/platform/sdl3/host.c',
            ROOT/'portable/whole_program/platform/sdl3/test_observer.inc',ROOT/'portable/whole_program/platform/sdl3/audio_observer.inc',
            ROOT/'portable/whole_program/platform/sdl3/input_time_host.c',
            ROOT/'portable/whole_program/platform/m1b73_events.c',
            ROOT/'portable/whole_program/platform/m1b73_queue_runtime.c',
            ROOT/'portable/whole_program/platform/audio_native.c',ROOT/'portable/whole_program/platform/whole_audio_provider.c',ROOT/'portable/whole_program/platform/input_time.h',ROOT/'portable/whole_program/platform/input_time.c',ROOT/'portable/whole_program/platform/m1b73_main_input.c']}
    inputs.update({r['generated']:sha(Path(r['generated'])) for r in observed_units})
    application_source=ROOT/'portable/whole_program/application.c'
    inputs[str(application_source)]=sha(application_source)
    exe=out/'simant-step.exe';receipt=out/'observer-build.json'
    if receipt.is_file() and exe.is_file():
        old=json.loads(receipt.read_text())
        if old['inputs']==inputs and old['executable_sha256']==sha(exe): return exe
    out.mkdir(parents=True,exist_ok=True)
    # Replace only test copies; the ordinary generated TUs remain pinned.
    response=(build/'application-objects.rsp').read_text()
    for filename in ('/sdl3/host.c','/whole_program/platform/whole_audio_provider.c'):
        host=next(r for r in report['native_services'] if r['source'].endswith(filename))
        obj=out/(Path(host['source']).stem+'.o')
        command=host['compile']['command'][:]
        if filename=='/sdl3/host.c':command+=['-DSIMANT_TEST_FRAMES']
        if filename=='/whole_program/platform/whole_audio_provider.c':
            from portable.tests.acceptance.audio_playback import instrument_provider_unit
            observed=out/'provider-time-observed.c'
            observed.write_text(instrument_provider_unit((ROOT/host['source']).read_text()))
            command[command.index('-c')+1]=str(observed)
            command+=['-I'+str((ROOT/host['source']).parent)]
        command[command.index('-o')+1]=str(obj)
        subprocess.run(command,check=True,capture_output=True,timeout=60)
        response=response.replace(Path(host['object']).as_posix(),obj.as_posix())
    for unit in observed_units:
        obj=out/(Path(unit['generated']).stem+'.o')
        command=unit['compile']['command'][:]
        if unit['source'] in ('src/sound/midi_player.c','src/sound/opl2_voices.c','src/sound/midi_voices.c'):
            from portable.tests.acceptance.audio_playback import instrument_music_unit
            observed=out/(Path(unit['generated']).stem+'-playback.c')
            observed.write_text(instrument_music_unit(Path(unit['generated']).read_text(),unit['source']))
            command[command.index('-c')+1]=str(observed)
        if unit['source']=='src/sound/sample_voices.c':
            from portable.tests.acceptance.audio_content import instrument_sample_unit
            observed=out/'sample-voices-observed.c'
            observed.write_text(instrument_sample_unit(Path(unit['generated']).read_text()))
            command[command.index('-c')+1]=str(observed)
        command[command.index('-o')+1]=str(obj)
        subprocess.run(command,check=True,capture_output=True,timeout=60)
        response=response.replace(Path(unit['object']).as_posix(),obj.as_posix())
    (out/'objects.rsp').write_text(response)
    observer_object=out/'native_observer.o'
    observer_compile=[report['application_link']['command'][0],'-std=c11','-O2','-g','-fno-lto','-DSIMANT_TEST_KEY_ALIASES','-DSIMANT_TEST_AUDIO_CONTENT','-I'+str(ROOT),'-I'+str(out),'-c',str(HERE/'native_observer.c'),'-o',str(observer_object)]
    subprocess.run(observer_compile,check=True,capture_output=True,timeout=60)
    command=report['application_link']['command'][:]
    command=[('-Wl,@'+str(out/'objects.rsp')) if arg=='-Wl,@application-objects.rsp' else arg for arg in command]
    command[command.index('-o')+1]=str(exe)
    command[1:1]=[str(observer_object),'-Wl,--wrap=DoAntSim',
                   '-Wl,--wrap=SDL_GetKeyFromName']
    run=subprocess.run(command,cwd=build,capture_output=True,text=True,timeout=120)
    (out/'link.log').write_text(run.stdout+run.stderr)
    if run.returncode:raise RuntimeError('Observer link failed: '+run.stderr[-3000:])
    for filename in ('SDL3.dll','simant-build-id.txt'):
        shutil.copyfile(build/filename,out/filename)
    shutil.copytree(build/'runtime-bios-fonts',out/'runtime-bios-fonts',dirs_exist_ok=True)
    receipt.write_text(json.dumps(dict(inputs=inputs,executable_sha256=sha(exe),command=command,observer_compile=observer_compile,sample_observation=dict(path=str(out/'sample-voices-observed.c'),sha256=sha(out/'sample-voices-observed.c'),rule='Read-only callbacks after source voice setup/stop; ordinary converted TU remains unchanged'),instrumented_units=[dict(module=r['module'],source=r['generated'],sha256=sha(Path(r['generated'])),rule='Read-only source-boundary callbacks in test copy') for r in observed_units]),indent=2)+'\n')
    return exe

