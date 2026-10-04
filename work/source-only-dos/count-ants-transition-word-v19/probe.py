"""Fresh MSC/RTLink storage and view controls for one saved FAR_BSS word."""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "build/workers/dos_saved_scalar_words_v19"
RUNTIME = OUT / "runtime/durable-v19"
FIXTURES = RUNTIME / "fixtures"
REPORT = RUNTIME / "saved-scalar-words-probe-v19.json"
NAME = "fd_50F6_0354"
SYMBOL = "_" + NAME
PROFILE = "msc600ax"
FLAGS = ["/AL", "/Os", "/Oe", "/Og", "/Zi"]

import sys
sys.path.insert(0, str(ROOT / "tools"))
import compiler
import dos_source_bindings as bindings
import source_only_dos as dos
from omf import OmfReader


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def pin(path: Path, expected: str | None = None) -> dict:
    path = path.resolve()
    raw = path.read_bytes()
    actual = digest(raw)
    if expected is not None and actual != expected:
        raise RuntimeError(f"pinned input changed: {path}")
    try:
        relative = path.relative_to(ROOT).as_posix()
    except ValueError:
        relative = str(path)
    return {"path": relative, "sha256": actual, "size": len(raw)}


def compile_source(stem: str, source: str, flags: list[str] | None = None):
    if len(stem) > 8:
        raise ValueError("MSC object stem must fit the DOS 8.3 basename")
    cpath = FIXTURES / f"{stem}.c"
    opath = FIXTURES / f"{stem}.OBJ"
    cpath.parent.mkdir(parents=True, exist_ok=True)
    cpath.write_text(source, encoding="ascii", newline="")
    result = compiler.compile_c(source, PROFILE, flags or FLAGS, basename=stem)
    if not result.ok:
        raise RuntimeError(f"compile failed for {stem}:\n{result.log}")
    opath.write_bytes(result.obj)
    return cpath, opath, result.obj, result.log


def communal_for(obj_bytes: bytes) -> list[dict]:
    return [row for row in OmfReader(communals=True).read(obj_bytes).communals
            if row["name"] == SYMBOL]


def make_consumer_sources() -> dict[str, str]:
    return {
        "typed_word": f'''extern int far {NAME};
extern int far ProbeAlias;
extern int far puts(char far *text);
int main(void)
{{
    if (&{NAME} != &ProbeAlias) {{ puts("FAIL_ALIAS"); return 1; }}
    if ({NAME} != 0) {{ puts("FAIL_STARTUP"); return 2; }}
    {NAME} = -1234;
    if ({NAME} != -1234) {{ puts("FAIL_SIGNED_WORD"); return 3; }}
    puts("PASS_TYPED_WORD");
    return 0;
}}
''',
        "saverec_byte": f'''struct SaveRec {{ int size; int count; void far *data; }};
extern int far {NAME};
extern int far puts(char far *text);
static struct SaveRec probe_row = {{ 2, 1, (void far *)&{NAME} }};
int main(void)
{{
    unsigned char far *p;
    if (probe_row.size != 2 || probe_row.count != 1) {{ puts("FAIL_SAVEREC_ROW"); return 1; }}
    p = (unsigned char far *)probe_row.data;
    if (p[0] != 0 || p[1] != 0) {{ puts("FAIL_SAVEREC_STARTUP"); return 2; }}
    {NAME} = 0x1234;
    if (p[0] != 0x34 || p[1] != 0x12) {{ puts("FAIL_WORD_TO_BYTE"); return 3; }}
    p[0] = 0x78; p[1] = 0x56;
    if ({NAME} != 0x5678) {{ puts("FAIL_BYTE_TO_WORD"); return 4; }}
    puts("PASS_SAVEREC_BYTE");
    return 0;
}}
''',
        "wrong_width": f'''extern int far {NAME};
extern int far ProbeUpperWord;
extern long far ProbeWhole;
extern int far puts(char far *text);
int main(void)
{{
    {NAME} = 0x1234;
    ProbeUpperWord = 0x5678;
    if (ProbeWhole == 0x56781234L) {{ puts("WRONG_WIDTH_FOUR_BYTE_OWNER_DETECTED"); return 0; }}
    puts("FAIL_WIDTH_CONTRAST");
    return 1;
}}
''',
        "wrong_signedness": f'''extern unsigned int far {NAME};
extern int far puts(char far *text);
int main(void)
{{
    {NAME} = -1;
    if ({NAME} > 32767U) {{ puts("WRONG_UNSIGNED_VIEW_DETECTED"); return 0; }}
    puts("FAIL_SIGNEDNESS_CONTRAST");
    return 1;
}}
''',
        "initialized_owner": f'''extern int far {NAME};
extern int far puts(char far *text);
int main(void)
{{
    if ({NAME} != 0) {{ puts("INITIALIZED_OWNER_DETECTED"); return 0; }}
    puts("FAIL_INITIALIZED_CONTRAST");
    return 1;
}}
''',
        "wrong_alias_base": f'''extern int far {NAME};
extern int far ProbeAlias;
extern int far puts(char far *text);
int main(void)
{{
    if (&{NAME} != &ProbeAlias) {{ puts("SHIFTED_ALIAS_BASE_DETECTED"); return 0; }}
    puts("FAIL_ALIAS_BASE_CONTRAST");
    return 1;
}}
''',
    }


def case_link(profile: str, case: str, consumer_obj: bytes, owner_obj: bytes,
              aliases: list[str], expected: str, runtime_libraries: list[dict],
              linker: dict, runner: dict, tool_dir: Path) -> dict:
    folder = RUNTIME / profile / case
    folder.mkdir(parents=True, exist_ok=True)
    try:
        folder.resolve().relative_to(RUNTIME.resolve())
    except ValueError as exc:
        raise RuntimeError("runtime fixture escaped durable-v19") from exc
    for leaf in ("PROBE.EXE", "PROBE.MAP", "RUN.LOG", "LINK.LOG"):
        (folder / leaf).unlink(missing_ok=True)
    (folder / "CRT.OBJ").write_bytes(consumer_obj)
    (folder / "OWNER.OBJ").write_bytes(owner_obj)
    for row in runtime_libraries:
        shutil.copyfile(row["path"], folder / Path(row["path"]).name.upper())

    link_script = (
        "OUTPUT PROBE\r\nMAP = PROBE S,N,A,L\r\nNODEFLIB\r\n"
        "LIBRARY LLIBCR, LIBH\r\nFILE CRT\r\n"
        "BEGINAREA\r\nSECTION FILE OWNER\r\nENDAREA\r\n"
    ) + "".join(alias + "\r\n" for alias in aliases)
    (folder / "PROBE.LNK").write_bytes(link_script.encode("ascii"))
    (folder / "RTLINK.CFG").write_bytes(b"SYNTAX = FREEFORMAT\r\n")
    (folder / "RUN.BAT").write_bytes((
        f"@echo off\r\nD:\\{linker['executable']} @PROBE.LNK < NUL > LINK.LOG\r\n"
        "PROBE.EXE > RUN.LOG\r\n").encode("ascii"))
    conf_lines = []
    for section, settings in runner["conf"].items():
        conf_lines.append("[" + section + "]")
        conf_lines.extend(f"{key}={value}" for key, value in settings.items())
    conf_lines.extend(["[autoexec]", f'mount c "{folder}"', f'mount d "{tool_dir}" -ro',
                       "c:", "call RUN.BAT", "exit"])
    (folder / "dosbox.conf").write_text("\n".join(conf_lines) + "\n", encoding="utf-8")

    env = os.environ.copy()
    env.update(SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy")
    timed_out = False
    try:
        done = subprocess.run([runner["path"], "-conf", str(folder / "dosbox.conf"),
                               "-fastlaunch", "-exit", "-nomenu"], cwd=folder, env=env,
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                              timeout=90, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        return_code = done.returncode
    except subprocess.TimeoutExpired:
        timed_out = True
        return_code = -1

    run_log = folder / "RUN.LOG"
    link_log = folder / "LINK.LOG"
    map_path = folder / "PROBE.MAP"
    run_text = run_log.read_text(encoding="latin1", errors="replace").strip() if run_log.exists() else "NO_RUN_LOG"
    link_text = link_log.read_text(encoding="latin1", errors="replace") if link_log.exists() else "NO_LINK_LOG"
    map_text = map_path.read_text(encoding="latin1", errors="replace") if map_path.exists() else ""
    link_clean = (folder / "PROBE.EXE").exists() and not timed_out and not any(
        token in link_text.lower() for token in ("unresolved external", "undefined symbol", "link error"))
    alias_names = [match.group(1) for match in re.finditer(r"(?im)^DEFINE\s+(_[A-Za-z0-9_]+)\s*=", link_script)]
    map_clean = (bool(map_text) and SYMBOL in map_text and
                 all(alias_name in map_text for alias_name in alias_names))
    files = []
    for path in sorted(folder.iterdir(), key=lambda p: p.name.lower()):
        if path.is_file():
            files.append(pin(path))
    passed = run_text == expected and return_code == 0 and not timed_out and link_clean and map_clean
    return {
        "linker": profile, "case": case, "expected_output": expected,
        "actual_output": run_text, "passed": passed,
        "runner_returncode": return_code, "timed_out": timed_out,
        "exe_created": (folder / "PROBE.EXE").exists(),
        "link_clean": link_clean, "map_clean": map_clean,
        "aliases": aliases,
        "map_rows": [line for line in map_text.splitlines()
                     if SYMBOL in line or "ProbeAlias" in line or
                     "ProbeUpperWord" in line or "ProbeWhole" in line],
        "link_log_tail": link_text[-1200:], "files": files,
    }


def main() -> None:
    RUNTIME.mkdir(parents=True, exist_ok=True)
    FIXTURES.mkdir(parents=True, exist_ok=True)
    compiler.WORK = RUNTIME / "compiler-work"
    denied_reads = dos.install_input_guard()

    manifest_path = ROOT / "layout/manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    toolchain = compiler.toolchain()
    compiler_rows = compiler.verify_profile(PROFILE)
    runtime_libraries = list(manifest["runtime"]["libraries"].values())
    runner = toolchain["runners"]["dosbox-x"]
    provider_path = OUT / "providers/saved-scalar-words-v19.c"
    provider_source = provider_path.read_text(encoding="ascii")

    owner_path, owner_obj_path, owner_obj, owner_log = compile_source("OWNV19", provider_source)
    long_path, long_obj_path, long_obj, long_log = compile_source("LONGV19", f"long far {NAME};\n")
    unsigned_path, unsigned_obj_path, unsigned_obj, unsigned_log = compile_source(
        "UNSGV19", f"unsigned int far {NAME};\n")
    init_path, init_obj_path, init_obj, init_log = compile_source("INITY19", f"int far {NAME} = 1;\n")
    consumers = {key: compile_source({
        "typed_word": "WORDV19", "saverec_byte": "BYTEV19", "wrong_width": "WIDV19",
        "wrong_signedness": "SGNV19", "initialized_owner": "ZROV19",
        "wrong_alias_base": "ALSV19",
    }[key], source) for key, source in make_consumer_sources().items()}

    correct_rows = communal_for(owner_obj)
    long_rows = communal_for(long_obj)
    unsigned_rows = communal_for(unsigned_obj)
    init_omf = OmfReader(communals=True).read(init_obj)
    if len(correct_rows) != 1 or correct_rows[0]["length"] != 2:
        raise RuntimeError(f"signed int provider is not one 2-byte far communal: {correct_rows}")
    if len(long_rows) != 1 or long_rows[0]["length"] != 4:
        raise RuntimeError(f"long-width negative control did not produce 4 bytes: {long_rows}")
    if len(unsigned_rows) != 1 or bindings.communal_key(correct_rows[0]) != bindings.communal_key(unsigned_rows[0]):
        raise RuntimeError("signedness control should retain the same OMF shape; source semantics carry signedness")
    if any(row["name"] == SYMBOL for row in init_omf.communals) or not any(
            row["name"] == SYMBOL for row in init_omf.publics):
        raise RuntimeError("initialized owner control did not replace the far communal with an initialized public")

    consumer_objs = {key: value[2] for key, value in consumers.items()}
    cases = []
    case_specs = [
        ("typed_word", consumer_objs["typed_word"], owner_obj,
         [f"DEFINE _ProbeAlias = {SYMBOL}"], "PASS_TYPED_WORD"),
        ("saverec_byte", consumer_objs["saverec_byte"], owner_obj, [], "PASS_SAVEREC_BYTE"),
        ("wrong_width_long_owner", consumer_objs["wrong_width"], long_obj,
         [f"DEFINE _ProbeUpperWord = {SYMBOL} + 2",
          f"DEFINE _ProbeWhole = {SYMBOL}"], "WRONG_WIDTH_FOUR_BYTE_OWNER_DETECTED"),
        ("wrong_signedness_unsigned_view", consumer_objs["wrong_signedness"], owner_obj,
         [], "WRONG_UNSIGNED_VIEW_DETECTED"),
        ("initialized_nonzero_owner", consumer_objs["initialized_owner"], init_obj,
         [], "INITIALIZED_OWNER_DETECTED"),
        ("wrong_alias_base_plus_two", consumer_objs["wrong_alias_base"], owner_obj,
         [f"DEFINE _ProbeAlias = {SYMBOL} + 2"], "SHIFTED_ALIAS_BASE_DETECTED"),
    ]
    all_input_pins = [pin(Path(__file__)), pin(provider_path), pin(manifest_path),
                      pin(ROOT / "layout/toolchain.json"), pin(ROOT / "layout/symbols.json"),
                      pin(ROOT / "tools/compiler.py"), pin(ROOT / "tools/omf.py"),
                      pin(ROOT / "tools/dos_source_bindings.py"), pin(ROOT / "tools/source_only_dos.py"),
                      pin(owner_path), pin(owner_obj_path), pin(long_path), pin(long_obj_path),
                      pin(unsigned_path), pin(unsigned_obj_path), pin(init_path), pin(init_obj_path)]
    for source_path, object_path, _, _ in consumers.values():
        all_input_pins.extend((pin(source_path), pin(object_path)))
    for relative, expected_hash in compiler_rows["files"].items():
        all_input_pins.append(pin(Path(compiler_rows["directory"]) / relative, expected_hash))
    all_input_pins.append(pin(Path(runner["path"]), runner["sha256"]))
    for row in runtime_libraries:
        all_input_pins.append(pin(Path(row["path"]), row["sha256"]))

    for linker_name in ("rtlink400", "rtlink610"):
        linker = toolchain["linkers"][linker_name]
        for relative, expected_hash in linker["files"].items():
            all_input_pins.append(pin(Path(linker["directory"]) / relative, expected_hash))
        tool_dir = compiler.pinned_tree(linker)
        for case, consumer, owner, aliases, expected in case_specs:
            result = case_link(linker_name, case, consumer, owner, aliases, expected,
                               runtime_libraries, linker, runner, tool_dir)
            cases.append(result)
            if not result["passed"]:
                raise RuntimeError("runtime control failed: " + json.dumps(result, indent=2))

    artifact_paths = [provider_path, Path(__file__), owner_path, owner_obj_path,
                      long_path, long_obj_path, unsigned_path, unsigned_obj_path,
                      init_path, init_obj_path]
    for source_path, object_path, _, _ in consumers.values():
        artifact_paths.extend((source_path, object_path))
    artifact_paths.append(Path(__file__))
    artifact_paths.extend(path for case in cases for path in
                          (RUNTIME / case["linker"] / case["case"]).iterdir() if path.is_file())
    artifacts = []
    seen = set()
    for path in sorted(artifact_paths, key=lambda p: str(p).lower()):
        resolved = path.resolve()
        if resolved not in seen:
            seen.add(resolved)
            artifacts.append(pin(path))

    report = {
        "schema": "simant-dos-saved-scalar-words-probe-v19",
        "status": "SCRATCH_ONLY_ROOT_REVIEW_PENDING",
        "provider": {"source": pin(provider_path), "source_shape": "one data-only int far tentative definition",
                     "omf_communal": correct_rows, "object": pin(owner_obj_path),
                     "source_function_definitions": 0},
        "controls": {
            "wrong_width": {"source": pin(long_path), "omf_communal": long_rows,
                            "expected_length": 4, "measured_length": 4},
            "wrong_signedness": {"source": pin(unsigned_path), "omf_communal": unsigned_rows,
                                 "omf_shape_matches_signed_int": True,
                                 "semantic_contrast": "unsigned consumer writes -1 and sees 65535 > 32767; the source graph's signed int view is the correct signed-word contract"},
            "initialized_owner": {"source": pin(init_path),
                                  "target_communal_absent": True,
                                  "target_initialized_public_present": True},
            "alias_base": {"exact_alias_positive": "typed_word case binds ProbeAlias exactly to candidate base",
                           "wrong_alias_negative": "ProbeAlias = candidate + 2 is detected by far-pointer comparison"},
        },
        "runtime": {"cases": cases, "all_expected_outcomes_pass": len(cases) == 12 and all(row["passed"] for row in cases),
                    "linkers": ["rtlink400", "rtlink610"],
                    "startup": "MSC 6.00AX large-model main under the pinned runtime libraries; positive word/SaveRec cases assert zero FAR_BSS at main",
                    "game_functions_or_stubs": 0, "original_game_objects_or_bytes": 0},
        "inputs": all_input_pins,
        "artifacts": artifacts,
        "denied_oracle_reads": denied_reads,
        "limits": ["OMF has identical signed-int and unsigned-int communal shape; signedness is source semantics and the unsigned high-bit consumer is a behavioral negative contrast",
                   "the long-owner case uses fixture-only +2 word alias to make the extra four-byte extent observable",
                   "no original COMDEF TU/order, production placement, or canonical admission is claimed"],
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"report": str(REPORT.relative_to(ROOT)),
                      "all_expected_outcomes_pass": report["runtime"]["all_expected_outcomes_pass"],
                      "runtime_cases": len(cases), "provider_omf": correct_rows}, indent=2))


if __name__ == "__main__":
    main()
