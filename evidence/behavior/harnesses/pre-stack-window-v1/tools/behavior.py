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
        self.cpu.mem_write(STACK_SEG * 16 + 0xE000, b'\xA5' * 0x1000)
        self.dirty = {}
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
            if not STACK_SEG * 16 <= at < (STACK_SEG + 0x1000) * 16:
                self.written.add(at)
                self.effect_initial.setdefault(at, self.read(at, 1)[0])

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
            self.trace.append({'name': name, 'args': projected, 'state_at_entry': entry,
                               'modified_state_at_entry': changes})
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

    def run(self, case):
        self._reset()
        self.case = case
        self.state = copy.deepcopy(case.state)
        self.trace, self.raw_trace, self.io, self.written = [], [], [], set()
        self.effect_initial = {}
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
        for address, data in case.writes:
            if not 0 <= address <= MEMORY_SIZE - len(data):
                raise ExecutionError('case memory initialization outside VM')
            self.write(address, data)
        # Poison unused frame bytes; scratch locals must not affect the contract.
        poison = bytes([case.registers.get('stack_poison', 0xA5) & 255]) * 0x1000
        if case.registers.get('stack_poison',0xA5) != 0xA5:
            self.write(STACK_SEG * 16 + 0xE000, poison)
        defaults = dict(ax=0x1234,bx=0x2345,cx=0x3456,dx=0x4567,si=0x5678,di=0x6789,
                        bp=0x789A,ss=STACK_SEG,ds=match.DGROUP_SEG,es=match.DGROUP_SEG,
                        sp=0xF000,eflags=2)
        defaults.update({k:v for k,v in case.registers.items() if k != 'stack_poison'})
        for name, value in defaults.items():
            self.set_reg(name, value)
        self.initial_registers = defaults
        self.write(defaults['ss'] * 16 + defaults['sp'], words(SENTINEL[1], SENTINEL[0], *case.args))
        entry = self.pair.candidate_entry if self.candidate else (self.pair.function['seg'], self.pair.function['off'])
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
        return {'return': value, 'ranges': {r.name: self.read(r.address,r.size).hex() for r in case.observe},
                'trace': self.trace, 'raw_trace': self.raw_trace, 'io': self.io, 'state': self.state,
                'preserved_registers': {n:self.reg(n) for n in ('si','di','bp','sp','ss','ds')},
                'written_addresses': sorted(self.written), 'blocks': self.blocks}


@dataclass
class Comparison:
    equal: bool
    original: dict
    candidate: dict
    diff: dict


class PreparedPair:
    def __init__(self, function, source=None, out=None):
        self.function = functions.get(function)
        name = self.function['name']
        if source is None:
            catalog = json.loads((ROOT/'work/takeover/hardtail/catalog.json').read_text())
            source = ROOT / next(r['best_source'] for r in catalog['records'] if r['function'] == name)
        self.source = Path(source).resolve()
        self.ctx = modctx.resolve(func=name, source=self.source)
        text = self.source.read_text(encoding='latin1')
        import autosearch
        text = autosearch.unscaffold(text, name)
        # Retain normal whole-module peer/data gates; an inexact target is expected.
        claims = list(self.ctx.claims)
        if not any(c['name'] == name for c in claims): claims.append(self.function)
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
            pname = p['name'].lstrip('_@')
            address = CODE_SEG * 16 + p['offset']
            self.candidate_entries[pname] = address
            if p['offset'] != record['offset']:
                try: self.delegate[address] = symbol(pname)
                except KeyError: raise ExecutionError(f'unregistered candidate peer {pname}')
        self.vectors = {exe.MANAGER_SEG*16+v.offset:v for v in exe.load().vectors}
        self.identity = {'function':name,'address':{k:self.function[k] for k in ('unit','seg','off','size')},
                         'source':str(self.source.relative_to(ROOT)), 'source_sha256':digest(self.source.read_bytes()),
                         'compiled_source_sha256':digest(text.encode('latin1')),
                         'object_sha256':digest(collected['object']), 'linked_code_sha256':digest(self.code),
                         'oracle_sha256':exe.load().sha256,'unicorn_version':uc.__version__,
                         'harness_sha256':digest(HARNESS_SOURCE),'profile':self.ctx.profile,'flags':self.ctx.flags,
                         'manifest_sha256':digest((ROOT/'layout/manifest.json').read_bytes())}
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
        diff = {k:{'oracle':a[k],'candidate':b[k]} for k in
                ('return','ranges','trace','io','state','preserved_registers') if a[k] != b[k]}
        addresses = sorted(set(a['written_addresses']) | set(b['written_addresses']))
        memory = []
        for at in addresses:
            av,bv = self.original_machine.read(at,1)[0],self.candidate_machine.read(at,1)[0]
            if av != bv: memory.append({'address':at,'oracle':av,'candidate':bv})
        if memory: diff['nonstack_memory'] = memory
        return Comparison(not diff,a,b,diff)
