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
uint32_t portable_test_clock_read(char k,void *p,uint32_t v){return v;}
void portable_test_step_boundary(unsigned s,unsigned p){}
void portable_test_diagnostics(FILE *f){fputs("\"pump_count\":999",f);}
int32_t __real_MacTickCount(void){return 0;}
void __real_DoAntSim(void){++state[0];++state[2];}
extern void __wrap_DoAntSim(void);
int main(int argc,char **argv){
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
            subprocess.run(['C:/msys64/mingw64/bin/gcc.exe','-std=c11',str(source),
                            str(Path(__file__).with_name('native_observer.c')),'-o',str(exe)],
                           check=True,capture_output=True,timeout=30)
            for negative in (False,True):
                expected=out/'expected';actual=out/'actual';result=out/'result';frame=out/'frame';config=out/'config'
                hashes=[]
                for i in range(3):
                    hashes += [fingerprint(bytes([9 if negative and i==1 else i+1,4])),fingerprint(b'\x07')]
                expected.write_bytes(struct.pack('<6I',*hashes))
                env=dict(os.environ,SIMANT_TEST_STEP_CONFIG=str(config))
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

    def test_stored_step_scenarios(self):
        """The driver runs every stored scenario (or reports it absent) and never launches a
        DOS recorder. Findings (exit 1 with one line per scenario) are reported, not failed:
        they are tracked in evidence/port/verification-matrix.json. A crash fails."""
        command=[os.sys.executable,str(Path(__file__).with_name('step_check.py'))]
        run=subprocess.run(command,cwd=ROOT,capture_output=True,text=True,timeout=60)
        print(run.stdout,end='')
        self.assertIn(run.returncode,(0,1),run.stderr+run.stdout)
        self.assertNotIn('Traceback',run.stderr)
        self.assertTrue(run.stdout.strip(),run.stderr)


if __name__=='__main__':unittest.main()
