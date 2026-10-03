"""RESEARCH_ONLY reproducibility runner for the admitted DrawBalloons fix.

This wrapper stages the admitted whole-module source and immutable archived
suite dependencies into a new ignored build/ scratch directory, compiles from
those staged sources, and runs the archived differential and width probes.
The original EXE is used only as a separate research oracle by PreparedPair;
it is never a source-only build input. This script writes no admission,
registry, canonical source, or promotion metadata.

Run from any working directory with the repository Python environment:

    python work/source-only-dos/DrawBalloons-correction-research.py
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import shutil
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ARCHIVE = ROOT / "evidence/behavior/harnesses/render-small-d25a35e5-20261002"
CORRECTION = ROOT / "work/source-only-dos/corrections/DrawBalloons"
RECEIPT_PATH = ROOT / "work/source-only-dos/static-completeness/DrawBalloons.json"
SUITE_REL = "evidence/behavior/harnesses/render-small-d25a35e5-20261002/runs/DrawBalloons/suite.py"
BEHAVIOR_REL = "evidence/behavior/harnesses/render-small-d25a35e5-20261002/tools/behavior.py"
LEDGER_REL = "evidence/behavior/harnesses/render-small-d25a35e5-20261002/tools/behavior_ledger.py"
MEMORY_REL = "evidence/behavior/harnesses/render-small-d25a35e5-20261002/tools/behavior_suites/memory.py"
ARCHIVE_INDEX_REL = "evidence/behavior/harnesses/render-small-d25a35e5-20261002/archive-index.json"
EXPECTED = {
    "source": "e222bc77fd4d83a777507a8ba73aa2c0ba6dd4d6fc4cb42db69cd83f6374c920",
    "suite": "d25a35e5a516d8f490bec1678e583c3a449c648b0a105a7bc32d3734841230df",
    "behavior": "2c0799048057f59eae61a48be4d695278635594484adf0c70bf46c51b4e0c799",
    "ledger": "6788ec00f1c02fd93d98b96b4c8d61d2b704c97308b2c3f4024bc3095e76395f",
    "memory": "927127a445081a032eb76b94e09b2f5e1aa712a659d95b2363f419fbe496b970",
    "manifest": "025a0a9255d910cae4b122ab5a3f3fb40888bb456d7fe42158db7c9e622fcf50",
    "oracle": "aa0596c6766322a8229ee3c36e57048c92adc82d50fbe2ef37afb8b85fcf4f11",
    "archive_index": "95bba78d7290d0c888c06011bd0b0d917a7b5f3f59c48744667e70be2e49f25e",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def json_default(value):
    if isinstance(value, bytes):
        return value.hex()
    raise TypeError(f"not JSON serializable: {type(value).__name__}")


def require_hash(path: Path, expected: str, label: str) -> str:
    if not path.is_file():
        raise FileNotFoundError(f"required pinned input missing: {path}")
    actual = sha(path)
    if actual != expected:
        raise RuntimeError(f"{label} SHA256 {actual} does not match expected {expected}")
    return actual


def load_helper(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load research helper {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def main() -> int:
    if not RECEIPT_PATH.is_file():
        raise FileNotFoundError(f"admitted receipt not found: {RECEIPT_PATH}")
    receipt = json.loads(RECEIPT_PATH.read_text(encoding="utf-8"))
    if receipt.get("schema") != "simant-dos-strict-static-review-v1" or receipt.get("status") != "BEHAVIOR_EXACT_CONFIRMED":
        raise RuntimeError("DrawBalloons admitted strict-static receipt is missing or not confirmed")
    audit = receipt["audit"]
    source_meta = audit["source"]
    source_path = ROOT / source_meta["path"]
    source_sha = require_hash(source_path, source_meta["sha256"], "admitted corrected source")
    if source_sha != EXPECTED["source"]:
        raise RuntimeError("admitted source pin changed from the reviewed research input")

    # The archived test inputs and execution engine are taken from the
    # immutable evidence snapshot. Check each against both its known run pin
    # and, where present, the admitted strict receipt.
    input_pins = {item["path"]: item["sha256"] for item in audit.get("inputs", [])}
    archived_specs = [
        (SUITE_REL, EXPECTED["suite"], "suite"),
        (BEHAVIOR_REL, EXPECTED["behavior"], "behavior engine"),
        (LEDGER_REL, EXPECTED["ledger"], "case ledger dependency"),
        (MEMORY_REL, EXPECTED["memory"], "Ralloc memory fixture"),
    ]
    immutable_inputs = []
    for rel, expected, label in archived_specs:
        path = ROOT / rel
        receipt_hash = input_pins.get(rel)
        if receipt_hash != expected:
            raise RuntimeError(f"admitted receipt has no matching pin for {rel}")
        immutable_inputs.append({"path": rel, "sha256": require_hash(path, expected, label)})
    immutable_inputs.append({
        "path": ARCHIVE_INDEX_REL,
        "sha256": require_hash(ROOT / ARCHIVE_INDEX_REL, EXPECTED["archive_index"],
                               "immutable archive index"),
    })

    repo_behavior = ROOT / "tools/behavior.py"
    require_hash(repo_behavior, EXPECTED["behavior"], "imported behavior engine")
    archive_index_path = ROOT / ARCHIVE_INDEX_REL
    require_hash(archive_index_path, EXPECTED["archive_index"], "immutable archive index")
    archive_index = json.loads(archive_index_path.read_text(encoding="utf-8"))
    tool_pins = []
    for component in archive_index.get("component_archive", []):
        rel = component.get("component", "")
        if rel.startswith("tools/") or rel.startswith("layout/"):
            tool_pins.append({"path": rel,
                              "sha256": require_hash(ROOT / rel, component["sha256"],
                                                     f"archived runtime dependency {rel}")})
    manifest_hash = require_hash(ROOT / "layout/manifest.json", EXPECTED["manifest"],
                                  "historical manifest")

    sys.path.insert(0, str(ROOT / "tools"))
    import behavior
    if behavior.digest(repo_behavior.read_bytes()) != EXPECTED["behavior"]:
        raise RuntimeError("runtime behavior import is not the immutable archived engine")
    original_exe_hash = behavior.exe.load().sha256
    if original_exe_hash != EXPECTED["oracle"]:
        raise RuntimeError(f"oracle image SHA256 {original_exe_hash} does not match admitted pin")

    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:10]
    scratch_root = ROOT / "build/source-only-dos-research/DrawBalloons"
    scratch_root.mkdir(parents=True, exist_ok=True)
    scratch = scratch_root / run_id
    scratch.mkdir(parents=False, exist_ok=False)

    staged_source = scratch / "source/module.c"
    staged_source.parent.mkdir(parents=True, exist_ok=False)
    shutil.copyfile(source_path, staged_source)
    if sha(staged_source) != source_sha:
        raise RuntimeError("staged source copy does not preserve the admitted source hash")

    suite_dir = scratch / "immutable-suite/runs/DrawBalloons"
    deps_dir = suite_dir / "deps/behavior_suites"
    deps_dir.mkdir(parents=True, exist_ok=False)
    archived_tools_dir = scratch / "immutable-suite/tools"
    archived_tools_dir.mkdir(parents=True, exist_ok=False)
    staged_suite = suite_dir / "suite.py"
    staged_ledger = suite_dir / "deps/behavior_ledger.py"
    staged_memory = deps_dir / "memory.py"
    staged_behavior = archived_tools_dir / "behavior.py"
    staged_archive_index = scratch / "immutable-suite/archive-index.json"
    shutil.copyfile(ROOT / SUITE_REL, staged_suite)
    shutil.copyfile(ROOT / LEDGER_REL, staged_ledger)
    shutil.copyfile(ROOT / MEMORY_REL, staged_memory)
    shutil.copyfile(ROOT / BEHAVIOR_REL, staged_behavior)
    shutil.copyfile(ROOT / ARCHIVE_INDEX_REL, staged_archive_index)
    staged_inputs = [
        {"path": "immutable-suite/runs/DrawBalloons/suite.py", "sha256": sha(staged_suite)},
        {"path": "immutable-suite/runs/DrawBalloons/deps/behavior_ledger.py", "sha256": sha(staged_ledger)},
        {"path": "immutable-suite/runs/DrawBalloons/deps/behavior_suites/memory.py", "sha256": sha(staged_memory)},
        {"path": "immutable-suite/tools/behavior.py", "sha256": sha(staged_behavior)},
        {"path": "immutable-suite/archive-index.json", "sha256": sha(staged_archive_index)},
    ]
    if [x["sha256"] for x in staged_inputs] != [EXPECTED["suite"], EXPECTED["ledger"], EXPECTED["memory"], EXPECTED["behavior"], EXPECTED["archive_index"]]:
        raise RuntimeError("staged suite or dependencies differ from immutable archive pins")

    helpers = CORRECTION / "research"
    replay_helper = helpers / "replay.py"
    probes_helper = helpers / "probes.py"
    replay_module = load_helper(replay_helper, "drawballoons_research_replay")
    probes_module = load_helper(probes_helper, "drawballoons_research_probes")

    replay = replay_module.run(ROOT, scratch, staged_suite, staged_source)
    probes = probes_module.full_probes(ROOT, scratch, staged_source, staged_suite)
    if replay["source_sha256"] != source_sha or probes["status"] != "PASS":
        raise RuntimeError("research result source pin or probe status mismatch")

    report = {
        "schema": "drawballoons-correction-reproducibility-v1",
        "status": "RESEARCH_ONLY_PASS",
        "run_id": run_id,
        "scratch": scratch.relative_to(ROOT).as_posix(),
        "scope": "Research replay only. The pinned original EXE was executed only as the separate oracle in PreparedPair; it was not supplied as source-only build input. No admission metadata or canonical source was modified.",
        "admitted_source": {"path": source_meta["path"], "sha256": source_sha,
                            "staged_path": staged_source.relative_to(ROOT).as_posix()},
        "immutable_harness_inputs": immutable_inputs,
        "staged_harness_inputs": staged_inputs,
        "runtime_engine": {"path": "tools/behavior.py",
                           "sha256": EXPECTED["behavior"],
                           "archive_sha256": EXPECTED["behavior"],
                           "archive_bytes_equal_to_imported_engine": True,
                           "admitted_tool_dependency_pins_verified": len(tool_pins),
                           "tool_dependencies": tool_pins},
        "compiler_context": {"profile": "msc600ax", "flags": ["/AL", "/Os", "/Oe", "/Og", "/Zi"],
                             "manifest_sha256": manifest_hash},
        "oracle": {"purpose": "separate behavioral comparison oracle only",
                   "sha256": original_exe_hash},
        "research_helpers": {
            "wrapper_sha256": sha(Path(__file__).resolve()),
            "replay_sha256": sha(replay_helper),
            "probes_sha256": sha(probes_helper),
        },
        "replay_1009": replay,
        "expression_width_and_queue_probes": probes,
    }
    report_path = scratch / "research-report.json"
    report_path.write_text(json.dumps(report, indent=2, default=json_default) + "\n",
                           encoding="utf-8")
    report["report_sha256"] = sha(report_path)
    # Keep the report self-contained with its own hash in a sidecar so the
    # report's hash is not recursively embedded in itself.
    (scratch / "research-report.sha256").write_text(report["report_sha256"] + "\n",
                                                     encoding="ascii")
    print(json.dumps({
        "status": report["status"],
        "scratch": report["scratch"],
        "report": report_path.relative_to(ROOT).as_posix(),
        "report_sha256": report["report_sha256"],
        "replay": {"cases": replay["cases_run"], "mismatches": replay["mismatches"],
                   "candidate_object_sha256": replay["candidate_object_sha256"]},
        "expression_verified": probes["expression_boundary"]["verified"],
        "width_cases": len(probes["full_function_width_boundary"]["cases"]),
        "queue_alias_cases": len(probes["queue_alias"]["cases"]),
        "queue_alias_all_equal": probes["queue_alias"]["all_equal"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
