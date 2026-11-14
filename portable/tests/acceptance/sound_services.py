"""Bind v9 foreground sound entries independently in each executable.

Marker 245 consumes one byte from observer.txt.sound. IDs are the alphabetical
one-based index of the reviewed census; no expected state supplies a boundary.
DOS and native observers suppress these entries while executing the sound ISR.
"""
import hashlib
import json
from pathlib import Path
import re
import struct
import sys

ROOT = Path(__file__).resolve().parents[3]
CENSUS = ROOT / 'evidence/canonical/native-audio-schedule/foreground-census.json'
ORDER_MARKER = 245
CONTRACT = 'foreground-sound-entries-v2'
WRAPPED = {'snd_service_and_test_stopped', 'snd_port_read_byte', 'snd_expand_sample_resource'}


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def services(census=None):
    """Stable IDs and reviewed function names; fail closed on census changes."""
    path = Path(census) if census is not None else CENSUS
    data = json.loads(path.read_text())
    if isinstance(data, dict) and 'inputs' in data:
        if not isinstance(data['inputs'], list):
            raise ValueError('Foreground sound census inputs must be identity pins')
        for pin in data['inputs']:
            if (not isinstance(pin, dict) or not isinstance(pin.get('path'), str)
                    or not re.fullmatch(r'[0-9a-f]{64}', str(pin.get('sha256', '')))):
                raise ValueError('Malformed foreground sound census input identity')
            source = ROOT / pin['path']
            if not source.is_file() or _sha(source.read_bytes()) != pin['sha256']:
                raise ValueError('Foreground sound census input changed: ' + pin['path'])
    rows = data if isinstance(data, list) else data.get('services', data.get('functions'))
    if not isinstance(rows, list) or not rows or len(rows) > 255:
        raise ValueError('Foreground sound census must have 1..255 service rows')
    rows = sorted(rows, key=lambda row: row['name'])
    names = [row['name'] for row in rows]
    if len(set(names)) != len(names) or any(not re.fullmatch(r'[A-Za-z_][A-Za-z_0-9]*', name) for name in names):
        raise ValueError('Duplicate or invalid foreground sound name')
    result = []
    for identifier, row in enumerate(rows, 1):
        if row.get('id', identifier) != identifier:
            raise ValueError('Foreground sound ID differs from reviewed sorted-name order')
        if not str(row['module']).startswith('root:') or row['size'] < 1:
            raise ValueError('Foreground sound entry needs a resident module and established extent')
        result.append(dict(row, id=identifier))
    return result


def service_manifest(census=None):
    path = Path(census) if census is not None else CENSUS
    keys = ('id', 'name', 'module', 'source', 'lang', 'native_name', 'required', 'entry_guard')
    return dict(contract=CONTRACT, order_marker=ORDER_MARKER, census_sha256=_sha(path.read_bytes()),
                services=[{key: row.get(key) for key in keys} for row in services(path)],
                rule='Foreground function ENTRY; census argument guards qualify shared-sound-state paths; '
                     'other paths remain diagnostic; suppressed while the actual sound ISR is active.')


def sound_entry_qualified(identifier, args=None, census=None):
    """Qualify live entry arguments; never filter a previously recorded tape.

    args may be a name/value mapping or the source's positional arguments.
    A 16-bit signed native value and its unsigned DOS word qualify identically.
    """
    row = next((row for row in services(census) if row['id'] == identifier), None)
    if row is None:
        raise ValueError('Unknown foreground sound service ID')
    guard = row.get('entry_guard')
    if guard is None:
        return True
    if (guard.get('kind'), guard.get('width_bits')) != ('argument_equal', 16):
        raise ValueError('Unsupported foreground sound entry guard')
    try:
        value = args[guard['argument_name']] if isinstance(args, dict) else args[guard['argument_index']]
    except (KeyError, IndexError, TypeError) as error:
        raise ValueError('Missing live foreground sound argument') from error
    if type(value) is not int or not -32768 <= value <= 65535:
        raise ValueError('Foreground sound argument is not a 16-bit word')
    return (value & 0xffff) == guard['value']


def native_sound_include(census=None):
    """Two-pass include: declarations, or SOUND_SERVICE(id, sound_addr_ID) rows.

    Declarations use assembler aliases, avoiding incompatible C prototypes.
    Projected bodies need strong aliases: MinGW COFF weak assembler aliases
    can resolve to zero despite the actual LTO body being present. Only the
    nine census entries without standalone native functions remain weak.
    Missing profile leaves remain explicit in native_sound_coverage.
    The --wrap targets alias their real instrumented bodies, not wrappers.
    """
    rows = services(census)
    sample_id = next(row['id'] for row in rows if row['name'] == 'snd_expand_sample_resource')
    lines = ['/* Generated from the reviewed foreground sound census. */',
             f'#define SOUND_SAMPLE_RESOURCE_ID {sample_id}', '#ifndef SOUND_SERVICE']
    for row in rows:
        name, identifier = row['name'], row['id']
        link = '__real_' + name if name in WRAPPED else (row.get('native_name') or name)
        absent = str(row.get('native_representation', '')).startswith('No standalone native function')
        weak = ' __attribute__((weak))' if absent and name not in WRAPPED else ''
        lines.append(f'extern void sound_addr_{identifier}(void) __asm__("{link}"){weak}; /* {name} */')
    lines.append('#else')
    lines += [f'SOUND_SERVICE({row["id"]}, sound_addr_{row["id"]}) /* {row["name"]} */' for row in rows]
    return '\n'.join(lines + ['#endif', ''])


def native_sound_coverage(symbols, used_ids=(), census=None):
    """Report missing optional native profile leaves; any observed missing ID fails."""
    addresses = symbols.addresses if hasattr(symbols, 'addresses') else symbols
    rows = services(census)
    allowed = {row['id'] for row in rows}
    used = set(used_ids)
    if used - allowed:
        raise ValueError('Unknown observed foreground sound ID')
    missing = [dict(id=row['id'], name=row['name']) for row in rows
               if not addresses.get(row.get('native_name') or row['name'])]
    if used & {row['id'] for row in missing}:
        raise ValueError('Observed DOS foreground sound entry has no native body: ' +
                         ', '.join(row['name'] for row in missing if row['id'] in used))
    return dict(contract=CONTRACT, missing_profile_entries=missing,
                observed_ids=sorted(used), entries=len(rows))


def sound_tape(source, order, destination=None, service_limit=None, census=None, include_ids=True):
    """Validate the full ID stream against marker count; optionally select a prefix.

    Unlike the IRQ timer tape there is no trailer: its complete chronological
    order and matching count are mandatory and hash-pinned by the manifest.
    The service at zero-based ordinal service_limit is outside the prefix.
    Set include_ids=False for large captures to avoid a Python integer list;
    the binary prefix, counts, digests and distinct used IDs remain available.
    """
    ids = Path(source).read_bytes()
    sequence = Path(order).read_bytes()
    valid = {row['id'] for row in services(census)}
    if len(ids) != sequence.count(ORDER_MARKER) or any(value not in valid for value in ids):
        raise ValueError('Foreground sound ID stream differs from chronological order markers')
    if service_limit is None:
        service_limit = len(sequence)
    if type(service_limit) is not int or not 0 <= service_limit <= len(sequence):
        raise ValueError('Invalid foreground sound service prefix limit')
    count = sequence.count(ORDER_MARKER, 0, service_limit)
    prefix = ids[:count]
    if destination is not None:
        Path(destination).write_bytes(prefix)
    result = dict(contract=CONTRACT, source_ids=len(ids), prefix_ids=count,
                  source_sha256=_sha(ids), prefix_sha256=_sha(prefix), used_ids=sorted(set(prefix)))
    if include_ids:
        result['ids'] = list(prefix)
    return result


def _mz_image(path, base):
    """Load this executable's own MZ root and apply its ordered DOS relocations."""
    raw = Path(path).read_bytes()
    if raw[:2] != b'MZ' or len(raw) < 28 or base < 0 or base % 16:
        raise ValueError('Invalid executable or paragraph load base')
    last, pages, count, paras = struct.unpack_from('<4H', raw, 2)
    end = (pages - 1) * 512 + last if last else pages * 512
    reloc_at = struct.unpack_from('<H', raw, 24)[0]
    start = paras * 16
    if not 28 <= start <= end <= len(raw) or reloc_at + 4 * count > start:
        raise ValueError('Truncated MZ root or relocation table')
    image = bytearray(raw[start:end])
    relocations = []
    for i in range(count):
        offset, segment = struct.unpack_from('<2H', raw, reloc_at + i * 4)
        at = segment * 16 + offset
        if at + 2 > len(image):
            raise ValueError('MZ relocation outside root image')
        value = (int.from_bytes(image[at:at + 2], 'little') + base // 16) & 0xffff
        image[at:at + 2] = value.to_bytes(2, 'little')
        relocations.append(at)
    return bytes(image), relocations, _sha(raw)


def _original_metadata(rows):
    symbols = json.loads((ROOT / 'layout/symbols.json').read_text())['code']
    table = json.loads((ROOT / 'layout/functions.json').read_text())['functions']
    functions = {(row['unit'], row['seg'], row['off']): row for row in table}
    metadata = {}
    for row in rows:
        name = row['name']
        symbol = symbols[name]
        function = functions[(symbol.get('unit', 'root'), symbol['seg'], symbol['off'])]
        linear = symbol['seg'] * 16 + symbol['off']
        if (symbol.get('unit', 'root') != 'root' or linear != row['original_linear']
                or function['size'] != row['size']):
            raise ValueError('Census original anchor/extent differs: ' + name)
        metadata[name] = dict(address=linear, start=linear, size=function['size'],
                              evidence='Original root symbol + independently recorded full function extent')
    path = ROOT / 'assets/SIMANT.EXE'
    expected = json.loads((ROOT / 'layout/oracle.lock.json').read_text())['inputs']['SIMANT.EXE']['sha256']
    if _sha(path.read_bytes()) != expected:
        raise ValueError('Original executable identity differs')
    return metadata, path, dict(executable_sha256=expected)


def _cfg(raw, start):
    """Reachable object instructions; calls stay in their caller's CFG."""
    from capstone import Cs, CS_ARCH_X86, CS_MODE_16, CS_GRP_JUMP, CS_GRP_RET, CS_GRP_IRET
    from capstone.x86 import X86_OP_IMM
    decoder = Cs(CS_ARCH_X86, CS_MODE_16)
    decoder.detail = True
    pending, seen = [start], {}
    while pending:
        at = pending.pop()
        if at in seen:
            continue
        if not 0 <= at < len(raw) or abs(at - start) > 8192:
            raise ValueError('Foreground sound CFG escapes its bounded object code')
        ins = next(decoder.disasm(raw[at:at + 15], at, count=1), None)
        if ins is None:
            raise ValueError('Invalid foreground sound object instruction')
        seen[at] = ins
        if ins.group(CS_GRP_RET) or ins.group(CS_GRP_IRET):
            continue
        if ins.group(CS_GRP_JUMP):
            if len(ins.operands) == 1 and ins.operands[0].type == X86_OP_IMM:
                pending.append(ins.operands[0].imm)
            elif ins.mnemonic not in ('ljmp', 'jmp'):
                raise ValueError('Unbound indirect conditional sound branch')
            if ins.mnemonic in ('ljmp', 'jmp'):
                continue
        pending.append(at + ins.size)
    if not any(ins.group(CS_GRP_RET) or ins.group(CS_GRP_IRET) for ins in seen.values()):
        raise ValueError('Sound entry has no reachable return')
    return seen


def _canonical_metadata(rows, report_path):
    sys.path.insert(0, str(ROOT / 'tools'))
    from omf import OmfReader
    report_path = Path(report_path)
    report = json.loads(report_path.read_text())
    candidate = report['link']['candidate_executable']
    executable = ROOT / candidate['path']
    if _sha(executable.read_bytes()) != candidate['sha256']:
        raise ValueError('Canonical executable identity differs from its build report')
    map_path = executable.with_name('SOURCE.MAP')
    addresses = {}
    for line in map_path.read_text(encoding='latin1').splitlines():
        match = re.match(r'\s*([0-9A-F]{4}):([0-9A-F]{4})\s+(?:Res|Ovl)\s+[_@](\w+)(?=\s|$)', line)
        if match:
            addresses.setdefault(match[3], int(match[1], 16) * 16 + int(match[2], 16))
    units = {row['key']: row for row in report['translation_units']}
    objects, metadata = {}, {}
    for row in rows:
        key, name = row['module'], row['name']
        module = units[key]
        if module['source'] != row['source']:
            raise ValueError('Census canonical owning module differs: ' + name)
        if key not in objects:
            pin = module['object']
            raw = (ROOT / pin['path']).read_bytes()
            if _sha(raw) != pin['sha256']:
                raise ValueError('Canonical sound object identity differs')
            objects[key] = OmfReader(communals=True).read(raw)
        obj = objects[key]
        public = [item for item in obj.publics if item['name'].lstrip('_@') == name]
        if len(public) != 1 or name not in addresses:
            raise ValueError('Missing/ambiguous independent canonical sound public: ' + name)
        public = public[0]
        segment, start = public['segment'], public['offset']
        raw = bytes(obj.segments[segment])
        debug, at, lengths = bytes(obj.segments.get('$$SYMBOLS', b'')), 0, []
        while at < len(debug):
            length = debug[at]
            body = debug[at + 1:at + 1 + length]
            if not length or len(body) != length:
                raise ValueError('Truncated canonical CodeView procedure record')
            if body[0] == 1 and len(body) >= 15 and body[15:15 + body[14]].decode('latin1') == name:
                lengths.append(int.from_bytes(body[5:7], 'little'))
            at += length + 1
        cfg = _cfg(raw, start)
        lower = min(cfg)
        upper = max(ins.address + ins.size for ins in cfg.values())
        if lengths:
            if len(lengths) != 1 or lower < start or upper > start + lengths[0]:
                raise ValueError('Canonical sound CodeView extent differs from reachable instructions: ' + name)
            lower, upper = start, start + lengths[0]
        if not 0 <= lower < upper <= len(raw):
            raise ValueError('Invalid canonical sound procedure extent: ' + name)
        fixes = [dict(offset=f['offset'], target=f.get('target'), location=f['loc'],
                      target_kind=f['target_kind']) for f in obj.linker_fixups
                 if f['segment'] == segment and lower <= f['offset'] < upper]
        call_bindings = []
        for at, ins in sorted(cfg.items()):
            if len(ins.bytes) != 5 or ins.bytes[0] != 0x9a:
                continue
            fix = [f for f in obj.linker_fixups if f['segment'] == segment
                   and f['offset'] == at + 1 and f['loc'] == 'pointer32'
                   and f['target_kind'] == 'external']
            if len(fix) == 1:
                target_name = fix[0]['target'].lstrip('_@')
                if target_name in addresses:
                    call_bindings.append(dict(offset=at - start, target=target_name,
                                              target_address=addresses[target_name]))
        metadata[name] = dict(address=addresses[name], start=addresses[name] + lower - start,
            size=upper - lower, object_sha256=module['object']['sha256'],
            object_function_sha256=_sha(raw[lower:upper]), object_fixups=fixes,
            reachable_instructions={str(pc - start): bytes(ins.bytes).hex() for pc, ins in sorted(cfg.items())},
            direct_call_bindings=call_bindings,
            evidence='Own MAP + OMF public + ' + ('CodeView extent and ' if lengths else '') + 'reachable object CFG')
    return metadata, executable, dict(executable_sha256=candidate['sha256'],
        build_report_sha256=_sha(report_path.read_bytes()), map_sha256=_sha(map_path.read_bytes()))


def _guard_binding(memory, pc, row):
    """Prove the live entry stack word is the source's actual type==5 guard."""
    from capstone import Cs, CS_ARCH_X86, CS_MODE_16
    from capstone.x86 import X86_OP_MEM, X86_OP_IMM, X86_REG_BP, X86_REG_SS
    guard = row.get('entry_guard')
    if guard is None:
        return None
    if (row['name'] != 'snd_expand_sample_resource'
            or guard.get('kind') != 'argument_equal' or guard.get('argument_index') != 3
            or guard.get('argument_name') != 'type' or guard.get('width_bits') != 16
            or guard.get('value') != 5 or guard.get('otherwise') != 'diagnostic_only'
            or guard.get('dos') != dict(base='ss:sp', byte_offset=14)
            or guard.get('native') != dict(source='typed_wrapper_argument', argument_name='type')):
        raise ValueError('Unsupported reviewed foreground sound entry guard')
    decoder = Cs(CS_ARCH_X86, CS_MODE_16)
    decoder.detail = True
    instructions = list(decoder.disasm(memory[pc:pc + 32], pc))
    setup = [('push', 'bp'), ('mov', 'bp, sp'), ('sub', 'sp, 4'), ('push', 'di'), ('push', 'si')]
    if len(instructions) < 7 or [(ins.mnemonic, ins.op_str) for ins in instructions[:5]] != setup:
        raise ValueError('Sound argument guard prologue differs')
    compare, branch = instructions[5:7]
    if (compare.mnemonic != 'cmp' or len(compare.operands) != 2
            or compare.operands[0].type != X86_OP_MEM or compare.operands[0].size != 2
            or compare.operands[0].mem.base != X86_REG_BP or compare.operands[0].mem.index
            or compare.operands[0].mem.segment not in (0, X86_REG_SS)
            or compare.operands[0].mem.disp != 16 or compare.operands[1].type != X86_OP_IMM
            or compare.operands[1].imm != 5 or branch.mnemonic != 'jne'
            or len(branch.operands) != 1 or branch.operands[0].type != X86_OP_IMM):
        raise ValueError('Sound argument guard is not the actual CMP [BP+16],5 / JNE')
    skip = branch.operands[0].imm
    tail = []
    for ins in decoder.disasm(memory[skip:skip + 12], skip):
        tail.append(ins)
        if ins.mnemonic == 'retf':
            break
    expected_tail = [('pop', 'si'), ('pop', 'di'), ('mov', 'sp, bp'), ('pop', 'bp'), ('retf', '')]
    if [(ins.mnemonic, ins.op_str) for ins in tail] != expected_tail:
        raise ValueError('Non-sample callback path does not return without sound work')
    # PUSH BP makes BP = entry SP - 2. Therefore [BP+16] is exactly
    # SS:[entry SP+14], before any source instruction or observation executes.
    return dict(id=row['id'], name=row['name'], entry=pc, entry_guard=guard,
        compare_pc=compare.address, branch_pc=branch.address, diagnostic_return_pc=skip,
        entry_stack_offset=14, compare_bp_offset=16,
        evidence='Actual prologue establishes BP=entrySP-2; CMP word [BP+16],5; '
                 'JNE reaches only POP SI/DI, MOV SP,BP, POP BP, RETF.',
        instructions={ins.address: bytes(ins.bytes).hex() for ins in instructions[:7] + tail})


def sound_binding(memory, base, addresses, target=None, build_report=None, census=None):
    """Bind entries and complete relocated procedure extents in this executable.

    Target may be original/canonical/canonical_dos. Without it, the entire
    reviewed name/address set must identify exactly one independently built
    symbol map. No original code address or extent is reused for a candidate.
    """
    rows = services(census)
    original, original_path, original_pin = _original_metadata(rows)
    original_match = all(addresses.get(row['name']) == original[row['name']]['address'] for row in rows)
    if target is None:
        target = 'original' if original_match else 'canonical'
    if target == 'original':
        metadata, executable, pin = original, original_path, original_pin
    elif target in ('canonical', 'canonical_dos'):
        metadata, executable, pin = _canonical_metadata(rows, build_report or ROOT / 'build/current/dos/build-report.json')
    else:
        raise ValueError('Unknown foreground sound executable target')
    if any(addresses.get(row['name']) != metadata[row['name']]['address'] for row in rows):
        raise ValueError('Foreground sound entries differ from the selected independent symbol map')
    image, relocs, image_sha = _mz_image(executable, base)
    if image_sha != pin['executable_sha256']:
        raise ValueError('Foreground sound executable changed during binding')
    functions, entries, guards = [], [], []
    for row in rows:
        name = row['name']
        item = metadata[name]
        start, size = item['start'], item['size']
        pc = base + item['address']
        expected = image[start:start + size]
        actual = memory[base + start:base + start + size]
        if len(expected) != size or actual != expected:
            raise ValueError('Foreground sound full procedure bytes differ: ' + name)
        guard = _guard_binding(memory, pc, row)
        if guard is not None:
            guards.append(guard)
        calls = []
        for call in item.get('direct_call_bindings', []):
            call_pc = pc + call['offset']
            code = memory[call_pc:call_pc + 5]
            target_pc = int.from_bytes(code[1:3], 'little') + 16 * int.from_bytes(code[3:5], 'little')
            if len(code) != 5 or code[0] != 0x9a or target_pc != base + call['target_address']:
                raise ValueError('Canonical foreground sound CALL differs from its own OMF fixup: ' + name)
            calls.append(dict(call, pc=call_pc, resolved_target=target_pc))
        functions.append(dict(item, id=row['id'], name=name, entry=pc,
            resolved_direct_calls=calls, relocated_function_sha256=_sha(actual),
            relocations=[at - start for at in relocs if start <= at < start + size]))
        entries.append(('s', pc, row['id']))
    if len({pc for _, pc, _ in entries}) != len(entries):
        raise ValueError('Foreground sound service entries alias')
    return dict(**service_manifest(census), target=target, runtime_base=base,
                **pin, entries=entries, functions=functions, guards=guards)


def sound_points(memory, base, addresses, **options):
    return sound_binding(memory, base, addresses, **options)['entries']
