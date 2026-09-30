"""Survey: SEGDEF alignment of every accepted module's code segment vs its placed start.

python work/align/survey.py [--jobs 6]  -> work/align/survey.json
Compiles each manifest module once (the gate's profile/flags), reads its OMF SEGDEFs, finds the
code segment(s) that hold claimed publics, and derives the object origin:
  extent modules: extent start; otherwise first-claim linear - public offset (one delta).
Also records the bytes between the previous function-table row end and the origin (fill).
"""
import sys, json, argparse
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools'))
import compiler, match, exe as exemod, modules as modmod  # noqa
import functions as fnmod  # noqa
from omf import OmfReader  # noqa

ALIGN = modmod.ALIGN_BYTES


def one(key, m):
    text = (ROOT / m['source']).read_text(encoding='latin1')
    if m.get('lang') == 'asm':
        r = compiler.assemble(text, m['profile'], m['flags'])
    else:
        r = compiler.compile_c(text, m['profile'], m['flags'])
    if not r.ok:
        return key, {'error': 'compile failed'}
    obj = OmfReader(communals=True).read(r.obj)
    segs = [{'name': s['name'], 'class': s.get('class'), 'align': s.get('alignment'),
             'length': modmod.segdef_length(s)} for s in obj.segment_defs]
    claims = [c for c in m.get('claims', []) if not modmod.is_data_claim(c)]
    deltas = {}
    for c in claims:
        pub, prec = match.public_in(obj, c['name'])
        if prec is None:
            continue
        lin = c['seg'] * 16 + c['off']
        deltas.setdefault(prec['segment'], set()).add(lin - prec['offset'])
    out = {'segdefs': segs, 'code': []}
    for sname, ds in deltas.items():
        sd = modmod.segment_def(obj, sname)
        for d in sorted(ds):
            out['code'].append({'segment': sname, 'align': sd.get('alignment'), 'origin': d,
                                'origin_hex': f'{d:05X}', 'length': modmod.segment_length(obj, sname),
                                'misaligned': bool(d % ALIGN.get(sd.get('alignment'), 1))})
    if m.get('extent'):
        out['extent'] = [f"{m['extent']['start']:05X}", f"{m['extent']['end']:05X}"]
    return key, out


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--jobs', type=int, default=6)
    a = ap.parse_args()
    man = modmod.load_manifest()
    x = exemod.load()
    with ThreadPoolExecutor(a.jobs) as ex:
        res = dict(ex.map(lambda k: one(k, man['modules'][k]), sorted(man['modules'])))
    rows = fnmod.table()['functions']
    for key, r in res.items():
        m = man['modules'][key]
        for c in r.get('code', []):
            o = c['origin']
            prev = max((q['seg'] * 16 + q['off'] + q['size'] for q in rows
                        if q['unit'] == m['unit'] and q['seg'] * 16 + q['off'] + q['size'] <= o), default=None)
            if prev is not None and o - prev < 32:
                c['gap_before'] = x.read(m['unit'], prev, o - prev).hex()
                c['prev_row_end'] = f'{prev:05X}'
    Path(__file__).with_name('survey.json').write_text(json.dumps(res, indent=1))
    bad = [(k, c) for k, r in res.items() for c in r.get('code', []) if c['misaligned']]
    n = sum(len(r.get('code', [])) for r in res.values())
    print(f'{len(res)} modules, {n} code placements, {len(bad)} misaligned')
    for k, c in bad:
        print(' ', k, c)
    from collections import Counter
    print(Counter((m.get('lang', 'c'), c['align']) for k, r in res.items() for c in r.get('code', [])
                  for m in [man['modules'][k]]))
    for k, r in res.items():
        if 'error' in r:
            print('ERR', k)


if __name__ == '__main__':
    main()
