"""Where does a linker put MEMHOOK_TEXT (root:2CFB) relative to the runtime _TEXT / EMULATOR_TEXT?

    python work/align/exp2.py

Original: ... last game code (29F0) | _TEXT (runtime, from 29F4C) | EMULATOR_TEXT (crt0dat, 2CFB0) |
MEMHOOK_TEXT (2CFB2) | paragraph fill | RTLink manager (2CFF0).
A.C stands for the game objects (its own A_TEXT, calls the hooks), MH.ASM is the hook object
(m2CFB.asm shape).  Each variant is linked with MS LINK 5.10 and RTLink/Plus 6.10 (one DOSBox-X run).

  M1_code      MH class 'CODE', listed as an object after A             (current source)
  M2_class     MH class 'MEMHOOK' (not a CODE class), listed after A
  M3_libafter  MH class 'CODE' in MH.LIB, searched after LLIBCR,LIBH
  M3b_libfirst MH class 'CODE' in MH.LIB, searched before LLIBCR
  M4_fileafter MH class 'CODE', RTLink script: FILE A / LIB ... / FILE MH (RTLink only)
"""
import sys, json, re, shutil, subprocess, os, hashlib
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools'))
import compiler  # noqa

HERE = Path(__file__).resolve().parent
OUT = HERE / 'exp2'
MSBIN = Path('C:/tools/msc-6.00/BIN')
RTL = Path('C:/tools/rtlink-plus-6.10/installed')
PINS = {RTL / 'RTL-REAL.EXE': '228c5d429438ea32ee21dd02c65b7f8e198715b3fa957be9da328f9857482773',
        MSBIN / 'link.exe': '163d8b86c18b93ccae9b2380d850cd42a9a5e1fd89a163b16170979afbbabb07'}

A = ("extern int far jt_a(void);\nint far target(void)\n{\n    return 1;\n}\n"
     "int main(void)\n{\n    return jt_a();\n}\n")
MH = """        extrn   _target:far
MEMHOOK_TEXT segment word public '{cls}'
        assume  cs:MEMHOOK_TEXT
        public  _jt_a
_jt_a:  jmp     _target
MEMHOOK_TEXT ends
        end
"""
VAR = {
    'M1CODE': dict(cls='CODE', ms='A+MH,MS.EXE,MS.MAP,LLIBCR+LIBH', rt='FI A,MH LIB LLIBCR,LIBH'),
    'M2CLASS': dict(cls='MEMHOOK', ms='A+MH,MS.EXE,MS.MAP,LLIBCR+LIBH', rt='FI A,MH LIB LLIBCR,LIBH'),
    'M3LIBAFT': dict(cls='CODE', lib=True, ms='A,MS.EXE,MS.MAP,LLIBCR+LIBH+MH', rt='FI A LIB LLIBCR,LIBH,MH'),
    'M3LIBFST': dict(cls='CODE', lib=True, ms='A,MS.EXE,MS.MAP,MH+LLIBCR+LIBH', rt='FI A LIB MH,LLIBCR,LIBH'),
    'M4FILEAF': dict(cls='CODE', ms=None, rt='FI A LIB LLIBCR,LIBH FI MH'),
}


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def segs(mapfile: Path):
    if not mapfile.exists():
        return None
    out = []
    for line in mapfile.read_text(errors='replace').splitlines():
        m = re.match(r'\s*([0-9A-F]{5})H\s+([0-9A-F]{5})H\s+([0-9A-F]{5})H\s+(\S+)\s+(\S+)', line)
        if m and 'TEXT' in m.group(4) or (m and m.group(5).startswith('$$')):
            out.append(f'{m.group(1)} {m.group(3)} {m.group(4)} {m.group(5)}')
    return out


def order(sl):
    if not sl:
        return None
    names = [s.split()[2] for s in sl]
    want = ['_TEXT', 'EMULATOR_TEXT', 'MEMHOOK_TEXT']
    if not all(w in names for w in want):
        return 'missing'
    i = [names.index(w) for w in want]
    return 'AFTER_RUNTIME (original)' if i[2] > i[1] > i[0] else ('BEFORE_TEXT' if i[2] < i[0] else 'OTHER')


def main():
    for p, h in PINS.items():
        assert sha(p) == h, p
    libs = json.loads((ROOT / 'layout/manifest.json').read_text())['runtime']['libraries']
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    bat = ['@echo off']
    for v, d in VAR.items():
        vd = OUT / v
        vd.mkdir()
        r = compiler.compile_c(A, 'msc600ax', ['/AL', '/Os', '/Gs'], basename='A')
        assert r.ok, r.log
        (vd / 'A.OBJ').write_bytes(r.obj)
        r = compiler.assemble(MH.format(cls=d['cls']), 'masm510', ['/Mx'], basename='MH')
        assert r.ok, r.log
        (vd / 'MH.OBJ').write_bytes(r.obj)
        for lib in ('llibcr.lib', 'libh.lib'):
            assert sha(libs[lib]['path']) == libs[lib]['sha256']
            shutil.copyfile(libs[lib]['path'], vd / lib.upper())
        bat.append(f'cd \\{v}')
        if d.get('lib'):
            bat.append('E:\\LIB.EXE MH.LIB +MH.OBJ; > LIB.LOG')
            (vd / 'MH.OBJ').rename(vd / 'MHX.OBJ')
            bat[-1] = 'E:\\LIB.EXE MH.LIB +MHX.OBJ; > LIB.LOG'
        if d['ms']:
            bat.append(f'E:\\LINK.EXE /NOD/MAP/NOE {d["ms"]}; > MS.LOG')
        bat.append(f'D:\\RTL-REAL.EXE {d["rt"]} NODEFLIB OUTPUT RT MAP = RT > RT.LOG')
    (OUT / 'RUN.BAT').write_bytes(('\r\n'.join(bat) + '\r\n').encode('ascii'))
    runner = compiler.toolchain()['runners']['dosbox-x']
    conf = []
    for sec, kv in runner['conf'].items():
        conf.append(f'[{sec}]')
        conf += [f'{k}={v}' for k, v in kv.items()]
    conf += ['[autoexec]', f'mount c "{OUT.resolve()}"', f'mount d "{RTL}" -ro', f'mount e "{MSBIN}" -ro', 'c:',
             'call RUN.BAT', 'exit']
    (OUT / 'dosbox.conf').write_text('\n'.join(conf) + '\n')
    env = os.environ.copy(); env.update(SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy')
    p = subprocess.Popen([runner['path'], '-conf', str(OUT / 'dosbox.conf'), '-fastlaunch', '-exit', '-nomenu'],
                         cwd=OUT, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        p.wait(timeout=300)
    except subprocess.TimeoutExpired:
        p.kill(); p.wait()          # our own DOSBox instance only
    res = {}
    for v, d in VAR.items():
        vd = OUT / v
        ms, rt = segs(vd / 'MS.MAP'), segs(vd / 'RT.MAP')
        res[v] = {'class': d['cls'], 'ms_cmd': d['ms'], 'rt_cmd': d['rt'],
                  'mslink510': {'order': order(ms), 'segments': ms},
                  'rtlink610': {'order': order(rt), 'segments': rt,
                                'log_tail': (vd / 'RT.LOG').read_text(errors='replace')[-300:]
                                if (vd / 'RT.LOG').exists() else None}}
        print(v, 'MS:', res[v]['mslink510']['order'], ' RT:', res[v]['rtlink610']['order'])
    (HERE / 'exp2.json').write_text(json.dumps(res, indent=1))


if __name__ == '__main__':
    main()
