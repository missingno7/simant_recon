"""Original-vs-reconstructed DOS acceptance at saved-game state boundaries.

Runs one scenario (dos/scenarios/*.json naming an emulated-time input script)
under the pinned acceptance DOSBox-X with fixed cycles and a fixed guest
clock, for the original oracle and for a reconstructed executable, then
compares every saved game byte for byte, reporting differing records by the
canonical S09 SaveRec schema. Input arrives at identical emulated times, so
any difference, including timer-derived fields, is a behavioural difference.

A PASS is a bounded observation for the recorded scenario; it is not closure
by itself and grants no acceptance outside that scenario.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from dos import build, diagnostic


def save_schema():
    """(index, offset, bytes, element size, name) from the canonical SaveRec table."""
    text = (ROOT / "src/S09/m35F5.c").read_text(encoding="latin1")
    start = re.search(r"struct SaveRec far fd_4E4B_0000\[\d+\] = \{", text).start()
    body = text[start:text.index("};", start)]
    rows, offset = [], 0
    for index, (size, count, data) in enumerate(
            re.findall(r"\{\s*([^,{}]+),\s*([^,{}]+),\s*([^{}]+?)\s*\}", body)):
        size, count = int(size, 0), int(count, 0)
        if count == 0:
            break
        name = re.sub(r"\(void far \*\)\s*&?", "", data).strip()
        rows.append((index, offset, size * count, size, name))
        offset += size * count
    return rows


def compare_saves(a: bytes, b: bytes) -> dict:
    schema = save_schema()
    total = schema[-1][1] + schema[-1][2]
    if len(a) != total or len(b) != total:
        return {"status": "SIZE_MISMATCH", "sizes": [len(a), len(b)], "schema_bytes": total}
    differences = []
    for index, offset, size, _, name in schema:
        x, y = a[offset:offset + size], b[offset:offset + size]
        if x != y:
            differences.append({"record": index, "name": name, "bytes": size,
                                "differing_bytes": sum(p != q for p, q in zip(x, y))})
    return {"status": "EQUAL" if not differences else "DIFFERS",
            "records": len(schema), "differences": differences}


def run_once(scenario: dict, out: Path, build_report: Path | None) -> dict:
    command = [sys.executable, str(ROOT / "dos/run.py"), "--out", str(out),
               "--seconds", str(scenario["host_seconds"]), "--fixed-clock",
               "--input-script", str(ROOT / scenario["script"])]
    command += ["--original"] if build_report is None else ["--build-report", str(build_report)]
    if scenario.get("saved_game"):
        command += ["--saved-game", str(ROOT / scenario["saved_game"])]
    subprocess.run(command, cwd=ROOT, check=True, stdout=subprocess.DEVNULL,
                   timeout=scenario["host_seconds"] + 180)
    report = json.loads((out / "execution-report.json").read_text())
    return {"report": report,
            "saves": {name: (out / name).read_bytes() if (out / name).is_file() else None
                      for name in scenario["saves"]}}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scenario", type=Path)
    parser.add_argument("--build-report", type=Path, required=True,
                        help="reconstructed executable receipt accepted by dos/run.py")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    scenario = json.loads(args.scenario.read_text())
    out = diagnostic.experimental_path(args.out)
    build.prepare_output(out, ROOT / "build/current/dos-acceptance")
    runs = {"original": run_once(scenario, out / "original", None),
            "reconstructed": run_once(scenario, out / "reconstructed", args.build_report)}
    result = {"schema": "simant-dos-acceptance-v2", "scenario": scenario,
              "scenario_sha256": build.digest(args.scenario.read_bytes()),
              "script_sha256": build.digest((ROOT / scenario["script"]).read_bytes()),
              "closure_eligible": False, "runs": {}, "saves": {}}
    passed = True
    for label, run in runs.items():
        report = run["report"]
        faults = report.get("runtime_faults", {}).get("count")
        result["runs"][label] = {"status": report.get("status"), "runner": report.get("runner"),
                                 "runtime_faults": faults,
                                 "executable": next((p for p in report.get("inputs", [])
                                                     if str(p.get("path", "")).upper().endswith(".EXE")
                                                     and "INSTALL" not in str(p.get("path", "")).upper()), None)}
        passed &= report.get("status") == "EMULATOR_EXITED" and not faults
    for name in scenario["saves"]:
        x, y = runs["original"]["saves"][name], runs["reconstructed"]["saves"][name]
        if x is None or y is None:
            result["saves"][name] = {"status": "MISSING", "present": [x is not None, y is not None]}
            passed = False
            continue
        row = compare_saves(x, y)
        row["sha256"] = [build.digest(x), build.digest(y)]
        result["saves"][name] = row
        passed &= row["status"] == "EQUAL"
    result["status"] = "PASS" if passed else "FAIL"
    (out / "acceptance.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"status": result["status"], "out": str(out / "acceptance.json"),
                      "saves": {k: (v["status"], [d["name"] for d in v.get("differences", [])][:10])
                                for k, v in result["saves"].items()}}, indent=1))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
