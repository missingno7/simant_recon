"""Prove the post-reviewed-overlay spider owner repair against the real pipeline."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
import sys
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from portable.tools.whole_program import reviewed_overlays
from portable.whole_program.conversions.spider_inline_source import SOURCE_RELATIVE, adapt
from portable.whole_program.conversions.spider_inline_reviewed import adapt_reviewed

CATALOG = "portable/research/whole_program_behavior_sources.json"
REPORT = Path(__file__).parent / "evidence" / "reviewed-overlay-adapt-v2.json"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def input_closure(gcc: str) -> dict[str, str]:
    catalog = json.loads((ROOT / CATALOG).read_text(encoding="utf-8"))
    paths = {
        SOURCE_RELATIVE,
        CATALOG,
        "portable/tools/whole_program.py",
        "portable/whole_program/conversions/spider_inline_source.py",
        "portable/whole_program/conversions/spider_inline_reviewed.py",
        "portable/whole_program/algorithms/line16b5.h",
        "portable/tests/spider_inline_source/test_reviewed_overlay.py",
    }
    paths.update(entry["reviewed_tested_source"]["path"] for entry in catalog["entries"]
                 if entry["canonical_translation_unit"]["path"] == SOURCE_RELATIVE)
    result = {p: sha((ROOT / p).read_bytes()) for p in sorted(paths)}
    result["compiler_executable"] = sha(Path(gcc).read_bytes())
    return result


def main() -> int:
    if REPORT.exists():
        raise SystemExit(f"refusing to overwrite {REPORT}")
    raw = (ROOT / SOURCE_RELATIVE).read_bytes()
    pre_overlay, base_receipt = adapt(raw, SOURCE_RELATIVE)
    entries = json.loads((ROOT / CATALOG).read_text(encoding="utf-8"))["entries"]
    pipeline_source, pipeline_rows = reviewed_overlays(
        ROOT / SOURCE_RELATIVE, pre_overlay.decode("utf-8"), entries)
    if len(pipeline_rows) != 3:
        raise SystemExit("actual overlay pipeline did not select all three root:m0250 bodies")
    if pipeline_source.count("fd_50F6_1F26") != 2:
        raise SystemExit("expected the DrawBalloons overlay to restore exactly two identifiers")
    if pipeline_source.count("portable_line16b5_source_buffer") != 14:
        raise SystemExit("expected 14 existing converted references before reviewed repair")

    repaired, receipt = adapt_reviewed(pipeline_source, SOURCE_RELATIVE)
    if receipt.reintroduced_active_references != 2 or receipt.resulting_owner_references != 16:
        raise SystemExit("reviewed source reference ledger mismatch")
    if repaired != pre_overlay.decode("utf-8"):
        raise SystemExit("repaired overlay source differs from canonical pre-word adapter output")

    for altered_source, altered_route in (
        (pipeline_source + "\n", SOURCE_RELATIVE),
        (pipeline_source, "src/root/m0250-copy.c"),
        (pipeline_source.replace("fd_50F6_1F26", "fd_50F6_1F2A", 1), SOURCE_RELATIVE),
    ):
        try:
            adapt_reviewed(altered_source, altered_route)
        except ValueError:
            continue
        raise SystemExit("post-overlay negative control was accepted")

    gcc = shutil.which("gcc")
    if not gcc:
        raise SystemExit("gcc unavailable")
    before = input_closure(gcc)
    with tempfile.TemporaryDirectory(prefix="spider-reviewed-overlay-") as td:
        adapted_path = Path(td) / "m0250_reviewed.c"
        adapted_path.write_bytes(repaired.encode("utf-8"))
        command = [gcc, "-std=gnu11", "-Dfar=", "-Dnear=", "-fsyntax-only", "-w",
                   "-I", str(ROOT), str(adapted_path)]
        compiled = subprocess.run(command, text=True, capture_output=True)
        if compiled.returncode:
            raise SystemExit("repaired reviewed source syntax check failed\n" +
                             compiled.stdout + compiled.stderr)
    after = input_closure(gcc)
    if before != after:
        raise SystemExit("reviewed source/compiler closure changed during compile")

    report = {
        "schema": "spider-inline-reviewed-overlay-adapt-v1",
        "status": "pass",
        "frozen_source_sha256": base_receipt.source_sha256,
        "overlay_catalog_sha256": receipt.overlay_catalog_sha256,
        "overlay_rows": pipeline_rows,
        "incoming_post_overlay_sha256": receipt.incoming_reviewed_source_sha256,
        "repaired_pre_word_source_sha256": receipt.output_sha256,
        "repair": {"overlay_count": receipt.overlay_count,
                   "reintroduced_active_references": receipt.reintroduced_active_references,
                   "typed_owner_references": receipt.resulting_owner_references,
                   "owner": receipt.owner_symbol},
        "negative_controls": ["post-overlay byte drift", "wrong route", "reference anchor drift"],
        "compiler": {"path": gcc, "sha256": before["compiler_executable"]},
        "command": command,
        "compiler_stdout": compiled.stdout,
        "compiler_stderr": compiled.stderr,
        "closure_before": before,
        "closure_after": after,
    }
    data = json.dumps(report, indent=2, sort_keys=True).encode("utf-8") + b"\n"
    if REPORT.exists():
        raise SystemExit(f"refusing to overwrite {REPORT}")
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_bytes(data)
    print(f"PASS: real m0250 reviewed-overlays to spider owner repair; report_sha256={sha(data)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
