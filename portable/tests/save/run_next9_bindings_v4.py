from __future__ import annotations

"""V4 closure refresh for the Next9 SaveRec address-sentinel proof.

This is diagnostic-only. It consumes the reviewed, read-only Next9 profile,
runs the actual DOS SaveGame sentinel probe, then two native byte-order positives and three
sensitivity negatives. Evidence output is immutable: an existing V4 packet is
never overwritten.
"""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Iterable

ROOT = Path(__file__).resolve().parents[3]
PACKET = ROOT / "portable/tests/save/evidence/legacy-save-codec-v4"
BUILD = ROOT / "build/workers/savegame_sentinel_v4"
NATIVE_BUILD = BUILD / "native"
PAYLOAD = BUILD / "original-dos-sentinel-stream.bin"
DOS_REPORT = BUILD / "original-dos-sentinel-report.json"
GEN_PROFILE = ROOT / "build/workers/recovered_source_next9/generated"
ADAPTER = ROOT / "portable/game/save/next9_bindings_v3.c"
CODEC = ROOT / "portable/game/save/legacy_codec.c"
STATE = GEN_PROFILE / "recovered_state.c"
SENTINELS = ROOT / "portable/tests/save/support/next9_source_sentinels_v3.c"
TEST = ROOT / "portable/tests/save/test_next9_bindings_v3.c"
PROBE = ROOT / "portable/tests/save/probe_original_savegame_sentinels_v4.py"
RECOVER9 = ROOT / "portable/tools/recover_source_next9.py"
RECOVER8 = ROOT / "portable/tools/recover_source_next8.py"
BINDGEN = ROOT / "portable/tools/generate_next9_bindings_v3.py"
V3_PACKET = ROOT / "portable/tests/save/evidence/legacy-save-codec-v3"
V3_RUNNER = ROOT / "portable/tests/save/run_next9_bindings_v3.py"
V3_PATHS = [V3_PACKET / name for name in (
    "README.md", "binding-map.json", "native-sentinel-validation.json",
    "original-dos-sentinel-report.json", "source-pins.json")]

# Python entrypoints/helpers used by the DOS-probe lane plus pinned lineage
# producers. The Next9 producer scripts are hashed but never executed here.
PYTHON_INPUTS = [
    RECOVER9, RECOVER8, BINDGEN, PROBE, V3_RUNNER,
    ROOT / "portable/tests/save/run_next9_bindings_v4.py",
    ROOT / "tools/behavior.py", ROOT / "tools/exe.py", ROOT / "tools/functions.py",
    ROOT / "tools/match.py", ROOT / "tools/modctx.py", ROOT / "tools/modules.py",
    ROOT / "tools/compiler.py", ROOT / "tools/symbols.py", ROOT / "tools/omf.py",
]
DOS_LAYOUT_INPUTS = [
    ROOT / "src/S09/m35F5.c",
    ROOT / "portable/tests/dialogs/evidence/savegame-format-source-inventory-v1/save-records.json",
    ROOT / "layout/symbols.json", ROOT / "layout/functions.json",
    ROOT / "layout/manifest.json", ROOT / "layout/toolchain.json",
    ROOT / "build/workers/recovered_source_next8/generated/provenance.json",
    ROOT / "build/workers/recovered_source_next8/generated/recovered_state.h",
    ROOT / "build/workers/recovered_source_next8/generated/recovered_state.c",
    ROOT / "build/workers/recovered_source_next9/generated/provenance.json",
    ROOT / "portable/tests/recovered/evidence/next9-profile-regeneration-review-20261002/review.json",
]
NATIVE_INPUTS = [
    CODEC, ROOT / "portable/game/save/legacy_codec.h",
    ROOT / "portable/game/save/legacy_records.inc",
    ADAPTER, ROOT / "portable/game/save/next9_bindings_v3.h",
    ROOT / "portable/game/save/next9_bindings_v3_rows.inc",
    STATE, GEN_PROFILE / "recovered_state.h",
    SENTINELS, ROOT / "portable/tests/save/support/next9_source_sentinels_v3.h",
    ROOT / "portable/game/save/next9_bindings_rows.inc",
    TEST,
]
MUTATIONS = {
    "swap-48-49": (
        "    { uint8_t *tmp = bindings[48].bytes; bindings[48].bytes = bindings[49].bytes; bindings[49].bytes = tmp; }\n"),
    "row48-wide-component": (
        "    bindings[48].storage_order = PORTABLE_LEGACY_SAVE_NATIVE_NUMERIC_32;\n"),
    "row99-numeric": (
        "    bindings[99].storage_order = PORTABLE_LEGACY_SAVE_NATIVE_NUMERIC_16;\n"),
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def key(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return str(path.resolve()).replace("\\", "/")


def hash_files(paths: Iterable[Path]) -> dict[str, str]:
    result = {}
    for path in sorted({p.resolve() for p in paths}, key=lambda p: str(p).casefold()):
        if not path.is_file():
            raise RuntimeError(f"required evidence input is missing: {path}")
        result[key(path)] = sha(path)
    return result


def tree_hashes(folder: Path) -> dict[str, str]:
    if not folder.is_dir():
        raise RuntimeError(f"preserved V3 folder is missing: {folder}")
    return {p.relative_to(folder).as_posix(): sha(p)
            for p in sorted(folder.rglob("*")) if p.is_file()}


def snapshot_readonly_inputs() -> dict[str, str]:
    files = [*PYTHON_INPUTS, *DOS_LAYOUT_INPUTS, *NATIVE_INPUTS, *V3_PATHS,
             V3_RUNNER, ROOT / "tools/behavior.py"]
    files.extend(sorted((ROOT / "assets").glob("*")))
    return hash_files(files)


def compiler_files(cc: Path) -> list[Path]:
    files = [cc.resolve()]
    for tool in ("cc1", "collect2", "ld", "as"):
        name = subprocess.check_output([str(cc), f"-print-prog-name={tool}"], text=True).strip()
        p = Path(name)
        if not p.is_absolute():
            p = cc.parent / p
        p = p.resolve()
        if p.is_file():
            files.append(p)
        else:
            raise RuntimeError(f"GCC tool path unresolved: {tool} -> {name}")
    return files


def msc_toolchain_files() -> list[Path]:
    config = json.loads((ROOT / "layout/toolchain.json").read_text(encoding="utf-8"))
    profile = config["profiles"]["msc600ax"]
    directory = Path(profile["directory"])
    return [(directory / rel).resolve() for rel in sorted(profile["files"])]


def local_dependencies(cc: Path, sources: list[Path], include_dirs: list[Path],
                       *, big_endian: bool = False) -> tuple[list[Path], str]:
    command = [str(cc), "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror"]
    if big_endian:
        command.append("-DPORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN")
    command += ["-MT", "v4-local-deps"]
    for inc in include_dirs:
        command += ["-I", str(inc)]
    command += ["-MM", *(str(p) for p in sources)]
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(f"gcc -MM failed:\n{result.stdout}{result.stderr}")
    flattened = result.stdout.replace("\\\n", " ").replace("\\\r\n", " ")
    colon = flattened.find(":")
    if colon < 0:
        raise RuntimeError(f"unparseable gcc -MM output: {flattened[:1000]}")
    deps = []
    for item in flattened[colon + 1:].split():
        dep = Path(item)
        if not dep.is_absolute():
            dep = ROOT / dep
        dep = dep.resolve()
        if dep.is_file():
            deps.append(dep)
    # GCC -MM must cover the unconditional legacy_codec.h dependency.
    expected = (ROOT / "portable/game/save/legacy_codec.h").resolve()
    if expected not in deps:
        raise RuntimeError("GCC -MM closure omitted unconditional legacy_codec.h")
    return sorted(set(deps), key=lambda p: str(p).casefold()), result.stdout


def command_for(cc: Path, out: Path, sources: list[Path], *, big_endian: bool = False) -> list[str]:
    command = [str(cc), "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror"]
    if big_endian:
        command.append("-DPORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN")
    command += ["-I", str(ROOT / "portable"), "-I", str(GEN_PROFILE),
                "-I", str(ROOT / "portable/tests/save/support"),
                "-I", str(ROOT / "portable/game/save"),
                *(str(p) for p in sources), "-o", str(out)]
    return command


def compile_run(cc: Path, name: str, payload: Path, *, big_endian: bool = False,
                mutant: str | None = None) -> dict:
    NATIVE_BUILD.mkdir(parents=True, exist_ok=True)
    adapter = ADAPTER
    mutant_sha = None
    if mutant:
        original = ADAPTER.read_text(encoding="utf-8")
        anchor = '#include "next9_bindings_v3_rows.inc"\n'
        if original.count(anchor) != 1:
            raise RuntimeError("V3 include anchor changed; refusing negative control mutation")
        adapter = NATIVE_BUILD / f"{name}-adapter.c"
        adapter.write_text(original.replace(anchor, anchor + MUTATIONS[mutant]),
                           encoding="utf-8", newline="")
        mutant_sha = sha(adapter)
    sources = [CODEC, adapter, STATE, SENTINELS, TEST]
    include_dirs = [ROOT / "portable", GEN_PROFILE,
                    ROOT / "portable/tests/save/support", ROOT / "portable/game/save"]
    deps, mm_stdout = local_dependencies(cc, sources, include_dirs, big_endian=big_endian)
    out = NATIVE_BUILD / f"{name}.exe"
    command = command_for(cc, out, sources, big_endian=big_endian)
    built = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    if built.returncode:
        raise RuntimeError(f"{name} compile failed:\n{built.stdout}{built.stderr}")
    run = subprocess.run([str(out), str(payload)], cwd=ROOT, capture_output=True,
                         text=True, timeout=120)
    expected_failure = mutant is not None
    passed = run.returncode == 0
    if passed == expected_failure:
        raise RuntimeError(f"{name} control expectation failed rc={run.returncode}: {run.stdout}{run.stderr}")
    return {
        "name": name, "mutant": mutant, "forced_big_endian": big_endian,
        "expected_failure": expected_failure, "returncode": run.returncode,
        "stdout": run.stdout, "stderr": run.stderr,
        "source_paths": [key(p) for p in sources],
        "source_sha256": {key(p): sha(p) for p in sources},
        "local_dependency_sha256": hash_files(deps),
        "gcc_mm_output": mm_stdout,
        "compile_command": command,
        "executable_path": key(out), "executable_sha256": sha(out),
        "mutant_source_sha256": mutant_sha,
    }


def run_script(script: Path) -> str:
    result = subprocess.run([sys.executable, str(script)], cwd=ROOT,
                            capture_output=True, text=True, timeout=1800)
    if result.returncode:
        raise RuntimeError(f"producer failed ({script}):\n{result.stdout}{result.stderr}")
    return result.stdout


def main() -> None:
    if PACKET.exists():
        raise SystemExit(f"refusing to overwrite V4 packet: {PACKET}")
    if not all(p.is_file() for p in V3_PATHS) or not V3_RUNNER.is_file():
        raise SystemExit("V3 packet/runner inputs are incomplete")
    v3_before = tree_hashes(V3_PACKET)
    v3_runner_before = sha(V3_RUNNER)
    v3_pin_manifest = json.loads((V3_PACKET / "source-pins.json").read_text(encoding="utf-8"))
    expected_profile_sha = "9821efeca4abdaf177f748c5179d9c7138618751641780b589baf7ac2efdf4ff"
    review_path = ROOT / "portable/tests/recovered/evidence/next9-profile-regeneration-review-20261002/review.json"
    review = json.loads(review_path.read_text(encoding="utf-8"))
    if review.get("status") != "PASS" or review.get("current_profile_sha256") != expected_profile_sha:
        raise SystemExit("reviewed Next9 profile receipt is absent or disagrees with the approved profile pin")
    current_profile = GEN_PROFILE / "provenance.json"
    if not current_profile.is_file() or sha(current_profile) != expected_profile_sha:
        current_sha = sha(current_profile) if current_profile.is_file() else None
        raise SystemExit(
            "refusing to regenerate or test against an unreviewed Next9 profile identity: "
            f"V3 pins {expected_profile_sha}, current generated profile {current_sha}. "
            "The shared generated profile is read-only input to V4; resolve identity first."
        )
    source_inputs_before = snapshot_readonly_inputs()
    sentinels_before = {
        key(SENTINELS): sha(SENTINELS),
        key(ROOT / "portable/tests/save/support/next9_source_sentinels_v3.h"):
            sha(ROOT / "portable/tests/save/support/next9_source_sentinels_v3.h"),
    }

    BUILD.mkdir(parents=True, exist_ok=True)
    producer_outputs = {
        "next9_profile": "reviewed existing generated profile is pinned input; no producer invoked",
        "v3_binding_generator": "pinned lineage input; not executed",
    }
    if sha(SENTINELS) != sentinels_before[key(SENTINELS)] or \
       sha(ROOT / "portable/tests/save/support/next9_source_sentinels_v3.h") != \
       sentinels_before[key(ROOT / "portable/tests/save/support/next9_source_sentinels_v3.h")]:
        raise RuntimeError("V3 sentinel sources changed while refreshing V4 proof")
    if tree_hashes(V3_PACKET) != v3_before or sha(V3_RUNNER) != v3_runner_before:
        raise RuntimeError("V3 packet or runner changed during V4 refresh")

    # Re-run the actual original DOS function and obtain a fresh source-address
    # payload. The V4 probe writes only under its own build directory.
    producer_outputs["original_dos_probe"] = run_script(PROBE)
    if not PAYLOAD.is_file():
        raise RuntimeError("original DOS probe did not produce the sentinel payload")
    dos_report_path = BUILD / "original-dos-sentinel-report.json"
    dos_report = json.loads(dos_report_path.read_text(encoding="utf-8"))
    payload_sha = sha(PAYLOAD)
    if dos_report.get("write_calls") != 307 or dos_report.get("payload_bytes") != 48386 or \
       dos_report.get("payload_sha256") != payload_sha or dos_report.get("status") != \
       "PASS_ORIGINAL_DOS_SOURCE_ADDRESS_TRACE":
        raise RuntimeError("original DOS probe did not satisfy its 307-write/48,386-byte contract")

    cc_name = shutil.which("gcc")
    if cc_name is None:
        raise RuntimeError("gcc is unavailable")
    cc = Path(cc_name).resolve()
    cc_version = subprocess.check_output([str(cc), "--version"], text=True).splitlines()[0]
    cc_target = subprocess.check_output([str(cc), "-dumpmachine"], text=True).strip()
    gcc_files = compiler_files(cc)
    msc_files = msc_toolchain_files()
    compiler_sha_before = hash_files([*gcc_files, *msc_files])

    runs = [
        compile_run(cc, "positive-little-endian", PAYLOAD),
        compile_run(cc, "positive-forced-big-endian", PAYLOAD, big_endian=True),
        compile_run(cc, "negative-swapped-rows", PAYLOAD, mutant="swap-48-49"),
        compile_run(cc, "negative-component-width", PAYLOAD, big_endian=True,
                    mutant="row48-wide-component"),
        compile_run(cc, "negative-row99-storage", PAYLOAD, big_endian=True,
                    mutant="row99-numeric"),
    ]

    source_inputs_after = snapshot_readonly_inputs()
    compiler_sha_after = hash_files([*gcc_files, *msc_files])
    if source_inputs_before != source_inputs_after:
        before_keys = set(source_inputs_before) | set(source_inputs_after)
        changed = [p for p in sorted(before_keys)
                   if source_inputs_before.get(p) != source_inputs_after.get(p)]
        raise RuntimeError(f"V4 proof inputs changed during execution: {changed}")
    if compiler_sha_before != compiler_sha_after:
        raise RuntimeError("GCC or MSC toolchain files changed during V4 execution")
    if tree_hashes(V3_PACKET) != v3_before or sha(V3_RUNNER) != v3_runner_before:
        raise RuntimeError("V3 packet or runner changed during native tests")

    binding_map_path = V3_PACKET / "binding-map.json"
    binding_map = json.loads(binding_map_path.read_text(encoding="utf-8"))
    sentinel_members = binding_map.get("sentinel_members", [])
    if len(sentinel_members) != 410:
        raise RuntimeError(f"expected 410 independent source sentinels; got {len(sentinel_members)}")
    if sum(1 for r in json.loads((ROOT / "portable/tests/dialogs/evidence/savegame-format-source-inventory-v1/save-records.json").read_text(encoding="utf-8"))["table"]["records"]) != 307:
        raise RuntimeError("SaveRec inventory row count is not 307")
    if len(runs) != 5 or sum(not r["expected_failure"] for r in runs) != 2 or \
       sum(r["expected_failure"] for r in runs) != 3:
        raise RuntimeError("positive/negative control count is wrong")

    # GCC-MM closure is complete per translation-unit/per variant. Pool it for
    # convenient auditing while retaining the exact per-run closures above.
    closure = {}
    for row in runs:
        for path, digest in row["local_dependency_sha256"].items():
            previous = closure.setdefault(path, digest)
            if previous != digest:
                raise RuntimeError(f"dependency changed between variants: {path}")
    if "portable/game/save/legacy_codec.h" not in closure:
        raise RuntimeError("V4 dependency closure failed to pin legacy_codec.h")

    # Source identities are recorded both before and after; equality above is a
    # mandatory condition, not a post-hoc note.
    external_files = hash_files([
        *gcc_files, *msc_files, *sorted((ROOT / "assets").glob("*")),
        ROOT / "assets/SIMANT.EXE", ROOT / "tools/behavior.py",
        *PYTHON_INPUTS, *DOS_LAYOUT_INPUTS,
    ])
    PACKET.mkdir(parents=True, exist_ok=False)
    shutil.copyfile(V3_PACKET / "binding-map.json", PACKET / "binding-map.json")
    shutil.copyfile(dos_report_path, PACKET / "original-dos-sentinel-report.json")
    native_report = {
        "schema": "simant-next9-bindings-v4-test-report-v1",
        "status": "PASS_DIAGNOSTIC_NOT_PRODUCTION",
        "v3_packet_sha256_before_after": hashlib.sha256(json.dumps(v3_before, sort_keys=True).encode()).hexdigest(),
        "v3_runner_sha256_before_after": v3_runner_before,
        "original_payload_sha256": payload_sha,
        "original_dos_write_calls": dos_report["write_calls"],
        "original_dos_payload_bytes": dos_report["payload_bytes"],
        "independent_source_sentinel_members": len(sentinel_members),
        "native_save_rows": 307,
        "native_payload_bytes": 48386,
        "positive_count": 2,
        "negative_count": 3,
        "runs": runs,
    }
    (PACKET / "native-validation.json").write_text(
        json.dumps(native_report, indent=2) + "\n", encoding="utf-8", newline="")
    pins = {
        "schema": "simant-next9-save-v4-source-pins-v1",
        "status": "DIAGNOSTIC_NOT_PRODUCTION",
        "source_inputs_before_sha256": source_inputs_before,
        "source_inputs_after_sha256": source_inputs_after,
        "source_inputs_stable": source_inputs_before == source_inputs_after,
        "gcc_version": cc_version,
        "gcc_target": cc_target,
        "gcc_toolchain_sha256_before": hash_files(gcc_files),
        "gcc_toolchain_sha256_after": hash_files(gcc_files),
        "msc_toolchain_sha256_before": hash_files(msc_files),
        "msc_toolchain_sha256_after": hash_files(msc_files),
        "external_file_sha256": external_files,
        "gcc_mm_local_dependency_union": closure,
        "gcc_mm_dependencies_per_run": {
            row["name"]: row["local_dependency_sha256"] for row in runs},
        "v3_packet_file_sha256_before_after": v3_before,
        "v3_runner_sha256_before_after": v3_runner_before,
        "original_dos_report_sha256": sha(dos_report_path),
        "native_validation_sha256": sha(PACKET / "native-validation.json"),
        "binding_map_sha256": sha(PACKET / "binding-map.json"),
        "generator_stdout": producer_outputs,
    }
    (PACKET / "source-pins.json").write_text(
        json.dumps(pins, indent=2) + "\n", encoding="utf-8", newline="")
    readme = f'''# Next9 SaveRec binding validation (V4 closure refresh)

This packet refreshes V3's 307-row SaveRec source-address sentinel experiment and closes its transitive native-source pin gap. It is diagnostic evidence only; it does not register or claim production save behavior.

The native build uses the unchanged `next9_bindings_v3.c`, `next9_bindings_v3.h`, and row include. The independently derived sentinel catalog contains {len(sentinel_members)} typed state members; original DOS `SaveGame` executed {dos_report['write_calls']} writes and produced a {dos_report['payload_bytes']}-byte stream. The two positive native runs (host little endian and forced big endian) matched that stream exactly. The three negative controls failed as intended: swapping rows 48/49, widening row 48, and treating raw row 99 as numeric.

Unlike V3, V4 records GCC `-MM` local dependency closures for all five compiled variants. The closure includes `portable/game/save/legacy_codec.h`, an unconditional include of `legacy_codec.c` that V3's manually assembled pins omitted. Active C/header/include inputs, Python producers and validators, GCC and MSC compiler files, original executable, all root assets, and DOS harness inputs are pinned before/after. V3 packet files and `run_next9_bindings_v3.py` are hashed before and after and were required to remain unchanged.

Reproduce from the repository root with `python portable/tests/save/run_next9_bindings_v4.py`. It refuses to overwrite this packet and requires the reviewed Next9 provenance receipt pinned in `source-pins.json`. The profile is read-only input; no Next9 recovery or binding generator is executed. A V4-specific copy of the original DOS probe writes only under `build/workers/savegame_sentinel_v4`. The runner obtains GCC `-MM` closures, compiles/runs the two positives and three negatives, and writes a fresh V4 directory only after every assertion succeeds.

The contract remains bounded to the recorded source-address sentinel state and exact 307 DOS writer calls. It is not a general save lifecycle, file-system, or arbitrary runtime-state proof.
'''
    (PACKET / "README.md").write_text(readme, encoding="utf-8", newline="")
    print(f"V4 PASS: 2 positives, 3 expected negatives; {len(sentinel_members)} sentinels, "
          f"{dos_report['write_calls']} DOS writes, {dos_report['payload_bytes']} bytes")
    print(f"packet={key(PACKET)}")


if __name__ == "__main__":
    main()
