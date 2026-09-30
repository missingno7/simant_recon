"""Expand Microsoft 'SZ ' (SZ 20 88 F0 27 33 D1) LZSS-compressed files (MSC 6.00 .XX$ media).
Validated by reproducing the DECOMP 1.02 output hashes recorded in C:/tools/msc-6.00a-dos-libs/provenance.json."""
import sys, struct, hashlib
def unsz(data, start):
    assert data[:8] == b'SZ \x88\xf0\x27\x33\xd1', data[:8]
    size = struct.unpack_from('<I', data, 8)[0]
    win = bytearray(b' ' * 4096); pos = start
    out = bytearray(); i = 12
    while i < len(data) and len(out) < size:
        flags = data[i]; i += 1
        for b in range(8):
            if i >= len(data) or len(out) >= size: break
            if flags & (1 << b):
                c = data[i]; i += 1; out.append(c); win[pos] = c; pos = (pos + 1) & 0xFFF
            else:
                lo, hi = data[i], data[i+1]; i += 2
                off = lo | ((hi & 0xF0) << 4); ln = (hi & 0x0F) + 3
                for k in range(ln):
                    c = win[(off + k) & 0xFFF]; out.append(c); win[pos] = c; pos = (pos + 1) & 0xFFF
    return bytes(out[:size])
if __name__ == '__main__':
    src, dst = sys.argv[1], sys.argv[2]
    start = int(sys.argv[3], 0) if len(sys.argv) > 3 else 4096 - 18
    d = unsz(open(src, 'rb').read(), start)
    open(dst, 'wb').write(d)
    print(dst, len(d), hashlib.sha256(d).hexdigest())
