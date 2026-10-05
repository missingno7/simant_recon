"""Independent asset wire parser used only by the native database test.

The expected payload file is never linked into the program or returned by its
database/handle services. The actual TUs read and decode the original DAT files.
"""
from pathlib import Path
import struct
from index_fixture_logic import parse_index


def lzss_payload(packed: bytes, size: int) -> bytes:
    ring = bytearray(b' ' * 4096)
    write = 4096 - 18
    cursor, flags = 0, 0
    result = bytearray()
    while len(result) < size:
        flags >>= 1
        if not flags & 0x100:
            if cursor >= len(packed):
                raise ValueError('truncated LZSS flag')
            flags = packed[cursor] | 0xff00
            cursor += 1
        if flags & 1:
            if cursor >= len(packed):
                raise ValueError('truncated LZSS literal')
            values = [packed[cursor]]
            cursor += 1
            for value in values:
                result.append(value)
                ring[write] = value
                write = (write + 1) & 4095
        else:
            if cursor + 2 > len(packed):
                raise ValueError('truncated LZSS reference')
            low, high = packed[cursor:cursor + 2]
            cursor += 2
            read = low | ((high & 0xf0) << 4)
            length = (high & 15) + 3
            for _ in range(length):
                if len(result) == size:
                    break
                value = ring[read]
                read = (read + 1) & 4095
                result.append(value)
                ring[write] = value
                write = (write + 1) & 4095
    return bytes(result)


def fnv64(raw):
    value = 14695981039346656037
    for byte in raw:
        value = ((value ^ byte) * 1099511628211) & ((1 << 64) - 1)
    return value


def write_expected_payloads(assets: Path, output: Path) -> dict:
    fixture = bytearray(struct.pack('<IH', 0x31445257, 3))
    record_count, compressed_count = 0, 0
    aggregate = 14695981039346656037
    for stem in ('HCEGANT', 'SHARED', 'SOUND'):
        count, _, rows = parse_index(assets / (stem + '.NDX'))
        data = (assets / (stem + '.DAT')).read_bytes()
        fixture.extend(struct.pack('<H', count))
        for offset, ident, kind, flags in rows[:count]:
            header = 14 + offset
            if header + 10 > len(data):
                raise ValueError('truncated DAT record header')
            stored_size = struct.unpack_from('<H', data, header + 6)[0]
            stored = data[header + 10:header + 10 + stored_size]
            if len(stored) != stored_size:
                raise ValueError('truncated DAT record payload')
            if not stored_size or not flags & 1:
                payload = stored
            elif flags & 4:
                payload = b'\xff\xff' + stored
            else:
                if stored_size < 2:
                    raise ValueError('missing LZSS output-size prefix')
                size = struct.unpack_from('<H', stored)[0]
                payload = lzss_payload(stored[2:], size)
                compressed_count += 1
            fixture.extend(struct.pack('<hBBI', ident, kind, flags, len(payload)) + payload)
            aggregate ^= (fnv64(payload) + ((ident & 0xffff) << 32) + kind) & ((1 << 64) - 1)
            aggregate = (aggregate * 1099511628211) & ((1 << 64) - 1)
            record_count += 1
    # Existing independently recorded resource corpus identity, not a native
    # decoder result. This catches a changed expectation parser/corpus.
    if (record_count, compressed_count, aggregate) != (840, 205, 0x2cd5f2c76ee8a96e):
        raise ValueError('independent resource corpus aggregate differs')
    output.write_bytes(fixture)
    return {'records': record_count, 'lzss_records': compressed_count,
            'aggregate_fnv1a64': f'{aggregate:016x}', 'fixture_bytes': len(fixture)}
