"""Controls for buffered ideal observation, including the two semantic rules."""
import json
import os
from pathlib import Path
import struct
import subprocess
import tempfile
import unittest
from .step_state import fingerprint

HERE = Path(__file__).resolve().parent


class BufferedObservation(unittest.TestCase):
    def test_image_hash_fast_path_keeps_every_verdict_field(self):
        from .frame_check import compare_pair
        from .test_frames import fixture
        with tempfile.TemporaryDirectory() as directory:
            out=Path(directory);dos=out/'dos';native=out/'native';base=fixture();dos.write_bytes(base)
            # Equal, attributes, unused DAC, projected RGB, cursor-sized pixel,
            # and a diagnostic-only header byte. Legacy comparison is the
            # independent control, including its detailed mismatch reports.
            for offset in (None,96,112+200*3,1136,1248+641,56):
                with self.subTest(offset=offset):
                    raw=base[:]
                    if offset is not None:raw[offset]^=1
                    native.write_bytes(raw)
                    slow=compare_pair(dos,native,out,1)
                    fast=compare_pair(dos,native,out,1,hash_first=True)
                    signature=fast.pop('semantic_sha256')
                    self.assertEqual(fast,slow)
                    self.assertEqual(signature['dos']==signature['native'],slow['status']=='FRAME_EQUAL')

    def test_all_streams_and_requested_dump(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            source = out/'fixture.c'; exe = out/'fixture.exe'
            source.write_text(r'''
#include <stdint.h>
#include <stdio.h>
#include <inttypes.h>
static uint8_t plain[]={1,2,3},event[16]={0,0,0,0,0,0,0,0,77,88,99,11,29,250,0,0};
static uint8_t ids[]={37,0,255,255,37,0,132,3},sentinel[]={1,2,0,128,99,100};
uint32_t portable_test_clock_read(char k,void *p,uint32_t v){return v;}
void portable_test_step_boundary(unsigned s,unsigned p){}
void portable_test_diagnostics(FILE *f){fputs("\"fixture\":true",f);}
void __real_DoAntSim(void){++plain[0];}
int32_t __real_MacTickCount(void){return 0;}
int16_t StillDown(void){return 0;}
int16_t edit_scroll_and_redraw(int16_t x,int16_t y){return 0;}
extern void __wrap_DoAntSim(void);
int main(int argc,char **argv){
 FILE *f=fopen(argv[1],"w");
 fprintf(f,"unused\n%s/raw\n%s/result\n%s/state\n4 3\n",argv[2],argv[2],argv[2]);
 const uint8_t *data[]={plain,event,ids,sentinel};unsigned size[]={3,16,8,6};
 for(unsigned i=0;i<4;++i)fprintf(f,"1 %u %u 1\n%" PRId64 " %u\n",size[i],i==3,
   (int64_t)(uintptr_t)data[i]-(int64_t)(uintptr_t)portable_test_clock_read,size[i]);
 fputs("KEYBOARD_CONTEXT 1\n1 1\nIDENTITY_PATTERN 1\n2 4\n",f);fclose(f);
 for(unsigned i=0;i<4;++i)__wrap_DoAntSim();return 99;
}
''')
            compiled=subprocess.run(['C:/msys64/mingw64/bin/gcc.exe', '-O2', '-std=c11', str(source),
                            str(HERE/'native_observer.c'), '-o', str(exe)],
                           capture_output=True, text=True, timeout=30)
            self.assertEqual(compiled.returncode,0,compiled.stdout+compiled.stderr)
            config = out/'config'
            env = dict(os.environ, SIMANT_TEST_IDEAL='1', SIMANT_TEST_STEP_CONFIG=str(config),
                       SIMANT_TEST_DUMP_ENTRY='2')
            run = subprocess.run([str(exe), str(config), str(out)], env=env, capture_output=True, timeout=10)
            self.assertEqual(run.returncode, 0, run.stderr)
            event = bytes([0]*8+[77,88,99,11,29,250,0,0])
            ids = struct.pack('<4H',37,65535,37,900)
            raw=[]; context=[]; semantic=[]
            for step in range(1,4):
                row=[fingerprint(bytes([step,2,3])),fingerprint(event),fingerprint(ids),fingerprint(bytes([1,2,0,128]))]
                raw.extend(row)
                row=row[:];row[1]=fingerprint(event[:8]+event[12:]);context.extend(row)
                row=row[:];row[2]=fingerprint(struct.pack('<4H',0,65535,0,1));semantic.extend(row)
            for filename, expected in [('raw',raw),('raw.keyboard-context-v1',context),('raw.ideal-state-v2',semantic)]:
                self.assertEqual((out/filename).read_bytes(),struct.pack('<12I',*expected))
            self.assertEqual(len((out/'raw.anim-ids').read_text().splitlines()),3)
            self.assertTrue((out/'state.1').is_file())
            self.assertTrue((out/'state.2').is_file())
            self.assertFalse((out/'state.3').exists())
            self.assertFalse((out/'state').exists())
            result=json.loads((out/'result').read_text())
            self.assertEqual(result['profile']['observed_bytes'],3*(3+16+8+6))
            self.assertEqual(result['profile']['write_calls'],9)


if __name__=='__main__': unittest.main()
