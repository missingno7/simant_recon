"""Fresh MSC/RTLink runtime fixture for the unadmitted data-only provider."""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "work/source-only-dos"
PROVIDER = PACKAGE / "providers/population-work-arrays.c"
OUT = ROOT / "build/dos_population_work_arrays/durable-v18"
FIXTURES = OUT / "fixtures"
sys.path.insert(0, str(ROOT / "tools"))
import compiler  # noqa: E402
import modules  # noqa: E402
from omf import OmfReader  # noqa: E402

OWNER_FLAGS = ["/AL", "/Os", "/Oe", "/Og", "/Zi"]
CONSUMER_FLAGS = ["/AL", "/Os", "/Zi"]
BYTE_OWNER = r'''unsigned char far fd_50F6_0AEC[12];
int far fd_50F6_0AFA[6];
void far SeedPopulation(void)
{
    int i;
    for (i = 0; i < 12; i++) fd_50F6_0AEC[i] = i + 1;
    for (i = 0; i < 6; i++) fd_50F6_0AFA[i] = 0x0200 + i;
}
'''
SHORT_OWNER = r'''struct BlueShortBlock { int words[5]; int guard; };
struct BlueShortBlock far fd_50F6_0AEC;
int far fd_50F6_0AFA[6];
void far SeedPopulation(void)
{
    int i;
    for (i = 0; i < 5; i++) fd_50F6_0AEC.words[i] = 0x0100 + i;
    fd_50F6_0AEC.guard = 0;
    for (i = 0; i < 6; i++) fd_50F6_0AFA[i] = 0x0200 + i;
}
int far ExtentGuardWasWritten(void) { return fd_50F6_0AEC.guard == 0x3579; }
'''


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def file_receipt(path: Path, label: str | None = None) -> dict:
    raw = path.read_bytes()
    return {"path": label or path.relative_to(ROOT).as_posix(), "sha256": sha(raw), "size": len(raw)}


def compile_c(name: str, text: str, flags: list[str]) -> dict:
    FIXTURES.mkdir(parents=True, exist_ok=True)
    src_path = FIXTURES / f"{name}.c"
    src_path.write_bytes(text.encode("ascii"))
    result = compiler.compile_c(text, "msc600ax", flags, basename=name)
    if not result.ok or result.obj is None:
        raise RuntimeError(f"{name} compile failed:\n{result.log}")
    obj_path = FIXTURES / f"{name}.OBJ"
    obj_path.write_bytes(result.obj)
    omf = OmfReader(communals=True).read(result.obj)
    return {
        "source": file_receipt(src_path), "object": file_receipt(obj_path), "object_bytes": result.obj,
        "flags": flags,
        "communals": [c for c in omf.communals if c["name"].lower() in (
            "_fd_50f6_0aec", "_fd_50f6_0afa")],
        "segments": [{k: d.get(k) for k in ("index", "name", "class", "length", "alignment", "combine", "big")}
                     for d in omf.segment_defs],
        "publics": [p for p in omf.publics if p["name"].startswith(("_SeedPopulation", "_ExtentGuardWasWritten"))],
    }


def consumer_source(mode: str) -> str:
    blue_count = 5 if mode == "wrong_save_count" else 6
    if mode == "wrong_extent":
        producer = "extern int far ExtentGuardWasWritten(void);"
        helper = ""
        special = '''if (ExtentGuardWasWritten()) { puts("FAIL_WITNESS"); return 0; }
        fd_50F6_0AEC[5] = 0x3579;
        if (!ExtentGuardWasWritten()) { puts("FAIL_WITNESS"); return 0; }
        puts("REJECTED_GUARD_OVERLAP"); return 0;'''
    elif mode == "wrong_type":
        producer = "extern void far SeedPopulation(void);"
        helper = ""
        special = '''SeedPopulation();
        if (fd_50F6_0AEC[0] == 0x0100 && fd_50F6_0AEC[1] == 0x0101 &&
            fd_50F6_0AEC[2] == 0x0102 && fd_50F6_0AEC[3] == 0x0103 &&
            fd_50F6_0AEC[4] == 0x0104 && fd_50F6_0AEC[5] == 0x0105) {
            puts("FAIL_WITNESS"); return 0;
        }
        puts("REJECTED"); return 0;'''
    else:
        producer = ""
        helper = '''void far SeedPopulation(void)
{
    int i;
    for (i = 0; i < 6; i++) {
        fd_50F6_0AEC[i] = 0x0100 + i;
        fd_50F6_0AFA[i] = 0x0200 + i;
    }
}
'''
        special = "SeedPopulation();"
    return f'''extern int far fd_50F6_0AEC[6];
extern int far fd_50F6_0AFA[6];
extern int far BlueSaveAlias[6];
extern int far RedSaveAlias[6];
extern int far puts(char far *text);
{producer}
{helper}
struct SaveRec {{ int size; int count; void far *data; }};
struct SaveRec far SaveRows[2] = {{
    {{ 2, {blue_count}, (void far *)&fd_50F6_0AEC }},
    {{ 2, 6, (void far *)&fd_50F6_0AFA }}
}};
int main(void)
{{
    int i;
    unsigned char far *blueBytes;
    unsigned char far *redBytes;
    if (SaveRows[0].size != 2 || SaveRows[0].count != 6 ||
        SaveRows[1].size != 2 || SaveRows[1].count != 6 ||
        SaveRows[0].data != (void far *)&BlueSaveAlias[0] ||
        SaveRows[1].data != (void far *)&RedSaveAlias[0] ||
        (void far *)&fd_50F6_0AEC[0] != (void far *)&BlueSaveAlias[0] ||
        (void far *)&fd_50F6_0AFA[0] != (void far *)&RedSaveAlias[0]) {{
        puts("REJECTED"); return 0;
    }}
    blueBytes = (unsigned char far *)SaveRows[0].data;
    redBytes = (unsigned char far *)SaveRows[1].data;
    for (i = 0; i < 6; i++)
        if (fd_50F6_0AEC[i] != 0 || fd_50F6_0AFA[i] != 0) {{
            puts("FAIL_WITNESS"); return 0;
        }}
    {special}
    for (i = 0; i < 6; i++)
        if (fd_50F6_0AEC[i] != 0x0100 + i || fd_50F6_0AFA[i] != 0x0200 + i) {{
            puts("REJECTED"); return 0;
        }}
    blueBytes[0] = 0x34; blueBytes[1] = 0x12;
    blueBytes[10] = 0x68; blueBytes[11] = 0x24;
    redBytes[0] = 0x78; redBytes[1] = 0x56;
    redBytes[10] = 0xbc; redBytes[11] = 0x6a;
    if (fd_50F6_0AEC[0] != 0x1234 || fd_50F6_0AEC[5] != 0x2468 ||
        fd_50F6_0AFA[0] != 0x5678 || fd_50F6_0AFA[5] != 0x6abc ||
        blueBytes[10] != 0x68 || blueBytes[11] != 0x24 ||
        redBytes[10] != 0xbc || redBytes[11] != 0x6a) {{
        puts("REJECTED"); return 0;
    }}
    puts("PASS"); return 0;
}}
'''


def map_symbols(map_text: str, names: tuple[str, ...]) -> dict[str, list[dict]]:
    result: dict[str, list[dict]] = {}
    for line in map_text.splitlines():
        match = re.match(r"\s*([0-9A-Fa-f]{4}):([0-9A-Fa-f]{4})\s+(Res|Ovl|U)\s+(_\S+)", line)
        if match and match.group(4) in names:
            result.setdefault(match.group(4), []).append({
                "segment": int(match.group(1), 16), "offset": int(match.group(2), 16), "state": match.group(3)})
    return result


def run_case(profile: str, case: dict, owner_obj: bytes, consumer_obj: bytes,
             runtime_rows: list[dict], linker: dict, runner: dict, tool_dir: Path) -> dict:
    d = OUT / "rtlink" / profile / case["name"]
    d.mkdir(parents=True, exist_ok=True)
    for filename in ("PROBE.EXE", "PROBE.MAP", "RUN.LOG", "LINK.LOG", "DOSBOX-HOST.LOG"):
        (d / filename).unlink(missing_ok=True)
    (d / "CRT.OBJ").write_bytes(consumer_obj)
    (d / "OWNER.OBJ").write_bytes(owner_obj)
    for row in runtime_rows:
        shutil.copyfile(row["path"], d / Path(row["path"]).name.upper())
    delta = case.get("alias_blue_delta", 0)
    suffix = f" + {delta:X}" if delta else ""
    link = ("OUTPUT PROBE\r\nMAP = PROBE S,N,A,L\r\nNODEFLIB\r\nLIBRARY LLIBCR, LIBH\r\n"
            "FILE CRT\r\nBEGINAREA\r\nSECTION FILE OWNER\r\nENDAREA\r\n"
            f"DEFINE _BlueSaveAlias = _fd_50F6_0AEC{suffix}\r\n"
            "DEFINE _RedSaveAlias = _fd_50F6_0AFA\r\n")
    (d / "PROBE.LNK").write_bytes(link.encode("ascii"))
    (d / "RTLINK.CFG").write_bytes(b"SYNTAX = FREEFORMAT\r\n")
    (d / "RUN.BAT").write_bytes((f"@echo off\r\nD:\\{linker['executable']} @PROBE.LNK < NUL > LINK.LOG\r\n"
                                 "PROBE.EXE > RUN.LOG\r\n").encode("ascii"))
    conf_lines = []
    for section, settings in runner["conf"].items():
        conf_lines.append("[" + section + "]")
        conf_lines += [f"{key}={value}" for key, value in settings.items()]
    conf_lines += ["[autoexec]", f'mount c "{d}"', f'mount d "{tool_dir}" -ro',
                   "c:", "call RUN.BAT", "exit"]
    conf_path = d / "dosbox.conf"
    conf_path.write_text("\n".join(conf_lines) + "\n", encoding="ascii")
    env = os.environ.copy()
    env.update(SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy")
    timed = False
    try:
        proc = subprocess.run([runner["path"], "-conf", str(conf_path), "-fastlaunch", "-exit", "-nomenu"],
                              cwd=d, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=60,
                              creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    except subprocess.TimeoutExpired as error:
        timed = True
        host_output = (error.stdout or b"") + (error.stderr or b"")
        return_code = -1
    else:
        host_output = proc.stdout
        return_code = proc.returncode
    (d / "DOSBOX-HOST.LOG").write_bytes(host_output)
    actual = (d / "RUN.LOG").read_text(encoding="latin1").strip() if (d / "RUN.LOG").exists() else "NO RUN.LOG"
    link_log = (d / "LINK.LOG").read_text(encoding="latin1", errors="replace") if (d / "LINK.LOG").exists() else ""
    map_text = (d / "PROBE.MAP").read_text(encoding="latin1", errors="replace") if (d / "PROBE.MAP").exists() else ""
    names = ("_fd_50F6_0AEC", "_fd_50F6_0AFA", "_BlueSaveAlias", "_RedSaveAlias")
    if case["name"] == "wrong_sixth_word_array_extent":
        names += ("_ExtentGuardWasWritten",)
    rows = map_symbols(map_text, names)
    allowed = {"_ExtentGuardWasWritten": {"Res", "Ovl"}}
    unresolved = [name for name in names if not rows.get(name) or
                  any(item["state"] not in allowed.get(name, {"Res"}) for item in rows[name])]
    link_clean = not re.search(r"warning\s+wrt|undefined symbol|error\s+wrt", link_log, re.I)
    def one_position(symbol: str):
        unique = {(item["segment"], item["offset"], item["state"]) for item in rows.get(symbol, [])}
        return next(iter(unique)) if len(unique) == 1 else None
    positions = {name: one_position(name) for name in names}
    alias_positions_ok = (positions.get("_fd_50F6_0AEC") is not None and
                          positions.get("_fd_50F6_0AFA") is not None and
                          positions.get("_RedSaveAlias") == positions.get("_fd_50F6_0AFA"))
    if case.get("alias_blue_delta", 0):
        base = positions.get("_fd_50F6_0AEC")
        alias = positions.get("_BlueSaveAlias")
        alias_positions_ok = alias_positions_ok and base is not None and alias == (base[0], base[1] + 2, base[2])
    else:
        alias_positions_ok = alias_positions_ok and positions.get("_BlueSaveAlias") == positions.get("_fd_50F6_0AEC")
    expected = case["expected_output"]
    passed = actual == expected and return_code == 0 and not timed and (d / "PROBE.EXE").exists() \
             and link_clean and not unresolved and alias_positions_ok
    case_files = [file_receipt(path, path.name) for path in sorted(d.iterdir()) if path.is_file()]
    return {"linker": profile, "case": case["name"], "fixture_inputs": case["fixture_inputs"],
            "expected_output": expected, "actual_output": actual, "runner_returncode": return_code,
            "timed_out": timed, "exe_created": (d / "PROBE.EXE").exists(), "link_clean": link_clean,
            "map_clean": not unresolved and alias_positions_ok, "unresolved_symbols": unresolved,
            "map_symbols": rows, "map_rows": [line.strip() for line in map_text.splitlines()
                if any(name in line for name in names)], "link_log_tail": link_log[-1000:],
            "passed": passed, "files": case_files}


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    FIXTURES.mkdir(parents=True, exist_ok=True)
    manifest = modules.load_manifest()
    tc = compiler.toolchain()
    compiler_profile = tc["profiles"]["msc600ax"]
    runner = tc["runners"]["dosbox-x"]
    runtime_rows = list(manifest["runtime"]["libraries"].values())
    for row in runtime_rows:
        if sha(Path(row["path"]).read_bytes()) != row["sha256"]:
            raise RuntimeError(f"runtime library hash mismatch: {row['path']}")

    provider_text = PROVIDER.read_text(encoding="ascii")
    compiled = {"PROVIDER": compile_c("PROVIDER", provider_text, OWNER_FLAGS),
                "OWNBYTE": compile_c("OWNBYTE", BYTE_OWNER, OWNER_FLAGS),
                "OWNEXT": compile_c("OWNEXT", SHORT_OWNER, OWNER_FLAGS)}
    expected_commons = {"_fd_50f6_0aec": (6, 2, 12), "_fd_50f6_0afa": (6, 2, 12)}
    provider_commons = {row["name"].lower(): row for row in compiled["PROVIDER"]["communals"]}
    if {name: (row["count"], row["element_size"], row["length"])
        for name, row in provider_commons.items()} != expected_commons:
        raise RuntimeError(f"data-only provider OMF communal shape differs: {provider_commons}")

    case_specs = [
        {"name": "typed_SaveRec_alias_positive", "owner": "PROVIDER", "mode": "positive",
         "expected_output": "PASS", "owner_input": "data-only provider source", "alias_blue_delta": 0},
        {"name": "wrong_element_type_same_12_byte_extent", "owner": "OWNBYTE", "mode": "wrong_type",
         "expected_output": "REJECTED", "owner_input": "unsigned char far[12] Blue, int far[6] Red"},
        {"name": "wrong_sixth_word_array_extent", "owner": "OWNEXT", "mode": "wrong_extent",
         "expected_output": "REJECTED_GUARD_OVERLAP", "owner_input": "five-word array subobject plus adjacent int guard"},
        {"name": "wrong_exact_base_plus_one_word", "owner": "PROVIDER", "mode": "wrong_base",
         "expected_output": "REJECTED", "alias_blue_delta": 2, "owner_input": "data-only provider source"},
        {"name": "wrong_SaveRec_count_extent", "owner": "PROVIDER", "mode": "wrong_save_count",
         "expected_output": "REJECTED", "owner_input": "data-only provider source"},
    ]
    for case in case_specs:
        consumer_name = {"positive": "CRTGOOD", "wrong_type": "CRTTYPE", "wrong_extent": "CRTEXNT",
                         "wrong_base": "CRTBASE", "wrong_save_count": "CRTSAVE"}[case["mode"]]
        result = compile_c(consumer_name, consumer_source(case["mode"]), CONSUMER_FLAGS)
        compiled[consumer_name] = result
        case["fixture_inputs"] = {
            "owner_source": (file_receipt(PROVIDER, "work/source-only-dos/providers/population-work-arrays.c")
                             if case["owner"] == "PROVIDER" else compiled[case["owner"]]["source"]),
            "owner_object": compiled[case["owner"]]["object"],
            "consumer_source": result["source"], "consumer_object": result["object"],
            "consumer_mode": case["mode"], "owner_shape": case["owner_input"],
            "startup_state": "both six-word vectors must be zero before any seed/write",
            "SaveRec_rows": [{"size": 2, "count": 5 if case["mode"] == "wrong_save_count" and i == 0 else 6}
                             for i in range(2)],
        }

    cases = []
    for profile in ("rtlink400", "rtlink610"):
        linker = tc["linkers"][profile]
        tool_dir = compiler.pinned_tree(linker)
        for case in case_specs:
            consumer_name = {"positive": "CRTGOOD", "wrong_type": "CRTTYPE", "wrong_extent": "CRTEXNT",
                             "wrong_base": "CRTBASE", "wrong_save_count": "CRTSAVE"}[case["mode"]]
            cases.append(run_case(profile, case, compiled[case["owner"]]["object_bytes"],
                                  compiled[consumer_name]["object_bytes"], runtime_rows, linker, runner, tool_dir))

    tools = [ROOT / "tools/compiler.py", ROOT / "tools/modules.py", ROOT / "tools/omf.py",
             ROOT / "layout/toolchain.json", ROOT / "layout/manifest.json"]
    tool_receipts = [file_receipt(path) for path in tools]
    manifest_path = ROOT / "layout/manifest.json"
    provider_receipt = file_receipt(PROVIDER, "work/source-only-dos/providers/population-work-arrays.c")
    report = {
        "schema": "simant-population-work-arrays-probe-v18",
        "status": "SCRATCH_ONLY_UNADMITTED_NO_PROMOTION",
        "provider": {**provider_receipt, "role": "data-only natural C provider; exactly two tentative int far[6] definitions; no functions",
                     "omf_communals": compiled["PROVIDER"]["communals"], "flags": OWNER_FLAGS,
                     "compiler_profile": "msc600ax"},
        "probe_script": file_receipt(Path(__file__), "work/source-only-dos/population-work-arrays-probe-v18.py"),
        "compiler_and_runtime": {
            "compiler_profile": {"name": "msc600ax", "product": compiler_profile["product"],
                "directory": compiler_profile["directory"], "executable": compiler_profile["executable"],
                "flags": OWNER_FLAGS, "profile_files": compiler_profile["files"],
                "include_file_pins": compiler_profile["include_files"]},
            "compiler_tools": tool_receipts,
            "runner": {k: runner.get(k) for k in ("path", "sha256", "conf")},
            "runtime_libraries": [dict(row) for row in runtime_rows],
            "linkers": {name: {"directory": tc["linkers"][name]["directory"],
                "executable": tc["linkers"][name]["executable"], "files": tc["linkers"][name]["files"],
                "profile_note": tc["linkers"][name].get("status")} for name in ("rtlink400", "rtlink610")},
            "consumer_flags": CONSUMER_FLAGS,
        },
        "fixture_inputs": [{"case": case["name"], **case["fixture_inputs"],
            "owner_omf_commons": compiled[case["owner"]]["communals"],
            "consumer_omf_commons": compiled[{"positive": "CRTGOOD", "wrong_type": "CRTTYPE", "wrong_extent": "CRTEXNT",
                "wrong_base": "CRTBASE", "wrong_save_count": "CRTSAVE"}[case["mode"]]]["communals"]}
            for case in case_specs],
        "case_summary": {"fresh_cases_expected": 10, "fresh_cases_passed": sum(case["passed"] for case in cases),
                         "all_five_cases_both_linkers_clean_and_passed": len(cases) == 10 and all(case["passed"] for case in cases)},
        "cases": cases,
        "provider_boundary": "Natural C source-functional storage ownership only. The historical COMDEF-producing TU/order/absolute layout/padding remain unknown; no source promotion or canonical change is performed.",
        "source_limits": "Unchecked raw SaveRec values remain outside this typed-storage claim; no universal game-index/value/lifetime domain is claimed.",
    }
    report_path = OUT / "population-work-arrays-probe-v18.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    summary = {"report": report_path.relative_to(ROOT).as_posix(), "all_pass": report["case_summary"]["all_five_cases_both_linkers_clean_and_passed"],
               "cases": [(c["linker"], c["case"], c["actual_output"], c["passed"]) for c in cases],
               "provider_commons": compiled["PROVIDER"]["communals"]}
    print(json.dumps(summary, indent=2))
    return 0 if report["case_summary"]["all_five_cases_both_linkers_clean_and_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
