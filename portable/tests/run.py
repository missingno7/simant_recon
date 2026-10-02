#!/usr/bin/env python3
"""Strict native regression gate. DOS differential proofs are separate suites."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
import shlex
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
PORT = ROOT / "portable"
BUILD = ROOT / "build/portable/tests"
UNITS = {
    "ants": ("ants/test_ants.c", []),
    "audio": ("audio/audio_test.c", ["assets/SOUND"]),
    "database": ("resources/database_test.c", ["assets"]),
    "advice": ("resources/advice_test.c", ["assets"]),
    "population": ("population/test_population.c", []),
    "render": ("render/test_render.c", ["assets"]),
    "setup": ("setup/test_setup.c", []),
    "session": ("session/test_session.c", ["assets"]),
    "terrain": ("terrain/test_terrain.c", []),
    "water": ("water/test_water.c", []),
    "feeding": ("feeding/test_feeding.c", []),
    "scent": ("scent/test_scent.c", []),
    "tick": ("tick/test_tick.c", []),
    "timing": ("timing/test_timing.c", []),
    "tiles": ("resources/tiles_test.c", ["assets"]),
    "windows": ("windows/test_window.c", []),
    "window_open": ("windows/test_open.c", []),
    "window_operations": ("windows/test_operations.c", []),
    "balloons": ("windows/test_balloons.c", []),
    "menus": ("menus/test_menu.c", ["assets"]),
    "menu_render": ("menus/test_menu_render.c", ["assets"]),
    "ribbon": ("windows/test_ribbon.c", []),
    "titles": ("windows/titles/test_titles.c", ["assets"]),
    "dialogs": ("dialogs/test_picture_dialog.c", ["assets"]),
    "game_over": ("dialogs/game_over_test.c", []),
    "nest_live_clock": ("nest/live_clock_test.c", []),
    "input": ("input/test_input.c", []),
    "bios_fonts": ("windows/render/test_bios_fonts_loader.c",
                   ["assets", "build/bios-reference/dosbox-staging-v0.83.0"]),
    "bios_provider": ("windows/render/test_bios_font_provider.c", []),
    "platform_memory": ("platform_memory/test_memory.c", []),
    "lesson_adapter": ("recovered/lesson_adapter_test.c", []),
    "session_bridge": ("recovered/session_bridge_test.c", []),
    "registry": ("windows/test_registry.c", ["assets"]),
    "map": ("map/test_map.c", ["assets"]),
    "overview": ("render/test_overview.c", []),
    "overview_view": ("render/test_overview_view.c", ["assets"]),
    "game_view": ("game_view/test_game_view.c", ["assets"]),
    "tile_raster": ("render/tile/test_tile_raster.c", ["assets"]),
    "worldgen": ("worldgen/test_worldgen.c", []),
    "yard": ("yard/test_yard.c", []),
}
EXTRA_SOURCES = {
    "platform_memory": [PORT / "game/recovered/memory_adapter.c"],
    "lesson_adapter": [PORT / "game/recovered/lesson_adapter.c"],
    "session_bridge": [PORT / "game/recovered/session_bridge.c"],
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--suite", choices=sorted(UNITS), action="append")
    parser.add_argument("--host", action="store_true", help="also exercise the real SDL3 host")
    parser.add_argument("--recovered-profile", type=Path,
                        help="explicit diagnostic generated profile for session_bridge")
    args = parser.parse_args()
    compiler = os.environ.get("SIMANT_CC") or shutil.which("gcc")
    if not compiler:
        fallback = Path("C:/msys64/mingw64/bin/gcc.exe")
        compiler = str(fallback) if fallback.exists() else None
    if not compiler:
        raise SystemExit("Native C compiler missing; set SIMANT_CC")
    # Source-reuse research is deliberately outside this production gate. Its
    # generated modules have their own compile/proof boundary until reviewed.
    sources = sorted([* (PORT / "game").glob("*.c"),
                      PORT / "platform/memory.c",
                      *(p for folder in ("game/simulation", "game/state", "game/resources", "game/render",
                                         "render", "ui_model", "audio")
                        for p in (PORT / folder).rglob("*.c"))])
    selected_units=args.suite or sorted(name for name in UNITS if name != "session_bridge")
    generated_sources=[]
    profile_include=[]
    if "session_bridge" in selected_units:
        if args.recovered_profile is None:
            raise SystemExit("session_bridge requires --recovered-profile; no implicit source profile")
        profile=args.recovered_profile.resolve()
        provenance=json.loads((profile / "provenance.json").read_text())
        state=provenance["recovered_state"]
        if state["binding_status"] != "COMPLETE" or state["source_data_initializer_mismatches"]:
            raise SystemExit("Recovered profile has incomplete state binding/initializers")
        for key,filename in (("header_sha256","recovered_state.h"),
                             ("source_sha256","recovered_state.c")):
            if sha(profile / filename) != state[key]:
                raise SystemExit("Recovered profile identity mismatch")
        generated_sources=[profile / "recovered_state.c"]
        profile_include=["-I",str(profile),"-I",str(PORT / "game/recovered")]
    test_sources=[PORT / "tests" / UNITS[name][0] for name in selected_units]
    tested_extras=[source for name in selected_units for source in EXTRA_SOURCES.get(name,[])]
    # Hash the headers the selected build actually consumes. An unrelated
    # experimental host header cannot stale a source-only regression run.
    dependencies=subprocess.check_output(
        [compiler,"-std=c11","-I", "portable",*profile_include,
         "-MM","-MT","SIMANT_DEP",
         *(p.relative_to(ROOT).as_posix() for p in
           sources+test_sources+tested_extras+generated_sources)],
        cwd=ROOT,text=True).replace("\\\n"," ")
    dependency_paths=set()
    for block in dependencies.split("SIMANT_DEP:")[1:]:
        for token in shlex.split(block):
            path=(ROOT / token).resolve()
            if path.is_relative_to(ROOT) and path.is_file():
                dependency_paths.add(path)
    BUILD.mkdir(parents=True, exist_ok=True)
    run_directory=Path(tempfile.mkdtemp(prefix="gate-",dir=BUILD))
    frozen_check = BUILD / "frozen-oracle-check.json"
    subprocess.run([sys.executable,str(ROOT / "tools/oracle_checkpoint.py"),
                    "--output",str(frozen_check)],cwd=ROOT,check=True)
    frozen_receipt = json.loads(frozen_check.read_text())
    if not frozen_receipt.get("ready"):
        raise SystemExit("Frozen historical input identity check failed")
    receipt = {"scope": "native unit/integration checks; not DOS differential acceptance",
               "frozen_oracle_inputs": {"status":"PASS", "receipt_sha256":sha(frozen_check)},
               "status": "RUNNING", "compiler": subprocess.check_output(
                   [compiler, "--version"], text=True).splitlines()[0],
               "inputs": {p.relative_to(ROOT).as_posix(): sha(p)
                          for p in sorted(dependency_paths | set(sources+tested_extras))},
               "tests": []}
    if generated_sources:
        receipt["inputs"].update({p.relative_to(ROOT).as_posix():sha(p)
                                  for p in [*generated_sources,profile / "recovered_state.h",
                                            profile / "provenance.json"]})
    report = BUILD / "native-unit-report.json"
    receipt["inputs"].update({p.relative_to(ROOT).as_posix():sha(p)
                              for p in test_sources+[Path(__file__).resolve()]})
    # Compile each shared TU once with the same strict flags used by every
    # suite. Linking these objects is equivalent to repeating the individual
    # TU compilations for each executable (no LTO or unity build is used).
    # Independent compiles use separate output paths; input stability is still
    # checked across the whole gate.
    shared_objects = [run_directory / f"common-{index}.o"
                      for index in range(len(sources))]
    def compile_shared(pair):
        source, output = pair
        command = [compiler, "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror",
                   "-I", str(PORT), *profile_include,
                   "-c", str(source), "-o", str(output)]
        result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
        return source, command, result
    print(f"[common] strict compile of {len(sources)} shared translation units", flush=True)
    with ThreadPoolExecutor(max_workers=4) as pool:
        for source, command, result in pool.map(compile_shared, zip(sources, shared_objects)):
            if result.returncode:
                receipt["status"] = "FAIL"
                receipt["common_compile_failure"] = {
                    "source": source.relative_to(ROOT).as_posix(),
                    "command": command, "exit_code": result.returncode,
                    "diagnostic": result.stdout + result.stderr}
                report.write_text(json.dumps(receipt, indent=2) + "\n")
                raise SystemExit(result.stdout + result.stderr)
    receipt["common_objects"] = {source.relative_to(ROOT).as_posix(): sha(output)
                                 for source, output in zip(sources, shared_objects)}
    for name in selected_units:
        relative, test_args = UNITS[name]
        test = PORT / "tests" / relative
        output = run_directory / f"{name}-test.exe"
        command = [compiler, "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror",
                   "-I", str(PORT), *profile_include, str(test),
                   *(str(p) for p in shared_objects + EXTRA_SOURCES.get(name,[]) +
                     (generated_sources if name == "session_bridge" else [])), "-o", str(output)]
        print(f"[{name}] strict native compile and run", flush=True)
        compiled = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
        if compiled.returncode:
            receipt["status"] = "FAIL"
            receipt["tests"].append({"name": name, "stage": "compile", "exit_code": compiled.returncode,
                                     "diagnostic": compiled.stdout + compiled.stderr})
            report.write_text(json.dumps(receipt, indent=2) + "\n")
            raise SystemExit(compiled.stdout + compiled.stderr)
        try:
            ran = subprocess.run([str(output), *test_args], cwd=ROOT, text=True,
                                 capture_output=True,timeout=30)
        except subprocess.TimeoutExpired:
            receipt["status"]="FAIL"
            receipt["tests"].append({"name":name,"stage":"run","failure":"30-second timeout"})
            report.write_text(json.dumps(receipt,indent=2)+"\n")
            raise SystemExit(f"Native suite timed out: {name}")
        result = {"name": name, "test_sha256": sha(test), "executable_sha256": sha(output),
                  "exit_code": ran.returncode, "output": ran.stdout + ran.stderr}
        receipt["tests"].append(result)
        print(result["output"].strip(), flush=True)
        if ran.returncode:
            receipt["status"] = "FAIL"
            report.write_text(json.dumps(receipt, indent=2) + "\n")
            raise SystemExit(ran.returncode)
    if args.host:
        subprocess.run([sys.executable, str(PORT / "tests/host/run.py")], cwd=ROOT, check=True)
        host_report = ROOT / "build/portable/host-smoke.test.json"
        host_receipt = json.loads(host_report.read_text())
        if host_receipt.get("status") != "PASS":
            raise SystemExit("SDL3 host gate did not record PASS")
        receipt["sdl3_host"] = {
            "status": "PASS", "receipt_sha256": sha(host_report),
            "receipt": host_receipt}
    changed = [name for name,expected in receipt["inputs"].items()
               if sha(ROOT / name)!=expected]
    if changed:
        receipt["status"]="STALE"
        receipt["changed_during_run"]=changed
        report.write_text(json.dumps(receipt,indent=2)+"\n")
        raise SystemExit(f"Sources changed during the regression gate; rerun required: {changed}")
    receipt["status"] = "PASS"
    report.write_text(json.dumps(receipt, indent=2) + "\n")
    print(f"PASS: {len(receipt['tests'])} native suites; {report}")


if __name__ == "__main__":
    main()
