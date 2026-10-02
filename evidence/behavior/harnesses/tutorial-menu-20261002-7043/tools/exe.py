"""Parser for the DOS SIMANT.EXE: MZ root image plus Pocket Soft RTLink sections.

Format facts (verified against the original, see docs/exe-format.md):

* The MZ image is the RTLink *root*: game code, the MSC runtime entry and the
  RTLink overlay manager (entry point 0x2CFF:0x06F8, which chains to the MSC
  runtime entry at 0x29F4:0x001C after loading).
* The manager's section table lives at 0x2CFF:0x0B71, count word at 0x2CFF:0x0B6B,
  18-byte entries:
      load_seg, w1, file_para, flags, mem_paras, reloc_count, w6, section_id, file_paras
  ``file_para * 16`` is the file offset of the section record: first
  ``reloc_count`` (offset, segment) relocation words, padded to a paragraph,
  then ``file_paras * 16`` bytes of image.  Relocated segment values are
  load-relative, exactly like MZ relocations.
* Sections 0..26 are overlays sharing four overlay areas (0x3126, 0x35F5,
  0x384C, 0x39C7); section 27 (flags 0x100) is a resident extension loaded at
  0x3D57 that also contains DGROUP.
* Overlay calls from other code go through 10-byte vectors at 0x2CFF:0x25F6:
      E8 rel16 (call manager) ; EA off seg (jmp far target) ; dw section_index
  where ``section_index`` is 0xFFFF for a root target.

Nothing in this module writes files.  It only reads the immutable oracle.
"""
from __future__ import annotations

import hashlib
import struct
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
EXE_PATH = ASSETS / "SIMANT.EXE"
EXPECTED_SHA256 = "aa0596c6766322a8229ee3c36e57048c92adc82d50fbe2ef37afb8b85fcf4f11"

MANAGER_SEG = 0x2CFF
SECTION_COUNT_OFF = 0x0B6B
SECTION_TABLE_OFF = 0x0B71
VECTOR_TABLE_OFF = 0x25F6


@dataclass(frozen=True)
class MZHeader:
    last_page: int
    pages: int
    reloc_count: int
    header_paras: int
    min_alloc: int
    max_alloc: int
    ss: int
    sp: int
    checksum: int
    ip: int
    cs: int
    reloc_offset: int
    overlay_number: int

    @property
    def file_size(self) -> int:
        return (self.pages - 1) * 512 + self.last_page if self.last_page else self.pages * 512

    @property
    def header_size(self) -> int:
        return self.header_paras * 16


@dataclass
class Section:
    index: int
    load_seg: int
    word1: int
    file_para: int
    flags: int
    mem_paras: int
    reloc_count: int
    word6: int
    section_id: int
    file_paras: int
    relocs: list[tuple[int, int]] = field(default_factory=list)  # ordered (seg, off), load-relative
    data: bytes = b""
    data_file_offset: int = 0

    @property
    def name(self) -> str:
        return f"S{self.index:02d}"

    @property
    def is_overlay(self) -> bool:
        return self.index < 27

    @property
    def load_linear(self) -> int:
        return self.load_seg * 16


@dataclass(frozen=True)
class Vector:
    offset: int          # offset within MANAGER_SEG
    target_seg: int
    target_off: int
    section: int         # 0xFFFF = root

    @property
    def unit(self) -> str:
        return "root" if self.section == 0xFFFF else f"S{self.section:02d}"


class Executable:
    def __init__(self, path: Path = EXE_PATH, verify: bool = True):
        self.path = path
        self.raw = path.read_bytes()
        self.sha256 = hashlib.sha256(self.raw).hexdigest()
        if verify and self.sha256 != EXPECTED_SHA256:
            raise SystemExit(f"oracle hash mismatch for {path}: {self.sha256}")
        self._parse()

    # -- parsing ---------------------------------------------------------------------------
    def _parse(self) -> None:
        d = self.raw
        if d[:2] != b"MZ":
            raise ValueError("not an MZ executable")
        f = struct.unpack_from("<13H", d, 2)
        self.mz = MZHeader(*f)
        self.image = d[self.mz.header_size:self.mz.file_size]
        self.relocs = [
            (seg, off) for off, seg in (struct.unpack_from("<HH", d, self.mz.reloc_offset + 4 * i)
                                        for i in range(self.mz.reloc_count))
        ]
        self.header_bytes = d[:self.mz.header_size]
        base = MANAGER_SEG * 16
        count = struct.unpack_from("<H", self.image, base + SECTION_COUNT_OFF)[0]
        self.sections: list[Section] = []
        for i in range(count):
            w = struct.unpack_from("<9H", self.image, base + SECTION_TABLE_OFF + 18 * i)
            s = Section(i, *w)
            rec = s.file_para * 16
            s.relocs = [(seg, off) for off, seg in
                        (struct.unpack_from("<HH", d, rec + 4 * k) for k in range(s.reloc_count))]
            s.data_file_offset = rec + ((s.reloc_count * 4 + 15) // 16) * 16
            s.data = d[s.data_file_offset:s.data_file_offset + s.file_paras * 16]
            if len(s.data) != s.file_paras * 16:
                raise ValueError(f"section {i} truncated")
            self.sections.append(s)
        last = self.sections[-1]
        self.trailer_offset = last.data_file_offset + len(last.data)
        self.trailer = d[self.trailer_offset:]
        self.vectors: list[Vector] = []
        off = VECTOR_TABLE_OFF
        while self.image[base + off] == 0xE8 and self.image[base + off + 3] == 0xEA:
            toff, tseg, sec = struct.unpack_from("<HHH", self.image, base + off + 4)
            self.vectors.append(Vector(off, tseg, toff, sec))
            off += 10

    # -- addressing ------------------------------------------------------------------------
    def unit_bytes(self, unit: str) -> tuple[int, bytes]:
        """Return (load_linear, bytes) of a unit: ``root`` or ``Snn``."""
        if unit == "root":
            return 0, self.image
        s = self.sections[int(unit[1:])]
        return s.load_linear, s.data

    def unit_relocs(self, unit: str) -> list[tuple[int, int]]:
        return self.relocs if unit == "root" else self.sections[int(unit[1:])].relocs

    def read(self, unit: str, linear: int, size: int) -> bytes:
        base, data = self.unit_bytes(unit)
        return data[linear - base:linear - base + size]

    def units(self) -> list[str]:
        return ["root"] + [s.name for s in self.sections]

    def unit_for_linear(self, linear: int, prefer: str | None = None) -> list[str]:
        """Units whose loaded bytes cover a linear load-relative address."""
        out = []
        for u in self.units():
            base, data = self.unit_bytes(u)
            if base <= linear < base + len(data):
                out.append(u)
        if prefer in out:
            return [prefer]
        return out

    def reloc_sites(self, unit: str) -> set[int]:
        """Linear addresses of the low byte of each relocated segment word in ``unit``."""
        return {seg * 16 + off for seg, off in self.unit_relocs(unit)}


@lru_cache(maxsize=1)
def load(verify: bool = True) -> Executable:
    return Executable(verify=verify)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == "__main__":
    exe = load()
    m = exe.mz
    print(f"SIMANT.EXE sha256 {exe.sha256}")
    print(f"MZ file size {m.file_size} header {m.header_size} image {len(exe.image)} relocs {m.reloc_count}")
    print(f"CS:IP {m.cs:04X}:{m.ip:04X} SS:SP {m.ss:04X}:{m.sp:04X} min {m.min_alloc} max {m.max_alloc}")
    for s in exe.sections:
        print(f"{s.name} load {s.load_seg:04X} mem {s.mem_paras:04X} file@{s.data_file_offset:06X} "
              f"size {len(s.data):6d} relocs {s.reloc_count:4d} flags {s.flags:04X} id {s.section_id:02X}")
    print(f"vectors {len(exe.vectors)}; trailer {len(exe.trailer)} bytes at {exe.trailer_offset:06X}")
