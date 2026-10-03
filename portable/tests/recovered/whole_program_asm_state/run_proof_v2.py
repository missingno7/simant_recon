#!/usr/bin/env python3
"""Immutable source/layout and native compile proof for state plan v2."""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
TOOL_DIR = ROOT / "portable/tools"
sys.path.insert(0, str(TOOL_DIR))
import source_state_aliases_v2 as alias_tool  # noqa: E402

PLAN_PATH = ROOT / "portable/tests/recovered/whole_program_asm_state/plan_v2.json"
DEFAULT_REPORT = ROOT / "portable/tests/recovered/evidence/whole-program-asm-state-v2/report.json"
FIXTURE_DIR = ROOT / "portable/tests/recovered/whole_program_asm_state/fixtures/v1-generated"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def validate_address_evidence(plan: dict) -> list[str]:
    symbols = json.loads((ROOT / "layout/symbols.json").read_text(encoding="utf-8"))["data"]
    manifest = json.loads((ROOT / "layout/manifest.json").read_text(encoding="utf-8"))["modules"]
    failures = []
    m0250 = manifest["root:0250"]["placements"]["_DATA"]
    m195a = manifest["root:195A"]["placements"]["_DATA"]
    if [m0250["seg"], m0250["off"]] != [21939, 6590]:
        failures.append("root:0250 _DATA placement mismatch")
    if [m195a["seg"], m195a["off"]] != [21939, 13826]:
        failures.append("root:195A _DATA placement mismatch")
    c_offsets = {"g_19C0": 6592, "g_19C6": 6598, "g_19CA": 6602, "g_19CE": 6606}
    for row in plan["alias_rewrites"]:
        address = row["address"]
        if row["kind"] == "scalar-lvalue":
            expected = [21939, c_offsets[row["target"]]]
        else:
            expected = [21939, 7380 + row["table_index"] * 4]
        if address != expected:
            failures.append(f"plan address mismatch for {row['alias']}")
        symbol = symbols.get(row["alias"])
        if symbol is None or [symbol.get("seg"), symbol.get("off")] != expected:
            failures.append(f"accepted OMF PUBLIC mismatch for {row['alias']}")
    base = symbols.get("fd_55B3_1CD4")
    if base is None or [base.get("seg"), base.get("off")] != [21939, 7380]:
        failures.append("accepted pointer-table base PUBLIC mismatch")
    for row in plan["asm_scalars"]:
        symbol = symbols.get(row["name"])
        expected = [m195a["seg"], m195a["off"] + {"fd_55B3_360C": 10,
                    "fd_55B3_3612": 16, "fd_55B3_3614": 18}[row["name"]]]
        if row["address"] != expected or symbol is None or [symbol.get("seg"), symbol.get("off")] != expected:
            failures.append(f"accepted ASM scalar address mismatch for {row['name']}")
    return failures


def closure_paths(plan: dict) -> list[Path]:
    paths = {ROOT / "portable/tests/recovered/whole_program_asm_state/plan_v2.json",
             ROOT / "portable/tests/recovered/whole_program_asm_state/run_proof_v2.py",
             ROOT / "portable/tools/source_state_aliases_v2.py",
             ROOT / "portable/tools/asm_state_provider.py",
             ROOT / "portable/tests/recovered/whole_program_asm_state/validate_historical_pins_v2.py",
             ROOT / plan["parent_receipt"]["path"]}
    paths.update(ROOT / p for p in plan["pinned_source_hashes"])
    paths.update(ROOT / p for p in plan["fixture_hashes"])
    return sorted(paths)


def compile_unit(compiler: Path, text: str, name: str, temp: Path) -> dict:
    cfile = temp / f"{name}.c"
    object_file = temp / f"{name}.o"
    cfile.write_text(text, encoding="utf-8", newline="\n")
    command = [str(compiler), "-std=c11", "-fsigned-char", "-fno-builtin", "-I", str(ROOT),
               "-I", str(ROOT / "portable/whole_program/state"), "-I", str(FIXTURE_DIR),
               "-Werror=implicit-function-declaration", "-c", str(cfile), "-o", str(object_file)]
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    if result.returncode:
        raise AssertionError(f"compile failed for {name}:\n{result.stdout}{result.stderr}")
    return {"translation_unit": name, "command": command,
            "returncode": result.returncode,
            "stdout": result.stdout, "stderr": result.stderr,
            "object_sha256": digest(object_file), "object_size": object_file.stat().st_size}


def run(report_path: Path = DEFAULT_REPORT) -> dict:
    if report_path.exists():
        raise FileExistsError(f"immutable report already exists: {report_path}")
    plan = alias_tool.load_plan(PLAN_PATH)
    mismatches = alias_tool.validate_historical_pins(plan)
    if mismatches:
        raise RuntimeError(f"historical input pins failed: {mismatches}")
    decl_failures = alias_tool.validate_source_declarations(plan)
    if decl_failures:
        raise RuntimeError("exact source declaration controls failed: " + "; ".join(decl_failures))
    address_failures = validate_address_evidence(plan)
    if address_failures:
        raise RuntimeError("source/accepted address controls failed: " + "; ".join(address_failures))
    paths = closure_paths(plan)
    before = {p.relative_to(ROOT).as_posix(): digest(p) for p in paths}

    controls = [{"name": "historical_pin_and_exact_declaration_checks", "passed": True,
                 "source_pins": len(plan["pinned_source_hashes"]),
                 "fixtures": len(plan["fixture_hashes"]),
                 "uses_live_migration": False},
                {"name": "source_manifest_omf_address_controls", "passed": True,
                 "alias_views": len(plan["alias_rewrites"]),
                 "asm_scalars": len(plan["asm_scalars"])}]

    # Positive control: lexical renames preserve comments/literals and leave
    # the existing table base untouched while lowering only interior views.
    source = (FIXTURE_DIR / "S20_m39F1.c").read_text(encoding="utf-8")
    transformed, trace = alias_tool.transform(source, plan)
    require(trace["lexical_passes"] == 1, "transform did not use exactly one lexical pass")
    require(not trace["canonical_table_base_rewritten"], "table-base symbol was rewritten")
    require("fd_55B3_1CD4[3]" in transformed and "fd_55B3_1CD4[4]" in transformed,
            "interior table slots were not resolved")
    require("extern char  *  fd_55B3_1CE" not in transformed,
            "interior view extern declaration remains")
    # Existing [1]/[2] aliases from the archived source-table lowering remain as-is.
    require("fd_55B3_1CD4[1]" in transformed and "fd_55B3_1CD4[2]" in transformed,
            "previous table slots changed during v2 lowering")
    control_probe = ('// fd_55B3_19C0\nconst char *literal = "fd_55B3_19C6";\n'
                     'extern int16_t fd_55B3_19C0;\nint f(void) { return fd_55B3_19C0; }\n')
    probe_out, probe_trace = alias_tool.transform(control_probe, plan)
    require('// fd_55B3_19C0' in probe_out and '"fd_55B3_19C6"' in probe_out,
            "comment or literal was rewritten")
    require("extern int16_t g_19C0;" in probe_out and "return g_19C0;" in probe_out,
            "scalar prototype/reference did not canonicalize")
    require(probe_trace["lexical_passes"] == 1, "probe triggered multiple rewrite passes")
    controls.append({"name": "one_pass_alias_transform_positive", "passed": True,
                     "removed_pointer_externs": trace["removed_externs"],
                     "scalar_replacements": probe_trace["replacement_counts"],
                     "preserved_comment_and_literal": True,
                     "canonical_table_base_rewritten": False,
                     "storage_owners_created": 0})

    # Negative address control uses a copy of the frozen plan. This proves the
    # validator rejects a perturbed plan without re-deriving aliases from a
    # changing migration report.
    bad = json.loads(json.dumps(plan))
    bad["alias_rewrites"][0]["address"][1] += 2
    bad_failures = validate_address_evidence(bad)
    require(any("plan address mismatch" in f for f in bad_failures),
            "wrong-address negative control was accepted")
    asm_text = (ROOT / "src/root/m195A.asm").read_text(encoding="utf-8")
    require("_fd_55B3_360E\tdd\t0" in asm_text,
            "excluded far pointer evidence changed")
    require(all(r["name"] != "fd_55B3_360E" for r in plan["asm_scalars"]),
            "unsupported pointer entered provider plan")
    controls.append({"name": "wrong_address_and_far_pointer_negative", "passed": True,
                     "wrong_plan_address_rejected": True,
                     "excluded_far_pointer_directive": "dd"})

    compiler_raw = shutil.which("gcc")
    if not compiler_raw:
        raise RuntimeError("GCC required for native compile controls")
    compiler = Path(compiler_raw).resolve()
    version = subprocess.run([str(compiler), "--version"], capture_output=True,
                             text=True, check=True).stdout.splitlines()[0]
    compile_results = []
    with tempfile.TemporaryDirectory(prefix="simant-state-plan-v2-") as temp_raw:
        temp = Path(temp_raw)
        provider = (ROOT / "portable/whole_program/state/asm_shared_state.c").read_text(encoding="utf-8")
        compile_results.append(compile_unit(compiler, provider, "asm_shared_state", temp))
        fixture_names = ["root_m15D9.c", "S04_m35F5.c", "S05_m35F5.c",
                         "S22_m39C7.c", "S22_m3BBD.c", "S20_m39F1.c"]
        traces = {}
        for name in fixture_names:
            original = (FIXTURE_DIR / name).read_text(encoding="utf-8")
            lowered, item_trace = alias_tool.transform(original, plan)
            traces[name] = item_trace
            compile_results.append(compile_unit(compiler, lowered, name.removesuffix(".c"), temp))

    after = {p.relative_to(ROOT).as_posix(): digest(p) for p in paths}
    changed = [name for name in before if before[name] != after[name]]
    missing = [name for name in before if not (ROOT / name).exists()]
    if changed or missing:
        raise RuntimeError(f"proof inputs changed during run: changed={changed}, missing={missing}")
    report = {
        "schema": "simant-whole-program-asm-state-proof-v2",
        "claim": "FIXED_SOURCE_DERIVED_DIAGNOSTIC_ONLY: immutable historical source/layout pins, exact consumer declarations, single-owner symbol canonicalization, and compile-only checks",
        "plan_path": PLAN_PATH.relative_to(ROOT).as_posix(),
        "plan_sha256": digest(PLAN_PATH),
        "parent_receipt": plan["parent_receipt"],
        "historical_migration_identity": plan["historical_migration_identity"],
        "uses_live_migration": False,
        "input_hashes_before": before,
        "input_hashes_after": after,
        "input_count": len(before),
        "unchanged_input_count": len(before),
        "controls": controls,
        "compile": {"compiler": str(compiler), "compiler_sha256": digest(compiler),
                    "version": version, "units": compile_results,
                    "translation_unit_count": len(compile_results), "execution_claim": False},
        "boundaries": {"alias_rewrite_count": len(plan["alias_rewrites"]),
                       "provider_scalar_count": len(plan["asm_scalars"]),
                       "lexical_pass_count_per_tu": 1,
                       "table_base_rewritten": False,
                       "storage_owners_created": 0,
                       "runtime_or_link_claim": False},
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with report_path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(report, stream, indent=2)
        stream.write("\n")
    return report


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()
    result = run(args.report)
    print(json.dumps({"inputs": result["input_count"],
                      "aliases": result["boundaries"]["alias_rewrite_count"],
                      "provider_scalars": result["boundaries"]["provider_scalar_count"],
                      "compiled_units": result["compile"]["translation_unit_count"],
                      "report": str(args.report)}))
