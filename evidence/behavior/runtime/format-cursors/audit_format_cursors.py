"""Dynamic audit of the linked 16-bit sprintf cursor cells used by drawHistGraph.

Run from the repository root with:
    python evidence/behavior/runtime/format-cursors/audit_format_cursors.py

This audit reads the hash-locked original image and the behavior-suite scratch
source. It does not modify the image, object, manifest, or promoted sources.
"""
import argparse
import hashlib
import importlib.util
import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path[:0] = [str(ROOT / "tools"), str(ROOT / "tools/behavior_suites")]
import behavior as bootstrap_behavior
import unicorn as uc

# Load the retained execution engine after the workspace dependency bootstrap.
# Its companion compiler/binder modules must still match their archived pins.
PINNED_ROOT = ROOT / "evidence/behavior/harnesses/live-state-v1"
for archived in (PINNED_ROOT / "tools").glob("*.py"):
    if archived.name != "behavior.py":
        current = ROOT / "tools" / archived.name
        if current.read_bytes() != archived.read_bytes():
            raise RuntimeError(f"runtime audit dependency changed: {current}")
if (ROOT / "layout/toolchain.json").read_bytes() != (PINNED_ROOT / "layout/toolchain.json").read_bytes():
    raise RuntimeError("runtime audit toolchain pin changed")
pinned_spec = importlib.util.spec_from_file_location("behavior_audit_pinned", PINNED_ROOT / "tools/behavior.py")
b = importlib.util.module_from_spec(pinned_spec)
sys.modules[pinned_spec.name] = b
pinned_spec.loader.exec_module(b)
b.ROOT = ROOT
sys.modules["behavior"] = b

ARCHIVED_SUITE = Path(__file__).with_name("text_card_suite_snapshot.py")
SOURCE = Path(__file__).with_name("S24.c")
suite_spec = importlib.util.spec_from_file_location("text_card_pinned", ARCHIVED_SUITE)
suite = importlib.util.module_from_spec(suite_spec)
suite_spec.loader.exec_module(suite)
suite.ROOT = ROOT
suite.SOURCE = SOURCE
TARGET = suite.HISTORY_FUNCTION
SPRINTF_RECORD = (0x5E936, 0x5E940)  # DGROUP:8e06..8e0f, private stream record
CASE = suite._history_case("sprintf-scratch-audit", 0, 1, 0, 0, 0,
                           (0, 0, 320, 200), 0x39C70329)


def observe_pair(poison_stale):
    pair = b.PreparedPair(TARGET, source=SOURCE)
    machine = pair.original_machine
    events = []

    def mem_access(cpu, access, address, size, value, userdata):
        if SPRINTF_RECORD[0] <= address < SPRINTF_RECORD[1]:
            events.append({
                "op": "read" if access == uc.UC_MEM_READ else "write",
                "address": f"{address:05x}", "size": size,
                "csip": f"{cpu.reg_read(uc.x86_const.UC_X86_REG_CS):04x}:"
                        f"{cpu.reg_read(uc.x86_const.UC_X86_REG_IP):04x}",
                "sp": f"{cpu.reg_read(uc.x86_const.UC_X86_REG_SP):04x}",
            })

    machine.cpu.hook_add(uc.UC_HOOK_MEM_READ | uc.UC_HOOK_MEM_WRITE,
                         mem_access, None, 0x5E936, 0x5E93F)
    machine.run(CASE)
    first_final = machine.read(0x5E936, 10).hex()
    first_n = len(events)
    machine.trace = []
    machine.raw_trace = []
    machine.io = []
    machine.written = set()
    machine.effect_initial = {}
    machine.blocks = 0
    machine.error = None
    machine.resume = False
    machine.completed = False

    stale_before_second = machine.read(0x5E936, 10).hex()
    if poison_stale:
        # Poison both retained stack pointers and the remaining-count word.
        # The next sprintf call must initialize its own stream before reading it.
        machine.write(0x5E936, struct.pack("<HHHHH", 0xFFFF, 0xFFFF,
                                          0xFFFF, 0xFFFF, 0xFFFF))

    # Same valid draw call at a different caller stack depth. Keep the first
    # invocation's BSS intact (or poisoned) to test the next-entry dataflow.
    sp = 0xA300
    machine.write(machine.reg("ss") * 16 + sp,
                  b.words(b.SENTINEL[1], b.SENTINEL[0], *CASE.args))
    registers = dict(ax=0x1234, bx=0x2345, cx=0x3456, dx=0x4567,
                     si=0x5678, di=0x6789, bp=0x789A, sp=sp,
                     ss=b.match.DGROUP_SEG, ds=b.match.DGROUP_SEG,
                     es=b.match.DGROUP_SEG, eflags=2)
    for name, value in registers.items():
        machine.set_reg(name, value)
    machine.set_reg("cs", pair.function["seg"])
    machine.set_reg("ip", pair.function["off"])
    machine.active = True
    try:
        while True:
            machine.resume = False
            start = machine.reg("cs") * 16 + machine.reg("ip")
            machine.cpu.emu_start(start, b.SENTINEL_LINEAR,
                                  count=CASE.max_instructions)
            if machine.error:
                raise RuntimeError(machine.error)
            if machine.reg("cs") * 16 + machine.reg("ip") == b.SENTINEL_LINEAR:
                machine.completed = True
            if machine.completed:
                break
            if not machine.resume:
                raise RuntimeError("second drawHistGraph invocation did not return")
    finally:
        machine.active = False

    second_events = events[first_n:]
    first_read = next((i for i, ev in enumerate(second_events)
                       if ev["op"] == "read" and ev["address"] == "5e936"), None)
    required_writes = set(range(*SPRINTF_RECORD))
    cursor_writes_before_read = set()
    for ev in second_events[:first_read or 0]:
        if ev["op"] == "write":
            address = int(ev["address"], 16)
            cursor_writes_before_read.update(range(address, address + ev["size"]))
    semantic_trace = [
        {k: v for k, v in item.items() if k != "modified_state_at_entry"}
        for item in machine.trace
    ]
    return {
        "poisoned_stale_values": poison_stale,
        "first_call_final_cells": first_final,
        "before_second_call_cells": stale_before_second,
        "after_second_call_cells": machine.read(0x5E936, 10).hex(),
        "second_call_events": second_events,
        "first_cursor_read_index": first_read,
        "all_cursor_record_bytes_written_before_first_cursor_read":
            required_writes.issubset(cursor_writes_before_read),
        "second_command_trace_sha256": hashlib.sha256(json.dumps(
            semantic_trace, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest(),
        "second_command_count": len(semantic_trace),
        "second_label_draws": machine.state.get("draws", []),
        "second_state_sha256": hashlib.sha256(json.dumps(
            machine.state, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest(),
        "second_renderer_counts": {
            key: len(machine.state.get(key, []))
            for key in ("segments", "color_calls", "draws", "boxes")
        },
    }


def _digest(value):
    raw = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _run_again(machine, case, function, sp):
    """Invoke another function on the already-running VM without resetting BSS."""
    machine.case = case
    machine.trace = []
    machine.raw_trace = []
    machine.io = []
    machine.written = set()
    machine.effect_initial = {}
    machine.blocks = 0
    machine.error = None
    machine.resume = False
    machine.completed = False
    machine.write(machine.reg("ss") * 16 + sp,
                  b.words(b.SENTINEL[1], b.SENTINEL[0], *case.args))
    registers = dict(ax=0x1234, bx=0x2345, cx=0x3456, dx=0x4567,
                     si=0x5678, di=0x6789, bp=0x789A, sp=sp,
                     ss=b.match.DGROUP_SEG, ds=b.match.DGROUP_SEG,
                     es=b.match.DGROUP_SEG, eflags=2)
    for name, value in registers.items():
        machine.set_reg(name, value)
    machine.set_reg("cs", function["seg"])
    machine.set_reg("ip", function["off"])
    machine.active = True
    try:
        while True:
            machine.resume = False
            start = machine.reg("cs") * 16 + machine.reg("ip")
            machine.cpu.emu_start(start, b.SENTINEL_LINEAR,
                                  count=case.max_instructions)
            if machine.error:
                raise RuntimeError(machine.error)
            if machine.reg("cs") * 16 + machine.reg("ip") == b.SENTINEL_LINEAR:
                machine.completed = True
            if machine.completed:
                break
            if not machine.resume:
                raise RuntimeError(f"second {function['name']} invocation did not return")
    finally:
        machine.active = False
    return machine.reg("ax")


def observe_vsprintf(poison_stale):
    """Run exact original _vsprintf twice with stack-resident output buffers."""
    pair = b.PreparedPair(TARGET, source=SOURCE)
    function = dict(b.symbol("_vsprintf"), name="_vsprintf", size=106)
    pair.function = function
    machine = b.Machine(pair, candidate=False)
    record_start, record_end = 0x5E942, 0x5E94C  # DGROUP:8e12..8e1b
    stream_events = []

    def mem_access(cpu, access, address, size, value, userdata):
        if record_start <= address < record_end:
            stream_events.append({
                "op": "read" if access == uc.UC_MEM_READ else "write",
                "address": f"{address:05x}", "size": size,
                "csip": f"{cpu.reg_read(uc.x86_const.UC_X86_REG_CS):04x}:"
                        f"{cpu.reg_read(uc.x86_const.UC_X86_REG_IP):04x}",
                "sp": f"{cpu.reg_read(uc.x86_const.UC_X86_REG_SP):04x}",
            })

    machine.cpu.hook_add(uc.UC_HOOK_MEM_READ | uc.UC_HOOK_MEM_WRITE,
                         mem_access, None, record_start, record_end - 1)
    seg = b.match.DGROUP_SEG
    first_buf, fmt, va = 0xA200, 0x9000, 0x9020
    format_bytes = b"%d\0"
    writes = [
        (seg * 16 + fmt, format_bytes),
        (seg * 16 + va, struct.pack("<h", 123)),
    ]
    first_case = b.Case("vsprintf-stack-buffer", args=[first_buf, seg, fmt, seg, va, seg],
        writes=writes,
        observe=[b.Range("buffer", seg * 16 + first_buf, 16)],
        return_kind="s16", callee_pop=0)
    first_result = machine.run(first_case)
    first_text = machine.read(seg * 16 + first_buf, 16).split(b"\0", 1)[0].decode("ascii")
    first_final = machine.read(record_start, record_end - record_start).hex()
    event_cut = len(stream_events)

    second_buf = 0xA100
    second_case = b.Case("vsprintf-stack-buffer-second-call",
        args=[second_buf, seg, fmt, seg, va, seg],
        observe=[b.Range("buffer", seg * 16 + second_buf, 16)],
        return_kind="s16", callee_pop=0)
    machine.write(seg * 16 + second_buf, b"\0" * 16)
    stale = machine.read(record_start, record_end - record_start).hex()
    if poison_stale:
        # Poison all five far-pointer/count words; _vsprintf must replace them
        # from its own arguments before the formatter reads the stream record.
        machine.write(record_start, struct.pack("<5H", *([0xFFFF] * 5)))
    second_return = _run_again(machine, second_case, function, 0xA300)
    second_text = machine.read(seg * 16 + second_buf, 16).split(b"\0", 1)[0].decode("ascii")
    second_events = stream_events[event_cut:]
    first_cursor_read = next((i for i, ev in enumerate(second_events)
        if ev["op"] == "read" and ev["address"] == "5e942"), None)
    required = set(range(record_start, record_end))
    written = set()
    for event in second_events[:first_cursor_read or 0]:
        if event["op"] == "write":
            address = int(event["address"], 16)
            written.update(range(address, address + event["size"]))
    return {
        "poisoned_stale_values": poison_stale,
        "first_return": first_result["return"], "first_text": first_text,
        "first_final_record": first_final,
        "stale_record_before_second": stale,
        "second_return": second_return, "second_text": second_text,
        "second_final_record": machine.read(record_start, record_end - record_start).hex(),
        "second_events": second_events,
        "first_cursor_read_index": first_cursor_read,
        "all_record_bytes_written_before_first_cursor_read": required.issubset(written),
    }


def main():
    clean = observe_pair(False)
    poisoned = observe_pair(True)
    same_output = (clean["second_command_trace_sha256"] == poisoned["second_command_trace_sha256"]
                   and clean["second_state_sha256"] == poisoned["second_state_sha256"])
    verify = json.loads((ROOT / "build/runtime/verify.json").read_text())
    refs = verify["placements"]["seg:sprintf.c:_BSS:DGROUP"]["0x8e06"]
    vsprintf_refs = verify["placements"]["seg:vsprintf.c:_BSS:DGROUP"]["0x8e12"]
    sprintf_member = next(x for x in verify["results"] if x["member"] == "sprintf.c")
    vsprintf_member = next(x for x in verify["results"] if x["member"] == "vsprintf.c")
    vsprintf_clean = observe_vsprintf(False)
    vsprintf_poisoned = observe_vsprintf(True)
    vsprintf_negative = (vsprintf_clean["second_return"] == vsprintf_poisoned["second_return"]
        and vsprintf_clean["second_text"] == vsprintf_poisoned["second_text"])
    report = {
        "schema": "runtime-format-cursor-audit-v1",
        "target": TARGET,
        "manifest_sha256": hashlib.sha256(
            (ROOT / "layout/manifest.json").read_bytes()).hexdigest(),
        "harness_sha256": hashlib.sha256(b.HARNESS_SOURCE).hexdigest(),
        "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "runtime_member": {
            "library": "llibcr.lib", "name": "sprintf.c",
            "sha256": sprintf_member["member_sha256"],
            "public": "_sprintf", "public_address": sprintf_member["public_addresses"]["_sprintf"],
            "direct_xrefs_to_bss_8e06": refs,
        },
        "vsprintf_runtime_member": {
            "library": "llibcr.lib", "name": "vsprintf.c",
            "sha256": vsprintf_member["member_sha256"],
            "public": "_vsprintf", "public_address": vsprintf_member["public_addresses"]["_vsprintf"],
            "direct_xrefs_to_bss_8e12": vsprintf_refs,
        },
        "cells": {
            "sprintf_DGROUP_8e06_8e0b": "active cursor far pointer at 8e06/08 and remaining count at 8e0a",
            "sprintf_DGROUP_8e0c_8e0f": "saved output-buffer base far pointer",
            "vsprintf_DGROUP_8e12_8e17": "active cursor far pointer at 8e12/14 and remaining count at 8e16",
            "vsprintf_DGROUP_8e18_8e1b": "saved output-buffer base far pointer",
            "adjacent_signature_bytes": {"8e10": "sprintf helper marker", "8e1c": "vsprintf helper marker"},
        },
        "dataflow_evidence": {
            "sprintf": [
                {"pc": "29F4:1E81", "effect": "store caller output-buffer offset at DGROUP:8e0c"},
                {"pc": "29F4:1E84", "effect": "store caller output-buffer segment at DGROUP:8e0e"},
                {"pc": "29F4:1E8B", "effect": "define active cursor offset at DGROUP:8e06"},
                {"pc": "29F4:1E8D", "effect": "define active cursor segment at DGROUP:8e08"},
                {"pc": "29F4:1E90", "effect": "initialize remaining capacity at DGROUP:8e0a"},
                {"pc": "29F4:1EA5", "effect": "call formatter with pointer to DGROUP:8e06 stream record"},
                {"pc": "29F4:13A1-13B4", "effect": "shared output helper reads record cursor/count, advances cursor, emits byte"},
                {"pc": "29F4:1EB5-1EB9", "effect": "read and advance final cursor before terminator store"},
            ],
            "vsprintf": [
                {"pc": "29F4:1EEA", "effect": "store caller output-buffer offset at DGROUP:8e18"},
                {"pc": "29F4:1EED", "effect": "store caller output-buffer segment at DGROUP:8e1a"},
                {"pc": "29F4:1EF4", "effect": "define active cursor offset at DGROUP:8e12"},
                {"pc": "29F4:1EF6", "effect": "define active cursor segment at DGROUP:8e14"},
                {"pc": "29F4:1EF9", "effect": "initialize remaining capacity at DGROUP:8e16"},
                {"pc": "29F4:1F0F", "effect": "call formatter with pointer to DGROUP:8e12 stream record"},
                {"pc": "29F4:13A1-13B4", "effect": "shared output helper reads record cursor/count, advances cursor, emits byte"},
                {"pc": "29F4:1F19-1F27", "effect": "read and advance final cursor before terminator store"},
            ],
            "cross_reference_basis": "build/runtime/verify.json placements map DGROUP:8e06 only to sprintf.c sites and DGROUP:8e12 only to vsprintf.c sites; both full site lists are preserved with the exact runtime member identities above.",
            "read_before_definition": "No stale record is consumed on a new invocation: the dynamic memory access stream shows all ten record bytes written by the member prologue before the first active-cursor read by the shared output helper.",
        },
        "dynamic_proof": {
            "first_call_leaves_stack_pointers": clean["first_call_final_cells"],
            "next_call_uses_different_stack_depth": True,
            "next_call_initializes_cursor_record_before_read":
                clean["all_cursor_record_bytes_written_before_first_cursor_read"],
            "old_pointer_poison_negative_control_preserves_second_output": same_output,
            "clean_second_call_cells_initialized_before_read": clean,
            "poisoned_second_call_cells_initialized_before_read": poisoned,
        },
        "vsprintf_dynamic_proof": {
            "clean": vsprintf_clean,
            "stale_pointer_poison_negative_control": vsprintf_poisoned,
            "old_pointer_poison_preserves_return_and_text": vsprintf_negative,
            "negative_control_passed": (
                vsprintf_negative
                and vsprintf_clean["all_record_bytes_written_before_first_cursor_read"]
                and vsprintf_poisoned["all_record_bytes_written_before_first_cursor_read"]
                and vsprintf_clean["first_text"] == vsprintf_clean["second_text"] == "123"
            ),
        },
        "retained_raw_mismatch": {
            "run_report": "build/workers/behavior_text_card/text/draw-history/run-a5dfe315124b-ee7c997d2f89/report.json",
            "ledger": "build/workers/behavior_text_card/text/draw-history/run-a5dfe315124b-ee7c997d2f89/cases-directed.jsonl.gz",
            "ledger_sha256": "06154bfa703ec0ad8d1e81b42cbda9f1aa1090056fbf384c0ad2725e3fe88115",
            "case": "grid/0/1/0/0",
            "raw_nonstack_memory_differences": [
                {"linear": "0x5e936", "dgroup": "55b3:8e06", "oracle": "0xc7", "candidate": "0xbb"},
                {"linear": "0x5e93c", "dgroup": "55b3:8e0c", "oracle": "0xc4", "candidate": "0xb8"},
            ],
            "handling": "Preserved as observed in the original per-case ledger; no address or byte is filtered or rewritten by this audit.",
        },
        "limitations": [
            "The dynamic sprintf run covers drawHistGraph's highlighted-label path and a sequential repeat at a different stack depth.",
            "The dynamic vsprintf run invokes the original CRT member directly with a stack-resident output buffer and repeats at a second stack depth.",
            "Runtime verify.json attributes direct BSS cross-references to each exact CRT member; indirect readers use the cursor record passed to the shared output helper.",
            "The raw differential ledger still records the two stack-pointer bytes as mismatches; this audit does not normalize or mask them.",
        ],
        "corroborating_tutorial_observation": {
            "report": "build/workers/behavior_tutorial_menu/raw_original_formatter/report.json",
            "ledger": "build/workers/behavior_tutorial_menu/raw_original_formatter/o10_35F5_0384.jsonl.gz",
            "ledger_sha256": "3f96047be1b78bf694dabbbef27ab7f060a705a22f1aeb012d292813db741d71",
            "harness_sha256": "ee7c997d2f89efa85ce932cd5ac7c674c465f1013a16a8c08e83d43c69f4be5b",
            "suite_sha256": "d8259f2e53e961f36e5f41c20fae7992afa6f8a6cf64f6452bd3b9582d29ca9e",
            "manifest_sha256": "025a0a9255d910cae4b122ab5a3f3fb40888bb456d7fe42158db7c9e622fcf50",
            "case": "random/35f50384/5",
            "raw_final_writes": {
                "DGROUP:8e12": {"oracle": "0x62", "candidate": "0x60"},
                "DGROUP:8e18": {"oracle": "0x5a", "candidate": "0x58"},
            },
            "scope": "Independent target-use corroboration only; its mismatch is retained and this suite does not repair or hide it.",
        },
    }
    report["dynamic_proof"]["negative_control_passed"] = (
        same_output and clean["all_cursor_record_bytes_written_before_first_cursor_read"]
        and poisoned["all_cursor_record_bytes_written_before_first_cursor_read"])
    report["all_negative_controls_passed"] = (
        report["dynamic_proof"]["negative_control_passed"]
        and report["vsprintf_dynamic_proof"]["negative_control_passed"])
    view_records = [
        {"name": "sprintf-output-stream", "address": 0x5E936, "size": 10,
         "private_owner": "llibcr.lib:sprintf.c:_BSS:DGROUP:8e06",
         "overwrite_before_read_proven": report["dynamic_proof"]["negative_control_passed"],
         "semantic_fields": ["cursor-minus-base advancement", "remaining capacity"]},
        {"name": "vsprintf-output-stream", "address": 0x5E942, "size": 10,
         "private_owner": "llibcr.lib:vsprintf.c:_BSS:DGROUP:8e12",
         "overwrite_before_read_proven": report["vsprintf_dynamic_proof"]["negative_control_passed"],
         "semantic_fields": ["cursor-minus-base advancement", "remaining capacity"]},
    ]
    digest_material = {
        "oracle_sha256": b.exe.load().sha256,
        "runtime_members": [report["runtime_member"], report["vsprintf_runtime_member"]],
        "records": view_records,
        "sprintf_negative_control": report["dynamic_proof"]["negative_control_passed"],
        "vsprintf_negative_control": report["vsprintf_dynamic_proof"]["negative_control_passed"],
        "raw_diffs_preserved": report["retained_raw_mismatch"]["raw_nonstack_memory_differences"],
    }
    report["typed_view_proposal"] = {
        "schema": "behavior-format-cursor-proof-v1",
        "review_status": "REVIEW_REQUIRED",
        "oracle_sha256": b.exe.load().sha256,
        "records": view_records,
        "proof_digest": _digest(digest_material),
        "raw_differences_policy": "All original/candidate bytes remain in their case ledgers; a typed view may compare only normalized cursor-base advance and remaining capacity.",
    }
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "build/workers/behavior_reviews/format-cursor-audit-replay.json")
    out = parser.parse_args().output.resolve()
    out.relative_to(ROOT / "build")
    if out.exists():
        raise RuntimeError("audit replay output already exists; use a fresh build path")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + "\n")
    proof = report["dynamic_proof"]
    print(json.dumps({
        "target": report["target"],
        "manifest_sha256": report["manifest_sha256"],
        "harness_sha256": report["harness_sha256"],
        "runtime_member": report["runtime_member"],
        "dynamic_summary": {
            "first_call_leaves_stack_pointers": proof["first_call_leaves_stack_pointers"],
            "clean_first_cursor_read_index": proof["clean_second_call_cells_initialized_before_read"]["first_cursor_read_index"],
            "poisoned_first_cursor_read_index": proof["poisoned_second_call_cells_initialized_before_read"]["first_cursor_read_index"],
            "clean_initialized_before_read": proof["clean_second_call_cells_initialized_before_read"]["all_cursor_record_bytes_written_before_first_cursor_read"],
            "poisoned_initialized_before_read": proof["poisoned_second_call_cells_initialized_before_read"]["all_cursor_record_bytes_written_before_first_cursor_read"],
            "old_pointer_poison_preserves_semantic_output": proof["old_pointer_poison_negative_control_preserves_second_output"],
            "negative_control_passed": proof["negative_control_passed"],
        },
        "vsprintf_summary": {
            "member_sha256": vsprintf_member["member_sha256"],
            "first_text": vsprintf_clean["first_text"],
            "second_text": vsprintf_clean["second_text"],
            "clean_cursor_read_index": vsprintf_clean["first_cursor_read_index"],
            "poisoned_cursor_read_index": vsprintf_poisoned["first_cursor_read_index"],
            "clean_initialized_before_read": vsprintf_clean["all_record_bytes_written_before_first_cursor_read"],
            "poisoned_initialized_before_read": vsprintf_poisoned["all_record_bytes_written_before_first_cursor_read"],
            "old_pointer_poison_preserves_return_and_text": vsprintf_negative,
            "negative_control_passed": report["vsprintf_dynamic_proof"]["negative_control_passed"],
        },
        "limitations": report["limitations"],
    }, indent=2))
    if not report["all_negative_controls_passed"]:
        raise SystemExit("runtime format cursor proof failed")


if __name__ == "__main__":
    main()
