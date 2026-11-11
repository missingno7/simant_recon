"""Infer data correspondences from fresh references, pointer tables and layout.

This is the selected, fixed method: no experimental modes or source promotion.
All analysis inputs are in memory; the executable entry point alone writes files.
Blind matching receives no shared-name seeds. Evaluation is performed afterwards.
"""
import collections
import copy
import struct
from binary import Extractor, resolve, MANAGER_SEG


def distinct(seq):
    """Keep each address's first reference and the access width observed there."""
    seen, out = (set(), [])
    for item in seq:
        k = (item[0], item[1])
        if k not in seen:
            seen.add(k)
            out.append((k, item[2]))
    return out

def lcs(a, b, same):
    """Find ordered anchors; ties advance the DOS sequence deterministically."""
    n, m = (len(a), len(b))
    t = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n - 1, -1, -1):
        for j in range(m - 1, -1, -1):
            t[i][j] = t[i + 1][j + 1] + 1 if same(a[i], b[j]) else max(t[i + 1][j], t[i][j + 1])
    i = j = 0
    out = []
    while i < n and j < m:
        if same(a[i], b[j]):
            out.append((i, j))
            i += 1
            j += 1
        elif t[i + 1][j] >= t[i][j + 1]:
            i += 1
        else:
            j += 1
    return out

def reference_inputs(data, refs):
    """Deduplicate each function's addresses in first-reference order, preserving width."""
    pairs = []
    for r in refs:
        d = distinct([(s,o,w) for s,o,w,_ in r['dos_refs']])
        w = distinct([(n,delta,width) for n,delta,width,_ in r['w16_refs']])
        if d and w:
            pairs.append((r['dos'],r['win16'],d,w))
    return refs,data.symbols['data'],data.ws,data.known,data.dn,pairs


def discover_tables(images):
    """Detect the longest valid 8-byte size/count/far-pointer record run on each side."""
    ds = Extractor('dos',images)
    ws = Extractor('w16',images)
    table = images.wtable
    result = {}
    for side, ex in [('dos', ds), ('win16', ws)]:
        candidates = {}
        for key, target in ex.ptrs.items():
            if side == 'dos':
                pos = key - ex.x.sections[27].load_linear
                data = ex.x.sections[27].data
                seg = 0
                off = key
            else:
                seg, off = key
                s = ex.ne['segments'][seg - 1]
                pos = s['file_offset'] + off
                data = ex.raw
            if pos < 4:
                continue
            size, count = struct.unpack_from('<HH', data, pos - 4)
            if size not in (1, 2, 4, 8) or not 1 <= count <= 16384:
                continue
            if ex.abskey(target[0], target[1]) in ex.segw:
                continue
            if key in ex.segw:
                continue
            if side == 'dos':
                if key + 2 not in ex.segw:
                    continue
            elif (seg, off + 2) not in ex.segw:
                continue
            candidates[seg, off] = {'source': [seg, off - 4], 'shape': [size, count], 'target': list(target)}
        runs = []
        for seg, off in candidates:
            if (seg, off - 8) in candidates:
                continue
            run = []
            while (seg, off) in candidates:
                run.append(candidates[seg, off])
                off += 8
            runs.append(run)
        runs.sort(key=len, reverse=True)
        print(side, 'runs', [(len(run), run[0]['source']) for run in runs[:8]])
        result[side] = runs[0]
    for r in result['win16']:
        x = resolve(table, *r['target'])
        r['symbol'] = list(x) if x else None
    return result

def match_order(data, refs, tables, blind=False):
    """Iterate reciprocal reference-order matches with fixed usage/rival thresholds.

    Two function-pair votes suffice; one needs at least two shared users and
    Jaccard overlap >=0.6. Unique-width-only votes need two pairs and overlap
    >=0.75. A runner-up may have at most half the winning order votes. The
    publication tier later excludes any remaining rival from Tier A.
    """
    refs, syms, ws, known, dn, pairs = reference_inputs(data, refs)
    du, wu = (collections.defaultdict(set), collections.defaultdict(set))
    dw, ww = (collections.defaultdict(set), collections.defaultdict(set))
    for i, (_, _, ds, wws) in enumerate(pairs):
        for d, w in ds:
            du[d].add(i)
            dw[d].add(w)
        for k, w in wws:
            wu[k].add(i)
            ww[k].add(w)

    def jac(d, w):
        return len(du[d] & wu[w]) / len(du[d] | wu[w]) if du[d] | wu[w] else 0
    mapping = {} if blind else dict(known)
    ev = {}
    tdata = {}
    tab = tables
    ds, wws = (tab['dos'], tab['win16'])
    assert len(ds) == len(wws) == 307 and all((d['shape'] == w['shape'] for d, w in zip(ds, wws)))
    for i, (d, w) in enumerate(zip(ds, wws)):
        dk = tuple(d['target'])
        wk = tuple(w['symbol'])
        if dk in mapping and mapping[dk] != wk:
            raise ValueError(('table disagrees', dk, mapping[dk], wk))
        if wk in mapping.values() and mapping.get(dk) != wk:
            raise ValueError(('duplicate table target', wk))
        mapping[dk] = wk
        tdata[dk] = {'index': i, 'shape': d['shape'], 'dos_source': d['source'], 'win16_source': w['source']}
        ev[dk] = {'method': 'table', 'table': tdata[dk]}
    taken = set(mapping.values())
    for rnd in range(16):
        votes = collections.defaultdict(lambda: collections.defaultdict(lambda: collections.defaultdict(set)))
        for i, (_, _, ds, wws) in enumerate(pairs):
            anchors = lcs(ds, wws, lambda x, y: mapping.get(x[0]) == y[0])
            bounds = [(-1, -1)] + anchors + [(len(ds), len(wws))]
            for (i0, j0), (i1, j1) in zip(bounds, bounds[1:]):
                gd = [x for x in ds[i0 + 1:i1] if x[0] not in mapping]
                gw = [x for x in wws[j0 + 1:j1] if x[0] not in taken]
                if gd and len(gd) == len(gw) and all((x[1] == y[1] for x, y in zip(gd, gw))):
                    for x, y in zip(gd, gw):
                        votes[x[0]][y[0]]['strict'].add(i)
                else:
                    dc = collections.defaultdict(list)
                    wc = collections.defaultdict(list)
                    for x in gd:
                        dc[x[1]].append(x)
                    for x in gw:
                        wc[x[1]].append(x)
                    for width, xs in dc.items():
                        ys = wc[width]
                        if width is None:
                            continue
                        if len(xs) == len(ys) and len(xs) == 1:
                            for x, y in zip(xs, ys):
                                votes[x[0]][y[0]]['width'].add(i)

        def voters(c):
            return set().union(*c.values())
        rev = collections.defaultdict(collections.Counter)
        for dk, c in votes.items():
            for wk, v in c.items():
                rev[wk][dk] = len(voters(v))
        new = []
        for dk, c in votes.items():
            ranked = sorted(((len(voters(v)), wk) for wk, v in c.items()), key=lambda t: (-t[0], str(t[1])))
            n, wk = ranked[0]
            second = ranked[1][0] if len(ranked) > 1 else 0
            wr = rev[wk].most_common(2)
            if wr[0][0] != dk or (len(wr) > 1 and wr[1][1] * 2 > n) or second * 2 > n:
                continue
            j = jac(dk, wk)
            shared = len(du[dk] & wu[wk])
            if n < 2 and (not (n == 1 and j >= 0.6 and (shared >= 2))):
                continue
            v = c[wk]
            if not v.get('strict') and (not (n >= 2 and j >= 0.75)):
                continue
            e = {
                'method': 'order',
                'round': rnd,
                'order_votes': n,
                'strict_votes': len(v.get('strict', ())),
                'width_votes': len(v.get('width', ())),
                'jaccard': round(j, 6),
                'shared_users': shared,
                'dos_users': len(du[dk]),
                'win16_users': len(wu[wk]),
                'second_dos_votes': second,
                'second_win16_votes': wr[1][1] if len(wr) > 1 else 0,
                'functions': [pairs[i][1] for i in sorted(voters(v))],
                'rivals': [{'win16': w[0], 'delta': w[1], 'votes': nn} for nn, w in ranked[1:]],
            }
            new.append((dk, wk, e))
        added = 0
        for dk, wk, e in sorted(new, key=lambda x: (-x[2]['order_votes'], -x[2]['jaccard'], x[0])):
            if wk in taken:
                continue
            mapping[dk] = wk
            taken.add(wk)
            ev[dk] = e
            added += 1
        if not added:
            break
    corroboration = collections.defaultdict(set)
    for dk, wk in mapping.items():
        for i in du[dk] & wu[wk]:
            _, _, ds, wws = pairs[i]
            anchors = lcs(ds, wws, lambda x, y: x[0] != dk and y[0] != wk and (mapping.get(x[0]) == y[0]))
            bounds = [(-1, -1)] + anchors + [(len(ds), len(wws))]
            for (i0, j0), (i1, j1) in zip(bounds, bounds[1:]):
                gd = [x for x in ds[i0 + 1:i1] if x[0] not in mapping or x[0] == dk]
                gw = [x for x in wws[j0 + 1:j1] if x[0] not in taken or x[0] == wk]
                if len(gd) == len(gw) and all((x[1] == y[1] for x, y in zip(gd, gw))):
                    if any((x[0] == dk and y[0] == wk for x, y in zip(gd, gw))):
                        corroboration[dk].add(i)
    for dk, wk in mapping.items():
        e = ev.setdefault(dk, {'method': 'registered'})
        e['leave_one_out_order'] = [pairs[i][1] for i in sorted(corroboration[dk])]
        e['usage'] = {
            'jaccard': round(jac(dk, wk), 6),
            'shared': len(du[dk] & wu[wk]),
            'dos': len(du[dk]),
            'win16': len(wu[wk]),
        }
        e['widths'] = {'dos': sorted((str(x) for x in dw[dk])), 'win16': sorted((str(x) for x in ww[wk]))}
    referenced = {d for d in known if d in du}
    covered = referenced | set(tdata) & set(known)
    wrong = [{
        'dos': dk,
        'expected': known[dk],
        'actual': wk,
    } for dk, wk in mapping.items() if dk in known and wk != known[dk]]
    steals = [{
        'dos': dk,
        'win16': wk,
    } for dk, wk in mapping.items() if dk not in known and wk in set(known.values())]
    ok = sum((d in mapping and mapping[d] == known[d] for d in covered))
    summary = {
        'correct': ok,
        'wrong': len(wrong),
        'missed': len(covered) - ok - len(wrong),
        'referenced': len(covered),
        'known_total': len(known),
        'correct_all_known': sum((mapping.get(d) == w for d, w in known.items())),
        'wrong_rows': wrong,
        'steals': steals,
        'rows': len(mapping),
        'new_rows': len(set(mapping) - set(known)),
        'objects': sum((w[1] == 0 for w in mapping.values())),
        'rounds': rnd + 1,
    }
    rows = [{
        'dos': f'{d[0]:04X}:{d[1]:04X}',
        'dos_name': dn.get(d),
        'win16': w[0],
        'delta': w[1],
        **ev[d],
    } for d, w in sorted(mapping.items())]
    return (rows, summary)

def add_layout(data, doc, refs):
    """Add bounded layout interpolation and reciprocal unique initialized contents.

    Layout runs need at least three agreeing anchors. Extending one symbol
    beyond a run also needs equal boundary distance and nonzero byte equality.
    Zero-filled storage alone never establishes an initial-content match.
    """
    doc = copy.deepcopy(doc)
    rows = doc['matches']
    mapping = {r['dos']: r for r in rows}
    coord = lambda d: tuple((int(x, 16) for x in d.split(':')))
    taken = {(r['win16'], r['delta']) for r in rows}
    source_refs = refs
    observed = {tuple(r[:2]) for pair in source_refs for r in pair['dos_refs']} | set(data.dn)
    added = []
    runs = []
    for seg, syms in data.wtable.items():
        names = {r['win16']: r for r in rows if not r['delta'] and data.ws[r['win16']]['segment'] == seg}
        anchors = [(o, n, names[n]) for o, n in syms if n in names]
        groups = []
        group = []
        key = None
        for o, n, r in anchors:
            d = coord(r['dos'])
            k = (d[0], o - d[1])
            if key != k or (group and o - group[-1][0] > 4096):
                if group:
                    groups.append(group)
                group = []
                key = k
            group.append((o, n, r))
        if group:
            groups.append(group)
        for group in groups:
            if len(group) < 3:
                continue
            lo, hi = (group[0][0], group[-1][0])
            ds, do = coord(group[0][2]['dos'])
            shift = lo - do
            run = {
                'win16_segment': seg,
                'dos_segment': ds,
                'shift': shift,
                'anchors': [g[1] for g in group],
                'win16_range': [lo, hi],
                'dos_range': [lo - shift, hi - shift],
            }
            runs.append(run)
            for o, n in syms:
                if not lo < o < hi or (n, 0) in taken:
                    continue
                d = (ds, o - shift)
                addr = f'{ds:04X}:{d[1]:04X}'
                if not 0 <= d[1] <= 65535 or d not in observed or addr in mapping:
                    continue
                r = {
                    'dos': addr,
                    'dos_name': data.dn.get(d),
                    'win16': n,
                    'delta': 0,
                    'method': 'layout',
                    'layout_run': run,
                    'leave_one_out_order': [],
                    'usage': {'jaccard': 0, 'shared': 0, 'dos': 0, 'win16': 0},
                    'widths': {'dos': [], 'win16': []},
                }
                mapping[addr] = r
                taken.add((n, 0))
                added.append(r)
            positions = [ix for ix, (o, n) in enumerate(syms) if o in (lo, hi)]
            edge_indices = [min(positions) - 1, max(positions) + 1]
            for ix in edge_indices:
                if not 0 <= ix < len(syms):
                    continue
                o, n = syms[ix]
                d = (ds, o - shift)
                addr = f'{ds:04X}:{d[1]:04X}'
                if (n, 0) in taken or addr in mapping or d not in observed or (not 0 <= d[1] <= 65535):
                    continue
                span = data.wspan(n)
                if not span or not 4 <= span <= 8192 or data.dspan(d) != span:
                    continue
                initial = data.initial(d, (seg, o), span)
                if not initial or initial['nonzero_bytes'] < 2:
                    continue
                r = {
                    'dos': addr,
                    'dos_name': data.dn.get(d),
                    'win16': n,
                    'delta': 0,
                    'method': 'layout-edge',
                    'layout_run': run,
                    'initial_contents': initial,
                    'leave_one_out_order': [],
                    'usage': {'jaccard': 0, 'shared': 0, 'dos': 0, 'win16': 0},
                    'widths': {'dos': [], 'win16': []},
                }
                mapping[addr] = r
                taken.add((n, 0))
                added.append(r)
    for name, s in data.ws.items():
        if (name, 0) in taken:
            continue
        span = data.wspan(name)
        if not span or not 4 <= span <= 8192:
            continue
        wb = data.wbytes((s['segment'], s['offset']), span)
        if len(wb) != span or not any(wb) or len(set(wb)) < 3:
            continue
        cands = []
        for d in data.dn:
            addr = f'{d[0]:04X}:{d[1]:04X}'
            if addr in mapping:
                continue
            result = data.initial(d, (s['segment'], s['offset']), span)
            if result and result['substantial']:
                cands.append((d, result))
        if len(cands) != 1:
            continue
        d, result = cands[0]
        rivals = [n for n, t in data.ws.items() if data.wbytes((t['segment'], t['offset']), span) == wb]
        if len(rivals) != 1:
            continue
        addr = f'{d[0]:04X}:{d[1]:04X}'
        r = {
            'dos': addr,
            'dos_name': data.dn.get(d),
            'win16': name,
            'delta': 0,
            'method': 'initial',
            'initial_contents': result,
            'leave_one_out_order': [],
            'usage': {'jaccard': 0, 'shared': 0, 'dos': 0, 'win16': 0},
            'widths': {'dos': [], 'win16': []},
        }
        mapping[addr] = r
        taken.add((name, 0))
        added.append(r)
    rows = sorted(mapping.values(), key=lambda r: r['dos'])
    spacing = []
    for seg, syms in data.wtable.items():
        names = {r['win16']: r for r in rows if not r['delta'] and data.ws[r['win16']]['segment'] == seg}
        for (o, n), (no, nn) in zip(syms, syms[1:]):
            if n not in names:
                continue
            r = names[n]
            d = coord(r['dos'])
            nr = names.get(nn)
            nd = coord(nr['dos']) if nr else None
            size = data.wspan(n)
            initial = data.initial(d, (seg, o), min(size or 0, data.dspan(d) or 0))
            if initial:
                r['initial_contents'] = initial
            ds = nd[1] - d[1] if nd and nd[0] == d[0] else None
            sp = {
                'win16': n,
                'win16_address': f'{seg:04X}:{o:04X}',
                'dos': r['dos'],
                'dos_name': r['dos_name'],
                'next_win16': nn,
                'win16_spacing': no - o,
                'next_dos': nr['dos'] if nr else None,
                'dos_spacing_to_win16_neighbor': ds,
                'dos_registered_spacing': data.dspan(d),
                'same_spacing': ds == no - o if ds is not None else None,
            }
            spacing.append(sp)
            if sp['same_spacing']:
                r.setdefault('spacing_support', []).append(sp)
                nr.setdefault('spacing_support', []).append(sp)
    known = data.known
    ok = sum(((r['win16'], r['delta']) == known.get(coord(r['dos'])) for r in rows))
    wrong = [r for r in rows if coord(r['dos']) in known and (r['win16'], r['delta']) != known[coord(r['dos'])]]
    steals = [r for r in rows if coord(r['dos']) not in known and (r['win16'], r['delta']) in set(known.values())]
    return {
        'summary': {'added': len(added), 'layout_added': sum((r['method'] == 'layout' for r in added)), 'initial_added': sum((r['method'] == 'initial' for r in added)), 'correct_all_known': ok, 'wrong': len(wrong), 'steals': len(steals), 'wrong_rows': wrong, 'stolen_rows': steals, 'rows': len(rows), 'objects': sum((r['delta'] == 0 for r in rows))},
        'matches': rows,
        'layout_runs': runs,
        'spacing': spacing,
    }

def verify_pointers(data, doc, refs):
    """Compare complete initialized pointer arrays after translating proven targets."""
    doc = copy.deepcopy(doc)
    rows = doc['matches']
    dmap = {tuple((int(x, 16) for x in r['dos'].split(':'))): (data.ws[r['win16']]['segment'], data.ws[r['win16']]['offset'] + r['delta']) for r in rows}
    dp = {}
    s = data.s27
    for sg, o in s.relocs:
        lin = sg * 16 + o
        pos = lin - s.load_linear
        if pos < 2 or lin - 2 in data.drel:
            continue
        off, seg = struct.unpack_from('<HH', s.data, pos - 2)
        dp[lin - 2] = (seg, off)
    wp = {}
    for s in data.ne['segments']:
        if s['kind'] != 'DATA':
            continue
        rel = {p for f in s['relocations'] for p in f['sites']}
        for f in s['relocations']:
            t = f['target']
            if t.get('kind') != 'internal':
                continue
            for site in f['sites']:
                if f['source_type'] == 2 and site >= 2 and (site - 2 not in rel):
                    wp[s['number'], site - 2] = (t['segment'], struct.unpack_from('<H', data.raw, s['file_offset'] + site - 2)[0])
                elif f['source_type'] == 3:
                    wp[s['number'], site] = (t['segment'], t['offset'])
    cards = data.cards
    pairs = data.pairs
    cd = collections.defaultdict(set)
    for r in pairs:
        unit, seg, off = r['dos'].split(':')
        card = cards[r['win16']]
        if unit == 'root':
            cd[int(seg, 16), int(off, 16)].add((card['segment'], card['offset']))
    for v in data.x.vectors:
        key = f'{v.unit}:{v.target_seg:04X}:{v.target_off:04X}'
        r = next((r for r in pairs if r['dos'] == key), None)
        if r:
            card = cards[r['win16']]
            cd[MANAGER_SEG, v.offset].add((card['segment'], card['offset']))
    cmap = {k: next(iter(v)) for k, v in cd.items() if len(v) == 1}

    def text(b):
        b = b.split(b'\x00', 1)[0]
        if 4 <= len(b) <= 256 and all((32 <= x < 127 or x in (9, 10, 13) for x in b)):
            return b.decode('ascii')

    def dnorm(t):
        s = text(data.dbytes(t, 257))
        if s:
            return ('string', s)
        if t in dmap:
            return ('address', *dmap[t])
        if t in cmap:
            return ('address', *cmap[t])
        return None

    def wnorm(t):
        if t[0] in (8, 9, 10):
            s = text(data.wbytes(t, 257))
            if s:
                return ('string', s)
        return ('address', *t)
    dn = {r['dos']: r for r in rows}
    wn = {r['win16']: r for r in rows if r['delta'] == 0}
    added = []
    proofs = []
    for name, sym in data.ws.items():
        span = data.wspan(name)
        if not span or span < 8:
            continue
        seg, off = (sym['segment'], sym['offset'])
        num = 0
        while num < min(span // 4, 256) and (seg, off + 4 * num) in wp:
            num += 1
        if num < 2:
            continue
        targets = [wp[seg, off + 4 * i] for i in range(num)]
        wsig = [wnorm(t) for t in targets]
        candidates = []
        observed = set(data.dn) | {tuple(r[:2]) for pair in refs for r in pair['dos_refs']}
        for d in observed:
            at = d[0] * 16 + d[1]
            if not all((at + 4 * i in dp for i in range(num))):
                continue
            dt = [dp[at + 4 * i] for i in range(num)]
            sig = [dnorm(t) for t in dt]
            if sig == wsig:
                candidates.append((d, dt))
        if len(candidates) != 1:
            continue
        d, dt = candidates[0]
        addr = f'{d[0]:04X}:{d[1]:04X}'
        proof = {
            'name': name,
            'dos': addr,
            'pointer_count': num,
            'win16_targets': targets,
            'dos_targets': dt,
            'normalized_targets': wsig,
        }
        proofs.append(proof)
        if name in wn:
            if wn[name]['dos'] == addr:
                wn[name]['pointer_contents'] = proof
            continue
        if addr in dn:
            continue
        r = {
            'dos': addr,
            'dos_name': data.dn.get(d),
            'win16': name,
            'delta': 0,
            'method': 'pointer-table',
            'pointer_contents': proof,
            'leave_one_out_order': [],
            'usage': {'jaccard': 0, 'shared': 0, 'dos': 0, 'win16': 0},
            'widths': {'dos': [], 'win16': []},
        }
        rows.append(r)
        dn[addr] = r
        wn[name] = r
        added.append(r)
    doc['matches'] = sorted(rows, key=lambda r: r['dos'])
    doc['pointer_proofs'] = proofs
    doc['summary'] = {
        'added': len(added),
        'pointer_tables_matched': len(proofs),
        'rows': len(rows),
        'objects': sum((r['delta'] == 0 for r in rows)),
    }
    return doc

def infer_bases(data, doc):
    """Check member-derived bases against each other and equal symbol-bound distances."""
    doc = copy.deepcopy(doc)
    rows = doc['matches']
    by_name = collections.defaultdict(list)
    bases = {r['win16']: r for r in rows if r['delta'] == 0}
    occupied = {r['dos']: r for r in rows}
    added = []
    rejected = []
    for r in rows:
        if r['delta'] > 0:
            by_name[r['win16']].append(r)
    for name, members in by_name.items():
        groups = collections.defaultdict(list)
        for r in members:
            s, o = (int(x, 16) for x in r['dos'].split(':'))
            if o >= r['delta']:
                groups[s, o - r['delta']].append(r)
        if len(groups) != 1:
            continue
        d, m = next(iter(groups.items()))
        addr = f'{d[0]:04X}:{d[1]:04X}'
        if name in bases and bases[name]['dos'] == addr:
            continue
        span = data.wspan(name)
        if not span or span > 8192 or data.dspan(d) != span or any((r['delta'] >= span for r in m)):
            continue
        deltas = {r['delta'] for r in m}
        funcs = {f for r in m for f in r.get('functions', [])}
        if len(deltas) < 2 and (not (d in data.dn and len(funcs) >= 2)):
            continue
        if name in bases:
            old = bases[name]
            if old['method'] != 'order' or old.get('order_votes', 0) > 1 or len(deltas) < 3 or (len(funcs) < 3):
                continue
            rejected.append({
                'row': old,
                'reason': 'single-gap base conflicts with multiple member addresses and the 14-byte object boundary',
                'replacement': addr,
            })
            rows.remove(old)
            occupied.pop(old['dos'], None)
        if addr in occupied:
            continue
        r = {
            'dos': addr,
            'dos_name': data.dn.get(d),
            'win16': name,
            'delta': 0,
            'method': 'member-base',
            'members': [{k: x[k] for k in ('dos', 'delta', 'functions', 'order_votes') if k in x} for x in m],
            'equal_boundary_spacing': span,
            'leave_one_out_order': [],
            'usage': {'jaccard': 0, 'shared': 0, 'dos': 0, 'win16': 0},
            'widths': {'dos': [], 'win16': []},
        }
        rows.append(r)
        occupied[addr] = r
        bases[name] = r
        added.append(r)
    doc['matches'] = sorted(rows, key=lambda r: r['dos'])
    doc.setdefault('rejected', []).extend(rejected)
    doc['summary'] = {
        'added': len(added),
        'replaced': len(rejected),
        'rows': len(rows),
        'objects': sum((r['delta'] == 0 for r in rows)),
    }
    return doc

def terminal_gaps(data, doc, refs):
    """Propose Tier B rows in <=4-entry gaps bounded by anchors on both sides.

    This pass does not iterate and its proposals are never reused as anchors.
    A proposal needs compatible width, overlap >=0.6, and no rival order vote.
    """
    doc = copy.deepcopy(doc)
    rows = doc['matches']
    _, _, _, known, dn, pairs = reference_inputs(data, refs)
    mapping = {tuple((int(x, 16) for x in r['dos'].split(':'))): (r['win16'], r['delta']) for r in rows}
    taken = set(mapping.values())
    du, wu = (collections.defaultdict(set), collections.defaultdict(set))
    for i, (_, _, ds, wws) in enumerate(pairs):
        for d, w in ds:
            du[d].add(i)
        for w, wd in wws:
            wu[w].add(i)
    votes = collections.defaultdict(lambda: collections.defaultdict(list))
    for i, (_, _, ds, wws) in enumerate(pairs):
        anchors = lcs(ds, wws, lambda x, y: mapping.get(x[0]) == y[0])
        for (i0, j0), (i1, j1) in zip(anchors, anchors[1:]):
            gd = [x for x in ds[i0 + 1:i1] if x[0] not in mapping]
            gw = [x for x in wws[j0 + 1:j1] if x[0] not in taken]
            if 1 <= len(gd) == len(gw) <= 4 and all((x[1] == y[1] and x[1] is not None for x, y in zip(gd, gw))):
                for rank, (x, y) in enumerate(zip(gd, gw)):
                    votes[x[0]][y[0]].append({
                        'function': pairs[i][1],
                        'left_dos': ds[i0][0],
                        'left_win16': wws[j0][0],
                        'right_dos': ds[i1][0],
                        'right_win16': wws[j1][0],
                        'width': x[1],
                        'gap_count': len(gd),
                        'rank': rank,
                    })
    reverse = collections.defaultdict(set)
    for d, c in votes.items():
        for w in c:
            reverse[w].add(d)
    added = []
    for d, c in votes.items():
        if len(c) != 1:
            continue
        w, obs = next(iter(c.items()))
        if len(reverse[w]) != 1 or w[1] != 0:
            continue
        j = len(du[d] & wu[w]) / len(du[d] | wu[w])
        if j < 0.6:
            continue
        r = {
            'dos': f'{d[0]:04X}:{d[1]:04X}',
            'dos_name': dn.get(d),
            'win16': w[0],
            'delta': 0,
            'method': 'terminal-gap',
            'terminal_observations': obs,
            'leave_one_out_order': [],
            'usage': {'jaccard': round(j, 6), 'shared': len(du[d] & wu[w]), 'dos': len(du[d]), 'win16': len(wu[w])},
            'widths': {'dos': sorted({o['width'] for o in obs}), 'win16': sorted({o['width'] for o in obs})},
        }
        rows.append(r)
        added.append(r)
    doc['matches'] = sorted(rows, key=lambda r: r['dos'])
    doc['summary'] = {
        'added': len(added),
        'rows': len(rows),
        'objects': sum((r['delta'] == 0 for r in rows)),
    }
    return doc

def terminal_usage(data, doc, refs):
    """Propose reciprocal usage-only Tier B rows, excluding sibling families.

    Require three shared users, overlap >=0.6, a shared memory access width,
    and alternatives on both sides no stronger than 0.75 of the best score.
    """
    doc = copy.deepcopy(doc)
    rows = doc['matches']
    refs, _, ws, known, dn, pairs = reference_inputs(data, refs)
    du, wu = (collections.defaultdict(set), collections.defaultdict(set))
    dw, ww = (collections.defaultdict(set), collections.defaultdict(set))
    for i, (_, _, ds, wws) in enumerate(pairs):
        for d, width in ds:
            du[d].add(i)
            dw[d].add(width)
        for w, width in wws:
            wu[w].add(i)
            ww[w].add(width)
    family = set()
    for name in ws:
        for before, after in [('Black', 'Red'), ('black', 'red'), ('X', 'Y'), ('x', 'y'), ('B', 'R'), ('A', 'B')]:
            for i in range(len(name)):
                if name.startswith(before, i):
                    alt = name[:i] + after + name[i + len(before):]
                    if alt in ws:
                        family.update((name, alt))
    mapping = {tuple((int(x, 16) for x in r['dos'].split(':'))): (r['win16'], r['delta']) for r in rows}
    taken = set(mapping.values())
    inv = collections.defaultdict(set)
    for w, users in wu.items():
        for i in users:
            inv[i].add(w)
    ranked = {}
    rev = collections.defaultdict(list)
    for d, users in du.items():
        scores = collections.Counter((w for i in users for w in inv[i]))
        rr = sorted(((n / len(users | wu[w]), n, w) for w, n in scores.items()), key=lambda t: (-t[0], -t[1], t[2]))
        ranked[d] = rr
        for j, n, w in rr:
            rev[w].append((j, n, d))
    for w in rev:
        rev[w].sort(key=lambda t: (-t[0], -t[1], t[2]))
    added = []
    for d, rr in ranked.items():
        if d in mapping or not rr:
            continue
        j, n, w = rr[0]
        if w in taken or w[1] != 0 or w[0] in family or (j < 0.6) or (n < 3):
            continue
        second = rr[1][0] if len(rr) > 1 else 0
        wr = rev[w]
        rival = wr[1][0] if len(wr) > 1 else 0
        if wr[0][2] != d or second > j * 0.75 or rival > j * 0.75:
            continue
        if not (dw[d] & ww[w]) - {None, 'address'}:
            continue
        r = {
            'dos': f'{d[0]:04X}:{d[1]:04X}',
            'dos_name': dn.get(d),
            'win16': w[0],
            'delta': 0,
            'method': 'terminal-usage',
            'functions': [pairs[i][1] for i in sorted(du[d] & wu[w])],
            'usage': {'jaccard': round(j, 6), 'shared': n, 'dos': len(du[d]), 'win16': len(wu[w]), 'second_for_dos': round(second, 6), 'rival_for_win16': round(rival, 6)},
            'leave_one_out_order': [],
            'widths': {'dos': sorted((str(x) for x in dw[d])), 'win16': sorted((str(x) for x in ww[w]))},
            'sibling_excluded': True,
        }
        rows.append(r)
        added.append(r)
    doc['matches'] = sorted(rows, key=lambda r: r['dos'])
    doc['summary'] = {
        'added': len(added),
        'rows': len(rows),
        'objects': sum((r['delta'] == 0 for r in rows)),
    }
    return doc

def calibrate(rows, data):
    """Compare after matching with shared names hidden; also count stolen names."""
    known = data.known
    mapping = {tuple((int(x, 16) for x in r['dos'].split(':'))): (r['win16'], r['delta']) for r in rows}
    correct = [d for d, w in known.items() if mapping.get(d) == w]
    wrong = [{
        'dos': f'{d[0]:04X}:{d[1]:04X}',
        'expected': known[d],
        'actual': w,
    } for d, w in mapping.items() if d in known and w != known[d]]
    steals = [{
        'dos': f'{d[0]:04X}:{d[1]:04X}',
        'actual': w,
    } for d, w in mapping.items() if d not in known and w in set(known.values())]
    return {
        'correct': len(correct),
        'wrong': len(wrong),
        'missed': len(known) - len(correct) - len(wrong),
        'known': len(known),
        'steals': len(steals),
        'wrong_rows': wrong,
        'stolen_rows': steals,
        'object_rows': sum((w[1] == 0 for w in mapping.values())),
        'rows': len(mapping),
    }
