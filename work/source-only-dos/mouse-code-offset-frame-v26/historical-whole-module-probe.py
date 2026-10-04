#!/usr/bin/env python3
"""Whole-module MASM source/frame variants for root:1B73; scratch-only."""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "tools"))
import compiler  # noqa: E402
from dos_source_bindings import apply_binding  # noqa: E402
from omf import OmfReader  # noqa: E402

BUILD = ROOT / "build/source-only-dos/build-report.json"
CANON = ROOT / "src/root/m1B73.asm"
GENERATED = ROOT / "build/source-only-dos/sources/U087.asm"
CURRENT_OBJ = ROOT / "build/source-only-dos/objects/U087.OBJ"
PACKET_CHAIN = [
    ROOT / "work/source-only-dos/source-bindings-v1.json",
    ROOT / "work/source-only-dos/assembly-frame-bindings-v1.json",
    ROOT / "work/source-only-dos/dgroup-rect-frame-bindings-v1.json",
]
TARGETS = [
    ("dx", "_f_1B73_03EE", 494, 0x24E),
    ("dx", "_f_1B73_065A", 504, 0x269),
    ("dx", "_f_1B73_06E3", 511, 0x281),
    ("dx", "_f_1B73_051F", 518, 0x299),
    ("ax", "_f_1B73_0CB3", 1531, 0xAB2),
]


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def pin(path: Path) -> dict:
    raw = path.read_bytes()
    try:
        name = path.relative_to(ROOT).as_posix()
    except ValueError:
        name = path.as_posix()
    return {"path": name, "size": len(raw), "sha256": digest(raw)}


def normalized_text(raw: bytes) -> str:
    return raw.decode("latin1").replace("\r\n", "\n").replace("\r", "\n")


def variant_source(base: str, form: str) -> str:
    text = base
    for reg, symbol, _line, _offset in TARGETS:
        old = f"lea {reg}, ds:{symbol}"
        if text.count(old) != 1:
            raise ValueError(f"expected exactly one source operand: {old}")
        if form == "lea_no_ds":
            new = f"lea {reg}, {symbol}"
        elif form == "lea_cs":
            new = f"lea {reg}, cs:{symbol}"
        elif form == "mov_offset":
            new = f"mov {reg}, offset {symbol}"
        elif form == "mov_offset_code_seg":
            new = f"mov {reg}, offset MOUSE_TEXT:{symbol}"
        else:
            raise ValueError(form)
        text = text.replace(old, new, 1)
    return text


def fixup_key(fix: dict) -> dict:
    return dict(fix)


def object_comparison(base_raw: bytes, candidate_raw: bytes, form: str) -> dict:
    reader = OmfReader()
    base = reader.read(base_raw, "U087-base")
    cand = reader.read(candidate_raw, "U087-" + form)
    global_equal = {
        "segment_bytes_equal": base.segments == cand.segments,
        "segment_lengths_equal": base.segment_lengths == cand.segment_lengths,
        "segment_defs_equal": base.segment_defs == cand.segment_defs,
        "publics_equal": base.publics == cand.publics,
        "groups_equal": base.groups == cand.groups,
        "externals_equal": base.externals == cand.externals,
        "local_publics_equal": base.local_publics == cand.local_publics,
        "local_externals_equal": base.local_externals == cand.local_externals,
    }
    base_fixups = [fixup_key(row) for row in base.linker_fixups]
    cand_fixups = [fixup_key(row) for row in cand.linker_fixups]
    changed = []
    invalid_count = 0
    expected_base_sites = {off: i for i, (_r, _s, _l, off) in enumerate(TARGETS)}
    expected_candidate_sites = {
        off if form in ("lea_no_ds", "lea_cs") else off - i - 1: i
        for i, (_r, _s, _l, off) in enumerate(TARGETS)
    }
    for old, new in zip(base_fixups, cand_fixups):
        fields = {k for k in set(old) | set(new) if old.get(k) != new.get(k)}
        if not fields:
            continue
        if (old.get("segment") == "MOUSE_TEXT"
                and old.get("offset") in expected_base_sites
                and new.get("offset") == old.get("offset")
                and new.get("target") == old.get("target")
                and new.get("displacement") == old.get("displacement")
                and fields <= {"frame_method", "frame_index", "frame_kind", "frame"}):
            changed.append({"offset": old["offset"], "target": old["target"],
                            "before_frame": [old.get("frame_kind"), old.get("frame")],
                            "after_frame": [new.get("frame_kind"), new.get("frame")],
                            "changed_fields": sorted(fields)})
        else:
            invalid_count += 1
    if len(base_fixups) != len(cand_fixups):
        invalid_count += abs(len(base_fixups) - len(cand_fixups))
    expected = set(expected_base_sites)
    changed_offsets = {row["offset"] for row in changed}
    segment = "MOUSE_TEXT"
    bdata = base.segment_bytes(segment)
    cdata = cand.segment_bytes(segment)
    candidate_by_site = {r.get("offset"): r for r in cand_fixups
                         if r.get("segment") == segment}
    instruction_rows = []
    for i, (_reg, symbol, line, fix_site) in enumerate(TARGETS):
        candidate_site = fix_site if form in ("lea_no_ds", "lea_cs") else fix_site - i - 1
        base_start = fix_site - 2
        candidate_start = candidate_site - (2 if form in ("lea_no_ds", "lea_cs") else 1)
        candidate_fixup = candidate_by_site.get(candidate_site)
        instruction_rows.append({
            "source_line": line,
            "base_instruction_offset": base_start,
            "candidate_instruction_offset": candidate_start,
            "base_fixup_site": fix_site,
            "candidate_fixup_site": candidate_site,
            "base_omf_instruction_bytes_relocation_words_zeroed": bdata[base_start:base_start + 4].hex().upper(),
            "candidate_omf_instruction_bytes_relocation_words_zeroed": cdata[candidate_start:candidate_start + (4 if form.startswith("lea") else 3)].hex().upper(),
            "symbol": symbol,
            "candidate_frame": ([candidate_fixup.get("frame_kind"), candidate_fixup.get("frame")]
                                if candidate_fixup else None),
            "candidate_target_displacement": candidate_fixup.get("displacement") if candidate_fixup else None,
        })
    target_candidate_fixups = [candidate_by_site.get(site) for site in sorted(expected_candidate_sites)]
    target_candidate_fixups = [r for r in target_candidate_fixups if r is not None]
    frame_only_form = form in ("lea_no_ds", "lea_cs")
    byte_diff_count = sum(a != b for a, b in zip(bdata, cdata)) + abs(len(bdata) - len(cdata))
    return {
        "global_object_structure_equal": all(global_equal.values()),
        "global_comparison": global_equal,
        "base_fixup_count": len(base_fixups),
        "candidate_fixup_count": len(cand_fixups),
        "unexpected_fixup_pair_difference_count": invalid_count,
        "target_frame_changes": changed,
        "target_offsets": sorted(expected),
        "target_instruction_rows": instruction_rows,
        "mouse_text_length_base": len(bdata),
        "mouse_text_length_candidate": len(cdata),
        "mouse_text_bytes_identical": bdata == cdata,
        "same_index_byte_difference_count": byte_diff_count,
        "mouse_text_length_delta": len(cdata) - len(bdata),
        "all_target_frames_now_code_segment": all(
            f.get("frame_kind") == "segment" and f.get("frame") == "MOUSE_TEXT"
            for f in target_candidate_fixups) and len(target_candidate_fixups) == 5,
        "passed_frame_only": (frame_only_form and all(global_equal.values()) and invalid_count == 0
                              and changed_offsets == expected and len(changed) == 5
                              and bdata == cdata and len(target_candidate_fixups) == 5
                              and all(f.get("frame_kind") == "segment"
                                      and f.get("frame") == "MOUSE_TEXT"
                                      for f in target_candidate_fixups)),
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    compiler.WORK = OUT / "compiler-work"
    compiler.WORK.mkdir(parents=True, exist_ok=True)
    build = json.loads(BUILD.read_text(encoding="utf-8"))
    row = next(x for x in build["translation_units"] if x["module"] == "root:1B73")
    current_source = pin(CANON)
    generated_pin = pin(GENERATED)
    current_obj_pin = pin(CURRENT_OBJ)
    if current_source["sha256"] != row["source"]["sha256"]:
        raise SystemExit("canonical source no longer matches current SOURCE_ONLY_DOS report")
    if generated_pin["sha256"] != row["generated_source"]["sha256"]:
        raise SystemExit("generated source no longer matches SOURCE_ONLY_DOS report")
    if current_obj_pin["sha256"] != row["object"]["sha256"]:
        raise SystemExit("current U087 object no longer matches SOURCE_ONLY_DOS report")

    # Rebuild the effective source binding from its pinned chain, then check it
    # byte-for-byte (modulo CRLF) against the generated SOURCE_ONLY_DOS TU.
    effective_text = normalized_text(CANON.read_bytes())
    binding_chain = []
    for packet_path in PACKET_CHAIN:
        packet = json.loads(packet_path.read_text(encoding="utf-8"))
        binding = next((x for x in packet["bindings"] if x["module"] == "root:1B73"), None)
        if binding is None:
            continue
        effective_text = apply_binding(effective_text, binding)
        binding_chain.append({"packet": pin(packet_path), "binding": binding})
    generated_matches_reconstructed_binding = (
        effective_text == normalized_text(GENERATED.read_bytes()))
    if not generated_matches_reconstructed_binding:
        raise SystemExit("packet chain does not reproduce generated U087 source")

    # Capture standard disassembly context only; no --raw option is passed.
    context_cmd = [sys.executable, str(ROOT / "tools/context.py"), "f_1B73_0235"]
    context = subprocess.run(context_cmd, cwd=ROOT, stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT, check=True, timeout=60)
    context_path = OUT / "context-f_1B73_0235.txt"
    context_path.write_bytes(context.stdout)

    source_variants = {"baseline_generated": effective_text}
    for form in ("lea_no_ds", "lea_cs", "mov_offset", "mov_offset_code_seg"):
        source_variants[form] = variant_source(effective_text, form)
    variant_rows = []
    candidate_obj_paths = {}
    for form, source in source_variants.items():
        source_path = OUT / "sources" / f"U087-{form}.asm"
        source_path.parent.mkdir(parents=True, exist_ok=True)
        source_path.write_bytes(source.replace("\n", "\r\n").encode("ascii"))
        result = compiler.assemble(source, "masm510", ["/Mx", "/L"],
                                  basename="U087", keep=True)
        if not result.ok:
            variant_rows.append({"form": form, "compile_ok": False,
                                 "log": result.log, "argv": result.argv})
            continue
        case_dir = OUT / "assembled" / form
        case_dir.mkdir(parents=True, exist_ok=True)
        obj_path = case_dir / "U087.OBJ"
        obj_path.write_bytes(result.obj)
        listing_path = result.workdir / "U087.LST"
        if listing_path.exists():
            (case_dir / "U087.LST").write_bytes(listing_path.read_bytes())
        log_path = case_dir / "MASM.LOG"
        log_path.write_text(result.log, encoding="latin1")
        candidate_obj_paths[form] = obj_path
        variant_rows.append({"form": form, "compile_ok": True,
                             "source": pin(source_path), "object": pin(obj_path),
                             "listing": pin(case_dir / "U087.LST") if (case_dir / "U087.LST").exists() else None,
                             "compiler_log": pin(log_path),
                             "masm_workdir": result.workdir.relative_to(ROOT).as_posix(),
                             "argv": result.argv,
                             "matches_admitted_u087_object": digest(result.obj) == row["object"]["sha256"]})

    baseline = candidate_obj_paths.get("baseline_generated")
    if baseline is None or digest(baseline.read_bytes()) != row["object"]["sha256"]:
        raise SystemExit("reassembled baseline does not match admitted SOURCE_ONLY_DOS U087 object")
    comparisons = {form: object_comparison(baseline.read_bytes(), path.read_bytes(), form)
                   for form, path in candidate_obj_paths.items() if form != "baseline_generated"}
    fixture_script = OUT / "callback_fixture_v29.py"
    fixture_run = subprocess.run([sys.executable, str(fixture_script)], cwd=ROOT,
                                  stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                  check=True, timeout=180)
    fixture_report_path = OUT / "callback-fixtures/callback-frame-runtime-fixture-v29.json"
    fixture_report = json.loads(fixture_report_path.read_text(encoding="utf-8"))
    report = {
        "schema": "simant-root-1b73-callback-offset-frame-probe-v29",
        "root_reviewed": False,
        "status": "WHOLE_MODULE_FRAME_ONLY_VARIANTS_AND_SHIFTED_CALLBACK_FIXTURE_PASS",
        "scope": "fresh scratch whole-module MASM frame variants and independent test-owned shifted-DGROUP callback fixture; no canonical edits, original byte input, object patching, full game link, or warning-image execution",
        "inputs": {
            "build_report": pin(BUILD),
            "canonical_source": current_source,
            "generated_source": generated_pin,
            "admitted_object": current_obj_pin,
            "binding_chain": [{"packet": r["packet"], "binding": r["binding"]}
                              for r in binding_chain],
            "toolchain": pin(ROOT / "layout/toolchain.json"),
            "masm_profile": compiler.verify_profile("masm510"),
            "omf_reader": pin(ROOT / "tools/omf.py"),
            "compiler_tool": pin(ROOT / "tools/compiler.py"),
            "context_tool": pin(ROOT / "tools/context.py"),
            "context_output": pin(context_path),
            "callback_fixture_script": pin(fixture_script),
            "callback_fixture_report": pin(fixture_report_path),
            "probe_script": pin(Path(__file__)),
        },
        "generated_binding_reconstruction_matches": generated_matches_reconstructed_binding,
        "context_invocation": context_cmd,
        "context_excerpt": normalized_text(context.stdout)[:3500],
        "admitted_binding_edits": row["source_binding"]["edits"],
        "whole_module_variants": variant_rows,
        "whole_module_comparisons": comparisons,
        "callback_runtime_fixture": {
            "report_path": fixture_report_path.relative_to(ROOT).as_posix(),
            "all_cases_pass": fixture_report["all_cases_pass"],
            "cases": [{"linker": c["linker"], "variant": c["variant"],
                       "expected": c["expected"], "actual": c["actual"],
                       "passed": c["passed"]} for c in fixture_report["cases"]],
            "invocation_output": normalized_text(fixture_run.stdout)[:1500],
        },
        "callback_use_interpretation": {
            "mouse_callback": "INT 33h function 0Ch consumes ES:DX; source sets ES=CS before LEA for _f_1B73_03EE.",
            "interrupt_vectors": "INT 21h function 25h consumes DS:DX; source switches DS to CS before the three LEAs for _f_1B73_065A, _f_1B73_06E3, and _f_1B73_051F, then restores DS.",
            "local_callback": "_f_1B73_0CB3 offset is stored in _g_5FFA and later used by a near CALL in the same code segment.",
        },
    }
    out_path = OUT / "callback-frame-whole-module-v29.json"
    out_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"report": out_path.relative_to(ROOT).as_posix(),
                      "variant_results": [{"form": row["form"], "compile_ok": row["compile_ok"],
                                           "matches_admitted": row.get("matches_admitted_u087_object")}
                                          for row in variant_rows],
                      "comparisons": {k: {"pass": v["passed_frame_only"],
                                           "frame_changes": len(v["target_frame_changes"]),
                                           "bytes_equal": v["mouse_text_bytes_identical"],
                                           "length_delta": v["mouse_text_length_delta"],
                                           "other_fixup_changes": v["unexpected_fixup_pair_difference_count"]}
                                      for k, v in comparisons.items()}}, indent=2))
    return 0 if fixture_report["all_cases_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
