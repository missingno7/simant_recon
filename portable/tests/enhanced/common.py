"""Fresh test-only links over production objects; all children are bounded/joined."""
import json, shutil, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
from portable.tests.acceptance.state_schema import sha
from portable.tests.hidden_desktop import install
install()

def check_build(build):
    report=json.loads((build/'report.json').read_text())
    if not report['passed'] or not report['input_stability']['at_end']:
        raise ValueError('Successful stable fresh native build required')
    changed=[p for p,h in report['input_pins'].items() if sha(ROOT/p)!=h]
    if changed:raise ValueError('Rebuild changed production inputs: '+str(changed))
    return report

def probe_link(build,out,observer=None):
    report=check_build(build);out.mkdir(parents=True,exist_ok=False)
    obj=out/'enhanced-probe.o';source=Path(__file__).with_name('probe.c')
    command=[report['application_link']['command'][0],'-std=c11','-O2','-g','-fno-lto','-I'+str(ROOT),'-I'+str(ROOT/'build/deps/sdl3-sdk/SDL3-3.4.16/x86_64-w64-mingw32/include'),'-c',str(source),'-o',str(obj)]
    if observer:command+=['-DENHANCED_ACCEPTANCE']
    subprocess.run(command,check=True,capture_output=True,timeout=60)
    if observer:
        receipt=json.loads((observer.parent/'observer-build.json').read_text())
        command=receipt['command'][:]
    else:command=report['application_link']['command'][:]
    exe=out/'simant-enhanced-test.exe'
    command[command.index('-o')+1]=str(exe)
    command[1:1]=[str(obj),'-Wl,--wrap=enhanced_execute_next','-Wl,--wrap=enhanced_source_poll','-Wl,--wrap=enhanced_world_enabled','-Wl,--wrap=modern_world_cell_pixels','-Wl,--wrap=ProcCasteEvent']
    if observer:command+=['-Wl,--wrap=portable_test_diagnostics','-Wl,--wrap=portable_test_step_boundary']
    result=subprocess.run(command,cwd=build,capture_output=True,text=True,timeout=120)
    (out/'link.log').write_text(result.stdout+result.stderr)
    if result.returncode:raise RuntimeError(result.stderr[-3000:])
    for name in ('SDL3.dll','simant-build-id.txt'):shutil.copyfile(build/name,out/name)
    shutil.copytree(build/'runtime-bios-fonts',out/'runtime-bios-fonts')
    (out/'receipt.json').write_text(json.dumps(dict(command=command,probe_sha256=sha(source),executable_sha256=sha(exe)),indent=2)+'\n')
    return exe
