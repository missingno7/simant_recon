"""Relink the pinned DOSBox observer with compact, read-only capture hooks.

Uses installed unchanged emulator objects; replaces only dosbox.cpp. All outputs
and compiler/linker auxiliary files are in the explicit scratch directory.
"""
import argparse, hashlib, json, re, subprocess
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
SOURCE=Path('C:/tools/dosbox-x-2026.08.31-simant-acceptance-observation-src')

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args(); out=a.out.resolve();out.mkdir(parents=True,exist_ok=True)
    obj=SOURCE/'obj/dosbox-x/x64/Release SDL2'
    logs=obj/'dosbox-x.tlog'
    source=SOURCE/'src/dosbox.cpp'; text=source.read_text()
    marker='void DOSBOX_AcceptanceOnInstruction(void) {'
    text=text.replace(marker,'#include "compact_observer.inc"\n'+marker+'\n    CompactInstruction(SegPhys(cs)+reg_eip);',1)
    text=text.replace('DOSBOX_AcceptanceExecArmed = still_armed;','DOSBOX_AcceptanceExecArmed = still_armed || compact_file != NULL;',1)
    text=text.replace('switch (event.action) {','CompactInput(event,emulated_ms);\n    switch (event.action) {',1)
    # Start after the acceptance scheduler has established its epoch.
    pos=text.index('static void AcceptanceRunEvent(Bitu event_index) {')
    text=text[:pos]+text[pos:].replace('if (event_index >= acceptance_events.size()) return;',
        'static bool compact_initialized=false;\n    if (!compact_initialized) { compact_initialized=true; CompactInit(); }\n    if (event_index >= acceptance_events.size()) return;',1)
    patched=out/'dosbox.cpp';patched.write_text(text)
    (out/'compact_observer.inc').write_bytes((HERE/'compact_observer.inc').read_bytes())
    clines=(logs/'CL.command.1.tlog').read_text(encoding='utf-16').splitlines()
    compile_args=next(clines[i+1] for i,l in enumerate(clines[:-1]) if l.upper().endswith('OBSERVATION-SRC\\SRC\\DOSBOX.CPP'))
    compile_args=re.sub(r'/Fo"[^"]*"',lambda m:'/Fo"'+str(out/'dosbox.obj')+'"',compile_args,flags=re.I)
    compile_args=re.sub(r'/Fd"[^"]*"',lambda m:'/Fd"'+str(out/'compiler.pdb')+'"',compile_args,flags=re.I)
    compile_args=compile_args[:compile_args.upper().rfind(' C:\\TOOLS\\')]+ ' "'+str(patched)+'"'
    (out/'compile.rsp').write_text(compile_args)
    link=(logs/'link.command.1.tlog').read_text(encoding='utf-16').splitlines()
    start=max(i for i,l in enumerate(link) if l.startswith('^'))
    link='\n'.join(link[start+1:])
    for option,filename in [('OUT','dosbox-x.exe'),('PDB','dosbox-x.pdb'),('IMPLIB','dosbox-x.lib'),('LTCGOUT','dosbox-x.iobj')]:
        link=re.sub('/'+option+r':"[^"]*"',lambda m:'/'+option+':"'+str(out/filename)+'"',link,flags=re.I)
    link=re.sub(r'/NATVIS:\S+','',link,flags=re.I)
    link=re.sub(r'"[^"\n]*\\DOSBOX\.OBJ"',lambda m:'"'+str(out/'dosbox.obj')+'"',link,flags=re.I)
    (out/'link.rsp').write_text(link)
    vc=Path('C:/Program Files/Microsoft Visual Studio/2022/Community/VC/Auxiliary/Build/vcvars64.bat')
    (out/'build.cmd').write_text('@echo off\ncall "'+str(vc)+'"\ncl @compile.rsp\nif errorlevel 1 exit /b 1\nlink @link.rsp\n')
    run=subprocess.run(['cmd','/c',str(out/'build.cmd')],cwd=out,capture_output=True,text=True,timeout=600)
    (out/'build.log').write_text(run.stdout+run.stderr)
    if run.returncode: raise RuntimeError((run.stdout+run.stderr)[-5000:])
    inputs=[source,SOURCE/'src/cpu/callback.cpp',SOURCE/'src/ints/bios_keyboard.cpp',HERE/'compact_observer.inc',HERE/'build_observer.py']+sorted(obj.glob('*.obj'))
    receipt=dict(schema='simant-read-only-observer-build-v1',executable=str(out/'dosbox-x.exe'),
        sha256=sha(out/'dosbox-x.exe'),inputs={str(p):sha(p) for p in inputs},
        patched_source_sha256=sha(patched),compiler_response_sha256=sha(out/'compile.rsp'),linker_response_sha256=sha(out/'link.rsp'),
        scope='Read-only compact clock returns, pump/step ordinals and scheduled host-input observations; no guest mutation.')
    (out/'observer-build.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps({k:v for k,v in receipt.items() if k!='inputs'},indent=2))
if __name__=='__main__': main()
