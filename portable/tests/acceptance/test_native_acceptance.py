"""Permanent observation controls and the repository upper-layer bridge."""
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from .state_schema import ROOT,acceptance
from .step_state import fingerprint

class Controls(unittest.TestCase):
    def test_recipe_key_names(self):
        """Real SDL lookup and scans for tick-recipe aliases."""
        with tempfile.TemporaryDirectory() as directory:
            out=Path(directory);source=out/'keys.c';exe=out/'keys.exe'
            sdk=ROOT/'build/deps/sdl3-sdk/SDL3-3.4.16/x86_64-w64-mingw32'
            source.write_text(r'''
#include <SDL3/SDL.h>
#include <stdint.h>
#include <stdio.h>
#include <signal.h>
#include <stdlib.h>

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
  const char *names[]={"lctrl","e","e","lctrl","lshift","4","lshift","esc","enter"};
  const SDL_Keycode keys[]={SDLK_LCTRL,SDLK_E,SDLK_E,SDLK_LCTRL,SDLK_LSHIFT,SDLK_4,SDLK_LSHIFT,SDLK_ESCAPE,SDLK_RETURN};
  const SDL_Keymod mods[]={0,0,0,0,0,0,0,0,0};
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
                '-Wl,--wrap=SDL_GetKeyFromName',
                '-L'+str(sdk/'lib'),'-lSDL3','-o',str(exe)],capture_output=True,text=True,timeout=30)
            self.assertEqual(compiled.returncode,0,compiled.stdout+compiled.stderr)
            import shutil
            shutil.copyfile(sdk/'bin/SDL3.dll',out/'SDL3.dll')
            self.assertEqual(subprocess.run([str(exe)],capture_output=True,timeout=10).returncode,0)

    def test_schema_and_fingerprint(self):
        self.assertEqual(len(acceptance.save_schema()),307)
        self.assertEqual(sum(r[2] for r in acceptance.save_schema()),48386)
        self.assertEqual(fingerprint(b'hello'),0x4f9f2cab)
        self.assertEqual(fingerprint(b'ab\0\x80XX',True),fingerprint(b'ab\0\x80YY',True))
        self.assertNotEqual(fingerprint(b'ab\0\x80XX'),fingerprint(b'ab\0\x80YY'))
        self.assertNotEqual(fingerprint(b'ab\0\x80',True),fingerprint(b'abXX\0\x80',True))


    def test_stored_ideal_scenarios(self):
        from .run import run
        build=Path(os.environ.get('SIMANT_STEP_TEST_BUILD',ROOT/'build/current/portable'))
        out=Path(os.environ.get('SIMANT_STEP_TEST_OUT',ROOT/'build/current/tests/acceptance'))
        result=run(build,out)
        self.assertTrue(result['passed'],json.dumps(result,indent=2))
