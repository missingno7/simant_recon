"""Compile/test V3 against actual DOS SaveGame source-address sentinels."""
from __future__ import annotations
import hashlib, json, os, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BUILD = ROOT / "build/workers/savegame_sentinel_v3/native"
BUILD.mkdir(parents=True, exist_ok=True)
GEN = ROOT / "build/workers/recovered_source_next9/generated"
PAYLOAD = ROOT / "build/workers/savegame_sentinel_v3/original-dos-sentinel-stream.bin"
CODEC = ROOT / "portable/game/save/legacy_codec.c"
ADAPTER = ROOT / "portable/game/save/next9_bindings_v3.c"
STATE = GEN / "recovered_state.c"
SENTINELS = ROOT / "portable/tests/save/support/next9_source_sentinels_v3.c"
TEST = ROOT / "portable/tests/save/test_next9_bindings_v3.c"

def compile_run(name: str, *, big_endian: bool=False, mutant: str|None=None, expect_failure: bool=False) -> dict:
    source = ADAPTER
    if mutant:
        text = ADAPTER.read_text(encoding="utf-8")
        anchor = '#include "next9_bindings_v3_rows.inc"\n'
        if text.count(anchor) != 1: raise RuntimeError("V3 binding include anchor changed")
        changes = {
            "swap-48-49": "    { uint8_t *tmp = bindings[48].bytes; bindings[48].bytes = bindings[49].bytes; bindings[49].bytes = tmp; }\n",
            "row48-wide-component": "    bindings[48].storage_order = PORTABLE_LEGACY_SAVE_NATIVE_NUMERIC_32;\n",
            "row99-numeric": "    bindings[99].storage_order = PORTABLE_LEGACY_SAVE_NATIVE_NUMERIC_16;\n",
        }
        if mutant not in changes: raise RuntimeError(f"unknown negative control {mutant}")
        source = BUILD / f"{name}.c"
        source.write_text(text.replace(anchor, anchor + changes[mutant]), encoding="utf-8", newline="")
    exe = BUILD / f"{name}.exe"
    command = ["gcc", "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror"]
    if big_endian: command.append("-DPORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN")
    command += ["-I",str(ROOT/"portable"),"-I",str(GEN),"-I",str(ROOT/"portable/tests/save/support"),
                "-I",str(ROOT/"portable/game/save"),str(CODEC),str(source),str(STATE),str(SENTINELS),str(TEST),"-o",str(exe)]
    built = subprocess.run(command,cwd=ROOT,capture_output=True,text=True)
    if built.returncode: raise RuntimeError(f"{name} compile failed:\n{built.stdout}{built.stderr}")
    run = subprocess.run([str(exe),str(PAYLOAD)],cwd=ROOT,capture_output=True,text=True)
    passed = run.returncode == 0
    if passed == expect_failure:
        raise RuntimeError(f"{name} negative/positive expectation failed rc={run.returncode}: {run.stdout}{run.stderr}")
    return {"name":name,"mutant":mutant,"forced_big_endian":big_endian,
            "expected_failure":expect_failure,"returncode":run.returncode,
            "stdout":run.stdout,"stderr":run.stderr,
            "source_sha256":hashlib.sha256(source.read_bytes()).hexdigest(),
            "executable_sha256":hashlib.sha256(exe.read_bytes()).hexdigest()}

def main() -> None:
    if not PAYLOAD.exists(): raise SystemExit("run probe_original_savegame_sentinels_v3.py first")
    rows = [compile_run("positive-little-endian"),compile_run("positive-forced-big-endian",big_endian=True),
            compile_run("negative-swapped-rows",mutant="swap-48-49",expect_failure=True),
            compile_run("negative-component-width",big_endian=True,mutant="row48-wide-component",expect_failure=True),
            compile_run("negative-row99-storage",big_endian=True,mutant="row99-numeric",expect_failure=True)]
    result = {"schema":"simant-next9-bindings-v3-test-report-v1","status":"PASS",
              "original_payload_sha256":hashlib.sha256(PAYLOAD.read_bytes()).hexdigest(),"runs":rows}
    report_path = ROOT / "portable/tests/save/evidence/legacy-save-codec-v3/native-sentinel-validation.json"
    report_path.parent.mkdir(parents=True,exist_ok=True)
    report_path.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8",newline="")
    for row in rows: print(f"{row['name']}={'EXPECTED_FAIL' if row['expected_failure'] else 'PASS'} rc={row['returncode']}")

if __name__ == "__main__": main()
