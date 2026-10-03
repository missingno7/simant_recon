"""Re-run compiler-expression, allocator-entry, and queue-alias probes.

Every generated C file and OMF object is written below the caller's fresh
scratch directory. The original EXE is used only by PreparedPair as the
separate research oracle; it is never a source-only build input.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import struct
import sys
from pathlib import Path

FLAGS = ["/AL", "/Os", "/Oe", "/Og", "/Zi"]
EXPRESSION_FLAGS = [*FLAGS, "/Gs"]
CODE_SEG, STACK_SEG, STACK_TOP = 0x9000, 0x8000, 0xA000
RETURN_SEG, RETURN_OFF = 0xF000, 0x8000
RETURN_LINEAR = RETURN_SEG * 16 + RETURN_OFF


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_suite(path: Path):
    spec = importlib.util.spec_from_file_location("drawballoons_probe_suite", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load staged suite: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def expression_probe(repo: Path, dest: Path) -> dict:
    sys.path.insert(0, str(repo / "tools"))
    import behavior
    import compiler
    import omf
    from unicorn import x86_const as xr

    import_dir = dest / "expression"
    import_dir.mkdir(parents=True, exist_ok=False)
    fixed_source = import_dir / "signed.c"
    unsigned_source = import_dir / "unsigned.c"
    fixed_source.write_text(
        "long far probe(unsigned n) { return (long)(int)(n + 4); }\n",
        encoding="ascii")
    unsigned_source.write_text(
        "long far probe(unsigned n) { return (long)(n + 4); }\n",
        encoding="ascii")

    def compile_and_run(path: Path, tag: str) -> dict:
        result = compiler.compile_c(path.read_text(encoding="ascii"),
                                    "msc600ax", EXPRESSION_FLAGS,
                                    basename="UNIT", keep=True)
        if not result.ok or result.obj is None:
            raise RuntimeError(f"pinned compiler failed for {tag}: {result.log}")
        obj_path = import_dir / f"{tag}.obj"
        obj_path.write_bytes(result.obj)
        obj = omf.OmfReader().read(result.obj)
        entry = next(p for p in obj.publics if p["name"].lstrip("_@") == "probe")
        later = [p["offset"] for p in obj.publics
                 if p["segment"] == entry["segment"] and p["offset"] > entry["offset"]]
        end = min(later) if later else len(obj.segments[entry["segment"]])
        code = bytes(obj.segments[entry["segment"]][entry["offset"]:end])
        fixups = [f for f in obj.fixups if f["segment"] == entry["segment"]
                  and entry["offset"] <= f["offset"] < end]
        if fixups:
            raise RuntimeError(f"unexpected probe code dependency: {fixups}")

        outcomes = []
        for value in (0x7FFC, 0x7FF8):
            cpu = behavior.uc.Uc(behavior.uc.UC_ARCH_X86, behavior.uc.UC_MODE_16)
            cpu.mem_map(0, 0x110000)
            cpu.mem_write(CODE_SEG * 16 + entry["offset"], code)
            sp = STACK_TOP
            cpu.mem_write(STACK_SEG * 16 + sp,
                          struct.pack("<HHH", RETURN_OFF, RETURN_SEG, value))
            for name, reg in (("cs", xr.UC_X86_REG_CS), ("ip", xr.UC_X86_REG_IP),
                              ("ss", xr.UC_X86_REG_SS), ("sp", xr.UC_X86_REG_SP),
                              ("ds", xr.UC_X86_REG_DS), ("es", xr.UC_X86_REG_ES)):
                cpu.reg_write(reg, {"cs": CODE_SEG, "ip": entry["offset"],
                                    "ss": STACK_SEG, "sp": sp,
                                    "ds": 0x55B3, "es": 0}[name])
            returned = {}

            def at_return(uc, address, size, userdata):
                if address == RETURN_LINEAR:
                    returned["ax"] = uc.reg_read(xr.UC_X86_REG_AX)
                    returned["dx"] = uc.reg_read(xr.UC_X86_REG_DX)
                    uc.emu_stop()

            hook = cpu.hook_add(behavior.uc.UC_HOOK_CODE, at_return,
                                begin=RETURN_LINEAR, end=RETURN_LINEAR)
            cpu.emu_start(CODE_SEG * 16 + entry["offset"], 0x110000, count=1000)
            cpu.hook_del(hook)
            if not returned:
                raise RuntimeError(f"{tag} probe did not return for n={value:04x}")
            raw = (returned["dx"] << 16) | returned["ax"]
            outcomes.append({
                "input_n": value, "sum_low16": (value + 4) & 0xFFFF,
                "dx_ax_hex": f"{returned['dx']:04x}:{returned['ax']:04x}",
                "argument_u32": raw,
                "argument_s32": raw - 0x100000000 if raw & 0x80000000 else raw,
            })
        return {"source_sha256": digest(path.read_bytes()),
                "object_sha256": digest(result.obj), "object_path": str(obj_path),
                "entry_offset": entry["offset"], "function_bytes": end - entry["offset"],
                "outcomes": outcomes}

    fixed = compile_and_run(fixed_source, "signed")
    unsigned = compile_and_run(unsigned_source, "unsigned")
    verified = (
        fixed["outcomes"][0]["dx_ax_hex"] == "ffff:8000"
        and unsigned["outcomes"][0]["dx_ax_hex"] == "0000:8000"
        and fixed["outcomes"][1]["dx_ax_hex"] == "0000:7ffc"
        and unsigned["outcomes"][1]["dx_ax_hex"] == "0000:7ffc")
    if not verified:
        raise AssertionError("standalone expression edge controls did not match expected DX:AX")
    return {"status": "PASS", "profile": "msc600ax", "flags": EXPRESSION_FLAGS,
            "compiler_inputs": [{"path": "layout/toolchain.json",
                                 "sha256": digest((repo / "layout/toolchain.json").read_bytes())}],
            "signed": fixed, "unsigned_negative_control": unsigned,
            "verified": verified}


def allocator_entry(pair, case, behavior) -> list[dict]:
    seen = []
    case.callbacks["f_171C_1A9E"] = behavior.Callback(5)
    target = behavior.symbol_address("f_171C_1A9E")
    for side, machine in (("original", pair.original_machine),
                          ("candidate", pair.candidate_machine)):
        def at_entry(cpu, address, size, userdata):
            if address != target:
                return
            stack = machine.reg("ss") * 16 + machine.reg("sp") + 4
            low, high, flags, name_off, name_seg = struct.unpack(
                "<5H", machine.read(stack, 10))
            raw = (high << 16) | low
            signed = raw - 0x100000000 if raw & 0x80000000 else raw
            seen.append({"side": side, "raw_stack_words": [low, high],
                         "argument_u32": raw, "argument_s32": signed,
                         "flags": flags, "name_far": [name_off, name_seg],
                         "service_executed": False,
                         "entry": f"{machine.reg('cs'):04X}:{machine.reg('ip'):04X}"})
            machine.error = "research stop before allocator service body"
            cpu.emu_stop()

        hook = machine.cpu.hook_add(behavior.uc.UC_HOOK_CODE, at_entry,
                                    begin=target, end=target)
        try:
            machine.run(case)
        except behavior.ExecutionError as exc:
            if "research stop before allocator service body" not in str(exc):
                raise
        else:
            raise RuntimeError(f"{side} ran beyond allocator entry")
        finally:
            machine.cpu.hook_del(hook)
    if len(seen) != 2 or {row["side"] for row in seen} != {"original", "candidate"}:
        raise RuntimeError(f"allocator-entry capture incomplete: {seen}")
    return seen


def make_width_case(suite, behavior, label: str, mode: int,
                    picture_width: int, visible_index: int = 0):
    case = suite._balloon_case(label, mode=mode, plane=0, x=76, y=85,
                               picw=8, pich=1)
    resource_at = (suite.memory_suite.HEAP_SEG + 2) * 16
    for i, (address, data) in enumerate(case.writes):
        if address == resource_at:
            header = struct.pack("<hB5sHH", 0, 0, b"\0" * 5,
                                 picture_width, 1)
            case.writes[i] = (address, header + data[12:])
            break
    else:
        raise RuntimeError("could not find fixture picture header")
    if visible_index:
        case.writes.extend([
            (behavior.symbol_address("fd_50F6_1092"), suite._w(visible_index + 1)),
            (behavior.symbol_address("fd_50F6_04C8"), b"".join(
                suite._w(x) + suite._w(y) for x, y in
                [*((640, 480) for _ in range(visible_index)), (76, 85)])),
            (behavior.symbol_address("fd_50F6_04F6"), suite._w(0) * (visible_index + 1)),
            (behavior.symbol_address("fd_50F6_04E6"), suite._w(0) * (visible_index + 1)),
            (behavior.symbol_address("fd_50F6_04A6"),
             struct.pack("<HH", *suite.BALLOON_TEXT) * (visible_index + 1)),
        ])
    return case


def compact_observation(result) -> dict:
    import behavior

    packed = json.dumps(result, sort_keys=True, default=lambda value:
                        value.hex() if isinstance(value, bytes) else repr(value),
                        separators=(",", ":")).encode("utf-8")
    state_names = ("buffer_size", "buffer_linear", "resource_requests",
                   "resource_releases", "tile_render_requests",
                   "tile_pixel_transfers", "message_blits", "format_commands",
                   "tile_resource_acquisitions", "tile_resource_releases",
                   "window_clip_setups", "selected_font")
    return {
        "return": result["return"],
        "preserved_registers": result["preserved_registers"],
        "event_arguments": [{"name": event["name"], "args": event["args"]}
                            for event in result["trace"]],
        "state": {name: result["state"].get(name) for name in state_names},
        "observed_range_sha256": {
            name: digest(bytes.fromhex(value))
            for name, value in result["ranges"].items()},
        "full_execution_result_sha256": digest(packed),
    }


def full_probes(repo: Path, scratch: Path, source_path: Path,
                suite_path: Path) -> dict:
    sys.path.insert(0, str(repo / "tools"))
    import behavior
    import compiler

    suite = load_suite(suite_path)
    probe_root = scratch / "probes"
    probe_root.mkdir(parents=True, exist_ok=False)

    expression = expression_probe(repo, probe_root)

    # Generate the unsigned control only in scratch from the admitted module;
    # never consume a prior worker's source or object.
    negative_source = probe_root / "negative_unsigned.c"
    corrected_text = source_path.read_text(encoding="latin1")
    anchor = "(long)(int)(n + 4)"
    if corrected_text.count(anchor) != 1:
        raise RuntimeError("admitted source does not have one signed conversion anchor")
    negative_source.write_text(corrected_text.replace(anchor, "(long)(n + 4)", 1),
                               encoding="latin1")

    # Standalone allocation expression boundary: n=0x7ffc produces the
    # high-bit sum 0x8000; n=0x7ff8 is the positive-side control.
    corrected = behavior.PreparedPair("DrawBalloons", source=source_path,
                                      out=probe_root / "width" / "corrected")
    unsigned = behavior.PreparedPair("DrawBalloons", source=negative_source,
                                     out=probe_root / "width" / "unsigned")
    width_cases = []
    for label, mode, width, expected_sum in (
            ("index-0-sum-7ffc", 2, 7280, 0x7FFC),
            ("index-0-sum-8004", 1, 4096, 0x8004),
            ("index-4-sum-7ffc", 2, 7280, 0x7FFC),
            ("index-4-sum-8004", 1, 4096, 0x8004)):
        index = 4 if label.startswith("index-4") else 0
        good = allocator_entry(corrected,
            make_width_case(suite, behavior, label, mode, width, index), behavior)
        bad = allocator_entry(unsigned,
            make_width_case(suite, behavior, label, mode, width, index), behavior)
        good_sides = {row["side"]: row for row in good}
        bad_sides = {row["side"]: row for row in bad}
        if good_sides["original"]["argument_u32"] != good_sides["candidate"]["argument_u32"]:
            raise AssertionError(f"fixed source differs at {label}: {good}")
        if good_sides["original"]["argument_u32"] & 0xFFFF != expected_sum:
            raise AssertionError(f"wrong low word at {label}: {good}")
        negative_detected = (bad_sides["original"]["argument_u32"] !=
                             bad_sides["candidate"]["argument_u32"])
        if negative_detected != (expected_sum == 0x8004):
            raise AssertionError(f"unsigned control result unexpected at {label}: {bad}")
        width_cases.append({
            "case": label, "queue_count": index + 1,
            "invisible_prefix": index, "mode": mode,
            "picture_width": width, "expected_sum_low16": expected_sum,
            "fixed_original_and_candidate": good,
            "unsigned_negative_control_original_and_candidate": bad,
            "unsigned_negative_detected": negative_detected,
        })

    # Six legal queue slots, with a visible record following the exact number
    # of invisible off-screen records needed to reach that index.
    alias_pair = behavior.PreparedPair("DrawBalloons", source=source_path,
                                       out=probe_root / "queue-alias" / "candidate")
    alias_cases = []
    for visible_index in range(6):
        case = suite._balloon_case(
            f"queue-alias/invisible-prefix-{visible_index}",
            mode=1, plane=0, x=80, y=80, picw=8, pich=8)
        entries = [*((640, 480) for _ in range(visible_index)), (80, 80)]
        case.writes.extend([
            (behavior.symbol_address("fd_50F6_1092"), suite._w(visible_index + 1)),
            (behavior.symbol_address("fd_50F6_04C8"), b"".join(
                suite._w(x) + suite._w(y) for x, y in entries)),
            (behavior.symbol_address("fd_50F6_04F6"), suite._w(0) * (visible_index + 1)),
            (behavior.symbol_address("fd_50F6_04E6"), suite._w(0) * (visible_index + 1)),
            (behavior.symbol_address("fd_50F6_04A6"),
             struct.pack("<HH", *suite.BALLOON_TEXT) * (visible_index + 1)),
        ])
        compared = alias_pair.compare(case)
        if not compared.equal:
            raise AssertionError(f"queue-alias comparison failed at index {visible_index}: {compared.diff}")
        alias_cases.append({
            "label": case.label, "queue_count": visible_index + 1,
            "invisible_prefix": visible_index, "visible_index": visible_index,
            "equal": compared.equal, "diff": compared.diff,
            "original": compact_observation(compared.original),
            "candidate": compact_observation(compared.candidate),
        })

    return {
        "status": "PASS",
        "compiler": {"profile": "msc600ax", "flags": FLAGS,
                     "manifest_sha256": corrected.identity["manifest_sha256"]},
        "expression_boundary": expression,
        "full_function_width_boundary": {
            "corrected_identity": corrected.identity,
            "unsigned_negative_control_identity": unsigned.identity,
            "capture_method": "The original and compiled whole-function candidate run to the real f_171C_1A9E entry; the hook reads argument stack words and stops before the service body.",
            "cases": width_cases,
        },
        "queue_alias": {
            "candidate_identity": alias_pair.identity,
            "domain": "six slots, i=0..5; i invisible off-screen entries then one visible entry at i",
            "all_equal": all(row["equal"] for row in alias_cases),
            "cases": alias_cases,
        },
        "negative_source_sha256": digest(negative_source.read_bytes()),
    }
