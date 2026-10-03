"""Compare the isolated native two-voice scheduler to frozen DOS timer ISR."""
from __future__ import annotations

import ctypes
import _ctypes
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / "tools"), str(ROOT / "build" / "behavior" / "deps")]
import exe  # noqa: E402
import functions  # noqa: E402
import unicorn  # noqa: E402
from unicorn import x86_const as xr  # noqa: E402

ORACLE_SHA256 = "aa0596c6766322a8229ee3c36e57048c92adc82d50fbe2ef37afb8b85fcf4f11"
PINNED = {
    "src/root/m28BC.asm": "",
    "src/root/m277E.c": "4e928689c743f473c5a007bbbbb5287cdf8728d12e9cae5652b1cb55debf09ee",
    "src/root/m290D.c": "eaec23e8d37bd606616dc44208c7bbcf82ced13e24abe0362ef767c5e4cc4fed",
    "src/root/m295C.c": "d392b6ce886cfd664a192194b79569bb6a0d4dea8b0bc029ffa9e32ff44add89",
    "src/data/d55B3_00B8.c": "d04646a28691ff05ad93a50c5e7142405ab64932f875f2d2a4d10d04a4566f3d",
    "assets/SOUND.NDX": "4b73be9e633b612946aac043f930b620df2483676be54c27acc08b699a84ac80",
    "assets/SOUND.DAT": "6a884b946d842bbddb4100a644a7aee6b3d8a9c9832aa65c0989ae50510d6629",
}
MEMORY_SIZE = 0x110000
DGROUP = 0x55B3
SAMPLE_SEG = 0xA000
SAMPLE_OFFS = (0x100, 0x120)
PCM_OFF = 0x3000
PCM_SEG = 0xB000
VOL_OFF = 0x7000
STACK = 0x8000
SENTINEL = 0xF000


class IndexEntry(ctypes.Structure):
    _fields_ = [("data_offset", ctypes.c_uint32), ("id", ctypes.c_int16),
                ("kind", ctypes.c_uint8), ("flags", ctypes.c_uint8)]


class Database(ctypes.Structure):
    _fields_ = [("index_file", ctypes.POINTER(ctypes.c_uint8)),
                ("index_file_size", ctypes.c_size_t),
                ("data_file", ctypes.POINTER(ctypes.c_uint8)),
                ("data_file_size", ctypes.c_size_t),
                ("entries", ctypes.POINTER(IndexEntry)),
                ("entry_count", ctypes.c_size_t), ("error", ctypes.c_char * 192)]


class VoiceChannel(ctypes.Structure):
    _fields_ = [("priority", ctypes.c_uint8), ("instrument_id", ctypes.c_int8),
                ("note", ctypes.c_uint8), ("age", ctypes.c_uint8),
                ("active", ctypes.c_uint8), ("owner_loaded", ctypes.c_uint8),
                ("sound_id", ctypes.c_int16), ("sample_object_id", ctypes.c_int16),
                ("velocity", ctypes.c_uint8)]


class Allocator(ctypes.Structure):
    _fields_ = [("channels", VoiceChannel * 2)]


class LiveVoice(ctypes.Structure):
    _fields_ = [("pcm", ctypes.POINTER(ctypes.c_uint8)), ("pcm_size", ctypes.c_size_t),
                ("position", ctypes.c_uint16), ("end", ctypes.c_uint16),
                ("loop_start", ctypes.c_uint16), ("step_8_8", ctypes.c_uint16),
                ("fraction", ctypes.c_uint8), ("volume_row", ctypes.c_uint8),
                ("looped", ctypes.c_uint8)]


class Scheduler(ctypes.Structure):
    _fields_ = [("allocator", Allocator), ("voices", LiveVoice * 2),
                ("speaker_enabled", ctypes.c_uint8)]


class Request(ctypes.Structure):
    _fields_ = [("sound_id", ctypes.c_int16), ("instrument_id", ctypes.c_int16),
                ("sample_object_id", ctypes.c_int16), ("priority", ctypes.c_uint8),
                ("note", ctypes.c_uint8), ("velocity", ctypes.c_uint8)]


class Start(ctypes.Structure):
    _fields_ = [("selected_channel", ctypes.c_int16), ("priority", ctypes.c_uint8),
                ("release_count", ctypes.c_uint8), ("released", ctypes.c_int8 * 2),
                ("stopped_channel", ctypes.c_int16), ("started_channel", ctypes.c_int16)]


class Tick(ctypes.Structure):
    _fields_ = [("output_generated", ctypes.c_uint8), ("mixed_register", ctypes.c_uint8),
                ("speaker_enabled", ctypes.c_uint8)]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class DosTimer:
    def __init__(self):
        row = functions.get("f_28BC_0015")
        image = exe.load()
        if sha(ROOT / "assets/SIMANT.EXE") != ORACLE_SHA256:
            raise RuntimeError("frozen EXE pin changed")
        self.cpu = unicorn.Uc(unicorn.UC_ARCH_X86, unicorn.UC_MODE_16)
        self.cpu.mem_map(0, MEMORY_SIZE)
        self.cpu.mem_write(0, image.image)
        resident = image.sections[27]
        self.cpu.mem_write(resident.load_linear, resident.data)
        self.entry = (row["seg"], row["off"])
        self.outputs: list[int] = []
        self.states = []
        self.samples = []
        self.cpu.hook_add(unicorn.UC_HOOK_CODE, self.on_code)
        self.cpu.hook_add(unicorn.UC_HOOK_INSN, self.on_in, None, 1, 0, xr.UC_X86_INS_IN)
        self.cpu.hook_add(unicorn.UC_HOOK_INSN, self.on_out, None, 1, 0, xr.UC_X86_INS_OUT)

    def linear(self, seg: int, off: int = 0) -> int:
        return seg * 16 + off

    def word(self, seg: int, off: int, val: int):
        self.cpu.mem_write(self.linear(seg, off), (val & 0xffff).to_bytes(2, "little"))

    def read_word(self, seg: int, off: int) -> int:
        return int.from_bytes(self.cpu.mem_read(self.linear(seg, off), 2), "little")

    def on_code(self, uc, address, size, data):
        if address in (self.linear(self.entry[0], 0x73), self.linear(self.entry[0], 0xb8)):
            self.samples.append((address & 0xffff, uc.reg_read(xr.UC_X86_REG_AX) & 0xff,
                                 uc.reg_read(xr.UC_X86_REG_BX), uc.reg_read(xr.UC_X86_REG_SI),
                                 uc.reg_read(xr.UC_X86_REG_DS), uc.reg_read(xr.UC_X86_REG_ES)))
        if address == self.linear(self.entry[0], 0x1C2):
            self.outputs.append(uc.reg_read(xr.UC_X86_REG_AX) & 0xff)
            self.states.append({name: uc.reg_read(reg) for name, reg in
                                (("ds", xr.UC_X86_REG_DS), ("es", xr.UC_X86_REG_ES),
                                 ("ax", xr.UC_X86_REG_AX), ("bx", xr.UC_X86_REG_BX),
                                 ("si", xr.UC_X86_REG_SI), ("dx", xr.UC_X86_REG_DX),
                                 ("cs", xr.UC_X86_REG_CS), ("ip", xr.UC_X86_REG_IP))})

    def on_in(self, uc, port, size, data):
        return 0

    def on_out(self, uc, port, size, value, data):
        return

    def reset_channels(self):
        # Timer ISR operates on the first two source descriptors at 55B3:6b4c/6b60.
        self.cpu.mem_write(self.linear(DGROUP, 0x6b4c), bytes(40))
        # g_6b9c = out_speaker; avoid sequencer dispatch and chaining on each PIT tick.
        self.word(DGROUP, 0x6b9c, 0x1c2)
        self.word(DGROUP, 0x6b48, 3)
        self.word(DGROUP, 0x6b3e, 0)
        self.word(DGROUP, 0x6b40, 0)
        self.word(DGROUP, 0x6b42, 0x7fff)
        self.word(DGROUP, 0x74a3, 0x7fff)
        self.word(DGROUP, 0x74a5, 0x7fff)
        # Eight volume rows at g_6b9e. Exact source arithmetic emitted as tables.
        for row in range(8):
            values = bytes((0x80 + (((sample - 0x80) * (8 - row)) // 8)
                            if sample >= 0x80 else
                            0x80 - (((0x80 - sample) * (8 - row) + 7) // 8))
                           & 0xff for sample in range(256))
            self.cpu.mem_write(self.linear(DGROUP, VOL_OFF + row * 256), values)
        self.word(DGROUP, 0x6b9e, VOL_OFF)
        self.cpu.mem_write(self.linear(SAMPLE_SEG, 0x200), bytes(4))
        self.outputs.clear()
        self.states.clear()
        self.samples.clear()

    def set_voice(self, channel: int, pcm: bytes | None, step: int = 0,
                  row: int = 0, end: int = 0):
        base = 0x6b4c + channel * 0x14
        if pcm is None:
            self.cpu.mem_write(self.linear(DGROUP, base), bytes(20))
            return
        sample_off = SAMPLE_OFFS[channel]
        # Sample.loaded=1, data -> indirect far pointer -> decoded data.
        self.word(SAMPLE_SEG, sample_off + 0x0c, 1)
        self.word(SAMPLE_SEG, sample_off + 0, 0x200)
        self.word(SAMPLE_SEG, sample_off + 2, SAMPLE_SEG)
        self.word(SAMPLE_SEG, 0x200, 0)
        self.word(SAMPLE_SEG, 0x202, PCM_SEG)
        self.cpu.mem_write(self.linear(PCM_SEG), pcm)
        self.word(DGROUP, base, 0)       # position
        self.word(DGROUP, base + 2, sample_off)
        self.word(DGROUP, base + 4, SAMPLE_SEG)
        self.word(DGROUP, base + 6, end)
        self.word(DGROUP, base + 8, 2)   # start/loop
        self.word(DGROUP, base + 10, step)
        self.word(DGROUP, base + 12, VOL_OFF + row * 256)
        self.cpu.mem_write(self.linear(DGROUP, base + 14), b"\0\0")
        self.word(DGROUP, base + 16, sample_off)
        self.word(DGROUP, base + 18, SAMPLE_SEG)

    def tick(self):
        self.outputs.clear()
        self.cpu.mem_write(self.linear(0x8000, STACK),
                           (STACK).to_bytes(2, "little") + (SENTINEL).to_bytes(2, "little") +
                           (0x0200).to_bytes(2, "little"))
        self.cpu.reg_write(xr.UC_X86_REG_SS, 0x8000)
        self.cpu.reg_write(xr.UC_X86_REG_SP, STACK)
        self.cpu.reg_write(xr.UC_X86_REG_CS, self.entry[0])
        self.cpu.reg_write(xr.UC_X86_REG_IP, self.entry[1])
        self.cpu.reg_write(xr.UC_X86_REG_DS, 0)
        self.cpu.emu_start(self.linear(*self.entry), self.linear(SENTINEL, STACK), count=10000)
        return list(self.outputs)


def main():
    for name, expected in PINNED.items():
        actual = sha(ROOT / name)
        if expected in ("TODO", ""):
            PINNED[name] = actual
        elif actual != expected:
            raise RuntimeError(f"source/assets pin mismatch for {name}: {actual}")
    compiler = shutil.which("gcc")
    if not compiler:
        raise RuntimeError("gcc required")
    out_dir = ROOT / "build/portable/audio-voice-scheduler"
    out_dir.mkdir(parents=True, exist_ok=True)
    dll = out_dir / "scheduler.dll"
    sources = ["portable/game/resources/database.c", "portable/audio/intent.c",
               "portable/audio/dac_mixer.c", "portable/research/audio_voice_admission.c",
               "portable/research/audio_voice_scheduler.c"]
    subprocess.run([compiler, "-std=c11", "-Wall", "-Wextra", "-Wconversion", "-Werror",
                    "-shared", "-fPIC", *sources, "-o", str(dll)], cwd=ROOT, check=True)
    lib = ctypes.CDLL(str(dll))
    lib.portable_db_open_files.argtypes = [ctypes.POINTER(Database), ctypes.c_char_p, ctypes.c_char_p]
    lib.portable_db_open_files.restype = ctypes.c_int
    lib.portable_db_close.argtypes = [ctypes.POINTER(Database)]
    lib.portable_dac_live_scheduler_init.argtypes = [ctypes.POINTER(Scheduler)]
    lib.portable_dac_live_scheduler_close.argtypes = [ctypes.POINTER(Scheduler)]
    lib.portable_dac_live_scheduler_start.argtypes = [ctypes.POINTER(Database), ctypes.POINTER(Scheduler), ctypes.POINTER(Request), ctypes.c_uint16, ctypes.POINTER(Start)]
    lib.portable_dac_live_scheduler_start.restype = ctypes.c_int
    lib.portable_dac_live_scheduler_tick.argtypes = [ctypes.POINTER(Scheduler), ctypes.POINTER(Tick)]
    lib.portable_dac_live_scheduler_tick.restype = ctypes.c_int
    db = Database()
    if lib.portable_db_open_files(ctypes.byref(db), str(ROOT / "assets/SOUND.NDX").encode(), str(ROOT / "assets/SOUND.DAT").encode()) != 0:
        raise RuntimeError("failed to open pinned SOUND database")
    scheduler = Scheduler()
    lib.portable_dac_live_scheduler_init(ctypes.byref(scheduler))
    dos = DosTimer()
    dos.reset_channels()
    profiles = {1: Request(1, 1, 1, 3, 60, 127), 2: Request(2, 2, 2, 3, 60, 127),
                55: Request(55, 10, 10, 4, 100, 127)}
    trace = []
    for start_at, sound_id in ((0, 1), (20, 2), (45, 55)):
        for _ in range(start_at - len(trace)):
            tick = Tick()
            if lib.portable_dac_live_scheduler_tick(ctypes.byref(scheduler), ctypes.byref(tick)) != 0:
                raise RuntimeError("native tick failed")
            outputs = dos.tick()
            if len(outputs) != tick.output_generated or (outputs and outputs[0] != tick.mixed_register):
                raise AssertionError(("mixed register", len(trace), outputs, tick.output_generated, tick.mixed_register,
                                      scheduler.voices[0].position, scheduler.voices[0].pcm[1] if scheduler.voices[0].pcm else None,
                                      dos.read_word(DGROUP, 0x6b4c), dos.read_word(DGROUP, 0x6b4e),
                                      dos.read_word(DGROUP, 0x6b58), dos.cpu.mem_read(dos.linear(DGROUP, VOL_OFF), 256)[128],
                                      dos.read_word(SAMPLE_SEG, 0x200), dos.cpu.mem_read(dos.linear(PCM_SEG), 4).hex(), dos.states, dos.samples))
            trace.append({"tick": len(trace), "output": outputs[0] if outputs else None,
                          "positions": [int(v.position) for v in scheduler.voices],
                          "fractions": [int(v.fraction) for v in scheduler.voices]})
        request = profiles[sound_id]
        start = Start()
        status = lib.portable_dac_live_scheduler_start(ctypes.byref(db), ctypes.byref(scheduler), ctypes.byref(request), 0x7f, ctypes.byref(start))
        if status != 0 or start.started_channel < 0:
            raise AssertionError(("start", sound_id, status, start.started_channel))
        voice = scheduler.voices[start.started_channel]
        pcm = ctypes.string_at(voice.pcm, voice.pcm_size)
        dos.set_voice(start.started_channel, pcm, voice.step_8_8, voice.volume_row, voice.end)
    for _ in range(320):
        tick = Tick()
        if lib.portable_dac_live_scheduler_tick(ctypes.byref(scheduler), ctypes.byref(tick)) != 0:
            raise RuntimeError("native tick failed")
        outputs = dos.tick()
        if len(outputs) != tick.output_generated or (outputs and outputs[0] != tick.mixed_register):
            raise AssertionError(("mixed register", len(trace), outputs, tick.output_generated, tick.mixed_register))
        for channel in range(2):
            base = 0x6b4c + channel * 0x14
            ds_pos = dos.read_word(DGROUP, base)
            ds_frac = dos.cpu.mem_read(dos.linear(DGROUP, base + 14), 1)[0]
            nv = scheduler.voices[channel]
            if nv.pcm and scheduler.allocator.channels[channel].active and (ds_pos, ds_frac) != (nv.position, nv.fraction):
                raise AssertionError(("voice cursor", len(trace), channel, ds_pos, ds_frac, nv.position, nv.fraction))
        trace.append({"tick": len(trace), "output": outputs[0] if outputs else None,
                      "positions": [int(v.position) for v in scheduler.voices],
                      "fractions": [int(v.fraction) for v in scheduler.voices]})
    lib.portable_dac_live_scheduler_close(ctypes.byref(scheduler))
    lib.portable_db_close(ctypes.byref(db))
    handle = lib._handle
    del lib
    _ctypes.FreeLibrary(handle)
    report = {"schema": "dos-dac-live-isr-differential-v1", "status": "PASS",
              "boundary": "native source-profile start/admission plus direct frozen f_28BC_0015 ISR calls; compare each source out_speaker AL and 8.8 cursors; no SDL, host-rate conversion, or acoustics claim",
              "oracle_sha256": ORACLE_SHA256, "pins": {**PINNED, "assets/SIMANT.EXE": sha(ROOT / "assets/SIMANT.EXE")},
              "modules": {p: sha(ROOT / p) for p in ["portable/research/audio_voice_scheduler.c", "portable/research/audio_voice_scheduler.h", "portable/research/audio_voice_admission.c", "portable/tests/audio/voice_scheduler_isr_differential.py"]},
              "pit_divisor": 100, "native_sample_rate_hz_approx": 11932, "schedule": ["SFX 1 at tick 0", "SFX 2 at tick 20", "SFX 55 at tick 45"],
              "compared_ticks": len(trace), "register_trace": trace}
    archive = ROOT / "portable/tests/audio/evidence/voice-admission-v1/scheduler-report.json"
    archive.write_text(json.dumps(report, indent=2) + "\n")
    print(f"PASS timer ISR compared_ticks={len(trace)} archive={archive.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
