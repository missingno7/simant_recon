"""Replay only pinned source-built fixture images in this worker's own directories."""
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
PACKET = ROOT / 'build/workers/dos_tail_clear_v36'
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / 'tools'))
import source_only_dos as dos
denied = dos.install_input_guard()
tc = json.loads((ROOT / 'layout/toolchain.json').read_bytes())
runner = tc['runners']['dosbox-x']
assert hashlib.sha256(Path(runner['path']).read_bytes()).hexdigest() == runner['sha256']
vm = json.loads((PACKET / 'stock-crt-controls.json').read_bytes())
rows = []
for case in vm['cases']:
    name, profile = case['name'], case['linker']
    directory = OUT / 'full-dos-replay' / profile / name
    directory.mkdir(parents=True, exist_ok=False)
    source = Path(case['directory'])
    raw = (source / 'PROBE.EXE').read_bytes()
    assert hashlib.sha256(raw).hexdigest() != dos.ORIGINAL_SHA
    shutil.copyfile(source / 'PROBE.EXE', directory / 'PROBE.EXE')
    shutil.copyfile(source / 'FULLRUN.BAT', directory / 'FULLRUN.BAT')
    config = []
    for section,settings in runner['conf'].items():
        config += ['['+section+']']+[f'{k}={v}' for k,v in settings.items()]
    config += ['[autoexec]', f'mount c "{directory}"', 'c:', 'call FULLRUN.BAT', 'exit']
    conf = directory / 'fullrun.conf'
    conf.write_text('\n'.join(config)+'\n', encoding='ascii')
    env=os.environ.copy()
    env.update(SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy')
    subprocess.run([runner['path'],'-conf',str(conf),'-fastlaunch','-exit','-nomenu'],cwd=directory,env=env,
        stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=60,
        creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0),check=True)
    actual=(directory/'FULLRUN.LOG').read_text().strip()
    assert actual=='PASS'
    row=dict(name=name,linker=profile,result=actual,executable_sha256=hashlib.sha256(raw).hexdigest())
    rows.append(row)
    print(profile,name,actual,flush=True)
assert not denied
(OUT/'full-dos-replay.json').write_text(json.dumps(dict(root_reviewed=False,admitted=False,
    original_build_bytes=0,denied_original_reads=denied,runner_sha256=runner['sha256'],cases=rows),indent=2)+'\n')
