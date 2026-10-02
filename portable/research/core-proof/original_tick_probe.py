#!/usr/bin/env python3
"""Capture a real DOS RandWorld -> DoAntSim sequence for native fixture work.

This records the frozen DOS execution only. It does not compare a native tick
or establish native equivalence. Every helper in DoAntSim executes from the
original image unless the bounded path reaches an explicit provider below.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
import math
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[3]
TOOLS = ROOT / "tools"
DEFAULT_GENERATED = ROOT / "build/workers/recovered_source/generated"
sys.path.insert(0, str(TOOLS))
sys.path.insert(0, str(ROOT / "portable/tests/worldgen"))

import behavior  # noqa: E402
import functions  # noqa: E402
import run_dos_diff  # noqa: E402

TICK_RANGES = [
    ("fd_3D57_07B2", 2), ("fd_50F6_0F06", 2), ("fd_50F6_0F2E", 2),
    ("fd_50F6_0F10", 2), ("fd_50F6_0EF6", 2), ("fd_50F6_08EC", 4),
    ("fd_50F6_0AA2", 4), ("fd_50F6_0A02", 4), ("fd_50F6_0852", 4),
    ("fd_50F6_0D40", 40), ("fd_50F6_0D72", 40),
    ("fd_50F6_08DC", 2), ("fd_50F6_08E8", 2),
    ("fd_50F6_0B12", 12), ("fd_50F6_0C2A", 12),
    ("fd_3D57_02C2", 2),
]
RAND_STATE_ADDR = behavior.match.DGROUP_SEG * 16 + 0x7BBE

# Native recovered-state fields come from the source-backed DATA/global schema.
# Capture each by its original symbol address so the native fixture can hydrate
# the actual struct layout without inventing values for omitted globals.
STATE_SCALAR_BYTES = {
    "int8_t": 1, "uint8_t": 1, "int16_t": 2, "uint16_t": 2,
    "int32_t": 4, "uint32_t": 4, "RecoveredPoint": 4,
    "struct Pt": 4, "struct Rect": 8,
}


def recovered_state_ranges(generated_dir: Path = DEFAULT_GENERATED) -> list[behavior.Range]:
    provenance_path = generated_dir / "provenance.json"
    provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
    fields = provenance["recovered_state"]["fields"]
    result = []
    for field in fields:
        unit = STATE_SCALAR_BYTES.get(field["type"])
        if unit is None:
            # Pointer fields are host bindings, not DOS value state.
            continue
        count = math.prod(int(dim, 0) for dim in field["dims"]) if field["dims"] else 1
        result.append(behavior.Range(
            field["name"], behavior.symbol_address(field["name"]), unit * count
        ))
    return result


def digest_ranges(ranges: dict[str, str]) -> str:
    payload = json.dumps(ranges, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def run_one(seed: int, scenario: int, cycle: int,
            generated_dir: Path = DEFAULT_GENERATED) -> dict:
    image = behavior.exe.load()
    pair = SimpleNamespace(
        function=functions.get("RandWorld"),
        vectors={behavior.exe.MANAGER_SEG * 16 + v.offset: v for v in image.vectors},
    )
    # Machine.sequence_function normally limits continuation calls to the
    # prepared module. The oracle-only fixture sequence intentionally changes
    # from the RandWorld entry to root DoAntSim while preserving VM memory.
    pair.sequence_function = functions.get
    class FunctionTraceMachine(behavior.Machine):
        def __init__(self, prepared):
            self.function_entries = []
            self.host_entry_stack = []
            self.entry_names = {}
            for spelling, symbol in behavior.match.symbols().items():
                if symbol.get("kind") == "code":
                    address = symbol["seg"] * 16 + symbol["off"]
                    self.entry_names.setdefault(address, spelling.lstrip("_"))
            super().__init__(prepared)

        def _on_block(self, cpu, address, size, userdata):
            name = self.entry_names.get(address)
            if name is not None:
                self.function_entries.append(name)
                if name in {"TickCount", "MacTickCount", "ZapEuMapAt",
                            "SetDefaultWindPrompt", "EditMessage", "OpenHistoryWindow"}:
                    ss, sp = self.reg("ss"), self.reg("sp")
                    stack = ss * 16 + sp
                    words = [self.word(stack + offset) for offset in range(0, 16, 2)]
                    self.host_entry_stack.append({
                        "name": name, "ss": ss, "sp": sp,
                        "stack_words_at_entry": words,
                    })
            return super()._on_block(cpu, address, size, userdata)

    machine = FunctionTraceMachine(pair)
    initial_case = run_dos_diff.case_for(seed, scenario)
    state_ranges = recovered_state_ranges(generated_dir)
    observed_names = {item.name for item in initial_case.observe}
    for name, size in TICK_RANGES:
        if name not in observed_names:
            initial_case.observe.append(
                behavior.Range(name, behavior.symbol_address(name), size)
            )
            observed_names.add(name)
    for item in state_ranges:
        if item.name in observed_names:
            # Older focused worldgen observations may cover a prefix of a
            # generated field (for example the 1000 live ant slots vs the
            # 1001-byte source array including its sentinel). Whole-state
            # snapshots must use the source declaration's complete extent.
            initial_case.observe = [
                item if prior.name == item.name else prior
                for prior in initial_case.observe
            ]
        else:
            initial_case.observe.append(item)
            observed_names.add(item.name)
    seed_case = behavior.Case(
        label="startup-seed-random-streams",
        writes=initial_case.writes,
        observe=initial_case.observe,
        return_kind="void",
        max_instructions=initial_case.max_instructions,
        max_blocks=initial_case.max_blocks,
    )
    machine.run(seed_case, function="SeedRRand")
    clock_case = behavior.Case(label="read-startup-source-tick", return_kind="u32")
    source_tick_count = machine.run(
        clock_case, preserve=True, function="TickCount"
    )["return"]
    machine.function_entries.clear()
    world_case = behavior.Case(
        label=initial_case.label,
        args=initial_case.args,
        observe=initial_case.observe,
        return_kind="void",
        max_instructions=initial_case.max_instructions,
        max_blocks=initial_case.max_blocks,
    )
    generated = machine.run(world_case, preserve=True, function="RandWorld")
    initial_ranges = generated["ranges"]
    world_rand_calls = machine.function_entries.count("rand")
    initial_c_rng = struct.unpack("<I", machine.read(RAND_STATE_ADDR, 4))[0]
    machine.function_entries.clear()
    initial_rng = machine.run(
        behavior.Case(label="get-s-rng-before-tick"),
        preserve=True, function="GetSRandSeed",
    )["return"]
    machine.set_word(behavior.symbol_address("Cycle"), cycle)
    # RandWorld initializes Cycle to zero; capture the caller's actual
    # cycle override in pre-tick state for periodic-path fixtures.
    initial_ranges["Cycle"] = (cycle & 0xFFFF).to_bytes(2, "little").hex()
    machine.function_entries.clear()
    machine.host_entry_stack.clear()
    tick_case = behavior.Case(
        label=f"do-ant-sim-cycle-{cycle}",
        observe=initial_case.observe,
        max_instructions=10_000_000,
        max_blocks=1_000_000,
    )
    tick = machine.run(tick_case, preserve=True, function="DoAntSim")
    tick_rand_calls = machine.function_entries.count("rand")
    post_tick_c_rng = struct.unpack("<I", machine.read(RAND_STATE_ADDR, 4))[0]
    tick_function_entries = list(machine.function_entries)
    tick_host_stack = list(machine.host_entry_stack)
    final_ranges = tick["ranges"]
    final_rng = machine.run(
        behavior.Case(label="get-s-rng-after-tick"),
        preserve=True, function="GetSRandSeed",
    )["return"]
    changed = {
        name: {"before": initial_ranges[name], "after": final_ranges[name]}
        for name in initial_ranges
        if initial_ranges[name] != final_ranges[name]
    }
    machine.function_entries.clear()
    machine.host_entry_stack.clear()
    next_tick = machine.run(
        behavior.Case(
            label=f"do-ant-sim-consecutive-after-{cycle}",
            observe=initial_case.observe,
            max_instructions=10_000_000,
            max_blocks=1_000_000,
        ),
        preserve=True,
        function="DoAntSim",
    )
    consecutive_rand_calls = machine.function_entries.count("rand")
    consecutive_c_rng = struct.unpack("<I", machine.read(RAND_STATE_ADDR, 4))[0]
    consecutive_ranges = next_tick["ranges"]
    consecutive_rng = machine.run(
        behavior.Case(label="get-s-rng-after-consecutive-tick"),
        preserve=True, function="GetSRandSeed",
    )["return"]
    consecutive_host_stack = list(machine.host_entry_stack)
    return {
        "cycle_before_tick": cycle,
        "randworld_blocks": generated["blocks"],
        "tick_blocks": tick["blocks"],
        "tick_return": tick["return"],
        "tick_host_trace": tick["trace"],
        "executed_function_entries": tick_function_entries,
        "host_entry_stack": tick_host_stack,
        "consecutive_host_entry_stack": consecutive_host_stack,
        "s_rng_seed_before_tick": initial_rng,
        "s_rng_seed_after_tick": final_rng,
        "pre_tick_ranges": initial_ranges,
        "post_tick_ranges": final_ranges,
        "consecutive_post_tick_ranges": consecutive_ranges,
        "recovered_source_globals": [item.name for item in state_ranges],
        "pre_tick_sha256": digest_ranges(initial_ranges),
        "post_tick_sha256": digest_ranges(final_ranges),
        "source_tick_count": source_tick_count,
        "source_mac_tick_count": (source_tick_count * 3) & 0xFFFFFFFF,
        "rand_calls_during_randworld": world_rand_calls,
        "original_c_rng_state_address_linear": RAND_STATE_ADDR,
        "original_c_rng_state_before_tick": initial_c_rng,
        "rand_calls_during_tick": tick_rand_calls,
        "rand_calls_during_consecutive_tick": consecutive_rand_calls,
        "original_c_rng_state_after_tick": post_tick_c_rng,
        "original_c_rng_state_after_consecutive_tick": consecutive_c_rng,
        "s_rng_seed_after_consecutive_tick": consecutive_rng,
        "consecutive_tick_blocks": next_tick["blocks"],
        "changed_ranges": changed,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=lambda x: int(x, 0), default=0x5A31)
    parser.add_argument("--scenario", type=lambda x: int(x, 0), default=0)
    parser.add_argument("--cycles", default="0,30,31,32,62,63")
    parser.add_argument("--profile", type=Path, default=DEFAULT_GENERATED,
                        help="generated source profile directory")
    parser.add_argument(
        "--out", type=Path,
        default=ROOT / "portable/research/core-proof/original-tick-fixtures.json",
    )
    args = parser.parse_args()
    cycles = [int(item, 0) for item in args.cycles.split(",")]
    generated_dir = args.profile if args.profile.is_absolute() else ROOT / args.profile
    generated_dir = generated_dir.resolve()
    state_ranges = recovered_state_ranges(generated_dir)
    state_provenance = json.loads(
        (generated_dir / "provenance.json").read_text(encoding="utf-8")
    )["recovered_state"]
    generated_profile = generated_dir.relative_to(ROOT).as_posix()
    report = {
        "schema": "original-dos-randworld-doantsim-probe-v1",
        "scope": "original DOS execution and complete non-pointer source-global fixture only; no native comparison",
        "oracle_sha256": behavior.exe.load().sha256,
        "behavior_harness_sha256": hashlib.sha256((TOOLS / "behavior.py").read_bytes()).hexdigest(),
        "recovered_state_header_sha256": state_provenance["header_sha256"],
        "generated_profile": generated_profile,
        "provenance_sha256": hashlib.sha256(
            (generated_dir / "provenance.json").read_bytes()).hexdigest(),
        "captured_recovered_source_global_count": len(state_ranges),
        "captured_recovered_source_global_bytes": sum(item.size for item in state_ranges),
        "excluded_pointer_fields": [
            field["name"] for field in state_provenance["fields"]
            if field["type"] not in STATE_SCALAR_BYTES
        ],
        "seed": args.seed,
        "scenario": args.scenario,
        "cycles": [run_one(args.seed, args.scenario, cycle, generated_dir)
                   for cycle in cycles],
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    try:
        shown_out = args.out.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        shown_out = str(args.out)
    print(f"wrote {shown_out} ({len(cycles)} original-DOS ticks)")
    for row in report["cycles"]:
        print(
            f"cycle={row['cycle_before_tick']} blocks={row['tick_blocks']} "
            f"changed_ranges={len(row['changed_ranges'])} "
            f"post={row['post_tick_sha256']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
