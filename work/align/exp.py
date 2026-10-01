"""Linker experiments for the 1986/19A9 boundary (worker align).

    python work/align/exp.py [--no-rtlink]

Synthetic objects that reproduce the shape of the boundary: IDX ends with an odd-length function
(like FindIndex, which ends at 0x19A95), the next bytes are retf, retf, retf, "sub ax,ax; retf".
Each variant is linked with MS LINK 5.10 (MSC 6.00, MS-DOS Player) and with RTLink/Plus 6.10
(RTL-REAL.EXE, headless DOSBox-X; pinned hashes checked).  For every link we locate the IDX code
in the load image and report whether the next bytes are contiguous (the original: no 00 fill),
and the segment map.  The original layout is  <IDX body> CB CB CB 2B C0 CB  with no fill byte.

Variants
  V1ACC : IDX = find;           DB = s5 s6 s7 d8   (current manifest: stubs in 19A9)
  V2HYPB     : IDX = find s5 s6 s7;  DB = d8            (stubs are the index module's tail)
  V2HYPA    : IDX = find s5;        DB = s6 s7 d8      (one stub in IDX)
  V3NT       : V1 split, both files /NT DB_TEXT (one combined public segment)
  V4ALLOC    : one file, s5..d8 moved to DB2_TEXT with #pragma alloc_text
  V5MBYTE : IDX = C; DB = MASM 'DB_TEXT segment byte public' (s5 s6 s7 d8)
  V6MWORD : as V5 with 'word' (control)
"""
import sys, json, re, shutil, subprocess, os, hashlib
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
import compiler  # noqa
from omf import OmfReader  # noqa

HERE = Path(__file__).resolve().parent
OUT = HERE / 'exp'
FLAGS = ['/AL', '/Os', '/Oeg', '/Gs', '/Zi']        # the flags of root:1986 and root:19A9
MSLINK = Path('C:/tools/msc-6.00/BIN/link.exe')
RTL = Path('C:/tools/rtlink-plus-6.10/installed')
PINS = {'RTL-REAL.EXE': '228c5d429438ea32ee21dd02c65b7f8e198715b3fa957be9da328f9857482773',
        'RTLINK.DAT': '10723fb4d4381b6a38417a18409e32d254e59850bcd3b465fbb824e01367a77b'}
MSLINK_SHA = '163d8b86c18b93ccae9b2380d850cd42a9a5e1fd89a163b16170979afbbabb07'

FIND = "int far find(int a, int b)\n{\n    return a + b;\n}\n"
S = {5: "void far s5(void)\n{\n}\n", 6: "void far s6(void)\n{\n}\n", 7: "void far s7(void)\n{\n}\n"}
D8 = "int far d8(void)\n{\n    return 0;\n}\n"
MAIN = "extern int far find(int, int);\nextern void far s5(void), far s6(void), far s7(void);\n" \
       "extern int far d8(void);\nint far start(void)\n{\n    s5(); s6(); s7();\n    return find(1, 2) + d8();\n}\n"
ASM = """DB_TEXT segment {al} public 'CODE'
        assume cs:DB_TEXT
        public _s5, _s6, _s7, _d8
_s5     proc far
        ret
_s5     endp
_s6     proc far
        ret
_s6     endp
_s7     proc far
        ret
_s7     endp
_d8     proc far
        sub ax, ax
        ret
_d8     endp
DB_TEXT ends
        end
"""

VARIANTS = {
    'V1ACC': [('IDX', 'c', FIND, []), ('DB', 'c', S[5] + S[6] + S[7] + D8, [])],
    'V2HYPB': [('IDX', 'c', FIND + S[5] + S[6] + S[7], []), ('DB', 'c', D8, [])],
    'V2HYPA': [('IDX', 'c', FIND + S[5], []), ('DB', 'c', S[6] + S[7] + D8, [])],
    'V3NT': [('IDX', 'c', FIND, ['/NTDB_TEXT']), ('DB', 'c', S[5] + S[6] + S[7] + D8, ['/NTDB_TEXT'])],
    'V4ALLOC': [('ONE', 'c', "void far s5(void);\nvoid far s6(void);\nvoid far s7(void);\nint far d8(void);\n"
                  "#pragma alloc_text(DB2_TEXT, s5, s6, s7, d8)\n" + FIND + S[5] + S[6] + S[7] + D8, [])],
    'V5MBYTE': [('IDX', 'c', FIND, []), ('DB', 'asm', ASM.format(al='byte'), [])],
    'V6MWORD': [('IDX', 'c', FIND, []), ('DB', 'asm', ASM.format(al='word'), [])],
}
EXPECT = bytes.fromhex('cbcbcb2bc0cb')


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def build(vdir: Path, files):
    info = {}
    for name, lang, src, extra in files + [('MAIN', 'c', MAIN, [])]:
        if lang == 'c':
            r = compiler.compile_c(src, 'msc600ax', FLAGS + extra, basename=name)
        else:
            r = compiler.assemble(src, 'masm510', ['/Mx'], basename=name)
        if not r.ok:
            raise SystemExit(f'{vdir.name}/{name}: {r.log[-400:]}')
        (vdir / f'{name}.OBJ').write_bytes(r.obj)
        o = OmfReader(communals=True).read(r.obj)
        info[name] = [{'seg': s['name'], 'class': s.get('class'), 'align': s['alignment'],
                       'len': s.get('length'), 'bytes': bytes(o.segments.get(s['name'], b'')).hex()}
                      for s in o.segment_defs if str(s.get('class')) == 'CODE']
    return info


def objs(files):
    return [n for n, *_ in files] + ['MAIN']


def link_all(vnames, with_rt=True):
    """MS LINK 5.10 (E:) and RTLink/Plus 6.10 (D:) in one headless DOSBox-X run; 8.3 directories."""
    for f, h in PINS.items():
        assert sha(RTL / f) == h, f
    bat = ['@echo off']
    for v in vnames:
        bat += [f'cd \\{v}', f'E:\\LINK.EXE /NOD/MAP/NOE {"+".join(objs(VARIANTS[v]))},MS.EXE,MS.MAP; > MS.LOG']
        if with_rt:
            bat += [f'D:\\RTL-REAL.EXE FI {",".join(objs(VARIANTS[v]))} OUTPUT RT MAP = RT > RT.LOG']
    (OUT / 'RUN.BAT').write_bytes(('\r\n'.join(bat) + '\r\n').encode('ascii'))
    tc = compiler.toolchain()
    runner = tc['runners']['dosbox-x']
    conf = []
    for sec, kv in runner['conf'].items():
        conf.append(f'[{sec}]')
        conf += [f'{k}={v}' for k, v in kv.items()]
    conf += ['[autoexec]', f'mount c "{OUT.resolve()}"', f'mount d "{RTL}" -ro', f'mount e "{MSLINK.parent}" -ro', 'c:', 'call RUN.BAT', 'exit']
    (OUT / 'dosbox.conf').write_text('\n'.join(conf) + '\n')
    env = os.environ.copy(); env.update(SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy')
    p = subprocess.Popen([runner['path'], '-conf', str(OUT / 'dosbox.conf'), '-fastlaunch', '-exit', '-nomenu'],
                         cwd=OUT, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        p.wait(timeout=300)
    except subprocess.TimeoutExpired:
        p.kill(); p.wait()          # our own DOSBox instance only


def analyse(vdir: Path, exe: str, mapf: str, info):
    p = vdir / exe
    if not p.exists():
        return {'error': 'no exe', 'log': (vdir / (exe[:-4] + '.LOG')).read_text(errors='replace')[-400:]
                if (vdir / (exe[:-4] + '.LOG')).exists() else None}
    raw = p.read_bytes()
    hdr = int.from_bytes(raw[8:10], 'little') * 16
    img = raw[hdr:]
    find_body = None
    for n, segs in info.items():
        for s in segs:
            if s['seg'] in ('IDX_TEXT', 'DB_TEXT', 'ONE_TEXT') and s['bytes'].startswith('55'):
                find_body = bytes.fromhex(s['bytes'])[:bytes.fromhex(s['bytes']).index(0xCB) + 1]
    at = img.find(find_body)
    after = img[at + len(find_body): at + len(find_body) + 8]
    segmap = []
    mp = vdir / mapf
    if mp.exists():
        for line in mp.read_text(errors='replace').splitlines():
            m = re.match(r'\s*([0-9A-F]{5})H\s+([0-9A-F]{5})H\s+([0-9A-F]{5})H\s+(\S+)\s+(\S+)', line)
            if m:
                segmap.append(line.strip())
    return {'find_at': f'{at:05X}', 'find_end_odd': (at + len(find_body)) % 2 == 1,
            'next_bytes': after.hex(), 'contiguous_like_original': after.startswith(EXPECT),
            'fill_then_stubs': after.startswith(b'\0' + EXPECT), 'segments': segmap}


def main():
    run_rt = '--no-rtlink' not in sys.argv
    assert sha(MSLINK) == MSLINK_SHA
    OUT.mkdir(exist_ok=True)
    res = {}
    for v, files in VARIANTS.items():
        vdir = OUT / v
        if vdir.exists():
            shutil.rmtree(vdir)
        vdir.mkdir()
        info = build(vdir, files)
        res[v] = {'objects': {n: [{k: s[k] for k in ('seg', 'class', 'align', 'len')} for s in segs]
                              for n, segs in info.items()}, '_info': info}
    link_all(list(VARIANTS), run_rt)
    for v, r in res.items():
        info = r.pop('_info')
        r['mslink510'] = analyse(OUT / v, 'MS.EXE', 'MS.MAP', info)
        if run_rt:
            r['rtlink610'] = analyse(OUT / v, 'RT.EXE', 'RT.MAP', info)
    (HERE / 'exp.json').write_text(json.dumps(res, indent=1))
    for v, r in res.items():
        print(v, {k: {'next': r[k].get('next_bytes'), 'orig_like': r[k].get('contiguous_like_original'),
                      'fill': r[k].get('fill_then_stubs'), 'err': r[k].get('error')}
                  for k in ('mslink510', 'rtlink610') if k in r})


if __name__ == '__main__':
    main()
