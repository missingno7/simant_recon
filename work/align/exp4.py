"""Can an RTLink/Plus 6.10 script place the hook object after the runtime without a .LIB file?

    python work/align/exp4.py      (reuses the objects of exp3/X1CODE)

  L1OBJ   LIBRARY LLIBCR, LIBH, MH.OBJ   (an .OBJ named in the LIBRARY list)
Result recorded in exp4.json.
"""
import sys, json, re, shutil, subprocess, os
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
import compiler  # noqa

HERE = Path(__file__).resolve().parent
OUT = HERE / 'exp4'
RTL = Path('C:/tools/rtlink-plus-6.10/installed')
SRC = HERE / 'exp3' / 'X1CODE'
VAR = {'L1OBJ': ['OUTPUT RT', 'MAP = RT S,N,A,L,V,X', 'NODEFLIB', 'LIBRARY LLIBCR, LIBH, MH.OBJ',
                 'FILE A, D', 'BEGINAREA', '  SECTION FILE B', 'ENDAREA']}


def main():
    OUT.mkdir(exist_ok=True)
    bat = ['@echo off', 'set LIB=C:\\;D:\\']
    for v, lnk in VAR.items():
        vd = OUT / v
        vd.mkdir(exist_ok=True)
        for f in ('A.OBJ', 'B.OBJ', 'D.OBJ', 'MH.OBJ', 'LLIBCR.LIB', 'LIBH.LIB'):
            shutil.copyfile(SRC / f, vd / f)
        for f in ('RT.EXE', 'RT.MAP', 'RT.LOG'):
            if (vd / f).exists():
                (vd / f).unlink()
        (vd / 'T.LNK').write_bytes(('\r\n'.join(lnk) + '\r\n').encode('ascii'))
        bat += [f'cd \\{v}', 'D:\\RTL-REAL.EXE @T.LNK > RT.LOG']
    (OUT / 'RUN.BAT').write_bytes(('\r\n'.join(bat) + '\r\n').encode('ascii'))
    runner = compiler.toolchain()['runners']['dosbox-x']
    conf = []
    for sec, kv in runner['conf'].items():
        conf.append(f'[{sec}]')
        conf += [f'{k}={v}' for k, v in kv.items()]
    conf += ['[autoexec]', f'mount c "{OUT.resolve()}"', f'mount d "{RTL}" -ro', 'c:', 'call RUN.BAT', 'exit']
    (OUT / 'dosbox.conf').write_text('\n'.join(conf) + '\n')
    env = os.environ.copy(); env.update(SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy')
    p = subprocess.Popen([runner['path'], '-conf', str(OUT / 'dosbox.conf'), '-fastlaunch', '-exit', '-nomenu'],
                         cwd=OUT, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        p.wait(timeout=200)
    except subprocess.TimeoutExpired:
        p.kill(); p.wait()          # our own DOSBox instance only
    res = {}
    for v in VAR:
        mp = OUT / v / 'RT.MAP'
        rows = []
        if mp.exists():
            for line in mp.read_text(errors='replace').split('Address')[0].splitlines():
                m = re.match(r'\s*([0-9A-F]{5})H\s+([0-9A-F]{5})H\s+([0-9A-F]{5})H\s+(\S+)\s+(\S+)', line)
                if m and ('TEXT' in m.group(4) or m.group(4).startswith('$$')):
                    rows.append(f'{m.group(1)} {m.group(3)} {m.group(4)} {m.group(5)}')
        res[v] = {'segments': rows, 'log_tail': (OUT / v / 'RT.LOG').read_text(errors='replace')[-500:]
                  if (OUT / v / 'RT.LOG').exists() else None}
        print(v, rows)
    (HERE / 'exp4.json').write_text(json.dumps(res, indent=1))


if __name__ == '__main__':
    main()
