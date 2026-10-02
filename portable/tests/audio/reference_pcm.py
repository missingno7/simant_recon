"""Independent scalar transcription of DOS f_290D_000E for SOUND object 1."""
from __future__ import annotations

import hashlib
import struct
import sys
from pathlib import Path


def main() -> None:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else "assets") / "SOUND"
    ndx = root.with_suffix(".NDX").read_bytes()
    dat = root.with_suffix(".DAT").read_bytes()
    count = struct.unpack_from("<H", ndx)[0]
    entry = next((ndx[20 + i * 8:28 + i * 8] for i in range(count)
                  if struct.unpack_from("<h", ndx, 24 + i * 8)[0] == 1 and
                  ndx[26 + i * 8] == 5), None)
    if entry is None:
        raise SystemExit("SOUND resource 1 kind 5 not found")
    offset = struct.unpack_from("<I", entry)[0]
    record = 14 + offset
    stored_size = struct.unpack_from("<H", dat, record + 6)[0]
    source = dat[record + 10:record + 10 + stored_size]
    if len(source) != stored_size or stored_size < 16:
        raise SystemExit("sample record is truncated")

    delta = source[:16]
    accumulator = 0x80
    decoded = bytearray()
    for packed in source[16:]:
        for nibble in (packed >> 4, packed & 0x0f):
            accumulator = (accumulator + delta[nibble]) & 0xff
            decoded.append(accumulator)
    digest = hashlib.sha256(decoded).hexdigest()
    if len(decoded) != 752 or digest != "9fc510cf3285d78b8ba322ed8792ddb4f73e9e8524fcc313e56ceb6817d2861f":
        print(f"decoded_bytes={len(decoded)} sha256={digest}")
        raise SystemExit("DOS decoder reference fingerprint changed")
    print(f"PASS source=f_290D_000E resource=1/5 bytes={len(decoded)} sha256={digest}")


if __name__ == "__main__":
    main()
