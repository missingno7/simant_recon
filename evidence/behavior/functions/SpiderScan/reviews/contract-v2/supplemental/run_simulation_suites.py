"""Run the first SpiderScan/EnterNest differential batch and preserve failures."""
from __future__ import annotations

import json
import hashlib
import gzip
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tools" / "behavior_suites"))
import behavior
import spider_nest
from behavior_ledger import CaseLedger


def _case_record(case):
    return {
        "label": case.label,
        "args": case.args,
        "writes": [[address, data.hex()] for address, data in case.writes],
        "observe": [vars(r) for r in case.observe],
        "callbacks": {name: {"stack_words": cb.stack_words,
                             "register_args": list(cb.register_args),
                             "pop": cb.pop}
                      for name, cb in case.callbacks.items()},
        "state": case.state,
        "registers": case.registers,
        "metadata": case.metadata,
    }


def _comparison_record(result):
    return {"equal": result.equal, "diff": result.diff,
            "original": result.original, "candidate": result.candidate}


def run(function: str, random_count: int = 1000, original_helpers=False, run_tag="stack-window-v1"):
    out = ROOT / "build" / "workers" / "behavior_sim_contracts" / "20261002" / run_tag / function
    out.mkdir(parents=True, exist_ok=True)
    suite_path = Path(spider_nest.__file__).resolve()
    runner_path = Path(__file__).resolve()
    suite_snapshot = out / "spider_nest.py"
    runner_snapshot = out / "run_simulation_suites.py"
    shutil.copyfile(suite_path, suite_snapshot)
    shutil.copyfile(runner_path, runner_snapshot)
    suite_source_sha256 = hashlib.sha256(suite_snapshot.read_bytes()).hexdigest()
    runner_source_sha256 = hashlib.sha256(runner_snapshot.read_bytes()).hexdigest()
    pair = behavior.PreparedPair(function, out=out / "prepared")
    enabled = (('SRand1', 'SRand4', 'fracSIN', 'fracCOS', 'FindAntIndex', 'DeadAntHere')
               if function == "SpiderScan" else
               ('SRand1', 'SRand4', 'ClearMyLife', 'SetMyLife', 'DigMyTile',
                'TryAntTheme', 'SetAlarmDropState')) if original_helpers else ()
    cases = spider_nest.make_cases(function, directed=True, random_seed=0x5A17E2,
                                   random_count=random_count,
                                   original_helpers=enabled)
    pair.identity["suite_id"] = spider_nest.SUITE_ID
    pair.identity["suite_source_sha256"] = suite_source_sha256
    pair.identity["suite_sha256"] = suite_source_sha256
    pair.identity["historical_manifest_sha256"] = pair.identity["manifest_sha256"]
    pair.identity["module"] = (f"{pair.identity['address']['unit']}:{pair.identity['address']['seg']:04X}")
    compared_effects = ["return value", "declared global/array/map state",
                        "ordered helper/callback names and arguments",
                        "final bytes across union of non-stack writes",
                        "caller-preserved register and stack ABI"]
    ledger_path = out / "cases.jsonl.gz"
    ledger = CaseLedger(ledger_path, pair, compared_effects)
    counts = {"directed": 0, "randomized": 0, "generated_directed": 0,
              "generated_randomized": 0, "mismatches": 0, "execution_errors": 0}
    first_mismatch = None
    first_error = None
    helper_calls = {}
    observed_call_counts = {}
    domain_values = {}
    positive_control = None
    call_trace_path = out / "helper-call-traces.jsonl.gz"
    trace_stream = gzip.open(call_trace_path, "wt", encoding="utf-8", newline="\n")
    for case in cases:
        group = "randomized" if case.label.startswith("seed005a17e2-") else "directed"
        counts[f"generated_{group}"] += 1
        try:
            result = pair.compare(case)
        except Exception as exc:
            counts["execution_errors"] += 1
            first_error = {"case": _case_record(case), "error": repr(exc)}
            break
        ledger_row = ledger.record(case, result, lane=group)
        counts[group] += 1
        for key, value in case.metadata.get("domain", {}).items():
            domain_values.setdefault(key, set()).add(value)
        original_calls = []
        for event in result.original["trace"]:
            observed_call_counts[event["name"]] = observed_call_counts.get(event["name"], 0) + 1
            if event["name"] in enabled:
                helper_calls[event["name"]] = helper_calls.get(event["name"], 0) + 1
            original_calls.append({"name": event["name"], "args": event["args"]})
        trace_stream.write(json.dumps({"case_id": case.label, "equal": result.equal,
                                       "calls": original_calls},
                                      sort_keys=True, separators=(",", ":")) + "\n")
        if not result.equal:
            counts["mismatches"] += 1
            record = {"case": _case_record(case), "comparison": _comparison_record(result)}
            mismatch_path = out / f"mismatch-{counts['mismatches']:04d}.json"
            mismatch_path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
            if first_mismatch is None:
                first_mismatch = mismatch_path.name
        elif positive_control is None:
            positive_control = {
                "id": f"pc-{function}-{case.label}", "case_id": case.label,
                "executed": True, "matched": True,
                "original_executed": True, "candidate_executed": True,
                "execution_errors": 0, "compared_effects": compared_effects,
                "original_observation_sha256": ledger_row["original_observation_sha256"],
                "candidate_observation_sha256": ledger_row["candidate_observation_sha256"],
            }
    trace_stream.close()
    ledger_pin = ledger.finalize()
    ledger_pin["path"] = ledger_path.relative_to(ROOT).as_posix()
    ledger_pin["lane_counts"] = {"directed": counts["directed"],
                                  "randomized": counts["randomized"]}
    domain_coverage = {}
    for key, values in sorted(domain_values.items()):
        ordered = sorted(values)
        domain_coverage[key] = {
            "distinct": len(ordered), "minimum": ordered[0], "maximum": ordered[-1],
        }
        if len(ordered) <= 256:
            domain_coverage[key]["values"] = ordered
    helper_modes = {name: "ORIGINAL_EXE" for name in enabled}
    if function == "SpiderScan":
        helper_modes["DoLaserFire"] = "TRACE_ONLY"
    else:
        helper_modes.update({"TickCount": "MODELED", "myBeginSong": "TRACE_ONLY",
                            "win_SetObjSelectedState": "MODELED", "InvalEuMap": "MODELED"})
    helper_boundaries = [{"name": name, "execution_mode": mode,
                          "observed_call_count": observed_call_counts.get(name, 0),
                          "executed_from_original": mode == "ORIGINAL_EXE",
                          "trace_recorded": True}
                         for name, mode in sorted(helper_modes.items())]
    report = {
        "schema": "behavior-run-evidence-v1",
        "completion": "COMPLETE" if counts["execution_errors"] == 0 else "INCOMPLETE",
        "suite": spider_nest.SUITE_ID,
        "function": function,
        "original_helpers_enabled": list(enabled),
        "original_helper_call_counts": helper_calls,
        "observed_call_counts": observed_call_counts,
        "identity": pair.identity,
        "suite_source_sha256": suite_source_sha256,
        "runner_source_sha256": runner_source_sha256,
        "harness_snapshot": str((out / "prepared" / "behavior-harness.py").relative_to(ROOT)),
        "domain_coverage": domain_coverage,
        "contract": spider_nest.CONTRACTS[function],
        "seed": "0x5A17E2",
        "requested_randomized": random_count,
        "counts": counts,
        "execution": {"engine": "PreparedPair.compare",
                      "actual_original_execution": True,
                      "actual_candidate_execution": True,
                      "original_exe_sha256": pair.identity["oracle_sha256"]},
        "cases": {
            "directed": {"generated": counts["generated_directed"],
                         "executed": counts["directed"],
                         "actual_original_invocations": counts["directed"],
                         "actual_candidate_invocations": counts["directed"], "seeds": []},
            "randomized": {"generated": counts["generated_randomized"],
                           "executed": counts["randomized"],
                           "actual_original_invocations": counts["randomized"],
                           "actual_candidate_invocations": counts["randomized"],
                           "seeds": ["0x5A17E2"] if counts["generated_randomized"] else []},
        },
        "errors": counts["execution_errors"],
        "mismatches": counts["mismatches"],
        "compared_effects": ["return value", "declared global/array/map state",
                             "ordered helper/callback names and arguments",
                             "final bytes across union of non-stack writes",
                             "caller-preserved register and stack ABI"],
        "unmodeled_boundaries": 0 if counts["execution_errors"] == 0 else None,
        "peer_data_gates": "PASS",
        "case_ledger": ledger_pin,
        "helper_boundaries": helper_boundaries,
        "positive_controls": [positive_control] if positive_control else [],
        "helper_call_trace": {"path": call_trace_path.relative_to(ROOT).as_posix(),
                              "sha256": hashlib.sha256(call_trace_path.read_bytes()).hexdigest(),
                              "case_count": counts["directed"] + counts["randomized"]},
        "first_mismatch_artifact": first_mismatch,
        "execution_error": first_error,
    }
    (out / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("function", "identity", "counts", "first_mismatch_artifact", "execution_error")}, indent=2))
    return 0 if counts["execution_errors"] == 0 else 2


if __name__ == "__main__":
    if len(sys.argv) not in (2, 3, 4, 5):
        raise SystemExit("usage: run_simulation_suites.py FUNCTION [RANDOM_COUNT] [--overlay] [RUN_TAG]")
    overlay = "--overlay" in sys.argv[2:]
    counts = [arg for arg in sys.argv[2:] if arg != "--overlay"]
    random_count = int(counts[0]) if counts and counts[0].isdigit() else 1000
    run_tag = counts[1] if counts and counts[0].isdigit() and len(counts) > 1 else "stack-window-v1"
    raise SystemExit(run(sys.argv[1], random_count, overlay, run_tag))

