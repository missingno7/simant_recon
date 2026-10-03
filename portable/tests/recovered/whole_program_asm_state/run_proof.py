#!/usr/bin/env python3
"""Focused controls and immutable provenance for ASM/C shared-state aliases."""
from __future__ import annotations

import copy
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "portable/tools"))
import asm_state_provider as asm_provider  # noqa: E402
import source_state_aliases as aliases_mod  # noqa: E402

EVIDENCE = ROOT / "portable/tests/recovered/evidence/whole-program-asm-state-v1"
DEFAULT_REPORT = EVIDENCE / "report.json"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def local_dependencies(migration: dict, alias_rows: list[dict]) -> list[Path]:
    paths = {
        ROOT / "portable/tools/asm_state_provider.py",
        ROOT / "portable/tools/source_state_aliases.py",
        ROOT / "portable/tests/recovered/whole_program_asm_state/run_proof.py",
        ROOT / "portable/whole_program/state/asm_shared_state.c",
        ROOT / "portable/whole_program/state/asm_shared_state.h",
        ROOT / "src/root/m195A.asm", ROOT / "src/root/m0250.c", ROOT / "src/root/m15F8.c",
        ROOT / "layout/manifest.json", ROOT / "layout/symbols.json",
        ROOT / "build/workers/whole_program/generated/migration.json",
    }
    for row in alias_rows:
        contract = migration["unprovided_symbol_contracts"].get(row["alias"], {})
        for rel in contract.get("required_by", []):
            paths.add(ROOT / rel)
    for rel in ("src/S04/m35F5.c", "src/S05/m35F5.c", "src/S22/m39C7.c",
                "src/S22/m3BBD.c", "src/root/m15D9.c", "src/S20/m39F1.c"):
        paths.add(ROOT / rel)
    for row in migration["modules"]:
        if row["source"] in {"src/root/m0250.c", "src/root/m15F8.c", "src/root/m15D9.c",
                              "src/S04/m35F5.c", "src/S05/m35F5.c", "src/S22/m39C7.c",
                              "src/S22/m3BBD.c", "src/S20/m39F1.c"}:
            paths.add(ROOT / row["generated"])
    return sorted(paths)


def compiler_path() -> Path:
    found = shutil.which("gcc")
    if not found:
        raise RuntimeError("GCC is required for native syntax controls")
    return Path(found).resolve()


def compile_source(cc: Path, source: str, name: str, temp: Path) -> dict:
    c_path = temp / f"{name}.c"
    o_path = temp / f"{name}.o"
    c_path.write_text(source, encoding="utf-8", newline="\n")
    command = [str(cc), "-std=c11", "-fsigned-char", "-fno-builtin", "-I", str(ROOT),
               "-I", str(ROOT / "portable/whole_program/state"),
               "-I", str(ROOT / "build/workers/whole_program/generated"),
               "-Werror=implicit-function-declaration", "-c", str(c_path), "-o", str(o_path)]
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    if result.returncode != 0:
        raise AssertionError(f"native syntax control failed for {name}:\n{result.stdout}{result.stderr}")
    return {"command": command, "returncode": result.returncode,
            "object_sha256": digest(o_path), "object_size": o_path.stat().st_size}


def run(report_path: Path) -> dict:
    if report_path.exists():
        raise FileExistsError(f"immutable report already exists: {report_path}")
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    migration = json.loads(asm_provider.DEFAULT_MIGRATION.read_text(encoding="utf-8"))
    alias_rows = aliases_mod.collect_aliases()
    input_paths = local_dependencies(migration, alias_rows)
    before = {p.relative_to(ROOT).as_posix(): digest(p) for p in input_paths}
    controls = []

    # Positive ASM control: three PUBLIC scalar initializers resolve to their
    # exact accepted OMF addresses and current missing shared-state contracts.
    scalar_rows = asm_provider.collect(asm_provider.DEFAULT_MIGRATION)
    require(len(scalar_rows) == 3, "expected exactly three bounded EMS scalar providers")
    controls.append({"name": "asm_public_scalar_positive", "passed": True,
                     "names": [r["name"] for r in scalar_rows],
                     "addresses": {r["name"]: r["computed_address"] for r in scalar_rows}})

    # Negative ASM controls: reject an unsupported far-pointer slot and reject
    # a byte declaration when the candidate contract requires a DOS word.
    asm_text = (ROOT / "src/root/m195A.asm").read_text(encoding="utf-8")
    parsed_asm = {r["name"]: r for r in asm_provider.scan_data_declarations(asm_text)}
    require(parsed_asm["fd_55B3_360E"]["directive"] == "dd", "far pointer width evidence changed")
    original = asm_provider.REVIEWED_SCALARS["fd_55B3_3612"]
    try:
        asm_provider.REVIEWED_SCALARS["fd_55B3_3612"] = {"directive": "db", "ctype": "int8_t", "size": 1}
        try:
            asm_provider.collect(asm_provider.DEFAULT_MIGRATION)
            raise AssertionError("negative directive-width control was accepted")
        except ValueError as exc:
            require("expected db, found dw" in str(exc), "negative width failed for an unrelated reason")
    finally:
        asm_provider.REVIEWED_SCALARS["fd_55B3_3612"] = original
    controls.append({"name": "asm_pointer_and_width_negative", "passed": True,
                     "excluded_pointer": "fd_55B3_360E", "observed_directive": "dd",
                     "wrong_width_rejected": True})

    # Negative source alias control: accepted PUBLIC address is mandatory.
    original_alias = aliases_mod.SCALAR_ALIASES["fd_55B3_19C0"]
    try:
        aliases_mod.SCALAR_ALIASES["fd_55B3_19C0"] = ("g_19C0", "int", "root:0250", 6594)
        try:
            aliases_mod.collect_aliases()
            raise AssertionError("negative OMF-address control was accepted")
        except ValueError as exc:
            require("source/accepted address mismatch" in str(exc), "negative alias failed for unrelated reason")
    finally:
        aliases_mod.SCALAR_ALIASES["fd_55B3_19C0"] = original_alias
    controls.append({"name": "c_data_alias_address_negative", "passed": True,
                     "changed_expected_offset": 6594, "rejected": True})

    # Transformation control: canonicalize only extern views and identifier
    # references, preserving comments, strings, statement ordering, and owner count.
    sample = (ROOT / "src/S20/m39F1.c").read_text(encoding="utf-8")
    transformed, trace = aliases_mod.transform(sample, alias_rows)
    require("extern char * fd_55B3_1CD4[];" in transformed,
            "pointer-table prototype did not reconcile to canonical owner")
    require("open((fd_55B3_1CD4[4]), 0)" in transformed and "msg = (fd_55B3_1CD4[3]);" in transformed,
            "pointer-table slot use did not resolve to indices 4 and 3")
    require('"SimAnt configuration file missing"' not in sample or
            '"SimAnt configuration file missing"' in transformed,
            "string literal was altered")
    require(trace["storage_owners_created"] == 0 and trace["control_flow_preserved"],
            "transform created storage or changed control-flow scope")
    controls.append({"name": "canonical_alias_transform_positive", "passed": True,
                     "rewritten_alias_count": len(trace["rewrites"]),
                     "storage_owners_created": 0,
                     "table_slot_uses": [3, 4]})

    compiler = compiler_path()
    version = subprocess.run([str(compiler), "--version"], capture_output=True,
                             text=True, check=True).stdout.splitlines()[0]
    compile_rows = []
    with tempfile.TemporaryDirectory(prefix="simant-asm-state-") as temp_raw:
        temp = Path(temp_raw)
        compile_rows.append(compile_source(compiler,
            (ROOT / "portable/whole_program/state/asm_shared_state.c").read_text(encoding="utf-8"),
            "asm_shared_state", temp))
        # Compile full converted consumer TUs after the remap. No link/execution
        # claim: this confirms declaration/type consistency only.
        for rel, generated in (("src/root/m15D9.c", "build/workers/whole_program/generated/root_m15D9.c"),
                               ("src/S04/m35F5.c", "build/workers/whole_program/generated/S04_m35F5.c"),
                               ("src/S20/m39F1.c", "build/workers/whole_program/generated/S20_m39F1.c")):
            text = (ROOT / generated).read_text(encoding="utf-8")
            transformed_native, _ = aliases_mod.transform(text, alias_rows)
            compile_rows.append(compile_source(compiler, transformed_native,
                                                Path(rel).stem + "_aliases", temp))

    after = {p.relative_to(ROOT).as_posix(): digest(p) for p in input_paths}
    changed = [rel for rel in before if before[rel] != after[rel]]
    missing = [p.relative_to(ROOT).as_posix() for p in input_paths if not p.exists()]
    if changed or missing:
        raise RuntimeError(f"source closure changed during proof: changed={changed}, missing={missing}")
    report = {
        "schema": "simant-whole-program-asm-state-proof-v1",
        "claim": "SOURCE_DERIVED_DIAGNOSTIC_ONLY: ASM scalar initialization and C DATA alias canonicalization; no integration/admission or runtime behavior claim",
        "input_hashes_before": before,
        "input_hashes_after": after,
        "current_input_changes": [],
        "input_count": len(before),
        "provider_state_count": len(scalar_rows),
        "canonical_alias_count": len(alias_rows),
        "canonical_storage_owners": sorted({r["storage_owner"] for r in alias_rows}),
        "controls": controls,
        "native_syntax_compile": {"compiler": str(compiler), "compiler_sha256": digest(compiler),
                                  "version": version, "translation_units": compile_rows,
                                  "execution_claim": False},
        "boundaries": {
            "asm_states": "Only PUBLIC literal scalar db/dw initializers whose parsed DGROUP offset plus accepted _DATA placement equals layout/symbols.json and migration views; three EMS scalar members.",
            "c_aliases": "Four current missing scalar views map to initialized m0250 canonical globals by DOS-width source declaration offsets; two pointer views map to slots 3 and 4 of the initialized five-entry m15F8 table.",
            "excluded": ["EMS far-pointer fd_55B3_360E (dd/far pointer unsupported)", "private ems_active", "graphics driver state", "font canvas/strides", "audio scheduler/resource voices", "input-owned state", "resolved aliases absent from current migration missing contracts"],
            "not_claimed": ["No executable link", "No DOS/native runtime comparison", "No provider selection in production build", "No pixel or resource-render equivalence"],
        },
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    # Immutable report: exclusive create prevents accidental overwrites.
    with report_path.open("x", encoding="utf-8", newline="\n") as f:
        json.dump(report, f, indent=2)
        f.write("\n")
    return report


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()
    result = run(args.report)
    print(json.dumps({"input_count": result["input_count"],
                      "provider_state_count": result["provider_state_count"],
                      "canonical_alias_count": result["canonical_alias_count"],
                      "compiler": result["native_syntax_compile"]["compiler"],
                      "report": str(args.report)}))
