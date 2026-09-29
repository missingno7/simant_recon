"""Build or verify layout/oracle.lock.json, the immutable description of the DOS originals.

    python tools/oracle.py --write     # (re)create the lock; refuses if it exists unless --force
    python tools/oracle.py             # verify current assets against the lock

The lock records identities and structure only.  It is never used as a source
of reconstructed bytes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import exe as exemod  # noqa: E402

ROOT = exemod.ROOT
LOCK = ROOT / "layout" / "oracle.lock.json"
COMMON_TAIL_SIZE = 256


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def mz_summary(d: bytes) -> dict:
    f = struct.unpack_from("<13H", d, 2)
    h = exemod.MZHeader(*f)
    return {"file_size_declared": h.file_size, "header_bytes": h.header_size, "relocations": h.reloc_count,
            "cs": h.cs, "ip": h.ip, "ss": h.ss, "sp": h.sp, "min_alloc": h.min_alloc, "max_alloc": h.max_alloc,
            "checksum": h.checksum, "reloc_offset": h.reloc_offset, "overlay_number": h.overlay_number}


def build() -> dict:
    inputs = {}
    for p in sorted(exemod.ASSETS.iterdir()):
        if p.is_file():
            b = p.read_bytes()
            inputs[p.name] = {"size": len(b), "sha256": sha(b)}
    x = exemod.load()
    d = x.raw
    tail = d[-COMMON_TAIL_SIZE:]
    same_tail = {}
    for other in ("INFO.EXE", "INSTALL.EXE"):
        ob = (exemod.ASSETS / other).read_bytes()
        same_tail[other] = ob[-COMMON_TAIL_SIZE:] == tail
    pad_start = x.mz.file_size
    pad_end = x.sections[0].file_para * 16
    lock = {
        "schema": "simant-oracle-lock-v1",
        "inputs": inputs,
        "executable": {
            "name": "SIMANT.EXE",
            "sha256": x.sha256,
            "size": len(d),
            "packed": False,
            "packing_note": "No EXEPACK/LZEXE: relocation table populated, image is plain code/data. "
                            "INFO.EXE and INSTALL.EXE are EXEPACKed separately (0 MZ relocations, "
                            "'Packed file is corrupt').",
            "mz": {**mz_summary(d), "load_image": {"size": len(x.image), "sha256": sha(x.image)},
                   "header_sha256": sha(x.header_bytes),
                   "relocations_sha256": sha(d[x.mz.reloc_offset:x.mz.reloc_offset + 4 * x.mz.reloc_count]),
                   "relocation_order": "link order; within a module, object FIXUPP order"},
            "post_image_padding": {"start": pad_start, "end": pad_end,
                                   "all_zero": all(v == 0 for v in d[pad_start:pad_end])},
            "rtlink": {
                "product": "Pocket Soft RTLink/Plus (overlay manager strings '.RTLink CACHE', eov/eca/evm error codes)",
                "manager_segment": exemod.MANAGER_SEG,
                "section_table": {"offset": exemod.SECTION_TABLE_OFF, "count_offset": exemod.SECTION_COUNT_OFF},
                "vector_table": {"offset": exemod.VECTOR_TABLE_OFF, "count": len(x.vectors), "entry_size": 10,
                                 "sha256": sha(b"".join(struct.pack("<HHHH", v.offset, v.target_seg, v.target_off, v.section)
                                                         for v in x.vectors))},
                "sections": [
                    {"index": s.index, "load_seg": s.load_seg, "word1": s.word1, "file_para": s.file_para,
                     "flags": s.flags, "mem_paras": s.mem_paras, "reloc_count": s.reloc_count, "word6": s.word6,
                     "section_id": s.section_id, "file_paras": s.file_paras,
                     "data_file_offset": s.data_file_offset,
                     "data_sha256": sha(s.data),
                     "relocations_sha256": sha(b"".join(struct.pack("<HH", o, sg) for sg, o in s.relocs)),
                     "reloc_padding_zero": all(v == 0 for v in d[s.file_para * 16 + 4 * s.reloc_count:s.data_file_offset]),
                     "role": "overlay" if s.is_overlay else "resident-data"}
                    for s in x.sections],
                "overlay_areas": sorted({s.load_seg for s in x.sections if s.is_overlay}),
                "inter_section_padding_zero": all(
                    all(v == 0 for v in d[a.data_file_offset + len(a.data):b.file_para * 16])
                    for a, b in zip(x.sections, x.sections[1:])),
            },
            "common_tail": {
                "offset": len(d) - COMMON_TAIL_SIZE, "size": COMMON_TAIL_SIZE, "sha256": sha(tail),
                "identical_in": same_tail,
                "note": "256 bytes appended to all three EXEs (contains a PC BIOS F000:FFxx fragment dated 06/13/90). "
                        "Not linker output; section 27's declared last paragraph overlaps its first 3 bytes.",
                "section27_overlap": (x.sections[-1].data_file_offset + len(x.sections[-1].data)) - (len(d) - COMMON_TAIL_SIZE),
            },
        },
    }
    return lock


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    cur = build()
    if a.write:
        if LOCK.exists() and not a.force:
            print("lock exists; use --force to rewrite")
            return 1
        LOCK.write_text(json.dumps(cur, indent=1) + "\n")
        print(f"wrote {LOCK}")
        return 0
    old = json.loads(LOCK.read_text())
    if old != cur:
        print("ORACLE MISMATCH: assets differ from layout/oracle.lock.json")
        return 1
    print(f"oracle OK: {cur['executable']['sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
