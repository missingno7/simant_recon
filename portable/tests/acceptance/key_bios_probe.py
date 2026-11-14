"""Measure US/CZ INT16 AH=01/00 words from physical scripted make/breaks.

The standalone GNU-as COM only polls BIOS and retains count/last word at 8000:0.
No game code or expected native state participates. Outputs stay under build/.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from dos.run import keyboard_runner
from tools.compiler import toolchain

ASM = '''.intel_syntax noprefix
.code16
.text
mov ax,0x8000
mov es,ax
xor ax,ax
mov es:[0],ax
mov es:[2],ax
mov es:[4],ax
mov ax,0x40
mov ds,ax
and byte ptr [0x17],0xdf
poll:
mov al,[0x17]
mov es:[4],al
mov ah,1
int 0x16
jz poll
xor ah,ah
int 0x16
mov es:[2],ax
mov bx,es:[0]
shl bx,1
mov es:[bx+0x100],ax
inc word ptr es:[0]
jmp poll
'''
KEYS = list('1234567890abcdefghijklmnopqrstuvwxyz') + '''minus equals lbracket
rbracket semicolon quote grave backslash comma period slash enter esc bspace
tab space home end up down left right pageup pagedown insert delete kp_5
f1 f2 f3 f4 f5 f6 f7 f8 f9 f10'''.split()


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--layout', choices=('us', 'cz243'), required=True)
    a = ap.parse_args()
    out = a.out.resolve()
    out.relative_to(ROOT/'build')
    out.mkdir(parents=True, exist_ok=False)
    source = out/'probe.s'
    source.write_text(ASM)
    subprocess.run(['C:/msys64/mingw64/bin/as.exe', '--32', str(source), '-o', str(out/'probe.o')], check=True)
    subprocess.run(['C:/msys64/mingw64/bin/objcopy.exe', '-O', 'binary', '-j', '.text', str(out/'probe.o'), str(out/'PROBE.COM')], check=True)
    cases = []; lines = []; t = 1000
    for mask in range(8):
        held = [key for bit, key in ((1,'lshift'),(2,'lctrl'),(4,'lalt')) if mask & bit]
        for key in KEYS:
            if mask & 6 == 6 and key == 'delete':
                continue  # Ctrl+Alt+Del reboots the emulator, not an INT16 word.
            index = len(cases)
            lines += [f'{t} keydown {k}' for k in held]
            lines += [f'{t+10} keydown {key}', f'{t+20} keyup {key}',
                      f'{t+30} dump 80000 1000 {out / (str(index)+".bin")}']
            lines += [f'{t+40} keyup {k}' for k in reversed(held)]
            lines += [f'{t+50} dump 80000 1000 {out / (str(index)+"-up.bin")}']
            cases.append(dict(key=key, modifiers=mask))
            t += 70
    lines += [f'{t+100} exit']
    (out/'INPUT.SCR').write_text('\n'.join(lines)+'\n')
    runner, pin = keyboard_runner(toolchain()['runners']['dosbox-x-acceptance'])
    conf = runner['conf']
    conf['dos']['keyboardlayout'] = a.layout
    conf['cpu']['cycles'] = 'fixed 10000'
    conf['dosbox'].update({'acceptance script':str(out/'INPUT.SCR'), 'acceptance log':str(out/'INPUT.LOG')})
    text = []
    for section, values in conf.items():
        text += ['['+section+']']+[k+'='+v for k,v in values.items()]
    text += ['[autoexec]',f'mount c "{out}"','c:','keyb > KEYBOARD.TXT','PROBE.COM','exit']
    (out/'dosbox.conf').write_text('\n'.join(text)+'\n')
    assert sha(Path(runner['path'])) == runner['sha256']
    command = [runner['path'],'-conf',str(out/'dosbox.conf'),'-fastlaunch','-exit','-nomenu']
    with (out/'host.log').open('w') as log:
        subprocess.run(command, cwd=out, env={**os.environ,'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'},
                       stdout=log,stderr=subprocess.STDOUT,timeout=180,check=True,
                       creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    count = 0
    for i, case in enumerate(cases):
        down = (out/(str(i)+'.bin')).read_bytes()
        up = (out/(str(i)+'-up.bin')).read_bytes()
        n, word, flags = struct.unpack('<HHH',down[:6])
        u, upword, upflags = struct.unpack('<HHH',up[:6])
        assert count <= n <= u < 1920, (i, case, count, n, u)
        words = lambda raw, a, b: list(struct.unpack('<'+'H'*(b-a),raw[0x100+2*a:0x100+2*b]))
        case.update(words=words(down,count,n), release_words=words(up,n,u), flags=flags & 255)
        count = u
    receipt = dict(layout=a.layout,runner=runner,environment_pin=pin,command=command,cases=cases,
                   inputs={str(p):sha(p) for p in (source, out/'PROBE.COM',out/'INPUT.SCR',out/'dosbox.conf',Path(__file__))},
                   outputs={p.name:sha(p) for p in out.glob('*.bin')},
                   host_log_sha256=sha(out/'host.log'), query=(out/'KEYBOARD.TXT').read_text())
    (out/'result.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(a.layout, len(cases), 'cases', count, 'BIOS words', flush=True)


if __name__ == '__main__':
    main()
