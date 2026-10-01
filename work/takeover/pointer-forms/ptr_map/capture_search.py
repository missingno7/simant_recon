from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
RUNS = [
    ("invert", "InvertPatch", [
        "build/workers/ptr_map/base.c",
        "build/workers/ptr_map/direct-m320-plus-hv_other-plus-vh.c",
    ]),
    ("cursor", "DrawMapCursor", [
        "build/workers/ptr_map/cursor-base.c",
        "build/workers/ptr_map/scale-top-plus_left-plus.c",
    ]),
]
rows = []
for label, function, sources in RUNS:
    cmd = [sys.executable, "tools/search.py", function, *sources]
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, encoding="utf-8")
    log = proc.stdout + ("\n[stderr]\n" + proc.stderr if proc.stderr else "")
    log_path = OUT / f"search-{label}.log"
    log_path.write_text(log, encoding="utf-8", newline="\n")
    rows.append({"label": label, "function": function, "command": cmd,
                 "returncode": proc.returncode, "log": str(log_path.relative_to(ROOT)),
                 "log_sha256": hashlib.sha256(log.encode("utf-8")).hexdigest()})
    print(f"{label}: returncode={proc.returncode} log={log_path.name}")
(OUT / "search-results.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
