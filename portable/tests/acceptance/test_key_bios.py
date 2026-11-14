"""Compile the production key path against independent DOS INT16 measurements."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from .state_schema import ROOT

HERE = Path(__file__).resolve().parent


class BiosKeys(unittest.TestCase):
    def test_measured_us_words_and_negative_control(self):
        fixture = json.loads((HERE/'key_bios_us.json').read_text())
        sdk = ROOT/'build/deps/sdl3-sdk/SDL3-3.4.16/x86_64-w64-mingw32'
        aliases = dict(enter='Return', esc='Escape', bspace='Backspace',
                       lbracket='[', rbracket=']', quote="'", grave='`',
                       minus='-', equals='=', semicolon=';', backslash='\\',
                       comma=',', period='.', slash='/', space='Space', kp_5='Keypad 5')
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            cases = []
            for c in fixture['cases']:
                words = c['words'] + c['release_words']
                self.assertLessEqual(len(words), 1)
                cases.append('{'+json.dumps(aliases.get(c['key'], c['key']))+
                             f', {c["modifiers"]}, {c["flags"]}, {len(words)}, {words[0] if words else 0}'+'}')
            source = out/'control.c'
            source.write_text('''#include <stdio.h>
#include <string.h>
#include "portable/whole_program/platform/sdl3/host.c"
#include "portable/whole_program/platform/sdl3/input_time_host.c"
int native_windows_translate(SDL_Event *e){return 0;}
int native_windows_take_deferred(SDL_Event *e){return 0;}
int native_windows_filter_root(SDL_Event *e){return 0;}
int native_windows_pointer(float *x,float *y){return 0;}
void native_windows_root_pointer(float *x,float *y){}
struct Case {const char *name; unsigned mod, flags, count, word;};
static const struct Case cases[] = {
'''+',\n'.join(cases)+'''
};
static int down_seen,up_seen;
static int observe(void *p,const HostEvent *e){
    if(e->kind==HOST_EVENT_KEY_DOWN)++down_seen;
    if(e->kind==HOST_EVENT_KEY_UP)++up_seen;
    return 1;
}
int main(int argc,char **argv){
    PortableInputTimeHost binding={0};
    for(unsigned i=0;i<sizeof(cases)/sizeof(*cases);++i){
        const struct Case *c=&cases[i];
        SDL_KeyboardEvent raw={0};HostEvent event={0};uint16_t actual=0,word;
        raw.scancode=SDL_GetScancodeFromKey(SDL_GetKeyFromName(c->name),NULL);
        if(!raw.scancode){fprintf(stderr,"bad name %s\\n",c->name);return 2;}
        /* Deliberately wrong localized symbol: physical US position wins. */
        raw.key=SDLK_Z;
        raw.mod=(c->mod&1?SDL_KMOD_LSHIFT:0)|(c->mod&2?SDL_KMOD_LCTRL:0)|(c->mod&4?SDL_KMOD_LALT:0);
        event.key=dos_key(&raw);
        event.extended=raw.scancode>=SDL_SCANCODE_INSERT && raw.scancode<=SDL_SCANCODE_UP;
        memset(&binding,0,sizeof(binding));alt_token=0;
        word=bios_key_word(&event,c->flags);
        /* Negative control restores the old spurious Ctrl+8 ASCII word. */
        if(argc>1 && !strcmp(c->name,"8") && c->mod==2)word=0x0938;
        if(word)push_key(&binding,word);
        if(alt_token)push_key(&binding,alt_token);
        unsigned count=pop_key(&binding,&actual);
        if(count!=c->count || (count && actual!=c->word)){
            fprintf(stderr,"case %u %s mod=%u: %u/%04x != %u/%04x\\n",i,c->name,c->mod,count,actual,c->count,c->word);return 3;
        }
        if(pop_key(&binding,&actual))return 4;
    }
    /* Real SDL queue -> retained IRQ events -> BIOS queue: suppression must
     * preserve both transitions and Ctrl+2 must keep its nonzero scan/NUL. */
    if(!host_init())return 5;
    Host *host=host_create_dimensions("keys",0,640,480);
    SimTimingClock clock={0};
    if(!host)return 6;
    memset(&binding,0,sizeof(binding));binding.host=host;binding.clock=&clock;
    binding.event_observer=observe;
    for(unsigned n=0;n<2;++n){
        SDL_Event e={0};e.type=SDL_EVENT_KEY_DOWN;e.key.scancode=n?SDL_SCANCODE_2:SDL_SCANCODE_8;
        e.key.key=SDLK_Z;e.key.mod=SDL_KMOD_LCTRL;
        SDL_PushEvent(&e);e.type=SDL_EVENT_KEY_UP;SDL_PushEvent(&e);
        if(ingest_host_events(&binding)<0)return 7;
        uint16_t value=0;int count=pop_key(&binding,&value);
        if((n==0 && count) || (n==1 && (!count || value!=0x0300)))return 8;
    }
    if(down_seen!=2 || up_seen!=2)return 9;
    /* A burst larger than the retained FIFO is backpressured in ordinary
     * polling and completely dispatched/drained by tape interrupt admission. */
    binding.event_count=0;binding.event_head=0;
    for(unsigned mode=0;mode<2;++mode){
        int target=up_seen+2000;
        for(unsigned n=0;n<2000;++n){
            SDL_Event e={0};e.type=SDL_EVENT_KEY_UP;e.key.scancode=SDL_SCANCODE_A;
            e.key.key=SDLK_A;if(!SDL_PushEvent(&e))return 10;
        }
        if(mode){
            active_host_binding=&binding;
            if(portable_input_time_host_interrupt()<0 || binding.event_count)return 11;
            active_host_binding=NULL;
        }else{
            while(up_seen<target){
                if(ingest_host_events(&binding)<0)return 12;
                HostEvent e;
                while(binding.event_count){
                    if(portable_input_time_host_poll_event(&binding,&e)!=1)return 13;
                }
            }
        }
        if(up_seen!=target)return 14;
    }
    host_destroy(host);host_shutdown();
    return 0;
}
''')
            # host_init/shutdown are SDL lifecycle wrappers in the public host API.
            text = source.read_text().replace('host_init()', 'SDL_Init(SDL_INIT_VIDEO)').replace('host_shutdown()', 'SDL_Quit()')
            source.write_text(text)
            exe = out/'control.exe'
            command = ['C:/msys64/mingw64/bin/gcc.exe','-std=c11','-O2','-ffunction-sections','-fdata-sections',
                       '-I'+str(ROOT),'-I'+str(sdk/'include'),str(source),
                       str(ROOT/'portable/whole_program/platform/pit_clock.c'),
                       str(ROOT/'portable/whole_program/platform/input_time.c'),
                       '-Wl,--gc-sections','-L'+str(sdk/'lib'),'-lSDL3','-o',str(exe)]
            run = subprocess.run(command,capture_output=True,text=True,timeout=60)
            self.assertEqual(run.returncode,0,run.stdout+run.stderr)
            shutil.copyfile(sdk/'bin/SDL3.dll',out/'SDL3.dll')
            env = {**os.environ,'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'}
            run = subprocess.run([str(exe)],env=env,capture_output=True,text=True,timeout=20)
            self.assertEqual(run.returncode,0,run.stdout+run.stderr)
            run = subprocess.run([str(exe),'old-ctrl8'],env=env,capture_output=True,text=True,timeout=20)
            self.assertEqual(run.returncode,3,run.stdout+run.stderr)
            self.assertIn('8 mod=2',run.stderr)

    def test_layout_admission_rejects_unproved_or_changed(self):
        from .keyboard_environment import neutral_proof, validate_keyboard
        from dos.run import keyboard_layout, keyboard_runner
        from tools.compiler import toolchain
        runner, pin = keyboard_runner(toolchain()['runners']['dosbox-x-acceptance'])
        self.assertEqual(runner['conf']['dos']['keyboardlayout'],'us')
        with self.assertRaises(ValueError): keyboard_layout('Host keyboard layout is now us')
        self.assertEqual(keyboard_layout('', 'Codepage 437 has been loaded for layout us\n')['layout'],'us')
        with self.assertRaises(ValueError): validate_keyboard(Path('.'),{}, {})
        for name in ('ant-commands','experiment','long-run','new-game-save','quick-game'):
            self.assertTrue(neutral_proof(ROOT/'dos/scenarios'/(name+'.scr'))['cases'])
        for name in ('interactive-play','load-from-save','full-game','random-17'):
            with self.assertRaises(ValueError): neutral_proof(ROOT/'dos/scenarios'/(name+'.scr'))


if __name__ == '__main__': unittest.main()
