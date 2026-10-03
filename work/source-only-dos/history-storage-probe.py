"""Source-only history communal experiments; no game executable or runtime claim."""
from pathlib import Path
import json
import os
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
import compiler
import dos_source_bindings as bindings
import source_only_dos as dos
from omf import OmfReader

SUFFIXES = ('0516', '05A0', '0626', '06AE', '073C', '07CE', '0856', '08F0', '0970', '0A0A')
CONSUMER = """_DATA segment word public 'DATA'
passed db 'PASS',13,10,'$'
failed db 'FAIL',13,10,'$'
_DATA ends
DGROUP group _DATA
extrn _history:word
STACKSEG segment para stack 'STACK'
db 100h dup (0)
STACKSEG ends
TEST_TEXT segment word public 'CODE'
assume cs:TEST_TEXT, ds:DGROUP
start:
mov ax,DGROUP
mov ds,ax
mov ax,SEG _history
mov es,ax
mov bx,OFFSET _history
mov di,bx
xor ax,ax
mov cx,64
cld
repe scasw
jne bad
mov word ptr es:[bx],1234h
mov word ptr es:[bx+126],5678h
cmp word ptr es:[bx],1234h
jne bad
cmp word ptr es:[bx+126],5678h
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
CRT_CONSUMER = """extern int far history[64];
extern int far puts(char far *text);
int main(void)
{
    int i;
    for (i = 0; i < 64; i++)
        if (history[i] != 0) {
            puts("FAIL");
            return 1;
        }
    history[0] = 0x1234;
    history[63] = 0x5678;
    if (history[0] != 0x1234 || history[63] != 0x5678) {
        puts("FAIL");
        return 1;
    }
    puts("PASS");
    return 0;
}
"""
BYTE_CONSUMER = """extern unsigned char far history[];
extern int far probe(void);
extern int far puts(char far *text);
struct SaveRec { int size; int count; void far *data; };
struct SaveRec far saved = {2, 64, (void far *)&history};
int far * far views[2] = {history, history};
int main(void)
{
    int i;
    unsigned char far *bytes;
    bytes = saved.data;
    if (saved.size * saved.count != 128 || bytes != history || views[0] != views[1]) {
        puts("FAIL");
        return 1;
    }
    for (i = 0; i < 64; i++)
        if (views[0][i] != 0) {
            puts("FAIL");
            return 1;
        }
    views[0][0] = 0x1234;
    views[1][63] = 0x5678;
    if (bytes[0] != 0x34 || bytes[1] != 0x12 ||
        bytes[126] != 0x78 || bytes[127] != 0x56 || probe() != 0x1234) {
        puts("FAIL");
        return 1;
    }
    puts("PASS");
    return 0;
}
"""


def main():
    out = ROOT / 'build/workers/dos_history_storage'
    out.mkdir(parents=True, exist_ok=True)
    denied = dos.install_input_guard()
    inputs = [dos.pin(Path(__file__))[1], dos.pin(ROOT / 'tools/dos_source_bindings.py')[1],
              dos.pin(ROOT / 'layout/toolchain.json')[1]]
    tc = compiler.toolchain()
    objects = {}
    sources = [('USE', CONSUMER, 'masm510', ['/Mx']),
               ('ZERO', 'int far history[64];\n', 'msc600ax', ['/AL', '/Os', '/Zi']),
               ('ZEROOVL', 'int far history[64];\nint far probe(void) { return history[0]; }\n',
                'msc600ax', ['/AL', '/Os', '/Zi', '/Gs']),
               ('BADOVL', 'int far history[64] = {1};\nint far probe(void) { return history[0]; }\n',
                'msc600ax', ['/AL', '/Os', '/Zi', '/Gs']),
               ('CRT', CRT_CONSUMER, 'msc600ax', ['/AL', '/Os', '/Zi']),
               ('BYTE', BYTE_CONSUMER, 'msc600ax', ['/AL', '/Os', '/Zi']),
               ('NONZERO', 'int far history[64] = {1};\n', 'msc600ax', ['/AL', '/Os', '/Zi'])]
    for name, source, profile, flags in sources:
        suffix = '.asm' if profile == 'masm510' else '.c'
        path = out / (name + suffix)
        path.write_bytes(source.encode('ascii'))
        run = compiler.assemble if suffix == '.asm' else compiler.compile_c
        result = run(source, profile, flags, basename=name)
        if not result.ok:
            raise ValueError(result.log)
        objects[name] = result.obj
        inputs.append(dos.pin(path)[1])
        tool = compiler.verify_profile(profile)
        inputs += [dos.pin(Path(tool['directory']) / rel, digest)[1] for rel, digest in tool['files'].items()]
    zero = OmfReader(communals=True).read(objects['ZERO'])
    expected = [{'name': '_history', 'kind': 'far', 'count': 64, 'element_size': 2, 'length': 128}]
    if [bindings.communal_key(c) for c in zero.communals] != [bindings.communal_key(c) for c in expected]:
        raise ValueError('fixture did not produce the intended far communal')
    runner = tc['runners']['dosbox-x']
    inputs += [dos.pin(Path(runner['path']), runner['sha256'])[1],
               dos.pin(Path(tc['runner']['path']), tc['runner']['sha256'])[1]]
    cases = []
    manifest_raw, manifest_pin = dos.pin(ROOT / 'layout/manifest.json')
    inputs.append(manifest_pin)
    runtimes = list(json.loads(manifest_raw)['runtime']['libraries'].values())
    inputs += [dos.pin(Path(row['path']), row['sha256'])[1] for row in runtimes]
    for profile in ('rtlink400', 'rtlink610'):
        tool = tc['linkers'][profile]
        inputs += [dos.pin(Path(tool['directory']) / rel, digest)[1] for rel, digest in tool['files'].items()]
        tool_dir = compiler.pinned_tree(tool)
        for case, owner, expected_log in (('zero_communal', 'ZERO', 'PASS'),
                                          ('overlay_without_crt', 'ZEROOVL', 'PASS'),
                                          ('nonzero_initialized_contrast', 'NONZERO', 'FAIL'),
                                          ('crt_overlay_zero_communal', 'ZEROOVL', 'PASS'),
                                          ('crt_overlay_nonzero_contrast', 'BADOVL', 'FAIL'),
                                          ('crt_byte_and_word_views', 'ZEROOVL', 'PASS'),
                                          ('crt_byte_and_word_nonzero_contrast', 'BADOVL', 'FAIL')):
            directory = out / profile / case
            directory.mkdir(parents=True, exist_ok=True)
            for name in ('PROBE.EXE', 'PROBE.MAP', 'RUN.LOG', 'LINK.LOG'):
                (directory / name).unlink(missing_ok=True)
            startup = 'CRT' if case.startswith('crt_') else 'USE'
            if case.startswith('crt_byte_and_word'):
                startup = 'BYTE'
            for name in (startup, owner):
                (directory / (name + '.OBJ')).write_bytes(objects[name])
            files = (f'FILE {startup}\r\nBEGINAREA\r\nSECTION FILE {owner}\r\nENDAREA\r\n'
                     if owner in ('ZEROOVL', 'BADOVL') else 'FILE ' + owner + ', USE\r\n')
            if startup in ('CRT', 'BYTE'):
                for row in runtimes:
                    shutil.copyfile(row['path'], directory / Path(row['path']).name.upper())
                files = 'LIBRARY LLIBCR, LIBH\r\n' + files
            (directory / 'PROBE.LNK').write_bytes((
                'OUTPUT PROBE\r\nMAP = PROBE S,N,A,L\r\nNODEFLIB\r\n' + files).encode('ascii'))
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
            conf.write_text('\n'.join(config) + '\n')
            env = os.environ.copy()
            env.update(SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy')
            run = subprocess.run([runner['path'], '-conf', str(conf), '-fastlaunch', '-exit', '-nomenu'],
                cwd=directory, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                timeout=60, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
            actual = (directory / 'RUN.LOG').read_text(encoding='latin1').strip()
            cases.append({'linker': profile, 'case': case, 'startup': startup,
                'expected': expected_log, 'actual': actual,
                'emulator_exit': run.returncode, 'passed': actual == expected_log and run.returncode == 0,
                'files': [dos.pin(p)[1] for p in sorted(directory.iterdir()) if p.is_file()]})
            print(profile, case, actual, flush=True)
    required = [r for r in cases if r['case'] != 'overlay_without_crt']
    report = {'schema': 'simant-dos-history-storage-probe-v1', 'inputs': inputs,
              'fixture_communals': zero.communals, 'cases': cases, 'denied_oracle_reads': denied,
              'all_required_checks_pass': all(r['passed'] for r in required) and not denied,
              'counterexamples': [r for r in cases if r['case'] == 'overlay_without_crt'],
              'startup_contract': 'Overlay data allocation is established only with the pinned MSC '
                                  'runtime startup. The bare ASM entry fails under RTLink 4.00; '
                                  'its RTLink 6.10 success cannot stand in for that contract.',
              'scope': 'Test-owned far communal allocation, zero-fill, first/last word access, '
                       'SaveRec byte-address and initialized word-pointer views, and overlay owner calls; '
                       'not a game link, original object ownership proof or game runtime comparison.'}
    (out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    return 0 if report['all_required_checks_pass'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
