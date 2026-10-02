#!/usr/bin/env python3
"""Capture an original DOS RandWorld followed by 256 uninterrupted DoAntSim ticks."""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import struct
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[3]
TOOLS = ROOT / "tools"
sys.path.insert(0, str(TOOLS))
sys.path.insert(0, str(ROOT / "portable/tests/worldgen"))
import behavior  # noqa: E402
import functions  # noqa: E402
import run_dos_diff  # noqa: E402
from original_tick_probe import TICK_RANGES, recovered_state_ranges
DEFAULT_GENERATED = ROOT / "build/workers/recovered_source/generated"

RAND_STATE_ADDR = behavior.match.DGROUP_SEG * 16 + 0x7BBE


def host_call(event: dict) -> dict | None:
    name = event["name"]
    words = event["stack_words_at_entry"]
    if name in {"MacTickCount", "TickCount"}:
        args = []
    elif name == "ZapEuMapAt":
        args = [value if value < 0x8000 else value - 0x10000 for value in words[2:5]]
    elif name == "SetDefaultWindPrompt":
        value = words[2]
        args = [value if value < 0x8000 else value - 0x10000]
    elif name == "EditMessage":
        pointer = words[2] | (words[3] << 16)
        if pointer != 0:
            return {"name": name, "normalization": "nonnull-message-needs-content-id",
                    "dos_pointer": pointer}
        ticks = words[4] | (words[5] << 16)
        mode = words[6]
        if ticks & 0x80000000:
            ticks -= 0x100000000
        if mode & 0x8000:
            mode -= 0x10000
        args = [0, ticks, mode]
    elif name == "PictStrnDialog":
        args = [value if value < 0x8000 else value - 0x10000
                for value in words[2:5]]
    else:
        return None
    return {"name": name, "args": args}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=lambda value: int(value, 0), required=True)
    parser.add_argument("--scenario", type=lambda value: int(value, 0), required=True)
    parser.add_argument("--ticks", type=int, default=256)
    parser.add_argument("--profile", type=Path, default=DEFAULT_GENERATED,
                        help="generated source profile directory")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--snapshots", type=Path, required=True)
    args = parser.parse_args()
    if args.ticks < 1 or args.ticks > 256:
        raise SystemExit("--ticks must be between 1 and 256")
    generated_dir = args.profile if args.profile.is_absolute() else ROOT / args.profile
    generated_dir = generated_dir.resolve()

    image = behavior.exe.load()
    pair = SimpleNamespace(
        function=functions.get("RandWorld"),
        vectors={behavior.exe.MANAGER_SEG * 16 + vector.offset: vector
                 for vector in image.vectors},
    )
    pair.sequence_function = functions.get

    class FunctionTraceMachine(behavior.Machine):
        def __init__(self, prepared):
            self.function_entries = []
            self.host_entry_stack = []
            self.host_events = []
            self.interrupts = []
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
                if name in {"rand", "RRand", "TickCount", "MacTickCount", "ZapEuMapAt",
                            "SetDefaultWindPrompt", "EditMessage", "PictStrnDialog",
                            "LessonDone"}:
                    ss, sp = self.reg("ss"), self.reg("sp")
                    stack = ss * 16 + sp
                    words = [self.word(stack + offset) for offset in range(0, 16, 2)]
                    event = {
                        "name": name, "stack_words_at_entry": words,
                    }
                    if name == "LessonDone":
                        event["source_values"] = {
                            field: self.read(self.state_by_name[field].address,
                                             self.state_by_name[field].size).hex()
                            for field in (
                                "fd_3D57_07A2", "fd_3D57_07A4", "fd_3D57_07A6",
                                "fd_3D57_07A8", "fd_50F6_0204", "fd_50F6_10B8",
                                "fd_50F6_1074", "fd_50F6_0A00", "fd_50F6_0A02",
                            )
                            if field in self.state_by_name
                        }
                    self.host_entry_stack.append(event)
                    self.host_events.append(event)
            return super()._on_block(cpu, address, size, userdata)

        def _on_interrupt(self, cpu, number, userdata):
            self.interrupts.append({
                "number": number,
                "ax": self.reg("ax"), "bx": self.reg("bx"),
                "cx": self.reg("cx"), "dx": self.reg("dx"),
                "cs": self.reg("cs"), "ip": self.reg("ip"),
                "ss": self.reg("ss"), "sp": self.reg("sp"),
                "flags": self.reg("eflags"),
            })
            return super()._on_interrupt(cpu, number, userdata)

    machine = FunctionTraceMachine(pair)
    initial_case = run_dos_diff.case_for(args.seed, args.scenario)
    state_ranges = recovered_state_ranges(generated_dir)
    state_by_name = {item.name: item for item in state_ranges}
    machine.state_by_name = state_by_name
    observed_names = {item.name for item in initial_case.observe}
    for name, size in TICK_RANGES:
        if name not in observed_names:
            initial_case.observe.append(behavior.Range(
                name, behavior.symbol_address(name), size))
            observed_names.add(name)
    for item in state_ranges:
        if item.name in observed_names:
            initial_case.observe = [
                item if prior.name == item.name else prior
                for prior in initial_case.observe
            ]
        else:
            initial_case.observe.append(item)
            observed_names.add(item.name)

    seed_case = behavior.Case(
        label="startup-seed-random-streams", writes=initial_case.writes,
        observe=initial_case.observe, return_kind="void",
        max_instructions=initial_case.max_instructions,
        max_blocks=initial_case.max_blocks)
    machine.run(seed_case, function="SeedRRand")
    source_tick_count = machine.run(
        behavior.Case(label="read-startup-source-tick", return_kind="u32"),
        preserve=True, function="TickCount")["return"]
    world_case = behavior.Case(
        label=initial_case.label, args=initial_case.args,
        observe=initial_case.observe, return_kind="void",
        max_instructions=initial_case.max_instructions,
        max_blocks=initial_case.max_blocks)
    machine.function_entries.clear()
    generated = machine.run(world_case, preserve=True, function="RandWorld")
    pre_ranges = generated["ranges"]
    world_rand_calls = machine.function_entries.count("rand")
    initial_rng = machine.run(
        behavior.Case(label="get-s-rng-before-tick"),
        preserve=True, function="GetSRandSeed")["return"] & 0xFFFF
    c_rng = struct.unpack("<I", machine.read(RAND_STATE_ADDR, 4))[0]
    initial_c_rng = c_rng

    args.snapshots.parent.mkdir(parents=True, exist_ok=True)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    metadata = []
    state_hashes = []
    with gzip.open(args.snapshots, "wb", compresslevel=9) as snapshot_file:
        for tick_index in range(args.ticks):
            machine.function_entries.clear()
            machine.host_entry_stack.clear()
            machine.host_events.clear()
            callback_events = []
            def pict_dialog_callback(_machine, words):
                args = [value if value < 0x8000 else value - 0x10000
                        for value in words]
                event = {"name": "PictStrnDialog", "callback_args": args}
                callback_events.append(event)
                machine.host_events.append(event)
            try:
                tick = machine.run(behavior.Case(
                    label=f"do-ant-sim-sequence-{tick_index}",
                    observe=initial_case.observe,
                    callbacks={"PictStrnDialog": behavior.Callback(
                        stack_words=3, handler=pict_dialog_callback)},
                    max_instructions=10_000_000,
                    max_blocks=1_000_000), preserve=True, function="DoAntSim")
            except behavior.ExecutionError as error:
                print(f"ORIGINAL_TICK_UNSUPPORTED tick={tick_index} "
                      f"cycle={machine.word(behavior.symbol_address('Cycle'))} "
                      f"error={error} recent_entries={machine.function_entries[-32:]!r} "
                      f"interrupt={machine.interrupts[-1] if machine.interrupts else None!r}")
                return 12
            rand_calls = machine.function_entries.count("rand")
            rand_positions = [index for index, name in enumerate(machine.function_entries)
                              if name == "rand"]
            rand_call_paths = [machine.function_entries[max(0, index - 24):index + 1]
                               for index in rand_positions]
            trace = []
            for event in machine.host_events:
                if "callback_args" in event:
                    trace.append({"name": event["name"], "args": event["callback_args"]})
                else:
                    call = host_call(event)
                    if call is not None:
                        trace.append(call)
            rng_s = machine.run(
                behavior.Case(label="read-s-rng-after-tick"),
                preserve=True, function="GetSRandSeed")["return"] & 0xFFFF
            c_rng = struct.unpack("<I", machine.read(RAND_STATE_ADDR, 4))[0]
            state_blob = b"".join(
                bytes.fromhex(tick["ranges"][item.name]) for item in state_ranges)
            snapshot_file.write(state_blob)
            digest = hashlib.sha256(state_blob).hexdigest()
            state_hashes.append(digest)
            metadata.append({
                "tick": tick_index,
                "cycle_after": int.from_bytes(
                    bytes.fromhex(tick["ranges"]["Cycle"]), "little"),
                "blocks": tick["blocks"],
                "state_sha256": digest,
                "s_rng": rng_s,
                "c_rng": c_rng,
                "rand_calls": rand_calls,
                "rand_call_paths": rand_call_paths,
                "rand_entry_stacks": [event["stack_words_at_entry"]
                                      for event in machine.host_entry_stack
                                      if event["name"] == "rand"],
                "rrand_entry_stacks": [event["stack_words_at_entry"]
                                       for event in machine.host_entry_stack
                                       if event["name"] == "RRand"],
                "lesson_done_entries": [
                    {
                        "stack_words": event["stack_words_at_entry"],
                        "source_values": event.get("source_values", {}),
                    }
                    for event in machine.host_entry_stack
                    if event["name"] == "LessonDone"
                ],
                "host_trace": trace,
            })

    state_bytes = sum(item.size for item in state_ranges)
    report = {
        "schema": "original-dos-consecutive-doantsim-v2",
        "scope": "DOS RandWorld plus uninterrupted actual DoAntSim calls; native comparison performed separately",
        "oracle_sha256": behavior.exe.load().sha256,
        "seed": args.seed,
        "scenario": args.scenario,
        "ticks": args.ticks,
        "recovered_state_header_sha256": json.loads(
            (generated_dir / "provenance.json")
            .read_text(encoding="utf-8"))["recovered_state"]["header_sha256"],
        "generated_profile": generated_dir.relative_to(ROOT).as_posix(),
        "provenance_sha256": hashlib.sha256(
            (generated_dir / "provenance.json").read_bytes()).hexdigest(),
        "source_global_count": len(state_ranges),
        "source_global_bytes": state_bytes,
        "source_globals": [item.name for item in state_ranges],
        "pre_tick_ranges": {name: pre_ranges[name] for name in
                             [item.name for item in state_ranges]},
        "snapshot_file": str(args.snapshots.resolve().relative_to(ROOT)),
        "snapshot_sha256": hashlib.sha256(args.snapshots.read_bytes()).hexdigest(),
        "snapshot_uncompressed_bytes": args.ticks * state_bytes,
        "initial_s_rng": initial_rng,
        "source_tick_count": source_tick_count,
        "initial_c_rng": initial_c_rng,
        "rand_state_observation": {
            "address_linear": RAND_STATE_ADDR,
            "dgroup_segment": behavior.match.DGROUP_SEG,
            "dgroup_offset": 0x7BBE,
            "before_first_tick": initial_c_rng,
            "method": "direct DOS memory read after SeedRRand and RandWorld",
        },
        "world_rand_calls": world_rand_calls,
        "tick_records": metadata,
    }
    args.out.write_text(json.dumps(report, separators=(",", ":")) + "\n",
                        encoding="utf-8")
    print(f"wrote {args.out} ticks={args.ticks} fields={len(state_ranges)} "
          f"bytes/tick={state_bytes} snapshots_sha256={report['snapshot_sha256']}")
    for row in metadata:
        if row["tick"] in {0, 31, 63, 127, 255} or row["tick"] == args.ticks - 1:
            print(f"tick={row['tick']} cycle={row['cycle_after']} "
                  f"state={row['state_sha256']} rng_s={row['s_rng']} "
                  f"rng_c={row['c_rng']} host_calls={len(row['host_trace'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
