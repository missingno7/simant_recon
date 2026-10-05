"""Run the bounded original-instruction mono access witness in test-owned memory.

This runner creates only a fresh --out directory beneath this repository's build/
tree. It never writes evidence, production sources, the oracle, or existing output.
The fixture's 584-byte prefix and adjacent marker are not an owner candidate.
"""
from pathlib import Path
import argparse
import hashlib
import json
import struct
import sys
sys.dont_write_bytecode = True
if not __debug__:
    raise RuntimeError('Run witness controls without Python -O')


def find_repository():
    for candidate in Path(__file__).resolve().parents:
        if (candidate / "src/program.json").is_file() and (candidate / "tools/exe.py").is_file():
            return candidate
    raise SystemExit("Cannot locate repository containing src/program.json and tools/exe.py")


ROOT = find_repository()
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--out", required=True, type=Path,
                    help="Fresh output directory beneath repository build/; relative paths are repository-relative")
options = parser.parse_args()
OUT = (options.out if options.out.is_absolute() else ROOT / options.out).resolve()
BUILD = (ROOT / "build").resolve()
if OUT == BUILD or not OUT.is_relative_to(BUILD):
    parser.error("--out must name a fresh directory strictly beneath repository build/")
if OUT.exists():
    parser.error("--out already exists; choose a fresh directory")

sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "build/behavior/deps"))
import exe
import unicorn as uc
from unicorn import x86_const as xr

IMAGE = exe.load()  # Current read-only tool verifies the immutable oracle hash.
CODE_BASE, CODE = IMAGE.unit_bytes("S01")


def pin(path):
    path = path.resolve()
    data = path.read_bytes()
    return {"path": path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else str(path),
            "size": len(data), "sha256": hashlib.sha256(data).hexdigest()}


DGROUP = 0x55B3
BASE = DGROUP * 16 + 0x8ED8
SRC = 0x7000 * 16
DST = 0x7800 * 16
SP = 0xF000


def run(entry, width, y, row, marker):
    cpu = uc.Uc(uc.UC_ARCH_X86, uc.UC_MODE_16)
    cpu.mem_map(0, 0x110000)
    cpu.mem_write(CODE_BASE, CODE)
    # Only fixture state is written: source, pattern prefix, discriminating byte,
    # and call frame. Original code is loaded intact and is never patched.
    cpu.mem_write(SRC, bytes([row]) * 128)
    cpu.mem_write(BASE, bytes(584))
    cpu.mem_write(BASE + 584, bytes([marker]))
    args = [0x8000, 0xF000, 0, 0x7000, 0, 0x7800]
    args += [y] if entry in (0x012C, 0x01D5) else [width, y]
    cpu.mem_write(DGROUP * 16 + SP, struct.pack("<" + "H" * len(args), *args))
    regs = {"cs": 0x328E, "ip": entry, "ss": DGROUP, "sp": SP,
            "ds": DGROUP, "es": 0, "eflags": 2}
    for name, value in regs.items():
        cpu.reg_write(getattr(xr, "UC_X86_REG_" + name.upper()), value)
    reads = []
    pc_samples = []

    def on_read(cpu, access, address, size, value, user):
        if BASE <= address <= BASE + 2050:
            reads.append(address - BASE)
            if len(pc_samples) < 12 or len(reads) % 1000 == 0:
                pc_samples.append([cpu.reg_read(xr.UC_X86_REG_CS),
                                   cpu.reg_read(xr.UC_X86_REG_IP), address - BASE])

    cpu.hook_add(uc.UC_HOOK_MEM_READ, on_read)
    # Stop immediately before authentic RETF, after body and register restores.
    # This access-domain witness does not claim return-ABI emulation.
    end = 0x328E * 16 + {0x000A: 0x009C, 0x009D: 0x012B,
                         0x012C: 0x01D4, 0x01D5: 0x027D}[entry]
    cpu.emu_start(0x328E * 16 + entry, end, count=20000)
    assert cpu.reg_read(xr.UC_X86_REG_CS) * 16 + cpu.reg_read(xr.UC_X86_REG_IP) == end
    expected_reads = {0x000A: 512, 0x009D: 256, 0x012C: 256, 0x01D5: 128}[entry]
    assert len(reads) == expected_reads, (entry, len(reads), pc_samples)
    output = bytes(cpu.mem_read(DST, 256))
    plane = {0x000A: 64, 0x009D: 32, 0x012C: 32, 0x01D5: 16}[entry]
    return {"entry": f"328e:{entry:04x}",
            "width_arg": width if entry in (0x000A, 0x009D) else None,
            "y_arg": y, "row_byte": row, "adjacent_marker": marker,
            "pattern_read_count": len(reads), "min_displacement": min(reads),
            "max_displacement": max(reads), "distinct_displacements": sorted(set(reads)),
            "output_sha256": hashlib.sha256(output).hexdigest(),
            "first_output_bytes": list(output[:4]), "second_plane_offset": plane,
            "second_output_plane_bytes": list(output[plane:plane + 4])}


tests = []
for entry, width in ((0x000A, 128), (0x009D, 64), (0x012C, 128), (0x01D5, 64)):
    for y in (6, 7):
        for marker in (0, 0xFF):
            tests.append(run(entry, width, y, 72, marker))
controls = [run(0x000A, 7, 6, 72, 0xFF), run(0x009D, 64, 6, 255, 0)]
for entry in ("328e:012c", "328e:01d5"):
    even = [t for t in tests if t["entry"] == entry and t["y_arg"] == 6]
    odd = [t for t in tests if t["entry"] == entry and t["y_arg"] == 7]
    assert even[0]["output_sha256"] == even[1]["output_sha256"]
    assert odd[0]["output_sha256"] != odd[1]["output_sha256"]
    assert even[0]["max_displacement"] == 583 and odd[0]["max_displacement"] == 584
main = [t for t in tests if t["entry"] == "328e:000a"]
assert len({t["output_sha256"] for t in main}) == 1
assert {t["max_displacement"] for t in main} == {579}

receipt = {
    "schema": "mono-owner-original-asm-access-witness-v2",
    "status": "NO_ALLOCATION_ADMISSION",
    "scope": "Four original S01 bodies through their authentic RETF boundaries in test-owned memory; no return-ABI claim, no code patching",
    "oracle": pin(IMAGE.path),
    "oracle_hash_check": {"expected_sha256": exe.EXPECTED_SHA256,
                          "actual_sha256": IMAGE.sha256},
    "original_S01": {"load_linear": CODE_BASE, "size": len(CODE),
                     "sha256": hashlib.sha256(CODE).hexdigest()},
    "canonical_input_pins": [pin(ROOT / p) for p in (
        "src/program.json", "src/S01/m328E.asm", "src/S15/m384C.c",
        "src/S12/m384C.c", "src/S04/m35F5.c", "src/data/d3D57.c",
        "src/root/m205F.c", "src/root/m15F8.c", "src/S20/m39F1.c",
        "src/root/m20E8.c", "src/root/m2505.c")],
    "implementation_pins": [pin(p) for p in (
        Path(__file__), ROOT / "tools/exe.py", Path(uc.__file__), Path(xr.__file__))],
    "unicorn_version": uc.__version__,
    "python_version": sys.version,
    "fixture": {
        "memory_owner": "test harness only; no candidate source allocation",
        "source": "Uniform128-byte row72 (row255 for generic-width control)",
        "pattern_prefix": "584 zero test bytes",
        "adjacent_marker": "Test byte at displacement584, either00 orff",
        "frame": "SS=DS=55B3; two far pointer args; width,y for000A/009D and y only for012C/01D5",
        "initialization": "Unicorn zeroed mapped memory plus explicitly written fixture state",
    },
    "nonclaims": ["No DOS tail owner/type/extent", "No actual gameplay reachability",
                  "No whole-program initialization/lifetime proof", "No return-ABI verification"],
    "tests": tests,
    "controls": controls,
}
OUT.mkdir(parents=True, exist_ok=False)
(OUT / "asm-witness.json").write_text(json.dumps(receipt, indent=2) + "\n")
print(json.dumps({"out": str(OUT / "asm-witness.json"), "status": receipt["status"],
                  "tests": len(tests), "controls": len(controls),
                  "mini_row72_y7_max_displacement": 584,
                  "main_width128_max_displacement": 579}, indent=2))
