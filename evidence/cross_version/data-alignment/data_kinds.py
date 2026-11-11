"""Targeted data evidence: value flow, initialized text tables, and interior contents.

These checks distinguish a stored object from a word inside a far pointer and
never infer ownership merely from the next Win16 public's address.
"""
import collections
import copy
import struct
from binary import Extractor, mem, resolve, MANAGER_SEG


def callee_sites(data, pair, side, instructions):
    """Resolve original call targets through paired publics and DOS overlay vectors."""
    if not hasattr(data, '_call_coordinates'):
        coords = {}
        for p in data.pairs:
            u, s, o = p['dos'].split(':')
            coords[u, int(s, 16), int(o, 16)] = p['win16']
        for name, r in data.symbols['code'].items():
            if not r.get('alias_of') and '_' + name in data.cards:
                coords.setdefault((r['unit'], r['seg'], r['off']), '_' + name)
        data._call_coordinates = (coords,
            {(c['segment'], c['offset']): n for n, c in data.cards.items()},
            {v.offset: (v.unit, v.target_seg, v.target_off) for v in data.x.vectors})
    coords, wincoords, vectors = data._call_coordinates
    result = {}
    if side == 'dos':
        unit, seg, _ = pair['dos'].split(':')
        seg = int(seg, 16)
    else:
        card = data.cards[pair['win16']]
        fixes = {p: f for f in data.ne['segments'][card['segment'] - 1]['relocations'] for p in f['sites']}
    for ins in instructions:
        mn, ops, at = ins['mnemonic'], ins['operands'], ins['offset']
        if mn not in ('call', 'lcall'):
            continue
        try:
            if side == 'dos':
                if mn == 'call':
                    target = (unit, seg, (int(ops, 0) - seg * 16) & 65535)
                else:
                    s, o = (int(x, 0) for x in ops.split(', '))
                    target = vectors.get(o) if s == MANAGER_SEG else (unit, s, o)
                name = coords.get(target)
                if name is None and target and mn == 'lcall':
                    name = coords.get(('root', target[1], target[2]))
            elif mn == 'call':
                name = wincoords.get((card['segment'], int(ops, 0) & 65535))
            else:
                fx = next((fixes[p] for p in range(at, at + len(ins['bytes']) // 2) if p in fixes), None)
                t = fx['target'] if fx else {}
                if t.get('kind') == 'import':
                    result[at] = f"import:{t['module']}:{t['symbol']}"
                    continue
                if t.get('kind') not in ('internal', 'entry') or 'segment' not in t:
                    continue
                off = t['offset'] if fx['source_type'] == 3 else int.from_bytes(bytes.fromhex(ins['bytes'])[1:3], 'little')
                name = wincoords.get((t['segment'], off))
            if name:
                result[at] = name
        except ValueError:
            continue
    return result


class ValueFlow(Extractor):
    """Track returned AX/DX words and the first stack argument to a resolved call."""

    def value(self, op, state, fix=None):
        value = super().value(op, state, fix)
        if value is not None:
            return value
        ea = self.ea(mem(op), state)
        if ea and ea[0] == 'local' and 6 <= ea[1] <= 32:
            return ('parameter', ea[1])
        if ea and ea[0] != 'local' and not ea[2] and self.abskey(*ea[:2]) not in self.segw:
            return ('load', ea[0], ea[1])
        return None

    def step(self, ins, state, fixups):
        args = ins['operands'].split(', ')
        mn, at = ins['mnemonic'], ins['offset']
        fx = next((fixups[p] for p in range(at, at + len(ins['bytes']) // 2) if p in fixups), None)
        after, events = super().step(ins, state, fixups)
        flow = []
        pending = state.get('ARGUMENTS', ())
        if mn == 'push':
            after['ARGUMENTS'] = (pending + (self.value(args[0], state, fx),))[-32:]
        elif mn == 'pop':
            after['ARGUMENTS'] = pending[:-1]
        elif mn in ('call', 'lcall', 'int'):
            after['ARGUMENTS'] = ()
            # A callee receiving &local cannot reach lower-addressed frame slots
            # by ordinary forward object writes. Preserve only slots below every
            # escaped address; raw BP copies make the entire frame unknown.
            if self.escape_floor is not None:
                for key, value in state.items():
                    if isinstance(key, tuple) and key[0] == 'L':
                        offset = key[1] - 65536 if key[1] >= 32768 else key[1]
                        if offset < self.escape_floor:
                            after[key] = value
            name = self.calls.get(at)
            if name:
                if at in self.far_near_calls:
                    pending = pending[:-1]  # PUSH CS is the far return frame, not a C argument.
                constants = []
                for v in reversed(pending):
                    if not v or v[0] != 'n' or len(constants) == 2:
                        break
                    constants.append(v[1])
                signature = tuple(constants)
                self.call_info[at] = (name, signature)
                after['ax'] = ('return', at, 'low')
                after['dx'] = ('return', at, 'high')
                if pending and pending[-1] and pending[-1][0] == 'load':
                    v = pending[-1]
                    size = 2
                    if len(pending) >= 2 and pending[-2] == ('load', v[1], v[2] + 2):
                        size = 4
                    flow.append(dict(kind='value-flow', role='argument', callee=name, address=list(v[1:]),
                                     bytes=size, site=at))
        elif mn == 'mov' and len(args) == 2:
            ea = self.ea(mem(args[0]), state)
            value = self.value(args[1], state, fx)
            if ea and ea[0] != 'local' and not ea[2] and value and value[0] == 'return':
                flow.append(dict(kind='value-flow', role='return-store', call_site=value[1], half=value[2],
                                 address=list(ea[:2]), site=at))
            if ea and ea[0] != 'local' and value and value[0] == 'parameter':
                flow.append(dict(kind='value-flow', role='parameter-store', parameter=value[1],
                                 address=list(ea[:2]), indexed=ea[2], site=at))
        return after, events + flow

    def scan(self, pair, row):
        unit = pair['dos'].split(':')[0] if self.side == 'dos' else None
        instructions, _ = self.instructions(unit, row)
        self.calls = callee_sites(self.images, pair, self.side, instructions)
        escaped = []
        self.escape_floor = 0
        for ins in instructions:
            if ins['mnemonic'] == 'mov' and ins['operands'].endswith(', bp') and not ins['operands'].startswith('sp,'):
                self.escape_floor = None
                break
            if ins['mnemonic'] == 'lea':
                m = mem(ins['operands'].split(', ', 1)[-1])
                if m and m[2] == ['bp']:
                    escaped.append(m[3] - 65536 if m[3] >= 32768 else m[3])
        if self.escape_floor is not None and escaped:
            self.escape_floor = min(escaped)
        self.far_near_calls = {right['offset'] for left, right in zip(instructions, instructions[1:])
            if left['mnemonic'] == 'push' and left['operands'] == 'cs' and right['mnemonic'] == 'call'
            and left['offset'] + len(left['bytes']) // 2 == right['offset']}
        self.call_info = {}
        events = [e for e in super().run(unit, row) if e['kind'] == 'value-flow']
        stores = collections.defaultdict(list)
        arguments = []
        parameters = []
        for e in events:
            if e['role'] == 'return-store':
                stores[e['call_site']].append(e)
            elif e['role'] == 'parameter-store':
                parameters.append(e)
            else:
                arguments.append(e)
        results = []
        for at, ss in stores.items():
            low = {tuple(s['address']) for s in ss if s['half'] == 'low'}
            if len(low) != 1:
                continue
            base = next(iter(low))
            high = {tuple(s['address']) for s in ss if s['half'] == 'high'}
            width = 4 if (base[0], base[1] + 2) in high else 2
            callee, signature = self.call_info[at]
            results.append(dict(role='result', callee=callee, signature=list(signature), address=list(base),
                                bytes=width, call_site=at, store_sites=[s['site'] for s in ss]))
        self.parameter_stores = []
        high_sites=set()
        for low in parameters:
            high = [h for h in parameters if h['parameter'] == low['parameter'] + 2
                    and h['address'] == [low['address'][0], low['address'][1] + 2]]
            if high:
                high_sites.add(high[0]['site'])
                self.parameter_stores.append(dict(role='parameter', callee='stack-parameter',
                    signature=[low['parameter']], address=low['address'], bytes=4,
                    store_sites=[low['site'], high[0]['site']]))
        for item in parameters:
            if item['site'] not in high_sites and not any(item['site'] in p['store_sites'] for p in self.parameter_stores):
                self.parameter_stores.append(dict(role='parameter',callee='stack-parameter',
                    signature=[item['parameter']],address=item['address'],bytes=2,store_sites=[item['site']]))
        return results, arguments


def collect_value_flows(data):
    """Collect binary producer/consumer observations for every paired function."""
    functions = {(r['unit'], r['seg'], r['off']): r for r in data.functions}
    dos, win = ValueFlow('dos', data), ValueFlow('w16', data)
    dos.images = win.images = data
    evidence = []
    creators = {'dos': [], 'w16': []}
    scanned_dos, scanned_win = set(), set()
    for pair in data.pairs:
        u, s, o = pair['dos'].split(':')
        dr, da = dos.scan(pair, functions[u, int(s, 16), int(o, 16)])
        dp = dos.parameter_stores
        wr, wa = win.scan(pair, data.cards[pair['win16']])
        wp = win.parameter_stores
        creators['dos'].extend(dict(e, owner=pair['dos']) for e in dr)
        creators['w16'].extend(dict(e, owner=pair['win16']) for e in wr)
        scanned_dos.add(pair['dos']);scanned_win.add(pair['win16'])
        for role, left, right in [('result', dr, wr), ('argument', da, wa), ('parameter', dp, wp)]:
            groups = []
            for seq in (left, right):
                group = collections.defaultdict(list)
                for e in seq:
                    key = (e['callee'], tuple(e.get('signature', [])))
                    group[key].append(e)
                groups.append(group)
            for key in groups[0].keys() & groups[1].keys():
                ds, ws = groups[0][key], groups[1][key]
                if role == 'parameter' and len(ds) == len(ws):
                    ds = sorted(ds, key=lambda e:min(e['store_sites']))
                    ws = sorted(ws, key=lambda e:min(e['store_sites']))
                    for index, (d, w) in enumerate(zip(ds, ws)):
                        resolved = resolve(data.wtable, *w['address'])
                        if resolved and not resolved[1]:
                            evidence.append(dict(dos=f"{d['address'][0]:04X}:{d['address'][1]:04X}",
                                win16=resolved[0],delta=0,role=role,callee=key[0],signature=list(key[1]),
                                dos_function=pair['dos'],win16_function=pair['win16'],dos_bytes=d['bytes'],
                                win16_bytes=w['bytes'],dos_sites=d['store_sites'],win16_sites=w['store_sites'],
                                store_index=index,store_count=len(ds)))
                    continue
                if role == 'result' and (len(ds) != 1 or len(ws) != 1):
                    continue
                if len({tuple(e['address']) for e in ds}) != 1 or len({tuple(e['address']) for e in ws}) != 1:
                    continue
                d, w = ds[0], ws[0]
                resolved = resolve(data.wtable, *w['address'])
                if not resolved or resolved[1] != 0:
                    continue
                evidence.append(dict(dos=f"{d['address'][0]:04X}:{d['address'][1]:04X}", win16=resolved[0], delta=0,
                    role=role, callee=key[0], signature=list(key[1]), dos_function=pair['dos'],
                    win16_function=pair['win16'], dos_bytes=d['bytes'], win16_bytes=w['bytes'],
                    dos_sites=d.get('store_sites', [d['site']] if 'site' in d else []),
                    win16_sites=w.get('store_sites', [w['site']] if 'site' in w else [])))
    # Producer functions need not themselves be paired. A paired consumer fixes
    # identity; matching producer callees independently establishes the value kind.
    for key, row in functions.items():
        address = f'{key[0]}:{key[1]:04X}:{key[2]:04X}'
        if address in scanned_dos:
            continue
        rs, _ = dos.scan(dict(dos=address,win16=''),row)
        creators['dos'].extend(dict(e,owner=address) for e in rs)
    for name, card in data.cards.items():
        if name in scanned_win:
            continue
        rs, _ = win.scan(dict(dos='',win16=name),card)
        creators['w16'].extend(dict(e,owner=name) for e in rs)
    for e in list(evidence):
        if e['role'] != 'argument':
            continue
        dk = [int(x,16) for x in e['dos'].split(':')]
        ws = data.ws[e['win16']];wk = [ws['segment'],ws['offset']]
        ds = [x for x in creators['dos'] if x['address']==dk]
        ww = [x for x in creators['w16'] if x['address']==wk]
        for d in ds:
            for w in ww:
                if (d['callee'],d['signature']) != (w['callee'],w['signature']):
                    continue
                evidence.append(dict(dos=e['dos'],win16=e['win16'],delta=0,role='result',callee=d['callee'],
                    signature=d['signature'],dos_function=d['owner'],win16_function=w['owner'],
                    dos_bytes=d['bytes'],win16_bytes=w['bytes'],dos_sites=d['store_sites'],win16_sites=w['store_sites'],
                    producer_scope='callee identity; parent functions need not be paired'))
    unique={repr(sorted(e.items())):e for e in evidence}
    evidence=list(unique.values())
    return sorted(evidence, key=lambda e:(e['dos'],e['win16'],e['win16_function'],e['role'],e['callee'],repr(sorted(e.items()))))


def add_value_flows(data, doc, flows, refs):
    """Use unique producer and consumer roles; preserve contradictions as rejections."""
    doc = copy.deepcopy(doc)
    rows = doc['matches']
    groups = collections.defaultdict(list)
    for e in flows:
        groups[e['dos'], e['win16']].append(e)
    rivals_d, rivals_w = collections.defaultdict(set), collections.defaultdict(set)
    def eligible(observations):
        roles = {e['role'] for e in observations}
        return ({'result', 'argument'} <= roles or 'parameter' in roles
                or any(e['role']=='result' and e['callee']=='_LoadStringAnt' and len(e['signature'])==1
                       for e in observations))
    for (d, w), observations in groups.items():
        if eligible(observations):
            rivals_d[d].add(w); rivals_w[w].add(d)
    for (address, name), observations in groups.items():
        roles = {e['role'] for e in observations}
        if not eligible(observations) or len(rivals_d[address]) != 1 or len(rivals_w[name]) != 1:
            continue
        key = tuple(int(x, 16) for x in address.split(':'))
        conflicts = [r for r in rows if (r['dos']==address or (r['win16']==name and not r['delta']))
                     and (r['dos'],r['win16'],r['delta'])!=(address,name,0)]
        if any(r['method'] in ('table','registered') for r in conflicts):
            doc.setdefault('flow_conflicts', []).append(dict(dos=address,win16=name,observations=observations,
                reason='conflicts with an already established table target or an explicitly seeded registration'))
            continue
        for r in conflicts:
            rows.remove(r)
            doc.setdefault('rejected', []).append(dict(row=r,
                reason='paired call-result stores and first-argument uses identify a different whole object',
                replacement=address, replacement_win16=name))
        old = next((r for r in rows if r['dos']==address and r['win16']==name and not r['delta']),None)
        if old is None:
            old = dict(dos=address,dos_name=data.dn.get(key),win16=name,delta=0,method='value-flow',
                leave_one_out_order=[],usage=dict(jaccard=0,shared=0,dos=0,win16=0),widths=dict(dos=[],win16=[]))
            rows.append(old)
        old['value_flows'] = observations
        du = {p['win16'] for p in refs if any(tuple(e[:2])==key for e in p['dos_refs'])}
        wu = {p['win16'] for p in refs if any(e[0]==name and not e[1] for e in p['w16_refs'])}
        if old['method']=='value-flow':
            old['usage'] = dict(shared=len(du & wu), dos=len(du), win16=len(wu),
                                jaccard=len(du & wu)/len(du | wu) if du | wu else 0)
    doc['matches'] = sorted(rows,key=lambda r:r['dos'])
    return doc


def dos_coordinate(data, linear):
    """Choose a frame evidenced by DOS registrations or resident data relocations."""
    frames = set(data.dtable)
    for segment, offset in data.s27.relocs:
        at = segment * 16 + offset - data.s27.load_linear
        frame = struct.unpack_from('<H', data.s27.data, at)[0]
        if data.s27.load_linear // 16 <= frame <= 0x55B3:
            frames.add(frame)
    valid = [s for s in frames if 0 <= linear - s * 16 <= 65535]
    if not valid:
        return None
    frame = max(valid)
    return frame, linear - frame * 16


def add_interior_contents(data, doc, refs):
    """Find exact initialized tables inside registered aggregates, not just at starts.

    A substantial unique common prefix can also support a changed table, but
    is admitted only when a paired function references the inferred DOS base.
    """
    doc = copy.deepcopy(doc)
    rows = doc['matches']
    occupied = {r['dos']:r for r in rows}
    named = {r['win16'] for r in rows if not r['delta']}
    blob = data.s27.data
    for name, symbol in data.ws.items():
        if name in named:
            continue
        span = data.wspan(name)
        if not span or not 4 <= span <= 8192:
            continue
        seg, off = symbol['segment'], symbol['offset']
        if any(off + i in data.wrel[seg] for i in range(span)):
            continue
        pattern = data.wbytes((seg,off),span)
        if len(pattern)!=span or len(set(pattern))<3 or sum(x!=0 for x in pattern)<3:
            continue
        hits=[];start=0
        while True:
            at=blob.find(pattern,start)
            if at<0:break
            hits.append(at);start=at+1
        full=True
        if len(hits)!=1 and span>=24:
            prefix=pattern[:24]
            hits=[];start=0
            while True:
                at=blob.find(prefix,start)
                if at<0:break
                hits.append(at);start=at+1
            full=False
        if len(hits)!=1:
            continue
        linear=data.s27.load_linear+hits[0]
        target=dos_coordinate(data,linear)
        if target is None:
            continue
        address=f'{target[0]:04X}:{target[1]:04X}'
        if address in occupied:
            continue
        equal=span
        if not full:
            equal=0
            while equal<span and hits[0]+equal<len(blob) and blob[hits[0]+equal]==pattern[equal]:equal+=1
        if any(linear+i in data.drel for i in range(equal)):
            continue
        shared=[p['win16'] for p in refs if any(tuple(e[:2])==target for e in p['dos_refs'])
                and any(e[0]==name for e in p['w16_refs'])]
        du={p['win16'] for p in refs if any(tuple(e[:2])==target for e in p['dos_refs'])}
        wu={p['win16'] for p in refs if any(e[0]==name for e in p['w16_refs'])}
        if not full and not shared:
            common=pattern[:equal]
            if equal < 32 or sum(x!=0 for x in common)<16 or len(set(common))<6:
                continue
        # Reject public-boundary duplicate patterns on the Win16 side too.
        rivals=[n for n,s in data.ws.items() if data.wbytes((s['segment'],s['offset']),equal)==pattern[:equal]]
        if rivals != [name]:
            continue
        r=dict(dos=address,dos_name=data.dn.get(target),win16=name,delta=0,method='interior-contents',
            content_match=dict(bytes=equal,win16_spacing=span,complete_span=full,prefix=pattern[:24].hex(),
                dos_linear=linear,functions=shared,unique_dos_occurrences=1,unique_win16_public=1),
            leave_one_out_order=[],usage=dict(jaccard=len(du & wu)/len(du | wu) if du | wu else 0,
                shared=len(du & wu),dos=len(du),win16=len(wu)),widths=dict(dos=[],win16=[]))
        rows.append(r);occupied[address]=r;named.add(name)
    doc['matches']=sorted(rows,key=lambda r:r['dos'])
    return doc


def add_text_tables(data, doc, refs):
    """Compare initialized text-pointer arrays across near/far pointer representations."""
    doc=copy.deepcopy(doc);rows=doc['matches']
    occupied={r['dos']:r for r in rows};named={r['win16'] for r in rows if not r['delta']}
    def text(raw):
        end=raw.find(b'\0')
        if not 2<=end<=180:return None
        body=raw[:end]
        return body.decode('ascii') if all(32<=b<127 or b in (9,10,13) for b in body) else None
    wp={}
    for s in data.ne['segments']:
        if s['kind']!='DATA':continue
        for fx in s['relocations']:
            t=fx['target']
            if fx['source_type']!=2 or t.get('kind')!='internal' or t['segment'] not in (8,9,10):continue
            for at in fx['sites']:
                if at<2:continue
                target=struct.unpack_from('<H',data.raw,s['file_offset']+at-2)[0]
                word=text(data.wbytes((t['segment'],target),181))
                if word:wp[s['number'],at-2]=word
    cache={}
    def dos_text(off):
        if off not in cache:cache[off]=text(data.dg[off:off+181])
        return cache[off]
    for name,s in data.ws.items():
        if name in named:continue
        span=data.wspan(name)
        if not span or span<12:continue
        words=[]
        while len(words)<min(span//4,128) and (s['segment'],s['offset']+4*len(words)) in wp:
            words.append(wp[s['segment'],s['offset']+4*len(words)])
        if len(words)<3:continue
        hits=[]
        for off in range(0x40,min(len(data.dg)-2*len(words),0x8BA0),2):
            target=struct.unpack_from('<H',data.dg,off)[0]
            if dos_text(target)!=words[0]:continue
            if all(dos_text(struct.unpack_from('<H',data.dg,off+2*i)[0])==word for i,word in enumerate(words)):
                hits.append(off)
        if len(hits)!=1:continue
        address=f'55B3:{hits[0]:04X}'
        if address in occupied:continue
        shared=[p['win16'] for p in refs if any(e[0]==0x55B3 and e[1]==hits[0] for e in p['dos_refs'])
                and any(e[0]==name for e in p['w16_refs'])]
        r=dict(dos=address,dos_name=data.dn.get((0x55B3,hits[0])),win16=name,delta=0,method='text-table',
            text_table=dict(entries=len(words),strings=words,dos_stride=2,win16_stride=4,functions=shared),
            leave_one_out_order=[],usage=dict(jaccard=0,shared=0,dos=0,win16=0),widths=dict(dos=[],win16=[]))
        rows.append(r);occupied[address]=r;named.add(name)
    doc['matches']=sorted(rows,key=lambda r:r['dos'])
    return doc


def add_layout_contents(data, doc, refs):
    """Test missing public starts in established layout runs, including one edge.

    At least three pre-existing anchors must give the same translation. A short
    common prefix can corroborate an edge, without assigning the following private
    bytes to that public. Fixup sites and all-zero patterns are excluded.
    """
    doc=copy.deepcopy(doc);rows=doc['matches']
    occupied={r['dos'] for r in rows};named={r['win16'] for r in rows if not r['delta']}
    proposals=collections.defaultdict(list)
    for run in doc.get('layout_runs', []):
        syms=data.wtable[run['win16_segment']]
        lo,hi=run['win16_range'];shift=run['shift'];ds=run['dos_segment']
        indices=[i for i,(o,n) in enumerate(syms) if lo<=o<=hi]
        if not indices:continue
        for ix in range(max(0,min(indices)-1),min(len(syms),max(indices)+2)):
            off,name=syms[ix]
            if name in named:continue
            target=(ds,off-shift);address=f'{ds:04X}:{target[1]:04X}'
            if address in occupied or not 0<=target[1]<=65535:continue
            span=data.wspan(name)
            if not span or span<2:continue
            edge=not lo<=off<=hi
            count=min(span,32 if not edge else abs(off-(lo if off<lo else hi)))
            if count<2:continue
            wb=data.wbytes((run['win16_segment'],off),count)
            db=data.dbytes(target,count)
            shared=[p['win16'] for p in refs if any(tuple(e[:2])==target for e in p['dos_refs'])
                    and any(e[0]==name and not e[1] for e in p['w16_refs'])]
            if len(wb)!=count or wb!=db or not any(wb):continue
            if sum(x!=0 for x in wb)<2 and not (span==2 and shared):continue
            linear=ds*16+target[1]
            if any(linear+i in data.drel or off+i in data.wrel[run['win16_segment']] for i in range(count)):continue
            proposals[name].append(dict(dos=address,dos_name=data.dn.get(target),win16=name,delta=0,
                method='interior-contents',layout_run=run,
                content_match=dict(bytes=count,win16_spacing=span,complete_span=count==span,
                    prefix=wb.hex(),functions=shared,scope='layout-predicted start; exact nonzero prefix'),
                leave_one_out_order=[],usage=dict(jaccard=0,shared=0,dos=0,win16=0),widths=dict(dos=[],win16=[])))
    for name,pp in sorted(proposals.items()):
        if len({p['dos'] for p in pp})!=1:continue
        p=pp[0]
        if p['dos'] in occupied:continue
        rows.append(p);occupied.add(p['dos']);named.add(name)
    doc['matches']=sorted(rows,key=lambda r:r['dos'])
    return doc


def add_indexed_order(data, doc, refs, tables, blind):
    """Compare array-reference order without intervening scalar platform state.

    This is a separate terminal view of the same function cohort. It cannot
    replace a rival mapping or seed later inference. A single pair remains B.
    """
    import alignment
    projected=copy.deepcopy(refs)
    for p in projected:
        p['dos_refs']=[e for e in p['dos_refs'] if e[3]]
        p['w16_refs']=[e for e in p['w16_refs'] if e[3]]
    candidates,_=alignment.match_order(data,projected,tables,blind)
    doc=copy.deepcopy(doc);rows=doc['matches']
    for r in candidates:
        if r['method']!='order':continue
        conflicts=[x for x in rows if x['dos']==r['dos'] or (x['win16'],x['delta'])==(r['win16'],r['delta'])]
        if conflicts:
            if len(conflicts)==1 and (conflicts[0]['dos'],conflicts[0]['win16'],conflicts[0]['delta'])==(r['dos'],r['win16'],r['delta']):
                conflicts[0]['indexed_order']=r
            continue
        r['method']='indexed-order';r['indexed_order']=copy.deepcopy(r)
        rows.append(r)
    doc['matches']=sorted(rows,key=lambda r:r['dos'])
    return doc


def platform_observations(data):
    """Record original Windows imports producing or consuming named global values.

    An import use is positive evidence of a Windows representation. The caller
    must still distinguish that representation from a possible DOS analogue.
    """
    ex=ValueFlow('w16',data);ex.images=data
    observations=[]
    for name,card in data.cards.items():
        results,args=ex.scan(dict(dos='',win16=name),card)
        for role,seq in [('result',results),('argument',args)]:
            for e in seq:
                if not e['callee'].startswith('import:'):continue
                symbol=resolve(data.wtable,*e['address'])
                if symbol and not symbol[1]:
                    observations.append(dict(win16=symbol[0],function=name,role=role,
                        **{k:v for k,v in e.items() if k!='role'}))
    return observations


def check_transfers(data):
    """Exercise pointer spills, call invalidation and parameter/return word roles.

    These are positive and negative controls for the new symbolic transfer rules;
    the blind name comparison separately measures their effect on real binaries.
    """
    ex=ValueFlow('dos',data);ex.images=data
    ex.escape_floor=-4;ex.calls={};ex.far_near_calls=set();ex.call_info={};ex.locals_escape=True
    def step(mnemonic,operands,state):
        return ex.step(dict(mnemonic=mnemonic,operands=operands,offset=0,bytes='90'),state,{})
    state={'es':('s',0x50F6),'ds':('s',0x55B3),'bx':('n',0x37F2)}
    state,_=step('mov','word ptr [bp - 4], bx',state)
    state,_=step('mov','word ptr [bp - 2], es',state)
    state['bx']=None;state['es']=None
    state,_=step('les','bx, ptr [bp - 4]',state)
    assert state['bx']==('n',0x37F2) and state['es']==('s',0x50F6)
    state[('L',65528)]=('return',10,'low')
    state[('L',65534)]=('return',10,'high')
    state['ax']=('return',10,'low')
    after,_=step('call','0x100',state)
    assert after.get('ax') is None and after.get(('L',65534)) is None
    assert after.get(('L',65528))==('return',10,'low')
    ex.escape_floor=None
    after,_=step('call','0x100',state)
    assert after.get(('L',65528)) is None
    state={'es':('s',0x50F6),'ax':('return',10,'low'),'dx':('return',10,'high')}
    _,events=step('mov','word ptr es:[0x37f2], ax',state)
    assert any(e.get('role')=='return-store' and e['half']=='low' and e['address']==[0x50F6,0x37F2] for e in events)
    _,events=step('mov','word ptr es:[0x37f4], dx',state)
    assert any(e.get('role')=='return-store' and e['half']=='high' for e in events)
    assert ex.value('word ptr [bp + 6]',{})==('parameter',6)
    assert ex.value('word ptr [bp - 6]',{}) is None
