"""Independent validation of everything accepted, plus the authoritative progress report.

    python tools/validate.py            # full: oracle, toolchain, fresh rebuild of every module, tests, report
    python tools/validate.py --no-tests

Nothing cached is trusted: every module file is recompiled from src/ and every
claim is re-bound and compared.  Writes docs/progress.json and docs/progress.md.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import compiler  # noqa: E402
import exe as exemod  # noqa: E402
import functions as fnmod  # noqa: E402
import modules as modmod  # noqa: E402

ROOT = exemod.ROOT


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-tests", action="store_true")
    a = ap.parse_args()
    failures = []

    r = subprocess.run([sys.executable, str(ROOT / "tools" / "oracle.py")], capture_output=True, text=True)
    print(r.stdout.strip())
    if r.returncode:
        failures.append("oracle lock")

    man = modmod.load_manifest()
    for prof in sorted({m["profile"] for m in man["modules"].values()} | {"msc600", "msc600a", "masm510"}):
        try:
            compiler.verify_profile(prof)
        except Exception as e:  # noqa: BLE001
            failures.append(f"toolchain {prof}: {e}")
    print("toolchain hashes verified" if not any(f.startswith("toolchain") for f in failures) else "TOOLCHAIN FAIL")

    x = exemod.load()
    claimed = []
    exact_c = 0
    exact_c_bytes = 0
    data_bytes = 0
    scaffolds = 0
    exact_tus = 0
    bss_bytes = 0
    per_unit = defaultdict(int)
    for key, m in man["modules"].items():
        path = ROOT / m["source"]
        text = path.read_text(encoding="latin1")
        if sha(text.encode("latin1")) != m["source_sha256"]:
            failures.append(f"{key}: source hash differs from manifest (unpublished edit)")
        res = modmod.verify_module(text, m, m["claims"])
        bad = [n for n, c in res["claims"].items() if not c["exact"]]
        dbad = [n for n, d in res.get("data", {}).items() if not d["exact"]]
        status = "OK" if res["exact"] else f"FAIL {bad + dbad}"
        print(f"  {key:<10} {len(m['claims']):3d} claims  {status}")
        if not res["exact"]:
            failures.append(f"{key}: {bad + dbad} {res.get('log', '')}")
        for c in m["claims"]:
            claimed.append((c["unit"], c["seg"] * 16 + c["off"], c["size"], c["name"]))
            if c.get("kind", "C") == "C":
                exact_c += 1
                exact_c_bytes += c["size"]
            per_unit[c["unit"]] += c["size"]
        for n, d in res.get("data", {}).items():
            if d.get("kind") == "BSS":
                bss_bytes += d["size"]
            elif d["exact"]:
                data_bytes += d["size"]
        scaffolds += len(res.get("scaffold", []))
        if m.get("extent") and res["exact"]:
            exact_tus += 1
    claimed.sort()
    for (u1, a1, s1, n1), (u2, a2, s2, n2) in zip(claimed, claimed[1:]):
        if u1 == u2 and a1 + s1 > a2:
            failures.append(f"overlapping claims {n1} {n2}")

    if not a.no_tests:
        t = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", str(ROOT / "tests"), "-q"],
                           capture_output=True, text=True, cwd=ROOT)
        print(t.stderr.strip().splitlines()[-1] if t.stderr.strip() else t.stdout.strip())
        if t.returncode:
            failures.append("unit tests")
            print(t.stderr[-2000:])

    # ---- accounting -------------------------------------------------------------------
    table = fnmod.table()["functions"]
    game = [f for f in table if f["region"] == "game_or_library"]
    runtime_located = 0
    lm = ROOT / "build" / "libmatch" / "msc600-large.json"
    if lm.exists():
        for rep in json.loads(lm.read_text()).values():
            runtime_located += sum(r["size"] for r in rep["rows"] if len(r.get("hits") or []) == 1)
    root_game_span = 0x29F4 * 16 + 0x1C - 0     # game code precedes the MSC runtime _TEXT
    overlay_code = sum(len(s.data) for s in x.sections[:27])
    code_total = root_game_span + overlay_code
    s27 = len(x.sections[27].data)
    progress = {
        "schema": "simant-progress-v1",
        "generated": dt.date.today().isoformat(),
        "oracle_sha256": x.sha256,
        "known_functions": len(table),
        "known_game_functions": len(game),
        "exact_c_functions": exact_c,
        "exact_c_bytes": exact_c_bytes,
        "exact_asm_functions": 0,
        "exact_asm_bytes": 0,
        "historical_runtime_bytes_accepted": 0,
        "historical_runtime_bytes_located_unaccepted": runtime_located,
        "rtlink_manager_bytes_unaccepted": len(x.image) - 0x2CFB * 16,
        "data_bytes_accepted": data_bytes,
        "bss_bytes_placed": bss_bytes,
        "game_code_span_bytes": code_total,
        "unresolved_code_bytes": code_total - exact_c_bytes,
        "unresolved_data_bytes": s27 - data_bytes,
        "overlay_coverage": {s.name: {"bytes": len(s.data), "claimed": per_unit.get(s.name, 0)}
                             for s in x.sections[:27]},
        "root_claimed_bytes": per_unit.get("root", 0),
        "scaffold_functions": scaffolds,
        "exact_translation_units": exact_tus,
        "whole_executable": "NOT_BUILT (no historical link yet; see docs/next-steps.md)",
        "validation": "PASS" if not failures else "FAIL",
        "failures": failures,
    }
    (ROOT / "docs").mkdir(exist_ok=True)
    (ROOT / "docs" / "progress.json").write_text(json.dumps(progress, indent=1) + "\n")
    md = ["# Progress (generated by tools/validate.py)", "",
          f"Validation: **{progress['validation']}** ({progress['generated']})", "",
          "| Measure | Value |", "|---|---:|"]
    for k in ("known_functions", "known_game_functions", "exact_c_functions", "exact_c_bytes",
              "exact_asm_bytes", "historical_runtime_bytes_accepted",
              "historical_runtime_bytes_located_unaccepted", "rtlink_manager_bytes_unaccepted",
              "data_bytes_accepted", "game_code_span_bytes", "unresolved_code_bytes", "unresolved_data_bytes",
              "scaffold_functions", "exact_translation_units"):
        md.append(f"| {k} | {progress[k]:,} |")
    md += ["", f"Whole executable: {progress['whole_executable']}", "",
           "Overlay coverage (claimed/bytes): " + ", ".join(
               f"{k} {v['claimed']}/{v['bytes']}" for k, v in progress["overlay_coverage"].items()), ""]
    (ROOT / "docs" / "progress.md").write_text("\n".join(md))
    print(f"exact C: {exact_c} functions, {exact_c_bytes} bytes; unresolved code {progress['unresolved_code_bytes']}")
    if failures:
        print("VALIDATION FAILED:")
        for f in failures:
            print("  -", f)
        return 1
    print("VALIDATION PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
