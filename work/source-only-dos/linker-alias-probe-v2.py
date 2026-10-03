"""Source-only RTLink symbol-alias contract: assemble, link and execute controls.

Small test-owned records only. Never a game image, game stub, or DOS baseline.
"""
from pathlib import Path
import json
import os
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
import compiler
import source_only_dos as dos
import dos_source_bindings as bindings

OWNER = """_DATA segment word public 'DATA'
public _owner
db 30h dup (0)
_owner dw 1234h, 5 dup (0), 5678h, 13 dup (0), 9ABCh
_DATA ends
FARDATA segment para public 'FAR_DATA'
public _farowner
db 20h dup (0)
_farowner dw 3456h, 19 dup (0), 789Ah
FARDATA ends
end
"""

CONSUMER = """_DATA segment word public 'DATA'
extrn _owner:word, _same:word, _interior:word
passed db 'PASS',13,10,'$'
failed db 'FAIL',13,10,'$'
_DATA ends
DGROUP group _DATA
extrn _farowner:word, _farsame:word, _farinterior:word
STACKSEG segment para stack 'STACK'
db 100h dup (0)
STACKSEG ends
TEST_TEXT segment word public 'CODE'
assume cs:TEST_TEXT, ds:DGROUP
start:
mov ax,DGROUP
mov ds,ax
mov ax,OFFSET DGROUP:_owner
cmp ax,OFFSET DGROUP:_same
jne bad
add ax,12
cmp ax,OFFSET DGROUP:_interior
jne bad
cmp word ptr _interior,5678h
jne bad
mov ax,SEG _farowner
cmp ax,SEG _farsame
jne bad
cmp ax,SEG _farinterior
jne bad
mov es,ax
mov ax,OFFSET _farowner
cmp ax,OFFSET _farsame
jne bad
add ax,40
cmp ax,OFFSET _farinterior
jne bad
mov bx,OFFSET _farinterior
cmp word ptr es:[bx],789Ah
jne bad
mov dx,OFFSET DGROUP:passed
mov ah,9
int 21h
mov ax,4C00h
int 21h
bad:
mov dx,OFFSET DGROUP:failed
mov ah,9
int 21h
mov ax,4C01h
int 21h
TEST_TEXT ends
end start
"""


def main():
    out = ROOT / 'build/workers/dos_linker_aliases_v2'
    out.mkdir(parents=True, exist_ok=True)
    denied = dos.install_input_guard()
    inputs = [dos.pin(Path(__file__))[1], dos.pin(ROOT / 'layout/toolchain.json')[1]]
    objects = {}
    for name, source in (('OWNER', OWNER), ('USE', CONSUMER)):
        path = out / (name + '.asm')
        path.write_text(source, encoding='ascii')
        result = compiler.assemble(source, 'masm510', ['/Mx'], basename=name)
        if not result.ok:
            raise ValueError(result.log)
        objects[name] = result.obj
        inputs.append(dos.pin(path)[1])
    tc = compiler.toolchain()
    assembler = compiler.verify_profile('masm510')
    for rel, digest in assembler['files'].items():
        inputs.append(dos.pin(Path(assembler['directory']) / rel, digest)[1])
    assembler_runner = tc['runner']
    inputs.append(dos.pin(Path(assembler_runner['path']), assembler_runner['sha256'])[1])
    runner = tc['runners']['dosbox-x']
    inputs.append(dos.pin(Path(runner['path']), runner['sha256'])[1])
    rows = []
    for profile in ('rtlink400', 'rtlink610'):
        tool = tc['linkers'][profile]
        for rel, digest in tool['files'].items():
            inputs.append(dos.pin(Path(tool['directory']) / rel, digest)[1])
        tool_dir = compiler.pinned_tree(tool)
        for case, near_delta, far_delta, expected in (
                ('correct', 12, 40, 'PASS'), ('wrong_near', 14, 40, 'FAIL'),
                ('wrong_far', 12, 42, 'FAIL'), ('unsuffixed_near', '12', 40, 'FAIL'),
                ('unsuffixed_far', 12, '40', 'FAIL')):
            directory = out / profile / case
            directory.mkdir(parents=True, exist_ok=True)
            # Remove only this probe's previous output, so link failure cannot
            # execute a stale successful control. No recursive cleanup.
            for name in ('PROBE.EXE', 'PROBE.MAP', 'RUN.LOG', 'LINK.LOG'):
                (directory / name).unlink(missing_ok=True)
            for name, raw in objects.items():
                (directory / (name + '.OBJ')).write_bytes(raw)
            script = ('OUTPUT PROBE\r\nMAP = PROBE S,N,A,L\r\nNODEFLIB\r\n'
                      'FILE OWNER, USE\r\nDEFINE _same = _owner\r\n'
                      f'DEFINE _interior = _owner{bindings.rtlink_alias_delta(near_delta) if isinstance(near_delta, int) else " + " + near_delta}\r\n'
                      'DEFINE _farsame = _farowner\r\n'
                      f'DEFINE _farinterior = _farowner{bindings.rtlink_alias_delta(far_delta) if isinstance(far_delta, int) else " + " + far_delta}\r\n')
            (directory / 'PROBE.LNK').write_bytes(script.encode('ascii'))
            (directory / 'RTLINK.CFG').write_bytes(b'SYNTAX = FREEFORMAT\r\n')
            (directory / 'RUN.BAT').write_bytes((
                f'@echo off\r\nD:\\{tool["executable"]} @PROBE.LNK < NUL > LINK.LOG\r\n'
                'PROBE.EXE > RUN.LOG\r\n').encode('ascii'))
            config = []
            for section, settings in runner['conf'].items():
                config.append('[' + section + ']')
                config += [f'{k}={v}' for k, v in settings.items()]
            config += ['[autoexec]', f'mount c "{directory}"',
                       f'mount d "{tool_dir}" -ro', 'c:', 'call RUN.BAT', 'exit']
            conf = directory / 'dosbox.conf'
            conf.write_text('\n'.join(config)+'\n')
            env = os.environ.copy()
            env.update(SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy')
            run = subprocess.run([runner['path'], '-conf', str(conf), '-fastlaunch', '-exit', '-nomenu'],
                cwd=directory, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                timeout=60, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
            log = (directory / 'RUN.LOG').read_text(encoding='latin1').strip()
            link_log = (directory / 'LINK.LOG').read_text(encoding='latin1')
            row = {'linker': profile, 'case': case, 'near_delta': near_delta,
                   'far_delta': far_delta, 'expected': expected,
                   'actual': log, 'process_exit': run.returncode,
                   'passed': log == expected and run.returncode == 0,
                   'files': [dos.pin(p)[1] for p in directory.iterdir() if p.is_file()]}
            rows.append(row)
            print(profile, case, log, link_log[-500:] if log != expected else '', flush=True)
    report = {'schema': 'simant-dos-linker-alias-probe-v2', 'inputs': inputs,
              'cases': rows, 'denied_oracle_reads': denied,
              'all_checks_pass': all(r['passed'] for r in rows) and not denied,
              'scope': 'Test-owned near/far record aliases only; no game link or runtime proof.'}
    (out / 'report.json').write_text(json.dumps(report, indent=2)+'\n')
    return 0 if report['all_checks_pass'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
