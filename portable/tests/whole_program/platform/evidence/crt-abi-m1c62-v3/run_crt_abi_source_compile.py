#!/usr/bin/env python3
"""Whole-module compiler control for the CRT adapter's m1C62 source shape."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from portable.tools.whole_program import (  # noqa: E402
    convert_words, function_heads, reviewed_overlays,
)
from portable.whole_program.conversions.crt_abi import adapt  # noqa: E402


def identity(path: Path) -> dict:
    data = path.read_bytes()
    return {"sha256": hashlib.sha256(data).hexdigest(), "size": len(data)}


def main() -> int:
    gcc_name = shutil.which("gcc") or r"C:\msys64\mingw64\bin\gcc.exe"
    gcc = Path(gcc_name).resolve()
    if not gcc.is_file():
        raise SystemExit(f"GCC not found: {gcc}")
    source_path = ROOT / "src/root/m1C62.c"
    catalog_path = ROOT / "portable/research/whole_program_behavior_sources.json"
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))["entries"]
    relevant = [row for row in catalog if row["canonical_translation_unit"]["path"] ==
                "src/root/m1C62.c"]
    if [row["function"] for row in relevant] != ["f_1C62_0415"]:
        raise SystemExit("m1C62 reviewed-overlay closure changed; refresh the compile receipt")
    reviewed_path = ROOT / relevant[0]["reviewed_tested_source"]["path"]
    pinned = [
        source_path, catalog_path, reviewed_path,
        ROOT / "portable/tools/whole_program.py",
        ROOT / "portable/whole_program/conversions/crt_abi.py",
        ROOT / "portable/whole_program/platform/crt_abi.h",
        ROOT / "portable/whole_program/conversions/unprovided_state_v2.py",
        ROOT / "portable/whole_program/conversions/source_bounded_state.py",
        ROOT / "portable/tools/word_spelling.py",
        ROOT / "portable/tests/whole_program/platform/run_crt_abi_source_compile.py",
    ]
    before = {p.relative_to(ROOT).as_posix(): identity(p) for p in pinned}
    source = source_path.read_text(encoding="latin1")
    source, overlay_rows = reviewed_overlays(source_path, source, relevant)
    source, adapter_ledger = adapt(source, "src/root/m1C62.c")
    source, word_ledger = convert_words(source)
    if "if (sim_msc_ctype_is_lower_ascii((uint8_t)c))" not in source:
        raise SystemExit("direct _ctype if lost its required condition parentheses")
    if "switch ((sim_msc_ctype_is_lower_ascii((uint8_t)c)) ?" not in source:
        raise SystemExit("switch _ctype predicate did not retain source expression grouping")
    if re.search(r"\b(?:_ctype|sys_errlist|sys_nerr)\b", source):
        raise SystemExit("old CRT runtime symbol survived conversion")
    functions = function_heads(source)
    if len(functions) < 10 or not any(f["name"] == "f_1C62_0415" for f in functions):
        raise SystemExit("candidate is not the complete adapted m1C62 translation unit")
    compiler_flags = ["-std=c11", "-fsyntax-only", "-fno-builtin",
                      "-Werror=implicit-function-declaration", "-I", str(ROOT)]
    with tempfile.TemporaryDirectory(prefix="crt-abi-m1c62-") as td:
        work = Path(td)
        good_source = work / "m1C62-adapted.c"
        good_source.write_text(source, encoding="latin1")
        good_command = [str(gcc), *compiler_flags, str(good_source)]
        good = subprocess.run(good_command, cwd=ROOT, capture_output=True, text=True,
                              timeout=40)
        if good.returncode:
            raise SystemExit(f"adapted whole m1C62 compile failed:\n{good.stderr}")

        bad = source.replace("if (sim_msc_ctype_is_lower_ascii((uint8_t)c))",
                             "if sim_msc_ctype_is_lower_ascii((uint8_t)c)", 1)
        bad_source = work / "m1C62-omitted-parens-negative.c"
        bad_source.write_text(bad, encoding="latin1")
        bad_command = [str(gcc), *compiler_flags, str(bad_source)]
        negative = subprocess.run(bad_command, cwd=ROOT, capture_output=True, text=True,
                                  timeout=40)
        if negative.returncode == 0:
            raise SystemExit("malformed missing-parenthesis control unexpectedly compiled")

    after = {p.relative_to(ROOT).as_posix(): identity(p) for p in pinned}
    gcc_id = identity(gcc)
    if before != after:
        raise SystemExit("input source changed during compile control")
    report = {
        "schema": "simant-crt-m1c62-whole-module-compile-v3",
        "status": "PASS_ADAPTED_WHOLE_MODULE_SYNTAX_AND_NEGATIVE_CONTROL",
        "historical_oracle_claim": None,
        "conversion_order": ["reviewed_overlays", "crt_abi.adapt", "whole_program.convert_words"],
        "module_function_count": len(functions),
        "reviewed_overlay_rows": overlay_rows,
        "crt_adapter_ledger": adapter_ledger,
        "word_conversion_counts": word_ledger,
        "positive_command": good_command,
        "positive": {"returncode": good.returncode, "stdout": good.stdout,
                     "stderr": good.stderr},
        "negative_command": bad_command,
        "negative_missing_condition_parentheses": {"returncode": negative.returncode,
                                                     "diagnostics": negative.stderr},
        "compiler": {"path": str(gcc), "identity": gcc_id},
        "input_identities_before": before,
        "input_identities_after": after,
        "candidate_sha256": hashlib.sha256(source.encode("latin1")).hexdigest(),
        "scope": "complete m1C62 TU parser/compile control for adapter syntax; not linked behavior or DOS equivalence",
    }
    out = ROOT / "build/workers/behavior_memory/crt-abi-m1c62-source-compile-v3.json"
    if out.exists():
        raise SystemExit(f"refusing to overwrite {out}")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "functions": len(functions),
                      "report": str(out)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
