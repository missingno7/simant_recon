"""Verify the SDL Sound Mode 6 provider uses virtual time, including ISA reads."""
import argparse,json,os,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--sdk',type=Path,required=True)
    ap.add_argument('--out',type=Path,default=ROOT/'build/current/tests/virtual-audio')
    args=ap.parse_args();sys.path.insert(0,str(ROOT/'tools'))
    from workspace import prepare_output
    out=prepare_output(args.out.resolve(),ROOT/'build/current/tests/virtual-audio',ROOT)
    sdk=args.sdk.resolve();cc='C:/msys64/mingw64/bin/gcc.exe'
    files=['portable/tests/acceptance/virtual_audio_test.c','portable/platform/sdl3/audio.c',
           'portable/platform/sdl3/whole_audio_provider.c','portable/platform/sdl3/whole_audio_startup.c',
           'portable/whole_program/platform/sdl3/host.c','portable/whole_program/platform/whole_audio_provider.c',
           'portable/whole_program/platform/audio_native.c','portable/audio/isa_devices.cpp',
           'portable/audio/ymfm/ymfm_opl.cpp','portable/audio/ymfm/ymfm_adpcm.cpp','portable/audio/ymfm/ymfm_pcm.cpp']
    objects=[];commands=[]
    for i,file in enumerate(files):
        obj=out/f'{i}.o';objects.append(str(obj))
        command=[cc,'-std=c++17' if file.endswith('.cpp') else '-std=c11','-I'+str(ROOT),
                 '-I'+str(sdk/'include'),'-c',str(ROOT/file),'-o',str(obj)]
        commands.append(command);subprocess.run(command,check=True,timeout=60)
    exe=out/'virtual-audio.exe'
    command=[cc,*objects,'-static-libgcc','-static-libstdc++','-lstdc++','-L'+str(sdk/'lib'),'-lSDL3','-o',str(exe)]
    commands.append(command);subprocess.run(command,check=True,timeout=60)
    env=dict(os.environ,PATH=str(sdk/'bin')+os.pathsep+os.environ.get('PATH',''))
    run=subprocess.run([str(exe)],env=env,capture_output=True,text=True,timeout=30)
    (out/'report.json').write_text(json.dumps(dict(commands=commands,returncode=run.returncode,
        stdout=run.stdout,stderr=run.stderr),indent=2)+'\n')
    print(run.stdout+run.stderr,end='');return run.returncode
if __name__=='__main__':raise SystemExit(main())
