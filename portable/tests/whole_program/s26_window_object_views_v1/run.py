from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
ADAPTER_PATH = ROOT / "portable/whole_program/conversions/s26_window_object_views_v1.py"
RAW_PATH = ROOT / "src/S26/m39C7.c"
GENERATED_PATH = ROOT / "build/workers/whole_program/generated/S26_m39C7.c"
V15_TU_FIXTURE = HERE / "fixtures/v15/S26_m39C7.c"
V15_TYPES_FIXTURE = HERE / "fixtures/v15/dos_types.h"
REGISTRY_C = ROOT / "portable/whole_program/window_refs.c"
HARNESS = HERE / "window_refs_harness.c"
CC = os.environ.get("CC", r"C:\msys64\mingw64\bin\gcc.exe")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


spec = importlib.util.spec_from_file_location("s26_views", ADAPTER_PATH)
adapter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(adapter)
raw = RAW_PATH.read_bytes()
raw_out, raw_report = adapter.adapt(raw, "src/S26/m39C7.c")
assert raw_report["active_lookups"] == {"index_0": 3, "index_1": 1}
assert "w->objs" not in raw_out
assert raw_out.count("simant_s26_window_object(w, 0)") == 3
assert raw_out.count("simant_s26_window_object(w, 1)") == 1

for rel, content in (("src/S26/m39C7.c", raw + b"\n/* drift */\n"),
                     ("src/S25/m39C7.c", raw)):
    try:
        adapter.adapt(content, rel)
    except ValueError:
        pass
    else:
        raise AssertionError("stale or unregistered S26 input was accepted")

probe = ("/* w->objs[1] */ const char *note = \"w->objs[0]\";\n"
         "w->objs[0]; w -> objs [ 0 ]; w->objs[0]->x; w->objs[1];")
rewritten, counts = adapter._replace_code_refs(probe)
assert counts == {"index_0": 3, "index_1": 1}
assert "/* w->objs[1] */" in rewritten and '"w->objs[0]"' in rewritten
assert "w->objs[0]" not in adapter._code_only(rewritten)

generated = V15_TU_FIXTURE.read_bytes()
native, generated_report = adapter.adapt_generated(
    generated, "build/workers/whole_program/generated/S26_m39C7.c")
assert native.count("simant_s26_window_object(w, 0)") == 3
assert native.count("simant_s26_window_object(w, 1)") == 1
assert "w->objs" not in adapter._code_only(native)

with tempfile.TemporaryDirectory(prefix="simant-s26-views-") as td:
    tmp = Path(td)
    tu = tmp / "S26_m39C7.c"
    obj = tmp / "S26_m39C7.o"
    exe = tmp / "window_refs_test.exe"
    tu.write_text(native, encoding="utf-8")
    subprocess.run([CC, "-std=c11", "-O0", "-Wall", "-Wextra", "-Werror",
                    "-fno-strict-aliasing", "-I", str(ROOT), "-I",
                    str(V15_TU_FIXTURE.parent), "-I", str(GENERATED_PATH.parent),
                    "-c", str(tu),
                    "-o", str(obj)], check=True)
    subprocess.run([CC, "-std=c11", "-O0", "-Wall", "-Wextra", "-Werror",
                    "-I", str(ROOT), str(REGISTRY_C), str(HARNESS), "-o", str(exe)],
                   check=True)
    subprocess.run([str(exe)], check=True)

report = {
    "schema": "simant-s26-window-object-views-v1",
    "status": "PASS",
    "scope": "Strict S26 preword source adapter, captured generated-TU compile, and bounded registry pointer-table owner control. No full-game or DOS pixel claim.",
    "inputs": {
        str(path.relative_to(ROOT)).replace("\\", "/"): sha(path.read_bytes())
        for path in (ADAPTER_PATH, RAW_PATH, V15_TU_FIXTURE, V15_TYPES_FIXTURE,
                     REGISTRY_C, HARNESS)
    },
    "raw_source_adapter": raw_report,
    "captured_generated_adapter": generated_report,
    "control": "Two synthetic native object records resolve to the registry-owned char** table at their actual buffer addresses; unknown buffer and detached owner return NULL.",
    "compiler": subprocess.check_output([CC, "--version"], text=True).splitlines()[0],
    "checks": ["strict frozen source identity", "wrong-path and mutated-source rejection",
               "comments/literals excluded from active reference rewrite",
               "all 4 S26 native pointer-table reads routed through sidecar",
               "captured v15 generated S26 TU compiles under -Werror",
               "registry attach/object lookup/detach positive and unknown-buffer negative"],
}
(HERE / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print("S26 sidecar conversion and pointer-table controls: PASS")
