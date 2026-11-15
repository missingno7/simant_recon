"""Grounded device-boundary controls; no game algorithms or copied DOS bytes."""
from pathlib import Path
import argparse,subprocess,sys
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'tools'))
from workspace import prepare_output
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,default=ROOT/'build/current/tests/audio');a=ap.parse_args()
 out=prepare_output(a.out.absolute(),ROOT/'build/current/tests/audio')
 cc='C:/msys64/mingw64/bin/gcc.exe'
 files=['portable/tests/audio/device_boundary.c','portable/whole_program/platform/whole_audio_provider.c',
        'portable/whole_program/platform/audio_native.c','portable/audio/native_renderer.cpp',
        'portable/audio/ymfm/ymfm_opl.cpp','portable/audio/ymfm/ymfm_adpcm.cpp','portable/audio/ymfm/ymfm_pcm.cpp']
 objects=[]
 for i,f in enumerate(files):
  obj=out/f'{i}.o';objects.append(str(obj))
  cmd=[cc,'-std=c++17' if f.endswith('.cpp') else '-std=c11','-I',str(ROOT),'-c',str(ROOT/f),'-o',str(obj)]
  subprocess.run(cmd,check=True)
 exe=out/'audio-test.exe'
 subprocess.run([cc,*objects,'-static','-lstdc++','-o',str(exe)],check=True)
 result=subprocess.run([str(exe)],capture_output=True,text=True,timeout=30)
 (out/'result.txt').write_text(result.stdout+result.stderr)
 print(result.stdout+result.stderr)
 if result.returncode:return result.returncode
 for argument,message in [('--unsupported-dma','unsupported native audio port/control'),
                          ('--invalid-position','sample position/volume outside payload'),
                          ('--invalid-volume','invalid sample start'),
                          ('--backward-event','events go backwards')]:
  negative=subprocess.run([str(exe),argument],capture_output=True,text=True,timeout=10)
  (out/(argument[2:]+'.txt')).write_text(negative.stdout+negative.stderr)
  assert negative.returncode==70 and message in negative.stderr
 print('PASS: unsupported DMA, invalid position/volume and backward event fail explicitly')
 sdk=ROOT/'build/deps/sdl3-sdk/SDL3-3.4.16/x86_64-w64-mingw32'
 queue=out/'queue-policy.exe'
 wrap=['SDL_GetTicksNS','SDL_OpenAudioDeviceStream','SDL_GetAudioStreamDevice','SDL_GetAudioDeviceFormat','SDL_ResumeAudioStreamDevice','SDL_PauseAudioStreamDevice']
 subprocess.run([cc,'-std=c11','-I'+str(ROOT),'-I'+str(sdk/'include'),str(ROOT/'portable/tests/audio/queue_policy.c'),str(ROOT/'portable/platform/sdl3/audio.c'),
     *['-Wl,--wrap='+name for name in wrap],'-L'+str(sdk/'lib'),'-lSDL3','-o',str(queue)],check=True)
 import shutil
 shutil.copyfile(sdk/'bin/SDL3.dll',out/'SDL3.dll')
 result=subprocess.run([str(queue)],capture_output=True,text=True,timeout=30)
 (out/'queue-policy.txt').write_text(result.stdout+result.stderr);print(result.stdout+result.stderr,end='')
 if result.returncode:return result.returncode
 # Both policy obligations must be decisive, using the identical real SDL
 # queue fixture. Neither mutation touches a source clock or game function.
 source=(ROOT/'portable/platform/sdl3/audio.c').read_text()
 for label,old,new in [('no-gate','a->gated=1;','a->gated=0;'),
                       ('no-bound','if((size_t)queued+a->pending_frames>','if(0 && (size_t)queued+a->pending_frames>')]:
  assert source.count(old)==1
  mutant=out/(label+'.c');mutant.write_text(source.replace(old,new));exe=out/(label+'.exe')
  subprocess.run([cc,'-std=c11','-I'+str(ROOT),'-I'+str(sdk/'include'),'-I'+str(ROOT/'portable/platform/sdl3'),str(ROOT/'portable/tests/audio/queue_policy.c'),str(mutant),
      *['-Wl,--wrap='+name for name in wrap],'-L'+str(sdk/'lib'),'-lSDL3','-o',str(exe)],check=True)
  negative=subprocess.run([str(exe)],capture_output=True,text=True,timeout=30)
  (out/(label+'.txt')).write_text(negative.stdout+negative.stderr)
  assert negative.returncode==1 and 'FAIL' in negative.stderr
 print('PASS: omitted pacing gate and omitted queue bound both fail the PCM fixture');return 0
if __name__=='__main__':raise SystemExit(main())
