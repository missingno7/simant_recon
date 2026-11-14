"""Original-instruction controls and finite interval proof for IRQ coordinate words.

Run directly, or via input_irq/run.py. No original bytes enter native sources.
The 320-wide result is conditional arithmetic, not a claim about absent resources.
"""
from pathlib import Path
import argparse
import hashlib
import json
import struct
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools'))
sys.path.insert(0, str(ROOT / 'build/deps/unicorn'))
import exe
from unicorn import Uc, UC_ARCH_X86, UC_MODE_16, UC_HOOK_CODE
from unicorn.x86_const import (UC_X86_REG_CS, UC_X86_REG_DS, UC_X86_REG_SS,
    UC_X86_REG_SP, UC_X86_REG_BP, UC_X86_REG_AX, UC_X86_REG_SI, UC_X86_REG_DI,
    UC_X86_REG_IP)


def s16(v):
    return ((v + 32768) & 65535) - 32768


def div0(v, divisor):
    return v // divisor if v >= 0 else -((-v) // divisor)


def model(h, v, left, top, width):
    x, y = s16(h - left), s16(v - top)
    if width == 320:
        x, y = s16((x + 2) * 2), s16((y - 8) * 2)
    y = div0(s16(y - 67), 10)
    x = div0(s16(s16(y * 10) - 169 + x), 28)
    return x, y


def geometry():
    # Parse the actual uncompressed window records, not a copied rectangle.
    sys.path.insert(0, str(ROOT / 'evidence/canonical/native-window-boundary'))
    from replay import parse_resources
    resources, offsets = parse_resources(ROOT)
    rows = {r['resource_id']: r for r in resources['resources']
            if r['database'] == 'HCEGANT'}
    data = (ROOT / 'assets/HCEGANT.DAT').read_bytes()

    def obj(win, index):
        record = rows[win]['objects'][index]
        at = offsets['HCEGANT', win] + record['offset']
        return struct.unpack_from('<12h', data, at + 8)

    # Yard/map cannot resize or zoom; minimap cannot drag/resize/zoom.
    assert rows[25]['window_flags'] == rows[1]['window_flags'] == 0x406
    assert rows[20]['window_flags'] == 0x1841
    assert obj(25, 0)[:4] == (62, 62, 516, 324)
    assert obj(25, 1)[:8] == (1, 2, -2, 19, 6400, 6400, 6400, 6401)
    assert obj(25, 2)[:8] == (1, 19, 513, 256, 6401, 6401, 6402, 6402)
    assert obj(20, 0)[:8] == (4, 0, 132, 68, 5, 5, 5120, 5120)
    assert obj(20, 1)[:8] == (2, 2, 128, 64, 5120, 5120, 5121, 5121)
    # Edit object 5 anchors minimap; its top is edit-root top + 22.
    assert obj(0, 1)[:4] == (2, 2, -2, 18)
    assert obj(0, 3)[:4] == (0, 17, 48, -3)
    assert obj(0, 5)[:4] == (3, 3, 41, 11)
    index = (ROOT / 'assets/HCEGANT.NDX').read_bytes()
    mode0 = [struct.unpack_from('<IhBB', index, 20 + i * 8)
             for i in range(struct.unpack_from('<H', index)[0])
             if struct.unpack_from('<IhBB', index, 20 + i * 8)[1:3] == (0, 9)]
    assert len(mode0) == 1 and mode0[0][3] == 8
    yard_mode0 = struct.unpack_from('<4h', data, 14 + mode0[0][0] + 10 + 25 * 8)
    assert yard_mode0 == (62, 18, 516, 324)
    return {'assets': resources['assets'], 'yard_root_size': [516, 324],
            'yard_viewport_offset': [3, 21],
            'mode0_yard_root': list(yard_mode0),
            'minimap_size': [132, 68], 'minimap_content_size': [128, 64],
            'conservative_yard_top': [1, 501], 'minimap_vertical_envelope': [1, 480]}


def check():
    image = exe.load()  # enforces the immutable oracle's SHA-256
    vm = Uc(UC_ARCH_X86, UC_MODE_16)
    vm.mem_map(0, 0x110000)
    base, root = image.unit_bytes('root')
    vm.mem_write(base, root)
    for index in (22, 27):
        section = image.sections[index]
        vm.mem_write(section.load_linear, section.data)
    vm.reg_write(UC_X86_REG_DS, 0x55b3)
    vm.reg_write(UC_X86_REG_SS, 0x9000)
    vm.reg_write(UC_X86_REG_BP, 0x8000)
    def words(at, *values):
        vm.mem_write(at, struct.pack('<' + 'H' * len(values), *(v & 65535 for v in values)))
    assert bytes(vm.mem_read(0x55b30 + 0x2a42, 4)) == struct.pack('<2H', 169, 67)
    stop = 0x39c70 + 0x16de
    vm.hook_add(UC_HOOK_CODE, lambda u, a, n, _: u.emu_stop(), begin=stop, end=stop)
    count = 0
    def yard(h, v, left, top, width):
        nonlocal count
        words(0x98000 - 10, h, v)
        words(0x55b30 + 0x3db2, width)
        words(0x50f60 + 0x10d2, left, top)
        vm.reg_write(UC_X86_REG_CS, 0x39c7)
        vm.emu_start(0x39c70 + 0x1607, 0x39c70 + 0x166a, count=100)
        actual = s16(vm.reg_read(UC_X86_REG_DI)), s16(vm.reg_read(UC_X86_REG_SI))
        assert actual == model(h, v, left, top, width), (h, v, left, top, width, actual)
        valid = 0 <= actual[0] <= 11 and 0 <= actual[1] <= 15
        assert vm.reg_read(UC_X86_REG_IP) == (0x166a if valid else 0x16de)
        count += 1
        return actual

    geom = geometry()
    # This superset contains both EXEs' possible DGROUP and DL-cleared words.
    lo, hi = 0x5400, 0x9640
    # IDIV truncates toward zero: y in [0,15] iff its dividend is [-9,159].
    # Inverting the *modular* subtract covers every v without sampling it.
    for top in range(1, 502):
        accepted_v = {(top + 67 + n) & 65535 for n in range(-9, 160)}
        assert accepted_v.isdisjoint(range(lo, hi + 1))
        assert 0 not in accepted_v
    # Execute the original instructions for every segment in the superset,
    # including the signed discontinuity, at both extreme origins.
    for v in range(lo, hi + 1):
        for top in (1, 501):
            x, y = yard(2, v, 0, top, 640)
            assert not (0 <= x <= 11 and 0 <= y <= 15)
    # Horizontal residue cannot rescue an invalid row. Exercise non-E0, E0
    # and F0 words around horizontal signed overflow with the original code.
    for h in list(range(2, 65536, 256)) + [0, 255, 32767, 32768, 65535]:
        for v in (0, lo, 0x7fff, 0x8000, hi):
            for left, top in ((-513, 1), (642, 501)):
                x, y = yard(h, v, left, top, 640)
                assert not (0 <= x <= 11 and 0 <= y <= 15)
    # Positive control: a real pointer can select an occupied yard cell.
    assert yard(65 + 169 + 28, 83 + 67 + 10, 65, 83, 640) == (1, 1)
    # The 320 path is not uniform over segment words: preserve its counterexample.
    # Geometry is controlled here, NOT asserted reachable with missing LCEGANT.
    assert yard(258, 0x8078, 65, 83, 320) == (7, 0)
    assert yard(258, 0, 65, 83, 320)[1] < 0

    def point(h, v, left, top, right, bottom):
        words(0x55b30 + 0x100, h, v)
        words(0x55b30 + 0x110, left, top, right, bottom)
        words(0x97000, 0, 0x8000, 0x100, 0x55b3, 0x110, 0x55b3)
        vm.reg_write(UC_X86_REG_SP, 0x7000)
        vm.reg_write(UC_X86_REG_CS, 0x1fd2)
        vm.emu_start(0x1fd20 + 0x4e5, 0x80000, count=100)
        return vm.reg_read(UC_X86_REG_AX)
    # Vertical envelope rejects all DOS words and zero independent of h.
    assert all(not (1 <= s16(v) < 480) for v in range(lo, hi + 1))
    for h in list(range(2, 65536, 256)) + [0, 255, 32767, 32768, 65535]:
        for v in (0, lo, 0x7fff, 0x8000, hi):
            assert point(h, v, -1, 1, 639, 480) == 0
    assert point(2, 2, 0, 1, 128, 65) == 1
    assert point(2, 65, 0, 1, 128, 65) == 0
    files = ['src/ui/minimap.c', 'src/ui/yellow_commands.c', 'src/ui/yard_window.c',
             'src/ui/view_commands.c', 'src/ui/view_dialog_helpers.c',
             'src/window/object_geometry.c', 'src/window/move_resize.c', 'src/window/lifecycle.c',
             'src/window/menu_helpers.c', 'src/platform/video/driver_select.c',
             'src/startup/dos_config.c']
    pins = {f: hashlib.sha256((ROOT / f).read_bytes()).hexdigest() for f in files}
    proof = json.loads((ROOT / 'evidence/canonical/native-input-irq/normal-words-proof.json').read_text())
    assert pins == proof['source_pins'], 'Geometry/source changed: redo the static review'
    assert geom == proof['geometry'], 'Shipped resource geometry changed: redo the static review'
    return {'passed': True, 'original_yard_instruction_cases': count,
            'oracle_sha256': exe.EXPECTED_SHA256, 'geometry': geom,
            'segment_word_superset': [lo, hi], 'vertical_origins': 501,
            'result_640': 'Both readers reject every DOS word and zero; all h.',
            'result_320': 'Conditional high-segment alias confirmed; resource reachability undecided.',
            'source_pins': pins}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    receipt = check()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(receipt, indent=2) + '\n')
    print('PASS IRQ normal words: original instructions, all 640-wide segment classes; 320 limit explicit')
