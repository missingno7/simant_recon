"""Rebuild the canonical DOS directory helper and test its real DOSBox path domain.

This is a source-built CRT fixture, not a SimAnt game or owner admission. All
outputs must be fresh and strictly under build/. The canonical assembly remains
unchanged and the historical runtime/linker inputs are hash checked.
"""
from pathlib import Path
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys

ROOT = next(p for p in Path(__file__).resolve().parents if (p/'src/program.json').is_file())
sys.path.insert(0, str(ROOT/'tools'))
import compiler
HERE = Path(__file__).resolve().parent
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--out', required=True, type=Path)
args = parser.parse_args()
OUT = (ROOT/args.out).resolve()
if not OUT.is_relative_to((ROOT/'build').resolve()) or OUT.exists():
    raise ValueError('output must be fresh and strictly under build/')
OUT.mkdir(parents=True)
compiler.WORK = OUT/'cc'
inputs = {}
for name, source, profile, flags in [('PROBE', HERE/'fixture.c', 'msc600ax', ['/AL','/Os','/Gs']),
                                     ('GOLDMAN', ROOT/'src/root/m1F66.asm', 'masm510', ['/Mx'])]:
    inputs[str(source.relative_to(ROOT))] = hashlib.sha256(source.read_bytes()).hexdigest()
    fn = compiler.assemble if profile.startswith('masm') else compiler.compile_c
    result = fn(source.read_text(), profile, flags, basename=name, keep=True)
    assert result.ok, result.log
    (OUT/(name+'.OBJ')).write_bytes(result.obj)
tc = compiler.toolchain()
program = json.loads((ROOT/'src/program.json').read_text())
for lib in program['dos']['runtime_libraries']:
    raw = Path(lib['path']).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == lib['sha256']
    (OUT/lib['name'].upper()).write_bytes(raw)
    inputs[lib['path']] = lib['sha256']
tool = tc['linkers']['rtlink400']
directory = compiler.pinned_tree(tool)
runner = tc['runners']['dosbox-x']
assert hashlib.sha256(Path(runner['path']).read_bytes()).hexdigest() == runner['sha256']
(OUT/'RTLINK.CFG').write_text('SYNTAX = FREEFORMAT\n')
(OUT/'PROBE.LNK').write_text('OUTPUT PROBE\nMAP = PROBE S,N,A,L\nNODEFLIB\nLIBRARY LLIBCR, LIBH\nFILE PROBE.OBJ, GOLDMAN.OBJ\n')
(OUT/'RUN.BAT').write_bytes(b'@echo off\r\nD:\\RTLINK.EXE @PROBE.LNK < NUL > LINK.LOG\r\nPROBE.EXE > RUN.LOG\r\n')
deep = OUT
for i in range(7):
    deep /= 'AAAAAAAA'
    deep.mkdir()
(deep/'A').mkdir()
lines = []
for section, settings in runner['conf'].items():
    lines.append('['+section+']')
    lines.extend(key+'='+value for key,value in settings.items())
lines.extend(['[autoexec]', f'mount c "{OUT}"', f'mount d "{directory}" -ro',
              'c:', 'set LIB=C:\\;D:\\', 'call RUN.BAT', 'exit'])
(OUT/'dosbox.conf').write_text('\n'.join(lines)+'\n')
env=os.environ.copy()
env.update({'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'})
result = subprocess.run([runner['path'],'-conf',str(OUT/'dosbox.conf'),'-fastlaunch','-exit','-nomenu'],
                        cwd=OUT,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=90,
                        creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
(OUT/'DOSBOX.LOG').write_bytes(result.stdout)
log = (OUT/'RUN.LOG').read_text()
assert (OUT/'PROBE.EXE').is_file(), (OUT/'LINK.LOG').read_text()
link_log = (OUT/'LINK.LOG').read_text()
assert not re.search(r'\b(?:warning|error|fatal|WRT\d+|undefined|unresolved)\b', link_log, re.I), link_log
assert 'depth=7 length=65 nul=65' in log
assert 'after-slash=66 requires=67 fits67=1' in log
assert 'depth=8 length=67 nul=67' in log
assert 'after-slash=68 requires=69 fits67=0' in log
for path, expected in inputs.items():
    assert hashlib.sha256(Path(path if Path(path).is_absolute() else ROOT/path).read_bytes()).hexdigest() == expected
print(log)
(OUT/'receipt.json').write_text(json.dumps({
    'schema':'simant-filename-domain-boundary-v1',
    'scope':'DOSBox-X AH47 in isolated linked canonical assembly helper; no game execution',
    'status':'POSITIVE_AND_NEGATIVE_CONFIRMED',
    'owner_admitted':False,
    'replay_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    'inputs':inputs,
    'profiles':{'helper':'msc600ax /AL /Os /Gs', 'goldman':'masm510 /Mx', 'linker':'rtlink400'},
    'dosbox_sha256':runner['sha256'],
    'linker_files':tool['files'],
    'output_identities':{name:hashlib.sha256((OUT/name).read_bytes()).hexdigest() for name in
                         ('PROBE.OBJ','GOLDMAN.OBJ','PROBE.EXE','PROBE.MAP','LINK.LOG','RUN.LOG')},
    'run_log':log},indent=2)+'\n')
