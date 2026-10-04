#!/usr/bin/env python3
"""Root-pending static probe of the SIMANT common-tail / MSC startup BSS boundary.

This script reads the immutable executable only to decode its historical loader,
bound runtime operands, and file-to-load mapping. It does not copy executable bytes
to a file, compile from them, patch anything, or produce a source provider.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "tools"))
import exe as exemod  # noqa: E402
from omf import OmfReader  # noqa: E402

LIBRARY = Path("C:/tools/msc-6.00/LIB/llibcr.lib")
STARTUP = Path("C:/tools/msc-6.00/STARTUP")
NDISASM = Path("C:/msys64/usr/bin/ndisasm.exe")
DGROUP_SEG = 0x55B3
DGROUP_LINEAR = DGROUP_SEG * 16
EXPECTED_CRT0_MEMBER_SHA = "2e9a254b9bd00ea59884089e78e951f0e40343e11d24976f32d9582f4ded259d"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def json_safe(value):
    if isinstance(value, bytes):
        return {"bytes_hex": value.hex()}
    if isinstance(value, dict):
        return {str(k): json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(v) for v in value]
    return value


def pin(path: Path, label: str | None = None) -> dict:
    blob = path.read_bytes()
    try:
        name = path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        name = path.as_posix()
    return {"path": name, "label": label, "size": len(blob), "sha256": sha(blob)}


def source_excerpt(path: Path, ranges: list[tuple[int, int]]) -> list[dict]:
    lines = path.read_text(encoding="latin1").splitlines()
    out = []
    for first, last in ranges:
        out.append({"first_line": first, "last_line": last,
                    "text": "\n".join(f"{n}: {lines[n - 1]}" for n in range(first, last + 1))})
    return out


def decode_obj(obj) -> dict:
    return {
        "module_name": obj.name,
        "segment_lengths": obj.segment_lengths,
        "segment_payloads_hex": {k: bytes(v).hex() for k, v in sorted(obj.segments.items())},
        "segment_defs": obj.segment_defs,
        "groups": obj.groups,
        "publics": obj.publics,
        "externals": obj.externals,
        "external_scopes": obj.external_scopes,
        "local_externals": obj.local_externals,
        "local_publics": obj.local_publics,
        "communals": obj.communals,
        "comments": obj.comments,
        "linker_fixups_in_record_order": obj.linker_fixups,
    }


def library_objects(rd: OmfReader) -> list[tuple[int, str, bytes, object]]:
    out = []
    for index, (name, blob) in enumerate(rd.split_library(LIBRARY.read_bytes())):
        if name.lower() in {"dos\\crt0.asm", "dos\\crt0msg.asm", "dos\\nmsghdr.asm"}:
            out.append((index, name, blob, rd.read(blob, name)))
    return out


def disassemble(blob: bytes, origin: int) -> str:
    result = subprocess.run(
        [str(NDISASM), "-b", "16", "-o", f"0x{origin:x}", "-"],
        input=blob, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )
    if result.returncode:
        raise SystemExit(f"ndisasm failed ({result.returncode}): "
                         f"{result.stderr.decode('latin1', errors='replace')}")
    return result.stdout.decode("latin1")


def signed16(value: int) -> int:
    return value - 0x10000 if value & 0x8000 else value


def main() -> int:
    manifest_path = ROOT / "layout/manifest.json"
    symbols_path = ROOT / "layout/symbols.json"
    build_report_path = ROOT / "build/source-only-dos/build-report.json"
    oracle_lock_path = ROOT / "layout/oracle.lock.json"
    toolchain_path = ROOT / "layout/toolchain.json"
    runtime_location_path = ROOT / "evidence/toolchain/runtime-location.json"
    crt0_source = STARTUP / "dos/crt0.asm"
    crt0msg_source = STARTUP / "dos/crt0msg.asm"
    nmsghdr_source = STARTUP / "dos/nmsghdr.asm"
    source_inc_paths = [STARTUP / "cmacros.inc", STARTUP / "version.inc",
                        STARTUP / "rterr.inc", STARTUP / "msdos.inc"]

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    symbols = json.loads(symbols_path.read_text(encoding="utf-8"))
    build_report = json.loads(build_report_path.read_text(encoding="utf-8"))
    oracle_lock = json.loads(oracle_lock_path.read_text(encoding="utf-8"))
    runtime_location = json.loads(runtime_location_path.read_text(encoding="utf-8"))

    exe = exemod.load(verify=True)
    original_pin = oracle_lock["inputs"]["SIMANT.EXE"]
    assert exe.sha256 == original_pin["sha256"] == exemod.EXPECTED_SHA256
    assert len(exe.raw) == original_pin["size"]

    rd = OmfReader(communals=True)
    libmods = library_objects(rd)
    module_by_name = {name.lower(): (index, name, blob, obj)
                      for index, name, blob, obj in libmods}
    assert set(module_by_name) == {"dos\\crt0.asm", "dos\\crt0msg.asm", "dos\\nmsghdr.asm"}
    crt_idx, crt_name, crt_blob, crt_obj = module_by_name["dos\\crt0.asm"]
    assert crt_idx == 0 and sha(crt_blob) == EXPECTED_CRT0_MEMBER_SHA
    assert crt_obj.segment_length("_TEXT") == 255

    runtime_rows = {r["member"].lower(): r for r in manifest["runtime"]["members"]}
    location_rows = {r["member"].lower(): r for r in runtime_location["members"]}
    crt_row = runtime_rows["dos\\crt0.asm"]
    crt_location = location_rows["dos\\crt0.asm"]
    assert crt_row["library"] == "llibcr.lib" and crt_row["module_index"] == crt_idx
    assert crt_row["member_sha256"] == sha(crt_blob)
    assert crt_row["linear"] == crt_location["linear"] == 171868
    assert crt_row["size"] == crt_location["size"] == 255
    assert crt_row["segment"] == "_TEXT"

    crt_runtime = exe.read("root", crt_row["linear"], crt_row["size"])
    obj_text = bytes(crt_obj.segments["_TEXT"])
    code_mask = bytearray(len(obj_text))
    for fix in crt_obj.linker_fixups:
        if fix["segment"] != "_TEXT":
            continue
        for n in range(fix["offset"], fix["offset"] + fix["width"]):
            if n < len(code_mask):
                code_mask[n] = 1
    nonfixup_equal = all(code_mask[i] or obj_text[i] == crt_runtime[i]
                         for i in range(len(obj_text)))
    assert nonfixup_equal

    ext_sites = []
    for fix in crt_obj.linker_fixups:
        if fix["segment"] == "_TEXT" and fix.get("target_kind") == "external" \
                and fix.get("target") in {"_edata", "_end"}:
            site = crt_row["linear"] + fix["offset"]
            operand = int.from_bytes(exe.read("root", site, fix["width"]), "little")
            displacement = signed16(int(fix.get("displacement", 0)) & 0xFFFF)
            symbol_value = (operand - displacement) & 0xFFFF
            ext_sites.append({
                "symbol": fix["target"], "object_offset": fix["offset"],
                "root_load_linear": site,
                "root_segment_offset": f"29F4:{(0x1C + fix['offset']):04X}",
                "fixup": fix,
                "original_loaded_operand": f"{operand:04X}",
                "encoded_addend_signed": displacement,
                "resolved_DGROUP_offset": f"{symbol_value:04X}",
            })
    edata_refs = [r for r in ext_sites if r["symbol"] == "_edata"]
    end_refs = [r for r in ext_sites if r["symbol"] == "_end"]
    assert len(edata_refs) == 1 and edata_refs[0]["resolved_DGROUP_offset"] == "8B9E"
    assert len(end_refs) == 2 and {r["resolved_DGROUP_offset"] for r in end_refs} == {"94F0"}
    assert {r["original_loaded_operand"] for r in end_refs} == {"94EE", "94F0"}
    for row in ext_sites:
        assert row["fixup"]["frame_kind"] == "group"
        assert row["fixup"]["frame"] == "DGROUP"
        assert row["fixup"]["loc"] == "offset16"

    manager_start = exe.mz.cs * 16 + exe.mz.ip
    assert (exe.mz.cs, exe.mz.ip) == (0x2CFF, 0x06F8)
    manager_code = exe.read("root", manager_start, 0x44)
    manager_disasm = disassemble(manager_code, 0x06F8)
    assert "jmp 0x29f4:0x1c" in manager_disasm.lower()
    crt_disasm = disassemble(crt_runtime, 0x001C)
    required = ["mov ss,di", "pop es", "cld", "mov di,0x8b9e", "mov cx,0x94f0",
                "sub cx,di", "xor ax,ax", "rep stosb", "call cx",
                "call 0x29f4:0x4c2", "call 0x29f4:0x314",
                "call 0x29f4:0x11c", "call 0x15f8:0x4"]
    lower_disasm = crt_disasm.lower()
    for s in required:
        assert s in lower_disasm, f"missing expected startup instruction: {s}"
    assert "jnc 0x29" in lower_disasm and "jnc 0x57" in lower_disasm
    assert lower_disasm.index("rep stosb") < lower_disasm.index("call cx")
    assert lower_disasm.index("rep stosb") < lower_disasm.index("call 0x29f4:0x4c2")
    assert lower_disasm.index("rep stosb") < lower_disasm.index("call 0x29f4:0x314")
    assert lower_disasm.index("rep stosb") < lower_disasm.index("call 0x29f4:0x11c")
    assert lower_disasm.index("rep stosb") < lower_disasm.index("call 0x15f8:0x4")

    sec = exe.sections[27]
    sec_end_file = sec.data_file_offset + len(sec.data)
    sec_end_linear = sec.load_linear + len(sec.data)
    tail_size = 256
    tail_start_file = exe.trailer_offset - 3
    tail_start_linear = sec_end_linear - 3
    tail_start_dgroup = tail_start_linear - DGROUP_LINEAR
    assert len(exe.trailer) == tail_size - 3
    assert tail_start_file + tail_size == len(exe.raw)
    assert tail_start_file + 3 == exe.trailer_offset == sec_end_file
    sec_end_dgroup = sec_end_linear - DGROUP_LINEAR
    assert sec_end_dgroup == 0x8BA0
    assert tail_start_dgroup == 0x8B9D
    tail_offsets = list(range(tail_start_dgroup, tail_start_dgroup + 3))
    clear_start = int(edata_refs[0]["resolved_DGROUP_offset"], 16)
    clear_end = int(end_refs[0]["resolved_DGROUP_offset"], 16)
    clear_count = clear_end - clear_start
    cleared_tail_offsets = [x for x in tail_offsets if clear_start <= x < clear_end]
    assert clear_count == 0x952
    assert tail_offsets == [0x8B9D, 0x8B9E, 0x8B9F]
    assert cleared_tail_offsets == [0x8B9E, 0x8B9F]

    dgroup_segments = []
    for row in manifest["runtime"]["members"]:
        for ds in row.get("data_segments", []):
            off = ds["linear"] - DGROUP_LINEAR
            if ds["segment"] in {"PAD", "EPAD"} and 0x8B90 <= off <= 0x8BA0:
                dgroup_segments.append({"member": row["member"], **ds,
                                        "dgroup_offset": f"{off:04X}",
                                        "dgroup_end_exclusive": f"{off + ds['size']:04X}"})
    assert any(x["segment"] == "PAD" and x["dgroup_offset"] == "8B9A"
               and x["dgroup_end_exclusive"] == "8B9C" for x in dgroup_segments)
    assert any(x["segment"] == "EPAD" and x["dgroup_offset"] == "8B9C"
               and x["dgroup_end_exclusive"] == "8B9D" for x in dgroup_segments)

    module_0093 = manifest["modules"]["root:0093"]
    seed_placement = module_0093["placements"]["_BSS"]
    seed_symbol = symbols["data"]["g_8BA2"]
    assert seed_placement == {"seg": DGROUP_SEG, "off": 0x8BA2, "size": 2}
    assert seed_symbol["seg"] == DGROUP_SEG and seed_symbol["off"] == 0x8BA2
    tu_row = next(row for row in build_report["translation_units"]
                  if row.get("module") == "root:0093")
    seed_object_path = ROOT / Path(tu_row["object"]["path"])
    seed_object = rd.read_file(seed_object_path)
    seed_bss_def = next(x for x in seed_object.segment_defs if x["name"] == "_BSS")
    assert seed_object.segment_length("_BSS") == 2
    assert seed_bss_def["alignment"] == "word"

    control_modules = []
    for key in ("dos\\crt0msg.asm", "dos\\nmsghdr.asm"):
        index, name, blob, obj = module_by_name[key]
        row = runtime_rows[key]
        assert row["module_index"] == index and row["member_sha256"] == sha(blob)
        control_modules.append({
            "member": name, "module_index": index,
            "member_sha256": sha(blob), "accepted_runtime_binding": row,
            "source_pin": pin(STARTUP / name.replace("\\", "/")),
            "full_object_decode": decode_obj(obj),
        })

    src_excerpts = source_excerpt(crt0_source,
                                  [(223, 244), (247, 318), (420, 476), (489, 503)])
    crt0msg_excerpt = source_excerpt(crt0msg_source, [(32, 68), (76, 123)])
    nmsghdr_excerpt = source_excerpt(nmsghdr_source, [(75, 125), (137, 175)])

    output_inputs = [
        ROOT / "README.md", ROOT / "docs/codegen-rules.md", ROOT / "docs/tu-evidence.md",
        ROOT / "docs/exe-format.md", manifest_path, symbols_path, build_report_path,
        oracle_lock_path, toolchain_path, runtime_location_path,
        ROOT / "tools/exe.py", ROOT / "tools/omf.py", ROOT / "tools/runtime.py",
        ROOT / "tools/rtlink.py", ROOT / "tools/compiler.py",
        crt0_source, crt0msg_source, nmsghdr_source, *source_inc_paths,
        LIBRARY, seed_object_path, NDISASM, Path(__file__).resolve(),
    ]
    input_pins = [pin(p) for p in output_inputs if p.is_file()]
    exe_pin = {"path": "assets/SIMANT.EXE (read-only analysis input)",
               "size": len(exe.raw), "sha256": exe.sha256,
               "asserted_against_oracle_lock": True}

    report = {
        "schema": "dos-tail-bss-boundary-v32-root-pending",
        "root_reviewed": False,
        "admitted": False,
        "status": "STATIC_RUNTIME_CLEAR_PROVEN_FOR_LAST_TWO_TAIL_BYTES; FIRST_TAIL_BYTE_AND_HISTORICAL_BOUNDARY_OPEN",
        "scope": "Static evidence only. No compiler/linker control, no executable output, and no image execution. Original executable is opened solely through tools/exe.py for historical analysis; its bytes are not written or used as any source/provider.",
        "source_and_tools": {"input_pins": input_pins, "original_executable": exe_pin,
                             "ndisasm_version": subprocess.run([str(NDISASM), "-v"],
                                 stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                 check=True).stdout.decode("latin1").strip()},
        "accepted_crt0_binding": {
            "runtime_manifest_row": crt_row,
            "runtime_location_row": crt_location,
            "library": "llibcr.lib", "library_module_index": crt_idx,
            "library_member": crt_name, "library_member_size": len(crt_blob),
            "library_member_sha256": sha(crt_blob),
            "member_segments": crt_obj.segment_lengths,
            "text_segment_sha256": sha(obj_text),
            "text_segment_length": len(obj_text),
            "bound_root_load_linear": crt_row["linear"],
            "bound_root_csip": "29F4:001C",
            "non_fixup_bytes_equal_to_historical_loaded_member": nonfixup_equal,
            "masked_fixup_byte_count": sum(code_mask),
            "whole_object_decode": decode_obj(crt_obj),
        },
        "runtime_source_evidence": {
            "crt0_source_pin": pin(crt0_source),
            "crt0_source_excerpts": src_excerpts,
            "source_claims": {
                "normal_exe_entry_sets_ss_to_dgroup_before_clear": True,
                "exe_path_copies_ss_to_es_before_clear": True,
                "clear_loop_is_cld_mov_di_edata_mov_cx_end_sub_xor_rep_stosb": True,
                "qczrinit_environment_argv_cinit_main_follow_clear_in_source": True,
                "preclear_error_calls_are_runtime_error_message_and_terminate": True,
            },
        },
        "manager_entry_chain": {
            "mz_cs_ip": f"{exe.mz.cs:04X}:{exe.mz.ip:04X}",
            "entry_linear": manager_start,
            "manager_frames_from_exe_format": ["2CFB", "2CFF", "2FB3"],
            "disassembler_origin_segment_offset": "2CFF:06F8",
            "original_manager_entry_disassembly": manager_disasm,
            "observed_terminal_transfer": "far JMP 2CFF:0737 -> 29F4:001C (__astart), after manager calls/stack setup",
            "terminal_jmp_instruction_linear": 0x2CFF * 16 + 0x0737,
        },
        "crt0_original_loaded_disassembly": {
            "disassembler_origin_segment_offset": "29F4:001C",
            "original_loaded_instruction_listing": crt_disasm,
        },
        "bss_bounds_from_symbol_fixups": {
            "fixup_sites": ext_sites,
            "edata_DGROUP_offset": "8B9E",
            "end_DGROUP_offset": "94F0",
            "end_anchor_consistency": "_end-2 resolves 94EE and _end resolves 94F0; both imply the same symbol value 94F0",
            "clear_interval": "DGROUP:[8B9E,94F0)",
            "clear_byte_count": clear_count,
            "last_written_byte": "94EF",
            "first_unwritten_end_byte": "94F0",
            "exact_runtime_instructions": [
                "29F4:009C push ss; 29F4:009D pop es (ES=DGROUP)",
                "29F4:009E cld (forward string direction)",
                "29F4:009F mov di,8B9E (_edata)",
                "29F4:00A2 mov cx,94F0 (_end)",
                "29F4:00A5 sub cx,di (CX=0952h)",
                "29F4:00A7 xor ax,ax",
                "29F4:00A9 rep stosb",
            ],
        },
        "historical_tail_file_to_runtime_mapping": {
            "section_index": sec.index,
            "section_load_segment": f"{sec.load_seg:04X}",
            "section_load_linear": sec.load_linear,
            "section_data_file_offset": sec.data_file_offset,
            "section_data_size": len(sec.data),
            "section_data_file_end_exclusive": sec_end_file,
            "section_load_end_linear_exclusive": sec_end_linear,
            "dgroup_segment": f"{DGROUP_SEG:04X}",
            "dgroup_linear": DGROUP_LINEAR,
            "dgroup_section_data_end_offset": f"{sec_end_dgroup:04X}",
            "common_tail_file_start": tail_start_file,
            "common_tail_size": tail_size,
            "common_tail_first_three_are_inside_section27_file_image": True,
            "tail_three_DGROUP_offsets": [f"{x:04X}" for x in tail_offsets],
            "overwritten_tail_offsets": [f"{x:04X}" for x in cleared_tail_offsets],
            "excluded_first_tail_offset": f"{tail_offsets[0]:04X}",
            "common_tail_bytes_emitted": False,
        },
        "nearby_accepted_dgroup_ownership": {
            "runtime_PAD_EPAD_contributions": dgroup_segments,
            "EPAD_end_exclusive": "8B9D",
            "edata_after_EPAD_by_one_byte": True,
            "file_backed_DGROUP_section_end": "8BA0",
            "first_confirmed_source_BSS_owner": {
                "module": "root:0093", "source": module_0093["source"],
                "source_sha256": module_0093["source_sha256"],
                "placement": seed_placement,
                "symbol": "g_8BA2", "symbol_row": seed_symbol,
                "object_path": tu_row["object"]["path"],
                "object_sha256": tu_row["object"]["sha256"],
                "BSS_SEGDEF": seed_bss_def,
            },
            "first_BSS_segment_start_8BA0": {
                "status": "LIKELY_BOUNDARY_INFERENCE_ONLY",
                "basis": "section-27 file-backed DGROUP ends at 8BA0; first confirmed word-aligned source BSS owner begins at 8BA2",
                "not_claimed_as": ["a located BSS object at 8BA0", "ownership of 8B9E-8B9F by a source variable"],
            },
            "unowned_seam_bytes_8B9D_through_8BA1": ["8B9D", "8B9E", "8B9F", "8BA0", "8BA1"],
        },
        "preclear_bypass_audit": {
            "normal_success_path": "DOS version >= 2 and stack-space check succeeds. It flows through the zero loop before any __qczrinit, _setenvp, _setargv, _cinit, or main call.",
            "dos_1_branch": "At 29F4:0022, JAE setup; the taken-less-than-2 path returns to PSP:0000 without reaching game or C-initializer code.",
            "stack_overflow_branch": "At 29F4:0043, JNC SPok; carry enters _FF_MSGBANNER, _NMSG_WRITE, then INT 21h terminate 4CFFh. It bypasses the clear but terminates without game/C-init callbacks.",
            "error_runtime_modules": control_modules,
            "error_runtime_source": {
                "crt0msg_pin": pin(crt0msg_source), "crt0msg_excerpts": crt0msg_excerpt,
                "nmsghdr_pin": pin(nmsghdr_source), "nmsghdr_excerpts": nmsghdr_excerpt,
                "bounded_effect_review": "The startup stack-error route prints fixed CRT MSG/HDR strings, checks CRT/debugger state in its own DGROUP contributions, and invokes DOS write. It does not call game code or C initializers; the inspected source path does not form a reference to 8B9D, 8B9E, or 8B9F. This does not claim that every possible DOS error-handler side effect is a game-independent runtime proof.",
            },
            "early_exit_routes_reach_game_or_c_init": False,
            "candidate_bytes_read_before_normal_clear": False,
        },
        "probe_controls": {
            "poison_before_startup_under_rtlink400_and_610": "NOT_RUN",
            "reason": "No verified RTLink entry-override/startup-hook syntax was established in this bounded static pass. Adding an unverified hook or patching the CRT would weaken the evidence; the actual unmodified startup object's linked control flow directly answers the normal-entry overwrite question.",
            "compiler_invoked": False,
            "linker_invoked": False,
            "linked_image_created": False,
            "image_executed": False,
            "raw_link_logs_or_maps": [],
        },
        "disposition": {
            "last_two_tail_bytes_overwritten_before_any_game_or_c_initializer": True,
            "first_tail_byte_overwritten": False,
            "first_tail_byte_role_proven": False,
            "historical_256_byte_tail_resolved": False,
            "unresolved_reason": "The first common-tail byte at DGROUP:8B9D precedes the actual _edata clear start and is not overwritten by CRT startup. The last two bytes are overwritten on the ordinary successful DOS EXE entry path, but the surrounding original file/runtime seam and any broader historical tail classification are not closed by this probe.",
            "no_padding_or_harmlessness_assumption": True,
        },
        "reproduction": {
            "command": "python build/workers/dos_tail_bss_boundary_v32/probe_tail_bss_boundary_v32.py",
            "outputs": ["build/workers/dos_tail_bss_boundary_v32/tail-bss-boundary-v32.json",
                        "build/workers/dos_tail_bss_boundary_v32/review-v32.md"],
        },
    }

    report_path = OUT / "tail-bss-boundary-v32.json"
    report = json_safe(report)
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"report": report_path.relative_to(ROOT).as_posix(),
                      "status": report["status"],
                      "edata": report["bss_bounds_from_symbol_fixups"]["edata_DGROUP_offset"],
                      "end": report["bss_bounds_from_symbol_fixups"]["end_DGROUP_offset"],
                      "tail_offsets": report["historical_tail_file_to_runtime_mapping"]["tail_three_DGROUP_offsets"],
                      "overwritten": report["historical_tail_file_to_runtime_mapping"]["overwritten_tail_offsets"],
                      "root_reviewed": False, "admitted": False}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
