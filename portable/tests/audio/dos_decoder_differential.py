"""Compare every native SOUND kind-5 decode with the frozen DOS routine."""
from __future__ import annotations

import ctypes
import _ctypes
import hashlib
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
import platform

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / "tools"), str(ROOT / "build" / "behavior" / "deps")]
import exe  # noqa: E402
import functions  # noqa: E402
import unicorn  # noqa: E402
from unicorn import x86_const as xr  # noqa: E402

SENTINEL = (0xF000, 0x8000)
SENTINEL_LINEAR = SENTINEL[0] * 16 + SENTINEL[1]
MEMORY_SIZE = 0x110000
SOUND_NDX_SHA256 = "4b73be9e633b612946aac043f930b620df2483676be54c27acc08b699a84ac80"
SOUND_DAT_SHA256 = "6a884b946d842bbddb4100a644a7aee6b3d8a9c9832aa65c0989ae50510d6629"


class PortableDatabase(ctypes.Structure):
    _fields_ = [
        ("index_file", ctypes.c_void_p), ("index_file_size", ctypes.c_size_t),
        ("data_file", ctypes.c_void_p), ("data_file_size", ctypes.c_size_t),
        ("entries", ctypes.c_void_p), ("entry_count", ctypes.c_size_t),
        ("error", ctypes.c_char * 192),
    ]


class PortableDbIndexEntry(ctypes.Structure):
    _fields_ = [("data_offset", ctypes.c_uint32), ("id", ctypes.c_int16),
                ("kind", ctypes.c_uint8), ("flags", ctypes.c_uint8)]


class PortableDbRecord(ctypes.Structure):
    _fields_ = [("id", ctypes.c_int16), ("kind", ctypes.c_uint8),
                ("index_flags", ctypes.c_uint8), ("data_offset", ctypes.c_uint32),
                ("data", ctypes.POINTER(ctypes.c_uint8)), ("size", ctypes.c_size_t)]


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def resolve_compiler() -> str:
    compiler = os.environ.get("SIMANT_CC") or shutil.which("gcc")
    if compiler is None:
        compiler = "C:/msys64/mingw64/bin/gcc.exe"
    return compiler


def compile_native(output: Path, compiler: str) -> None:
    command = [compiler, "-std=c11", "-Wall", "-Wextra", "-Wconversion", "-Werror",
               "-shared", "-I", "portable", "portable/game/resources/database.c",
               "portable/audio/intent.c", "-o", str(output)]
    subprocess.run(command, cwd=ROOT, check=True)


def bind_native(path: Path):
    lib = ctypes.CDLL(str(path))
    lib.portable_db_open.argtypes = [ctypes.POINTER(PortableDatabase), ctypes.c_char_p]
    lib.portable_db_open.restype = ctypes.c_int
    lib.portable_db_close.argtypes = [ctypes.POINTER(PortableDatabase)]
    lib.portable_db_load.argtypes = [ctypes.POINTER(PortableDatabase), ctypes.c_int16,
                                     ctypes.c_int16, ctypes.POINTER(PortableDbRecord)]
    lib.portable_db_load.restype = ctypes.c_int
    lib.portable_db_record_free.argtypes = [ctypes.POINTER(PortableDbRecord)]
    lib.portable_audio_load_sample_pcm.argtypes = [ctypes.POINTER(PortableDatabase),
                                                   ctypes.c_int16,
                                                   ctypes.POINTER(ctypes.POINTER(ctypes.c_uint8)),
                                                   ctypes.POINTER(ctypes.c_size_t)]
    lib.portable_audio_load_sample_pcm.restype = ctypes.c_int
    lib.portable_audio_free_pcm.argtypes = [ctypes.POINTER(ctypes.c_uint8)]
    lib.portable_audio_dac_sample_for_sound_id.argtypes = [ctypes.c_int16,
                                                           ctypes.POINTER(ctypes.c_int16)]
    lib.portable_audio_dac_sample_for_sound_id.restype = ctypes.c_int
    return lib


def sample_rows(db: PortableDatabase) -> list[tuple[int, int, int]]:
    rows = ctypes.cast(db.entries, ctypes.POINTER(PortableDbIndexEntry))
    return sorted((int(rows[i].id), int(rows[i].kind), int(rows[i].flags))
                  for i in range(db.entry_count) if rows[i].kind == 5)


def native_record_bytes(lib, db: PortableDatabase, object_id: int) -> bytes:
    record = PortableDbRecord()
    status = lib.portable_db_load(ctypes.byref(db), object_id, 5, ctypes.byref(record))
    if status != 0:
        raise RuntimeError(f"native resource load id={object_id} failed status={status}: "
                           f"{bytes(db.error).split(bytes([0]), 1)[0]!r}")
    try:
        return ctypes.string_at(record.data, record.size)
    finally:
        lib.portable_db_record_free(ctypes.byref(record))


def native_decode(lib, db: PortableDatabase, object_id: int) -> bytes:
    out = ctypes.POINTER(ctypes.c_uint8)()
    size = ctypes.c_size_t()
    status = lib.portable_audio_load_sample_pcm(ctypes.byref(db), object_id,
                                                ctypes.byref(out), ctypes.byref(size))
    if status != 0:
        raise RuntimeError(f"native PCM decode id={object_id} failed status={status}")
    try:
        return ctypes.string_at(out, size.value)
    finally:
        lib.portable_audio_free_pcm(out)


class DosDecoder:
    def __init__(self) -> None:
        row = functions.get("f_290D_000E")
        if row["unit"] != "root":
            raise RuntimeError("DOS decoder is not in the resident root image")
        image = exe.load()  # verifies the locked original executable identity
        self.entry = (row["seg"], row["off"])
        self.cpu = unicorn.Uc(unicorn.UC_ARCH_X86, unicorn.UC_MODE_16)
        self.cpu.mem_map(0, MEMORY_SIZE)
        self.cpu.mem_write(0, image.image)
        resident = image.sections[27]
        self.cpu.mem_write(resident.load_linear, resident.data)
        self.src = 0x60000
        self.dst = 0x70000
        self.ss = 0x8000
        self.sp = 0x8000

    def decode(self, source: bytes) -> bytes:
        if len(source) < 16:
            raise RuntimeError("sample is shorter than the delta table")
        output_size = (len(source) - 16) * 2
        if output_size > 0xffff:
            raise RuntimeError("sample output does not fit DOS unsigned size argument")
        self.cpu.mem_write(self.src, source)
        # Far C call frame: retf target, src far pointer, dst far pointer, n.
        frame = struct.pack("<7H", SENTINEL[1], SENTINEL[0],
                            self.src & 0x0f, self.src >> 4,
                            self.dst & 0x0f, self.dst >> 4, output_size)
        self.cpu.mem_write(self.ss * 16 + self.sp, frame)
        regs = ((xr.UC_X86_REG_SS, self.ss), (xr.UC_X86_REG_SP, self.sp),
                (xr.UC_X86_REG_CS, self.entry[0]), (xr.UC_X86_REG_IP, self.entry[1]),
                (xr.UC_X86_REG_DS, 0x3D57), (xr.UC_X86_REG_ES, 0x3D57),
                (xr.UC_X86_REG_EFLAGS, 2))
        for reg, value in regs:
            self.cpu.reg_write(reg, value)
        self.cpu.emu_start(self.entry[0] * 16 + self.entry[1], SENTINEL_LINEAR,
                           count=200000)
        if (self.cpu.reg_read(xr.UC_X86_REG_CS), self.cpu.reg_read(xr.UC_X86_REG_IP)) != SENTINEL:
            raise RuntimeError("DOS decoder did not return within the instruction budget")
        if (self.cpu.reg_read(xr.UC_X86_REG_AX), self.cpu.reg_read(xr.UC_X86_REG_DX)) != \
                (self.dst & 0xffff, self.dst >> 4):
            raise RuntimeError("DOS decoder returned an unexpected far pointer")
        return bytes(self.cpu.mem_read(self.dst, output_size))


def main() -> None:
    assets = ROOT / "assets"
    sound_root = assets / "SOUND"
    ndx_path, dat_path = sound_root.with_suffix(".NDX"), sound_root.with_suffix(".DAT")
    ndx_raw, dat_raw = ndx_path.read_bytes(), dat_path.read_bytes()
    if sha256(ndx_raw) != SOUND_NDX_SHA256 or sha256(dat_raw) != SOUND_DAT_SHA256:
        raise SystemExit("SOUND database asset pin mismatch")

    with tempfile.TemporaryDirectory(prefix="simant-audio-diff-") as temporary:
        dll = Path(temporary) / "audio-decoder.dll"
        compiler = resolve_compiler()
        compile_native(dll, compiler)
        lib = bind_native(dll)
        db = PortableDatabase()
        status = lib.portable_db_open(ctypes.byref(db), str(sound_root).encode())
        if status != 0:
            raise RuntimeError(f"native SOUND open failed status={status}")
        try:
            rows = sample_rows(db)
            if [row[0] for row in rows] != list(range(57)):
                raise RuntimeError("active SOUND kind-5 objects are not ids 0..56")
            dos = DosDecoder()
            sound_id_mapping = []
            for sound_id in range(56):
                sample_id = ctypes.c_int16(-1)
                if not lib.portable_audio_dac_sample_for_sound_id(sound_id,
                                                                  ctypes.byref(sample_id)):
                    raise RuntimeError(f"DOS DAC sound id {sound_id} has no mapped sample")
                sound_id_mapping.append({"sound_id": sound_id,
                                         "sample_object_id": sample_id.value})
            comparisons = []
            for object_id, kind, flags in rows:
                source = native_record_bytes(lib, db, object_id)
                expected = dos.decode(source)
                actual = native_decode(lib, db, object_id)
                if actual != expected:
                    first = next((i for i, (a, b) in enumerate(zip(actual, expected)) if a != b),
                                 min(len(actual), len(expected)))
                    raise RuntimeError(f"DOS PCM mismatch object={object_id} byte={first} "
                                       f"native={len(actual)} DOS={len(expected)}")
                comparisons.append({"object_id": object_id, "kind": kind, "flags": flags,
                                   "stored_bytes": len(source), "pcm_bytes": len(expected),
                                   "pcm_sha256": sha256(expected)})
        finally:
            lib.portable_db_close(ctypes.byref(db))
            _ctypes.FreeLibrary(lib._handle)

    source_paths = ["src/root/m290D.c", "src/root/m0000.c", "src/root/m00DF.c",
                    "src/root/m295C.c", "src/data/d55B3_00B8.c",
                    "portable/game/resources/database.c", "portable/game/resources/database.h",
                    "portable/audio/intent.c", "portable/audio/intent.h",
                    "tools/exe.py", "tools/functions.py", "tools/symbols.py",
                    "layout/functions.json", "layout/symbols.json",
                    "portable/tests/audio/dos_decoder_differential.py"]
    report = {
        "schema": "native-audio-dos-decoder-differential-v1",
        "proof_boundary": "direct 16-bit execution of frozen root:f_290D_000E in Unicorn 2.1.4",
        "runner": {"python": sys.version.split()[0], "platform": platform.platform(),
                   "unicorn": unicorn.__version__,
                   "native_compiler": subprocess.check_output(
                       [compiler, "--version"], text=True).splitlines()[0]},
        "oracle": {"path": "assets/SIMANT.EXE", "sha256": exe.load().sha256,
                   "function": {"unit": "root", "seg": dos.entry[0], "off": dos.entry[1]}},
        "assets": {"SOUND.NDX": {"sha256": sha256(ndx_raw), "bytes": len(ndx_raw)},
                   "SOUND.DAT": {"sha256": sha256(dat_raw), "bytes": len(dat_raw)}},
        "current_source_pins": {path: sha256((ROOT / path).read_bytes()) for path in source_paths},
        "record_count": len(comparisons),
        "all_output_bytes_equal": True,
        "sound_id_profile": "DOS SFX note table through DAC instrument table fd_55B3_0C42",
        "sound_ids_mapped": len(sound_id_mapping),
        "sound_id_mapping": sound_id_mapping,
        "comparisons": comparisons,
    }
    evidence = ROOT / "portable" / "tests" / "audio" / "evidence"
    evidence.mkdir(parents=True, exist_ok=True)
    (evidence / "dos-decoder-differential.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"PASS DOS f_290D_000E kind5_records={len(comparisons)} "
          f"asset_pins={SOUND_NDX_SHA256[:12]}/{SOUND_DAT_SHA256[:12]}")


if __name__ == "__main__":
    main()
