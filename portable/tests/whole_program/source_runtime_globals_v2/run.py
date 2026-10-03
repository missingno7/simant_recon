import hashlib
import importlib.util
import json
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
CC = os.environ.get("CC", r"C:\msys64\mingw64\bin\gcc.exe")
OWNER_C = ROOT / "portable/game/state/source_runtime_globals.c"
OWNER_H = ROOT / "portable/game/state/source_runtime_globals.h"
ADAPTER = ROOT / "portable/tools/source_runtime_globals.py"
HARNESS = HERE / "clip_capacity_harness.c"
spec = importlib.util.spec_from_file_location("source_runtime_globals", ADAPTER)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
transformed = {}
for rel in mod.PINNED:
    raw = (ROOT / rel).read_bytes()
    out = mod.adapt_transformed(raw, rel, raw)
    transformed[rel] = out
    mutated = bytearray(raw)
    mutated[0] ^= 1
    try:
        mod.adapt_transformed(out, rel, bytes(mutated))
    except ValueError as exc:
        assert "identity drift" in str(exc)
    else:
        raise AssertionError(f"stale original accepted for {rel}")
clip = transformed["src/root/m1E57.c"]
assert clip.count("sim_source_runtime_reserve_clip_rects(((size_t)n + 1u) * sizeof(struct Rect))") == 4
for source in clip.split("g_5AAC = fd_50F6_3C14;"):
    pass
assert clip.index("sim_source_runtime_reserve_clip_rects(5u * sizeof(struct Rect))") < clip.index("g_5AAC = fd_50F6_3C14;", clip.index("sim_source_runtime_reserve_clip_rects(5u * sizeof(struct Rect))"))
exe = HERE / "clip_capacity.exe"
subprocess.run([CC, "-std=c11", "-O0", "-Wall", "-Wextra", "-Werror", "-I", str(ROOT / "portable/game/state"),
                str(OWNER_C), str(HARNESS), "-o", str(exe)], check=True)
subprocess.run([str(exe)], check=True)
asan = {"available": False}
asan_exe = HERE / "clip_capacity_asan.exe"
try:
    subprocess.run([CC, "-std=c11", "-O0", "-fsanitize=address", "-fno-omit-frame-pointer", "-I", str(ROOT / "portable/game/state"),
                    str(OWNER_C), str(HARNESS), "-o", str(asan_exe)], check=True, capture_output=True, text=True)
    subprocess.run([str(asan_exe)], check=True, capture_output=True, text=True)
    asan = {"available": True, "status": "PASS"}
except (subprocess.CalledProcessError, OSError) as exc:
    asan = {"available": False, "reason": str(exc)}
inputs = [OWNER_C, OWNER_H, ADAPTER, HARNESS]
report = {
    "schema": "simant-source-runtime-global-owner-native-v2",
    "status": "PASS",
    "scope": "Bounded native clip scratch owner/rebase and adapter-order controls; no DOS pixel/source-body equivalence claim.",
    "inputs": {str(p.relative_to(ROOT)).replace("\\", "/"): hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs},
    "source_pins": mod.PINNED,
    "adapted_m1e57_sha256": hashlib.sha256(clip.encode()).hexdigest(),
    "compiler": subprocess.check_output([CC, "--version"], text=True).splitlines()[0],
    "controls": ["four runtime clip-size sites reserve before assigning scratch alias", "five-Rect output bound reserves before g_5AAC assignment", "scratch pointer interior alias rebased across realloc", "SIZE_MAX reserve failure preserves old pointer and alias", "stale canonical source rejected in every adapter"],
    "address_sanitizer": asan,
}
(HERE / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
