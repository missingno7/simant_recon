"""The only omitted bytes are h/v of explicitly bound, qualified Event records."""
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from .sound_off import select_config,context_views

HERE=Path(__file__).resolve().parent
class EventContext(unittest.TestCase):
    def test_shipped_configuration_selection(self):
        before=b'Display Mode: V\r\nSound Mode: 6\r\n'
        self.assertEqual(select_config(before),b'Display Mode: V\r\nSound Mode: 0\r\n')
        self.assertEqual(select_config(select_config(before)),select_config(before))
        with self.assertRaises(ValueError):select_config(b'Display Mode: T\nSound Mode: 6\n')

    def test_c_and_cpp_observer_qualification(self):
        source=r'''
#include "event_context_rule.h"
#include <stdio.h>
#include <string.h>
#define CHECK(c) do { if(!(c)) {fprintf(stderr,"failed line %d\n",__LINE__);return 1;} } while(0)
static uint32_t hash(const uint8_t *p,unsigned records) {
    uint32_t h=2166136261u;
    for(unsigned at=0;at<32;++at) if(simant_event_context_includes(p,records,at)) h=(h^p[at])*16777619u;
    return h;
}
int main(void) {
    uint8_t a[32]={0},b[32];
    /* Exhaust the code domain. Mutate each byte independently: flags, time,
     * modifiers, code and payload always matter, as does every mouse/object
     * coordinate. The second Event is deliberately outside the bound span. */
    for(unsigned code=0;code<65536;++code) {
        a[12]=(uint8_t)code;a[13]=(uint8_t)(code>>8);
        int keyboard=(code>=0xfa00 && code<=0xfaff) || (code>=0xf081 && code<=0xf087);
        for(unsigned at=0;at<32;++at) {
            memcpy(b,a,32);b[at]^=1;
            CHECK((hash(a,1)==hash(b,1))==(keyboard && at>=8 && at<12));
            CHECK(hash(a,0)!=hash(b,0));
        }
    }
    /* Real entry72: code FA1D, h0202/0002, same DGROUP. */
    uint8_t original[16]={0,0,0,0,13,2,0,0,2,2,215,93,29,250,0,0};
    memset(a,0,32);memcpy(a,original,16);memcpy(b,a,32);b[9]=0;
    CHECK(hash(a,1)==hash(b,1) && hash(a,0)!=hash(b,0));
    puts("PASS keyboard context: every code/byte, raw and mouse/object negative controls");return 0;
}
'''
        with tempfile.TemporaryDirectory() as temporary:
            out=Path(temporary);file=out/'rule.c';file.write_text(source)
            for compiler,language in [('gcc','c11'),('g++','c++17')]:
                exe=out/(compiler+'.exe')
                subprocess.run(['C:/msys64/mingw64/bin/'+compiler+'.exe','-O2','-std='+language,'-I'+str(HERE),str(file),'-o',str(exe)],check=True,capture_output=True,timeout=60)
                run=subprocess.run([str(exe)],capture_output=True,text=True,timeout=20)
                self.assertEqual(run.returncode,0,run.stderr)

if __name__=='__main__':unittest.main()
