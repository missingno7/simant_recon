"""Direct frozen-DOS differential probes for portable/game/simulation/rng.c.

Original root:0093 RNG entries and the linked MSC rand() routine run in the
isolated Unicorn machine. TickCount is the only injected boundary for startup
seeding. This is a diagnostic suite, not a historical acceptance registration.
"""
from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import random
import struct
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))
import behavior
import exe
import functions
import match

SRAND_STATE_ADDR = match.DGROUP_SEG * 16 + 0x8BA2
RAND_STATE_ADDR = match.DGROUP_SEG * 16 + 0x7BBE
MASKS = {
    "SRand2": ("sim_rng_s2", 0x0001),
    "SRand4": ("sim_rng_s4", 0x0003),
    "SRand8": ("sim_rng_s8", 0x0007),
    "SRand16": ("sim_rng_s16", 0x000F),
    "SRand32": ("sim_rng_s32", 0x001F),
    "SRand64": ("sim_rng_s64", 0x003F),
    "SRand128": ("sim_rng_s128", 0x007F),
    "SRand256": ("sim_rng_s256", 0x00FF),
}
S1_RANGES = (1, 3, 7, 8, 255, 32767, 65535)
SG_CASES = (("SGIRand", "sim_rng_sg_i"),
            ("SGRand", "sim_rng_sg"),
            ("SGSRand", "sim_rng_sg_signed"))


class SimRng(ctypes.Structure):
    _fields_ = [("s_state", ctypes.c_uint16), ("c_state", ctypes.c_uint32)]


def digest_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def bind_native(path: Path):
    lib = ctypes.CDLL(str(path.resolve()))
    P = ctypes.POINTER(SimRng)
    lib.sim_rng_set_s_seed.argtypes = [P, ctypes.c_int16]
    lib.sim_rng_seed_s_from_tick.argtypes = [P, ctypes.c_uint32]
    lib.sim_rng_seed_startup.argtypes = [P, ctypes.c_uint32, ctypes.c_uint32]
    lib.sim_rng_seed_r.argtypes = [P, ctypes.c_uint32, ctypes.c_uint32]
    lib.sim_rng_get_s_seed.argtypes = [P]
    lib.sim_rng_get_s_seed.restype = ctypes.c_uint16
    lib.sim_rng_get_c_seed.argtypes = [P]
    lib.sim_rng_get_c_seed.restype = ctypes.c_uint32
    lib.sim_rng_s1.argtypes = [P, ctypes.c_uint16, ctypes.POINTER(ctypes.c_uint16)]
    lib.sim_rng_s1.restype = ctypes.c_int
    for native_name, _ in MASKS.values():
        fn = getattr(lib, native_name)
        fn.argtypes = [P]
        fn.restype = ctypes.c_uint16
    for _, native_name in SG_CASES:
        fn = getattr(lib, native_name)
        fn.argtypes = [P, ctypes.c_uint16 if native_name != "sim_rng_sg_signed" else ctypes.c_int16,
                       ctypes.POINTER(ctypes.c_int16)]
        fn.restype = ctypes.c_int
    lib.sim_rng_msc_rand.argtypes = [P]
    lib.sim_rng_msc_rand.restype = ctypes.c_uint16
    lib.sim_rng_r.argtypes = [P, ctypes.c_int16, ctypes.POINTER(ctypes.c_int16)]
    lib.sim_rng_r.restype = ctypes.c_int
    return lib


def oracle_machine():
    pair = SimpleNamespace(
        function=functions.get("SRand1"),
        sequence_targets=frozenset(),
        sequence_function=lambda name: functions.get(name),
        vectors={exe.MANAGER_SEG * 16 + v.offset: v for v in exe.load().vectors},
    )
    return behavior.Machine(pair)


def u16(value: int) -> bytes:
    return struct.pack("<H", value & 0xFFFF)


def u32(value: int) -> bytes:
    return struct.pack("<I", value & 0xFFFFFFFF)


def seed_case(machine, function: str, seed: int, args=(), return_kind="u16"):
    return machine.run(behavior.Case(
        label=f"{function}/seed{seed:04x}",
        args=list(args),
        writes=[(SRAND_STATE_ADDR, u16(seed))],
        return_kind=return_kind,
    ), function=function)


def run_mask_sweeps(lib, machine):
    # Native implementation is checked exhaustively against the source-level
    # recurrence. Original DOS execution is sampled at 518 strata per helper;
    # a per-state fresh Unicorn invocation makes a full 8 x 65536 oracle sweep
    # disproportionately expensive, so do not imply that it was run.
    oracle_seeds = sorted(set(range(0, 65536, 128)) |
                          {0, 1, 2, 0x7FFF, 0x8000, 0xFFFF, 0x3751, 0xA55A})
    summary = {"native_seeds_per_mask": 65536, "original_oracle_seeds_per_mask": len(oracle_seeds),
               "functions": {}, "mismatches": 0}
    aggregate = hashlib.sha256()
    for original_name, (native_name, mask) in MASKS.items():
        native_fn = getattr(lib, native_name)
        native_transcript = hashlib.sha256()
        oracle_transcript = hashlib.sha256()
        oracle_seed_set = set(oracle_seeds)
        for seed in range(65536):
            native_rng = SimRng(seed, 0x12345678)
            native_value = int(native_fn(ctypes.byref(native_rng)))
            expected_state = ((seed << 1) & 0xFFFF) ^ (0x1BF5 if seed & 0x8000 else 0)
            expected_value = expected_state & mask
            if native_value != expected_value or native_rng.s_state != expected_state:
                raise AssertionError({"native_function": native_name, "seed": seed,
                                      "native": native_value, "expected": expected_value,
                                      "native_state": native_rng.s_state,
                                      "expected_state": expected_state})
            row = struct.pack("<HHH", seed, expected_value, expected_state)
            native_transcript.update(row)
            if seed in oracle_seed_set:
                oracle = seed_case(machine, original_name, seed)
                final_seed = struct.unpack("<H", machine.read(SRAND_STATE_ADDR, 2))[0]
                if oracle["return"] != expected_value or final_seed != expected_state:
                    raise AssertionError({"function": original_name, "seed": seed,
                                          "oracle": oracle["return"], "expected": expected_value,
                                          "oracle_state": final_seed, "expected_state": expected_state})
                oracle_transcript.update(row)
                aggregate.update(original_name.encode() + row)
        summary["functions"][original_name] = {
            "native_exhaustive_transcript_sha256": native_transcript.hexdigest(),
            "original_oracle_sample_transcript_sha256": oracle_transcript.hexdigest(),
            "original_oracle_cases": len(oracle_seeds),
        }
    summary["ordered_all_mask_transcript_sha256"] = aggregate.hexdigest()
    return summary


def run_s1_sweeps(lib, machine):
    fn = lib.sim_rng_s1
    native_transcript = hashlib.sha256()
    oracle_transcript = hashlib.sha256()
    counts = {str(r): 0 for r in S1_RANGES}
    for seed in range(65536):
        expected_state = ((seed << 1) & 0xFFFF) ^ (0x1BF5 if seed & 0x8000 else 0)
        for range_value in S1_RANGES:
            native_rng = SimRng(seed, 0xA5A5A5A5)
            value = ctypes.c_uint16(0xC0DE)
            ok = fn(ctypes.byref(native_rng), range_value, ctypes.byref(value))
            expected_value = expected_state % range_value
            if (ok != 1 or value.value != expected_value or
                    native_rng.s_state != expected_state):
                raise AssertionError({"function": "SRand1/native", "seed": seed,
                                      "range": range_value, "native": value.value,
                                      "native_state": native_rng.s_state,
                                      "expected": expected_value, "expected_state": expected_state})
            native_transcript.update(struct.pack("<HHHH", seed, range_value,
                                                 expected_value, expected_state))
            counts[str(range_value)] += 1

    oracle_seeds = sorted(set(range(0, 65536, 32)) |
                          {0, 1, 2, 0x7FFF, 0x8000, 0xFFFF, 0x3751, 0xA55A})
    oracle_counts = {str(r): 0 for r in S1_RANGES}
    for i, seed in enumerate(oracle_seeds):
        range_value = S1_RANGES[i % len(S1_RANGES)]
        oracle = seed_case(machine, "SRand1", seed, [range_value])
        final_seed = struct.unpack("<H", machine.read(SRAND_STATE_ADDR, 2))[0]
        expected_state = ((seed << 1) & 0xFFFF) ^ (0x1BF5 if seed & 0x8000 else 0)
        expected_value = expected_state % range_value
        if oracle["return"] != expected_value or final_seed != expected_state:
            raise AssertionError({"function": "SRand1/original", "seed": seed,
                                  "range": range_value, "oracle": oracle["return"],
                                  "oracle_state": final_seed, "expected": expected_value,
                                  "expected_state": expected_state})
        oracle_transcript.update(struct.pack("<HHHH", seed, range_value,
                                             expected_value, expected_state))
        oracle_counts[str(range_value)] += 1
    return {"native_cases": 65536 * len(S1_RANGES), "native_range_counts": counts,
            "original_oracle_cases": len(oracle_seeds), "original_oracle_range_counts": oracle_counts,
            "native_exhaustive_transcript_sha256": native_transcript.hexdigest(),
            "original_oracle_sample_transcript_sha256": oracle_transcript.hexdigest(), "mismatches": 0}


def run_signed_helpers(lib, machine, seed: int):
    rows = []
    ranges = (1, 2, 3, 7, 8, 255, 1024, 32767)
    for original_name, native_name in SG_CASES:
        for range_value in ranges:
            oracle = seed_case(machine, original_name, seed, [range_value], "s16")
            final_seed = struct.unpack("<H", machine.read(SRAND_STATE_ADDR, 2))[0]
            native_rng = SimRng(seed, 0xCAFEBABE)
            value = ctypes.c_int16(0x4D2B)
            ok = getattr(lib, native_name)(ctypes.byref(native_rng), range_value,
                                           ctypes.byref(value))
            if ok != 1 or oracle["return"] != value.value or final_seed != native_rng.s_state:
                raise AssertionError({"function": original_name, "seed": seed,
                                      "range": range_value, "oracle": oracle["return"],
                                      "oracle_state": final_seed, "native": value.value,
                                      "native_state": native_rng.s_state})
            rows.append([original_name, range_value, oracle["return"], final_seed])
    return rows


def run_sg_sweeps(lib, machine):
    seeds = [0, 1, 2, 0x7FFF, 0x8000, 0xFFFF, 0x3751, 0xA55A]
    rng = random.Random(0x5A6D_0093)
    seeds.extend(rng.randrange(65536) for _ in range(512))
    transcript = hashlib.sha256()
    cases = 0
    for seed in seeds:
        rows = run_signed_helpers(lib, machine, seed)
        for name, range_value, value, final_seed in rows:
            transcript.update(name.encode() + struct.pack("<HHhH", seed, range_value,
                                                           value, final_seed))
            cases += 1
    return {"directed_and_random_seeds": len(seeds), "cases": cases,
            "range_values": [1, 2, 3, 7, 8, 255, 1024, 32767],
            "input_domain": "positive signed-int range 1..32767; zero/negative excluded",
            "ordered_transcript_sha256": transcript.hexdigest(), "mismatches": 0}


def tick_callback(values, seen):
    iterator = iter(values)

    def handler(machine, args):
        value = next(iterator)
        seen.append(value)
        return value & 0xFFFF, (value >> 16) & 0xFFFF

    return behavior.Callback(stack_words=0, handler=handler)


def lfsr_next(state):
    value = (state << 1) & 0xFFFF
    if state & 0x8000:
        value ^= 0x1BF5
    return value


def warmup_extreme_ticks():
    want = {0: None, 127: None}
    for tick in range(65536):
        seed = tick ^ 0x3751
        count = lfsr_next(seed) & 0x7F
        if count in want and want[count] is None:
            want[count] = tick
    return want


def seed_pair_cases():
    extremes = warmup_extreme_ticks()
    ticks = [
        (0, 0), (1, 1), (0x12345678, 0x89ABCDEF),
        (0xFFFFFFFF, 0x80000000), (0x10000, 0xFFFF),
        (extremes[0], 0), (extremes[127], 0xFFFFFFFF),
    ]
    rng = random.Random(0x5EED_0093)
    ticks.extend((rng.getrandbits(32), rng.getrandbits(32)) for _ in range(96))
    return ticks, extremes


def run_startup_sweeps(lib, machine):
    ticks, extremes = seed_pair_cases()
    transcript = hashlib.sha256()
    limit_sequence = (1, 3, 7, 8, 255, 32767) * 3
    rows = []
    for index, (lfsr_tick, c_tick) in enumerate(ticks):
        seen = []
        case = behavior.Case(
            label=f"SeedRRand/tick-pair-{index}",
            callbacks={"TickCount": tick_callback([lfsr_tick, c_tick], seen)},
            return_kind="void",
        )
        machine.run(case, function="SeedRRand")
        original_s = struct.unpack("<H", machine.read(SRAND_STATE_ADDR, 2))[0]
        original_c = struct.unpack("<I", machine.read(RAND_STATE_ADDR, 4))[0]

        native_rng = SimRng(0xBEEF, 0xDEADBEEF)
        lib.sim_rng_seed_startup(ctypes.byref(native_rng), lfsr_tick, c_tick)
        if len(seen) != 2 or seen != [lfsr_tick, c_tick]:
            raise AssertionError({"SeedRRand": "TickCount call sequence", "expected": [lfsr_tick, c_tick], "seen": seen})
        if original_s != native_rng.s_state or original_c != native_rng.c_state:
            raise AssertionError({"SeedRRand": "warmed seeds differ", "ticks": [lfsr_tick, c_tick],
                                  "original_s": original_s, "native_s": native_rng.s_state,
                                  "original_c": original_c, "native_c": native_rng.c_state})
        calls = []
        for draw, limit in enumerate(limit_sequence):
            observed = machine.run(behavior.Case(
                label=f"SeedRRand/rrand/{index}/{draw}", args=[limit], return_kind="s16"),
                preserve=True, function="RRand")
            original_s_after = struct.unpack("<H", machine.read(SRAND_STATE_ADDR, 2))[0]
            original_c_after = struct.unpack("<I", machine.read(RAND_STATE_ADDR, 4))[0]
            value = ctypes.c_int16(0x5678)
            ok = lib.sim_rng_r(ctypes.byref(native_rng), limit, ctypes.byref(value))
            if (ok != 1 or observed["return"] != value.value or
                    original_s_after != native_rng.s_state or original_c_after != native_rng.c_state):
                raise AssertionError({"SeedRRand": "RRand mismatch", "ticks": [lfsr_tick, c_tick],
                                      "draw": draw, "limit": limit, "original": observed["return"],
                                      "native": value.value, "original_s": original_s_after,
                                      "native_s": native_rng.s_state, "original_c": original_c_after,
                                      "native_c": native_rng.c_state})
            calls.append(value.value)
        row = struct.pack("<IIHHI", lfsr_tick, c_tick, original_s, len(seen), original_c)
        transcript.update(row)
        for value in calls:
            transcript.update(struct.pack("<h", value))
        rows.append({"ticks": [lfsr_tick, c_tick], "warm_s": original_s,
                     "warm_c": original_c, "rrand_draws": len(calls)})
    return {"tick_pairs": len(ticks), "tick_calls_per_seed": 2,
            "rrand_draws_per_pair": len(limit_sequence),
            "warmup_boundary_tick_values": {str(k): v for k, v in extremes.items()},
            "ordered_transcript_sha256": transcript.hexdigest(),
            "mismatches": 0, "sample_rows": rows[:7]}


def run_seed_srand(lib, machine):
    ticks = [0, 1, 0x7FFF, 0x8000, 0xFFFF, 0x10000, 0x12345678, 0xFFFFFFFF]
    transcript = hashlib.sha256()
    for tick in ticks:
        seen = []
        case = behavior.Case(
            label=f"SeedSRand/tick-{tick:08x}",
            callbacks={"TickCount": tick_callback([tick], seen)},
            return_kind="void",
        )
        machine.run(case, function="SeedSRand")
        original_s = struct.unpack("<H", machine.read(SRAND_STATE_ADDR, 2))[0]
        native_rng = SimRng(0, 0)
        lib.sim_rng_seed_s_from_tick(ctypes.byref(native_rng), tick)
        if seen != [tick] or original_s != native_rng.s_state:
            raise AssertionError({"SeedSRand": "mismatch", "tick": tick,
                                  "seen": seen, "original": original_s,
                                  "native": native_rng.s_state})
        transcript.update(struct.pack("<IH", tick, original_s))
    return {"cases": len(ticks), "tick_calls_per_case": 1,
            "ordered_transcript_sha256": transcript.hexdigest(), "mismatches": 0}


def run_arbitrary_c_states(lib, machine):
    rng = random.Random(0xC0FFEE_0093)
    seeds = [0, 1, 0xFFFFFFFF, 0x80000000, 0x7FFFFFFF, 0x12345678, 0x89ABCDEF]
    seeds.extend(rng.getrandbits(32) for _ in range(8192))
    transcript = hashlib.sha256()
    for state in seeds:
        oracle = machine.run(behavior.Case(
            label=f"RRand/arbitrary-c-state-{state:08x}",
            args=[32768],
            writes=[(RAND_STATE_ADDR, u32(state))],
            return_kind="s16",
        ), function="RRand")
        oracle_state = struct.unpack("<I", machine.read(RAND_STATE_ADDR, 4))[0]
        native_rng = SimRng(0xA55A, state)
        native_value = int(lib.sim_rng_msc_rand(ctypes.byref(native_rng)))
        if (oracle["return"] != native_value or oracle_state != native_rng.c_state):
            raise AssertionError({"RRand": "arbitrary C state mismatch", "state": state,
                                  "oracle": oracle["return"], "native": native_value,
                                  "oracle_state": oracle_state, "native_state": native_rng.c_state})
        transcript.update(struct.pack("<IHI", state, native_value, native_rng.c_state))
    return {"states": len(seeds), "state_domain": "all uint32; direct MSC rand() state injection at manifest-pinned 4-byte rand.c data contribution", "mismatches": 0,
            "ordered_transcript_sha256": transcript.hexdigest()}


def run_setter_and_getter(machine):
    seeds = (0, 1, 0x7FFF, 0x8000, 0xFFFF, 0x3751, 0xA55A)
    for seed in seeds:
        machine.run(behavior.Case("SetSRandSeed", args=[seed], return_kind="void"),
                    function="SetSRandSeed")
        state = struct.unpack("<H", machine.read(SRAND_STATE_ADDR, 2))[0]
        result = machine.run(behavior.Case("GetSRandSeed", return_kind="u32"),
                             preserve=True, function="GetSRandSeed")
        if state != seed or result["return"] != seed:
            raise AssertionError({"seed": seed, "stored": state, "getter": result["return"]})
    return {"seeds": len(seeds), "values": list(seeds), "mismatches": 0}


def run_invalid_range_controls(lib, machine):
    seed = 0xA55A
    rng = SimRng(seed, 0x12345678)
    value = ctypes.c_uint16(0xBEEF)
    ok_s = lib.sim_rng_s1(ctypes.byref(rng), 0, ctypes.byref(value))
    s1_native = {"accepted": int(ok_s), "seed_after": int(rng.s_state), "output_after": int(value.value)}
    r_value = ctypes.c_int16(0xBEEF)
    ok_r = lib.sim_rng_r(ctypes.byref(rng), 0, ctypes.byref(r_value))
    r_native = {"accepted": int(ok_r), "seed_after": int(rng.s_state), "output_after": int(r_value.value)}
    sg_value = ctypes.c_int16(0xBEEF)
    ok_sg = lib.sim_rng_sg_signed(ctypes.byref(rng), -1, ctypes.byref(sg_value))
    sg_native = {"accepted": int(ok_sg), "seed_after": int(rng.s_state), "output_after": int(sg_value.value)}
    if (ok_s != 0 or ok_r != 0 or ok_sg != 0 or rng.s_state != seed or
            value.value != 0xBEEF or r_value.value != ctypes.c_int16(0xBEEF).value or
            sg_value.value != ctypes.c_int16(0xBEEF).value):
        raise AssertionError({"native_invalid_range": "state or output changed",
                              "seed_expected": seed, "seed_after": rng.s_state,
                              "s1_output": value.value, "r_output": r_value.value,
                              "sg_output": sg_value.value,
                              "accepted": [int(ok_s), int(ok_r), int(ok_sg)]})

    try:
        seed_case(machine, "SRand1", seed, [0])
        srandoff = "did_not_fault"
    except behavior.ExecutionError as exc:
        srandoff = str(exc)
    try:
        machine.run(behavior.Case("RRand/div-zero", args=[0], writes=[(RAND_STATE_ADDR, u32(1))],
                                  return_kind="s16"), function="RRand")
        rrandoff = "did_not_fault"
    except behavior.ExecutionError as exc:
        rrandoff = str(exc)
    division_faults = ("divide", "unmodeled interrupt 00", "unmodeled interrupt 08")
    if not any(token in srandoff.lower() for token in division_faults) and not any(
            token in rrandoff.lower() for token in division_faults):
        raise AssertionError({"SRand1_zero": srandoff, "RRand_zero": rrandoff})
    return {
        "native_srand1_zero": s1_native,
        "native_rrand_zero": r_native,
        "native_sg_signed_negative": sg_native,
        "original_srand1_zero": f"DOS INT 0 divide fault ({srandoff}); deliberately not treated as equivalent to rejection",
        "original_rrand_zero": f"DOS INT 0 divide fault ({rrandoff}); deliberately not treated as equivalent to rejection",
        "fault_captured": True,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--library", type=Path,
                        default=ROOT / "build/workers/rng_differential/rng.dll")
    parser.add_argument("--output", type=Path,
                        default=ROOT / "portable/tests/rng/rng-dos-differential.json")
    parser.add_argument("--skip-exhaustive", action="store_true")
    args = parser.parse_args()

    lib = bind_native(args.library)
    machine = oracle_machine()
    report = {
        "suite": "portable_rng_original_dos_differential_v1",
        "status": "DIAGNOSTIC_PASS_NO_ACCEPTANCE_CLAIM",
        "oracle": {"sha256": exe.load().sha256, "unicorn": behavior.uc.__version__},
        "harness_sha256": behavior.digest(behavior.HARNESS_SOURCE),
        "suite_sha256": digest_file(Path(__file__)),
        "native_source_sha256": digest_file(ROOT / "portable/game/simulation/rng.c"),
        "native_header_sha256": digest_file(ROOT / "portable/game/simulation/rng.h"),
        "native_library_sha256": digest_file(args.library),
        "source_anchors": {
            "rng_source": {"path": "src/root/m0093.c", "sha256": digest_file(ROOT / "src/root/m0093.c")},
            "rand_member": {"library": "llibcr.lib", "member": "rand.c",
                            "sha256": "b569e225824dcaef61bcaa7e351b1a764772804fa376b7be2586935616220f02",
                            "state_address_linear": RAND_STATE_ADDR,
                            "state_bytes": 4,
                            "manifest_data_linear": 382702},
            "private_s_seed": {"DGROUP_offset": 0x8BA2, "linear": SRAND_STATE_ADDR,
                                "verified_from_original_SetSRandSeed_and_GetSRandSeed_operands": True},
        },
        "source_domains": {
            "SRand1": "unsigned 16-bit range 1..65535; range zero reaches DOS div and faults.",
            "SGIRand_SGRand_SGSRand": "positive signed-int ranges 1..32767; negative/zero behavior is excluded from equivalence.",
            "RRand": "positive signed-int limits 1..32767; zero reaches DOS idiv and faults.",
            "seed_zero": "tested as a pure LFSR state; no world-generation or termination claim is made.",
        },
    }

    report["SetSRandSeed_GetSRandSeed"] = run_setter_and_getter(machine)
    report["SeedSRand"] = run_seed_srand(lib, machine)
    if not args.skip_exhaustive:
        report["mask_functions"] = run_mask_sweeps(lib, machine)
        report["SRand1"] = run_s1_sweeps(lib, machine)
    report["SG_helpers"] = run_sg_sweeps(lib, machine)
    report["SeedRRand_and_RRand"] = run_startup_sweeps(lib, machine)
    report["MSC_rand_arbitrary_state"] = run_arbitrary_c_states(lib, machine)
    report["invalid_range_controls"] = run_invalid_range_controls(lib, machine)
    report["scope"] = (
        "Direct DOS RNG and linked CRT rand entries compared to native rng.c. "
        "TickCount is injected deterministically at exactly the two SeedRRand call sites. "
        "No world-generation function is invoked; invalid DOS divide ranges are reported as faults, not equivalence cases."
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
