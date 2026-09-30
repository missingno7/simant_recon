"""d2a.py MODULE.json -> MASM 5.10 draft of a genuine-assembly overlay module.

Recursive descent from the module's entry points, symbolic operands:
  * branch/call targets -> labels,  far calls to own segment -> far ptr labels
  * DGROUP absolute operands -> registered data names (extrn in _DATA)
  * relocated segment immediates -> segment/group names
  * cs: operands -> code labels (+displacement for self-modified operands)
  * root / other-overlay far calls -> registered code names (extrn far)
Unreached bytes are reported; code-segment data comes only from the module config.
"""
import json, struct, sys
from pathlib import Path
sys.path.insert(0, 'tools')
import exe, symbols as symmod
from capstone import Cs, CS_ARCH_X86, CS_MODE_16
from capstone import x86_const as X

md = Cs(CS_ARCH_X86, CS_MODE_16)
md.detail = True
DGROUP = 0x55B3

REG = {X.X86_REG_AX: 'ax', X.X86_REG_BX: 'bx', X.X86_REG_CX: 'cx', X.X86_REG_DX: 'dx', X.X86_REG_SI: 'si',
       X.X86_REG_DI: 'di', X.X86_REG_BP: 'bp', X.X86_REG_SP: 'sp', X.X86_REG_AL: 'al', X.X86_REG_AH: 'ah',
       X.X86_REG_BL: 'bl', X.X86_REG_BH: 'bh', X.X86_REG_CL: 'cl', X.X86_REG_CH: 'ch', X.X86_REG_DL: 'dl',
       X.X86_REG_DH: 'dh', X.X86_REG_CS: 'cs', X.X86_REG_DS: 'ds', X.X86_REG_ES: 'es', X.X86_REG_SS: 'ss'}
LOOPS = ('loop', 'loope', 'loopne', 'jcxz')
SIZE = {1: 'byte ptr', 2: 'word ptr', 4: 'dword ptr'}


def hx(v, bits=16):
    v &= (1 << bits) - 1
    s = '%X' % v
    if s[0] in 'ABCDEF':
        s = '0' + s
    return s + 'h' if v > 9 else str(v)


class Module:
    def __init__(self, cfg):
        self.cfg = cfg
        self.x = exe.load()
        self.unit = cfg['unit']
        self.frame = int(cfg['frame'], 16)
        self.start = int(cfg['start'], 16)          # linear
        self.end = int(cfg['end'], 16)              # linear, exclusive
        base, data = self.x.unit_bytes(self.unit)
        self.data = data[self.start - base:self.end - base]
        self.o0 = self.start - self.frame * 16      # frame offset of first byte
        self.relocs = self.x.reloc_sites(self.unit)
        self.vec = {v.offset: v for v in self.x.vectors}
        s = symmod.load()
        self.code_names = {}
        for n, r in s['code'].items():
            if not r.get('alias_of'):
                self.code_names[(r['unit'], r['seg'], r['off'])] = n
        for n, r in s['runtime'].items():
            self.code_names.setdefault((r['unit'], r['seg'], r['off']), n)
        self.data_names = {r['off']: n for n, r in s['data'].items()
                           if r['seg'] == DGROUP and not r.get('alias_of')}
        self.far_data = {(r['seg'], r['off']): n for n, r in s['data'].items() if not r.get('alias_of')}
        self.entries = {int(k, 16): v for k, v in cfg['entries'].items()}
        self.datas = [(int(a, 16), int(b, 16), lab, fmt) for a, b, lab, fmt in cfg.get('data', [])]
        self.extra = [int(a, 16) for a in cfg.get('extra_code', [])]
        self.dg_ranges = [(int(a, 16), int(b, 16)) for a, b in cfg.get('dgroup_symbolic', [])]
        self.labels = {}                            # off -> name
        self.insn = {}                              # off -> capstone insn
        self.extrn_data = {}                        # name -> type
        self.extrn_code = {}
        self.missing_data = set()
        self.problems = []
        self.padnop = set()

    # ----------------------------------------------------------------------------------
    def in_mod(self, off):
        return self.o0 <= off < self.o0 + len(self.data)

    def in_data(self, off):
        for a, b, lab, fmt in self.datas:
            if a <= off < b:
                return (a, b, lab, fmt)
        return None

    def decode(self, off):
        b = self.data[off - self.o0:off - self.o0 + 16]
        for i in md.disasm(b, off):
            return i
        return None

    def trace(self):
        work = list(self.entries) + self.extra
        while work:
            off = work.pop()
            while True:
                if off in self.insn or not self.in_mod(off):
                    break
                if self.in_data(off):
                    self.problems.append(f'flow into data at {off:04X}')
                    break
                i = self.decode(off)
                if i is None:
                    self.problems.append(f'undecodable at {off:04X}')
                    break
                self.insn[off] = i
                b0 = i.bytes[0]
                grp = i.groups
                nxt = off + i.size
                if X.X86_GRP_JUMP in grp or X.X86_GRP_CALL in grp or i.mnemonic in LOOPS:
                    op = i.operands[0] if i.operands else None
                    if op is not None and op.type == X.X86_OP_IMM and b0 not in (0x9A, 0xEA):
                        t = op.imm & 0xFFFF
                        if self.in_mod(t):
                            work.append(t)
                            self.labels.setdefault(t, f'L{t:04X}')
                        else:
                            self.problems.append(f'branch out of module at {off:04X} -> {t:04X}')
                    if b0 == 0x9A:
                        toff, tseg = struct.unpack_from('<HH', i.bytes, 1)
                        if tseg == self.frame and self.frame * 16 + off + 3 in self.relocs and self.in_mod(toff):
                            work.append(toff)
                    if i.mnemonic in ('jmp', 'ljmp'):
                        break
                if i.mnemonic in ('ret', 'retf', 'iret'):
                    break
                off = nxt

    # ----------------------------------------------------------------------------------
    def reloc_in(self, i, k):
        return self.frame * 16 + i.address + k in self.relocs

    def seg_name(self, v):
        if v == self.frame:
            return self.cfg['segname']
        if v == DGROUP:
            return 'DGROUP'
        return None

    def dsym(self, off, size):
        n = self.data_names.get(off)
        if n is None:
            self.missing_data.add(off)
            n = f'g_{off:04X}'
        name = '_' + n
        self.extrn_data.setdefault(name, 'byte')
        return name

    def code_label(self, t):
        """label expression for a code-segment offset t"""
        if t in self.labels:
            return self.labels[t]
        d = self.in_data(t)
        if d:
            return d[2] if t == d[0] else f'{d[2]}+{t - d[0]}'
        # inside an instruction?
        for s in range(t, t - 8, -1):
            if s in self.insn:
                if s not in self.labels:
                    self.labels[s] = f'L{s:04X}'
                return f'{self.labels[s]}+{t - s}' if t != s else self.labels[s]
        self.labels[t] = f'L{t:04X}'
        return self.labels[t]

    def is_dg(self, disp):
        return any(a <= disp < b for a, b in self.dg_ranges)

    def mem(self, i, op, first_pass):
        m = op.mem
        seg = REG.get(m.segment, '')
        base = REG.get(m.base, '')
        idx = REG.get(m.index, '')
        disp = m.disp & 0xFFFF
        size = SIZE.get(op.size, '')
        if i.mnemonic in ('les', 'lds'):
            size = 'dword ptr'
        if i.mnemonic in ('lea',):
            size = ''
        if i.mnemonic in ('lcall', 'ljmp'):
            size = 'dword ptr'
        if i.mnemonic in ('call', 'jmp') and op.size == 2:
            size = 'word ptr'
        regs = '+'.join(r for r in (base, idx) if r)
        if seg == 'cs' and regs and m.disp == 0:
            return f'{size} cs:[{regs}]'.strip()
        if seg == 'cs':
            lab = self.code_label(disp) if not first_pass else 'X'
            inner = f'[{regs}+{lab}]' if regs else lab
            return f'{size} cs:{inner}'.strip()
        default_ds = (not seg or seg == 'ds') and base not in ('bp',)
        if not regs:
            if (not seg or seg in ('ds', 'es', 'ss')) and self.is_dg(disp):
                return f'{size} {seg + ":" if seg else ""}{self.dsym(disp, op.size)}'.strip()
            return f'{size} {seg or "ds"}:[{hx(disp)}]'.strip()
        if default_ds and disp and self.is_dg(disp):
            return f'{size} {seg + ":" if seg else ""}[{regs}+{self.dsym(disp, op.size)}]'.strip()
        s = f'[{regs}'
        if m.disp:
            dv = m.disp
            if dv < 0 or (dv >= 0x8000 and False):
                s += f'-{hx(-dv)}'
            else:
                s += f'+{hx(dv)}'
        s += ']'
        return f'{size} {seg + ":" if seg else ""}{s}'.strip()

    def fmt(self, i, first_pass=False):
        b0 = i.bytes[0]
        mn = i.mnemonic
        pfx = ''
        # opcode-named specials
        if b0 == 0x98:
            return 'cbw'
        if b0 == 0x99:
            return 'cwd'
        if mn == 'xlatb':
            for pb in i.prefix:
                if pb in (0x26, 0x2E, 0x36, 0x3E):
                    return 'xlat byte ptr ' + {0x26: 'es', 0x2E: 'cs', 0x36: 'ss', 0x3E: 'ds'}[pb] + ':[bx]'
            return 'xlat'
        # string instructions
        if mn.rstrip('bw') in ('lods', 'stos', 'movs', 'cmps', 'scas') or mn.startswith('rep'):
            parts = mn.split()
            core = parts[-1]
            rep = ' '.join(parts[:-1])
            segov = None
            for pb in i.prefix:
                if pb in (0x26, 0x2E, 0x36, 0x3E):
                    segov = {0x26: 'es', 0x2E: 'cs', 0x36: 'ss', 0x3E: 'ds'}[pb]
            if segov:
                sz = 'byte ptr' if core.endswith('b') else 'word ptr'
                c = core[:-1]
                if c == 'lods':
                    return f'{rep} lods {sz} {segov}:[si]'.strip()
                if c == 'movs':
                    return f'{rep} movs {sz} es:[di], {sz} {segov}:[si]'.strip()
                if c == 'cmps':
                    return f'{rep} cmps {sz} {segov}:[si], {sz} es:[di]'.strip()
                self.problems.append(f'segov string op at {i.address:04X}')
            return f'{rep} {core}'.strip()
        ops = []
        for k, op in enumerate(i.operands):
            if op.type == X.X86_OP_REG:
                ops.append(REG[op.reg])
            elif op.type == X.X86_OP_IMM:
                v = op.imm
                if X.X86_GRP_JUMP in i.groups or X.X86_GRP_CALL in i.groups or mn in LOOPS:
                    if b0 in (0x9A, 0xEA):
                        return self.farbranch(i)
                    t = v & 0xFFFF
                    lab = self.labels.get(t, f'L{t:04X}')
                    if mn == 'jmp':
                        if b0 == 0xEB:
                            short_ok_fwd = t > i.address
                            nxt = i.address + 2
                            if short_ok_fwd and self.in_mod(nxt) and self.data[nxt - self.o0] == 0x90 \
                                    and not (nxt in self.labels) and not (nxt in self.entries):
                                self.padnop.add(nxt)
                                return f'jmp {lab}'           # MASM pads forward jmp with NOP
                            return f'jmp short {lab}' if t > i.address else f'jmp {lab}'
                        if b0 == 0xE9:
                            rel = t - (i.address + 2)
                            if -128 <= rel <= 127 or t > i.address:
                                return f'jmp near ptr {lab}'
                            return f'jmp {lab}'
                    if mn == 'call':
                        return f'call near ptr {lab}'
                    return f'{mn} {lab}'
                # segment relocation?
                sz = op.size or 2
                pos = i.size - sz if k == len(i.operands) - 1 else None
                if pos is not None and sz == 2 and self.reloc_in(i, pos):
                    sn = self.seg_name(v & 0xFFFF)
                    if sn is None:
                        self.problems.append(f'unknown segment immediate {v:04X} at {i.address:04X}')
                        sn = hx(v)
                    ops.append(sn)
                else:
                    bits = 8 if sz == 1 else 16
                    if b0 in (0x83, 0x6B) or (b0 in (0x80, 0x82, 0xC0, 0xC1, 0xD0, 0xD1)):
                        vv = v & ((1 << bits) - 1)
                        if b0 == 0x83:
                            vv = v & 0xFF
                            ops.append(hx(v & 0xFFFF) if not (v & 0x8000) else ('-' + hx((-v) & 0xFFFF)))
                            continue
                        ops.append(hx(vv, bits))
                    else:
                        ops.append(hx(v, bits))
            elif op.type == X.X86_OP_MEM:
                if mn in ('lcall', 'ljmp'):
                    return f'{"call" if mn == "lcall" else "jmp"} {self.mem(i, op, first_pass)}'
                ops.append(self.mem(i, op, first_pass))
        # shifts by 1: capstone gives imm 1 for D0/D1
        if mn in ('lcall', 'ljmp'):
            return self.farbranch(i)
        if b0 in (0x86, 0x87) and (i.bytes[1] >> 6) == 3:
            ops = ops[::-1]           # MASM puts the first operand in the reg field
        m2 = {'retf': 'retf', 'ret': 'retn', 'iret': 'iret'}.get(mn, mn)
        if mn in ('ret', 'retf') and i.operands:
            return f'{m2} {ops[0]}'
        # memory operand needs size only when ambiguous; keep ptr always (harmless)
        return (m2 + ' ' + ', '.join(ops)).strip()

    def farbranch(self, i):
        b0 = i.bytes[0]
        verb = 'call' if b0 == 0x9A else 'jmp'
        toff, tseg = struct.unpack_from('<HH', i.bytes, 1)
        if not self.reloc_in(i, 3):
            self.problems.append(f'unrelocated far branch at {i.address:04X}')
            return f'{verb} far ptr ???'
        if tseg == self.frame and self.in_mod(toff):
            lab = self.labels.get(toff) or self.entry_name(toff)
            return f'{verb} far ptr {lab}'
        if tseg == self.frame:
            key = (self.unit, tseg, toff)
        elif tseg == exe.MANAGER_SEG and toff in self.vec:
            v = self.vec[toff]
            key = (v.unit, v.target_seg, v.target_off)
        elif tseg < 0x3126:
            key = ('root', tseg, toff)
        else:
            key = (self.unit, tseg, toff)
        n = self.code_names.get(key)
        if n is None:
            n = f'f_{tseg:04X}_{toff:04X}'
            self.problems.append(f'unnamed far target {key} at {i.address:04X}')
        cname = n if n.startswith('_') else '_' + n
        self.extrn_code[cname] = 'far'
        return f'{verb} far ptr {cname}'

    def entry_name(self, off):
        e = self.entries.get(off)
        if e:
            return '_' + e['name']
        return f'L{off:04X}'

    # ----------------------------------------------------------------------------------
    def emit(self):
        self.trace()
        for off, e in self.entries.items():
            self.labels[off] = '_' + e['name']
        for a, b, lab, fmt in self.datas:
            self.labels.setdefault(a, lab)
        # first pass formatting to create cs: labels
        for off in sorted(self.insn):
            self.fmt(self.insn[off], first_pass=False)
        lines = []
        cov = bytearray(len(self.data))
        for off, i in self.insn.items():
            for k in range(i.size):
                cov[off - self.o0 + k] = 1
        for a, b, lab, fmt in self.datas:
            for k in range(a, b):
                cov[k - self.o0] = 2
        for k in self.padnop:
            cov[k - self.o0] = 3
        gaps = []
        k = 0
        while k < len(cov):
            if cov[k] == 0:
                s = k
                while k < len(cov) and cov[k] == 0:
                    k += 1
                gaps.append((s + self.o0, k + self.o0))
            else:
                k += 1
        seg = self.cfg['segname']
        out = []
        out.append(f'; {self.cfg.get("title", "")}')
        out.append(f'; Overlay section {self.unit}, code frame {self.frame:04X}, linear '
                   f'{self.start:05X}-{self.end:05X}.')
        for c in self.cfg.get('comment', []):
            out.append('; ' + c)
        out.append('')
        out.append('_DATA\tsegment word public \'DATA\'')
        body_idx = len(out)
        out.append('_DATA\tends')
        out.append('DGROUP\tgroup\t_DATA')
        out.append('')
        out.append(f'{seg}\tsegment word public \'CODE\'')
        out.append(f'\tassume\tcs:{seg}, ds:DGROUP')
        out.append('')
        pubs = [e for e in self.entries.values() if e.get('public', True)]
        for e in sorted(pubs, key=lambda e: e['name']):
            out.append(f'\tpublic\t_{e["name"]}')
        out.append('')
        cur_proc = None
        off = self.o0
        end = self.o0 + len(self.data)
        if self.o0 & 0xF and self.cfg.get('org', True):
            pass
        while off < end:
            if off in self.entries:
                e = self.entries[off]
                if cur_proc:
                    out.append(f'{cur_proc}\tendp')
                    out.append('')
                if e.get('comment'):
                    out.append('; ' + e['comment'])
                cur_proc = '_' + e['name']
                out.append(f'{cur_proc}\tproc\t{e.get("kind", "far")}')
            d = self.in_data(off)
            if d and off == d[0]:
                a, b, lab, fmt = d
                out.extend(self.emit_data(a, b, lab, fmt))
                off = b
                continue
            if off in self.padnop:
                off += 1
                continue
            if off in self.insn:
                i = self.insn[off]
                lab = self.labels.get(off)
                if lab and not (off in self.entries):
                    out.append(f'{lab}:')
                out.append('\t' + self.fmt(i))
                off += i.size
                continue
            # unreached byte
            g = next(g for g in gaps if g[0] <= off < g[1])
            out.append(f'; ??? unreached bytes {g[0]:04X}-{g[1]:04X}: '
                       + self.data[g[0] - self.o0:g[1] - self.o0].hex())
            off = g[1]
        if cur_proc:
            out.append(f'{cur_proc}\tendp')
        out.append('')
        out.append(f'{seg}\tends')
        out.append('\tend')
        ext = []
        for n in sorted(self.extrn_data):
            ext.append(f'\textrn\t{n}:byte')
        out[body_idx:body_idx] = ext
        # far externs before code segment
        cx = [f'\textrn\t{n}:far' for n in sorted(self.extrn_code)]
        i0 = out.index(f'{seg}\tsegment word public \'CODE\'')
        out[i0:i0] = cx + ([''] if cx else [])
        return '\n'.join(out) + '\n', gaps

    def emit_data(self, a, b, lab, fmt):
        raw = self.data[a - self.o0:b - self.o0]
        out = []
        if fmt.startswith('text:'):
            return [lab + '	label	byte'] + Path(fmt[5:]).read_text().rstrip().split(chr(10))
        if fmt.startswith('dup'):
            v = raw[0]
            assert all(c == v for c in raw), 'dup data not uniform'
            out.append(f'{lab}\tdb\t{b - a} dup ({hx(v, 8)})')
        elif fmt == 'words':
            vals = struct.unpack(f'<{(b - a) // 2}H', raw)
            out.append(f'{lab}\tdw\t' + ', '.join(hx(v) for v in vals[:8]))
            for k in range(8, len(vals), 8):
                out.append('\tdw\t' + ', '.join(hx(v) for v in vals[k:k + 8]))
        elif fmt == 'labels':      # table of near code offsets
            vals = struct.unpack(f'<{(b - a) // 2}H', raw)
            out.append(f'{lab}\tdw\t' + ', '.join(self.code_label(v) for v in vals))
        else:
            out.append(f'{lab}\tdb\t' + ', '.join(hx(v, 8) for v in raw[:12]))
            for k in range(12, len(raw), 12):
                out.append('\tdb\t' + ', '.join(hx(v, 8) for v in raw[k:k + 12]))
        return out


if __name__ == '__main__':
    cfg = json.loads(Path(sys.argv[1]).read_text())
    m = Module(cfg)
    text, gaps = m.emit()
    outp = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(sys.argv[1]).with_suffix('.asm')
    outp.write_text(text)
    print('wrote', outp, 'insns', len(m.insn), 'gaps', [(f'{a:04X}', f'{b:04X}') for a, b in gaps])
    for p in m.problems[:40]:
        print('  problem:', p)
    if m.missing_data:
        print('  unregistered DGROUP data:', ' '.join(f'{o:04X}' for o in sorted(m.missing_data)))
