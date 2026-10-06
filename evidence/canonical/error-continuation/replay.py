"""Regress original Punt's explicit guard and the database minus-one prefix.

This is an isolated unchanged-original instruction witness, not DOSBox-X
whole-game acceptance or evidence of a reachable complete fatal continuation.
"""
from pathlib import Path
import argparse
import hashlib
import json
import struct
import sys
import types

ROOT = next(p for p in Path(__file__).resolve().parents if (p / 'src/program.json').is_file())
sys.dont_write_bytecode = True
if not __debug__:
    raise RuntimeError('Run witness checks without Python -O')
sys.path.insert(0, str(ROOT / 'tools'))
import behavior as b
import exe
import functions

IMAGE = exe.load()
SOURCE_PINS = {
    'src/root/m1C62.c': '3acba3b8e221d554b0ec7b2e26870389682ae9db629ca882b9e95d22adfc4d36',
    'src/root/m1A28.c': '5db49039ef64717680153a4b9445554b58ab2abf8a3c3fd9d67e6573af58a740',
}
ORACLE_PIN = 'aa0596c6766322a8229ee3c36e57048c92adc82d50fbe2ef37afb8b85fcf4f11'
DATA = 0x55B30
GUARD = DATA + 0x54F8
RECORDS = 0x50F60 + 0x3958

def machine(name):
    return b.Machine(types.SimpleNamespace(function=functions.get(name),
        vectors={exe.MANAGER_SEG * 16 + v.offset: v for v in IMAGE.vectors}))

def pin(path):
    return {'path': path.relative_to(ROOT).as_posix(),
            'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}

def require_pin(raw, expected, label):
    actual = hashlib.sha256(raw).hexdigest()
    if actual != expected:
        raise ValueError('reviewed input pin differs: ' + label)

def verify_inputs():
    for path, expected in SOURCE_PINS.items():
        require_pin((ROOT / path).read_bytes(), expected, path)
    if IMAGE.sha256 != ORACLE_PIN:
        raise ValueError('reviewed oracle pin differs')
    require_pin(IMAGE.path.read_bytes(), ORACLE_PIN, 'oracle')
    inventory = json.loads((ROOT / 'src/program.json').read_text())
    for path, expected in SOURCE_PINS.items():
        rows = [m for m in inventory['modules'] if m.get('source') == path]
        if len(rows) != 1 or rows[0]['source_sha256'] != expected:
            raise ValueError('current canonical inventory differs: ' + path)
    return [pin(IMAGE.path)] + [pin(ROOT / p) for p in [*SOURCE_PINS, 'tools/behavior.py',
        'tools/exe.py', 'tools/functions.py', 'layout/symbols.json',
        'layout/functions.json', 'layout/oracle.lock.json', 'src/program.json']]

def guard_case(value):
    m = machine('Punt')
    entered = []
    stop = None
    deps = {b.symbol_address(n): n for n in
            ['vsprintf', 'sprintf', 'printf', 'f_1CE2_01C3', 'o15_384C_0152']}
    def code(cpu, address, size, user):
        nonlocal stop
        if address in deps:
            entered.append(deps[address])
            if value == 0:
                stop = deps[address]
                cpu.emu_stop()
    m.cpu.hook_add(b.uc.UC_HOOK_CODE, code)
    c = b.Case('guard-' + str(value), args=[0, 0x7000],
        writes=[(GUARD, b.words(value)), (0x70000, b'guard probe\0')],
        return_kind='void', observe=[b.Range('guard', GUARD, 2)])
    if value:
        result = m.run(c)
        assert m.completed and entered == [] and m.word(GUARD) == value
        return {'incoming_guard': value, 'returns': True, 'dependency_entries': entered,
                'blocks': result['blocks'], 'guard_after': value}
    try:
        m.run(c)
        raise AssertionError('zero guard unexpectedly returned')
    except b.ExecutionError:
        assert stop == 'vsprintf' and m.word(GUARD) == 1 and not m.completed
    return {'incoming_guard': 0, 'returns': 'UNPROVED',
            'dependency_entries': entered, 'stop': stop, 'guard_after': m.word(GUARD)}

def dos_punt_case(errno):
    m = machine('DosPunt')
    entered = []
    def code(cpu, address, size, user):
        if address == b.symbol_address('Punt'):
            entered.append('Punt')
    m.cpu.hook_add(b.uc.UC_HOOK_CODE, code)
    result = m.run(b.Case('DosPunt-errno-' + str(errno), args=[0, 0x7000],
        writes=[(GUARD, b.words(1)), (b.symbol_address('errno'), b.words(errno)),
                (0x70000, b'guard probe\0')], return_kind='void'))
    assert entered == ['Punt'] * (2 if errno == 24 else 1) and m.completed
    return {'incoming_guard': 1, 'errno': errno, 'Punt_calls': len(entered),
            'returns': True, 'blocks': result['blocks']}

def open_db_prefix(occupied):
    m = machine('OpenDB')
    reached = False
    entered = []
    def code(cpu, address, size, user):
        nonlocal reached
        if address == b.symbol_address('Punt'):
            entered.append('Punt')
        if address == 0x1A280 + 0x49:
            reached = True
            cpu.emu_stop()
    m.cpu.hook_add(b.uc.UC_HOOK_CODE, code)
    slots = bytearray(4 * 124)
    for i in range(occupied):
        slots[i * 124] = ord('A') + i
    writes = [(GUARD, b.words(1)), (DATA + 0x394E, b.words(1)),
              (RECORDS, bytes(slots)), (0x70000, b'guard-probe\0')]
    try:
        m.run(b.Case('OpenDB-slots-' + str(occupied), args=[0, 0x7000],
            writes=writes, max_instructions=10000))
        raise AssertionError('prefix unexpectedly ran to return')
    except b.ExecutionError:
        assert reached, m.error
    index = occupied if occupied < 4 else -1
    destination = RECORDS + index * 124
    assert m.read(destination, 12) == b'guard-probe\0'
    assert m.read(destination + 79, 1) == b'\0'
    assert m.reg('si') == (index & 65535)
    assert entered == ([] if occupied < 4 else ['Punt'])
    return {'occupied_records': occupied, 'incoming_guard': 1,
            'GetFreeHandle_result': index, 'Punt_calls': len(entered),
            'original_name_copy_completed': True,
            'name_destination': '50F6:' + format(destination - 0x50F60, '04X'),
            'out_of_record_owner': index < 0,
            'stop': '1A28:0049 immediately after original CopyRootName returns'}

def probe():
    inputs = verify_inputs()
    cases = {'Punt_guard': [guard_case(v) for v in [0, 1, 2, 65535]],
             'DosPunt_guard': [dos_punt_case(e) for e in [2, 24]],
             'OpenDB_copy_prefix': [open_db_prefix(n) for n in range(5)]}
    if inputs != verify_inputs():
        raise ValueError('inputs changed during replay')
    return {'schema': 'punt-guard-database-prefix-v1',
        'status': 'PASS', 'scope': 'Isolated unchanged-original instructions with explicit incoming guard/occupancy fixtures; no DOS calls or callbacks modeled.',
        'oracle_sha256': IMAGE.sha256, 'unicorn_version': b.uc.__version__,
        'input_pins': inputs, 'implementation': pin(Path(__file__).resolve()),
        'cases': cases,
        'nonclaims': ['No original full-game runtime acceptance (DOSBox-X is authoritative).',
            'No proof ordinary startup/game reaches incoming nonzero guard with four occupied records.',
            'No proof first Punt reaches fatal overlay, returns, exits, or preserves fatal state.',
            'No semantic waiver for relocation of preceding storage; no extra record/slot is admitted.']}

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out', required=True, type=Path)
    out = ap.parse_args().out.resolve()
    if out.exists() or not out.is_relative_to(ROOT / 'build'):
        ap.error('--out must be fresh beneath build/')
    receipt = probe()
    out.mkdir(parents=True)
    (out / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print('PASS: nonzero Punt guard returns; guarded four-full OpenDB writes original record[-1] prefix')

if __name__ == '__main__':
    main()
