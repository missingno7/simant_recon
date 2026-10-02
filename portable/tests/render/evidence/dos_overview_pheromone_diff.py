"""Direct S12 pheromone-buffer differential against the frozen DOS image."""
from __future__ import annotations

import ctypes
import hashlib
import json
import random
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "tools"))
import behavior
import exe
import functions


class SimWorldTiles(ctypes.Structure):
    _fields_ = [("surface", (ctypes.c_uint8 * 64) * 128),
                ("nest_b", (ctypes.c_uint8 * 64) * 64),
                ("nest_r", (ctypes.c_uint8 * 64) * 64),
                ("terrain_set", ctypes.c_int16)]


class SimGameWorldPrefix(ctypes.Structure):
    _fields_ = [("tiles", SimWorldTiles),
                ("exit_b", (ctypes.c_uint8 * 64) * 64),
                ("exit_r", (ctypes.c_uint8 * 64) * 64),
                ("life_a", (ctypes.c_uint8 * 64) * 128),
                ("life_b", (ctypes.c_uint8 * 64) * 64),
                ("life_r", (ctypes.c_uint8 * 64) * 64),
                ("pheromone_a", (ctypes.c_uint8 * 32) * 64),
                ("pheromone_b_nest", (ctypes.c_uint8 * 32) * 64),
                ("pheromone_b_trail", (ctypes.c_uint8 * 32) * 64),
                ("pheromone_r_nest", (ctypes.c_uint8 * 32) * 64),
                ("pheromone_r_trail", (ctypes.c_uint8 * 32) * 64)]


class SimOverviewInput(ctypes.Structure):
    _fields_ = [("world", ctypes.POINTER(SimGameWorldPrefix)),
                ("mode", ctypes.c_int16), ("hardware_profile", ctypes.c_int16),
                ("fresh", ctypes.c_uint8), ("previous_mode", ctypes.c_int16),
                ("previous_pixels", ctypes.POINTER(ctypes.c_uint8))]


class SimOverviewImage(ctypes.Structure):
    _fields_ = [("pixels", ctypes.c_uint8 * 8192), ("width", ctypes.c_uint16),
                ("height", ctypes.c_uint16), ("stride", ctypes.c_uint16),
                ("scale_x", ctypes.c_uint8), ("scale_y", ctypes.c_uint8),
                ("left_margin", ctypes.c_uint16), ("mode", ctypes.c_uint8),
                ("hardware_profile", ctypes.c_int16)]


SOURCE_OFF, SOURCE_SEG = 0x0200, 0xA100
DEST_OFF, DEST_SEG = 0x0100, 0xB000
PHEROMONE_FIELDS = {
    4: "pheromone_b_nest",
    5: "pheromone_b_trail",
    6: "pheromone_r_nest",
    7: "pheromone_r_trail",
    8: "pheromone_a",
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def run_dos(source: bytes, profile: int, case_id: str) -> bytes:
    function = functions.get("o12_384C_0706")
    vectors = {exe.MANAGER_SEG * 16 + vector.offset: vector
               for vector in exe.load().vectors}
    pair = SimpleNamespace(function=function, sequence_targets=frozenset(),
                           sequence_function=lambda name: functions.get(name),
                           vectors=vectors)
    machine = behavior.Machine(pair)
    case = behavior.Case(
        label=case_id,
        args=[SOURCE_OFF, SOURCE_SEG],
        writes=[(SOURCE_SEG * 16 + SOURCE_OFF, source),
                (behavior.symbol_address("g_5A97"), bytes([profile & 0xff]))],
        observe=[behavior.Range("expanded", DEST_SEG * 16 + DEST_OFF, 8192)],
        callbacks={
            "f_171C_1B84": behavior.Callback(
                stack_words=2,
                handler=lambda _machine, _args: (DEST_OFF, DEST_SEG)),
            "f_171C_1BBA": behavior.Callback(stack_words=2),
        },
        return_kind="void")
    result = machine.run(case, function="o12_384C_0706")
    return bytes.fromhex(result["ranges"]["expanded"])


def main() -> None:
    rng = random.Random(0x384C0706)
    library_path = ROOT / "build/workers/behavior_render_small/overview_diff.dll"
    subprocess.run(["gcc", "-std=c11", "-Wall", "-Wextra", "-Werror", "-shared",
                    "-Iportable", "portable/game/render/overview.c",
                    "portable/render/primitives.c", "-o", str(library_path)],
                   cwd=ROOT, check=True, capture_output=True, text=True)
    library = ctypes.CDLL(str(library_path))
    library.sim_overview_prepare.argtypes = [ctypes.POINTER(SimOverviewInput),
                                              ctypes.POINTER(SimOverviewImage)]
    library.sim_overview_prepare.restype = ctypes.c_int
    cases = []
    for profile in (0, 3):
        for mode, field in PHEROMONE_FIELDS.items():
            world = SimGameWorldPrefix()
            source = bytes(rng.randrange(256) for _ in range(2048))
            ctypes.memmove(ctypes.addressof(world) +
                           getattr(SimGameWorldPrefix, field).offset,
                           source, len(source))
            input_value = SimOverviewInput(ctypes.pointer(world), mode, profile,
                                           0, -1, None)
            image = SimOverviewImage()
            status = library.sim_overview_prepare(ctypes.byref(input_value),
                                                  ctypes.byref(image))
            if status != 0:
                raise AssertionError(f"portable prepare returned status {status}")
            case_id = f"mode-{mode}-profile-{profile}"
            dos_output = run_dos(source, profile, case_id)
            portable_output = bytes(image.pixels)
            equal = portable_output == dos_output
            cases.append({
                "case_id": case_id,
                "input_sha256": sha256(source),
                "dos_output_sha256": sha256(dos_output),
                "portable_output_sha256": sha256(portable_output),
                "equal": equal,
            })
            if not equal:
                mismatch = next(i for i, (a, b) in enumerate(
                    zip(portable_output, dos_output)) if a != b)
                raise AssertionError(
                    f"{case_id} differs at {mismatch}: "
                    f"portable={portable_output[mismatch]:02x}, "
                    f"DOS={dos_output[mismatch]:02x}")

    report = {
        "schema": "portable-overview-dos-differential-v1",
        "status": "PASS",
        "scope": "S12 pheromone selector-buffer comparison only; no raster or framebuffer claim",
        "framebuffer_raster_status": "NOT_ESTABLISHED_BY_THIS_REPORT",
        "function": "o12_384C_0706",
        "cases": cases,
        "row_count": len(cases),
        "bytes_per_case": 8192,
        "execution_boundary": "Original DOS target executes in Unicorn. Only f_171C_1B84 locks a synthetic 8192-byte output handle to B000:0100 and f_171C_1BBA unlock is a no-op.",
        "input_output_regions": {
            "source": "A100:0200..A100:09FF",
            "destination": "B000:0100..B000:20FF",
            "overlap": False
        },
        "source_hashes": {
            path: sha256((ROOT / path).read_bytes())
            for path in ("src/S12/m384C.c", "src/data/d3D57.c",
                         "tools/behavior.py", "portable/game/render/overview.c",
                         "portable/game/render/overview.h")
        },
        "oracle_sha256": exe.load().sha256,
        "unicorn_version": behavior.uc.__version__,
    }
    out = ROOT / "portable/tests/render/evidence/dos-overview-pheromone-differential.json"
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"DOS overview differential matched {len(cases)}/{len(cases)} cases.")


if __name__ == "__main__":
    main()
