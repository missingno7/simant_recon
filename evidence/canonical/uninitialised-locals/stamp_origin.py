"""Reproduce startup register-save residue in the pinned DOS reference runtime.
All executable/memory output stays under --out. Only the small evidence receipt
is checked in; no executable bytes are used by native runtime code.
"""
from pathlib import Path
import argparse,hashlib,json,os,subprocess,sys
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
from portable.tests.acceptance.capture_dos_steps import capture_addresses
from portable.tests.acceptance.state_schema import memory_base

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def run(target,name,out,extra=None,memsize=None):
    work=out/name; script=out/(name+'.scr');script.write_text('500 dump 0 100000 binding\n1000 exit\n')
    cmd=[sys.executable,str(ROOT/'dos/run.py'),'--original' if target=='original' else '--build-report']
    if target!='original':cmd.append(str(ROOT/'build/current/dos/build-report.json'))
    cmd+=['--out',str(work),'--seconds','15','--fixed-clock','--input-script',str(script),'--prepare-only']
    p=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,timeout=40)
    if p.returncode:raise RuntimeError(p.stdout+p.stderr)
    if extra:
        p=work/'RUN.BAT';s=p.read_text();s=s.replace('SIMANT.EXE  > GAME.LOG','set SIMANT_UNINIT='+extra+'\nSIMANT.EXE  > GAME.LOG');p.write_text(s)
    if memsize:
        p=work/'dosbox.conf';p.write_text(p.read_text().replace('memsize=16','memsize='+str(memsize)))
    runner=json.loads((ROOT/'layout/toolchain.json').read_text())['runners']['dosbox-x-observation']
    def execute():
        p=subprocess.run([runner['path'],'-conf',str(work/'dosbox.conf'),'-fastlaunch','-exit','-nomenu'],cwd=work,env={**os.environ,'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'},capture_output=True,timeout=30)
        if p.returncode:raise RuntimeError('emulator failed: '+str(p.returncode))
    execute()
    exe=ROOT/'assets/SIMANT.EXE' if target=='original' else ROOT/json.loads((ROOT/'build/current/dos/build-report.json').read_text())['link']['candidate_executable']['path']
    addresses=capture_addresses(target=='original',exe);base=memory_base((work/'dump-binding').read_bytes(),addresses)
    # Original CRT __cinit 29F4:011C; canonical linked CRT 29F7:0112.
    # Both have the same +A1h INT 21h in their descriptor loop.
    cinit=(0x29f4*16+0x11c) if target=='original' else (0x29f7*16+0x112)
    before=base+cinit+0xa1; main=base+addresses['main']
    (work/'INPUT.SCR').write_text(f'0 on_exec lin {before:X} 5 dump 0 100000 {work}/exec-before\n0 on_exec lin {before+2:X} 5 dump 0 100000 {work}/exec-after\n0 on_exec lin {main:X} 1 dump 0 100000 {work}/exec-main\n1000 exit\n')
    execute()
    frames={}
    for label,hit in [('before',5),('after',5),('main',1)]:
        p=work/f'exec-{label}.{hit}.bin';reg=json.loads(p.with_suffix('.json').read_text())['registers'];m=p.read_bytes()
        ss=int(reg['ss'],16)*16;sp=int(reg['esp'],16)&65535
        # Before INT SP is the __cinit frame, then hardware pushes six bytes.
        # DOS saves BX at (SP-6)-16 and CX at (SP-6)-14.
        stamp=ss+sp-22 if label!='main' else ss+sp-12
        frames[label]=dict(path=str(p.relative_to(ROOT)),sha256=sha(p),registers=reg,stamp_linear=stamp,stamp_bytes=m[stamp:stamp+4].hex())
    assert frames['after']['stamp_bytes']==frames['main']['stamp_bytes']
    reg=frames['main']['registers'];m=(work/'exec-main.1.bin').read_bytes();ds=int(reg['ds'],16)*16
    # CRT global offsets differ by -20h between linked runtimes.
    psp=int.from_bytes(m[ds+(0x7740 if target=='original' else 0x7720):ds+(0x7742 if target=='original' else 0x7722)],'little')
    env=int.from_bytes(m[psp*16+0x2c:psp*16+0x2e],'little')
    strings=m[env*16:].split(b'\0\0',1)[0].split(b'\0')
    value=int(frames['main']['stamp_bytes'],16) if False else int.from_bytes(bytes.fromhex(frames['main']['stamp_bytes']),'little',signed=True)
    return dict(target=target,variant=name,executable_sha256=sha(exe),runtime_base=base,environment=[s.decode('ascii') for s in strings],stamp_signed=value,frames=frames,run_bat_sha256=sha(work/'RUN.BAT'),config_sha256=sha(work/'dosbox.conf'),runner_sha256=sha(Path(runner['path'])))

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);ap.add_argument('--write',action='store_true');a=ap.parse_args();out=a.out.resolve();out.mkdir(parents=True,exist_ok=False)
    rows=[]
    for t,n,e,m in [('original','original-reference',None,None),('canonical','canonical-reference',None,None),('original','original-extra-env','abc',None),('original','original-memory-8mb',None,8)]:
        row=run(t,n,out,e,m);rows.append(row);print(n,row['stamp_signed'],flush=True)
    result=dict(schema='dos-startup-uninitialised-stamp-v1',source='src/startup/main.c',source_sha256=sha(ROOT/'src/startup/main.c'),reference_value=0x7fe20000,observations=rows)
    p=out/'stamp-origin.json';p.write_text(json.dumps(result,indent=2)+'\n')
    if a.write:(Path(__file__).with_name('stamp-origin.json')).write_bytes(p.read_bytes())
if __name__=='__main__':main()
