"""Genuine source-built CRT all the way through main under pinned DOSBox-X."""
import json
import os
import subprocess
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'tools'))
import compiler
import source_only_dos as dos
denied=dos.install_input_guard()
tc=compiler.toolchain(); runner=tc['runners']['dosbox-x']
cases=[]
for profile in ('rtlink400','rtlink610'):
    for name, expected in (('bss_two',0),('bss_shift',111),('file_seed',136)):
        d=OUT/profile/name
        lines=['@echo off','PROBE.EXE > NUL',f'if errorlevel {expected+1} goto bad']
        if expected:lines += [f'if not errorlevel {expected} goto bad']
        lines += ['echo PASS > FULLRUN.LOG','goto done',':bad','echo FAIL > FULLRUN.LOG',':done']
        (d/'FULLRUN.BAT').write_bytes(('\r\n'.join(lines)+'\r\n').encode('ascii'))
        config=[]
        for section,settings in runner['conf'].items():config += ['['+section+']']+[f'{k}={v}' for k,v in settings.items()]
        config += ['[autoexec]',f'mount c "{d}"','c:','call FULLRUN.BAT','exit']
        conf=d/'fullrun.conf';conf.write_text('\n'.join(config)+'\n')
        env=os.environ.copy();env.update(SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy')
        run=subprocess.run([runner['path'],'-conf',str(conf),'-fastlaunch','-exit','-nomenu'],cwd=d,env=env,
            stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=60,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0),check=True)
        actual=(d/'FULLRUN.LOG').read_text().strip()
        assert actual=='PASS', (profile,name,actual)
        cases.append(dict(linker=profile,case=name,expected_main_return=expected,result=actual))
        print(profile,name,actual,flush=True)
assert not denied
(OUT/'full-dos-execution.json').write_text(json.dumps(dict(schema='dos-tail-stock-crt-full-fixtures-v36',
    root_reviewed=False,admitted=False,original_build_bytes=0,denied_original_reads=denied,
    cases=cases,scope='Genuine stock CRT, cinit and source main executed under pinned DOSBox-X; prior-memory poisons are tested separately in the bounded VM.'),indent=2)+'\n')
