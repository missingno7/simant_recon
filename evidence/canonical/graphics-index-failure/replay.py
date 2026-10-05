"""Bounded original execution after the real driver-callback reset.

This validates one graphics-index failure prefix, stopping at the end of the
first glyph's row loop. It does not claim eventual fatal-helper or exit behavior.
Original instructions are validation inputs only; no linked game is built here.
"""
from pathlib import Path
import argparse
import hashlib
import json
import struct
import sys
import types

sys.dont_write_bytecode = True
if not __debug__:
    raise RuntimeError('Run witness checks without Python -O')
ROOT = next(p for p in Path(__file__).resolve().parents
            if (p / 'src/program.json').is_file() and (p / 'tools/behavior.py').is_file())
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--out', required=True, type=Path)
options = parser.parse_args()
BUILD = (ROOT / 'build').resolve()
OUT = (options.out if options.out.is_absolute() else ROOT / options.out).resolve()
if not BUILD.is_relative_to(ROOT.resolve()) or OUT == BUILD or not OUT.is_relative_to(BUILD):
    parser.error('--out must resolve strictly beneath repository build/')
if OUT.exists():
    parser.error('--out must be fresh')
sys.path.insert(0, str(ROOT / 'tools'))
import behavior as b
import canonical
import csrc
import exe
import functions
import modules

DGROUP = 0x55B3
DATA = DGROUP * 16
RASTER = 0x1FBD
FIRST_ROW = RASTER * 16 + 0x93
ROW_DONE = RASTER * 16 + 0x98
IMAGE = exe.load()
PROGRAM = canonical.load()
MANIFEST = modules.load_manifest()
KEYS = ['root:1B4E', 'root:205F', 'root:1986', 'root:1A28',
        'root:1C62', 'root:1CE2', 'root:24AB', 'root:1FBD']


def pin(path):
    raw = path.read_bytes()
    return {'path': path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else str(path),
            'size': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def c_body(source, name):
    text = source.read_bytes().decode('latin1')
    function = csrc.Source(text).function(name)
    return text[function.body.s:function.body.e]


def static_order():
    body = c_body(ROOT / 'src/root/m205F.c', 'f_205F_0004')
    reset = body.index('f_1B4E_0025();')
    database = body.index('db_SetDataBase(path);')
    cursor = body.index('f_1B28_0006();')
    first_driver = body.index('o00_31AD_2AB4();')
    font = body.index('(*g_9130)();')
    assert reset < database < cursor < first_driver < font
    # Reset is the first call; preceding material consists only of local declarations.
    assert '(' not in body[:reset]
    raster_source = (ROOT / 'src/root/m1FBD.asm').read_text(encoding='latin1')
    assert 'L0093:\n\tmovsb\n\tadd di, dx\n\tloop L0093\n\tmov di, ax' in raster_source
    return {'order': ['real callback reset', 'database open', 'cursor setup',
                      'video driver setup', 'font callback'],
            'scope': 'Static current complete-TU order only; full f_205F_0004 is not executed.'}


def read_string(machine, address, maximum=250):
    raw = machine.read(address, maximum)
    assert b'\0' in raw, 'fixture expected a bounded NUL-terminated string'
    return raw.split(b'\0', 1)[0]


def execute(height):
    pair = types.SimpleNamespace(function=functions.get('OpenIndex'),
        vectors={exe.MANAGER_SEG * 16 + v.offset: v for v in IMAGE.vectors})
    machine = b.Machine(pair)
    entries = []
    addresses = []
    row_entry = None
    at_stop = False
    phase = 'reset'
    observed = {}
    watched = {'fatal_guard': (DATA + 0x54F8, 2),
               'callback_table': (b.symbol_address('g_9128'), 100),
               'font_pointer': (DATA + 0x3DD6, 4), 'font_height': (DATA + 0x3DDA, 2)}
    state_before_rows = None
    named = {b.symbol_address(name): name for name in
        ('OpenIndex', 'DosPunt', 'Punt', 'sprintf', 'vsprintf',
         'f_1B4E_000C', 'f_1CE2_01C3', 'f_24AB_038D', 'f_1FBD_0000')}

    def code(cpu, address, size, user):
        nonlocal row_entry, at_stop, state_before_rows
        if phase != 'failure':
            return
        if address in named:
            name = named[address]
            entries.append(name)
            if name == 'f_1FBD_0000':
                frame = machine.reg('ss') * 16 + machine.reg('sp')
                off, seg = struct.unpack('<HH', machine.read(frame + 8, 4))
                observed['fatal_text'] = read_string(machine, seg * 16 + off).decode('ascii')
        if address == FIRST_ROW and row_entry is None:
            row_entry = {r: machine.reg(r) for r in ('cx', 'dx', 'di', 'si', 'ds', 'es', 'ss', 'sp', 'eflags')}
            state_before_rows = {name: machine.read(at, width).hex() for name, (at, width) in watched.items()}
        if address == ROW_DONE:
            at_stop = True
            cpu.emu_stop()

    def write(cpu, access, address, size, value, user):
        if phase == 'failure' and machine.reg('cs') == RASTER and machine.reg('ip') == 0x93:
            assert size == 1
            addresses.append(address)

    machine.cpu.hook_add(b.uc.UC_HOOK_CODE, code)
    machine.cpu.hook_add(b.uc.UC_HOOK_MEM_WRITE, write)
    # The original resident data and zeroed mapped BSS have their ordinary
    # startup representations. The path and valid call frame belong to this test.
    assert machine.read(b.symbol_address('g_9128'), 100) == bytes(100)
    for offset, size in ((0x3DD6, 4), (0x3DDA, 2), (0x3DDC, 2), (0x54F8, 2), (0x65A4, 4)):
        assert machine.read(DATA + offset, size) == bytes(size)
    assert machine.word(DATA + 0x3DDE) == 8
    assert machine.read(b.symbol_address('g_5A97'), 1) == b'\xff'
    machine.run(b.Case('actual-driver-reset', return_kind='void',
        writes=[(0x70000, b'hcegant\0'), (b.symbol_address('g_5A97'), b'\0')]),
        original_entry=b.symbol('f_1B4E_0025'))
    empty = b.symbol('f_1B4E_000C')
    callback = struct.pack('<HH', empty['off'], empty['seg'])
    assert machine.read(b.symbol_address('g_9128'), 100) == callback * 25
    if height:
        # Typed positive controls only. The failing baseline changes no font state.
        machine.set_word(DATA + 0x3DDA, height)
    phase = 'failure'

    def open_failed(cpu, args):
        name = read_string(cpu, args[1] * 16 + args[0]).decode('ascii')
        assert name == 'hcegant.ndx' and args[2] == 0x8002
        observed['open'] = {'name': name, 'flags': args[2], 'return': -1, 'errno': 2}
        cpu.set_word(b.symbol_address('errno'), 2)
        return -1

    def print_newlines(cpu, args):
        assert read_string(cpu, args[1] * 16 + args[0]) == b'\n\n\n\n'
        observed['stdout'] = '\n\n\n\n'
        return 4

    try:
        machine.run(b.Case('post-reset-graphics-index-failure', args=[0, 0x7000, 1],
            return_kind='void', callbacks={'open': b.Callback(3, open_failed),
                                          'printf': b.Callback(2, print_newlines)},
            max_instructions=600000, max_blocks=200000),
            preserve=True, original_entry=b.symbol('OpenIndex'))
        raise AssertionError('failure prefix unexpectedly returned')
    except b.ExecutionError:
        if not at_stop:
            raise
    assert (machine.reg('cs'), machine.reg('ip')) == (RASTER, 0x98)
    assert machine.error is None and row_entry is not None
    assert entries == ['OpenIndex', 'sprintf', 'DosPunt', 'Punt', 'vsprintf', 'sprintf',
                       'f_1B4E_000C', 'f_1CE2_01C3', 'vsprintf', 'f_24AB_038D', 'f_1FBD_0000']
    assert observed['fatal_text'] == ('FATAL ERROR: PROGRAM ABORTED\nIndex file missing\n'
                                      'Dos error: 2: No such file or directory')
    assert len(observed['fatal_text']) == 87
    assert row_entry['cx'] == height and row_entry['dx'] == 78
    assert row_entry['di'] == 0x5ABE and row_entry['es'] == DGROUP
    assert row_entry['ds'] == 0 and not row_entry['eflags'] & 0x400
    count = height or 65536
    expected = [DATA + ((0x5ABE + 79 * i) & 0xFFFF) for i in range(count)]
    assert addresses == expected and machine.reg('cx') == 0
    assert len(set(addresses)) == count
    state_after_rows = {name: machine.read(at, width).hex() for name, (at, width) in watched.items()}
    if height == 0:
        assert set(addresses) == set(range(DATA, DATA + 65536))
        assert addresses[14] - (DATA + 0x5ABE) == 1106
        assert addresses[17] - (DATA + 0x5ABE) == 1343
        assert state_before_rows != state_after_rows
    else:
        assert state_before_rows == state_after_rows
    return {'height': height, 'real_reset': {'slots': 25, 'callback': '1B4E:000C'},
            'entries': entries, 'boundaries': observed, 'row_entry': row_entry,
            'state_before_rows': state_before_rows, 'state_after_rows': state_after_rows,
            'fixture_selector': 'g_5A97=0 (supported EGA selector); hardware detection is not executed',
            'stop': '1FBD:0098 before MOV DI,AX', 'row_stores': count,
            'distinct_offsets': len(set(addresses)),
            'address_trace_sha256': hashlib.sha256(b''.join(struct.pack('<I', a) for a in addresses)).hexdigest(),
            'first_offsets': [a - DATA for a in addresses[:18]],
            'last_offsets': [a - DATA for a in addresses[-3:]],
            'entire_DGROUP_offset_space_visited': height == 0}


def main():
    paths = [ROOT / p for p in ['src/program.json', 'layout/manifest.json',
        'layout/toolchain.json', 'tools/behavior.py', 'tools/exe.py', 'tools/modules.py',
        'tools/canonical.py', 'tools/omf.py', 'tools/compiler.py'] +
        [next(m['source'] for m in PROGRAM['modules'] if m['key'] == k) for k in KEYS]]
    input_pins = [pin(p) for p in paths]
    implementation = pin(Path(__file__).resolve())
    order = static_order()
    comparisons = []
    for key in KEYS:
        item = next(m for m in PROGRAM['modules'] if m['key'] == key)
        path = ROOT / item['source']
        assert pin(path)['sha256'] == item['source_sha256']
        module = MANIFEST['modules'][key]
        result = modules.verify_module(path.read_bytes().decode('latin1'), module,
                                       module['claims'], man=MANIFEST)
        errors = canonical.audit_context(key, result, module['canonical_admission']) if module.get('canonical_admission') else []
        assert result['exact'] or module.get('canonical_admission') and not errors, (key, errors)
        comparisons.append({'key': key, 'object_sha256': result['object_sha256'],
                            'comparison': canonical.observed(result)})
    cases = [execute(height) for height in (0, 1, 8, 13)]
    receipt = {'schema': 'post-reset-graphics-index-failure-v1', 'status': 'PASS',
        'scope': 'Actual driver reset followed by direct OpenIndex failure prefix through first glyph row loop.',
        'static_order': order, 'cases': cases, 'whole_TU_comparisons': comparisons,
        'input_pins': input_pins,
        'implementation': implementation, 'oracle': pin(IMAGE.path),
        'unicorn_version': b.uc.__version__, 'python_version': sys.version,
        'nonclaims': ['No independent DOS game executable', 'No full graphics/IBMInitStuff execution',
                     'No eventual continuation, fatal helper, cleanup or exit claim',
                     'No fifth database access witness', 'No allocated font bitmap or new storage',
                     'No code patch, linked original bytes or production fallback']}
    assert input_pins == [pin(p) for p in paths], 'inputs changed during witness execution'
    assert implementation == pin(Path(__file__).resolve()), 'runner changed during witness execution'
    OUT.mkdir(parents=True)
    (OUT / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    print('PASS: real 25-slot reset; four failure-prefix controls; first row visits 65536/1/8/13 offsets')


if __name__ == '__main__':
    main()
