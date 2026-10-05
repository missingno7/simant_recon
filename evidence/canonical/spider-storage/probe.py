"""Bounded original DOS byte-access controls for the spider scratch contract.

Resource bytes and original instructions are validation inputs only. No linked
source provider, original-capacity assertion, or whole-game closure is produced.
"""
from pathlib import Path
import argparse
import hashlib
import json
import struct
import sys
import types

sys.dont_write_bytecode = True
ROOT = next(p for p in Path(__file__).resolve().parents if (p / 'src/program.json').is_file())
sys.path.insert(0, str(ROOT / 'tools'))
sys.path.insert(0, str(ROOT / 'portable/tests/native_database'))
import behavior as b
import exe
import functions
from index_fixture_logic import parse_index
from resource_fixture_logic import lzss_payload

IMAGE = exe.load()
BUF = 0x70000
SRC = 0x80000
CLIP = 0x90000
END = BUF + 6276


def words(*values):
    return struct.pack('<' + 'H' * len(values), *(v & 65535 for v in values))


def ptr(name):
    target = b.symbol(name)
    return words(target['off'], target['seg'])


def machine(name):
    pair = types.SimpleNamespace(function=functions.get(name),
        vectors={exe.MANAGER_SEG * 16 + v.offset: v for v in IMAGE.vectors})
    result = b.Machine(pair)
    touched = {'reads': set(), 'writes': set()}

    def access(cpu, kind, address, size, value, userdata):
        if result.active and BUF <= address < BUF + 0x10000:
            key = 'reads' if kind == b.uc.UC_MEM_READ else 'writes'
            touched[key].update(range(address - BUF, address - BUF + size))

    result.cpu.hook_add(b.uc.UC_HOOK_MEM_READ | b.uc.UC_HOOK_MEM_WRITE, access)
    return result, touched


def span(values):
    return {'minimum': min(values) if values else None,
            'maximum': max(values) if values else None,
            'unique_bytes': len(values),
            'beyond_6276': sorted(v for v in values if v >= 6276)[:8]}


def blob(stem, row):
    offset, ident, kind, flags = row
    raw = (ROOT / 'assets' / f'{stem}.DAT').read_bytes()
    at = 14 + offset
    size = struct.unpack_from('<H', raw, at + 6)[0]
    payload = raw[at + 10:at + 10 + size]
    if size and flags & 1:
        if flags & 4:
            payload = b'\xff\xff' + payload
        else:
            payload = lzss_payload(payload[2:], struct.unpack_from('<H', payload)[0])
    return payload


def signed_table(name, count):
    m, _ = machine('PreDrawSpider')
    return list(struct.unpack('<' + 'b' * count, m.read(b.symbol_address(name), count)))


def resource_controls():
    count, _, rows = parse_index(ROOT / 'assets/HCEGANT.NDX')
    selected = {ident: blob('HCEGANT', row) for row in rows[:count]
                for ident in [row[1]] if row[2] == 2 and (1000 <= ident <= 1007 or 1050 <= ident <= 1053)}
    assert set(selected) == set(range(1000, 1008)) | set(range(1050, 1054))
    xs = signed_table('fd_3D57_09BC', 8)
    ys = signed_table('fd_3D57_09C4', 8)
    deathx = signed_table('fd_3D57_09CC', 4)
    deathy = signed_table('fd_3D57_09D0', 4)
    result = []
    for ident, payload in sorted(selected.items()):
        typ, width, height = struct.unpack_from('<h', payload)[0], *struct.unpack_from('<hh', payload, 8)
        assert typ == 3 and width > 0 and height > 0
        index = ident - (1000 if ident < 1050 else 1050)
        basex = (xs if ident < 1050 else deathx)[index] + 48
        basey = (ys if ident < 1050 else deathy)[index] + 48
        all_extents = []
        for modx in range(16):
            for mody in range(16):
                x, y = basex + modx, basey + mody
                caprows = min(height, 112 - y)
                # The decoder touches a word at each final source byte. Account
                # for the high byte even when its rotated mask has no high bits.
                maximum = 4 + (y + caprows - 1) * 56 + 3 * 14 + x // 8 + (width + 7) // 8
                assert caprows > 0 and x >= 0 and y >= 0
                all_extents.append((maximum, x, y, caprows))
        high, x, y, caprows = max(all_extents)
        m, touched = machine('o00_35A6_0007')
        m.run(b.Case(f'hcegant-{ident}-greatest-access',
            args=[0, 0x8000, 0, 0x7000, x, y], return_kind='void',
            writes=[(SRC, payload[8:]), (BUF, words(112, 112) + bytes(6272))]))
        assert max(touched['reads']) == high == max(touched['writes'])
        assert not any(v >= 6276 for v in touched['reads'] | touched['writes'])
        result.append({'id': ident, 'payload_sha256': hashlib.sha256(payload).hexdigest(),
            'source_dimensions': [width, height], 'base_position': [basex, basey],
            'enumerated_positions': len(all_extents), 'greatest_access_position': [x, y],
            'rows': caprows, 'reads': span(touched['reads']), 'writes': span(touched['writes'])})
    return result


def line_controls():
    result = []
    for mode, width, height, expected in ((0, 112, 112, 1571), (1, 84, 84, 3531), (2, 112, 112, 6275)):
        m, touched = machine('f_16B5_0033')
        m.run(b.Case(f'bind-mode-{mode}', args=[0, 0x7000, mode], return_kind='void',
            writes=[(BUF, words(width, height) + bytes(6272))]))
        touched['reads'].clear()
        touched['writes'].clear()
        m.run(b.Case(f'last-pixel-mode-{mode}',
            args=[width - 1, height - 2, width - 1, height - 1, 15], return_kind='void'),
            preserve=True, original_entry=b.symbol('f_16B5_0008'))
        assert max(touched['reads']) == expected == max(touched['writes'])
        result.append({'mode': mode, 'dimensions': [width, height],
            'reads': span(touched['reads']), 'writes': span(touched['writes'])})
    return result


def resource_bound_negative_control():
    # Valid positive picture geometry at an actual source-produced death
    # placement (ID1050, modx=mody=0). This is a synthetic resource contrast,
    # never a claim about any absent shipped database's bytes or dimensions.
    m, touched = machine('o00_35A6_0007')
    width = height = 112
    rowbytes = (width + 7) // 8
    payload = words(width, height) + (bytes([255]) * rowbytes + bytes([165]) * (rowbytes * 4)) * height
    m.run(b.Case('missing-picture-bound-negative', args=[0, 0x8000, 0, 0x7000, 21, 23],
        return_kind='void', writes=[(SRC, payload), (BUF, words(112, 112) + bytes(6272))]))
    assert max(touched['reads']) == 6278 == max(touched['writes'])
    assert touched['writes'].issuperset({6276, 6277, 6278})
    return {'kind': 'synthetic grammar-valid dimension contrast only',
        'source_dimensions': [112, 112], 'actual_source_placement': [21, 23],
        'profile_decoder': 'o00_35A6_0007', 'reads': span(touched['reads']),
        'writes': span(touched['writes']),
        'scope': 'Proves picture dimension premise is necessary; does not prove an absent shipped picture has this size or that a game run reaches a spill.'}


def blit_controls():
    result = []
    profiles = [(0, 'S00', 'o00_31AD_0CF9', 'o00_31AD_0D06', 112, 112, 6275),
                (5, 'S01', 'o01_3126_073C', 'o01_3126_0749', 112, 112, 1571),
                (2, 'S03', 'o03_3126_091F', 'o03_3126_092C', 84, 84, 3531)]
    # The nominal planar/mono raw paths are corroboration controls. Tandy
    # hardware setup is not modeled by this standalone entry-state fixture.
    for mode, unit, driver, rawdriver, width, height, expected in profiles[:2]:
        for shift in (0, 1):
                    m, touched = machine(rawdriver)
                    y = 30
                    label = f'raw-screen-{mode}-x{shift}'
                    m.run(b.Case(label, args=[40 + shift, y, 4, 0x7000, width, height], return_kind='void',
                        writes=[(BUF, words(width, height) + bytes(6272)),
                            (b.symbol_address('g_5A97'), bytes([mode])),
                            (b.symbol_address('g_914C'), ptr(driver)),
                            (b.symbol_address('g_9150'), ptr(rawdriver)),
                            (b.symbol_address('g_5AAC'), words(0, 0x9000)),
                            (CLIP, words(0, 0, 640, 480) + words(0, -32768, 0, 0)),
                            (b.symbol_address('g_4333'), b'\x01'),
                            (b.symbol_address('g_3DB0'), words(0xA000)),
                            (b.symbol_address('g_3DB6'), words(80)),
                            (b.symbol_address('g_3DFC'), b''.join(words(i * 80) for i in range(480)))]))
                    assert max(touched['reads']) == expected and not touched['writes']
                    result.append({'case': label, 'profile': mode, 'x': 40 + shift, 'y': y,
                        'entry': rawdriver, 'prefix': [width, height],
                        'reads': span(touched['reads']), 'writes': span(touched['writes'])})
    return result


def sentinel_controls():
    """Check actual clipping with the public source outcode as a modeled leaf."""
    result = []
    for width, height, clipleft in ((112, 112, 0), (0, 0, 0), (0, 0, 1)):
        m, _ = machine('f_1D8E_003F')
        def outcode(cpu, args):
            x, y, off, seg = args
            x = x - 65536 if x >= 32768 else x
            y = y - 65536 if y >= 32768 else y
            left, top, right, bottom = struct.unpack('<hhhh', cpu.read(seg * 16 + off, 8))
            return ((0x80 if y < top else 0x40 if y >= bottom else 0)
                    + (0x20 if x < left else 0x10 if x >= right else 0))
        m.run(b.Case('sentinel-rectangle', args=[0, 0x7000, 0, 0x9000, 0, 0x8000, 0, 0],
            return_kind='farptr', writes=[(BUF, words(0, -32768, width, -32768 + height)),
                (CLIP, words(clipleft, 0, 640, 480))],
            callbacks={'f_1D8E_0002': b.Callback(4, outcode)}))
        first = list(struct.unpack('<hhhh', m.read(SRC, 8)))
        rejected = first[1] == -32768
        assert rejected == (height > 0 or clipleft > 0)
        result.append({'dimensions': [width, height], 'clip_left': clipleft,
            'first_output_rect': first, 'rejected': rejected,
            'modeled_helper': 'f_1D8E_0002 exact signed-coordinate source predicate; original f_1D8E_003F executes',
            'scope': 'Clipping result only. Zero-width raw-renderer effects and whole caller reachability are not claimed.'})
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', required=True, help='Fresh output directory beneath build/')
    args = parser.parse_args()
    import modctx
    output = Path(args.out)
    destination = modctx.under_build(output if output.is_absolute() else ROOT / output)
    destination.mkdir(parents=True, exist_ok=False)
    OUT = destination / 'receipt.json'
    lock = json.loads((ROOT / 'layout/oracle.lock.json').read_text())
    assert IMAGE.sha256 == lock['executable']['sha256']
    for name in ('HCEGANT.NDX', 'HCEGANT.DAT'):
        data = (ROOT / 'assets' / name).read_bytes()
        assert len(data) == lock['inputs'][name]['size']
        assert hashlib.sha256(data).hexdigest() == lock['inputs'][name]['sha256']
    receipt = {'schema': 'dos-spider-byte-access-controls-v1',
        'scope': 'Original functions at valid typed entry states; screen clip/table initialization are explicit fixtures, not a proof of actual startup/caller state.',
        'oracle_sha256': IMAGE.sha256,
        'pins': {rel: hashlib.sha256((ROOT / rel).read_bytes()).hexdigest() for rel in
            ('assets/HCEGANT.NDX', 'assets/HCEGANT.DAT', 'src/root/m0250.c', 'src/root/m16B5.asm',
             'src/root/m2662.c', 'src/root/m1D8E.c', 'src/S00/m35A6.asm', 'src/S00/m31AD.asm',
             'src/S01/m3126.asm', 'src/S03/m3126.asm')},
        'hcegant_sprite_controls': resource_controls(),
        'missing_resource_bound_negative_control': resource_bound_negative_control(),
        'last_pixel_line_controls': line_controls(),
        'screen_blit_controls': blit_controls(),
        'sentinel_clip_controls': sentinel_controls()}
    OUT.write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'receipt': str(OUT), 'resources': len(receipt['hcegant_sprite_controls']),
        'lines': len(receipt['last_pixel_line_controls']), 'blits': len(receipt['screen_blit_controls'])}))


if __name__ == '__main__':
    main()
