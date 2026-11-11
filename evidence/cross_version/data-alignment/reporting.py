"""Apply publication filters and tiers, describe rows, and compare evidence artifacts.

Publication is an evidence classification, not a source rename or a byte-exact
reconstruction claim. The generated summary is derived from each row's evidence.
"""
import collections
import copy
import re
from alignment import calibrate


def prepare(data, doc, blind, refs):
    """Filter unsupported deltas, classify tiers and attach auditable observations."""
    doc = copy.deepcopy(doc)
    rows = copy.deepcopy(doc['matches'])
    br = {r['dos']: r for r in blind['matches']}
    known = data.known
    for i, r in enumerate(rows):
        b = br.get(r['dos'])
        if r['method'] == 'registered' and b and ((b['win16'], b['delta']) == (r['win16'], r['delta'])):
            rows[i] = copy.deepcopy(b)
    base = {r['win16']: r for r in rows if r['delta'] == 0}
    rejected = copy.deepcopy(doc.get('rejected', []))
    retained = []
    for r in rows:
        if r['delta']:
            b = base.get(r['win16'])
            expected = None
            if b:
                s, o = (int(x, 16) for x in b['dos'].split(':'))
                expected = f"{s:04X}:{o + r['delta']:04X}"
            if expected != r['dos'] or r['delta'] >= data.wspan(r['win16']):
                rejected.append({
                    'row': r,
                    'reason': 'no consistent independently named object base; nearest-public arithmetic does not establish ownership',
                })
                continue
        retained.append(r)
    rows = retained
    spacing = []
    by_name = {r['win16']: r for r in rows if r['delta'] == 0}
    for seg, syms in data.wtable.items():
        for (o, n), (no, nn) in zip(syms, syms[1:]):
            if n not in by_name:
                continue
            r = by_name[n]
            ds, do = (int(x, 16) for x in r['dos'].split(':'))
            nr = by_name.get(nn)
            nd = tuple((int(x, 16) for x in nr['dos'].split(':'))) if nr else None
            ds2 = nd[1] - do if nd and nd[0] == ds else None
            sp = {
                'win16': n,
                'win16_address': f'{seg:04X}:{o:04X}',
                'dos': r['dos'],
                'dos_name': r['dos_name'],
                'next_win16': nn,
                'win16_spacing': no - o,
                'next_dos': nr['dos'] if nr else None,
                'dos_spacing_to_win16_neighbor': ds2,
                'dos_registered_spacing': data.dspan((ds, do)),
                'same_spacing': ds2 == no - o if ds2 is not None else None,
            }
            spacing.append(sp)
            if sp['same_spacing']:
                r.setdefault('spacing_support', []).append(sp)
                nr.setdefault('spacing_support', []).append(sp)
            if 'initial_contents' not in r:
                init = data.initial((ds, do), (seg, o), min(no - o, data.dspan((ds, do)) or 0))
                if init:
                    r['initial_contents'] = init
    reported = {s['win16'] for s in spacing}
    for name, r in by_name.items():
        if name in reported:
            continue
        s = data.ws[name]
        d = tuple((int(x, 16) for x in r['dos'].split(':')))
        spacing.append({
            'win16': name,
            'win16_address': f"{s['segment']:04X}:{s['offset']:04X}",
            'dos': r['dos'],
            'dos_name': r['dos_name'],
            'next_win16': None,
            'win16_spacing': None,
            'next_dos': None,
            'dos_spacing_to_win16_neighbor': None,
            'dos_registered_spacing': data.dspan(d),
            'same_spacing': None,
        })

    def observed(r):
        s, o = (int(x, 16) for x in r['dos'].split(':'))
        name, delta = (r['win16'], r['delta'])
        result = []
        for p in refs:
            de = [e for e in p['dos_events'] if (e['seg'], e['off']) == (s, o)]
            we = [e for e in p['w16_events'] if (e['name'], e['delta']) == (name, delta)]
            if de and we:
                result.append({
                    'dos_function': p['dos'],
                    'win16_function': p['win16'],
                    'dos_sites': [f"{e['site']:05X}" for e in de[:4]],
                    'win16_sites': [f"{e['site']:04X}" for e in we[:4]],
                    'dos_instructions': [e['instruction'] for e in de[:2]],
                    'win16_instructions': [e['instruction'] for e in we[:2]],
                })
        return result[:3]

    def evidence(r):
        ev = []
        method = r['method']
        usage = r.get('usage', {})
        lo = r.get('leave_one_out_order', [])
        if method == 'registered':
            ev.append({
                'kind': 'existing_registration',
                'note': 'existing DOS spelling; no fresh blind recovery',
            })
        if 'table' in r:
            t = r['table']
            i = t['index']
            ev.append({
                'kind': 'initialized_pointer_table',
                'record': i,
                'records': 307,
                'size': t['shape'][0],
                'count': t['shape'][1],
                'dos_record': f'4E4B:{i * 8:04X}',
                'win16_record': f'0008:{38256 + i * 8:04X}',
                'note': 'entire ordered 307-record size/count sequence agrees; no shared-name seed needed',
            })
        if r.get('order_votes') or lo:
            ev.append({
                'kind': 'reference_order',
                'function_pairs': r.get('order_votes', len(lo)),
                'strict_votes': r.get('strict_votes', len(lo)),
                'unique_width_votes': r.get('width_votes', 0),
                'functions': r.get('functions', lo),
                'leave_one_out_functions': lo,
                'rivals_for_dos': r.get('second_dos_votes', 0),
                'rivals_for_win16': r.get('second_win16_votes', 0),
                'alternatives': r.get('rivals', []),
            })
        if 'terminal_observations' in r:
            ev.append({
                'kind': 'reference_order',
                'scope': 'terminal only; not reused as anchors',
                'observations': r['terminal_observations'],
            })
        if usage.get('shared'):
            ev.append({'kind': 'usage_overlap', **usage})
        widths = r.get('widths', {})
        actual = lambda xs: set(xs) - {'address', 'None'}
        if actual(widths.get('dos', [])) and actual(widths.get('win16', [])):
            ev.append({'kind': 'access_widths', **widths})
        if 'layout_run' in r:
            ev.append({'kind': 'layout_spacing', 'scope': method, 'run': r['layout_run']})
        elif r.get('spacing_support'):
            uniq = {(s['win16'], s['next_win16']): s for s in r['spacing_support']}
            ev.append({'kind': 'layout_spacing', 'adjacent_objects': list(uniq.values())})
        init = r.get('initial_contents')
        if init and (init['substantial'] or (method == 'layout-edge' and init['nonzero_bytes'] >= 2)):
            ev.append({'kind': 'initial_contents', **init})
        if 'pointer_contents' in r:
            ev.append({'kind': 'initialized_pointer_contents', **r['pointer_contents']})
        if 'members' in r:
            ev.append({'kind': 'member_offsets', 'members': r['members']})
            ev.append({
                'kind': 'layout_spacing',
                'dos_and_win16_boundary_spacing': r['equal_boundary_spacing'],
            })
        if r['delta']:
            ev.append({
                'kind': 'member_offsets',
                'object_base': base[r['win16']]['dos'],
                'delta': r['delta'],
                'note': 'supporting address only; does not name another object',
            })
        return ev

    def tier(r, ev):
        kinds = {e['kind'] for e in ev}
        method = r['method']
        u = r.get('usage', {})
        no_rival = not r.get('second_dos_votes', 0) and (not r.get('second_win16_votes', 0))
        if method in ('terminal-gap', 'terminal-usage'):
            return 'B'
        n = max(r.get('order_votes', 0), len(r.get('leave_one_out_order', [])))
        if r['delta']:
            return 'A' if no_rival and n >= 2 and (len(kinds & {
                'reference_order',
                'usage_overlap',
                'member_offsets',
                'access_widths',
            }) >= 2) else 'B'
        if method == 'table':
            return 'A' if 'layout_spacing' in kinds or 'initial_contents' in kinds or 'initialized_pointer_contents' in kinds or (u.get('shared', 0) >= 1 and (n >= 1 or u.get('jaccard', 0) >= 0.6)) else 'B'
        if method in ('layout', 'layout-edge'):
            return 'A' if kinds & {
                'initial_contents',
                'initialized_pointer_contents',
            } or (n >= 1 and no_rival) else 'B'
        if method == 'initial':
            return 'A' if 'layout_spacing' in kinds or (n >= 1 and no_rival) else 'B'
        if method == 'member-base':
            functions = {f for m in r['members'] for f in m.get('functions', [])}
            return 'A' if len(functions) >= 2 else 'B'
        if no_rival and n >= 1 and kinds & {
            'layout_spacing',
            'initial_contents',
            'initialized_pointer_contents',
        }:
            return 'A'
        if no_rival and n >= 2 and (u.get('shared', 0) >= 2) and (u.get('jaccard', 0) >= 0.6):
            return 'A'
        return 'B'
    result = []
    for r in rows:
        ev = evidence(r)
        t = tier(r, ev)
        obs = observed(r)
        if obs:
            ev.append({'kind': 'site_examples', 'pairs': obs})
        b = br.get(r['dos'])
        ev.append({
            'kind': 'calibration_scope',
            'existing_shared_name': tuple((int(x, 16) for x in r['dos'].split(':'))) in known,
            'also_recovered_blind': bool(b and (b['win16'], b['delta']) == (r['win16'], r['delta'])),
        })
        rr = {k: r[k] for k in ('dos', 'dos_name', 'win16', 'delta')}
        rr.update(tier=t, summary=describe(r, ev), evidence=ev)
        result.append(rr)
    assert len({r['dos'] for r in result}) == len(result)
    assert len({(r['win16'], r['delta']) for r in result}) == len(result)
    for r in result:
        assert re.fullmatch('[0-9A-F]{4}:[0-9A-F]{4}', r['dos'])
        if r['tier'] == 'A':
            assert len({e['kind'] for e in r['evidence']} - {'calibration_scope', 'site_examples', 'existing_registration'}) >= 2
    counts = collections.Counter(((r['tier'], 'object' if r['delta'] == 0 else 'support') for r in result))
    new = collections.Counter(((r['tier'], 'object' if r['delta'] == 0 else 'support') for r in result if tuple((int(x, 16) for x in r['dos'].split(':'))) not in known))
    summary = {
        'counts': {f'{t}_{k}': counts[t, k] for t in ('A', 'B') for k in ('object', 'support')},
        'new_counts': {f'{t}_{k}': new[t, k] for t in ('A', 'B') for k in ('object', 'support')},
        'rows': len(result),
        'object_names': sum((r['delta'] == 0 for r in result)),
        'rejected': len(rejected),
        'raw_blind_calibration': calibrate(blind['matches'], data),
    }
    keep = {(r['dos'], r['win16'], r['delta']) for r in result}
    blind_retained = [r for r in blind['matches'] if (r['dos'], r['win16'], r['delta']) in keep]
    summary['published_blind_calibration'] = calibrate(blind_retained, data)
    return (result, summary, spacing, rejected)


def describe(row, evidence):
    """Summarize decisive observations without overstating ownership or size."""
    kinds = {e['kind']:e for e in evidence}
    clauses = []
    if 'initialized_pointer_table' in kinds:
        e = kinds['initialized_pointer_table']
        clauses.append(f"save record index {e['record']} of {e['records']}, same element size and count")
    if 'reference_order' in kinds:
        e = kinds['reference_order']
        functions = e.get('functions',[]) or [x['function'] for x in e.get('observations',[])]
        if functions:
            names = ', '.join(n.lstrip('_') for n in functions[:2])
            remainder = f" and {len(functions)-2} more function pairs" if len(functions)>2 else ''
            clauses.append(f'same reference position in {names}{remainder}')
    if 'member_offsets' in kinds:
        e = kinds['member_offsets']
        if row['delta']:
            clauses.append(f"interior address +{row['delta']} from DOS base {e['object_base']}; support only")
        elif 'members' in e:
            clauses.append(f"{len(e['members'])} member references imply the same object base")
    if 'initialized_pointer_contents' in kinds:
        clauses.append(f"all {kinds['initialized_pointer_contents']['pointer_count']} initialized pointer targets agree")
    if 'initial_contents' in kinds:
        clauses.append(f"{kinds['initial_contents']['bytes']} initial bytes agree exactly")
    if 'layout_spacing' in kinds and len(clauses)<3:
        e = kinds['layout_spacing']
        if 'run' in e:
            clauses.append(f"consistent spacing across {len(e['run']['anchors'])} layout anchors")
        elif 'dos_and_win16_boundary_spacing' in e:
            clauses.append(f"both boundary distances are {e['dos_and_win16_boundary_spacing']} bytes")
        else:
            clauses.append('spacing to mapped neighboring objects agrees')
    if 'usage_overlap' in kinds and len(clauses)<3:
        e = kinds['usage_overlap']
        if e['shared']==e['dos']==e['win16']:
            clauses.append(f"used by the same {e['shared']} function pairs")
        else:
            clauses.append(f"{e['shared']} shared users among {e['dos']} DOS and {e['win16']} Win16 function pairs")
    if not clauses:
        clauses.append('existing registered name; not independently recovered by blind matching')
    order = kinds.get('reference_order',{})
    if order.get('rivals_for_dos',0) or order.get('rivals_for_win16',0):
        clauses.append('rival order votes remain; Tier B')
    return '; '.join(clauses[:4])+'.'
