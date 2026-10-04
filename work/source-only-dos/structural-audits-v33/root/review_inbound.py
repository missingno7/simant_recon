"""Independent direct-transfer/relocation census, not runtime reachability proof."""
import hashlib
import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools'))
import exe
import functions
from omf import OmfReader
try:
    from capstone import Cs, CS_ARCH_X86, CS_MODE_16
except ImportError:
    sys.path.insert(0, 'C:/tools/capstone-5.0.3')
    from capstone import Cs, CS_ARCH_X86, CS_MODE_16

names = ['f_208F_027F', 'f_208F_02F0', 'f_1C62_06A6', 'f_208F_0419']
targets = {name: functions.get(name) for name in names}
image = exe.load()
decoder = Cs(CS_ARCH_X86, CS_MODE_16)
unsupported_direct = []
results = {name: dict(external_direct=[], relocated_pointer=[], vectors=[], object_fixups=[])
           for name in names}
for unit in image.units():
    base, raw = image.unit_bytes(unit)
    for row in functions.table()['functions']:
        if row['unit'] != unit:
            continue
        frame = row['seg'] * 16
        start = frame + row['off']
        for insn in decoder.disasm(raw[start-base:start-base+row['size']], start):
            b = bytes(insn.bytes)
            destination = None
            if len(b) == 5 and b[0] in (0x9a, 0xea):
                off, seg = struct.unpack_from('<HH', b, 1)
                destination = seg * 16 + off
            elif len(b) == 3 and b[0] in (0xe8, 0xe9):
                destination = frame + ((insn.address-frame + 3 + struct.unpack_from('<h', b, 1)[0]) & 0xffff)
            elif len(b) == 2 and (b[0] == 0xeb or 0x70 <= b[0] <= 0x7f or 0xe0 <= b[0] <= 0xe3):
                destination = frame + ((insn.address-frame + 2 + struct.unpack_from('<b', b, 1)[0]) & 0xffff)
            elif len(b) == 4 and b[0] == 0x0f and 0x80 <= b[1] <= 0x8f:
                destination = frame + ((insn.address-frame + 4 + struct.unpack_from('<h', b, 2)[0]) & 0xffff)
            if destination is None:
                # FF /2..5 transfers are deliberately outside this direct census.
                if insn.mnemonic.startswith(('j', 'loop')) or insn.mnemonic in ('call', 'lcall', 'ljmp'):
                    if not (b and (b[0] == 0xff or b[0] in (0x26, 0x2e, 0x36, 0x3e) and len(b) > 1 and b[1] == 0xff)):
                        unsupported_direct.append(dict(unit=unit, site=insn.address,
                            instruction=insn.mnemonic + ' ' + insn.op_str, bytes=b.hex()))
                continue
            for name, target in targets.items():
                lo = target['seg'] * 16 + target['off']
                if target['unit'] == 'root' and lo <= destination < lo + target['size']:
                    if unit != target['unit'] or not lo <= insn.address < lo + target['size']:
                        results[name]['external_direct'].append(dict(unit=unit,
                            source=functions.name_of(unit, row['seg'], row['off']),
                            instruction=insn.mnemonic + ' ' + insn.op_str,
                            site=insn.address, destination=destination))
    for seg, off in image.unit_relocs(unit):
        local = seg * 16 + off - base
        if not 2 <= local <= len(raw) - 2:
            continue
        pointer_off, pointer_seg = struct.unpack_from('<HH', raw, local - 2)
        destination = pointer_seg * 16 + pointer_off
        for name, target in targets.items():
            lo = target['seg'] * 16 + target['off']
            if lo <= destination < lo + target['size']:
                results[name]['relocated_pointer'].append(dict(unit=unit, site=seg*16+off))
for vector in image.vectors:
    destination = vector.target_seg * 16 + vector.target_off
    for name, target in targets.items():
        lo = target['seg'] * 16 + target['off']
        if lo <= destination < lo + target['size']:
            results[name]['vectors'].append(vector.offset)
report = json.loads((ROOT / 'build/source-only-dos/build-report.json').read_bytes())
reader = OmfReader(communals=True)
for tu in report['translation_units']:
    path = ROOT / tu['object']['path']
    assert hashlib.sha256(path.read_bytes()).hexdigest() == tu['object']['sha256']
    obj = reader.read_file(path)
    for name in names:
        for fixup in obj.linker_fixups:
            if fixup['target'] == '_' + name:
                results[name]['object_fixups'].append(dict(module=tu['module'], fixup=fixup))
for name in names[:3]:
    assert not any(results[name].values()), (name, results[name])
assert results['f_208F_0419']['external_direct']
assert results['f_208F_0419']['relocated_pointer']
assert results['f_208F_0419']['object_fixups']
assert not unsupported_direct, unsupported_direct
def pin(path):
    path = Path(path)
    if not path.is_absolute():
        path = ROOT / path
    raw = path.read_bytes()
    return dict(path=path.relative_to(ROOT).as_posix(), sha256=hashlib.sha256(raw).hexdigest(), size=len(raw))
input_pins = [pin(path) for path in (Path(__file__), 'tools/exe.py', 'tools/functions.py',
    'tools/symbols.py', 'tools/omf.py', 'layout/functions.json', 'layout/symbols.json',
    'layout/oracle.lock.json', 'build/source-only-dos/build-report.json')]
for tu in report['translation_units']:
    input_pins.append(pin(tu['object']['path']))
receipt = dict(status='PASS', root_reviewed=True, admitted=False,
    original_analysis_only=True, original_build_bytes_used=0,
    functions_scanned=len(functions.table()['functions']), units_scanned=len(image.units()),
    objects_scanned=len(report['translation_units']), targets=results,
    input_pins=input_pins, unsupported_direct_transfers=unsupported_direct,
    positive_control='f_208F_0419 has real inbound transfers, relocations and current external fixups',
    scope='Direct calls/jumps including conditional branches and loops, and relocation-backed '
          'far pointers only. No indirect-control closure, computed pointer proof or storage admission.')
path = Path(__file__).with_name('root-inbound.json')
path.write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
print(json.dumps(dict(status='PASS', summary={name: {key: len(value) for key,value in result.items()}
    for name,result in results.items()}), indent=2))
