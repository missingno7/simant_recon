"""Checkpoint controls: exact pixels, unused DAC, cursor pixels, and coverage."""
import struct
import tempfile
import unittest
import json
import shutil
import subprocess
from pathlib import Path
from .frame_check import compare_pair, read_screen, SIZE, comment_checkpoints


def fixture():
    h=[0x37464153,640,480,0x12,0,80,0,0,1023,15,6,255,0,0,1]+[0]*9
    return bytearray(struct.pack('<24I',*h)+bytes(range(16))+bytes(768)+bytes([1])*256+bytes(48)+bytes(64)+bytes(640*480))


class Frames(unittest.TestCase):
    def test_frame_layer_is_independent_of_state(self):
        from .step_check import attribute_frames
        equal=dict(status='FRAME_EQUAL',replay_complete=True)
        diff=dict(status='FRAME_DIFFERENCE',replay_complete=True)
        gap=dict(status='FRAME_EQUAL',replay_complete=False)
        self.assertEqual(attribute_frames(diff,diff),'PORT_INTRODUCED')
        self.assertEqual(attribute_frames(diff,equal),'RECONSTRUCTION_INTRODUCED')
        self.assertEqual(attribute_frames(equal,equal),'ORIGINAL_EQUAL_ALL')
        self.assertEqual(attribute_frames(equal,gap),'UNATTRIBUTED')

    def test_actual_dos_scanout_addressing(self):
        from .state_schema import ROOT
        text=(ROOT/'portable/tests/acceptance/compact_observer.inc').read_text()
        function='static void CompactScreen('+text.split('static void CompactScreen(',1)[1].split('\nstatic std::string compact_output;',1)[0]
        with tempfile.TemporaryDirectory() as directory:
            out=Path(directory);source=out/'scan.cpp';exe=out/'scan.exe'
            source.write_text(r'''
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <signal.h>
#include <string>
#include <vector>
#define LOG_MSG(...) ((void)0)
enum { M_EGA=1 };
struct Card {
  int mode;
  struct { unsigned width,height,address_line_total,address_add,bytes_skip,linear_mask; } draw;
  struct { unsigned real_start,hlines_skip,line_compare; uint8_t pel_panning,addr_shift; } config;
  struct { uint8_t color_plane_enable,color_select,mode_control,palette[16]; } attr;
  struct { uint8_t bits,pel_mask,combine[16];struct { uint8_t red,green,blue; } rgb[256]; } dac;
  struct { uint8_t *linear; } mem;
} vga;
static uint8_t ram[262144], saved_ram[262144];
void CompactMouseFrame(uint32_t w[8],uint16_t masks[32]) { w[0]=1; }
static void rejected(int s) { _Exit(23); }
'''+function+r'''
int main(int argc,char **argv) {
  signal(SIGABRT,rejected);
  vga.mode=M_EGA;vga.draw.width=640;vga.draw.height=480;
  vga.draw.address_line_total=1;vga.draw.address_add=400;vga.draw.linear_mask=262143;
  vga.draw.bytes_skip=2;vga.config.real_start=37;vga.config.addr_shift=1;
  vga.config.pel_panning=3;vga.config.line_compare=1023;
  vga.attr.color_plane_enable=15;vga.dac.bits=6;vga.dac.pel_mask=255;vga.mem.linear=ram;
  for(unsigned i=0;i<16;++i) { vga.dac.combine[i]=i;vga.attr.palette[i]=i; }
  ram[312]=0x10;ram[714]=0x10; // first pixel plane0, next row plane2
  if(argc>2 && !strcmp(argv[2],"wrap")) {
    memset(ram,0,sizeof(ram));vga.config.real_start=65532;vga.config.addr_shift=0;
    vga.config.pel_panning=0;vga.draw.bytes_skip=2;ram[1]=128;
  }
  if(argc>2 && !strcmp(argv[2],"split"))vga.config.line_compare=100;
  if(argc>2 && !strcmp(argv[2],"mode"))vga.mode=0;
  Card before=vga;memcpy(saved_ram,ram,sizeof(ram));
  CompactScreen(argv[1]);
  return memcmp(&vga,&before,sizeof(vga)) || memcmp(ram,saved_ram,sizeof(ram));
}
''')
            run=subprocess.run(['C:/msys64/mingw64/bin/g++.exe','-std=c++11',str(source),'-static','-o',str(exe)],capture_output=True,text=True,timeout=30)
            self.assertEqual(run.returncode,0,run.stdout+run.stderr)
            self.assertEqual(subprocess.run([str(exe),str(out/'frame')],capture_output=True,timeout=10).returncode,0)
            frame=read_screen(out/'frame');self.assertEqual(int(frame['pixels'][0,0]),1);self.assertEqual(int(frame['pixels'][1,0]),4)
            self.assertEqual(int((frame['pixels']!=0).sum()),2)
            self.assertEqual(subprocess.run([str(exe),str(out/'wrap'),'wrap'],capture_output=True,timeout=10).returncode,0)
            self.assertEqual(int(read_screen(out/'wrap')['pixels'][0,16]),2)
            for mode in ('split','mode'):
                self.assertEqual(subprocess.run([str(exe),str(out/mode),mode],capture_output=True,timeout=10).returncode,23)

    def test_reference_policy_follows_current_classification(self):
        import copy,hashlib
        from .step_state import bind_reference_policy
        item=dict(name='counter',bytes=4,sentinel=False,original_address=100,canonical_address=200,
                  verdict=True,category='game_state',slices=[[300,4]])
        stable=[{k:v for k,v in item.items() if k not in ('slices','canonical_address')}]
        stored=dict(items=[item],identity=hashlib.sha256(json.dumps(stable,sort_keys=True).encode()).hexdigest())
        live=copy.deepcopy(stored);live['items'][0].update(verdict=False,category='runtime',slices=[[400,4]])
        bound=bind_reference_policy(live,stored)
        self.assertFalse(bound['items'][0]['verdict']);self.assertEqual(bound['items'][0]['slices'],[[400,4]])
        self.assertEqual(bound['policy_changes'],[dict(name='counter',recorded='game_state',current='runtime')])
        same=bind_reference_policy(copy.deepcopy(stored),stored)
        self.assertTrue(same['items'][0]['verdict']);self.assertEqual(same['policy_changes'],[])
        tampered=copy.deepcopy(stored);tampered['identity']='0'*64
        with self.assertRaises(ValueError):bind_reference_policy(copy.deepcopy(stored),tampered)
        wrong=copy.deepcopy(stored);wrong['items'][0]['bytes']=2
        with self.assertRaises(ValueError):bind_reference_policy(wrong,stored)

    def test_actual_hook_is_read_only(self):
        from .state_schema import ROOT
        build=ROOT/'build/current/portable'
        if not (build/'report.json').is_file():self.skipTest('Native build absent')
        sdk=ROOT/'build/deps/sdl3-sdk/SDL3-3.4.16/x86_64-w64-mingw32'
        with tempfile.TemporaryDirectory() as directory:
            out=Path(directory);source=out/'hook.c';exe=out/'hook.exe'
            host=(ROOT/'portable/whole_program/platform/sdl3/host.c').as_posix()
            source.write_text('#define SIMANT_TEST_FRAMES\n#include "'+host+'"\n'+r'''
static SimGraphicsDriver graphics, before;
int native_windows_translate(SDL_Event *e) { (void)e;return 0; }
int native_windows_take_deferred(SDL_Event *e) { (void)e;return 0; }
int native_windows_filter_root(SDL_Event *e) { (void)e;return 0; }
int native_windows_pointer(float *x,float *y) { (void)x;(void)y;return 0; }
void native_windows_root_pointer(float *x,float *y) { (void)x;(void)y; }
SimGraphicsDriver *sim_graphics_source_owner(void) { return &graphics; }
int main(int argc,char **argv) {
  SimSdlPaletteHost palette={0}, saved;
  graphics.video_mode=SIM_GRAPHICS_MODE_VGA_640X480;
  graphics.vga.written=1;graphics.vga.latch[2]=73;
  graphics.last_status=SIM_GRAPHICS_FONT_UNBOUND;
  memset(graphics.vga.planes[0],255,65536);
  palette.ready=1;palette.dac6[1][0]=63;palette.dac_written[1]=1;
  palette.presentation.rgb[1][0]=255;
  before=graphics;saved=palette;
  FILE *f=fopen(argv[1],"wb");if (!f)return 2;
  portable_test_screen(f,&palette);fclose(f);
  return memcmp(&before,&graphics,sizeof(graphics)) || memcmp(&saved,&palette,sizeof(palette));
}
''')
            run=subprocess.run(['C:/msys64/mingw64/bin/gcc.exe','-std=c11','-ffunction-sections','-fdata-sections',
                '-I'+str(build/'include'),'-I'+str(ROOT),'-I'+str(build),'-I'+str(ROOT/'portable/whole_program'),
                '-I'+str(sdk/'include'),str(source),'-Wl,--gc-sections','-L'+str(sdk/'lib'),'-lSDL3','-o',str(exe)],
                capture_output=True,text=True,timeout=30)
            self.assertEqual(run.returncode,0,run.stdout+run.stderr)
            shutil.copyfile(sdk/'bin/SDL3.dll',out/'SDL3.dll')
            self.assertEqual(subprocess.run([str(exe),str(out/'frame')],capture_output=True,timeout=10).returncode,0)
            frame=read_screen(out/'frame')
            self.assertTrue((frame['pixels']==1).all())
            self.assertEqual(frame['dac'][1].tolist(),[63,0,0])

    def test_exact_pixel_and_unused_palette(self):
        with tempfile.TemporaryDirectory() as directory:
            out=Path(directory);d=out/'dos';n=out/'native'
            raw=fixture();d.write_bytes(raw);n.write_bytes(raw)
            self.assertEqual(compare_pair(d,n,out,1)['status'],'FRAME_EQUAL')
            # Cursor-sized changes are ordinary pixel differences, never masked.
            raw[1248+100*640+10]=1;n.write_bytes(raw)
            row=compare_pair(d,n,out,2)
            self.assertEqual(row['pixel_count'],1)
            self.assertEqual(row['bounding_box'],[10,100,11,101])
            self.assertEqual(len(row['png_triple']),3)
            # Unused palette entries still differ even with identical RGB scanout.
            raw=fixture();raw[112+200*3]=1;n.write_bytes(raw)
            row=compare_pair(d,n,out,3)
            self.assertEqual(row['status'],'FRAME_DIFFERENCE')
            self.assertEqual(row['palette_indices'],[200])
            self.assertEqual(row['visible_pixel_count'],0)
            n.write_bytes(raw[:-1])
            with self.assertRaises(ValueError):read_screen(n)

    def test_comment_coverage(self):
        self.assertEqual(comment_checkpoints('# one\n10 key enter\n20 key a\n# two\n30 exit\n'),[(10,'one'),(30,'two')])

if __name__=='__main__':unittest.main()
