"""Shared unchanged golden read vectors, ISR transition and omitted-notification control."""
import argparse,json,os,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
def run(out):
    out=out.resolve();out.mkdir(parents=True,exist_ok=False)
    cc='C:/msys64/mingw64/bin/gcc.exe';cxx='C:/msys64/mingw64/bin/g++.exe'
    base=[cc,'-std=c11','-O0','-g','-I'+str(ROOT)];commands=[];results=[]
    def execute(command,expected=0):
        commands.append(command);r=subprocess.run(command,capture_output=True,text=True,timeout=90)
        results.append(dict(command=command,code=r.returncode,stdout=r.stdout,stderr=r.stderr))
        if r.returncode!=expected:raise RuntimeError(str(results[-1]))
    pit=ROOT/'portable/whole_program/platform/pit_clock.c';golden=ROOT/'portable/tests/idle_yield/rule.c'
    execute(base+['-c',str(pit),'-o',str(out/'pit.o')])
    execute(base+['-Dportable_input_time_read_quantum=dos_clock_read_quantum','-c',str(golden),'-o',str(out/'golden.o')])
    (out/'dos.cpp').write_text('#include "native_clock_v1.h"\nextern "C" uint64_t dos_clock_read_quantum(const char*s,uint64_t q){return DosClockReadQuantum(s,q);}\n')
    execute([cxx,'-I'+str(HERE/'ideal'),'-c',str(out/'dos.cpp'),'-o',str(out/'dos.o')])
    execute([cxx,str(out/'golden.o'),str(out/'dos.o'),str(out/'pit.o'),'-o',str(out/'dos.exe')]);execute([str(out/'dos.exe')])
    execute(base+[str(ROOT/'portable/whole_program/platform/input_time.c'),str(pit),str(golden),'-o',str(out/'native.exe')]);execute([str(out/'native.exe')])
    files=['portable/tests/acceptance/ideal_timer_test.c','portable/whole_program/platform/whole_audio_provider.c','portable/whole_program/platform/audio_native.c','portable/audio/isa_devices.cpp','portable/audio/ymfm/ymfm_opl.cpp','portable/audio/ymfm/ymfm_adpcm.cpp','portable/audio/ymfm/ymfm_pcm.cpp']
    objects=[]
    for i,name in enumerate(files):
        obj=out/f'{i}.o';objects.append(str(obj))
        execute([cc,'-std=c++17' if name.endswith('.cpp') else '-std=c11','-I'+str(ROOT),'-c',str(ROOT/name),'-o',str(obj)])
    execute([cc,*objects,'-static','-lstdc++','-o',str(out/'timer.exe')]);execute([str(out/'timer.exe')])
    reload_object=out/'reload.o'
    execute(base+['-c',str(ROOT/'portable/tests/acceptance/ideal_reload_edge_test.c'),'-o',str(reload_object)])
    reload_objects=[str(reload_object),*objects[1:]]
    execute([cc,*reload_objects,'-static','-lstdc++','-o',str(out/'reload.exe')]);execute([str(out/'reload.exe')])
    reload_provider=(ROOT/files[1]).read_text()
    edge='if(pit_output_low(p)) p->pending_irq=1;'
    if reload_provider.count(edge)!=1:raise ValueError('Reload edge binding differs')
    (out/'no-reload-edge.c').write_text(reload_provider.replace(edge,''))
    execute(base+['-I'+str(ROOT/'portable/whole_program/platform'),'-c',str(out/'no-reload-edge.c'),'-o',str(out/'no-reload-edge.o')])
    no_edge=[str(reload_object),str(out/'no-reload-edge.o'),*objects[2:]]
    execute([cc,*no_edge,'-static','-lstdc++','-o',str(out/'no-reload-edge.exe')]);execute([str(out/'no-reload-edge.exe')],1)
    fractional='(p->irq_ns<target || (p->irq_ns==target && !p->irq_fraction))'
    if reload_provider.count(fractional)!=1:raise ValueError('Rational endpoint binding differs')
    (out/'early-edge.c').write_text(reload_provider.replace(fractional,'p->irq_ns<=target'))
    execute(base+['-I'+str(ROOT/'portable/whole_program/platform'),'-c',str(out/'early-edge.c'),'-o',str(out/'early-edge.o')])
    early=[str(reload_object),str(out/'early-edge.o'),*objects[2:]]
    execute([cc,*early,'-static','-lstdc++','-o',str(out/'early-edge.exe')]);execute([str(out/'early-edge.exe')],1)
    # Same ISR with only its slow reprogram notification removed. The expected
    # source semantics remain unchanged; this must fail the positive fixture.
    provider=(ROOT/files[1]).read_text();needle='timer_event(p,1);return;'
    if provider.count(needle)!=1:raise ValueError('Slow notification binding differs')
    (out/'negative.c').write_text(provider.replace(needle,'return;'))
    execute(base+['-I'+str(ROOT/'portable/whole_program/platform'),'-c',str(out/'negative.c'),'-o',str(out/'negative.o')])
    negative=objects[:];negative[1]=str(out/'negative.o')
    execute([cc,*negative,'-static','-lstdc++','-o',str(out/'negative.exe')]);execute([str(out/'negative.exe')],1)
    # The real CLI/STI fixture must detect delivery while guest IF is clear.
    guard='if(portable_whole_audio_interrupts_enabled()) {'
    if provider.count(guard)!=1:raise ValueError('IF delivery binding differs')
    (out/'forced-if.c').write_text(provider.replace(guard,'if(1) {'))
    execute(base+['-I'+str(ROOT/'portable/whole_program/platform'),'-c',str(out/'forced-if.c'),'-o',str(out/'forced-if.o')])
    forced=objects[:];forced[1]=str(out/'forced-if.o')
    execute([cc,*forced,'-static','-lstdc++','-o',str(out/'forced-if.exe')]);execute([str(out/'forced-if.exe')],1)
    (out/'report.json').write_text(json.dumps(dict(status='PASS',results=results),indent=2)+'\n')
    print('PASS: shared DOS/native golden vectors, timer transition, negative control',flush=True)
if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();run(a.out)
