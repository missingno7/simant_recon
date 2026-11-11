"""Read original DOS/NE images, reconstruct function CFGs, and extract data references.

Only raw executable bytes and registries supplied by run.py are read. No generated
cards, cache, source reconstruction or published match is used as an analysis input.
Segment/offset coordinates remain in their original binaries' coordinate systems.
"""
import bisect
import collections
import re
import struct
from types import SimpleNamespace
import capstone as cs
from capstone import Cs, CS_ARCH_X86, CS_MODE_16
from capstone.x86 import X86_OP_IMM

DGROUP = 0x55B3
W_DGROUP = 10
W_DATA_SEGS = {8, 9, 10}
MANAGER_SEG = 0x2CFF
REGS = ('ax','bx','cx','dx','si','di','bp','sp','ds','es','ss','cs')
IMM = re.compile(r'^-?(?:0x[0-9a-f]+|\d+)$')
MEM = re.compile(r'(?:(byte|word|dword) ptr )?(?:(es|ds|ss|cs):)?\[([^\]]+)\]')
LOW = {'al':'ax','ah':'ax','bl':'bx','bh':'bx','cl':'cx','ch':'cx','dl':'dx','dh':'dx'}
md = Cs(CS_ARCH_X86, CS_MODE_16)

def decoder():
    d = Cs(CS_ARCH_X86, CS_MODE_16)
    d.detail = True
    return d

class DosImage:
    """MZ image and RTLink resident/overlay sections; see docs/exe-format.md."""

    def __init__(self, raw):
        if raw[:2] != b'MZ':
            raise ValueError('DOS input is not MZ')
        last, pages, count, header = struct.unpack_from('<4H', raw, 2)
        size = (pages-1)*512+last if last else pages*512
        self.image = raw[header*16:size]
        reloc_offset = struct.unpack_from('<H', raw, 24)[0]
        self.relocs = [(s,o) for o,s in (struct.unpack_from('<HH',raw,reloc_offset+4*i) for i in range(count))]
        self.sections = []
        base = MANAGER_SEG*16
        count = struct.unpack_from('<H', self.image, base+0x0B6B)[0]
        for i in range(count):
            w = struct.unpack_from('<9H', self.image, base+0x0B71+18*i)
            rec = w[2]*16
            pos = rec+((w[5]*4+15)//16)*16
            section = SimpleNamespace(load_linear=w[0]*16,
                data=raw[pos:pos+w[8]*16], data_file_offset=pos,
                relocs=[(s,o) for o,s in (struct.unpack_from('<HH',raw,rec+4*k) for k in range(w[5]))])
            if len(section.data) != w[8]*16:
                raise ValueError('truncated RTLink section')
            self.sections.append(section)
        self.vectors = []
        off = 0x25F6
        while self.image[base+off] == 0xE8 and self.image[base+off+3] == 0xEA:
            toff,tseg,sec = struct.unpack_from('<HHH',self.image,base+off+4)
            self.vectors.append(SimpleNamespace(offset=off,target_seg=tseg,target_off=toff,
                unit='root' if sec==0xFFFF else f'S{sec:02d}'))
            off += 10

    def unit_bytes(self, unit):
        if unit == 'root':
            return 0, self.image
        s = self.sections[int(unit[1:])]
        return s.load_linear, s.data

    def reloc_sites(self, unit):
        relocs = self.relocs if unit=='root' else self.sections[int(unit[1:])].relocs
        return {s*16+o for s,o in relocs}

def parse_ne(raw):
    """Read segment records and follow loader relocation chains without applying them."""
    n = struct.unpack_from('<I', raw, 60)[0]
    if raw[n:n+2] != b'NE':
        raise ValueError('Win16 input is not NE')
    count = struct.unpack_from('<H',raw,n+28)[0]
    table = n+struct.unpack_from('<H',raw,n+34)[0]
    shift = struct.unpack_from('<H',raw,n+50)[0]
    widths = {0:1, 2:2, 3:4, 5:2, 11:6, 13:4}
    result = {'segments': []}
    for i in range(count):
        sector,size,flags,alloc = struct.unpack_from('<4H',raw,table+8*i)
        start = sector<<shift
        logical = size or 65536
        segment = dict(number=i+1,file_offset=start if sector else None,
            logical_size=logical, allocation_size=alloc or 65536,
            kind='DATA' if flags&1 else 'CODE',relocations=[])
        if flags&8:
            raise ValueError('iterated NE segments are unsupported')
        if sector and flags&256:
            at = start+logical
            rc = struct.unpack_from('<H',raw,at)[0]
            for j in range(rc):
                typ,rf,source,t1,t2 = struct.unpack_from('<BBHHH',raw,at+2+8*j)
                if typ not in widths:
                    raise ValueError(f'unsupported NE relocation type {typ}')
                target = {'kind':'other'}
                if rf&3==0 and t1&255!=255:
                    target = {'kind':'internal','segment':t1&255,'offset':t2}
                sites = []
                site = source
                while True:
                    if site in sites or site+widths[typ]>logical:
                        raise ValueError('invalid NE relocation chain')
                    sites.append(site)
                    if rf&4:
                        break
                    site = struct.unpack_from('<H',raw,start+site)[0]
                    if site == 65535:
                        break
                segment['relocations'].append(dict(source_type=typ,width=widths[typ],
                    target=target,sites=sites))
        result['segments'].append(segment)
    return result


def switch_table(ins, chain, seen, code, start, limit, relocation_bytes):
    """Recognise the MSC 7 switch dispatch `cmp r,N ; ja default ; shl r,1 ;
    xchg bx,r|mov bx,r ; jmp word ptr cs:[bx+T]` and return its table.

    The table holds N+1 (`ja`) or N (`jae`/`jnb`) near code offsets stored
    directly after the jump (up to two alignment NOPs allowed). Every entry must lie
    inside the symbol bound and no table byte may carry a loader obligation.
    Anything else stays an unresolved indirect jump.
    """
    if ins.mnemonic != 'jmp' or len(ins.operands) != 1 or ins.operands[0].type != cs.x86.X86_OP_MEM:
        return None
    mem = ins.operands[0].mem
    if ins.reg_name(mem.segment) != 'cs' or ins.reg_name(mem.base) != 'bx' or mem.index:
        return None
    table = mem.disp & 65535
    after = ins.address + ins.size
    if not (after <= table <= after + 2 and all((b == 144 for b in code[after:table]))):
        return None
    back = []
    pos = ins.address
    for _ in range(3):
        pos = chain.get(pos)
        if pos is None:
            break
        back.append(seen[pos])
    text = [(i.mnemonic, i.op_str) for i in back]
    if len(text) < 2:
        return None
    prescaled = False
    if text[0] in (('xchg', 'bx, ax'), ('xchg', 'ax, bx'), ('mov', 'bx, ax')) and text[1] == ('shl', 'ax, 1'):
        shift = back[1]
    elif text[0] == ('shl', 'bx, 1'):
        shift = back[0]
    elif text[0] in (('xchg', 'bx, ax'), ('xchg', 'ax, bx'), ('mov', 'bx, ax')) and text[1][0] in ('ja', 'jae', 'jnb'):
        shift = back[0]
        prescaled = True
    else:
        return None
    pred = chain.get(shift.address)
    branch = seen.get(pred) if pred is not None else None
    if branch is not None and branch.mnemonic == 'mov' and branch.op_str.startswith('ax, '):
        pred = chain.get(branch.address)
        branch = seen.get(pred) if pred is not None else None
    if branch is None or branch.mnemonic not in ('ja', 'jae', 'jnb'):
        branch = next((i for i in seen.values() if i.mnemonic in ('jbe', 'jb', 'jna', 'jnae') and len(i.operands) == 1 and (i.operands[0].type == X86_OP_IMM) and (i.operands[0].imm == shift.address)), None)
        if branch is None:
            return None
    cmp_pos = chain.get(branch.address)
    cmp_ins = seen.get(cmp_pos) if cmp_pos is not None else None
    if cmp_ins is None or cmp_ins.mnemonic != 'cmp' or len(cmp_ins.operands) != 2 or (cmp_ins.operands[1].type != X86_OP_IMM):
        return None
    bound = cmp_ins.operands[1].imm
    count = bound + 1 if branch.mnemonic in ('ja', 'jbe', 'jna') else bound
    if prescaled:
        pos = chain.get(cmp_ins.address)
        shr = seen.get(pos) if pos is not None else None
        if shr is None or shr.mnemonic != 'shr' or (not shr.op_str.startswith('ax, ')) or (shr.operands[1].type != X86_OP_IMM):
            return None
        k = shr.operands[1].imm
        mask = None
        for _ in range(4):
            pos = chain.get(pos)
            if pos is None:
                break
            prev = seen[pos]
            if prev.mnemonic == 'and' and prev.op_str.startswith('ax, ') and (prev.operands[1].type == X86_OP_IMM):
                mask = prev.operands[1].imm
                break
            if prev.mnemonic not in ('test', 'cmp') and (not prev.group(cs.CS_GRP_JUMP)):
                break
        if mask is None or mask >> k & 1 or bound % 2 or (branch.mnemonic not in ('ja', 'jbe', 'jna')):
            return None
        count = bound // 2 + 1
    if not 1 <= count <= 256 or table + 2 * count > limit:
        return None
    if any((p in relocation_bytes for p in range(table, table + 2 * count))):
        return None
    targets = [int.from_bytes(code[table + 2 * i:table + 2 * i + 2], 'little') for i in range(count)]
    if any((not start <= t < limit for t in targets)):
        return None
    return dict(source=ins.address, table=table, count=count, targets=targets, bound_check=cmp_ins.address)

def solve(code, start, limit, entries=(), relocations=(), segment=None):
    pending = [start]
    seen = {}
    edges = []
    returns = []
    issues = []
    indirect = []
    occupied = {}
    chain = {}
    tables = []
    entries = set(entries)
    relocation_bytes = {p for r in relocations for q in r['sites'] for p in range(q, q + r['width'])}
    while pending:
        pos = pending.pop()
        if pos in seen:
            continue
        if not start <= pos < limit:
            edges.append(dict(target=pos, kind='CROSS_BOUNDARY'))
            continue
        if pos in occupied:
            issues.append('overlapping instruction streams')
            continue
        ins = next(decoder().disasm(code[pos:min(pos + 15, limit)], pos, count=1), None)
        if ins is None:
            issues.append('undecodable instruction')
            continue
        if any((p in occupied for p in range(pos, pos + ins.size))):
            issues.append('overlapping instruction streams')
            continue
        seen[pos] = ins
        for p in range(pos, pos + ins.size):
            occupied[p] = pos
        if ins.group(cs.CS_GRP_RET):
            returns.append(pos)
            continue
        if ins.mnemonic in ('int', 'int3', 'iret', 'iretw', 'hlt'):
            issues.append('non-return terminator')
            continue
        if ins.group(cs.CS_GRP_JUMP):
            found = switch_table(ins, chain, seen, code, start, limit, relocation_bytes)
            if found:
                if any((p in occupied for p in range(found['table'], found['table'] + 2 * found['count']))):
                    issues.append('overlapping instruction streams')
                    continue
                for p in range(found['table'], found['table'] + 2 * found['count']):
                    occupied[p] = 'table'
                tables.append(found)
                for t in found['targets']:
                    edges.append(dict(source=pos, target=t, kind='TABLE'))
                    pending.append(t)
                continue
            if ins.mnemonic == 'ljmp':
                relocation = next((r for r in relocations if pos + 1 in r['sites'] or pos + 3 in r['sites']), None)
                target = relocation.get('target', {}) if relocation else {}
                if target.get('kind') == 'internal':
                    dest = target['offset'] if relocation['source_type'] == 3 else int.from_bytes(code[pos + 1:pos + 3], 'little')
                    edge = dict(source=pos, target=dest, target_segment=target['segment'], kind='BRANCH' if target['segment'] == segment else 'CROSS_BOUNDARY')
                    edges.append(edge)
                    if target['segment'] == segment:
                        pending.append(dest)
                    continue
            if len(ins.operands) != 1 or ins.operands[0].type != X86_OP_IMM:
                indirect.append(pos)
                continue
            dest = ins.operands[0].imm
            edges.append(dict(source=pos, target=dest, kind='BRANCH'))
            pending.append(dest)
            if ins.mnemonic == 'jmp':
                continue
        chain[pos + ins.size] = pos
        pending.append(pos + ins.size)
    end = max([i.address + i.size for i in seen.values()] + [t['table'] + 2 * t['count'] for t in tables], default=start)
    gaps = []
    pos = start
    table_spans = {(t['table'], t['table'] + 2 * t['count']) for t in tables}
    for ins in sorted(seen.values(), key=lambda i: i.address):
        if pos < ins.address:
            data = code[pos:ins.address]
            padding = all((b == 144 for b in data)) and (not any((p in relocation_bytes for p in range(pos, ins.address))))
            inside = [(a, b) for a, b in table_spans if pos <= a and b <= ins.address]
            remainder = [code[q:q + 1] for q in range(pos, ins.address) if not any((a <= q < b for a, b in inside))]
            table_gap = bool(inside) and all((x == b'\x90' for x in remainder)) and (not any((p in relocation_bytes for p in range(pos, ins.address))))
            if table_gap:
                classification = 'JUMP_TABLE'
            elif padding:
                classification = 'ALIGNMENT_NOP'
            else:
                classification = 'UNOWNED'
            gaps.append(dict(start=pos, end=ins.address, hex=data.hex(), classification=classification))
        pos = ins.address + ins.size
    for a, b in table_spans:
        if a >= pos:
            gaps.append(dict(start=a, end=b, hex=code[a:b].hex(), classification='JUMP_TABLE'))
    cross = [e for e in edges if e['kind'] == 'CROSS_BOUNDARY']
    overlapping = [p for p in entries if start < p < end]
    closed = bool(returns) and (not issues) and (not indirect) and (not cross) and all((g['classification'] in ('ALIGNMENT_NOP', 'JUMP_TABLE') for g in gaps))
    status = 'OVERLAPPING_ENTRY' if overlapping or 'overlapping instruction streams' in issues else 'AMBIGUOUS_TABLE' if indirect else 'SHARED_TAIL' if cross else 'PROBABLE'
    if not closed and status == 'PROBABLE':
        issues.append('graph not closed or unowned gap')
    return dict(status=status, start=start, end=end if closed else None, size=end - start if closed else None, upper_bound=limit, reachable_end=end, return_offsets=sorted(returns), edges=edges, gaps=gaps, indirect_jumps=indirect, jump_tables=tables, overlapping_entries=overlapping, reasons=sorted(set(issues)), instruction_starts=sorted(seen), proof='CFG_ONLY_NOT_RECOVERED_SOURCE')

def simple_extent(code, start, limit):
    """Next symbol is only a hard upper bound. Traverse both conditional arms.

    A closed, contiguous graph with a reachable RET is PROBABLE, not automatically
    a historical function proof. Manifest review promotes selected extents.
    """
    d = decoder()
    pending = [start]
    seen = {}
    returns = []
    reasons = []
    while pending:
        pos = pending.pop()
        if pos in seen:
            continue
        if not start <= pos < limit:
            reasons.append('control flow escapes symbol bound')
            continue
        ins = next(d.disasm(code[pos:min(limit, pos + 15)], pos, count=1), None)
        if ins is None:
            reasons.append('undecodable instruction')
            continue
        seen[pos] = ins
        if ins.group(cs.CS_GRP_RET):
            returns.append(pos)
            continue
        if ins.mnemonic in ('int', 'int3', 'iret', 'iretw', 'hlt'):
            reasons.append('interrupt or non-return terminator')
            continue
        if ins.group(cs.CS_GRP_JUMP):
            if len(ins.operands) != 1 or ins.operands[0].type != X86_OP_IMM:
                reasons.append('indirect/far jump')
                continue
            pending.append(ins.operands[0].imm)
            if ins.mnemonic == 'jmp':
                continue
        pending.append(pos + ins.size)
    ordered = sorted(seen.values(), key=lambda i: i.address)
    end = start
    for i in ordered:
        if i.address != end:
            reasons.append('gap or overlapping instruction stream')
        end = max(end, i.address + i.size)
    if not returns:
        reasons.append('no reachable return')
    return {
        'status': 'PROBABLE' if not reasons else 'SYMBOL_ONLY_START',
        'start': start,
        'end': end if not reasons else None,
        'size': end - start if not reasons else None,
        'upper_bound': limit,
        'return_offsets': returns,
        'reasons': sorted(set(reasons)),
    }

def function_cards(raw, ne, inventory):
    """Regenerate just the card fields needed for reference extraction from the binary."""
    cards = {}
    for item in inventory['symbols']:
        if item['kind']=='DATA_SYMBOL':
            continue
        segment = ne['segments'][item['segment']-1]
        code = raw[segment['file_offset']:segment['file_offset']+segment['logical_size']]
        start, limit = item['offset'],item['next_symbol_upper_bound']
        peers = [s['offset'] for s in inventory['symbols'] if s['segment']==item['segment']]
        solved = solve(code,start,limit,peers,segment['relocations'],item['segment'])
        e = solved
        if e['end'] is None and e['status'] not in ('SHARED_TAIL','OVERLAPPING_ENTRY','AMBIGUOUS_TABLE'):
            e = simple_extent(code,start,limit)
        end = e['end'] or limit
        spans = sorted((t['table'],t['table']+2*t['count']) for t in solved['jump_tables']
                       if start<=t['table'] and t['table']+2*t['count']<=end)
        disassembly = []
        cursor = start
        for lo, hi in spans+[(end,end)]:
            for ins in md.disasm(code[cursor:lo],cursor):
                operands = ins.op_str
                # Near relative CALL targets wrap IP at the 16-bit segment boundary.
                if ins.mnemonic=='call' and operands.startswith('0x') and int(operands,16)>65535:
                    operands = f'{int(operands,16)&65535:#x}'
                disassembly.append(dict(offset=ins.address,bytes=bytes(ins.bytes).hex(),
                    mnemonic=ins.mnemonic,operands=operands))
            for at in range(lo,hi,2):
                target = struct.unpack_from('<H',code,at)[0]
                disassembly.append(dict(offset=at,bytes=code[at:at+2].hex(),mnemonic='dw',operands=f'offset {target:#x}'))
            cursor = hi
        disassembly.sort(key=lambda d:d['offset'])
        fixups = [dict(f,sites=[p for p in f['sites'] if start<=p<limit])
                  for f in segment['relocations'] if any(start<=p<limit for p in f['sites'])]
        cards[item['name']] = dict(symbol=item['name'],segment=item['segment'],offset=start,
            disassembly=disassembly,known_fixups=fixups,extent=e)
    return cards

def symbol_table(inventory):
    """Original data publics in segment/offset order; no inferred ownership extent."""
    table = collections.defaultdict(list)
    for s in inventory['symbols']:
        if s['kind']=='DATA_SYMBOL' and s['name'] not in ('_end','__end','_edata','__edata'):
            table[s['segment']].append((s['offset'],s['name']))
    for seg in table:
        table[seg].sort()
    return table

def resolve(table, seg, off):
    best = None
    for o,n in table.get(seg,()):
        if o>off:
            break
        best = (n,off-o)
    return best

def function_pairs(functions, symbols, decisions, cards, review_cutoff):
    """Reviewed CONFIRMED/HIGH pairs plus identical non-alias code registrations."""
    pairs = {}
    for key,v in decisions['pairs'].items():
        if v.get('reviewed','') > review_cutoff:
            continue
        if v.get('win16') and v.get('confidence') in ('CONFIRMED','HIGH'):
            unit,seg,off = key.split(':')
            pairs[unit,int(seg,16),int(off,16)] = v['win16']
    for name,r in symbols['code'].items():
        if not r.get('alias_of') and '_'+name in cards:
            pairs.setdefault((r['unit'],r['seg'],r['off']),'_'+name)
    rows = {(r['unit'],r['seg'],r['off']):r for r in functions['functions']}
    return [dict(dos=f'{u}:{s:04X}:{o:04X}',win16=w) for (u,s,o),w in sorted(pairs.items())
            if (u,s,o) in rows and w in cards]


def imm(s):
    return int(s, 0) & 65535 if IMM.fullmatch(s) else None

def mem(s):
    if s.startswith('ptr '):
        s = s[4:]
    m = MEM.fullmatch(s)
    if not m:
        return None
    width, seg, inner = m.groups()
    terms = re.findall('[+-]?\\s*(?:0x[0-9a-f]+|[a-z]+|\\d+)', inner)
    off = 0
    regs = []
    for t in terms:
        sign = -1 if t.strip().startswith('-') else 1
        t = t.replace('+', '').replace('-', '').strip()
        if t in REGS:
            if sign < 0:
                return None
            regs.append(t)
        elif imm(t) is not None:
            off += sign * imm(t)
        else:
            return None
    return (width, seg or ('ss' if 'bp' in regs else 'ds'), regs, off & 65535)

def vnum(n):
    return ('n', n & 65535)

def vseg(s):
    return ('s', s)

class Extractor:
    """Conservative constant propagation for segment, offset and stack-local values.

    CFG joins retain agreement across all predecessors. Calls kill scratch
    registers and any stack locals whose address may have escaped. Selector
    loads are tracked as segments, not counted as data-object references.
    """

    def __init__(self, side, data):
        self.side = side
        self.locals_escape = True
        self.ne, self.raw = (data.ne, data.raw) if side == 'w16' else (None, None)
        self.dgroup = DGROUP if side == 'dos' else W_DGROUP
        self.x = data.x
        self.dg, self.drel = (data.dg, data.dg_relocations)
        self.ptrs = {}
        self.segw = {}
        self.stats = collections.Counter()
        if side == 'dos':
            s = self.x.sections[27]
            base = s.load_linear
            for sg, o in s.relocs:
                at = sg * 16 + o - base
                if 0 <= at <= len(s.data) - 2:
                    target = struct.unpack_from('<H', s.data, at)[0]
                    self.segw[base + at] = target
                    if at >= 2 and 15703 <= target <= DGROUP:
                        self.ptrs[base + at - 2] = (target, struct.unpack_from('<H', s.data, at - 2)[0])
        else:
            for s in self.ne['segments']:
                if s['kind'] != 'DATA':
                    continue
                for f in s['relocations']:
                    t = f['target']
                    typ = f['source_type']
                    if t.get('kind') != 'internal' or t.get('segment') not in W_DATA_SEGS:
                        continue
                    for at in f['sites']:
                        if typ == 3:
                            self.ptrs[s['number'], at] = (t['segment'], t['offset'])
                        if typ == 2:
                            self.segw[s['number'], at] = t['segment']
                            if at >= 2:
                                off = struct.unpack_from('<H', self.raw, s['file_offset'] + at - 2)[0]
                                self.ptrs[s['number'], at - 2] = (t['segment'], off)
        self.ptrs = {k: v for k, v in self.ptrs.items() if k not in self.segw}

    def abskey(self, s, o):
        return s * 16 + o if self.side == 'dos' else (s, o)

    def data_seg(self, s):
        return 15703 <= s <= DGROUP if self.side == 'dos' else s in W_DATA_SEGS

    def ea(self, m, st):
        """Resolve a data effective address, or a BP-local slot, only when grounded."""
        if not m:
            return None
        width, seg, regs, off = m
        if seg == 'ss' and regs == ['bp']:
            return ('local', off)
        sv = st.get(seg)
        if not sv or sv[0] != 's' or (not self.data_seg(sv[1])):
            return None
        idx = False
        known_base = False
        for r in regs:
            rv = st.get(r)
            if rv and rv[0] == 'n':
                off += rv[1]
                known_base = True
            else:
                idx = True
        if idx and (not known_base) and (m[3] == 0):
            return None
        return (sv[1], off & 65535, idx)

    def value(self, op, st, fix=None):
        if fix:
            typ, t = fix
            if typ == 0:
                return None
            if typ == 2:
                return vseg(t['segment'])
            if typ == 5:
                return vnum(t['offset'])
            if typ == 3:
                return ('p', t['segment'], t['offset'])
        if op in REGS:
            return st.get(op)
        n = imm(op)
        if n is not None:
            return vnum(n)
        m = mem(op)
        ea = self.ea(m, st)
        if ea:
            if ea[0] == 'local':
                return st.get(('L', ea[1]))
            if not ea[2]:
                key = self.abskey(*ea[:2])
                if key in self.segw:
                    return vseg(self.segw[key])
        return None

    def instructions(self, unit, row):
        if self.side == 'w16':
            ins = row['disassembly']
            fix = {site: (f['source_type'], f['target']) if f['target'].get('kind') == 'internal' and f['target'].get('segment') in W_DATA_SEGS else (0, {}) for f in row['known_fixups'] for site in f['sites']}
            return (ins, fix)
        base, data = self.x.unit_bytes(unit)
        lin = row['seg'] * 16 + row['off']
        spans = [(t['table'], t['table'] + 2 * t['count']) for t in row.get('jump_tables', [])]
        ins = []
        cursor = lin
        for lo, hi in sorted(spans) + [(lin + row['size'], lin + row['size'])]:
            ins.extend(({
                'offset': i.address,
                'mnemonic': i.mnemonic,
                'operands': i.op_str,
                'bytes': bytes(i.bytes).hex(),
            } for i in md.disasm(data[cursor - base:lo - base], cursor)))
            cursor = hi
        sites = self.x.reloc_sites(unit)
        fix = {site: (2, {'segment': struct.unpack_from('<H', data, site - base)[0]}) for site in sites if lin <= site < lin + row['size']}
        return (ins, fix)

    def step(self, d, state, fix):
        """Transfer one instruction, emitting references before its destinations change."""
        st = dict(state)
        out = []
        mn, ops, at = (d['mnemonic'], d['operands'], d['offset'])
        args = ops.split(', ')
        dst = args[0]
        src = args[1] if len(args) > 1 else ''
        n = len(d['bytes']) // 2
        fx = next((fix[s] for s in range(at, at + n) if s in fix), None)

        def emit(ea, width, kind):
            if ea and ea[0] != 'local' and self.data_seg(ea[0]):
                if ea[0] == self.dgroup and ea[1] < 64:
                    return
                if kind == 'memory' and self.abskey(*ea[:2]) in self.segw:
                    return
                out.append({
                    'seg': ea[0],
                    'off': ea[1],
                    'width': width,
                    'indexed': ea[2] if len(ea) > 2 else False,
                    'site': at,
                    'kind': kind,
                    'instruction': mn + ' ' + ops,
                })
        if mn != 'lea' and (not (fx and fx[0] == 0)):
            for op in args:
                m = mem(op)
                if m:
                    emit(self.ea(m, st), m[0] or ('dword' if mn in ('les', 'lds') else None), 'memory')
        if mn in ('call', 'lcall', 'int'):
            for k in ('ax', 'bx', 'cx', 'dx', 'es', 'P'):
                st.pop(k, None)
            if self.locals_escape:
                for k in list(st):
                    if isinstance(k, tuple):
                        st.pop(k, None)
            return (st, out)
        val = None
        if mn == 'mov':
            val = self.value(src, st, fx)
        elif mn == 'lea':
            e = self.ea(mem(src), st)
            if e and e[0] != 'local' and (not e[2]):
                val = vnum(e[1])
                emit(e, 'address', 'lea')
        elif mn in ('add', 'sub'):
            a = st.get(dst)
            b = imm(src)
            if a and a[0] == 'n' and (b is not None):
                val = vnum(a[1] + (b if mn == 'add' else -b))
        elif mn == 'xor' and src == dst:
            val = vnum(0)
        elif mn in ('inc', 'dec'):
            a = st.get(dst)
            if a and a[0] == 'n':
                val = vnum(a[1] + (1 if mn == 'inc' else -1))
        elif mn in ('les', 'lds'):
            m = mem(src)
            e = self.ea(m, st)
            p = None
            if e:
                if e[0] == 'local':
                    lo = st.get(('L', e[1]))
                    hi = st.get(('L', e[1] + 2 & 65535))
                    if lo and lo[0] == 'n' and hi and (hi[0] == 's'):
                        p = (hi[1], lo[1])
                elif e[0] != 'local' and (not e[2]):
                    p = self.ptrs.get(self.abskey(*e[:2]))
            sg = 'es' if mn == 'les' else 'ds'
            if p:
                st[sg] = vseg(p[0])
                val = vnum(p[1])
                emit((*p, False), 'address', 'load-far-address')
            else:
                st.pop(sg, None)
        if mn == 'push':
            v = self.value(dst, st, fx)
            pending = st.get('P')
            if v and v[0] == 'n' and pending and (pending[0] == 's'):
                emit((pending[1], v[1], False), 'address', 'push-far-address')
            st.pop('P', None)
            if v:
                st['P'] = v
        elif mn == 'pop':
            val = st.pop('P', None)
        elif mn in ('cmp', 'test', 'nop', 'enter', 'leave', 'ret', 'retf') or mn.startswith('j') or mn.startswith('loop'):
            pass
        elif mn not in ('mov', 'lea', 'les', 'lds', 'add', 'sub', 'xor', 'inc', 'dec'):
            val = None
        if mn not in ('push', 'cmp', 'test', 'nop', 'ret', 'retf') and (not mn.startswith('j')) and (not mn.startswith('loop')):
            if dst in REGS:
                st.pop(dst, None)
                if val is not None:
                    st[dst] = val
            elif dst in LOW:
                st.pop(LOW[dst], None)
            else:
                dm = mem(dst)
                e = self.ea(dm, st)
                if e and e[0] == 'local':
                    st.pop(('L', e[1]), None)
                    if mn == 'mov' and val:
                        st['L', e[1]] = val
        if fx and fx[0] in (3, 5):
            emit((fx[1]['segment'], fx[1]['offset'], False), 'address', 'offset-fixup')
        if mn in ('mul', 'imul', 'div', 'idiv'):
            st.pop('ax', None)
            st.pop('dx', None)
        if mn in ('cwd', 'cdq'):
            st.pop('dx', None)
        if mn in ('cbw', 'cwde'):
            st.pop('ax', None)
        if mn == 'xchg':
            for op in args:
                st.pop(LOW.get(op, op), None)
        if mn.startswith(('lods', 'stos', 'movs', 'scas', 'cmps', 'rep')):
            for op in ('ax', 'si', 'di', 'cx'):
                st.pop(op, None)
        if mn.startswith('loop'):
            st.pop('cx', None)
        return (st, out)

    def run(self, unit, row):
        """Reach a fixed point over known branches and switch-table destinations."""
        ins, fix = self.instructions(unit, row)
        if not ins:
            return []
        self.locals_escape = any((d['mnemonic'] == 'lea' and 'bp' in d['operands'] or (d['mnemonic'] == 'mov' and d['operands'].endswith(', bp') and (not d['operands'].startswith('sp,'))) for d in ins))
        by = {d['offset']: d for d in ins}
        succ = {}
        for d in ins:
            mn = d['mnemonic']
            at = d['offset']
            n = len(d['bytes']) // 2
            ss = []
            if mn not in ('ret', 'retf', 'iret', 'hlt', 'dw', 'jmp', 'ljmp') and at + n in by:
                ss.append(at + n)
            if mn.startswith('j') or mn.startswith('loop'):
                v = imm(d['operands'])
                if IMM.fullmatch(d['operands']):
                    v = int(d['operands'], 0)
                if v in by:
                    ss.append(v)
            succ[at] = ss
        if self.side == 'w16':
            for t in row.get('extent', {}).get('jump_tables', []):
                if t['source'] in succ:
                    succ[t['source']].extend((tgt for tgt in t['targets'] if tgt in by))
        else:
            base, data = self.x.unit_bytes(unit)
            for t in row.get('jump_tables', []):
                if t['site'] in succ:
                    succ[t['site']].extend((row['seg'] * 16 + struct.unpack_from('<H', data, t['table'] + 2 * k - base)[0] for k in range(t['count'])))
                    succ[t['site']] = [dst for dst in succ[t['site']] if dst in by]
        states = {ins[0]['offset']: {'ds': vseg(self.dgroup), 'ss': vseg(self.dgroup)}}
        q = collections.deque(states)
        iterations = 0
        while q:
            at = q.popleft()
            st, _ = self.step(by[at], states[at], fix)
            iterations += 1
            if iterations > 100000:
                raise RuntimeError('CFG did not converge')
            for dst in succ[at]:
                if dst in states:
                    new = {k: v for k, v in states[dst].items() if st.get(k) == v}
                else:
                    new = dict(st)
                if dst not in states or new != states[dst]:
                    states[dst] = new
                    q.append(dst)
        out = []
        for d in ins:
            if d['offset'] in states:
                _, events = self.step(d, states[d['offset']], fix)
                out.extend(events)
        self.stats['instructions'] += len(ins)
        self.stats['reachable'] += len(states)
        self.stats.update((e['kind'] for e in out))
        return out


class Data:
    """Binary bytes and registry boundaries; spacing never silently becomes a C size."""

    def __init__(self, dos_raw, win_raw, inventory, symbols):
        self.x = DosImage(dos_raw)
        self.ne, self.raw = parse_ne(win_raw), win_raw
        self.s27 = self.x.sections[27]
        self.dg = self.s27.data[DGROUP*16-self.s27.load_linear:]
        self.dg_relocations = {s*16+o-DGROUP*16 for s,o in self.s27.relocs}
        self.drel = {s*16+o for s,o in self.s27.relocs}
        self.wrel = {s['number']:{site for f in s['relocations'] for site in f['sites']} for s in self.ne['segments']}
        self.ws = {s['name']:s for s in inventory['symbols'] if s['kind']=='DATA_SYMBOL'}
        self.wtable = symbol_table(inventory)
        self.symbols = symbols
        self.dn = {(r['seg'],r['off']):n for n,r in symbols['data'].items() if not r.get('alias_of')}
        self.dtable = collections.defaultdict(list)
        for s,o in self.dn:
            self.dtable[s].append(o)
        for s in self.dtable:
            self.dtable[s].sort()
        self.known = {(r['seg'],r['off']):('_'+n,0) for n,r in symbols['data'].items()
                      if not r.get('alias_of') and '_'+n in self.ws}

    def dbytes(self, d, size):
        at = d[0] * 16 + d[1] - self.s27.load_linear
        return self.s27.data[at:at + size] if at >= 0 else b''

    def wbytes(self, w, size):
        s = self.ne['segments'][w[0] - 1]
        return self.raw[s['file_offset'] + w[1]:s['file_offset'] + w[1] + size] if w[1] + size <= s['logical_size'] else b''

    def wspan(self, name):
        s = self.ws[name]
        offsets = [o for o, n in self.wtable[s['segment']]]
        ix = bisect.bisect_right(offsets, s['offset'])
        return offsets[ix] - s['offset'] if ix < len(offsets) else None

    def dspan(self, d):
        offsets = self.dtable[d[0]]
        ix = bisect.bisect_right(offsets, d[1])
        return offsets[ix] - d[1] if ix < len(offsets) else None

    def initial(self, d, w, size):
        if not size or size < 2 or size > 32768:
            return None
        db = self.dbytes(d, size)
        wb = self.wbytes(w, size)
        if len(db) != size or len(wb) != size:
            return None
        if any((d[0] * 16 + d[1] + i in self.drel for i in range(size))):
            return None
        if any((w[1] + i in self.wrel[w[0]] for i in range(size))):
            return None
        if db == wb and any(db):
            return {
                'bytes': size,
                'nonzero_bytes': sum((b != 0 for b in db)),
                'distinct_bytes': len(set(db)),
                'prefix': db[:24].hex(),
                'substantial': size >= 4 and (len(set(db)) >= 3 or sum((b != 0 for b in db)) >= 4),
            }
        return None

def extract_references(data, functions, pairs, cards):
    """Extract fresh ordered events for the independently regenerated function pairs."""
    rows = {(r['unit'],r['seg'],r['off']):r for r in functions['functions']}
    dos,win = Extractor('dos',data),Extractor('w16',data)
    refs = []
    for pair in pairs:
        u,s,o = pair['dos'].split(':')
        dr = dos.run(u,rows[u,int(s,16),int(o,16)])
        wr = win.run(None,cards[pair['win16']])
        rr,we = [],[]
        for e in wr:
            r = resolve(data.wtable,e['seg'],e['off'])
            if r:
                rr.append([*r,e['width'],e['indexed']])
                we.append(dict(e,name=r[0],delta=r[1]))
        refs.append(dict(dos=pair['dos'],win16=pair['win16'],
            dos_refs=[[e['seg'],e['off'],e['width'],e['indexed']] for e in dr],
            w16_refs=rr,dos_events=dr,w16_events=we))
    return refs,dict(dos=dos.stats,win16=win.stats)
