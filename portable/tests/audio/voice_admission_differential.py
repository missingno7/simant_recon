"""Differentially execute the frozen DOS DAC voice allocator and the native model."""
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
SOURCE_PINS = {
    "src/root/m00DF.c": "6615da596be7ecdcdf432bd280d53e5d57ac75674b06e71a831989904a1a6ce4",
    "src/root/m277E.c": "4e928689c743f473c5a007bbbbb5287cdf8728d12e9cae5652b1cb55debf09ee",
    "src/root/m290D.c": "eaec23e8d37bd606616dc44208c7bbcf82ced13e24abe0362ef767c5e4cc4fed",
    "src/root/m295C.c": "d392b6ce886cfd664a192194b79569bb6a0d4dea8b0bc029ffa9e32ff44add89",
    "src/data/d55B3_00B8.c": "d04646a28691ff05ad93a50c5e7142405ab64932f875f2d2a4d10d04a4566f3d",
}
ASSET_PINS = {
    "assets/SOUND.NDX": "4b73be9e633b612946aac043f930b620df2483676be54c27acc08b699a84ac80",
    "assets/SOUND.DAT": "6a884b946d842bbddb4100a644a7aee6b3d8a9c9832aa65c0989ae50510d6629",
}
MEMORY_SIZE = 0x110000
SENTINEL_SEG = 0xF000
SENTINEL_OFF = 0x8000
DS = 0x8000
CHANNEL_SEG = 0x50F6
CHANNEL_OFF = 0x4A4E
STATE_SEG = 0x9000
SAMPLE_SEG = 0xA000
SLOT_OFF = 0x6B4E


class NativeChannel(ctypes.Structure):
    _fields_ = [("priority", ctypes.c_uint8), ("instrument_id", ctypes.c_int8),
                ("note", ctypes.c_uint8), ("age", ctypes.c_uint8),
                ("active", ctypes.c_uint8), ("owner_loaded", ctypes.c_uint8),
                ("sound_id", ctypes.c_int16),
                ("sample_object_id", ctypes.c_int16),
                ("velocity", ctypes.c_uint8)]


class NativeAllocator(ctypes.Structure):
    _fields_ = [("channels", NativeChannel * 2)]


class NativeDecision(ctypes.Structure):
    _fields_ = [("selected_channel", ctypes.c_int16),
                ("priority", ctypes.c_uint8), ("release_count", ctypes.c_uint8),
                ("released_owner_channels", ctypes.c_int8 * 2)]


class NativeRequest(ctypes.Structure):
    _fields_ = [("sound_id", ctypes.c_int16),
                ("instrument_id", ctypes.c_int16),
                ("sample_object_id", ctypes.c_int16),
                ("priority", ctypes.c_uint8), ("note", ctypes.c_uint8),
                ("velocity", ctypes.c_uint8)]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def bind_native(lib):
    lib.portable_dac_voice_allocator_init.argtypes = [ctypes.POINTER(NativeAllocator)]
    lib.portable_dac_voice_admit.argtypes = [ctypes.POINTER(NativeAllocator), ctypes.c_uint8]
    lib.portable_dac_voice_admit.restype = NativeDecision
    lib.portable_dac_voice_admit_request.argtypes = [
        ctypes.POINTER(NativeAllocator), ctypes.POINTER(NativeRequest)]
    lib.portable_dac_voice_admit_request.restype = NativeDecision
    lib.portable_dac_voice_commit_request.argtypes = [
        ctypes.POINTER(NativeAllocator), ctypes.c_int16, ctypes.POINTER(NativeRequest)]
    lib.portable_dac_voice_commit_request.restype = ctypes.c_int
    lib.portable_dac_voice_set_active.argtypes = [
        ctypes.POINTER(NativeAllocator), ctypes.c_int16, ctypes.c_int]
    lib.portable_dac_voice_set_active.restype = ctypes.c_int
    return lib


class DosVoiceOracle:
    def __init__(self) -> None:
        row = functions.get("f_295C_00C9")
        if row["unit"] != "root":
            raise RuntimeError("DOS allocator is not in the resident root image")
        image = exe.load()
        if hashlib.sha256((ROOT / "assets/SIMANT.EXE").read_bytes()).hexdigest() != ORACLE_SHA256:
            raise RuntimeError("frozen DOS oracle identity differs from its pinned executable")
        self.entry = (row["seg"], row["off"])
        self.cpu = unicorn.Uc(unicorn.UC_ARCH_X86, unicorn.UC_MODE_16)
        self.cpu.mem_map(0, MEMORY_SIZE)
        self.cpu.mem_write(0, image.image)
        resident = image.sections[27]
        self.cpu.mem_write(resident.load_linear, resident.data)
        self.sample_offsets = [0x0100, 0x0120]
        self.release_call_count = 0
        self._word(DS, 0x8AA0, STATE_SEG)
        self._word(DS, 0x7DD4, STATE_SEG)
        self._word(DS, 0x7DD6, SAMPLE_SEG)
        self._word(SAMPLE_SEG, 0x7574, 1)  # keep resource cleanup out of f_0000_00DE
        self._word(DS, 0x181C, 0)
        self._word(STATE_SEG, 0x150, 0)
        self._word(STATE_SEG, 0x152, 0)

        def count_release(uc, address, size, user_data):
            if address == 0x149:
                self.release_call_count += 1
        self.cpu.hook_add(unicorn.UC_HOOK_CODE, count_release)

    def _linear(self, seg: int, off: int) -> int:
        return seg * 16 + off

    def _word(self, seg: int, off: int, value: int) -> None:
        self.cpu.mem_write(self._linear(seg, off), int(value & 0xFFFF).to_bytes(2, "little"))

    def _read_word(self, seg: int, off: int) -> int:
        return int.from_bytes(self.cpu.mem_read(self._linear(seg, off), 2), "little")

    def _write_channel_fixture(self, state: NativeAllocator) -> None:
        for index in range(2):
            channel = state.channels[index]
            off = CHANNEL_OFF + index * 6
            self.cpu.mem_write(self._linear(CHANNEL_SEG, off), bytes((
                1, index, channel.priority, channel.instrument_id & 0xFF,
                channel.note, channel.age)))
            slot_off = SLOT_OFF + index * 0x14
            self._word(STATE_SEG, slot_off, 1 if channel.active else 0)
            self._word(STATE_SEG, slot_off + 2, 0)
            if channel.owner_loaded:
                sample_off = self.sample_offsets[index]
                self._word(SAMPLE_SEG, sample_off + 0x0C, 1)
                self._word(STATE_SEG, slot_off + 0x0E, sample_off)
                self._word(STATE_SEG, slot_off + 0x10, SAMPLE_SEG)
            else:
                self._word(STATE_SEG, slot_off + 0x0E, 0)
                self._word(STATE_SEG, slot_off + 0x10, 0)
        self.cpu.mem_write(self._linear(CHANNEL_SEG, CHANNEL_OFF + 12), b"\0" * 6)

    def call(self, state: NativeAllocator, priority: int) -> tuple[int, list[int], list[tuple[int, int]]]:
        self._write_channel_fixture(state)
        releases_before = self._read_word(DS, 0x181C)
        sp = 0x8000
        frame = (SENTINEL_OFF.to_bytes(2, "little") +
                 SENTINEL_SEG.to_bytes(2, "little") +
                 (1).to_bytes(2, "little") + priority.to_bytes(2, "little"))
        self.cpu.mem_write(self._linear(DS, sp), frame)
        self.cpu.reg_write(xr.UC_X86_REG_SS, DS)
        self.cpu.reg_write(xr.UC_X86_REG_SP, sp)
        self.cpu.reg_write(xr.UC_X86_REG_DS, DS)
        self.cpu.reg_write(xr.UC_X86_REG_CS, self.entry[0])
        self.cpu.reg_write(xr.UC_X86_REG_IP, self.entry[1])
        begin = self._linear(*self.entry)
        self.cpu.emu_start(begin, self._linear(SENTINEL_SEG, SENTINEL_OFF), count=10000)
        result = self.cpu.reg_read(xr.UC_X86_REG_AX) & 0xFFFF
        selected = result if result < 0x8000 else result - 0x10000
        release_end = self._read_word(DS, 0x181C)
        released: list[int] = []
        pointers: list[tuple[int, int]] = []
        for index in range(releases_before, release_end):
            sample_off = self._read_word(STATE_SEG, 0x150 + index * 4)
            sample_seg = self._read_word(STATE_SEG, 0x152 + index * 4)
            pointers.append((sample_seg, sample_off))
            if sample_seg == SAMPLE_SEG and sample_off in self.sample_offsets:
                released.append(self.sample_offsets.index(sample_off))
        return selected, released, pointers

    def commit_source_caller(self, channel_index: int, request: NativeRequest) -> None:
        off = CHANNEL_OFF + channel_index * 6
        self.cpu.mem_write(self._linear(CHANNEL_SEG, off + 2),
                           bytes((request.priority, request.instrument_id,
                                  request.note, 0)))
        slot_off = SLOT_OFF + channel_index * 0x14
        self._word(STATE_SEG, slot_off, 1)
        self._word(STATE_SEG, slot_off + 2, 0)
        sample_off = self.sample_offsets[channel_index]
        self._word(SAMPLE_SEG, sample_off + 0x0C, 1)
        self._word(STATE_SEG, slot_off + 0x0E, sample_off)
        self._word(STATE_SEG, slot_off + 0x10, SAMPLE_SEG)

    def read_source_channel(self, channel_index: int) -> tuple[int, int, int, int]:
        off = CHANNEL_OFF + channel_index * 6
        data = self.cpu.mem_read(self._linear(CHANNEL_SEG, off + 2), 4)
        return data[0], data[1], data[2], data[3]


def run() -> dict:
    observed_pins = {name: digest(ROOT / name) for name in SOURCE_PINS}
    if observed_pins != SOURCE_PINS:
        raise RuntimeError("frozen source anchors changed: " + json.dumps(observed_pins))
    observed_assets = {name: digest(ROOT / name) for name in ASSET_PINS}
    if observed_assets != ASSET_PINS:
        raise RuntimeError("SOUND assets changed: " + json.dumps(observed_assets))
    compiler = shutil.which("gcc")
    if compiler is None:
        raise RuntimeError("gcc is required for the standalone native differential")
    with tempfile.TemporaryDirectory(prefix="voice-admission-") as directory:
        library = Path(directory) / "voice_admission.dll"
        subprocess.run([compiler, "-std=c11", "-Wall", "-Wextra", "-Wconversion",
                        "-Werror", "-shared", "-fPIC", "portable/research/audio_voice_admission.c",
                        "-o", str(library)], cwd=ROOT, check=True)
        native = bind_native(ctypes.CDLL(str(library)))
        state = NativeAllocator()
        native.portable_dac_voice_allocator_init(ctypes.byref(state))
        dos = DosVoiceOracle()
        # Exact source rows from d55B3_00B8.c, resolved through mode-1 DAC
        # rows in fd_55B3_0C42. These rows anchor instrument/note/priority,
        # with objects confirmed by each Sample initializer.
        profiles = {
            0: NativeRequest(0, 0, 35, 3, 60, 127),
            1: NativeRequest(1, 1, 1, 3, 60, 127),
            2: NativeRequest(2, 2, 2, 3, 60, 127),
            3: NativeRequest(3, 3, 56, 3, 60, 127),
            4: NativeRequest(4, 4, 4, 3, 60, 127),
            55: NativeRequest(55, 10, 10, 4, 100, 127),
        }
        calls = [
            # Fill both idle slots, then alternate equal-priority oldest wins.
            (0, 1), (1, 2), (3, 0), (3, 55),
            # The low-priority contrast is an allocator input, not a shipped SFX row.
            (3, -1),
            # Stop channel 0, release its source sample owner, and refill it.
            (2, 3), (3, 4), (3, 55),
            # Priority-zero early return is the negative no-mutation contrast.
            (3, -2),
        ]
        trace = []
        for active_mask, request_id in calls:
            if request_id == -1:
                request = NativeRequest(0, 0, 35, 1, 60, 127)
                label = "priority_below_active"
            elif request_id == -2:
                request = NativeRequest(0, 0, 35, 0, 60, 127)
                label = "priority_zero_early_return"
            else:
                request = profiles[request_id]
                label = f"sfx_{request_id}"
            priority = int(request.priority)
            for channel_index in range(2):
                active = 1 if active_mask & (1 << channel_index) else 0
                if not native.portable_dac_voice_set_active(ctypes.byref(state),
                                                             channel_index, active):
                    raise RuntimeError("native active state rejected valid channel")
            oracle_input = NativeAllocator()
            ctypes.memmove(ctypes.byref(oracle_input), ctypes.byref(state),
                           ctypes.sizeof(state))
            native_result = native.portable_dac_voice_admit_request(
                ctypes.byref(state), ctypes.byref(request))
            dos_selected, dos_released, dos_pointers = dos.call(oracle_input, priority)
            if native_result.selected_channel != dos_selected:
                raise AssertionError(("selection", active_mask, priority,
                                      native_result.selected_channel, dos_selected))
            native_released = list(native_result.released_owner_channels[:native_result.release_count])
            if native_released != dos_released:
                raise AssertionError(("owner release order", active_mask, priority,
                                      native_released, dos_released, dos_pointers,
                                      dos.release_call_count,
                                      [(int(oracle_input.channels[i].owner_loaded),
                                        int(oracle_input.channels[i].active),
                                        int(oracle_input.channels[i].age)) for i in range(2)]))
            for channel_index in range(2):
                native_channel = state.channels[channel_index]
                dos_priority, dos_instrument, dos_note, dos_age = dos.read_source_channel(channel_index)
                native_values = (native_channel.priority,
                                 native_channel.instrument_id & 0xFF,
                                 native_channel.note, native_channel.age)
                if native_values != (dos_priority, dos_instrument, dos_note, dos_age):
                    raise AssertionError(("mutated channel state", active_mask, priority,
                                          channel_index,
                                          native_values,
                                          (dos_priority, dos_instrument, dos_note, dos_age)))
            trace.append({"case": label, "sound_id": int(request.sound_id),
                          "instrument_id": int(request.instrument_id),
                          "sample_object_id": int(request.sample_object_id),
                          "note": int(request.note), "velocity": int(request.velocity),
                          "active_mask": active_mask, "priority": priority,
                          "selected": native_result.selected_channel,
                          "released_owners": native_released,
                          "channels": [[int(state.channels[i].priority),
                                        int(state.channels[i].age)] for i in range(2)]})
            selected = native_result.selected_channel
            if selected >= 0:
                if not native.portable_dac_voice_commit_request(
                        ctypes.byref(state), selected, ctypes.byref(request)):
                    raise RuntimeError("native commit rejected an accepted source channel")
                dos.commit_source_caller(selected, request)
                committed = dos.read_source_channel(selected)
                expected_commit = (request.priority, request.instrument_id,
                                   request.note, 0)
                if committed != expected_commit:
                    raise AssertionError(("source caller commit", committed, expected_commit))

        # Age is an unsigned source byte and wraps after 255. Exercise wrap under
        # an active two-channel schedule after resetting both allocators.
        native.portable_dac_voice_allocator_init(ctypes.byref(state))
        dos = DosVoiceOracle()
        for _ in range(270):
            for channel_index in range(2):
                native.portable_dac_voice_set_active(ctypes.byref(state), channel_index, 1)
            oracle_input = NativeAllocator()
            ctypes.memmove(ctypes.byref(oracle_input), ctypes.byref(state),
                           ctypes.sizeof(state))
            request = profiles[1]
            decision = native.portable_dac_voice_admit_request(
                ctypes.byref(state), ctypes.byref(request))
            original, released, _ = dos.call(oracle_input, 3)
            if decision.selected_channel != original or released:
                raise AssertionError(("age wrap", decision.selected_channel, original, released))
            for index in range(2):
                nc = state.channels[index]
                op, oi, on, oa = dos.read_source_channel(index)
                native_values = (nc.priority, nc.instrument_id & 0xFF, nc.note, nc.age)
                if native_values != (op, oi, on, oa):
                    raise AssertionError(("age wrap state", index, native_values,
                                          (op, oi, on, oa)))
            if decision.selected_channel >= 0:
                native.portable_dac_voice_commit_request(
                    ctypes.byref(state), decision.selected_channel,
                    ctypes.byref(request))
                dos.commit_source_caller(decision.selected_channel, request)
        result = {"schema": "dos-dac-voice-admission-differential-v1",
                "status": "PASS",
                "boundary": "direct frozen root:f_295C_00C9 execution; loaded f_0000_0149 resource-release routine executes; downstream mixer output is outside this allocator trace",
                "oracle_sha256": ORACLE_SHA256,
                "local_input_pins": {**observed_pins, **observed_assets,
                                     "assets/SIMANT.EXE": digest(ROOT / "assets/SIMANT.EXE"),
                                     "portable/research/audio_voice_admission.c": digest(ROOT / "portable/research/audio_voice_admission.c"),
                                     "portable/research/audio_voice_admission.h": digest(ROOT / "portable/research/audio_voice_admission.h"),
                                     "portable/tests/audio/voice_admission_differential.py": digest(Path(__file__))},
                "environment": {"python": sys.version.split()[0],
                                "compiler": subprocess.check_output([compiler, "--version"], text=True).splitlines()[0],
                                "unicorn": unicorn.__version__},
                "native_sha256": digest(ROOT / "portable/research/audio_voice_admission.c"),
                "asset_pins": observed_assets,
                "channel_count": 2,
                "calls_compared": len(calls),
                "age_wrap_calls": 270,
                "trace": trace}
        library_handle = native._handle
        del native
        _ctypes.FreeLibrary(library_handle)
        return result


if __name__ == "__main__":
    result = run()
    report = ROOT / "build/portable/audio-voice-admission-differential.json"
    report.parent.mkdir(parents=True, exist_ok=True)
    report_data = json.dumps(result, indent=2) + "\n"
    report.write_text(report_data)
    archive = ROOT / "portable/tests/audio/evidence/voice-admission-v1/report.json"
    archive.parent.mkdir(parents=True, exist_ok=True)
    archive.write_text(report_data)
    print(f"PASS DOS f_295C_00C9 calls={result['calls_compared']} age_wrap={result['age_wrap_calls']} archived={archive.relative_to(ROOT)}")
