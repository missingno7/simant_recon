"""Execute the actual full-clock and SDL input hooks, including rejection lanes."""
import os,shutil,subprocess,tempfile,unittest
from pathlib import Path
from .state_schema import ROOT
from .full_inputs import parse_trace
from .capture_dos_steps import countdown_points

class FullInputControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory();cls.out=Path(cls.tmp.name)
        sdk=ROOT/'build/deps/sdl3-sdk/SDL3-3.4.16/x86_64-w64-mingw32'
        cls.sdk=sdk;cls.exe=cls.out/'control.exe'
        source=cls.out/'control.c'
        source.write_text('''#include "portable/whole_program/platform/sdl3/host_modes.h"
#include "portable/whole_program/platform/input_time.h"
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
int native_windows_translate(SDL_Event *e) { (void)e;return 0; }
int native_windows_take_deferred(SDL_Event *e) { (void)e;return 0; }
int native_windows_filter_root(SDL_Event *e) { (void)e;return 0; }
int native_windows_pointer(float *x,float *y) { (void)x;(void)y;return 0; }
void native_windows_root_pointer(float *x,float *y) { (void)x;(void)y; }
static void rejected(int s) { (void)s;_Exit(23); }
static Host *control_host;
static unsigned down_seen,up_seen;
static int check_context;
int portable_input_time_host_interrupt(void) {
    HostEvent e;
    while (host_poll_event(control_host,&e)>0) {
        uint16_t cx=0,dx=0;
        portable_test_irq_context(&cx,&dx);
        if (check_context && (cx!=(e.kind==HOST_EVENT_KEY_DOWN ? 770 : 2366) ||
                              dx!=(e.kind==HOST_EVENT_KEY_DOWN ? 24023 : 23596))) return -1;
        if (!check_context && (cx || dx)) return -1;
        if (e.kind==HOST_EVENT_KEY_DOWN) {
            if (e.key!=0x1c0d)return -1;
            ++down_seen;
            if (portable_test_clock_read('B',(void *)((uintptr_t)portable_test_clock_read+14),99)!=11)return -1;
        }
        if (e.kind==HOST_EVENT_KEY_UP) ++up_seen;
    }
    return 1;
}
int main(int argc,char **argv) {
    signal(SIGABRT,rejected);
    if (argc>1 && !strcmp(argv[1],"unclocked")) {
        HostEvent e;
        host_virtual_clock_configure(1);
        SDL_SetHintWithPriority(SDL_HINT_VIDEO_DRIVER,"dummy",SDL_HINT_OVERRIDE);
        control_host=host_create_dimensions("input control",1,640,480);if (!control_host)return 20;
        while (host_poll_event(control_host,&e)>0) {}
        portable_test_input_sample(249,0);
        portable_test_before_poll();
        if (down_seen!=1 || up_seen)return 21;
        portable_test_input_sample(246,0);
        portable_test_before_poll();
        if (up_seen!=1)return 22;
        host_destroy(control_host);return 0;
    }
    if (argc>1 && !strncmp(argv[1],"services",8)) {
        HostEvent e;
        check_context=!strcmp(argv[1],"services-context");
        host_virtual_clock_configure(1);
        SDL_SetHintWithPriority(SDL_HINT_VIDEO_DRIVER,"dummy",SDL_HINT_OVERRIDE);
        control_host=host_create_dimensions("input control",1,640,480);if (!control_host)return 20;
        while (host_poll_event(control_host,&e)>0) {}
        void *pc=(void *)((uintptr_t)portable_test_clock_read+13);
        if (portable_test_clock_read('T',pc,99)!=7 || down_seen!=1 || up_seen)return 21;
        if (portable_test_clock_read('T',pc,99)!=7 || down_seen!=1 || up_seen!=1)return 22;
        if (portable_test_clock_read('C',NULL,99)!=2 || up_seen!=1)return 24;
        host_destroy(control_host);return 0;
    }
    void *pc=(void *)((uintptr_t)portable_test_clock_read+13);
    if (argc>1 && !strcmp(argv[1],"wrong"))pc=(void *)((uintptr_t)pc+1);
    if (argc>1 && !strcmp(argv[1],"devices")) {
        uint32_t value=portable_test_clock_read('h',pc,0);
        printf("%u\\n",value);return 0;
    }
    uint32_t a=portable_test_observed_clock('T',pc,99);
    if (argc>1 && !strcmp(argv[1],"short"))return 0;
    uint32_t b=portable_test_observed_clock('T',pc,99);
    uint32_t c=portable_test_observed_clock('C',NULL,99);
    printf("%u %u %u\\n",a,b,c);return 0;
}
''')
        cc=shutil.which('gcc') or 'C:/msys64/mingw64/bin/gcc.exe'
        run=subprocess.run([cc,'-std=c11','-Wall','-Wextra','-Werror','-O0','-I'+str(ROOT),'-I'+str(sdk/'include'),
            str(source),str(ROOT/'portable/whole_program/platform/sdl3/host.c'),'-L'+str(sdk/'lib'),'-lSDL3','-o',str(cls.exe)],capture_output=True,text=True,timeout=60)
        if run.returncode:raise RuntimeError(run.stdout+run.stderr)
    @classmethod
    def tearDownClass(cls):cls.tmp.cleanup()
    def run_hook(self,clock=None,events=None,mode=None,order=None,disable_context=False):
        env=dict(os.environ,PATH=str(self.sdk/'bin')+os.pathsep+os.environ.get('PATH',''))
        for name in ('SIMANT_TEST_FULL_CLOCK','SIMANT_TEST_SERVICE_INPUT','SIMANT_TEST_CLOCK_CONTROL_READ','SIMANT_TEST_SERVICE_ORDER','SIMANT_TEST_DISABLE_IRQ_CONTEXT'):env.pop(name,None)
        if disable_context:env['SIMANT_TEST_DISABLE_IRQ_CONTEXT']='1'
        for name,value,filename in [('SIMANT_TEST_FULL_CLOCK',clock,'clock.txt'),('SIMANT_TEST_SERVICE_INPUT',events,'events.txt')]:
            if value is not None:
                p=self.out/filename;p.write_text(value);env[name]=str(p)
        if order is not None:
            p=self.out/'order.bin';p.write_bytes(order);env['SIMANT_TEST_SERVICE_ORDER']=str(p)
        return subprocess.run([str(self.exe)]+([mode] if mode else []),env=env,capture_output=True,text=True,timeout=15)
    def test_device_order_and_real_answer_without_tape(self):
        self.assertEqual(self.run_hook(mode='devices').stdout.strip(),'0')
        tape='h 13 h 123 1 1\nX\n'
        good=self.run_hook(tape,mode='devices',order=bytes([0]))
        self.assertEqual(good.returncode,0,good.stderr)
        self.assertEqual(good.stdout.strip(),'1')
        self.assertEqual(self.run_hook(tape,mode='devices',order=bytes([254])).returncode,23)

    def test_device_queries_bind_all_reachable_retf_instructions(self):
        from .device_services import return_points
        # conditional return: both independently reachable RETFs, no scan into data
        returns,instructions=return_points(bytes.fromhex('85c0 7401 cb cb 90'),0)
        self.assertEqual(returns,[4,5])
        self.assertNotIn(6,instructions)
        for raw in ('c3','ff e0'):
            with self.assertRaises(ValueError):return_points(bytes.fromhex(raw),0)

    def test_v5_atomic_sample_and_bios_callback_admission_points(self):
        from capstone import Cs,CS_ARCH_X86,CS_MODE_16
        from .capture_dos_steps import sample_admission_points
        memory=bytes.fromhex('a1 34 12 fe 38 08 00 cf')
        decoder=Cs(CS_ARCH_X86,CS_MODE_16)
        self.assertEqual(sample_admission_points(memory,[('P',0),('F',3)],decoder),{0:3,3:7})
        self.assertEqual(sample_admission_points(bytes(0xa0000),[('F',0xfcfc1)],decoder),{0xfcfc1:0xfcfc5})
        with self.assertRaisesRegex(ValueError,'callback extent'):
            sample_admission_points(bytes.fromhex('fe38 0800 90'),[('F',0)],decoder)

    def test_v5_hold_requires_real_delivery_at_same_boundary(self):
        trace=self.out/'quiet.txt'
        body=('U raise 10.1 10 1234 100 200 2 0 0 0 3\n'
              'I 10 2 0 0 key_down enter\n'
              'D K 10.2 2 0 0 0 28 0 17 19 R 3\n'
              'U return 10.3 1234 100 200\n'
              'S 11 2 1 1 0 0 3\n')
        trace.write_text(body)
        self.assertEqual(len(parse_trace(trace,1,require_quiet=True)[1]),1)
        for bad in (body.replace(' R 3',' R 4'),
                    body.replace('U raise 10.1 10 1234 100 200 2 0 0 0 3\n',''),
                    body.replace('D K 10.2 2 0 0 0 28 0 17 19 R 3\n','')):
            trace.write_text(bad)
            with self.assertRaises(ValueError):parse_trace(trace,1,require_quiet=True)

    def test_v4_reference_is_refused_before_replay(self):
        import json
        from .step_check import validate_reference
        directory=self.out/'old';directory.mkdir(exist_ok=True)
        (directory/'manifest.json').write_text(json.dumps({'input_contract':'service-samples-v4'}))
        with self.assertRaisesRegex(ValueError,'pre-v8 timing is refused'):
            validate_reference(directory,ROOT/'dos/scenarios/new-game-save.json')

    def test_actual_cross_translation_unit_hook_and_rle(self):
        r=self.run_hook('T 13 T 100 7 2\nC 0 C 0 2 1\nX\n')
        self.assertEqual(r.returncode,0,r.stderr);self.assertEqual(r.stdout.strip(),'7 7 2')
        r=self.run_hook();self.assertEqual(r.returncode,0);self.assertEqual(r.stdout.strip(),'99 99 99')
    def test_missing_wrong_pc_and_invalid_count_rejected(self):
        good='T 13 T 100 7 2\nC 0 C 0 2 1\nX\n'
        for tape,mode in [(good,'short'),(good,'wrong'),('T 13 T 100 7 0\nX\n',None),('T 13 T 100 7 2\n',None)]:
            r=self.run_hook(tape,mode=mode);self.assertEqual(r.returncode,23,r.stderr)
    def test_input_after_sample_preserves_nested_bios_stamp(self):
        tape='T 13 T 100 7 2\nB 14 V 0 11 1\nC 0 C 0 2 1\nX\n'
        events='1 0 0 keydown enter 0 0\n3 0 0 keyup enter 0 0\n'
        r=self.run_hook(tape,events,mode='services',order=bytes([0,1,0,2]))
        self.assertEqual(r.returncode,0,r.stderr)
        r=self.run_hook(tape,events,mode='services',order=bytes([0,0,1,2]))
        self.assertEqual(r.returncode,23,r.stderr)
        self.assertIn('service order mismatch at 2',r.stderr)
    def test_unclocked_input_samples_advance_admission(self):
        tape='B 14 V 0 11 1\nX\n'
        events='1 0 0 keydown enter 0 0\n3 0 0 keyup enter 0 0\n'
        r=self.run_hook(tape,events,mode='unclocked',order=bytes([249,0,246]))
        self.assertEqual(r.returncode,0,r.stderr)
        r=self.run_hook(tape,events,mode='unclocked',order=bytes([249,246,0]))
        self.assertEqual(r.returncode,23,r.stderr)
    def test_irq_context_follows_each_raw_event_and_can_be_disabled(self):
        tape='T 13 T 100 7 2\nB 14 V 0 11 1\nC 0 C 0 2 1\nX\n'
        events='1 0 0 keydown enter 0 0 770 24023\n3 0 0 keyup enter 0 0 2366 23596\n'
        order=bytes([0,1,0,2])
        r=self.run_hook(tape,events,mode='services-context',order=order)
        self.assertEqual(r.returncode,0,r.stderr)
        r=self.run_hook(tape,events,mode='services',order=order,disable_context=True)
        self.assertEqual(r.returncode,0,r.stderr)
        for bad in (events.replace('770','65536'),events.replace('770 24023','770'),events.replace('770 24023','770 24023 extra')):
            r=self.run_hook(tape,bad,mode='services-context',order=order)
            self.assertEqual(r.returncode,23,r.stderr)
    def test_bounded_trace_keeps_counts_and_phase(self):
        p=self.out/'trace.txt';p.write_text('# test\nR T 100 7 2\nI 5 10 0 0 key_down enter\nS 6 11 1 1 2 99\nR T 100 8 1\n')
        r,i,b=parse_trace(p,1)
        self.assertEqual(r,[('T',256,7,2)]);self.assertEqual(i[0]['pump'],10);self.assertEqual(i[0]['clock_reads'],2)
        self.assertEqual(b[0]['clock_reads'],2);self.assertEqual(b[0]['clock_hash'],99)
        with self.assertRaises(ValueError):parse_trace(p,2)
    def test_actual_irq_delivery_replaces_scheduled_submission(self):
        p=self.out/'irq.txt';p.write_text('I 5 9 0 0 key_down enter\nR T 100 7 2\nD K 5.3 10 0 0 2 7196 0 0 0\nS 6 11 1 1 2 99\n')
        _,i,_=parse_trace(p,1)
        self.assertEqual((i[0]['milliseconds'],i[0]['pump'],i[0]['clock_reads']),(5.3,10,2))
        p.write_text(p.read_text().replace('7196','40092'))
        with self.assertRaises(ValueError):parse_trace(p,1)
    def test_small_decimal_es_countdown_operand_and_independent_segment(self):
        m=bytearray(0x2000)
        for at in (0x1000,0x1100):m[at:at+7]=bytes.fromhex('26 83 3e 06 00 00 cb')
        m[0x1203:0x1205]=(0x1234).to_bytes(2,'little')
        points=countdown_points(m,0,dict(timer_wait_countdown=0x1000,timer_countdown_done=0x1100),dict(SeedSRand=0x1205))
        self.assertEqual(points,[('C',0x1000),('C',0x1100),('D',0x12346)])
        m[0x1103]=8
        with self.assertRaises(ValueError):countdown_points(m,0,dict(timer_wait_countdown=0x1000,timer_countdown_done=0x1100),dict(SeedSRand=0x1205))
if __name__=='__main__':unittest.main()
