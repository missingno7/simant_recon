"""Isolated 16-bit differential execution; never writes historical claims/images.

The original is read from the hash-locked EXE. A compiler-produced whole module
is symbolically linked into a separate scratch code arena in the candidate VM.
Non-target module entries delegate to original helpers, never scaffold bodies.
Modeled boundaries are explicit and cannot alone grant behavioral acceptance.
"""
from __future__ import annotations

import copy
import hashlib
import json
import struct
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'build/behavior/deps'))
try:
    import unicorn as uc
    from unicorn import x86_const as xr
except ImportError as exc:
    raise RuntimeError('Install pinned Unicorn 2.1.4 into build/behavior/deps; see docs/behavioral-proof.md') from exc
import exe
import functions
import match
import modctx
import modules

REGS = {n: getattr(xr, 'UC_X86_REG_' + n.upper()) for n in
        ('ax','bx','cx','dx','si','di','bp','sp','ip','cs','ds','es','ss','eflags')}
STACK_SEG = 0x8000
CODE_SEG = 0x9000
SENTINEL = (0xF000, 0x8000)
SENTINEL_LINEAR = SENTINEL[0] * 16 + SENTINEL[1]
MEMORY_SIZE = 0x110000
HARNESS_SOURCE = Path(__file__).read_bytes()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def symbol(name):
    for spelling in (name, '_' + name, '@' + name):
        if spelling in match.symbols():
            return match.symbols()[spelling]
    raise KeyError(f'unregistered oracle symbol: {name}')


def symbol_address(name):
    s = symbol(name)
    return s['seg'] * 16 + s['off']


def words(*values):
    return struct.pack('<' + 'H' * len(values), *(v & 65535 for v in values))


@dataclass(frozen=True)
class Range:
    name: str
    address: int
    size: int


@dataclass(frozen=True)
class Callback:
    stack_words: int
    handler: Callable | None = None
    register_args: tuple[str, ...] = ()
    pop: int = 0
    project: Callable | None = None


@dataclass(frozen=True)
class FormatCursorView:
    """Reviewed private CRT stream: cursor far ptr, capacity, base far ptr.

    Only stack-home identity is abstracted. Cursor advancement and remaining
    capacity stay observable; the original raw bytes remain in the report.
    """
    name: str
    address: int
    proof_path: str
    proof_sha256: str


@dataclass
class Case:
    label: str
    args: list[int] = field(default_factory=list)
    writes: list[tuple[int, bytes]] = field(default_factory=list)
    observe: list[Range] = field(default_factory=list)
    callbacks: dict[str, Callback] = field(default_factory=dict)
    return_kind: str = 's16'
    registers: dict[str, int] = field(default_factory=dict)
    state: dict = field(default_factory=dict)
    metadata: dict = field(default_factory=dict)
    io_reads: dict[int, int | Callable] = field(default_factory=dict)
    max_instructions: int = 1_000_000
    max_blocks: int = 200_000
    observe_at_calls: bool = True
    callee_pop: int = 0
    stack_bytes: int = 0xF00
    format_cursor_views: list[FormatCursorView] = field(default_factory=list)


class ExecutionError(RuntimeError):
    pass


class ExecutionBinder(match.Binder):
    """Normal scratch linking of defined publics, separate from exact placement.

    Existing Binder resolves registered C publics to their historical addresses.
    This execution-only linker locates code publics actually defined in the
    candidate object at the scratch frame, so same-module relative calls remain
    valid. Objects and all production binding/acceptance code remain untouched.
    """
    def resolve(self, fix, pub_off):
        resolved = super().resolve(fix, pub_off)
        if resolved[0] == 'code':
            for p in self.obj.publics + getattr(self.obj, 'local_publics', []):
                if p['segment'] == self.segment and p['name'] == fix['target']:
                    return ('code', self.t.unit, self.t.seg, p['offset'])
        return resolved


class Machine:
    def __init__(self, pair, candidate=False):
        self.pair, self.candidate = pair, candidate
        self.cpu = uc.Uc(uc.UC_ARCH_X86, uc.UC_MODE_16)
        self.cpu.mem_map(0, MEMORY_SIZE)
        x = exe.load()
        self.cpu.mem_write(0, x.image)
        resident = x.sections[27]
        self.cpu.mem_write(resident.load_linear, resident.data)
        if pair.function['unit'] != 'root':
            s = x.sections[int(pair.function['unit'][1:])]
            self.cpu.mem_write(s.load_linear, s.data)
        self.loaded_units = set() if pair.function['unit'] == 'root' else {pair.function['unit']}
        self.overlay_frames = []
        if candidate:
            self.cpu.mem_write(CODE_SEG * 16, pair.code)
        self.dirty = {}
        self.stack_poison_window = None
        self.cursor_proofs = {}
        self.active = False
        self.cpu.hook_add(uc.UC_HOOK_MEM_WRITE, self._on_write)
        self.cpu.hook_add(uc.UC_HOOK_BLOCK, self._on_block)
        self.cpu.hook_add(uc.UC_HOOK_INTR, self._on_interrupt)
        self.cpu.hook_add(uc.UC_HOOK_INSN, self._on_in, None, 1, 0, xr.UC_X86_INS_IN)
        self.cpu.hook_add(uc.UC_HOOK_INSN, self._on_out, None, 1, 0, xr.UC_X86_INS_OUT)

    def reg(self, name):
        return self.cpu.reg_read(REGS[name.lower()])

    def set_reg(self, name, value):
        self.cpu.reg_write(REGS[name.lower()], value & (0xFFFFFFFF if name.lower() == 'eflags' else 65535))

    def read(self, address, size):
        return bytes(self.cpu.mem_read(address, size))

    def word(self, address):
        return int.from_bytes(self.read(address, 2), 'little')

    def set_word(self, address, value):
        self.write(address, words(value))

    def _remember(self, address, size):
        old = self.read(address, size)
        for i, value in enumerate(old):
            self.dirty.setdefault(address + i, value)

    def write(self, address, data):
        data = bytes(data)
        self._remember(address, len(data))
        if self.active:
            self._record_write(address, len(data))
        self.cpu.mem_write(address, data)

    def _record_write(self, address, size):
        for at in range(address, address + size):
            if not self.stack_bounds[0] <= at < self.stack_bounds[1]:
                self.written.add(at)
                self.effect_initial.setdefault(at, self.read(at, 1)[0])

    def semantic_effects(self, addresses):
        """Return bytes plus typed views; never apply an arbitrary byte mask."""
        addresses = set(addresses)
        views = {}
        for view in self.case.format_cursor_views:
            cells = set(range(view.address, view.address + 10))
            if not addresses.intersection(cells):
                continue
            cur, cseg, remaining, start, sseg = struct.unpack('<5H', self.read(view.address,10))
            cursor, base = cseg * 16 + cur, sseg * 16 + start
            lower, upper = self.stack_bounds
            if not lower <= base < upper and not lower <= cursor < upper:
                # A formatter may also target a real heap buffer. Its actual
                # address remains observable; no stack-home view applies.
                continue
            if not (lower <= base <= cursor < upper and cseg == sseg == self.initial_registers['ss']):
                raise ExecutionError(f'{view.name}: private formatter pointer is not a valid call-stack reference')
            views[view.name] = {'cursor_advance': cursor-base, 'remaining_capacity': remaining,
                                'buffer_lifetime': 'private formatter invocation'}
            addresses.difference_update(cells)
        return [(at,self.read(at,1)[0]) for at in sorted(addresses)], views

    def _validate_cursor_views(self):
        used = set()
        for view in self.case.format_cursor_views:
            path = (ROOT/view.proof_path).resolve()
            path.relative_to(ROOT)
            if not view.proof_path.startswith('evidence/behavior/runtime/'):
                raise ExecutionError('formatter view requires retained runtime evidence')
            if view.proof_sha256 not in self.cursor_proofs:
                raw = path.read_bytes()
                if digest(raw) != view.proof_sha256:
                    raise ExecutionError('formatter cursor proof changed')
                proof = json.loads(raw)
                if (proof.get('schema') != 'behavior-format-cursor-proof-v1'
                        or proof.get('review',{}).get('status') != 'APPROVED'
                        or proof.get('review',{}).get('reviewer') != 'root'
                        or proof.get('oracle_sha256') != self.pair.identity['oracle_sha256']):
                    raise ExecutionError('unreviewed or unrelated formatter cursor proof')
                self.cursor_proofs[view.proof_sha256] = proof
            proof = self.cursor_proofs[view.proof_sha256]
            record = next((r for r in proof['records'] if r['name']==view.name and r['address']==view.address),None)
            if (record is None or record.get('size')!=10
                    or record.get('private_owner') not in ('sprintf.c','vsprintf.c')
                    or record.get('overwrite_before_read_proven') is not True):
                raise ExecutionError('formatter view lacks matching private lifetime proof')
            cells=set(range(view.address,view.address+10))
            if used.intersection(cells):raise ExecutionError('overlapping formatter views')
            used.update(cells)

    def _on_write(self, cpu, access, address, size, value, userdata):
        self._remember(address, size)
        if self.active:
            self._record_write(address, size)

    def _on_interrupt(self, cpu, number, userdata):
        self.error = f'unmodeled interrupt {number:02X}'
        cpu.emu_stop()

    def _on_in(self, cpu, port, size, userdata):
        provider = self.case.io_reads.get(port)
        if provider is None:
            self.error = f'unmodeled IN port {port:04X}'
            cpu.emu_stop()
            return 0
        value = provider(self, port, size) if callable(provider) else provider
        value &= (1 << (size * 8)) - 1
        self.io.append(('in', port, size, value))
        return value

    def _on_out(self, cpu, port, size, value, userdata):
        self.io.append(('out', port, size, value))

    def _return_far(self, pop=0):
        stack = self.reg('ss') * 16 + self.reg('sp')
        ip, cs = struct.unpack('<HH', self.read(stack, 4))
        self.set_reg('sp', self.reg('sp') + 4 + pop)
        self.set_reg('cs', cs)
        self.set_reg('ip', ip)
        self.resume = True
        self.cpu.emu_stop()

    def _jump(self, seg, off):
        self.set_reg('cs', seg)
        self.set_reg('ip', off)
        self.resume = True
        self.cpu.emu_stop()

    def _on_block(self, cpu, address, size, userdata):
        self.blocks += 1
        if self.blocks > self.case.max_blocks:
            self.error = 'basic-block execution budget exceeded'
            cpu.emu_stop()
            return
        if address == SENTINEL_LINEAR:
            self.completed = True
            cpu.emu_stop()
            return
        if self.overlay_frames and address == self.overlay_frames[-1]['return']:
            saved = self.overlay_frames.pop()
            for base, data in saved['images']:
                self.cpu.mem_write(base, data)
                self.cpu.ctl_remove_cache(base, base + len(data))
            self.loaded_units = saved['loaded']
            # Re-enter at the restored address: the current translated block
            # may have been decoded from the replacement overlay.
            self._jump(self.reg('cs'), self.reg('ip'))
            return
        hit = self.callback_addresses.get(address)
        if hit:
            name, spec = hit
            stack = self.reg('ss') * 16 + self.reg('sp') + 4
            args = [self.reg(r) for r in spec.register_args]
            args += list(struct.unpack('<' + 'H' * spec.stack_words, self.read(stack, 2 * spec.stack_words)))
            projected = spec.project(self, args) if spec.project else args
            entry = {r.name: self.read(r.address, r.size).hex() for r in self.case.observe} if self.case.observe_at_calls else {}
            changes = [(at,self.read(at,1)[0]) for at in sorted(self.written)
                       if self.read(at,1)[0] != self.effect_initial[at]]
            raw_effect = {'name': name, 'args': projected, 'state_at_entry': entry,
                          'modified_state_at_entry': changes}
            self.raw_effect_trace.append(copy.deepcopy(raw_effect))
            semantic_changes, views = self.semantic_effects(at for at,_ in changes)
            self.trace.append({**raw_effect,'modified_state_at_entry': semantic_changes,
                               **({'private_formatter_views':views} if views else {})})
            self.raw_trace.append({'name': name, 'args': args})
            if spec.handler:
                result = spec.handler(self, args)
                if isinstance(result, tuple):
                    self.set_reg('ax', result[0]); self.set_reg('dx', result[1])
                elif result is not None:
                    self.set_reg('ax', result)
                self._return_far(spec.pop)
                return
        # Whole-module scaffold/peer entries delegate to the identical original.
        if self.candidate and address in self.pair.delegate:
            s = self.pair.delegate[address]
            self._jump(s['seg'], s['off'])
            return
        # Resolve RTLink vectors without running or rewriting its manager.
        vector = self.pair.vectors.get(address)
        if vector:
            if vector.unit != 'root':
                self._load_overlay(vector.unit)
            self._jump(vector.target_seg, vector.target_off)

    def _load_overlay(self, unit):
        if unit in self.loaded_units:
            return
        x = exe.load()
        base, data = x.unit_bytes(unit)
        overlapping = []
        for old in self.loaded_units:
            old_base, old_data = x.unit_bytes(old)
            if max(base,old_base) < min(base+len(data),old_base+len(old_data)):
                overlapping.append((old,old_base,len(old_data)))
        if overlapping:
            stack = self.reg('ss') * 16 + self.reg('sp')
            off,seg = struct.unpack('<HH',self.read(stack,4))
            self.overlay_frames.append({'return':seg*16+off,
                                        'loaded':self.loaded_units.copy(),
                                        'images':[(b,self.read(b,n)) for _,b,n in overlapping]})
        for old,_,_ in overlapping:
            self.loaded_units.remove(old)
        self.cpu.mem_write(base,data)
        self.cpu.ctl_remove_cache(base,base+len(data))
        self.loaded_units.add(unit)

    def _reset(self):
        # An interrupted overlay invocation must not leak replacement code into
        # the next case. Restore nested overlay contexts before ordinary state.
        while self.overlay_frames:
            saved = self.overlay_frames.pop()
            for base, data in saved['images']:
                self.cpu.mem_write(base, data)
                self.cpu.ctl_remove_cache(base, base + len(data))
            self.loaded_units = saved['loaded']
        if self.dirty:
            positions = sorted(self.dirty)
            start, previous = positions[0], positions[0]
            data = bytearray([self.dirty[start]])
            for at in positions[1:]:
                if at == previous + 1:
                    data.append(self.dirty[at])
                else:
                    self.cpu.mem_write(start, bytes(data)); start = at; data = bytearray([self.dirty[at]])
                previous = at
            self.cpu.mem_write(start, bytes(data))
            self.dirty.clear()

    def run(self, case, *, preserve=False, function=None):
        if preserve:
            if case.writes or case.state:
                raise ExecutionError('continuation cannot reinitialize memory or model state')
            previous_stack = self.stack_bounds
        else:
            self._reset()
        self.case = case
        if not preserve:
            self.state = copy.deepcopy(case.state)
            self.written, self.effect_initial = set(), {}
        self.trace, self.raw_trace, self.io = [], [], []
        self.raw_effect_trace = []
        self.blocks = 0
        self.error, self.resume, self.completed = None, False, False
        self.active = False
        self.callback_addresses = {}
        for name, spec in case.callbacks.items():
            s = symbol(name)
            self.callback_addresses[s['seg'] * 16 + s['off']] = (name, spec)
            v = match.vector_for(s.get('unit'), s['seg'], s['off'])
            if v and spec.handler:
                self.callback_addresses[exe.MANAGER_SEG * 16 + v.offset] = (name, spec)
            if self.candidate and spec.handler and name in self.pair.candidate_entries:
                self.callback_addresses[self.pair.candidate_entries[name]] = (name, spec)
        # The CRT establishes SS=DS=DGROUP. Only the reserved call-stack
        # interval is implementation-private; other DGROUP writes are effects.
        defaults = dict(ax=0x1234,bx=0x2345,cx=0x3456,dx=0x4567,si=0x5678,di=0x6789,
                        bp=0x789A,ss=match.DGROUP_SEG,ds=match.DGROUP_SEG,es=match.DGROUP_SEG,
                        sp=0xA400,eflags=2)
        defaults.update({k:v for k,v in case.registers.items() if k != 'stack_poison'})
        if not 0 < case.stack_bytes <= defaults['sp']:
            raise ExecutionError('invalid reserved stack depth')
        frame = words(SENTINEL[1], SENTINEL[0], *case.args)
        if defaults['sp'] + len(frame) > 0x10000:
            raise ExecutionError('initial far-call frame wraps stack segment')
        base = defaults['ss'] * 16
        self.stack_bounds = (base + defaults['sp'] - case.stack_bytes,
                             base + defaults['sp'] + len(frame))
        if preserve and (self.stack_bounds[0] != previous_stack[0]
                         or defaults['ss'] != self.initial_registers['ss']
                         or defaults['sp'] != self.initial_registers['sp']):
            raise ExecutionError('continuation must preserve its reserved stack location')
        poison_window = (self.stack_bounds[0], base + defaults['sp'])
        if poison_window != self.stack_poison_window:
            if self.stack_poison_window is not None:
                self.cpu.mem_write(self.stack_poison_window[0], self.stack_initial_image)
            self.stack_initial_image = self.read(poison_window[0], case.stack_bytes)
            self.cpu.mem_write(poison_window[0], b'\xA5' * case.stack_bytes)
            self.stack_poison_window = poison_window
        for address, data in case.writes:
            if not 0 <= address <= MEMORY_SIZE - len(data):
                raise ExecutionError('case memory initialization outside VM')
            if address < self.stack_bounds[1] and address + len(data) > self.stack_bounds[0]:
                raise ExecutionError('fixture memory overlaps reserved call stack')
            self.write(address, data)
        # Poison unused frame bytes; scratch locals must not affect the contract.
        if case.registers.get('stack_poison', 0xA5) != 0xA5:
            poison = bytes([case.registers['stack_poison'] & 255]) * case.stack_bytes
            self.write(self.stack_bounds[0], poison)
        for name, value in defaults.items():
            self.set_reg(name, value)
        self.initial_registers = defaults
        self._validate_cursor_views()
        self.write(defaults['ss'] * 16 + defaults['sp'], frame)
        if function is None:
            entry = self.pair.candidate_entry if self.candidate else (self.pair.function['seg'], self.pair.function['off'])
        else:
            target = self.pair.sequence_function(function)
            if self.candidate and function in self.pair.sequence_targets:
                entry = (CODE_SEG, self.pair.candidate_entries[function] - CODE_SEG * 16)
            else:
                entry = (target['seg'], target['off'])
        self.set_reg('cs', entry[0]); self.set_reg('ip', entry[1])
        self.active = True
        try:
            while True:
                self.resume = False
                start = self.reg('cs') * 16 + self.reg('ip')
                self.cpu.emu_start(start, SENTINEL_LINEAR, count=case.max_instructions)
                if self.error:
                    raise ExecutionError(self.error)
                if self.reg('cs') * 16 + self.reg('ip') == SENTINEL_LINEAR:
                    self.completed = True
                if self.completed:
                    break
                if not self.resume:
                    raise ExecutionError('instruction budget exhausted or stopped before return')
        except (uc.UcError, Exception) as exc:
            raise ExecutionError(f'{case.label} {"candidate" if self.candidate else "oracle"} at {self.reg("cs"):04X}:{self.reg("ip"):04X}: {exc}') from exc
        finally:
            self.active = False
        expected = {n:defaults[n] for n in ('si','di','bp','ss','ds')}
        expected['sp'] = (defaults['sp'] + 4 + case.callee_pop) & 65535
        violations = {n:{'expected':v,'actual':self.reg(n)} for n,v in expected.items() if self.reg(n) != v}
        if violations:
            raise ExecutionError(f'{case.label}: caller ABI violated: {violations}')
        value = self.reg('ax')
        if case.return_kind == 'void': value = None
        elif case.return_kind == 's16': value = value - 65536 if value >= 32768 else value
        elif case.return_kind in ('s32','u32','farptr'):
            value |= self.reg('dx') << 16
            if case.return_kind == 's32' and value >= 0x80000000: value -= 0x100000000
        _, cursor_views = self.semantic_effects(self.written)
        return {'return': value, 'ranges': {r.name: self.read(r.address,r.size).hex() for r in case.observe},
                'trace': self.trace, 'raw_trace': self.raw_trace, 'io': self.io, 'state': self.state,
                'raw_effect_trace':self.raw_effect_trace, 'private_formatter_views':cursor_views,
                'preserved_registers': {n:self.reg(n) for n in ('si','di','bp','sp','ss','ds')},
                'written_addresses': sorted(self.written), 'blocks': self.blocks}


@dataclass
class Comparison:
    equal: bool
    original: dict
    candidate: dict
    diff: dict
    implementation_differences: dict = field(default_factory=dict)


class PreparedPair:
    def __init__(self, function, source=None, out=None, *, sequence_targets=()):
        self.function = functions.get(function)
        name = self.function['name']
        self.sequence_targets = frozenset(sequence_targets)
        for target in self.sequence_targets:
            self.sequence_function(target)
        if source is None:
            catalog = json.loads((ROOT/'work/takeover/hardtail/catalog.json').read_text())
            source = ROOT / next(r['best_source'] for r in catalog['records'] if r['function'] == name)
        self.source = Path(source).resolve()
        self.ctx = modctx.resolve(func=name, source=self.source)
        text = self.source.read_text(encoding='latin1')
        import autosearch
        text = autosearch.unscaffold(text, name)
        for target in sorted(self.sequence_targets - {name}):
            text = autosearch.unscaffold(text, target)
        # Retain normal whole-module peer/data gates; an inexact target is expected.
        claims = list(self.ctx.claims)
        if not any(c['name'] == name for c in claims): claims.append(self.function)
        for target in sorted(self.sequence_targets):
            if not any(c['name'] == target for c in claims): claims.append(self.sequence_function(target))
        collected = {}
        self.strict = modules.verify_module(text, self.ctx.module_dict(), claims, collect=collected)
        if not self.strict.get('compile_ok'):
            raise ExecutionError(self.strict.get('log','candidate compile failed'))
        peers = [c['name'] for c in self.ctx.claims if not self.strict['claims'].get(c['name'],{}).get('exact')]
        data = [n for n,r in self.strict.get('data',{}).items() if not r.get('exact')]
        if peers or data:
            raise ExecutionError(f'candidate has existing peer/data regressions: {peers} / {data}')
        self.obj = modctx.read_obj(collected['object'])
        public, record = match.public_in(self.obj, name)
        if record is None: raise ExecutionError('candidate lacks function public')
        segment = record['segment']
        raw = self.obj.segments[segment]
        if len(raw) > 65536: raise ExecutionError('candidate code segment exceeds real-mode arena')
        bound = ExecutionBinder(match.Target(self.function['unit'], CODE_SEG, 0, len(raw)),
                             self.obj, segment, None, self.ctx.placements_bind, span=(0,len(raw))).bind()
        if bound.unbound or len(bound.candidate) != len(raw):
            raise ExecutionError(f'candidate harness link is incomplete: {bound.unbound}')
        self.code = bound.candidate
        self.candidate_entry = (CODE_SEG, record['offset'])
        self.candidate_entries, self.delegate = {}, {}
        for p in self.obj.publics + getattr(self.obj,'local_publics',[]):
            if p['segment'] != segment: continue
            # Strip the single ABI prefix, preserving C identifiers such as
            # _ffree whose actual object public is __ffree.
            pname = p['name'][1:] if p['name'].startswith(('_','@')) else p['name']
            address = CODE_SEG * 16 + p['offset']
            self.candidate_entries[pname] = address
            if p['offset'] != record['offset'] and pname not in self.sequence_targets:
                try: self.delegate[address] = symbol(pname)
                except KeyError: raise ExecutionError(f'unregistered candidate peer {pname}')
        if self.sequence_targets - self.candidate_entries.keys():
            raise ExecutionError('sequence target lacks a candidate definition')
        self.vectors = {exe.MANAGER_SEG*16+v.offset:v for v in exe.load().vectors}
        self.identity = {'function':name,'address':{k:self.function[k] for k in ('unit','seg','off','size')},
                         'source':str(self.source.relative_to(ROOT)), 'source_sha256':digest(self.source.read_bytes()),
                         'compiled_source_sha256':digest(text.encode('latin1')),
                         'object_sha256':digest(collected['object']), 'linked_code_sha256':digest(self.code),
                         'oracle_sha256':exe.load().sha256,'unicorn_version':uc.__version__,
                         'harness_sha256':digest(HARNESS_SOURCE),'profile':self.ctx.profile,'flags':self.ctx.flags,
                         'manifest_sha256':digest((ROOT/'layout/manifest.json').read_bytes())}
        if self.sequence_targets:
            self.identity['sequence_targets'] = sorted(self.sequence_targets)
        if out:
            out = modctx.under_build(Path(out)); out.mkdir(parents=True,exist_ok=True)
            (out/'candidate.obj').write_bytes(collected['object'])
            (out/'identity.json').write_text(json.dumps(self.identity,indent=2)+'\n')
            (out/'behavior-harness.py').write_bytes(HARNESS_SOURCE)
        self.original_machine = Machine(self)
        self.candidate_machine = Machine(self,True)

    def compare(self, case):
        a = self.original_machine.run(case)
        b = self.candidate_machine.run(case)
        return PreparedPair._comparison(self, case, a, b)

    def sequence_function(self, name):
        target = functions.get(name)
        if (target['unit'],target['seg']) != (self.function['unit'],self.function['seg']):
            raise ExecutionError('sequence entry must belong to the prepared original module')
        return target

    def compare_sequence(self, steps):
        """Yield a comparison after each live-state invocation.

        Steps are (function name, Case) pairs. Only the first case initializes
        memory/model state. Record each yielded result before advancing: the
        machines then retain their independently computed memory and model state.
        Listed sequence_targets execute natural candidate code; other same-module
        setup/helper entries execute the original on both sides.
        """
        for index,(name,case) in enumerate(steps):
            self.sequence_function(name)
            a = self.original_machine.run(case,preserve=index>0,function=name)
            b = self.candidate_machine.run(case,preserve=index>0,function=name)
            yield PreparedPair._comparison(self,case,a,b)

    def _comparison(self, case, a, b):
        diff = {k:{'oracle':a[k],'candidate':b[k]} for k in
                ('return','ranges','trace','io','state','preserved_registers','private_formatter_views') if a[k] != b[k]}
        addresses = sorted(set(a['written_addresses']) | set(b['written_addresses']))
        av,_ = self.original_machine.semantic_effects(addresses)
        bv,_ = self.candidate_machine.semantic_effects(addresses)
        if av != bv: diff['nonstack_memory'] = {'oracle':av,'candidate':bv}
        raw_memory = []
        for at in addresses:
            av,bv = self.original_machine.read(at,1)[0],self.candidate_machine.read(at,1)[0]
            if av != bv: raw_memory.append({'address':at,'oracle':av,'candidate':bv})
        implementation = {}
        if case.format_cursor_views:
            if raw_memory:implementation['raw_nonstack_memory']=raw_memory
            if a['raw_effect_trace']!=b['raw_effect_trace']:
                implementation['raw_effect_trace']={'oracle':a['raw_effect_trace'],'candidate':b['raw_effect_trace']}
        return Comparison(not diff,a,b,diff,implementation)
