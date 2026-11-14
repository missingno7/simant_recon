"""Compile the unchanged Yard draw bodies with the native position-table view."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from portable.canonical_native_abi.yard_offsets import adapt
from portable.canonical_native_abi.scalar import convert

ROOT = Path(__file__).resolve().parents[3]
CC = 'C:/msys64/mingw64/bin/gcc.exe'


def body(source, name):
    start = source.index('void far ' + name + '(void)\n{')
    end = source.index('\n}', start) + 2
    return source[start:end]


class YardPositions(unittest.TestCase):
    def test_compiled_draw_positions_and_split_storage_negative(self):
        canonical = (ROOT/'src/ui/yard_window.c').read_text()
        adapted = adapt(canonical)
        tables = adapted[:adapted.index('/*\n * Handles yard')]
        functions = '\n'.join(body(adapted, name) for name in ('DrawSimKid', 'DrawDog', 'DrawSimCat'))
        definitions = r'''
#include <stdint.h>
#include <stdlib.h>
#include <stdio.h>
typedef char **Handle;
struct Pt { int16_t x,y; };
struct Rect { int16_t left,top,right,bottom; };
#define PIC_YARD_HUMAN_FRAME_BASE 8000
#define PIC_YARD_DOG_FRAME_BASE 8500
#define PIC_YARD_CAT_FRAME_BASE 8400
#define PIC_HUMAN_BALLOON_BUFFER 30000
static int16_t BoyX=100,BoyY=200,BoyFrame,DogX=100,DogY=200,DogFrame,CatX=100,CatY=200,CatFrame;
static int16_t gfx_screen_width_pixels=640,GamePaused=1,BoyMessOn,BoyMsgOffset,ForSaleState;
static int16_t g_2A2A=-1,g_2A30=-1,g_2A2C=-1,g_2A3E=-1;
static int32_t BoyMsgCnt,g_2A36;
static Handle yardAnimHandle;
static char **BoyMsgs;
static struct Rect map_viewport_rect={17,23,500,400};
static int16_t captured_x,captured_y,captured_pic;
static int16_t hanim_AddAnimObject(Handle h,int16_t x,int16_t y,int16_t p,int16_t pri) {
  captured_x=x;captured_y=y;captured_pic=p;return 7;
}
static void hanim_SetObjectPos(int16_t x,int16_t y,int16_t p,Handle h,int16_t id,int16_t pri) {
  captured_x=x;captured_y=y;captured_pic=p;
}
static int32_t MacTickCount(void){return 0;}
static void hanim_RemoveAnimObject(Handle h,int16_t id){}
static void mem_Free(int32_t h){}
static void font_SetFont(int16_t font){}
static int32_t MakeBalloon(char *msg,int16_t flags){return 0;}
static void gr_BitMapSize(struct Pt *p,int16_t id){p->x=40;p->y=20;}
'''
        checks = r'''
int main(void) {
  if(sizeof(struct YardPositionTables)!=116)return 9;
  /* Values below are original signed-byte operand results, including reads
   * into the NEXT declared table. Picture/frame selection stays identical. */
  BoyFrame=20;DrawSimKid();
  if(captured_x!=121 || captured_y!=223 || captured_pic!=8020)return 1;
  BoyFrame=103;DrawSimKid();
  if(captured_x!=118 || captured_y!=224 || captured_pic!=8103)return 2;
  DogFrame=100;DrawDog();
  if(captured_x!=119 || captured_y!=224 || captured_pic!=8600)return 3;
  DogFrame=102;DrawDog();
  if(captured_x!=119 || captured_y!=226 || captured_pic!=8602)return 4;
  DogFrame=9;DrawDog();
  if(captured_x!=118 || captured_y!=224 || captured_pic!=8509)return 5;
  CatFrame=12;DrawSimCat();
  if(captured_x!=107 || captured_y!=205 || captured_pic!=8412)return 6;
  char *messages[]={"The ant is a hexapod"};
  BoyMsgs=messages;BoyMessOn=1;BoyFrame=20;DrawSimKid();
  if(captured_x!=125 || captured_y!=203 || captured_pic!=30000)return 7;
  gfx_screen_width_pixels=320;DogFrame=100;DrawDog();
  if(captured_x!=73 || captured_y!=129 || captured_pic!=8600)return 8;
  return 0;
}
'''
        # Explicitly separate the five storage members in the control. Its
        # dog/human frame is unchanged; only the cross-table x byte is wrong.
        negative = functions.replace('((signed char *)&yard_position_tables)[0 + (BoyFrame + 4)]',
                                     'yard_position_tables.kidX[(BoyFrame + 4) % 12]')
        self.assertNotEqual(functions, negative)
        with tempfile.TemporaryDirectory() as directory:
            for label, draw, expected in (('positive', functions, 0), ('split-control', negative, 1)):
                source=Path(directory)/(label+'.c');exe=source.with_suffix('.exe')
                source.write_text(convert(definitions+tables+draw)+checks)
                run=subprocess.run([CC,'-std=c11','-O2',str(source),'-o',str(exe)],capture_output=True,text=True,timeout=30)
                self.assertEqual(run.returncode,0,run.stderr)
                self.assertEqual(subprocess.run([str(exe)],capture_output=True,timeout=10).returncode,expected,label)

    def test_changed_table_fails_closed(self):
        source=(ROOT/'src/ui/yard_window.c').read_text()
        with self.assertRaisesRegex(ValueError,'dogWalkY'):
            adapt(source.replace('dogWalkY[8]', 'dogWalkY[12]'))


if __name__ == '__main__':
    unittest.main()
