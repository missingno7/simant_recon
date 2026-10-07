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
        'portable/whole_program/platform/audio_native.c','portable/audio/isa_devices.cpp',
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
 negative=subprocess.run([str(exe),'--unsupported-dma'],capture_output=True,text=True,timeout=10)
 (out/'unsupported-dma.txt').write_text(negative.stdout+negative.stderr)
 assert negative.returncode==70 and 'Unimplemented SB DSP command 14' in negative.stderr
 print('PASS: unsupported DMA fails explicitly');return 0
if __name__=='__main__':raise SystemExit(main())
