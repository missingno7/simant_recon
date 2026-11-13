"""Clock tape rejection controls and observed replay regression controls."""
import os,shutil,subprocess,tempfile,unittest
from pathlib import Path
if __package__:
    from .native_acceptance import ROOT
else:
    from native_acceptance import ROOT


class ClockTapeControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cc=shutil.which('gcc') or 'C:/msys64/mingw64/bin/gcc.exe'
        if not Path(cc).is_file(): raise unittest.SkipTest('MinGW compiler unavailable')
        cls.scratch=tempfile.TemporaryDirectory();cls.directory=Path(cls.scratch.name)
        source=cls.directory/'clock.c';cls.exe=cls.directory/'clock.exe'
        # Compile the actual opt-in service in isolation; keep one implementation.
        hook=(ROOT/'portable/whole_program/platform/m1b73_events.c').read_text().split(
            '/* BEGIN TEST CLOCK INPUTS:',1)[1].split('*/',1)[1].split('/* END TEST CLOCK INPUTS */',1)[0]
        source.write_text('''#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <signal.h>
'''+hook+'''
void SeedSRand(void) {}
static void rejected(int sig) { (void)sig; _Exit(23); }
int main(int argc,char **argv) {
    signal(SIGABRT,rejected);
    void *s=(void *)((uintptr_t)SeedSRand+13), *r=(void *)((uintptr_t)SeedSRand+58);
    uint32_t a=clock_replay_value(s,0);
    if (argc>1 && !strcmp(argv[1],"short")) return 0;
    if (clock_replay_value((void *)((uintptr_t)SeedSRand+99),99)!=99) return 9;
    uint32_t b=clock_replay_value(s,0),c=clock_replay_value(r,0);
    printf("%u %u %u\\n",a,b,c);
    if (argc>1 && !strcmp(argv[1],"extra")) clock_replay_value(s,0);
    return 0;
}
''')
        subprocess.run([cc,'-std=c11','-Wall','-Wextra','-Werror','-I',str(ROOT),str(source),'-o',str(cls.exe)],check=True,capture_output=True,timeout=60)
    @classmethod
    def tearDownClass(cls): cls.scratch.cleanup()

    def run_tape(self,tape=None,mode=None):
        env=dict(os.environ);env.pop('SIMANT_TEST_CLOCK_REPLAY',None)
        if tape is not None:
            path=self.directory/'input.txt';path.write_text(tape);env['SIMANT_TEST_CLOCK_REPLAY']=str(path)
        return subprocess.run([str(self.exe)]+([mode] if mode else []),env=env,capture_output=True,text=True,timeout=15)

    def test_opt_in_and_original_values(self):
        result=self.run_tape();self.assertEqual(result.returncode,0);self.assertEqual(result.stdout.strip(),'0 0 0')
        result=self.run_tape('S 13 1 1\nS 13 2 1\nR 58 1 1\n')
        self.assertEqual(result.returncode,0);self.assertEqual(result.stdout.strip(),'1 1 1')

    def test_wrong_order_duplicate_missing_extra_and_unconsumed_fail(self):
        good='S 13 1 1\nS 13 2 1\nR 58 1 1\n'
        for tape,mode in [(good,'short'),(good,'extra'),
                          ('S 13 2 1\nS 13 1 1\nR 58 1 1\n',None),
                          ('S 13 1 1\nS 13 1 1\nR 58 1 1\n',None),
                          ('S 13 1 1\nR 58 1 1\n',None),('S 999 1 1\n',None)]:
            with self.subTest(tape=tape,mode=mode):self.assertNotEqual(self.run_tape(tape,mode).returncode,0)


if __name__=='__main__': unittest.main()
