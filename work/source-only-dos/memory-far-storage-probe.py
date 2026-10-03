"""Source-only far-storage owner and startup/linker probe; no game or oracle inputs."""
from pathlib import Path
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "build/workers/dos_memory_far_owners"
sys.path.insert(0, str(ROOT / "tools"))
import compiler
import dos_source_bindings as bindings
import source_only_dos as dos
from omf import OmfReader

compiler.WORK = OUT / "cc"
SOURCE = OUT / "source"
OBJECTS = OUT / "objects"
SOURCE.mkdir(parents=True, exist_ok=True)
OBJECTS.mkdir(parents=True, exist_ok=True)
OWNER_SOURCE = ROOT / "work/source-only-dos/providers/memory-far-state.c"

CONSUMER_SOURCE = r'''extern int far puts(char far *text);
extern unsigned far fd_50F6_394C;
extern unsigned far fd_50F6_394E;
extern unsigned far fd_50F6_3950;
extern char far * far fd_50F6_3948;
extern char far * far fd_50F6_3B48;

int main(void)
{
    unsigned far *halves;
    union FarValue {
        char far *value;
        unsigned word[2];
    } marker3948, marker3B48;

    if (sizeof(fd_50F6_394C) != 2 || sizeof(fd_50F6_394E) != 2 ||
        sizeof(fd_50F6_3950) != 2 || sizeof(fd_50F6_3948) != 4 ||
        sizeof(fd_50F6_3B48) != 4) {
        puts("FAIL");
        return 0;
    }
    halves = (unsigned far *)&fd_50F6_3948;
    if (fd_50F6_394C != 0 || fd_50F6_394E != 0 || fd_50F6_3950 != 0 ||
        halves[0] != 0 || halves[1] != 0) {
        puts("FAIL");
        return 0;
    }
    halves = (unsigned far *)&fd_50F6_3B48;
    if (halves[0] != 0 || halves[1] != 0) {
        puts("FAIL");
        return 0;
    }

    fd_50F6_394C = 0x8001;
    fd_50F6_394E = 0xABCD;
    fd_50F6_3950 = 0xF00D;
    /* Test pointers are real far addresses of test commons and are never dereferenced. */
    marker3948.value = (char far *)&fd_50F6_394C;
    marker3B48.value = (char far *)&fd_50F6_394E;
    fd_50F6_3948 = marker3948.value;
    fd_50F6_3B48 = marker3B48.value;
    if (fd_50F6_394C != 0x8001 || fd_50F6_394C < 0 || fd_50F6_394E != 0xABCD ||
        fd_50F6_3950 != 0xF00D) {
        puts("FAIL");
        return 0;
    }
    halves = (unsigned far *)&fd_50F6_3948;
    if (halves[0] != marker3948.word[0] || halves[1] != marker3948.word[1]) {
        puts("FAIL");
        return 0;
    }
    halves = (unsigned far *)&fd_50F6_3B48;
    if (halves[0] != marker3B48.word[0] || halves[1] != marker3B48.word[1]) {
        puts("FAIL");
        return 0;
    }
    puts("PASS");
    return 0;
}
'''
WRONG_EXTENT_OWNER_SOURCE = r'''unsigned far fd_50F6_394C;
unsigned far fd_50F6_394E;
unsigned far fd_50F6_3950;
char far * far fd_50F6_3948[2];
char far * far fd_50F6_3B48;
'''
WRONG_EXTENT_TEST_SOURCE = r'''extern int far puts(char far *text);
extern char far * far fd_50F6_3948[2];
int main(void)
{
    if (sizeof(fd_50F6_3948) != 4) {
        puts("FAIL");
        return 0;
    }
    puts("PASS");
    return 0;
}
'''
WRONG_TYPE_SOURCE = r'''extern int far puts(char far *text);
extern int far fd_50F6_394C;
int main(void)
{
    fd_50F6_394C = 0x8001;
    if (fd_50F6_394C < 0)
        puts("FAIL");
    else
        puts("PASS");
    return 0;
}
'''
NONZERO_OWNER_SOURCE = r'''unsigned far fd_50F6_394C = 1;
unsigned far fd_50F6_394E;
unsigned far fd_50F6_3950;
char far * far fd_50F6_3948;
char far * far fd_50F6_3B48;
'''

EXPECTED = [
    ("_fd_50F6_3948", "far", 4, 1, 4),
    ("_fd_50F6_394C", "far", 2, 1, 2),
    ("_fd_50F6_394E", "far", 2, 1, 2),
    ("_fd_50F6_3950", "far", 2, 1, 2),
    ("_fd_50F6_3B48", "far", 4, 1, 4),
]
CONTRACT_COMMUNALS = [
    ("_fd_50F6_394C", "far", 2, 1, 2),
    ("_fd_50F6_394E", "far", 2, 1, 2),
    ("_fd_50F6_3950", "far", 2, 1, 2),
    ("_fd_50F6_3948", "far", 4, 1, 4),
    ("_fd_50F6_3B48", "far", 4, 1, 4),
]


def pin(path, expected=None):
    return dos.pin(Path(path), expected)[1]


def pin_unique(inputs, seen, path, expected=None):
    item = pin(path, expected)
    key = (item["path"], item["sha256"])
    if key not in seen:
        seen.add(key)
        inputs.append(item)
    return item


def stage_sources():
    sources = {
        "memory-far-state.c": OWNER_SOURCE.read_text(encoding="ascii"),
        "consumer.c": CONSUMER_SOURCE,
        "memory-far-state-wrong-extent.c": WRONG_EXTENT_OWNER_SOURCE,
        "consumer-wrong-extent.c": WRONG_EXTENT_TEST_SOURCE,
        "consumer-wrong-type.c": WRONG_TYPE_SOURCE,
        "memory-far-state-nonzero.c": NONZERO_OWNER_SOURCE,
    }
    for name, text in sources.items():
        (SOURCE / name).write_text(text, encoding="ascii")


def compile_source(stem, flags):
    source_path = SOURCE / (stem + ".c")
    source = source_path.read_text(encoding="ascii")
    basename = {
        "memory-far-state": "MFOWNER", "consumer": "FARTEST",
        "memory-far-state-wrong-extent": "FAREXT",
        "consumer-wrong-extent": "EXTEST", "consumer-wrong-type": "TYPEC",
        "memory-far-state-nonzero": "FARINIT",
    }[stem]
    result = compiler.compile_c(source, "msc600ax", flags, basename=basename, keep=True)
    if not result.ok:
        raise RuntimeError("MSC compile failed for " + stem + ":\n" + result.log)
    target = OBJECTS / (basename + ".OBJ")
    target.write_bytes(result.obj)
    return {"obj": result.obj, "path": target, "compiler_log": result.log,
            "source_path": source_path, "workdir": result.workdir}


def communal_rows(raw):
    obj = OmfReader(communals=True).read(raw)
    return obj, sorted(bindings.communal_key(c) for c in obj.communals)


def far_bss_layout(map_path):
    text = map_path.read_text(encoding="latin1", errors="replace")
    segment = re.search(
        r"^\s*([0-9A-F]+)H\s+([0-9A-F]+)H\s+([0-9A-F]+)H\s+FAR_BSS\s+FAR_BSS\s*$",
        text, re.M)
    if not segment:
        raise ValueError("candidate MAP lacks the FAR_BSS segment")
    start, stop, length = (int(value, 16) for value in segment.groups())
    symbols = {}
    for match in re.finditer(r"^\s*([0-9A-F]+):([0-9A-F]+)\s+(_fd_50F6_(?:3948|394C|394E|3950|3B48))\s*$",
                             text, re.M):
        symbols[match.group(3)] = (int(match.group(1), 16), int(match.group(2), 16))
    required = {row[0]: row[4] for row in EXPECTED}
    if set(symbols) != set(required) or sum(required.values()) != length:
        raise ValueError("FAR_BSS map does not bound exactly the five candidate objects")
    for name, (seg, off) in symbols.items():
        linear = (seg << 4) + off
        if not (start <= linear and linear + required[name] <= stop + 1):
            raise ValueError("far common lies outside the linker FAR_BSS region: " + name)
    return {"region_start_linear": start, "region_stop_linear": stop,
            "region_length": length,
            "test_link_symbols": {name: {"segment": seg, "offset": off}
                                  for name, (seg, off) in sorted(symbols.items())}}


def run_case(linker_name, linker, tool_dir, runner, runtimes, main_obj, owner_obj,
             case_name, expected_log, observed_contract):
    directory = OUT / "fixtures" / linker_name / case_name
    directory.mkdir(parents=True, exist_ok=True)
    for filename in ("PROBE.EXE", "PROBE.MAP", "RUN.LOG", "LINK.LOG"):
        (directory / filename).unlink(missing_ok=True)
    for name, path in (("MAIN", main_obj), ("OWNER", owner_obj)):
        shutil.copyfile(path, directory / (name + ".OBJ"))
    for row in runtimes:
        shutil.copyfile(row["path"], directory / Path(row["path"]).name.upper())
    (directory / "PROBE.LNK").write_bytes((
        "OUTPUT PROBE\r\nMAP = PROBE S,N,A,L\r\nNODEFLIB\r\n"
        "LIBRARY LLIBCR, LIBH\r\nFILE MAIN, OWNER\r\n").encode("ascii"))
    (directory / "RTLINK.CFG").write_bytes(b"SYNTAX = FREEFORMAT\r\n")
    (directory / "RUN.BAT").write_bytes((
        f"@echo off\r\nD:\\{linker['executable']} @PROBE.LNK < NUL > LINK.LOG\r\n"
        "PROBE.EXE > RUN.LOG\r\n").encode("ascii"))
    config = []
    for section, values in runner["conf"].items():
        config.append("[" + section + "]")
        config += [f"{key}={value}" for key, value in values.items()]
    config += ["[autoexec]", f'mount c "{directory.resolve()}"',
               f'mount d "{tool_dir}" -ro', "c:", "call RUN.BAT", "exit"]
    conf_path = directory / "dosbox.conf"
    conf_path.write_text("\n".join(config) + "\n", encoding="ascii")
    env = os.environ.copy()
    env.update(SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy")
    run = subprocess.run([runner["path"], "-conf", str(conf_path), "-fastlaunch", "-exit", "-nomenu"],
                         cwd=directory, env=env, stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL, timeout=90,
                         creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    exe_path = directory / "PROBE.EXE"
    run_log = directory / "RUN.LOG"
    link_log = directory / "LINK.LOG"
    map_path = directory / "PROBE.MAP"
    actual = run_log.read_text(encoding="latin1").strip() if run_log.exists() else ""
    link_text = link_log.read_text(encoding="latin1", errors="replace") if link_log.exists() else ""
    layout = far_bss_layout(map_path) if case_name == "candidate_zero_write_halfwords" and map_path.exists() else None
    if case_name == "candidate_zero_write_halfwords" and (
            layout is None or layout["region_length"] != 14):
        raise ValueError("candidate link did not allocate exactly 14 bytes in FAR_BSS")
    files = [pin(p) for p in sorted(directory.iterdir()) if p.is_file()]
    return {
        "linker": linker_name, "case": case_name, "expected_log": expected_log,
        "actual_log": actual, "observed_contract": observed_contract,
        "link_succeeded": exe_path.exists(), "dosbox_exit": run.returncode,
        "far_bss_layout": layout,
        "link_log_sha256": hashlib.sha256(link_text.encode("latin1", "replace")).hexdigest(),
        "files": files,
        "passed": exe_path.exists() and actual == expected_log and run.returncode == 0,
    }


def main():
    denied = dos.install_input_guard()
    OUT.mkdir(parents=True, exist_ok=True)
    stage_sources()
    inputs = []
    seen = set()

    # Pin the complete source/research basis and the immutable no-raw context packets.
    source_paths = [
        ROOT / "src/root/m171C.c", ROOT / "src/root/m19DC.c", ROOT / "src/root/m195A.asm",
        ROOT / "layout/symbols.json", ROOT / "layout/manifest.json",
        ROOT / "layout/toolchain.json", ROOT / "evidence/behavior/manifest.json",
        ROOT / "work/source-only-dos/numeric-address-audit-v1.md",
        ROOT / "work/source-only-dos/compile-and-intake-v1.json",
        ROOT / "build/source-only-dos/build-report.json",
        ROOT / "tools/context.py", ROOT / "tools/compiler.py", ROOT / "tools/omf.py",
        ROOT / "tools/source_only_dos.py", ROOT / "tools/dos_source_bindings.py",
    ]
    for function in ("f_171C_09CC", "f_171C_0ADC", "f_171C_0BE2", "f_171C_0CF4",
                     "f_171C_0FBC", "f_171C_0EEA", "f_171C_1804", "f_171C_1D40",
                     "f_171C_1E9A", "f_171C_0678", "f_171C_0034", "f_171C_07BE",
                     "f_19DC_0008", "f_19DC_001A", "f_19DC_0148", "f_19DC_02FB",
                     "f_195A_001D"):
        source_paths.append(OUT / "context" / (function + ".txt"))
    for function in ("f_171C_09CC", "f_171C_0ADC", "f_171C_0FBC"):
        source_paths.append(ROOT / "evidence/behavior/functions" / function /
                            "contracts/live-state-v2/module.c")
        source_paths.append(ROOT / "evidence/behavior/functions" / function /
                            "contracts/live-state-v2/evidence.json")
    for path in source_paths:
        pin_unique(inputs, seen, path)
    pin_unique(inputs, seen, Path(__file__))
    pin_unique(inputs, seen, OWNER_SOURCE)
    for source in sorted(SOURCE.glob("*.c")):
        pin_unique(inputs, seen, source)

    tc = compiler.toolchain()
    compiler_profile = compiler.verify_profile("msc600ax")
    c_runner = tc["runners"]["dosbox-x"]
    pin_unique(inputs, seen, ROOT / "layout/toolchain.json")
    pin_unique(inputs, seen, Path(c_runner["path"]), c_runner["sha256"])
    for rel, digest in compiler_profile["files"].items():
        pin_unique(inputs, seen, Path(compiler_profile["directory"]) / rel, digest)
    for name, digest in (compiler_profile.get("include_files") or {}).items():
        include_path = compiler.include_root(compiler_profile) / name
        pin_unique(inputs, seen, include_path, digest)

    flags = ["/AL", "/Os"]
    compiled = {}
    for stem in ("memory-far-state", "consumer", "memory-far-state-wrong-extent",
                 "consumer-wrong-extent", "consumer-wrong-type", "memory-far-state-nonzero"):
        compiled[stem] = compile_source(stem, flags)
        pin_unique(inputs, seen, compiled[stem]["path"])

    provider_obj, candidate_comm = communal_rows(compiled["memory-far-state"]["obj"])
    expected_comm = sorted(EXPECTED)
    if candidate_comm != expected_comm:
        raise ValueError("candidate COMDEF shape differs: " + repr(candidate_comm))
    storage_segments = ("_DATA", "CONST", "_BSS")
    nonempty_provider_segments = [
        {"name": row["name"], "class": row["class"], "length": row["length"]}
        for row in provider_obj.segment_defs if row["length"]]
    if provider_obj.publics or nonempty_provider_segments or any(
            provider_obj.segment_length(k) for k in storage_segments):
        raise ValueError("data-only provider unexpectedly contains code, initialized, or debug data")
    wrong_obj, wrong_comm = communal_rows(compiled["memory-far-state-wrong-extent"]["obj"])
    wrong_pointer = [row for row in wrong_comm if row[0] == "_fd_50F6_3948"]
    if (len(wrong_pointer) != 1 or wrong_pointer[0] !=
            ("_fd_50F6_3948", "far", 2, 4, 8) or wrong_comm == expected_comm):
        raise ValueError("wrong-extent negative did not produce an 8-byte far COMDEF")
    if wrong_obj.publics or any(row["length"] for row in wrong_obj.segment_defs) or any(
            wrong_obj.segment_length(k) for k in storage_segments):
        raise ValueError("wrong-extent control unexpectedly contains code, initialized, or debug data")
    nonzero_obj = OmfReader(communals=True).read(compiled["memory-far-state-nonzero"]["obj"])
    if not any(nonzero_obj.segments.values()):
        raise ValueError("nonzero initialization contrast did not emit initialized bytes")

    pin_unique(inputs, seen, Path(tc["runner"]["path"]), tc["runner"]["sha256"])
    manifest = json.loads((ROOT / "layout/manifest.json").read_text(encoding="utf-8"))
    runtimes = []
    for row in manifest["runtime"]["libraries"].values():
        p = Path(row["path"])
        pin_unique(inputs, seen, p, row["sha256"])
        runtimes.append(row)

    cases = []
    for linker_name in ("rtlink400", "rtlink610"):
        linker = tc["linkers"][linker_name]
        for rel, digest in linker["files"].items():
            pin_unique(inputs, seen, Path(linker["directory"]) / rel, digest)
        tool_dir = compiler.pinned_tree(linker)
        for case_name, consumer_key, provider_key, expected_log, contract in (
                ("candidate_zero_write_halfwords", "consumer", "memory-far-state", "PASS",
                 "candidate: zero far commons at CRT entry; near words and far-pointer halves round-trip"),
                ("wrong_extent", "consumer-wrong-extent", "memory-far-state-wrong-extent", "FAIL",
                 "negative: two far pointers occupy 8 bytes where one 4-byte pointer is required"),
                ("wrong_signed_type", "consumer-wrong-type", "memory-far-state", "FAIL",
                 "negative: signed int view treats 0x8001 as negative, contradicting unsigned consumer"),
                ("nonzero_initialized_owner", "consumer", "memory-far-state-nonzero", "FAIL",
                 "negative: initialized far storage is nonzero on main entry")):
            cases.append(run_case(
                linker_name, linker, tool_dir, tc["runners"]["dosbox-x"], runtimes,
                compiled[consumer_key]["path"], compiled[provider_key]["path"],
                case_name, expected_log, contract))

    startup_contract_cases = [
        {key: row[key] for key in ("linker", "case", "expected_log", "actual_log", "passed")}
        | {"expected": row["expected_log"], "actual": row["actual_log"]}
        for row in cases
    ]
    runtime_components = [{"path": row["path"], "sha256": row["sha256"]}
                          for row in runtimes]
    report = {
        "schema": "simant-dos-memory-far-owners-candidate-v1",
        "inputs": inputs,
        "runtime_components": runtime_components,
        "compiler": {"profile": "msc600ax", "flags": flags,
                     "provider_commdefs": [dict(zip(("name", "kind", "count", "element_size", "length"), r))
                                           for r in candidate_comm],
                     "provider_has_publics": bool(provider_obj.publics),
                     "provider_initialized_segments": [k for k, v in provider_obj.segments.items()
                                                        if k in storage_segments and v],
                     "provider_nonempty_segments": nonempty_provider_segments,
                     "provider_code_length": provider_obj.segment_length("MFOWNER_TEXT"),
                     "provider_debug_segment_bytes": len(provider_obj.segments.get("$$SYMBOLS", b"")),
                     "wrong_extent_commdefs": [dict(zip(("name", "kind", "count", "element_size", "length"), r))
                                                for r in wrong_comm],
                     "nonzero_initialized_segments": [k for k, v in nonzero_obj.segments.items() if v]},
        "fixtures": cases,
        "memory_far_storage_contract": {
            "root_reviewed": False,
            "required_cases": {
                "candidate_zero_write_halfwords": "PASS",
                "wrong_extent": "FAIL",
                "wrong_signed_type": "FAIL",
                "nonzero_initialized_owner": "FAIL",
            },
            "cases": startup_contract_cases,
            "communals": [
                {"name": row[0], "kind": row[1], "length": row[4],
                 "count": row[2], "element_size": row[3]}
                for row in CONTRACT_COMMUNALS
            ],
            "inputs": inputs,
            "all_required_checks_pass": (not denied and candidate_comm == expected_comm and
                wrong_pointer == [("_fd_50F6_3948", "far", 2, 4, 8)] and
                all(case["passed"] for case in cases)),
        },
        "denied_oracle_reads": denied,
        "all_required_checks_pass": (not denied and candidate_comm == expected_comm and
            wrong_pointer == [("_fd_50F6_3948", "far", 2, 4, 8)] and
            all(case["passed"] for case in cases)),
        "limits": [
            "Functional storage proposal only; it does not claim the original compiler TU or link order.",
            "The CRT test covers the candidate's far commons and the tested MSC startup/RTLink fixtures, not the game's actual EMS hardware session.",
            "Synthetic far-pointer values are read as words only and are never dereferenced; runtime EMS segment values remain supplied by the INT 67h source path.",
            "The probe does not link game code, use game stubs, or read the original executable.",
        ],
    }
    report_path = OUT / "candidate-receipt.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"all_required_checks_pass": report["all_required_checks_pass"],
                      "candidate_commdefs": report["compiler"]["provider_commdefs"],
                      "fixtures": [{k: row[k] for k in ("linker", "case", "actual_log", "passed")}
                                  for row in cases],
                      "report": str(report_path)}, indent=2))
    return 0 if report["all_required_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
