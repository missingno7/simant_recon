"""MEMHOOK_TEXT placement in an RTLink/Plus 6.10 *overlaid* link (root + overlay area + far data).

    python work/align/exp3.py

In the original the runtime's C_ETEXT (class ENDCODE) is the first segment of the resident data
section 27 (crt0 DBDATA word = 3D57, S27 relocation at 5D8F0), i.e. behind the overlay areas, while
MEMHOOK_TEXT sits in the root right after EMULATOR_TEXT.  t3 shows 6.10 does the same with C_ETEXT.
This run tests where a hook segment of a non-CODE class goes in the same setting, against a
CODE-class hook read from a library searched after LLIBCR.

  X1CODE   MH class 'CODE', object listed as FILE after A        (t3 layout)
  X2CLASS  MH class 'MEMHOOK'
  X2END    MH class 'HOOKCODE' (class name ends in CODE)
  X3LIB    MH class 'CODE' in MH.LIB searched after LLIBCR, LIBH
"""
import sys, json, re, shutil, subprocess, os, hashlib
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
import compiler  # noqa

HERE = Path(__file__).resolve().parent
OUT = HERE / 'exp3'
MSBIN = Path('C:/tools/msc-6.00/BIN')
RTL = Path('C:/tools/rtlink-plus-6.10/installed')
PINS = {RTL / 'RTL-REAL.EXE': '228c5d429438ea32ee21dd02c65b7f8e198715b3fa957be9da328f9857482773',
        RTL / 'RTLUTILS.LIB': 'c718bac09b0b1204a259494446acfa8bfffb129144cc7d36799855621f4fdccb'}

A = ("extern int far jt_a(void);\nextern int far ovl(void);\nextern int far fd[4];\n"
     "int far target(void)\n{\n    return fd[1];\n}\n"
     "int main(void)\n{\n    return jt_a() + ovl();\n}\n")
B = "int far ovl(void)\n{\n    return 2;\n}\n"
D = "int far fd[4] = {1, 2, 3, 4};\n"
MH = """        extrn   _target:far
MEMHOOK_TEXT segment word public '{cls}'
        assume  cs:MEMHOOK_TEXT
        public  _jt_a
_jt_a:  jmp     _target
MEMHOOK_TEXT ends
        end
"""
VAR = {'X1CODE': ('CODE', False), 'X2CLASS': ('MEMHOOK', False), 'X2END': ('HOOKCODE', False),
       'X3LIB': ('CODE', True)}


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    for p, h in PINS.items():
        assert sha(p) == h, p
    libs = json.loads((ROOT / 'layout/manifest.json').read_text())['runtime']['libraries']
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    bat = ['@echo off', 'set LIB=C:\\;D:\\']
    for v, (cls, inlib) in VAR.items():
        vd = OUT / v
        vd.mkdir()
        for name, src in (('A', A), ('B', B), ('D', D)):
            r = compiler.compile_c(src, 'msc600ax', ['/AL', '/Os', '/Gs'], basename=name)
            assert r.ok, r.log
            (vd / f'{name}.OBJ').write_bytes(r.obj)
        r = compiler.assemble(MH.format(cls=cls), 'masm510', ['/Mx'], basename='MH')
        assert r.ok, r.log
        (vd / ('MHX.OBJ' if inlib else 'MH.OBJ')).write_bytes(r.obj)
        for lib in ('llibcr.lib', 'libh.lib'):
            shutil.copyfile(libs[lib]['path'], vd / lib.upper())
        lnk = ['OUTPUT RT', 'MAP = RT S,N,A,L,V,X', 'NODEFLIB',
               'LIBRARY LLIBCR, LIBH' + (', MH' if inlib else ''),
               'FILE A, D' + ('' if inlib else ', MH'), 'BEGINAREA', '  SECTION FILE B', 'ENDAREA']
        (vd / 'T.LNK').write_bytes(('\r\n'.join(lnk) + '\r\n').encode('ascii'))
        bat.append(f'cd \\{v}')
        if inlib:
            bat.append('E:\\LIB.EXE MH.LIB +MHX.OBJ; > LIB.LOG')
        bat.append('D:\\RTL-REAL.EXE @T.LNK > RT.LOG')
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
    for v in VAR:
        mp = OUT / v / 'RT.MAP'
        rows = []
        if mp.exists():
            txt = mp.read_text(errors='replace')
            head = txt.split('Address')[0]
            for line in head.splitlines():
                s = line.strip()
                if s.startswith('Overlay') or s.startswith('Resident'):
                    rows.append(s)
                m = re.match(r'([0-9A-F]{5})H\s+([0-9A-F]{5})H\s+([0-9A-F]{5})H\s+(\S+)\s+(\S+)', s)
                if m:
                    rows.append(f'{m.group(1)} {m.group(3)} {m.group(4)} {m.group(5)}')
        names = [r.split()[2] if len(r.split()) > 3 else r for r in rows]
        verdict = None
        if rows:
            try:
                i_emu, i_mh = names.index('EMULATOR_TEXT'), names.index('MEMHOOK_TEXT')
                i_mgr = next(i for i, n in enumerate(names) if n.startswith('$$OVLMGR'))
                i_ovl = next(i for i, n in enumerate(names) if n.startswith('Overlay'))
                verdict = ('ORIGINAL (root, after EMULATOR_TEXT, before manager)' if i_emu < i_mh < i_mgr
                           else 'BEFORE _TEXT' if i_mh < names.index('_TEXT')
                           else 'AFTER OVERLAY AREAS' if i_mh > i_ovl else 'OTHER')
            except (ValueError, StopIteration) as e:
                verdict = f'incomplete: {e}'
        res[v] = {'class': VAR[v][0], 'library': VAR[v][1], 'verdict': verdict, 'segments': rows,
                  'log_tail': (OUT / v / 'RT.LOG').read_text(errors='replace')[-400:]
                  if (OUT / v / 'RT.LOG').exists() else None}
        print(v, verdict)
    (HERE / 'exp3.json').write_text(json.dumps(res, indent=1))


if __name__ == '__main__':
    main()
