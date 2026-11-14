"""Step observer controls, included by the repository's upper-layer bridge."""
import json
import os
import struct
import subprocess
import tempfile
import unittest
from pathlib import Path
from .state_schema import ROOT, differences, acceptance
from .step_state import fingerprint, read_hashes, split_frame


class Controls(unittest.TestCase):
    def test_recipe_key_names_and_held_modifiers(self):
        """Real SDL lookup/scans with recipe aliases and physical held state."""
        with tempfile.TemporaryDirectory() as directory:
            out=Path(directory);source=out/'keys.c';exe=out/'keys.exe'
            sdk=ROOT/'build/deps/sdl3-sdk/SDL3-3.4.16/x86_64-w64-mingw32'
            source.write_text(r'''
#include <SDL3/SDL.h>
#include <stdint.h>
#include <stdio.h>
#include <signal.h>
#include <stdlib.h>
uint32_t portable_test_clock_read(char k,void *p,uint32_t v){return v;}
void portable_test_step_boundary(unsigned s,unsigned p){}
void portable_test_diagnostics(FILE *f){}
void __real_DoAntSim(void){}
int32_t __real_MacTickCount(void){return 0;}
int16_t StillDown(void){return 0;}
int16_t edit_scroll_and_redraw(int16_t x,int16_t y){return 0;}
static void rejected(int s){_Exit(23);}
int main(int argc,char **argv){
  signal(SIGABRT,rejected);
  if(argc>1){SDL_GetKeyFromName(argv[1]);return 99;}
  const char *names[]={"lctrl~64","e~64","e~64","lctrl~0","lshift~1","4~1","lshift~0","esc","enter"};
  const SDL_Keycode keys[]={SDLK_LCTRL,SDLK_E,SDLK_E,SDLK_LCTRL,SDLK_LSHIFT,SDLK_4,SDLK_LSHIFT,SDLK_ESCAPE,SDLK_RETURN};
  const SDL_Keymod mods[]={SDL_KMOD_LCTRL,SDL_KMOD_LCTRL,SDL_KMOD_LCTRL,0,SDL_KMOD_LSHIFT,SDL_KMOD_LSHIFT,0,0,0};
  for(unsigned i=0;i<sizeof(keys)/sizeof(*keys);++i){
    SDL_Keymod mod=0;SDL_Keycode key=SDL_GetKeyFromName(names[i]);
    SDL_Scancode scan=SDL_GetScancodeFromKey(key,&mod);
    if(key!=keys[i] || scan==SDL_SCANCODE_UNKNOWN || mod!=mods[i])return 10+i;
  }
  return 0;
}
''')
            compiled=subprocess.run(['C:/msys64/mingw64/bin/gcc.exe','-std=c11','-DSIMANT_TEST_KEY_ALIASES',
                '-I'+str(sdk/'include'),str(source),str(Path(__file__).with_name('native_observer.c')),
                '-Wl,--wrap=SDL_GetKeyFromName','-Wl,--wrap=SDL_GetScancodeFromKey',
                '-L'+str(sdk/'lib'),'-lSDL3','-o',str(exe)],capture_output=True,text=True,timeout=30)
            self.assertEqual(compiled.returncode,0,compiled.stdout+compiled.stderr)
            import shutil
            shutil.copyfile(sdk/'bin/SDL3.dll',out/'SDL3.dll')
            self.assertEqual(subprocess.run([str(exe)],capture_output=True,timeout=10).returncode,0)
            for bad in ('e~2','e~','e~64extra','e~65536'):
                self.assertEqual(subprocess.run([str(exe),bad],capture_output=True,timeout=10).returncode,23)

    def test_schema_and_fingerprint(self):
        self.assertEqual(len(acceptance.save_schema()),307)
        self.assertEqual(sum(r[2] for r in acceptance.save_schema()),48386)
        self.assertEqual(fingerprint(b'hello'),0x4f9f2cab)
        self.assertEqual(fingerprint(b'ab\0\x80XX',True),fingerprint(b'ab\0\x80YY',True))
        self.assertNotEqual(fingerprint(b'ab\0\x80XX'),fingerprint(b'ab\0\x80YY'))
        self.assertNotEqual(fingerprint(b'ab\0\x80',True),fingerprint(b'abXX\0\x80',True))

    def test_named_three_way_verdicts(self):
        from .step_check import attribute
        equal=dict(status='REFERENCE_EQUAL');diff=dict(status='STATE_DIFFERENCE');gap=dict(status='INCOMPLETE')
        self.assertEqual(attribute(equal,equal),'ORIGINAL_EQUAL_ALL')
        self.assertEqual(attribute(gap,diff),'PORT_INTRODUCED')
        self.assertEqual(attribute(diff,equal),'RECONSTRUCTION_INTRODUCED')
        self.assertEqual(attribute(equal,gap),'UNATTRIBUTED')
        self.assertEqual(differences(b'abc',b'axc')['first_offset'],1)

    def test_compiled_observer_stops_on_state_only(self):
        """Real C observer: gather split storage, ignore diagnostics, stop at 2."""
        with tempfile.TemporaryDirectory() as directory:
            out=Path(directory);source=out/'fixture.c';exe=out/'fixture.exe'
            source.write_text(r'''
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <inttypes.h>
static uint8_t state[4]={1,2,7,4};
static unsigned input_samples[256];
void portable_test_before_poll(void){}
void portable_test_input_sample(unsigned kind,unsigned value){(void)value;++input_samples[kind];}
int16_t StillDown(void){return 1;}
int16_t edit_scroll_and_redraw(int16_t x,int16_t y){return x+y;}
static int internal_input_calls(void){return StillDown()+edit_scroll_and_redraw(2,3);}
uint32_t portable_test_clock_read(char k,void *p,uint32_t v){return v;}
void portable_test_step_boundary(unsigned s,unsigned p){}
void portable_test_diagnostics(FILE *f){fputs("\"pump_count\":999",f);}
int32_t __real_MacTickCount(void){return 0;}
void __real_DoAntSim(void){++state[0];++state[2];}
void portable_test_screen(FILE *f,const void *p){(void)p;fputc(state[0],f);}
extern void __wrap_DoAntSim(void);
int main(int argc,char **argv){
    if(internal_input_calls()!=6 || input_samples[247]!=1 || input_samples[246]!=1)return 98;
    FILE *f=fopen(argv[1],"w");
    fprintf(f,"%s\n%s\n%s\n%s\n2 3\n1 2 0 2\n%" PRId64 " 1\n%" PRId64 " 1\n0 1 0 1\n%" PRId64 " 1\n",
      argv[2],argv[3],argv[4],argv[5],
      (int64_t)(uintptr_t)state-(int64_t)(uintptr_t)portable_test_clock_read,
      (int64_t)(uintptr_t)(state+3)-(int64_t)(uintptr_t)portable_test_clock_read,
      (int64_t)(uintptr_t)(state+2)-(int64_t)(uintptr_t)portable_test_clock_read);
    fclose(f);
    for(int i=0;i<5;++i)__wrap_DoAntSim();return 99;
}
''')
            subprocess.run(['C:/msys64/mingw64/bin/gcc.exe','-std=c11','-finstrument-functions',str(source),
                            str(Path(__file__).with_name('native_observer.c')),'-o',str(exe)],
                           check=True,capture_output=True,timeout=30)
            for negative,frames in ((False,False),(True,False),(True,True)):
                expected=out/'expected';actual=out/'actual';result=out/'result';frame=out/'frame';config=out/'config'
                hashes=[]
                for i in range(3):
                    hashes += [fingerprint(bytes([9 if negative and i==1 else i+1,4])),fingerprint(b'\x07')]
                expected.write_bytes(struct.pack('<6I',*hashes))
                env=dict(os.environ,SIMANT_TEST_STEP_CONFIG=str(config))
                if frames:
                    frame_config=out/'frames.config'
                    frame_config.write_text(str(out)+'\n0 3\n1 2 3\n')
                    env['SIMANT_TEST_FRAME_CONFIG']=str(frame_config)
                run=subprocess.run([str(exe),str(config),str(expected),str(actual),str(result),str(frame)],
                                   env=env,capture_output=True,timeout=10)
                self.assertEqual(run.returncode,10 if negative else 0)
                row=json.loads(result.read_text())
                self.assertEqual(row['steps_compared'],2 if negative else 3)
                self.assertEqual(row['first_differing_step'],2 if negative else 0)
                self.assertEqual(row['pump_count'],999)
                self.assertEqual(len(read_hashes(actual,2)),row['steps_compared'])
                if negative:
                    self.assertEqual(frame.read_bytes(),b'\x02\x04\x08')
                if frames:
                    self.assertEqual(row['frame_entry_reached'],3)
                    self.assertEqual([(out/f'native.screen.{i}').read_bytes() for i in (1,2,3)],[b'\x01',b'\x02',b'\x03'])
                    self.assertEqual((out/'frame.1').read_bytes(),b'\x01\x04\x07')
                    self.assertEqual((out/'frame.2').read_bytes(),b'\x02\x04\x08')
                    self.assertFalse((out/'frame.3').is_file())

    def test_sound_order_failure_keeps_other_verdicts_independent(self):
        """Real replay: a bad sound ID detaches audio; other services stay strict."""
        from .step_check import test_build, run_lane
        build=Path(os.environ.get('SIMANT_STEP_TEST_BUILD',ROOT/'build/current/portable'))
        if not (build/'report.json').is_file() or not (ROOT/'assets/SIMANT.EXE').is_file():
            self.skipTest('Native build or game assets absent')
        scenario=ROOT/'dos/scenarios/new-game-save.json'
        references={}
        for path in (ROOT/'build/reference/new-game-save').glob('*v9/manifest.json'):
            row=json.loads(path.read_text())
            if row.get('complete'):references[row['target']]=path.parent
        if set(references)!={'original','canonical'}:
            self.skipTest('Both v9 references are needed')
        out=Path(os.environ.get('SIMANT_STEP_TEST_OUT',ROOT/'build/current/tests/steps'))/'sound-controls'
        scratch=Path(os.environ.get('SIMANT_STEP_SCRATCH_ROOT',ROOT/'build/scratch/steps'))
        exe=test_build(build,out/'test-build')
        for target,reference in references.items():
            for control in ('sound-order','service-order'):
                with self.subTest(target=target,control=control):
                    row=run_lane(scenario,reference,build,exe,out/target/control,60,control,8,scratch)
                    self.assertTrue(row['diagnostics']['sound_order_detached'])
                    self.assertEqual(row['audio']['status'],'AUDIO_INCOMPLETE')
                    self.assertEqual(row['audio']['sound_order_failure']['entry'],1)
                    if control=='sound-order':
                        self.assertEqual(row['status'],'REFERENCE_EQUAL')
                        self.assertEqual(row['steps_compared'],8)
                        self.assertEqual(row['frames']['status'],'FRAME_EQUAL')
                        self.assertTrue(row['frames']['replay_complete'])
                        self.assertNotIn('service_order_failure',row)
                    else:
                        self.assertEqual(row['status'],'INCOMPLETE')
                        self.assertIn('service_order_failure',row)
                        self.assertFalse(row['frames']['replay_complete'])

    def test_stored_step_scenarios(self):
        """The driver runs every stored scenario against build/current/portable (or reports
        it absent) and never launches a DOS recorder. Each scenario must give exactly the
        outcome pinned in known_findings.json (unlisted ones must be equal in both lanes):
        an earlier stop is a regression, a later one a fix that must update the file."""
        out=Path(os.environ.get('SIMANT_STEP_TEST_OUT',ROOT/'build/current/tests/steps'))
        command=[os.sys.executable,str(Path(__file__).with_name('step_check.py')),'--out',str(out)]
        if os.environ.get('SIMANT_STEP_TEST_BUILD'):
            command+=['--build',os.environ['SIMANT_STEP_TEST_BUILD']]
        if os.environ.get('SIMANT_STEP_SCRATCH_ROOT'):
            command+=['--scratch-root',os.environ['SIMANT_STEP_SCRATCH_ROOT']]
        run=subprocess.run(command,cwd=ROOT,capture_output=True,text=True,timeout=300)
        print(run.stdout,end='')
        self.assertIn(run.returncode,(0,1),run.stderr+run.stdout)
        self.assertNotIn('Traceback',run.stderr)
        self.assertTrue(run.stdout.strip(),run.stderr)
        known=json.loads(Path(__file__).with_name('known_findings.json').read_text())['scenarios']
        frame_known=json.loads(Path(__file__).with_name('known_findings.json').read_text()).get('frames',{})
        audio_known=json.loads(Path(__file__).with_name('known_findings.json').read_text()).get('audio',{})
        from .frame_check import frame_signature
        for line in run.stdout.splitlines():
            scenario=line.split(':',1)[0]
            if 'no reference' in line:continue
            row=json.loads((out/scenario/'result.json').read_text())
            actual={'verdict':row['verdict'],'lanes':{}}
            for target,lane in row['lanes'].items():
                entry={'status':lane['status'],'steps_compared':lane['steps_compared']}
                if lane['status']=='STATE_DIFFERENCE':
                    entry['first']=sorted({d['name'] for d in lane.get('game_differences',[])})
                actual['lanes'][target]=entry
            if scenario in known:
                self.assertEqual(actual,known[scenario],scenario)
            else:
                self.assertEqual(row['verdict'],'ORIGINAL_EQUAL_ALL',line)
            observed_frames={target:frame_signature(lane['frames']) for target,lane in row['lanes'].items()}
            if scenario in frame_known:self.assertEqual(observed_frames,frame_known[scenario],scenario+' frames')
            else:self.assertTrue(all(f['status']=='FRAME_EQUAL' for f in observed_frames.values()),scenario+' unpinned frame finding')
            observed_audio={target:lane['audio'] for target,lane in row['lanes'].items()}
            if scenario in audio_known:self.assertEqual(observed_audio,audio_known[scenario],scenario+' audio')
            else:self.assertTrue(all(a['status']=='AUDIO_EQUAL' for a in observed_audio.values()),scenario+' unpinned audio finding')


if __name__=='__main__':unittest.main()
