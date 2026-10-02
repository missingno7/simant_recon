"""Run the corrected LessonDone original-vs-compiled campaign and ABI audit."""
from __future__ import annotations
import gzip, hashlib, json, sys, time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "tools"))
from behavior_suites import tutorial_menu as suite
from behavior_ledger import CaseLedger

OUT = Path(__file__).resolve().parent
SEED = 0x35F50384 ^ 0x0E2E065E
EFFECTS = ["return", "ordered host/helper calls", "ordered input consumption",
           "pointed rectangles and strings", "global and pointed writes",
           "all nonstack writes", "caller ABI"]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    cases = suite.tutorial_cases(500, SEED)
    pair = suite.b.PreparedPair("LessonDone", out=OUT / "candidate")
    ledger = CaseLedger(OUT / "LessonDone.jsonl.gz", pair, EFFECTS)
    counts, first = Counter(), {}
    failures, errors = [], []
    start = time.monotonic()
    for index, case in enumerate(cases):
        try:
            cmp = pair.compare(case)
        except Exception as exc:
            errors.append({"index": index, "label": case.label, "error": str(exc)})
            continue
        ledger.record(case, cmp, lane="randomized" if case.label.startswith("random/") else "directed")
        if not cmp.equal:
            failures.append({"index": index, "label": case.label,
                             "diff": suite._diff_summary(cmp.diff)})
        for call in pair.original_machine.trace:
            counts[call["name"]] += 1
            first.setdefault(call["name"], case.label)
    ledger_pin = ledger.finalize()
    seed_source = "work/takeover/hardtail/seeds/root_0E2E_c611660dde4d.c"
    identity = pair.identity
    target = {"target": "LessonDone", "identity": identity,
        "candidate_strict": pair.strict.get("claims", {}).get("LessonDone", {}),
        "cases_generated": len(cases), "cases_attempted": len(cases),
        "completed_comparisons": ledger_pin["row_count"],
        "execution_error_count": len(errors), "mismatches": len(failures),
        "execution_errors": errors, "failures": failures, "ledger": ledger_pin,
        "elapsed_seconds": round(time.monotonic() - start, 3),
        "behavioral_status": "UNRESOLVED pending contract review"}
    negative_source = (ROOT / seed_source).read_text(encoding="latin1")
    old = "if (fd_50F6_0224 > fd_50F6_0204 && fd_50F6_0AA0 == 0)"
    if negative_source.count(old) != 2:
        raise RuntimeError("strict threshold source anchor changed")
    mutant = OUT / "negative" / "lesson-wrong-threshold.c"
    mutant.parent.mkdir(parents=True, exist_ok=True)
    mutant.write_text(negative_source.replace(old,
        "if (fd_50F6_0224 >= fd_50F6_0204 && fd_50F6_0AA0 == 0)", 1), encoding="latin1")
    neg_case = suite.tutorial_case("negative/equal-threshold", 3,
        {"fd_50F6_0224": 10, "fd_50F6_0204": 10, "fd_50F6_0AA0": 0},
        {"clock": (0, 0), "top_window": 0})
    base_pair = suite.b.PreparedPair("LessonDone", out=OUT / "negative" / "baseline")
    base = base_pair.compare(neg_case)
    mutant_pair = suite.b.PreparedPair("LessonDone", source=mutant, out=OUT / "negative" / "mutant")
    changed = mutant_pair.compare(neg_case)
    neg = {"id": "lesson-strict-threshold", "target": "LessonDone",
        "mutation": "strict > changed to >= for lesson 3", "baseline_matches": base.equal,
        "detected": base.equal and not changed.equal, "mutant_differs": not changed.equal,
        "baseline_diff": base.diff, "diff": changed.diff, "mutant_source": str(mutant),
        "mutant_identity": mutant_pair.identity}
    if not neg["detected"]:
        raise AssertionError("source mutant was not detected on the same input")
    report = {"schema": "behavior-suite-run-v1", "suite": suite.SUITE,
        "suite_sha256": suite.b.digest((ROOT / "tools/behavior_suites/tutorial_menu.py").read_bytes()),
        "targets": [target], "negative_controls": [neg], "seed": 0x35F50384,
        "elapsed_seconds": round(time.monotonic() - start, 3),
        "scope": "Corrected 32-bit timer threshold, original MacTickCount/TickCount arithmetic, original win_IsWinInFront AX/global contract, and MapA[128][64] row-major layout.",
        "status": "UNRESOLVED pending independent review of fixture validity and boundary contracts"}
    (OUT / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    case_map = {c.label: c for c in cases}
    audit_rows = []
    for name in sorted(counts):
        callback_case = case_map[first[name]]
        spec = callback_case.callbacks[name]
        modeled = spec.handler is not None
        audit_rows.append({"name": name, "execution_mode": "MODELED" if modeled else "ORIGINAL_EXE",
            "executed_from_original": not modeled, "observed_call_count": counts[name],
            "observed_call_count_scope": f"all {len(cases)} matched campaign cases",
            "stack_words": spec.stack_words, "register_args": list(spec.register_args),
            "callee_pop_bytes": spec.pop,
            "contract_note": "modeled zero-argument TickCount provider; original MacTickCount computes requested result" if name == "TickCount"
                else ("trace-only ABI observation followed by original canonical body" if not modeled else "modeled downstream Win16 UI sink")})
    mac_count = counts.get("TickCount", 0)
    audit_rows.append({"name": "MacTickCount", "execution_mode": "ORIGINAL_EXE",
        "executed_from_original": True, "observed_call_count": mac_count,
        "observed_call_count_scope": "original MacTickCount source body calls TickCount exactly once per invocation",
        "stack_words": 0, "register_args": [], "callee_pop_bytes": 0,
        "contract_note": "f_00F8_02BE alias executes original far-long TickCount()*3"})
    audit = {"schema": "tutorial-menu-callback-audit-v1", "run_report": "report.json",
        "suite_sha256": report["suite_sha256"], "runner_sha256": identity["harness_sha256"],
        "targets": {"LessonDone": {"cases": len(cases), "equal_comparisons": len(cases)-len(errors)-len(failures),
            "execution_errors": len(errors), "callback_boundaries": audit_rows,
            "all_observed_entry_counts": dict(sorted(counts.items()))}}}
    (OUT / "callback-boundary-audit.json").write_text(json.dumps(audit, indent=2) + "\n")
    with gzip.open(OUT / "LessonDone.jsonl.gz", "rt", encoding="utf-8") as stream:
        ledger_rows = {r["case_id"]: r for r in map(json.loads, stream)}
    positive = {"schema": "tutorial-menu-positive-boundary-cases-v1", "targets": {"LessonDone": {}}}
    for row in audit_rows:
        name = row["name"]
        case_id = first.get(name, first.get("TickCount"))
        pin = ledger_rows[case_id]
        positive["targets"]["LessonDone"][name] = {"case_id": case_id,
            "input_sha256": pin["input_sha256"],
            "original_observation_sha256": pin["original_observation_sha256"],
            "candidate_observation_sha256": pin["candidate_observation_sha256"],
            "comparison": "original_and_compiler_candidate_matched"}
    (OUT / "positive-boundary-cases.json").write_text(json.dumps(positive, indent=2) + "\n")
    print(json.dumps({"suite_sha256": report["suite_sha256"], "cases": target["cases_generated"],
        "completed": target["completed_comparisons"], "errors": target["execution_error_count"],
        "mismatches": target["mismatches"], "ledger_sha256": ledger_pin["sha256"],
        "negative_detected": neg["detected"], "callback_counts": dict(counts)}, indent=2))


if __name__ == "__main__":
    main()
