"""Read-only v36 database/fatal boundary proof, plus a whole-module source control.

Only this worker directory is written.  The executable is read by context/search
as a research oracle; no executable bytes are inputs to a generated build.
The loop model computes addresses only and never supplies physical-memory bytes.
"""
from __future__ import annotations
import contextlib
import hashlib
import io
import json
import math
from pathlib import Path
import shutil
import struct
import subprocess
import sys

sys.dont_write_bytecode = True
OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, "C:/tools/capstone-5.0.3")
from capstone import Cs, CS_ARCH_X86, CS_MODE_16
import compiler
import functions
import match
import search
from omf import OmfReader

MODULES = {
    "root:15F8", "S20:39F1", "root:205F", "root:1A28", "root:1A53",
    "root:1986", "root:1C62", "root:1CE2", "root:24AB", "root:1FBD",
    "root:1B4E", "S15:384C", "root:171C", "root:277E", "root:0000",
    "root:0250", "root:19DC", "root:195A", "root:1B73", "root:1FD2",
    "root:28BC", "root:295C",
}
CONTEXTS = [
    "OpenDB", "GetFreeHandle", "db_SetDataBase", "DosPunt", "Punt",
    "IBMInitStuff", "f_205F_0004", "f_1CE2_01C3", "f_24AB_038D",
    "f_1FBD_0000", "f_1B4E_005E", "o15_384C_0152",
]
HISTORICAL = [
    "work/source-only-dos/database-punt-root-review-v17.md",
    "work/source-only-dos/database-punt-static-dependency-review-v3.md",
    "work/source-only-dos/database-punt-static-dependency-proof-candidate-v3.json",
    "work/source-only-dos/database-punt-call-closure-supplement-v3.json",
    "work/source-only-dos/database-punt-effective-overlay-check-v16.json",
    "work/source-only-dos/database-layout-review-v22/root-review.md",
    "work/source-only-dos/database-layout-review-v22/receipt.md",
    "work/source-only-dos/database-layout-review-v22/v22-static-closure-receipt.json",
    "work/source-only-dos/database-layout-review-v22/v22-early-punt-continuation-addendum.md",
    "work/source-only-dos/database-layout-review-v22/v22-early-punt-continuation-addendum.json",
    "work/source-only-dos/structural-audits-v32/database-v32/review.md",
    "work/source-only-dos/structural-audits-v32/database-v32/receipt.json",
    "work/source-only-dos/structural-audits-v26/dos_remaining_misc_owners_v31/free-list-punt-reentry-v31.md",
    "work/source-only-dos/structural-audits-v35/sound-report-v35.md",
    "work/source-only-dos/callback-table-reviewed-contract-v1.json",
    "work/source-only-dos/callback-table-bindings-v1.json",
    "work/source-only-dos/providers/callback-table.c",
    "work/source-only-dos/database-record-state-contract-v1.json",
    "work/source-only-dos/database-record-state-bindings-v1.json",
    "work/source-only-dos/providers/database-record-state.c",
    "work/source-only-dos/driver-ss-frame-contract-v1.json",
    "work/source-only-dos/queue-lifetime-contract-v1.json",
    "work/source-only-dos/database-punt-crt-control/crt-exit-control-result.json",
]


def pin(path: Path) -> dict:
    return {"path": path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else path.as_posix(),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "size": path.stat().st_size}


def checked(pin_row: dict) -> dict:
    actual = pin(ROOT / pin_row["path"].replace("\\", "/"))
    if actual["sha256"] != pin_row["sha256"]:
        raise AssertionError("Input drift: " + pin_row["path"])
    return actual


def loop_addresses(rows: int, columns: int, base: int = 0) -> list[int]:
    """Literal 16-bit MOVSB; ADD DI,DX; LOOP semantics, DF=0, DX=columns-1."""
    cx = rows & 0xFFFF
    di = base & 0xFFFF
    offsets = []
    while True:
        offsets.append(di)
        di = (di + 1) & 0xFFFF       # MOVSB postincrement
        di = (di + columns - 1) & 0xFFFF
        cx = (cx - 1) & 0xFFFF       # LOOP decrements before testing
        if cx == 0:
            return offsets
        assert len(offsets) < 65536


def main() -> None:
    report_path = ROOT / "build/source-only-dos/build-report.json"
    report_pin = pin(report_path)
    report = json.loads(report_path.read_text(encoding="utf-8-sig"))
    man = json.loads((ROOT / "layout/manifest.json").read_text(encoding="utf-8-sig"))
    rows = report["translation_units"]
    joins = []
    for row in rows:
        joins.append({"module": row["module"], "generated_source": checked(row["generated_source"]),
                      "object": checked(row["object"])})
    direct = [{"module": row["module"], "source": checked(row["source"]),
               "generated_source": checked(row["generated_source"]), "object": checked(row["object"]),
               "reviewed_bodies": row.get("reviewed_bodies", [])}
              for row in rows if row["module"] in MODULES]

    # Context first; all captures are symbolic disassembly, never raw byte capsules.
    context_pins = []
    for name in CONTEXTS:
        proc = subprocess.run([sys.executable, "-B", str(ROOT / "tools/context.py"), name],
                              cwd=ROOT, capture_output=True, check=True)
        path = OUT / (name + ".context.txt")
        path.write_bytes(proc.stdout)
        context_pins.append(pin(path))

    # Unmodified readable whole module as the positive source control.  Override
    # both scratch output roots so no search/cc output escapes this worker.
    draft = OUT / "m1FBD.asm"
    shutil.copyfile(ROOT / "src/root/m1FBD.asm", draft)
    compiler.WORK = OUT / "cc"
    search.ROOT = OUT
    search_log = io.StringIO()
    with contextlib.redirect_stdout(search_log):
        strict = search.run("f_1FBD_0000", [draft], None, None, None, {}, quiet=True)
    (OUT / "search.log").write_text(search_log.getvalue(), encoding="utf-8")
    assert len(strict) == 1 and strict[0]["status"] == "EXACT", strict

    generated = next(row for row in rows if row["module"] == "root:1FBD")
    obj = OmfReader(communals=True).read_file(ROOT / generated["object"]["path"])
    f = functions.get("f_1FBD_0000")
    rec = man["modules"]["root:1FBD"]
    placements = {k: {"seg": v["seg"], "off": v["off"]} for k, v in rec["placements"].items()}
    bound = match.Binder(match.Target(f["unit"], f["seg"], f["off"], f["size"]),
                         obj, "TEXTOUT_TEXT", "_f_1FBD_0000", placements).bind()
    assert bound.exact, bound.reasons
    md = Cs(CS_ARCH_X86, CS_MODE_16)
    insns = {i.address: (i.mnemonic, i.op_str) for i in md.disasm(bound.candidate, 0)}
    expected = {
        0x84: ("mov", "cx, word ptr [0x3dda]"),
        0x88: ("mul", "cl"),
        0x8B: ("lds", "si, ptr [0x3dd6]"),
        0x93: ("movsb", "byte ptr es:[di], byte ptr [si]"),
        0x94: ("add", "di, dx"),
        0x96: ("loop", "0x93"),
    }
    assert {off: insns[off] for off in expected} == expected
    assert obj.segment_length("_DATA") == 1324
    assert next(p for p in obj.publics if p["name"] == "_g_5ABE")["offset"] == 4
    assert obj.segment_length("TEXTOUT_TEXT") == 343

    asm = (ROOT / "src/root/m1FBD.asm").read_text(encoding="latin1")
    video = (ROOT / "src/root/m1B4E.asm").read_text(encoding="latin1")
    assert "_g_5ABE\t\tdb\t1040 dup (0)" in asm
    assert "_g_5ECE\t\tdb\t79 dup (0)" in asm
    assert "_g_5F1D\t\tdb\t0" in asm
    assert "_g_3DDA\t\tdw\t0" in video
    assert "_g_3DDC\t\tdw\t0" in video
    assert "_g_3DDE\t\tdw\t8" in video
    assert "_g_3DD6\t\tdw\t0" in video and "_g_3DD8\t\tdw\t0" in video

    # Rejoin the unchanged fatal/data-access functions to the actual generated
    # objects, including the conditional return after Punt.  This is research
    # binding of existing source objects, never an original-byte constructor.
    fatal_object_checks = []
    for name, module in (("OpenDB", "root:1A28"), ("GetFreeHandle", "root:1A28"),
                         ("db_SetDataBase", "root:1A53"), ("DosPunt", "root:1A28"),
                         ("Punt", "root:1C62"), ("f_1CE2_01C3", "root:1CE2"),
                         ("f_24AB_038D", "root:24AB"), ("f_1B4E_005E", "root:1B4E"),
                         ("o15_384C_0152", "S15:384C")):
        tu = next(row for row in rows if row["module"] == module)
        compiled = OmfReader(communals=True).read_file(ROOT / tu["object"]["path"])
        target = functions.get(name)
        pub_name, pub = match.public_in(compiled, name)
        assert pub, name
        context = man["modules"][module]
        pl = {k: {"seg": v["seg"], "off": v["off"]} for k, v in context.get("placements", {}).items()}
        result = match.Binder(match.Target(target["unit"], target["seg"], target["off"], target["size"]),
                              compiled, pub["segment"], pub_name, pl).bind()
        assert result.exact, (name, result.reasons)
        fatal_object_checks.append({"name": name, "module": module, "extent": target["size"],
                                    "exact": result.exact, "sha256": hashlib.sha256(result.original).hexdigest()})

    # The current compiled initialized fields, rather than declarations alone,
    # establish the zero-height/zero-font prefix of the counterexample.
    vtu = next(row for row in rows if row["module"] == "root:1B4E")
    vobj = OmfReader(communals=True).read_file(ROOT / vtu["object"]["path"])
    data = vobj.segment_bytes("_DATA")
    initial_fields = []
    for name, expected_value in (("_g_3DD6", 0), ("_g_3DD8", 0), ("_g_3DDA", 0),
                                  ("_g_3DDC", 0), ("_g_3DDE", 8)):
        public = next(p for p in vobj.publics if p["name"] == name)
        assert struct.unpack_from("<H", data, public["offset"])[0] == expected_value
        initial_fields.append({"name": name, "segment": "_DATA", "object_offset": public["offset"],
                               "value": expected_value})
    callback_tu = next(row for row in rows if row["module"] == "source-owned:driver-callback-table")
    callback_obj = OmfReader(communals=True).read_file(ROOT / callback_tu["object"]["path"])
    callback_comdef = next(c for c in callback_obj.communals if c["name"] == "_driver_callback_table")
    callback_owner_check = {"source": checked(callback_tu["generated_source"]),
                            "object": checked(callback_tu["object"]), "communal": callback_comdef,
                            "no_initialized_segment_bytes": not any(callback_obj.segments.values())}
    assert callback_owner_check["no_initialized_segment_bytes"]

    # The existing source diagnostic is bounded in both Punt local buffers.
    # Missing shared.ndx is a normal DOS-open failure.  Verify errno-2 diagnostic
    # from the pinned, source-build-eligible third-party runtime library.
    prefix = "FATAL ERROR: PROGRAM ABORTED\n"
    runtime_path = Path(next(row["path"] for row in report["runtime_components"] if row["name"] == "llibcr.lib"))
    reader = OmfReader(communals=True)
    member_name, member = next((n, b) for n, b in reader.split_library(runtime_path.read_bytes()) if n == "syserr.c")
    syserr = reader.read(member)
    errors = syserr.segment_bytes("_DATA")
    errlist = next(p for p in syserr.publics if p["name"] == "_sys_errlist")
    errno2_site = errlist["offset"] + 2 * 4
    errno2_fixup = next(f for f in syserr.linker_fixups if f["segment"] == "_DATA" and f["offset"] == errno2_site)
    assert errno2_fixup["target_kind"] == "segment" and errno2_fixup["target"] == "_DATA"
    errno2_offset = struct.unpack_from("<H", errors, errno2_site)[0] + errno2_fixup["displacement"]
    errno2_text = errors[errno2_offset:errors.index(0, errno2_offset)].decode("ascii")
    assert errno2_text == "No such file or directory"
    message = "Index file missing\nDos error: 2: " + errno2_text
    fatal = prefix + message
    assert len(message) < 90 and len(fatal) < 140
    assert len(fatal) >= 80
    columns = min(len(fatal), 79)
    assert columns == 79
    zero = loop_addresses(0, columns)
    first_out = next((k, p) for k, p in enumerate(zero) if p >= 1040)
    first_out_tu = next((k, p) for k, p in enumerate(zero) if p >= 1320)
    # Odd stride visits every possible near offset, for *any* symbolic base.
    assert len(zero) == 65536 and len(set(zero)) == 65536
    assert math.gcd(columns, 65536) == 1
    for base in (0, 4, 0xFFFF):
        assert len(set(loop_addresses(0, columns, base))) == 65536
    controls = []
    for height in (1, 8, 13, 0):
        offsets = loop_addresses(height, columns)
        highest_full_bitmap_offset = (height - 1) * columns + columns - 1 if height else None
        controls.append({"initial_CX": height, "column_count": columns,
                         "first_glyph_stores": len(offsets), "unique_first_glyph_destinations": len(set(offsets)),
                         "first_glyph_within_1040_byte_bitmap": max(offsets) < 1040,
                         "max_full_string_bitmap_offset_for_positive_height": highest_full_bitmap_offset})
    assert [c["first_glyph_stores"] for c in controls] == [1, 8, 13, 65536]
    assert [c["first_glyph_within_1040_byte_bitmap"] for c in controls] == [True, True, True, False]
    assert all(c["max_full_string_bitmap_offset_for_positive_height"] < 1040 for c in controls[:3])

    head = subprocess.run(["git", "-c", "safe.directory=D:/Prog/simant_recon", "rev-parse", "HEAD"],
                          cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    gates = [dict(row) for row in report["layout_dependencies"]
             if row["id"] in {"database-open-minus-one-record", "database-handle-plus-four"}]
    lock = json.loads((ROOT / "layout/oracle.lock.json").read_text(encoding="utf-8-sig"))
    receipt = {
        "schema": "simant-dos-database-exit-boundary-v36", "verdict": "UNRESOLVED_WITH_NEW_CONDITIONAL_COUNTEREXAMPLE",
        "root_reviewed": False, "head_observation": head, "build_report": report_pin,
        "report_head_provenance_claim": None, "translation_units_verified": len(joins),
        "generated_sources_verified": len(joins), "objects_verified": len(joins),
        "strict_imports": len(report["strict_static_audit"]), "gates_unchanged": gates,
        "direct_tu_pins": direct,
        "input_pins": [pin(ROOT / p) for p in HISTORICAL] + [pin(ROOT / p) for p in (
            "layout/manifest.json", "layout/symbols.json", "layout/functions.json", "layout/oracle.lock.json",
            "tools/context.py", "tools/search.py", "tools/compiler.py", "tools/match.py", "tools/omf.py",
            "tools/source_only_dos.py", "tools/dos_source_bindings.py")]
            + [pin(Path("C:/tools/msc-6.00/STARTUP/dos/crt0.asm")), pin(Path("C:/tools/msc-6.00/STARTUP/dos/crt0dat.asm"))]
            + [checked(row) for row in report["runtime_components"]],
        "contexts": context_pins, "whole_module_source_control": strict,
        "compiled_module_research_check": {"generated_object_exact_to_original": bound.exact,
            "original_function_hash": hashlib.sha256(bound.original).hexdigest(),
            "bound_candidate_hash": hashlib.sha256(bound.candidate).hexdigest(),
            "original_function_extent": 343, "source_data_extent": 1324,
            "selected_instructions": [{"offset": f"{off:04X}", "mnemonic": pair[0], "operands": pair[1]}
                                      for off, pair in expected.items()]},
        "fatal_function_object_checks": fatal_object_checks,
        "compiled_initial_fields": initial_fields,
        "compiled_callback_owner": callback_owner_check,
        "runtime_diagnostic_check": {"library": pin(runtime_path), "member": member_name,
            "member_sha256": hashlib.sha256(member).hexdigest(), "errno": 2,
            "pointer_site": errno2_site, "string_offset": errno2_offset,
            "error_text_chars": len(errno2_text), "expected_text_verified": True},
        "new_boundary": {
            "condition": "Early first Punt; pre-display g_5A97 != 6; g_9128 returns normally with source startup state and DF=0 preserved.",
            "direct_source_state": {"fd_55B3_65A4": 0, "g_3DD6_far_pointer": "0000:0000", "g_3DDA": 0,
                                    "g_3DDC": 0, "g_3DDE": 8},
            "source_path": ["Punt", "f_1CE2_01C3", "f_24AB_038D", "f_1FBD_0000:L0093"],
            "diagnostic_length_example": {"message_chars": len(message), "fatal_chars": len(fatal), "copied_chars": columns},
            "address_recurrence": "destination(k) = (bitmap_base + 79*k) mod 65536, k=0..65535",
            "stores_before_next_character": len(zero), "unique_DGROUP_byte_offsets": len(set(zero)),
            "first_outside_bitmap": {"zero_based_iteration": first_out[0], "ordinal_store": first_out[0] + 1,
                                     "bitmap_relative_offset": first_out[1], "same_TU_text_copy_relative_offset": first_out[1] - 1040},
            "first_outside_whole_TU": {"zero_based_iteration": first_out_tu[0], "ordinal_store": first_out_tu[0] + 1,
                                       "bitmap_relative_offset": first_out_tu[1], "TU_relative_offset": first_out_tu[1] + 4},
            "consequence": "The first inner loop writes every near byte offset, including callbacks, guard, and stack under SS=DGROUP, before g_9154 or fatal cleanup. Written values and subsequent control cannot be predicted without external physical memory. The prior ordinary-return continuation is not a state-preserving closure.",
            "does_not_claim": ["actual 0000:0000 return", "actual startup escape", "reachable fifth invalid record/handle access", "specific overwritten values", "physical IVT bytes", "whole-game runtime test"],
            "controls": controls,
        },
        "source_owned_alias_attempt": {"status": "EXCLUDED_WITHIN_AUTHORIZED_SCOPE",
            "reasons": ["g_9128/g_9154 are already bounded views of the same zero-startup 25-slot owner.",
                        "g_3DF4 contains the real empty entry but is a distinct initialized pointer; rebinding slot zero to it would detach it from the table copied by f_1B4E_0025/f_1B4E_01AE.",
                        "No prior source call to f_1B4E_0025 or driver font setup precedes the early opens.",
                        "Pre-initializing callbacks/fonts or guarding zero CX changes historical source semantics.",
                        "Growing bitmap/record/handle owners cannot close a 64KiB uncontrolled DGROUP copy."]},
        "oracle": lock["inputs"]["SIMANT.EXE"],
        "original_executable_role": "read-only research in context/search/binder; zero oracle bytes emitted in any source or build input",
        "scope": "Source/disassembly/address arithmetic counterexample; no promotion, gate mutation, standalone game link, or acceptance claim.",
        "probe_source": pin(Path(__file__)),
    }
    (OUT / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"verdict": receipt["verdict"], "source_control": strict[0]["status"],
                      "translation_units_verified": len(joins), "strict_imports": receipt["strict_imports"],
                      "controls": controls, "first_outside_bitmap": receipt["new_boundary"]["first_outside_bitmap"],
                      "first_outside_whole_TU": receipt["new_boundary"]["first_outside_whole_TU"]}, indent=2))


if __name__ == "__main__":
    main()
