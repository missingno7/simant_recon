"""Regenerate and verify the bounded DOS BpopT/RpopT source-storage contract."""
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
HERE = Path(__file__).resolve().parent
OUT = ROOT / "build" / "workers" / "dos_population_owners"
OUT.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(ROOT / "tools"))

import compiler  # noqa: E402
import dos_source_bindings as bindings  # noqa: E402
import source_only_dos as dos  # noqa: E402
from omf import OmfReader  # noqa: E402


OWNER = r"""int far BpopT;
int far population_guard;
int far RpopT;
int far population_owner_word_sum(void)
{
    return BpopT + RpopT;
}
"""

INITIALIZED_OWNER = r"""int far BpopT = 1;
int far RpopT = 2;
int far population_owner_word_sum(void)
{
    return BpopT + RpopT;
}
"""

UNSIGNED_OWNER = r"""unsigned int far BpopT;
int far population_guard;
int far RpopT;
int far population_owner_is_negative(void)
{
    return BpopT < 0;
}
"""

ARRAY_OWNER = r"""int far BpopT[2];
int far population_guard;
int far RpopT;
"""

WORD_CONSUMER = r"""extern int far BpopT;
extern int far RpopT;
extern int far fd_50F6_0330;
extern int far fd_50F6_0350;
extern int far population_owner_word_sum(void);
extern int far puts(char far *text);
int main(void)
{
    if (&BpopT != &fd_50F6_0330 || &RpopT != &fd_50F6_0350 ||
        BpopT != 0 || RpopT != 0 || population_owner_word_sum() != 0) {
        puts("FAIL"); return 1;
    }
    BpopT = 0x1234;
    fd_50F6_0350 = 0x5678;
    if (fd_50F6_0330 != 0x1234 || RpopT != 0x5678 ||
        population_owner_word_sum() != 0x68AC) {
        puts("FAIL"); return 1;
    }
    puts("PASS"); return 0;
}
"""

BYTE_CONSUMER = r"""extern unsigned char far BpopT[];
extern unsigned char far RpopT[];
extern int far fd_50F6_0330;
extern int far fd_50F6_0350;
extern int far population_owner_word_sum(void);
extern int far puts(char far *text);
struct SaveRec { int size; int count; void far *data; };
struct SaveRec far SaveRecTable[2] = {
    {2, 1, (void far *)&BpopT}, {2, 1, (void far *)&RpopT}
};
int main(void)
{
    unsigned char far *black = (unsigned char far *)SaveRecTable[0].data;
    unsigned char far *red = (unsigned char far *)SaveRecTable[1].data;
    if (SaveRecTable[0].size != 2 || SaveRecTable[0].count != 1 ||
        SaveRecTable[1].size != 2 || SaveRecTable[1].count != 1 ||
        black != BpopT || red != RpopT ||
        &fd_50F6_0330 != (int far *)BpopT || &fd_50F6_0350 != (int far *)RpopT ||
        black[0] != 0 || black[1] != 0 || red[0] != 0 || red[1] != 0 ||
        population_owner_word_sum() != 0) { puts("FAIL"); return 1; }
    black[0] = 0x34; black[1] = 0x12;
    red[0] = 0x78; red[1] = 0x56;
    if (*((int far *)BpopT) != 0x1234 || *((int far *)RpopT) != 0x5678 ||
        fd_50F6_0330 != 0x1234 || fd_50F6_0350 != 0x5678 ||
        population_owner_word_sum() != 0x68AC) { puts("FAIL"); return 1; }
    fd_50F6_0330 = 0x2468;
    if (black[0] != 0x68 || black[1] != 0x24 ||
        population_owner_word_sum() != 0x7AE0) { puts("FAIL"); return 1; }
    puts("PASS"); return 0;
}
"""

TYPE_CONSUMER = r"""extern int far BpopT;
extern int far fd_50F6_0330;
extern int far population_owner_is_negative(void);
extern int far puts(char far *text);
int main(void)
{
    if (&BpopT != &fd_50F6_0330) { puts("FAIL"); return 1; }
    BpopT = -1;
    if (population_owner_is_negative() != 1) { puts("FAIL"); return 1; }
    puts("PASS"); return 0;
}
"""

EXTENT_CONSUMER = r"""extern unsigned char far BpopT[];
extern int far population_guard;
extern int far puts(char far *text);
int main(void)
{
    if ((void far *)&population_guard != (void far *)&BpopT[2]) {
        puts("FAIL"); return 1;
    }
    puts("PASS"); return 0;
}
"""


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def source_pin(path: Path) -> dict:
    data = path.read_bytes()
    try:
        name = path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        name = str(path.resolve())
    return {"path": name, "sha256": sha(data), "size": len(data)}


def add_pin(rows: list[dict], row: dict) -> None:
    key = (row["path"], row["sha256"])
    if not any((old["path"], old["sha256"]) == key for old in rows):
        rows.append(row)


def pin_external(path: str | Path, expected_sha256: str | None = None) -> dict:
    row = dos.pin(Path(path), expected_sha256)[1]
    return row


def compile_c(label: str, text: str, profile: str, flags: list[str],
              basename: str = "UNIT") -> tuple[object, bytes]:
    result = compiler.compile_c(text, profile, flags, basename=basename, keep=True)
    if not result.ok:
        raise RuntimeError(f"{label} compile failed:\n{result.log}")
    (OUT / f"{label}.C").write_text(text, encoding="ascii")
    (OUT / f"{label}.OBJ").write_bytes(result.obj)
    return OmfReader(communals=True).read(result.obj), result.obj


def fixup_key(fixup: dict) -> tuple:
    return tuple(fixup[k] for k in (
        "segment", "offset", "width", "loc", "self_relative", "target_kind",
        "target", "displacement", "frame_kind", "frame", "encoded_addend"))


def object_packet(obj) -> dict:
    return {
        "segment_defs": obj.segment_defs,
        "segment_lengths": obj.segment_lengths,
        "groups": obj.groups,
        "segments": {
            name: {"length": len(data), "sha256": sha(bytes(data))}
            for name, data in sorted(obj.segments.items())
        },
        "publics": obj.publics,
        "ordered_fixups": [fixup_key(f) for f in obj.linker_fixups],
        "externals": obj.externals,
        "external_scopes": obj.external_scopes,
        "communals": obj.communals,
    }


def full_module_probe(manifest: dict) -> dict:
    module = manifest["modules"]["root:0BE8"]
    original = (ROOT / module["source"]).read_text(encoding="ascii")
    before_b = "extern int far BpopT;"
    before_r = "extern int far RpopT;"
    assert original.count(before_b) == 1 and original.count(before_r) == 1
    candidate = original.replace(before_b, "int far BpopT;").replace(
        before_r, "int far RpopT;")
    (OUT / "m0BE8-population-owner.c").write_text(candidate, encoding="ascii")

    control, control_bytes = compile_c(
        "root0BE8-control-extern", original, module["profile"], module["flags"])
    owner, owner_bytes = compile_c(
        "root0BE8-owner-int-tentative", candidate, module["profile"], module["flags"])
    control_packet, owner_packet = object_packet(control), object_packet(owner)

    byte_owner, _ = compile_c(
        "root0BE8-negative-byte-type",
        original.replace(before_b, "unsigned char far BpopT;").replace(
            before_r, "unsigned char far RpopT;"),
        module["profile"], module["flags"])
    long_owner, _ = compile_c(
        "root0BE8-negative-long-type",
        original.replace(before_b, "long far BpopT;").replace(before_r, "long far RpopT;"),
        module["profile"], module["flags"])
    initialized, _ = compile_c(
        "root0BE8-negative-initialized",
        original.replace(before_b, "int far BpopT = 1;").replace(
            before_r, "int far RpopT = 2;"),
        module["profile"], module["flags"])
    extent, _ = compile_c(
        "population-owner-negative-array-extent",
        "int far BpopT[2];\nint far RpopT[2];\n",
        module["profile"], module["flags"])

    segment_equal = control_packet["segments"] == owner_packet["segments"]
    segment_meta_equal = all(control_packet[k] == owner_packet[k] for k in (
        "segment_defs", "segment_lengths", "groups"))
    publics_equal = control_packet["publics"] == owner_packet["publics"]
    fixups_equal = control_packet["ordered_fixups"] == owner_packet["ordered_fixups"]
    external_names_equal = control.externals == owner.externals
    scope_changes = [
        {"index": i, "name": control.externals[i],
         "control": control.external_scopes[i], "candidate": owner.external_scopes[i]}
        for i in range(len(control.externals))
        if control.external_scopes[i] != owner.external_scopes[i]
    ]
    expected_scopes = [
        {"name": "_BpopT", "control": "external", "candidate": "communal"},
        {"name": "_RpopT", "control": "external", "candidate": "communal"},
    ]
    actual_scope_names = [
        {k: row[k] for k in ("name", "control", "candidate")}
        for row in scope_changes
    ]
    assert control.communals == []
    assert [bindings.communal_key(c) for c in owner.communals] == [
        ("_BpopT", "far", 2, 1, 2), ("_RpopT", "far", 2, 1, 2)]
    assert segment_equal and segment_meta_equal and publics_equal and fixups_equal
    assert external_names_equal and actual_scope_names == expected_scopes
    assert sha(control_bytes) == module["object_sha256"]
    assert sorted(c["length"] for c in byte_owner.communals) == [1, 1]
    assert sorted(c["length"] for c in long_owner.communals) == [4, 4]
    assert sorted(c["length"] for c in extent.communals) == [4, 4]
    assert initialized.communals == []
    assert any(name.endswith("_DATA") and data for name, data in initialized.segments.items())

    return {
        "module": "root:0BE8",
        "source": module["source"],
        "source_sha256": source_pin(ROOT / module["source"])["sha256"],
        "profile": module["profile"],
        "flags": module["flags"],
        "manifest_extent": module["extent"],
        "manifest_object_sha256": module["object_sha256"],
        "fresh_control_object_sha256": sha(control_bytes),
        "candidate_object_sha256": sha(owner_bytes),
        "candidate_object_size_delta": len(owner_bytes) - len(control_bytes),
        "candidate_source_path": (OUT / "m0BE8-population-owner.c").relative_to(ROOT).as_posix(),
        "candidate_source_sha256": source_pin(OUT / "m0BE8-population-owner.c")["sha256"],
        "all_segment_bytes_equal": segment_equal,
        "segment_definitions_lengths_groups_equal": segment_meta_equal,
        "publics_equal": publics_equal,
        "ordered_fixups_equal": fixups_equal,
        "external_name_sequence_equal": external_names_equal,
        "only_external_scope_changes": scope_changes,
        "candidate_communal_rows": owner.communals,
        "negative_controls": {
            "unsigned_byte_scalars": {
                "communal_lengths": [c["length"] for c in byte_owner.communals],
                "segment_bytes_equal_control": object_packet(byte_owner)["segments"] == control_packet["segments"],
            },
            "long_scalars": {
                "communal_lengths": [c["length"] for c in long_owner.communals],
                "segment_bytes_equal_control": object_packet(long_owner)["segments"] == control_packet["segments"],
            },
            "two_element_int_arrays": {
                "communal_lengths": [c["length"] for c in extent.communals],
                "communal_rows": extent.communals,
            },
            "nonzero_initialized_scalars": {
                "communal_rows": initialized.communals,
                "data_segments": {k: len(v) for k, v in initialized.segments.items() if k.endswith("_DATA")},
            },
        },
    }, owner, owner_bytes


def compile_fixture(name: str, text: str, flags: list[str]) -> tuple[Path, bytes]:
    path = OUT / f"{name}.c"
    path.write_text(text, encoding="ascii")
    result = compiler.compile_c(text, "msc600ax", flags, basename=name)
    if not result.ok:
        raise RuntimeError(f"{name} compile failed:\n{result.log}")
    (OUT / f"{name}.OBJ").write_bytes(result.obj)
    return path, result.obj


def run_case(profile: str, case: str, consumer_obj: bytes, owner_obj: bytes,
             delta_b: int, delta_r: int, expected: str, runtimes: list[dict],
             linker: dict, runner: dict, tool_dir: Path) -> dict:
    directory = OUT / profile / case
    directory.mkdir(parents=True, exist_ok=True)
    for name in ("PROBE.EXE", "PROBE.MAP", "RUN.LOG", "LINK.LOG"):
        (directory / name).unlink(missing_ok=True)
    (directory / "CRT.OBJ").write_bytes(consumer_obj)
    (directory / "OWNER.OBJ").write_bytes(owner_obj)
    for row in runtimes:
        shutil.copyfile(row["path"], directory / Path(row["path"]).name.upper())
    script = (
        "OUTPUT PROBE\r\nMAP = PROBE S,N,A,L\r\nNODEFLIB\r\n"
        "LIBRARY LLIBCR, LIBH\r\nFILE CRT\r\nBEGINAREA\r\n"
        "SECTION FILE OWNER\r\nENDAREA\r\n"
        "DEFINE _fd_50F6_0330 = _BpopT"
        + (f" + {delta_b}" if delta_b else "") + "\r\n"
        "DEFINE _fd_50F6_0350 = _RpopT"
        + (f" + {delta_r}" if delta_r else "") + "\r\n"
    )
    (directory / "PROBE.LNK").write_bytes(script.encode("ascii"))
    (directory / "RTLINK.CFG").write_bytes(b"SYNTAX = FREEFORMAT\r\n")
    (directory / "RUN.BAT").write_bytes((
        f'@echo off\r\nD:\\{linker["executable"]} @PROBE.LNK < NUL > LINK.LOG\r\n'
        "PROBE.EXE > RUN.LOG\r\n"
    ).encode("ascii"))
    config = []
    for section, settings in runner["conf"].items():
        config += ["[" + section + "]"] + [f"{k}={v}" for k, v in settings.items()]
    config += [
        "[autoexec]", f'mount c "{directory}"', f'mount d "{tool_dir}" -ro',
        "c:", "call RUN.BAT", "exit",
    ]
    conf_path = directory / "dosbox.conf"
    conf_path.write_text("\n".join(config) + "\n")
    env = os.environ.copy()
    env.update(SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy")
    timed_out = False
    try:
        result = subprocess.run(
            [runner["path"], "-conf", str(conf_path), "-fastlaunch", "-exit", "-nomenu"],
            cwd=directory, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            timeout=60, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    except subprocess.TimeoutExpired:
        timed_out = True
        result = type("TimedOut", (), {"returncode": -1})()
    log_path = directory / "RUN.LOG"
    actual = log_path.read_text(encoding="latin1").strip() if log_path.exists() else "NO RUN.LOG"
    link_path = directory / "LINK.LOG"
    link_log = link_path.read_text(encoding="latin1", errors="replace") if link_path.exists() else ""
    files = [dos.pin(path)[1] for path in sorted(directory.iterdir()) if path.is_file()]
    return {
        "linker": profile,
        "case": case,
        "alias_delta_bytes": [delta_b, delta_r],
        "expected": expected,
        "actual": actual,
        "passed": actual == expected and result.returncode == 0 and not timed_out,
        "emulator_exit": result.returncode,
        "timed_out": timed_out,
        "link_log_tail": link_log[-800:],
        "files": files,
    }


def consumer_source_pins() -> list[dict]:
    token = re.compile(r"\b(?:BpopT|RpopT)\b")
    rows = []
    for path in sorted((ROOT / "src").rglob("*.c")):
        if token.search(path.read_text(encoding="ascii")):
            rows.append(source_pin(path))
    return rows


def main() -> int:
    denied = dos.install_input_guard()
    toolchain = compiler.toolchain()
    manifest_raw, manifest_pin = dos.pin(ROOT / "layout" / "manifest.json")
    manifest = json.loads(manifest_raw)
    symbols_raw, symbols_pin = dos.pin(ROOT / "layout" / "symbols.json")
    symbols = json.loads(symbols_raw)
    owner_anchor = symbols["data"]["BpopT"]
    red_anchor = symbols["data"]["RpopT"]
    assert symbols["data"]["fd_50F6_0330"].get("alias_of") == "BpopT"
    assert symbols["data"]["fd_50F6_0350"].get("alias_of") == "RpopT"
    full_module, full_owner, full_owner_bytes = full_module_probe(manifest)
    runtimes = list(manifest["runtime"]["libraries"].values())

    owner_path, owner_bytes = compile_fixture(
        "POPONR", OWNER, ["/AL", "/Os", "/Og", "/Oe", "/Zi"])
    initialized_path, initialized_bytes = compile_fixture(
        "POPBAD", INITIALIZED_OWNER, ["/AL", "/Os", "/Og", "/Oe", "/Zi"])
    unsigned_path, unsigned_bytes = compile_fixture(
        "POPSIGN", UNSIGNED_OWNER, ["/AL", "/Os", "/Og", "/Oe", "/Zi"])
    array_path, array_bytes = compile_fixture(
        "POPEXT", ARRAY_OWNER, ["/AL", "/Os", "/Og", "/Oe", "/Zi"])
    word_path, word_bytes = compile_fixture(
        "POPWORD", WORD_CONSUMER, ["/AL", "/Os", "/Zi"])
    byte_path, byte_bytes = compile_fixture(
        "POPBYTE", BYTE_CONSUMER, ["/AL", "/Os", "/Zi"])
    type_path, type_bytes = compile_fixture(
        "POPTYPE", TYPE_CONSUMER, ["/AL", "/Os", "/Zi"])
    extent_path, extent_consumer_bytes = compile_fixture(
        "POPSIZE", EXTENT_CONSUMER, ["/AL", "/Os", "/Zi"])

    owner_obj = OmfReader(communals=True).read(owner_bytes)
    initialized_obj = OmfReader(communals=True).read(initialized_bytes)
    unsigned_obj = OmfReader(communals=True).read(unsigned_bytes)
    array_obj = OmfReader(communals=True).read(array_bytes)
    candidate_pair = [c for c in full_owner.communals if c["name"] in ("_BpopT", "_RpopT")]
    fixture_pair = [c for c in owner_obj.communals if c["name"] in ("_BpopT", "_RpopT")]
    assert [bindings.communal_key(c) for c in candidate_pair] == [
        bindings.communal_key(c) for c in fixture_pair]
    assert initialized_obj.communals == []
    assert any(name.endswith("_DATA") and data for name, data in initialized_obj.segments.items())
    assert sorted(c["length"] for c in unsigned_obj.communals if c["name"] == "_BpopT") == [2]
    assert sorted(c["length"] for c in array_obj.communals if c["name"] == "_BpopT") == [4]

    consumer_pins = consumer_source_pins()
    source_paths = [
        "src/root/m0BE8.c", "src/S09/m35F5.c", "src/S22/m39C7.c",
        "layout/manifest.json", "layout/symbols.json", "layout/toolchain.json",
        "tools/compiler.py", "tools/omf.py", "tools/dos_source_bindings.py",
        "tools/source_only_dos.py",
    ]
    pinned_inputs = list(consumer_pins)
    for rel in source_paths:
        add_pin(pinned_inputs, source_pin(ROOT / rel))
    add_pin(pinned_inputs, source_pin(Path(__file__)))
    for path in (
        owner_path, initialized_path, unsigned_path, array_path, word_path,
        byte_path, type_path, extent_path,
    ):
        add_pin(pinned_inputs, source_pin(path))
    add_pin(pinned_inputs, manifest_pin)
    add_pin(pinned_inputs, symbols_pin)
    add_pin(pinned_inputs, source_pin(ROOT / "layout" / "toolchain.json"))

    compiler_profile = compiler.verify_profile("msc600ax")
    compiler_file_pins = [
        pin_external(Path(compiler_profile["directory"]) / rel, digest)
        for rel, digest in compiler_profile["files"].items()
    ]
    compiler_runner_pin = pin_external(
        toolchain["runner"]["path"], toolchain["runner"]["sha256"])
    runner = toolchain["runners"]["dosbox-x"]
    dosbox_pin = pin_external(runner["path"], runner["sha256"])
    linker_pins = {}
    runtime_pins = [
        pin_external(row["path"], row["sha256"]) for row in runtimes
    ]
    cases = []
    case_specs = [
        ("typed_owner_word_exact_aliases", word_bytes, owner_bytes, 0, 0, "PASS"),
        ("typed_owner_SaveRec_BYTE_exact_aliases", byte_bytes, owner_bytes, 0, 0, "PASS"),
        ("wrong_alias_word_plus2", word_bytes, owner_bytes, 2, 0, "FAIL"),
        ("wrong_type_unsigned_scalar", type_bytes, unsigned_bytes, 0, 0, "FAIL"),
        ("wrong_extent_two_element_array", extent_consumer_bytes, array_bytes, 0, 0, "FAIL"),
        ("initialized_nonzero_owner", word_bytes, initialized_bytes, 0, 0, "FAIL"),
    ]
    required_cases = {name: expected for name, *_rest, expected in case_specs}
    for profile in ("rtlink400", "rtlink610"):
        linker = toolchain["linkers"][profile]
        linker_pins[profile] = [
            pin_external(Path(linker["directory"]) / rel, digest)
            for rel, digest in linker["files"].items()
        ]
        tool_dir = compiler.pinned_tree(linker)
        for case_spec in case_specs:
            cases.append(run_case(profile, *case_spec, runtimes, linker, runner, tool_dir))

    per_linker = {}
    for profile in ("rtlink400", "rtlink610"):
        rows = [row for row in cases if row["linker"] == profile]
        per_linker[profile] = {
            "pass_count": sum(row["actual"] == "PASS" for row in rows),
            "fail_count": sum(row["actual"] == "FAIL" for row in rows),
            "all_expected_cases_pass": len(rows) == 6 and all(row["passed"] for row in rows),
        }
    runtime_ok = all(
        row["pass_count"] >= 2 and row["fail_count"] >= 4 and row["all_expected_cases_pass"]
        for row in per_linker.values()
    )
    exact_runtime_cases = all(
        len([row for row in cases if row["linker"] == profile]) == len(required_cases)
        and {
            row["case"]: row["expected"]
            for row in cases if row["linker"] == profile
        } == required_cases
        and all(row["passed"] and row["actual"] == row["expected"]
                for row in cases if row["linker"] == profile)
        for profile in ("rtlink400", "rtlink610")
    )
    all_checks = (
        full_module["all_segment_bytes_equal"]
        and full_module["segment_definitions_lengths_groups_equal"]
        and full_module["publics_equal"]
        and full_module["ordered_fixups_equal"]
        and full_module["fresh_control_object_sha256"] == full_module["manifest_object_sha256"]
        and runtime_ok and exact_runtime_cases and not denied
    )

    tool_runtime_pins = {
        "compiler_profile": "msc600ax",
        "compiler_flags_full_module": full_module["flags"],
        "compiler_files": compiler_file_pins,
        "compiler_runner": compiler_runner_pin,
        "dosbox_runner": dosbox_pin,
        "linkers": linker_pins,
        "runtime_libraries": runtime_pins,
    }
    local_report = {
        "schema": "simant-dos-population-owner-local-report-v1",
        "full_module": full_module,
        "test_owner": {
            "source": source_pin(owner_path),
            "object_sha256": sha(owner_bytes),
            "communal_rows": owner_obj.communals,
            "matches_full_candidate_pair": True,
            "full_game_module_linked": False,
            "game_function_stubs": 0,
        },
        "negative_owners": {
            "initialized": {"source": source_pin(initialized_path), "communal_rows": initialized_obj.communals},
            "unsigned": {"source": source_pin(unsigned_path), "communal_rows": unsigned_obj.communals},
            "two_element_array": {"source": source_pin(array_path), "communal_rows": array_obj.communals},
        },
        "cases": cases,
        "per_linker": per_linker,
        "denied_oracle_reads": denied,
        "all_required_checks_pass": all_checks,
    }
    local_path = OUT / "population-owner-local-report.json"
    local_path.write_text(json.dumps(local_report, indent=2) + "\n", encoding="utf-8")
    local_pin = source_pin(local_path)
    probe_pin = source_pin(Path(__file__))
    owner_source = source_pin(ROOT / "src/root/m0BE8.c")
    contract = {
        "schema": "simant-dos-population-owner-contract-v1",
        "category": "REVIEWED_SOURCE_STORAGE_CONTRACT",
        "probe_source": probe_pin,
        "full_local_report": local_pin,
        "members": ["BpopT", "RpopT"],
        "dos_type": "int far",
        "word_bytes": 2,
        "required_cases": required_cases,
        "owner_candidate": {
            "module": "root:0BE8",
            "source": owner_source,
            "candidate_source": {
                "path": full_module["candidate_source_path"],
                "sha256": full_module["candidate_source_sha256"],
            },
            "source_functional_owner": "CountAnts rebuilds caste counts from live ant lists and writes BpopT/RpopT from the resulting black/red caste buckets.",
            "historical_comdef_module_identity": "NOT_CLAIMED",
            "full_module_is_runtime_linked": False,
        },
        "source_ownership_facts": {
            "CountAnts": "Clears per-caste scratch counts, scans live ant lists, and assigns both totals from the caste buckets at the end; it does not directly zero these two words at entry.",
            "FullCount": "Calls CountAnts then CountUpdate.",
            "world_and_population_lifecycle": "S08 RandWorld calls CountAnts during world setup. Tutorial setup later adds 32 ants to each colony and calls FullCount. root:015B AddSomeAnts/KillSomeAnts and selected root:0894 DoSmells phases also call FullCount. S22 YellowBirth adjusts the matching total with its caste counters after successful birth.",
            "save_load": "S09 SaveRec stores each value as one 2-byte item through unsigned-byte address views. LoadGame reads the records, rebuilds the life maps, and calls FullCount to recompute totals from the loaded lists.",
            "typed_consumers": "All game computations declare signed int far words and use word reads, writes, increments, comparisons, shifts, sums, and divisions. S12 widens a display-bar numerator to long. SaveRec byte views only form addresses; no byte indexing or other pointer escape was found.",
            "registered_aliases": {
                "fd_50F6_0330": {"alias_of": "BpopT", "address": [owner_anchor["seg"], owner_anchor["off"]]},
                "fd_50F6_0350": {"alias_of": "RpopT", "address": [red_anchor["seg"], red_anchor["off"]]},
            },
            "consumer_pins": consumer_pins,
            "registry_pin": symbols_pin,
        },
        "inputs": pinned_inputs,
        "tool_runtime_pins": tool_runtime_pins,
        "full_module_control": full_module,
        "cases": [
            {key: row[key] for key in (
                "linker", "case", "expected", "actual", "passed",
                "emulator_exit", "timed_out", "alias_delta_bytes")}
            for row in cases
        ],
        "per_linker": per_linker,
        "denied_oracle_reads": denied,
        "all_required_checks_pass": all_checks,
        "scope": "Test-owned typed scalar storage contract. Verifies the whole source-owner object delta, compiler communal extent, zero-filled MSC startup, numeric alias binding, word and SaveRec byte views, and wrong alias/type/extent/initializer contrasts under RTLink 4.00 and 6.10. No game stubs, original executable/build inputs, or historical COMDEF identity claim.",
    }
    contract_path = OUT / "population-owner-contract-candidate.json"
    contract_path.write_text(json.dumps(contract, indent=2) + "\n", encoding="utf-8")
    contract_pin = source_pin(contract_path)

    communicator_specs = []
    for name, anchor, alias in (
        ("BpopT", owner_anchor, "fd_50F6_0330"),
        ("RpopT", red_anchor, "fd_50F6_0350"),
    ):
        communicator_specs.append({
            "name": "_" + name,
            "kind": "far",
            "count": 2,
            "element_size": 1,
            "length": 2,
            "historical_address": [anchor["seg"], anchor["off"]],
            "source_extent_anchor": (
                f"root:0BE8 CountAnts assigns this int far scalar; S09 SaveRec has "
                "{2,1,&" + name + "}; typed consumers read/write a word."
            ),
            "initialization": (
                "Tentative int far definition with no source initializer; zero-fill is "
                "confirmed by the pinned MSC startup and RTLink 4.00/6.10 fixtures."
            ),
            "views": [
                "root:0BE8 CountAnts signed int far scalar",
                "S22:39C7 YellowBirth signed int far increment",
                "S09:35F5 unsigned char far address-only SaveRec view",
                f"registered exact alias {alias}",
            ],
            "registered_interior_names": [],
        })
    owner_binding = {
        "module": "root:0BE8",
        "source": owner_source["path"],
        "source_sha256": owner_source["sha256"],
        "edits": [
            {"before": "extern int far BpopT;", "after": "int far BpopT;", "count": 1},
            {"before": "extern int far RpopT;", "after": "int far RpopT;", "count": 1},
        ],
        "exports": [],
        "communals": communicator_specs,
        "relocations": [],
        "scalar_storage": {"families": ["population"]},
    }
    binding_packet = {
        "schema": "simant-dos-population-owner-bindings-v1",
        "category": "REVIEWED_SOURCE_STORAGE_BINDING",
        "scope": "The complete root:0BE8 source unit functionally owns BpopT/RpopT recomputation; only these two tentative scalar definitions are added in a derived source build.",
        "historical_claim_limit": "Historical COMDEF-emitting object identity/order, absolute FAR_BSS placement by an independent link, and game runtime execution are not claimed. Canonical source and the historical ledger remain frozen.",
        "review_sources": consumer_pins,
        "runtime_contract_key": "population_storage_contract",
        "bindings": [owner_binding],
        "runtime_contract": {
            "path": contract_pin["path"],
            "sha256": contract_pin["sha256"],
            "size": contract_pin["size"],
        },
    }
    bindings_path = OUT / "population-owner-bindings-candidate.json"
    bindings_path.write_text(json.dumps(binding_packet, indent=2) + "\n", encoding="utf-8")

    print(json.dumps({
        "all_required_checks_pass": all_checks,
        "full_control_matches_manifest": full_module["fresh_control_object_sha256"] == full_module["manifest_object_sha256"],
        "whole_module_candidate_preserves_contributions": all(full_module[k] for k in (
            "all_segment_bytes_equal", "segment_definitions_lengths_groups_equal",
            "publics_equal", "ordered_fixups_equal")),
        "runtime_cases": len(cases),
        "per_linker": per_linker,
        "denied_oracle_reads": denied,
        "contract": str(contract_path),
        "bindings": str(bindings_path),
    }, indent=2))
    return 0 if all_checks else 1


if __name__ == "__main__":
    raise SystemExit(main())
