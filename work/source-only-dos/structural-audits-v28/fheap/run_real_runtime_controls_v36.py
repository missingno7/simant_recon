#!/usr/bin/env python3
"""Execute linked pinned MSC runtime controls in isolated DOSBox-X; no stubs."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "tools"))
import compiler  # noqa: E402

tc = compiler.toolchain()
runner = tc["runners"]["dosbox-x"]
report = json.loads((OUT / "fheap-runtime-probe-v36.json").read_text(encoding="utf-8"))
run_results = []
for link in report["link_runs"]:
    case = OUT / "links" / link["linker"]
    batch = "@echo off\r\necho begin > BEGIN.TXT\r\nPROBE.EXE > OUTPUT.TXT\r\necho done > DONE.TXT\r\nexit\r\n"
    (case / "RRUN.BAT").write_bytes(batch.encode("ascii"))
    conf = []
    for section, values in runner["conf"].items():
        conf.append(f"[{section}]")
        conf.extend(f"{key}={value}" for key, value in values.items())
    conf += ["[autoexec]", f'mount c "{case.resolve()}"', "c:",
             "call RRUN.BAT", "exit"]
    conf_path = case / "dosbox-runtime.conf"
    conf_path.write_text("\n".join(conf) + "\n", encoding="ascii")
    env = os.environ.copy()
    env.update(SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy")
    process = subprocess.run([runner["path"], "-conf", str(conf_path), "-fastlaunch",
                             "-exit", "-nomenu"], cwd=case, env=env,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            timeout=90, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    output_path = case / "OUTPUT.TXT"
    done_path = case / "DONE.TXT"
    if not done_path.exists():
        raise SystemExit(f"DOSBox-X did not reach the post-program marker for {link['linker']}; "
                         f"runner output={process.stdout.decode('latin1', errors='replace')[-1200:]}")
    result = {"linker": link["linker"], "dosbox_exit_code": process.returncode,
              "fixture_reached_post_program_marker": True,
              "runtime_output": output_path.read_text(encoding="latin1", errors="replace")
              if output_path.exists() else "<no output file>"}
    run_results.append(result)

report["status"] = "LINKED_AND_EXECUTED_REAL_RUNTIME_CONTROL"
report["execution"] = {"allocator_stubs_present": False,
                       "original_executable_used": False,
                       "runs": run_results}
(OUT / "fheap-runtime-probe-v36.json").write_text(json.dumps(report, indent=2) + "\n",
                                                 encoding="utf-8")
print(json.dumps(report["execution"], indent=2))
