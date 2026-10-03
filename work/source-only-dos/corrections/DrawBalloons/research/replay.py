"""Re-run the immutable render_small_v1 DrawBalloons suite from staged inputs.

This module is called only by DrawBalloons-correction-research.py. It writes
all objects, ledgers, and reports under the fresh ignored scratch directory.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


def load_suite(path: Path):
    spec = importlib.util.spec_from_file_location("drawballoons_staged_suite", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load staged suite: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def run(repo: Path, scratch: Path, suite_path: Path, source_path: Path) -> dict:
    sys.path.insert(0, str(repo / "tools"))
    import behavior

    suite = load_suite(suite_path)
    if suite.SUITE != "render_small_v1":
        raise RuntimeError(f"unexpected suite id: {suite.SUITE}")
    outdir = scratch / "replay"
    outdir.mkdir(parents=True, exist_ok=False)
    suite._run_target("DrawBalloons", suite.balloon_cases, 1000, 0xBEEF,
                      outdir, source=source_path)

    summary_path = outdir / "DrawBalloons.json"
    evidence_path = outdir / "DrawBalloons.run-evidence.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    expected = {"cases_generated": 1009, "cases_run": 1009, "mismatches": 0}
    for key, value in expected.items():
        if summary.get(key) != value:
            raise AssertionError(f"replay {key}: {summary.get(key)!r}, expected {value!r}")
    if evidence.get("completion") != "COMPLETE" or evidence.get("errors") != 0:
        raise AssertionError("replay run evidence is not complete and error-free")
    if evidence.get("peer_data_gates") != "PASS":
        raise AssertionError("whole-module peer/private-data gate did not pass")
    if summary.get("source_sha256") != evidence["identity"]["source_sha256"]:
        raise AssertionError("replay summary and run evidence source hashes differ")
    return {
        "status": "PASS",
        "suite_id": suite.SUITE,
        "suite_sha256": behavior.digest(suite_path.read_bytes()),
        "source_sha256": summary["source_sha256"],
        "candidate_object_sha256": summary["object_sha256"],
        "linked_code_sha256": summary["linked_code_sha256"],
        "oracle_sha256": summary["oracle_sha256"],
        "historical_manifest_sha256": summary["manifest_sha256"],
        "profile": summary["profile"],
        "flags": summary["flags"],
        "cases_generated": summary["cases_generated"],
        "cases_run": summary["cases_run"],
        "directed_cases": summary["directed_cases"],
        "randomized_cases": summary["randomized_cases"],
        "seed": summary["seed"],
        "mismatches": summary["mismatches"],
        "peer_data_gates": evidence["peer_data_gates"],
        "case_ledger_sha256": summary["case_ledger"]["sha256"],
        "run_evidence_sha256": behavior.digest(evidence_path.read_bytes()),
        "candidate_strict": summary["candidate_strict"],
    }
