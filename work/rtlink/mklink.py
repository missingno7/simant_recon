"""Trial historical link (worker rtlink): build objects + stubs + an RTLink/Plus freeformat script.

    python mklink.py OUTDIR [--jobs 6] [--reuse]

* Real objects: every manifest module with a complete-TU extent (and the data-only TUs), freshly
  compiled/assembled with the pinned profile.  C modules are recompiled with a distinct basename
  (8.3 object name) so each gets its own NAME_TEXT code segment, as the original sources did
  (the gate stages every source as UNIT.C, which would merge all C code segments into one
  UNIT_TEXT segment).  The code bytes are checked against the gate's object (only the segment
  name may differ).
* Stubs (trial debt, build/ only): one OMF object per original code range that no real object
  covers (unreconstructed modules and partial modules), with the exact byte size of the range and
  PUBDEFs for every symbol a real object references there; far data / DGROUP stubs define the
  referenced data symbols.  Stub bytes are zeros.  Every stub range is listed in stubs.json.
* Script T.LNK: root FILE list in address order, 4 BEGINAREA blocks with one SECTION per original
  section (objects in address order), ALWAYS list = the first 18 original vector targets in vector
  order, RELOAD FAR 400 (reload stack 0x1800 bytes), PRELOAD on S00, LLIBCR/LIBH, MAP.
"""
from __future__ import annotations
import argparse, json, os, struct, sys
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(r'D:\Prog\simant_recon')
sys.path.insert(0, str(ROOT / 'tools'))
import compiler, exe, match  # noqa: E402
from omf import OmfReader  # noqa: E402
import link as tl  # noqa: E402

ROOT_CODE_END = 0x29F4C
AREAS = [(0, 3), (4, 11), (12, 19), (20, 26)]


# ------------------------------------------------------------------ OMF writer for stubs
def rec(t, body):
    body = bytes(body)
    r = bytes([t]) + struct.pack('<H', len(body) + 1) + body
    return r + bytes([(-sum(r)) & 0xFF])


def nm(s):
    s = s.encode('latin1')
    return bytes([len(s)]) + s


def idx(i):
    return bytes([i]) if i < 0x80 else bytes([0x80 | (i >> 8), i & 0xFF])


def stub_obj(modname, segs, group=None):
    """segs: [(segname, classname, size, align_code, [(pubname, off)])]; align 1=byte 2=word 3=para.
    group: (groupname, [segment names]) or None.  No LEDATA: the linker fills zeros."""
    lnames = ['']
    def ln(x):
        if x not in lnames:
            lnames.append(x)
        return lnames.index(x)
    for s, c, *_ in segs:
        ln(s); ln(c)
    if group:
        ln(group[0])
    out = rec(0x80, nm(modname))
    out += rec(0x96, b''.join(nm(x) for x in lnames[1:]))
    for s, c, size, al, _ in segs:
        acbp = (al << 5) | (2 << 2) | (2 if size == 0x10000 else 0)
        out += rec(0x98, bytes([acbp]) + struct.pack('<H', size & 0xFFFF) + idx(ln(s)) + idx(ln(c)) + idx(1))
    if group:
        gi = [i + 1 for i, (s, *_r) in enumerate(segs) if s in group[1]]
        out += rec(0x9A, idx(ln(group[0])) + b''.join(b'\xff' + idx(i) for i in gi))
    for si, (s, c, size, al, pubs) in enumerate(segs, 1):
        grp = 1 if group and s in group[1] else 0
        for i in range(0, len(pubs), 30):
            out += rec(0x90, idx(grp) + idx(si) + b''.join(nm(n) + struct.pack('<H', o) + b'\0' for n, o in pubs[i:i + 30]))
    out += rec(0x8A, b'\0')
    return out


# ------------------------------------------------------------------ helpers
def short(key):
    unit, rest = key.split(':', 1)
    seg, _, off = rest.partition('@')
    if unit == 'root':
        base = 'R' + seg
    elif unit == 'data':
        base = 'D' + seg
    else:
        base = 'S' + unit[1:] + seg[1:]          # S + NN + 3 hex digits (frames 3126-3D56)
    if off:
        base = base[:5] + off[-3:]
    return base[:8]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('out')
    ap.add_argument('--jobs', type=int, default=6)
    ap.add_argument('--reuse', action='store_true')
    a = ap.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    man = json.loads((ROOT / 'layout/manifest.json').read_text())
    col = tl._dec(json.loads((ROOT / 'build/link/collection.json').read_text())['collection'])
    x = exe.load()
    rd = OmfReader(communals=True)
    mods = man['modules']
    real = [k for k, m in mods.items() if (m.get('extent') or k.startswith('data:'))
            and col['modules'].get(k, {}).get('res', {}).get('exact') and col['modules'][k]['source_ok']]
    names = {k: short(k) for k in real}
    assert len(set(names.values())) == len(names), 'short-name clash'

    # ---- compile real objects with distinct basenames
    def build(k):
        p = out / (names[k] + '.OBJ')
        if a.reuse and p.exists():
            return k, 'reused'
        m = mods[k]
        text = (ROOT / m['source']).read_text(encoding='latin1')
        if m.get('lang') == 'asm':
            r = compiler.assemble(text, m['profile'], m['flags'], basename=names[k])
        else:
            r = compiler.compile_c(text, m['profile'], m['flags'], basename=names[k])
        if not r.ok:
            return k, 'FAIL ' + r.log[-300:]
        mine = rd.read(r.obj, k); gate = rd.read(col['modules'][k]['col']['object'], k)
        code_m = [v for s, v in mine.segments.items() if s.endswith('_TEXT')]
        code_g = [v for s, v in gate.segments.items() if s.endswith('_TEXT')]
        same = sorted(code_m) == sorted(code_g)
        p.write_bytes(r.obj)
        return k, 'ok' if same else 'CODE DIFFERS FROM GATE OBJECT'
    with ThreadPoolExecutor(max_workers=a.jobs) as ex:
        res = dict(ex.map(build, sorted(real)))
    bad = {k: v for k, v in res.items() if v not in ('ok', 'reused')}
    if bad:
        print('build problems:', bad)
    objs = {k: rd.read((out / (names[k] + '.OBJ')).read_bytes(), k) for k in real if (out / (names[k] + '.OBJ')).exists()}

    # ---- code ranges per unit
    fx = json.loads((ROOT / 'layout/functions.json').read_text())['functions']
    unit_start = {'root': 0}
    unit_end = {'root': ROOT_CODE_END}
    for s in x.sections[:27]:
        unit_start[s.name] = s.load_seg * 16
        # code end: last function end in the section (the section image is paragraph padded)
    # frame starts: the first byte of each frame = min function address in that frame (<16 into the frame)
    fmin = defaultdict(lambda: 1 << 30)
    fend = defaultdict(int)
    for f in fx:
        u = f['unit']
        lin = f['seg'] * 16 + f['off']
        if u == 'root' and lin >= ROOT_CODE_END:
            continue
        fmin[(u, f['seg'])] = min(fmin[(u, f['seg'])], lin)
        fend[u] = max(fend[u], lin + f['size'])
    for s in x.sections[:27]:
        unit_end[s.name] = fend[s.name]
    ranges = defaultdict(list)       # unit -> [(start, kind, key)]
    for (u, seg), lin in fmin.items():
        ranges[u].append([lin, 'frame', f'{u}:{seg:04X}'])
    covered = defaultdict(list)
    for k in real:
        m = mods[k]
        if m.get('extent'):
            covered[m['unit']].append((m['extent']['start'], m['extent']['end'], k))
    seg_align, real_size, code_seg = {}, {}, {}
    AL = {'byte': 1, 'word': 2, 'paragraph': 16, 'page': 256, 'dword': 4}
    for k, o in objs.items():
        cs = [sd for sd in o.segment_defs if str(sd['name']).endswith('_TEXT') and o.segment_lengths.get(sd['name'])]
        if cs:
            seg_align[k] = AL.get(cs[0]['alignment'], 2)
            real_size[k] = o.segment_lengths[cs[0]['name']]
            code_seg[k] = cs[0]['name']
    # build ordered pieces per unit: real objects at their extents, stubs for everything else
    pieces = {}
    stubs_report = []
    for u in ['root'] + [f'S{i:02d}' for i in range(27)]:
        cov = sorted(covered[u])
        cuts = sorted({r[0] for r in ranges[u]} | {c[0] for c in cov} | {c[1] for c in cov} | {unit_start[u], unit_end[u]})
        cuts = [c for c in cuts if unit_start[u] <= c <= unit_end[u]]
        lst = []
        for lo, hi in zip(cuts, cuts[1:]):
            owner = next((k for s, e, k in cov if s <= lo < e), None)
            if owner:
                if not lst or lst[-1][2] != owner:
                    lst.append(['real', lo, owner])
            else:
                lst.append(['stub', lo, hi])
        # merge: a stub piece ends where the next piece starts (covers LINK fill before a word-aligned object)
        # simulate placement: real objects at max(aligned cursor, ...) with their SEGDEF alignment;
        # a stub fills from the cursor to the next real object's accepted start (resynchronises
        # after an unavoidable shift); a gap inside one combined segment gets no stub.
        fixed = []
        cur = unit_start[u]
        for i, p in enumerate(lst):
            if p[0] == 'real':
                al = seg_align.get(p[2], 2)
                cur = (cur + al - 1) // al * al
                p = p + [cur]                      # simulated start
                fixed.append(p)
                cur = cur + real_size.get(p[2], 0)
            else:
                nxt = lst[i + 1][1] if i + 1 < len(lst) else unit_end[u]
                if i + 1 < len(lst) and lst[i + 1][0] == 'real':
                    prv = fixed[-1] if fixed and fixed[-1][0] == 'real' else None
                    if prv and code_seg.get(prv[2]) == code_seg.get(lst[i + 1][2]):
                        continue                   # same combined segment: alignment fill only
                    al = seg_align.get(lst[i + 1][2], 2)
                    # stub ends so that the aligned cursor lands on the next object's start
                    end = nxt
                else:
                    end = nxt
                if end > cur:
                    fixed.append(['stub', cur, end, p[1]])
                    cur = end
        pieces[u] = fixed

    # ---- symbols the real objects need and nobody real defines
    defined = set()
    for o in objs.values():
        defined |= {p['name'] for p in o.publics}
        defined |= {c['name'] if isinstance(c, dict) else c[0] for c in getattr(o, 'communals', [])}
    needed = set()
    for o in objs.values():
        needed |= set(o.externals)
    runtime_names = set(json.loads((ROOT / 'layout/symbols.json').read_text())['runtime'])
    want = defaultdict(list)          # (unit, lin) -> names ; data -> ('data', frame)
    unresolved = []
    # public address map of the real objects: (unit, linear) -> public name (object placed at its extent)
    real_pub = {}
    for k, o in objs.items():
        m = mods[k]
        if not m.get('extent'):
            continue
        for p in o.publics:
            seg = p['segment']
            if not seg.endswith('_TEXT'):
                continue
            real_pub.setdefault((m['unit'], m['extent']['start'] + p['offset']), p['name'])
    defines = []
    for n in sorted(needed - defined):
        if n in runtime_names:
            continue
        r = match.obj_name_lookup(n)
        if r is None:
            unresolved.append(n); continue
        if r['kind'] == 'code':
            lin = r['seg'] * 16 + r['off']
            u = r.get('unit', 'root')
            if (u, lin) in real_pub:
                defines.append((n, real_pub[(u, lin)]))
            else:
                want[u].append((lin, n))
        else:
            want['data'].append((r['seg'], r['off'], n))

    # ---- write stub objects and the script
    stub_files = defaultdict(list)
    nstub = 0
    for u, lst in pieces.items():
        for p in lst:
            if p[0] != 'stub':
                continue
            lo, hi, olo = p[1], p[2], p[3]
            if hi <= lo:
                continue
            nstub += 1
            sname = f'Z{nstub:03d}'
            pubs = [(n, max(0, lin - lo)) for lin, n in want[u] if min(lo, olo) <= lin < hi]
            del p[3:]
            b = stub_obj(sname, [(f'{sname}_TEXT', 'CODE', hi - lo, 1, pubs)])
            (out / f'{sname}.OBJ').write_bytes(b)
            p.append(sname)
            stubs_report.append({'stub': sname, 'unit': u, 'start': lo, 'end': hi, 'bytes': hi - lo,
                                 'publics': [n for n, _ in pubs]})
    # data stubs: far frames and DGROUP
    dfr = defaultdict(list)
    for seg, off, n in want['data']:
        dfr[seg].append((off, n))
    dsegs, dgroup = [], None
    for seg in sorted(dfr):
        pubs = sorted((o, n) for o, n in dfr[seg])
        size = max(o for o, _ in pubs) + 16
        if seg == 0x55B3:
            dsegs.append(('_DATA', 'DATA', 2 * len(pubs), 2, [(n, 2 * i) for i, (o, n) in enumerate(pubs)]))
            dgroup = ('DGROUP', ['_DATA'])
        else:
            dsegs.append((f'FD{seg:04X}', 'FAR_DATA', min(size, 0xFFFF), 3, [(n, o) for o, n in pubs]))
    (out / 'ZDATA.OBJ').write_bytes(stub_obj('ZDATA', dsegs, dgroup))
    stubs_report.append({'stub': 'ZDATA', 'unit': 'data', 'segments': [(s, sz, [n for n, _ in p]) for s, c, sz, al, p in dsegs]})

    def files(u):
        return [names[p[2]] if p[0] == 'real' else p[3] for p in pieces[u] if p[0] == 'real' or len(p) > 3]
    datafiles = [names[k] for k in sorted(real) if k.startswith('data:')]
    # ALWAYS: the first 18 original vectors (declared up front, VEC-1)
    code = json.loads((ROOT / 'layout/symbols.json').read_text())['code']
    by_addr = {}
    for n, r in code.items():
        if 'alias_of' in r:
            continue
        by_addr.setdefault((r['unit'], r['seg'], r['off']), n)
    always = []
    for v in x.vectors[:18]:
        n = by_addr.get((v.unit, v.target_seg, v.target_off))
        always.append(('_' + n) if n else f'?{v.unit}:{v.target_seg:04X}:{v.target_off:04X}')
    # NEVER: cross-unit references to overlay procedures that have no vector in the original
    # (RTLink/Plus 6.10 vectors every cross-unit reference to an overlay symbol by default)
    vec_targets = {(v.unit, v.target_seg * 16 + v.target_off) for v in x.vectors}
    pub_addr = {}
    for k, o in objs.items():
        m = mods[k]
        if m.get('extent'):
            for p_ in o.publics:
                if p_['segment'].endswith('_TEXT'):
                    pub_addr[p_['name']] = (m['unit'], m['extent']['start'] + p_['offset'])
    for u_, lst_ in want.items():
        if u_ != 'data':
            for lin_, n_ in lst_:
                pub_addr.setdefault(n_, (u_, lin_))
    for a_, b_ in defines:
        if b_ in pub_addr:
            pub_addr[a_] = pub_addr[b_]
    never = set()
    for k, o in objs.items():
        uk = mods[k]['unit'] if not k.startswith('data:') else 'S27'
        for f in o.linker_fixups:
            if f['target_kind'] != 'external':
                continue
            src = uk if f['segment'].endswith('_TEXT') else 'S27'      # data segments live in the resident data section
            e = f['target']
            ua = pub_addr.get(e)
            if ua and ua[0].startswith('S') and ua[0] != src and ua not in vec_targets:
                never.add(e)
    never = sorted(never)
    L = ['# trial RTLink/Plus freeformat script generated by work/rtlink/mklink.py',
         'OUTPUT SIMANT', 'MAP = SIMANT S,N,A,L,V,X', 'NODEFLIB', 'LIBRARY LLIBCR, LIBH',
         'RELOAD FAR 400', 'VERBOSE']
    rootf = files('root')
    for i in range(0, len(rootf), 8):
        L.append('FILE ' + ', '.join(rootf[i:i + 8]))
    late_root = [names[k] for k in sorted(real) if mods[k]['unit'] == 'root' and mods[k].get('extent')
                 and mods[k]['extent']['start'] >= ROOT_CODE_END]
    if late_root:
        L.append('FILE ' + ', '.join(late_root))
    L.append('FILE ' + ', '.join(['ZDATA'] + datafiles))
    for lo, hi in AREAS:
        L.append('BEGINAREA')
        for s in range(lo, hi + 1):
            f = files(f'S{s:02d}')
            L.append('  SECTION FILE ' + ', '.join(f) + (' PRELOAD' if s == 0 else ''))
        L.append('ENDAREA')
    for a_, b_ in defines:
        q = lambda z: f'"{z}"' if z[:1] == '@' else z
        L.append(f'DEFINE {q(a_)} = {q(b_)}')
    L.append('ALWAYS ' + ', '.join(f'"{n}"' if n.startswith('@') else n for n in always if not n.startswith('?')))
    q = lambda z: f'"{z}"' if z[:1] == '@' else z
    for i in range(0, len(never), 8):
        L.append('NEVER ' + ', '.join(q(n_) for n_ in never[i:i + 8]))
    (out / 'T.LNK').write_text('\n'.join(L) + '\n', newline='\r\n')
    json.dump({'real': {k: names[k] for k in sorted(real)}, 'build': res, 'stubs': stubs_report,
               'unresolved_externals': unresolved, 'defines': defines, 'always': always, 'never': never,
               'pieces': {u: [list(p) for p in lst]
                          for u, lst in pieces.items()}},
              open(out / 'trial.json', 'w'), indent=1)
    sb = sum(s.get('bytes', 0) for s in stubs_report)
    print(f'real objects {len(objs)}, stubs {nstub} ({sb} code bytes), unresolved {len(unresolved)}: {unresolved[:10]}')


if __name__ == '__main__':
    main()
