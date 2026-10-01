"""Run search and whole-module verify-only gates for generated candidates."""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
WORKER = ROOT / "build" / "workers" / "ptr_small"
GENERATED = json.loads((WORKER / "generated.json").read_text(encoding="utf-8"))
SEARCH_HISTORY = ROOT / "build" / "search" / "f_20E8_0903" / "history.jsonl"
SOURCE = {
    Path(row["source"]).name: row
    for line in SEARCH_HISTORY.read_text(encoding="utf-8").splitlines()
    if (row := json.loads(line)).get("source")
    and Path(row["source"]).name in {Path(v["path"]).name for v in GENERATED["variants"]}
}


def main() -> None:
    variants = GENERATED["variants"]
    report = {
        "target": GENERATED["target"],
        "module": GENERATED["module"],
        "seed_sha256_search_text": GENERATED["seed_sha256_search_text"],
        "generated_count": len(variants),
        "search_rows_found": len(SOURCE),
        "verify_only_command": "python tools/promote.py CANDIDATE --module root:20E8 --claim f_20E8_0903 --verify-only",
        "limits": {"generated_max": 40, "parallel_jobs": 1},
        "results": [],
    }
    log_path = WORKER / "verify-only.log"
    log_path.write_text("", encoding="utf-8")
    result_path = WORKER / "gate-report.json"
    for index, variant in enumerate(variants, 1):
        candidate = ROOT / variant["path"]
        found = SOURCE.get(candidate.name)
        command = [
            sys.executable,
            "tools/promote.py",
            str(candidate),
            "--module",
            "root:20E8",
            "--claim",
            "f_20E8_0903",
            "--verify-only",
        ]
        proc = subprocess.run(command, cwd=ROOT, text=True, encoding="utf-8", errors="replace", capture_output=True)
        output = proc.stdout + proc.stderr
        peer_rows = []
        data_rows = []
        for line in output.splitlines():
            match = re.match(r"\s*([A-Za-z0-9_]+): (EXACT|FAIL)(?: (.*))?$", line)
            if match:
                peer_rows.append({"name": match.group(1), "status": match.group(2), "detail": match.group(3) or ""})
            match = re.match(r"\s*data ([A-Za-z0-9_]+): (EXACT|FAIL)(?: (.*))?$", line)
            if match:
                data_rows.append({"name": match.group(1), "status": match.group(2), "detail": match.group(3) or ""})
        peer_only = [row for row in peer_rows if row["name"] != GENERATED["target"]]
        target_rows = [row for row in peer_rows if row["name"] == GENERATED["target"]]
        item = {
            "name": variant["name"],
            "source": variant["path"],
            "source_sha256_file_bytes": variant["source_sha256_file_bytes"],
            "source_sha256_search_text": variant["source_sha256_search_text"],
            "search": None if found is None else {
                "status": found.get("status"),
                "reasons": found.get("reasons", []),
                "opcode_ratio": found.get("opcode_ratio"),
                "first_diff_insn": found.get("first_diff_insn"),
                "profile": found.get("profile"),
                "flags": found.get("flags"),
            },
            "verify_only_exit_code": proc.returncode,
            "accepted_peers_exact": bool(peer_only) and all(row["status"] == "EXACT" for row in peer_only),
            "accepted_peer_rows": peer_only,
            "private_data_exact": bool(data_rows) and all(row["status"] == "EXACT" for row in data_rows),
            "private_data_rows": data_rows,
            "candidate_exact": proc.returncode == 0 and target_rows and all(row["status"] == "EXACT" for row in target_rows),
            "target_rows": target_rows,
            "refused": "REFUSED:" in output,
        }
        if found is None:
            item["search"] = {"status": "MISSING_SEARCH_ROW"}
        report["results"].append(item)
        with log_path.open("a", encoding="utf-8") as fh:
            fh.write(f"[{index}/{len(variants)}] {variant['name']} (exit {proc.returncode})\n")
            fh.write(output)
            fh.write("\n")
        result_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        if index % 5 == 0 or index == len(variants):
            print(f"verified {index}/{len(variants)}: {variant['name']}", flush=True)

    summary = {
        "search_statuses": {},
        "all_accepted_peers_exact": all(row["accepted_peers_exact"] for row in report["results"]),
        "all_private_data_exact": all(row["private_data_exact"] for row in report["results"]),
        "exact_candidates": [row["name"] for row in report["results"] if row["candidate_exact"]],
        "missing_search_rows": [row["name"] for row in report["results"] if row["search"]["status"] == "MISSING_SEARCH_ROW"],
    }
    for row in report["results"]:
        status = row["search"]["status"]
        summary["search_statuses"][status] = summary["search_statuses"].get(status, 0) + 1
    report["summary"] = summary
    result_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
