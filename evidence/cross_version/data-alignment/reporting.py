"""Apply publication filters and tiers, describe rows, and compare evidence artifacts.

Publication is an evidence classification, not a source rename or a byte-exact
reconstruction claim. The generated summary is derived from each row's evidence.
"""
import collections
import copy
import re
from alignment import calibrate

# Audited Windows platform objects. Positive import uses are regenerated from
# the original NE before applying this exclusion; this is not a name seed.
WINDOWS_ONLY = {
    '_antCursor','_bigFontH','_captureWnd','_clipDC','_clipWind','_digCursor',
    '_dropCursor','_foodCursor','_hHelpCursor','_hInst','_lpTimerFunc',
    '_magCursor','_mainRootWnd','_paletteH','_ribbonBarWnd','_rockCursor',
    '_rootWnd','_smallFontH','_sprayCursor','_theDDEDataH','_updateRgn',
    '_wSoundBlasterMsg','_win_hwnd',
}


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
    platform_names={e['win16'] for e in getattr(data,'platform_objects',[])}
    retained = []
    for r in rows:
        if r['win16'] in WINDOWS_ONLY and r['win16'] in platform_names:
            rejected.append(dict(row=r,reason='positive Windows API handle/callback/message representation; scalar reference order is not a DOS object correspondence'))
            continue
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
        flows = r.get('value_flows', [])
        for role, kind in [('result', 'call_result_storage'), ('argument', 'call_argument_use'),
                           ('parameter', 'parameter_storage')]:
            observations = [e for e in flows if e['role'] == role]
            if observations:
                ev.append({'kind': kind, 'observations': observations,
                           'note': 'whole stored value; low and high halves distinguished explicitly'})
        if 'content_match' in r:
            ev.append({'kind': 'initial_contents', **r['content_match'],
                       'note': 'unique matching initialized bytes; public spacing is not an ownership boundary'})
        if 'text_table' in r:
            ev.append({'kind': 'text_table_contents', **r['text_table']})
        if 'indexed_order' in r:
            e=r['indexed_order']
            ev.append({'kind':'indexed_reference_order','function_pairs':e['order_votes'],
                'functions':e['functions'],'rivals_for_dos':e['second_dos_votes'],
                'rivals_for_win16':e['second_win16_votes'],
                'note':'terminal array-only projection; not reused as an anchor'})
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
        if 'content_match' not in r and init and (init['substantial'] or (method == 'layout-edge' and init['nonzero_bytes'] >= 2)):
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
        if {'call_result_storage', 'call_argument_use'} <= kinds:
            return 'A'
        if method in ('interior-contents', 'text-table'):
            shared = r.get('content_match', r.get('text_table', {})).get('functions', [])
            return 'A' if 'layout_spacing' in kinds or shared else 'B'
        if method == 'value-flow':
            return 'A' if 'layout_spacing' in kinds or (u.get('shared',0)>=2 and u.get('jaccard',0)>=0.6) else 'B'
        if method == 'indexed-order':
            return 'A' if no_rival and r['order_votes']>=2 and u.get('shared',0)>=2 else 'B'
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
    if 'call_result_storage' in kinds:
        e = kinds['call_result_storage']['observations'][0]
        suffix = f" with resource {e['signature'][0]}" if e['callee']=='_LoadStringAnt' else ''
        clauses.append(f"stores the result of {e['callee'].lstrip('_')}{suffix} ({e['dos_bytes']} DOS / {e['win16_bytes']} Win16 bytes)")
    if 'call_argument_use' in kinds:
        e = kinds['call_argument_use']['observations'][0]
        clauses.append(f"passed as the first argument to {e['callee'].lstrip('_')} in {e['win16_function'].lstrip('_')}")
    if 'parameter_storage' in kinds:
        e = kinds['parameter_storage']['observations'][0]
        clauses.append(f"stores a {e['dos_bytes']}-byte parameter at BP+{e['signature'][0]} in {e['win16_function'].lstrip('_')}")
    if 'text_table_contents' in kinds:
        clauses.append(f"same ordered {kinds['text_table_contents']['entries']} text strings across pointer representations")
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


def coverage(data, rows, refs, platform_objects):
    """Account for every original public without turning absence into a DOS match.

    The Windows-only set contains API handles or Windows callback/message state
    with positive import-use evidence. Other missing names remain unresolved.
    Pointer-view diagnostics report candidate initialized pointer sites, not new
    objects: a save-schema pointer to an array is not a named pointer variable.
    """
    from binary import Extractor, resolve
    from data_kinds import dos_coordinate
    windows_only = WINDOWS_ONLY
    by_name={r['win16']:r for r in rows if not r['delta']}
    platform=collections.defaultdict(list)
    for e in platform_objects:platform[e['win16']].append(e)
    controls={w[0] for w in data.known.values()}
    entries=[]
    for name,symbol in sorted(data.ws.items()):
        row=by_name.get(name)
        if name in controls:status='registered'
        elif row:status='tier-'+row['tier']
        elif name in windows_only:
            assert platform[name],name
            status='Windows-only'
        else:status='unresolved'
        users=[p['win16'] for p in refs if any(e[0]==name for e in p['w16_refs'])]
        entry=dict(win16=name,win16_address=f"{symbol['segment']:04X}:{symbol['offset']:04X}",
            status=status,candidate=row['dos'] if row else None,win16_spacing=data.wspan(name),
            paired_function_users=users)
        if name in windows_only:
            entry['evidence']=platform[name]
            entry['reason']='Windows API object, callback, registered message or DDE state; no DOS object with this platform representation'
        entries.append(entry)
    de,we=Extractor('dos',data),Extractor('w16',data)
    views=[]
    for name in ('_PherMapAPtr','_PherMapBNPtr','_PherMapBTPtr','_PherMapRNPtr','_PherMapRTPtr'):
        s=data.ws[name];target=we.ptrs.get((s['segment'],s['offset']))
        resolved=resolve(data.wtable,*target) if target else None
        row=by_name.get(resolved[0]) if resolved and not resolved[1] else None
        sites=[]
        if row:
            ds,do=(int(x,16) for x in row['dos'].split(':'));linear=ds*16+do
            for source,t in de.ptrs.items():
                if t[0]*16+t[1]!=linear:continue
                coord=dos_coordinate(data,source)
                if coord:
                    sites.append(dict(address=f'{coord[0]:04X}:{coord[1]:04X}',
                        in_save_schema=0x4E4B*16<=source<0x4E4B*16+307*8,
                        note='raw relocated pointer occurrence; not evidence of a separately allocated pointer variable'))
        views.append(dict(win16=name,initialized_target=list(resolved) if resolved else None,
            dos_pointer_occurrences=sites,conclusion='unresolved; matching an array target alone does not identify a pointer variable'))
    return dict(counts=dict(collections.Counter(e['status'] for e in entries)),
                names=entries,map_pointer_views=views)
