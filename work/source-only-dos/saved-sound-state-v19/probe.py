#!/usr/bin/env python3
"""Guarded root-false check of the v19 seven-word FAR_BSS owner candidate."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / "tools"))
import source_only_dos as dos
import compiler
from omf import OmfReader
import dos_source_bindings as bindings

denied = dos.install_input_guard()

PROBE_PATH = ROOT / "work/source-only-dos/database-index-state-probe.py"
REVIEW_PATH = ROOT / "work/source-only-dos/saved-sound-state-v19/review.json"
SOURCE_AUDIT_PATH = ROOT / "work/source-only-dos/saved-sound-state-v19/source-audit.json"
PROVIDER_PATH = ROOT / "work/source-only-dos/saved-sound-state-v19/provider.c"
spec = importlib.util.spec_from_file_location("database_index_state_probe", PROBE_PATH)
probe = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(probe)

OWNER_SOURCE = PROVIDER_PATH.read_text(encoding="ascii")
NONZERO_OWNER_SOURCE = "int far fd_50F6_01F0[7] = { 1 };\n"
WRONG_WIDTH_SOURCE = "long far fd_50F6_01F0[7];\n"
SHORT_EXTENT_SOURCE = "int far fd_50F6_01F0[6];\n"
ALIAS_SOURCE = r'''extern int far fd_50F6_01F0[];
int far *fd_55B3_74FE = fd_50F6_01F0;
'''
MAIN_SOURCE = r'''extern void far puts(char far *text);
extern int far fd_50F6_01F0[7];
extern int far * far fd_55B3_74FE;

int main(void)
{
    int i;
    if (fd_55B3_74FE != fd_50F6_01F0) {
        puts("FAIL");
        return 0;
    }
    for (i = 0; i < 7; i++) {
        if (fd_50F6_01F0[i] != 0 || fd_55B3_74FE[i] != 0) {
            puts("FAIL");
            return 0;
        }
    }
    puts("PASS");
    return 0;
}
'''
SHORT_MAIN_SOURCE = r'''extern void far puts(char far *text);
extern int far fd_50F6_01F0[7];
extern int far * far fd_55B3_74FE;

int main(void)
{
    int i;
    if (fd_55B3_74FE != fd_50F6_01F0) {
        puts("FAIL");
        return 0;
    }
    for (i = 0; i < 6; i++) {
        if (fd_50F6_01F0[i] != 0 || fd_55B3_74FE[i] != 0) {
            puts("FAIL");
            return 0;
        }
    }
    puts("PASS");
    return 0;
}
'''


def pin(path: Path, expected: str | None = None) -> dict:
    return dos.pin(path, expected)[1]


def pin_unique(rows: list, seen: set, path: Path, expected: str | None = None) -> dict:
    row = pin(path, expected)
    key = (row["path"], row["sha256"])
    if key not in seen:
        seen.add(key)
        rows.append(row)
    return row


def compile_source(text: str, name: str, out: Path, inputs: list, seen: set) -> dict:
    staged = out / "sources" / (name + ".c")
    staged.write_text(text, encoding="ascii")
    pin_unique(inputs, seen, staged)
    return probe.compile_unit(text, name, out / "objects", inputs, seen, staged)


def check_communal(raw: bytes) -> tuple[dict, list]:
    obj = OmfReader(communals=True).read(raw)
    comms = sorted(bindings.communal_key(item) for item in obj.communals)
    return obj, comms


def run_fixture(out: Path, linker_name: str, linker: dict, tool_dir: Path,
                runner: dict, runtime_rows: list, main_obj: Path,
                alias_obj: Path, owner_obj: Path, case_name: str,
                expected: str, expected_far_bss_length: int | None,
                expected_owner_in_far_bss: bool) -> dict:
    directory = out / "fixtures" / linker_name / case_name
    directory.mkdir(parents=True)
    for obj, name in ((main_obj, "MAIN.OBJ"), (alias_obj, "ALIAS.OBJ"),
                      (owner_obj, "OWNER.OBJ")):
        shutil.copyfile(obj, directory / name)
    for row in runtime_rows:
        shutil.copyfile(row["path"], directory / Path(row["path"]).name.upper())
    (directory / "PROBE.LNK").write_bytes((
        "OUTPUT PROBE\r\nMAP = PROBE S,N,A,L\r\nNODEFLIB\r\n"
        "LIBRARY LLIBCR, LIBH\r\nFILE MAIN, ALIAS, OWNER\r\n").encode("ascii"))
    (directory / "RTLINK.CFG").write_bytes(b"SYNTAX = FREEFORMAT\r\n")
    (directory / "RUN.BAT").write_bytes((
        f"@echo off\r\nD:\\{linker['executable']} @PROBE.LNK < NUL > LINK.LOG\r\n"
        "PROBE.EXE > RUN.LOG\r\n").encode("ascii"))
    config = []
    for section, values in runner["conf"].items():
        config.append("[" + section + "]")
        config.extend(f"{key}={value}" for key, value in values.items())
    config.extend(["[autoexec]", f'mount c "{directory.resolve()}"',
                   f'mount d "{tool_dir}" -ro', "c:", "call RUN.BAT", "exit"])
    conf = directory / "dosbox.conf"
    conf.write_text("\n".join(config) + "\n", encoding="ascii")
    env = os.environ.copy()
    env.update(SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy")
    completed = subprocess.run(
        [runner["path"], "-conf", str(conf), "-fastlaunch", "-exit", "-nomenu"],
        cwd=directory, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        timeout=90, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    exe = directory / "PROBE.EXE"
    log_path = directory / "RUN.LOG"
    actual = log_path.read_text(encoding="latin1").strip() if log_path.exists() else ""
    link_text = (directory / "LINK.LOG").read_text(encoding="latin1", errors="replace") \
        if (directory / "LINK.LOG").exists() else ""
    layout = None
    map_path = directory / "PROBE.MAP"
    if map_path.exists():
        map_text = map_path.read_text(encoding="latin1", errors="replace")
        regions = []
        for row in re.finditer(
                r"^\s*([0-9A-F]+)H\s+([0-9A-F]+)H\s+([0-9A-F]+)H\s+FAR_BSS\s+FAR_BSS\s*$",
                map_text, re.M):
            start, stop, length = (int(value, 16) for value in row.groups())
            regions.append({"start_linear": start, "stop_linear": stop,
                            "length": length})
        data_regions = []
        for row in re.finditer(
                r"^\s*([0-9A-F]+)H\s+([0-9A-F]+)H\s+([0-9A-F]+)H\s+_DATA\s+DATA\s+DGROUP\s*$",
                map_text, re.M):
            start, stop, length = (int(value, 16) for value in row.groups())
            data_regions.append({"start_linear": start, "stop_linear": stop,
                                 "length": length})
        publics = {}
        by_name_at = map_text.find("Publics by Name")
        by_value_at = map_text.find("Publics by Value")
        if by_name_at < 0 or by_value_at <= by_name_at:
            raise RuntimeError("MAP lacks ordered public-name and public-value tables")
        name_table = map_text[by_name_at:by_value_at]
        value_table = map_text[by_value_at:]
        for name in ("_fd_50F6_01F0", "_fd_55B3_74FE", "_main"):
            pattern = r"^\s*([0-9A-F]+):([0-9A-F]+)\s+" + re.escape(name) + r"\s*$"
            by_name = re.findall(pattern, name_table, re.M)
            by_value = re.findall(pattern, value_table, re.M)
            if len(by_name) != 1 or len(by_value) != 1 or by_name != by_value:
                raise RuntimeError(f"MAP public tables disagree for {name}: {by_name!r}/{by_value!r}")
            publics[name] = {"segment": int(by_name[0][0], 16),
                             "offset": int(by_name[0][1], 16)}
        owner = publics["_fd_50F6_01F0"]
        owner_linear = (owner["segment"] << 4) + owner["offset"]
        owner_regions = [row for row in regions
                         if row["start_linear"] <= owner_linear <= row["stop_linear"]]
        owner_in_far_bss = len(owner_regions) == 1
        if owner_in_far_bss != expected_owner_in_far_bss:
            raise RuntimeError("MAP FAR_BSS ownership differs for selector: " + case_name)
        if expected_far_bss_length is not None:
            if len(owner_regions) != 1 or owner_regions[0]["length"] != expected_far_bss_length:
                raise RuntimeError("MAP FAR_BSS extent differs for selector: " + case_name)
            if owner_linear + expected_far_bss_length > owner_regions[0]["stop_linear"] + 1:
                raise RuntimeError("MAP selector extends beyond its FAR_BSS region")
        alias = publics["_fd_55B3_74FE"]
        alias_linear = (alias["segment"] << 4) + alias["offset"]
        alias_data_regions = [row for row in data_regions
                              if row["start_linear"] <= alias_linear <= row["stop_linear"]]
        if len(alias_data_regions) != 1:
            raise RuntimeError("MAP initialized pointer alias is not in exactly one _DATA/DGROUP region")
        if owner_regions and owner_regions[0]["start_linear"] <= alias_linear <= owner_regions[0]["stop_linear"]:
            raise RuntimeError("MAP pointer object was folded into the selector FAR_BSS object")
        layout = {"far_bss_regions": regions, "owner_in_far_bss": owner_in_far_bss,
                  "data_regions": data_regions, "alias_in_data_dgroup": True,
                  "owner_far_bss_region_length": owner_regions[0]["length"] if owner_regions else None,
                  "required_publics": publics}
    files = [pin(item) for item in sorted(directory.iterdir()) if item.is_file()]
    return {
        "linker": linker_name, "case": case_name, "expected_log": expected,
        "actual_log": actual, "link_succeeded": exe.exists(),
        "dosbox_exit": completed.returncode, "far_bss_layout": layout,
        "link_log_sha256": hashlib.sha256(link_text.encode("latin1", "replace")).hexdigest(),
        "files": files,
        "passed": exe.exists() and actual == expected and completed.returncode == 0,
    }


def main() -> int:
    parser = __import__("argparse").ArgumentParser()
    parser.add_argument("--out", type=Path,
                        default=ROOT / "build/workers/dos_sound_saved_state_owner/saved-sound-state-v19-fresh-run")
    out = parser.parse_args().out.resolve()
    allowed = (ROOT / "build/workers").resolve()
    if not out.is_relative_to(allowed) or out == allowed or out.exists():
        raise SystemExit("--out must be a new child directory under build/workers")
    review = json.loads(REVIEW_PATH.read_text(encoding="utf-8"))
    source_audit = json.loads(SOURCE_AUDIT_PATH.read_text(encoding="utf-8"))
    if review.get("root_decision", {}).get("accepted") is not False:
        raise RuntimeError("v19 review must remain root-false")
    if set(review.get("gate_effect", {}).values()) != {"UNRESOLVED"}:
        raise RuntimeError("v19 review must leave both gates unresolved")
    if source_audit.get("source_domain", {}).get("unique_sources") != 156:
        raise RuntimeError("reviewed 156-source domain changed")
    if hashlib.sha256(SOURCE_AUDIT_PATH.read_bytes()).hexdigest() != \
            review["source_domain"]["source_audit_sha256"]:
        raise RuntimeError("source-audit pin changed")
    if hashlib.sha256(PROVIDER_PATH.read_bytes()).hexdigest() != \
            review["candidate_provider"]["sha256"]:
        raise RuntimeError("source-owned provider pin changed")
    current_report_path = ROOT / review["current_effective_build"]["path"]
    if hashlib.sha256(current_report_path.read_bytes()).hexdigest() != \
            review["current_effective_build"]["sha256"]:
        raise RuntimeError("current build report pin changed")
    current_report = json.loads(current_report_path.read_text(encoding="utf-8"))
    unresolved = [row for row in current_report.get("unresolved_symbols", [])
                  if row.get("name") == "_fd_50F6_01F0"]
    if len(unresolved) != 1 or unresolved[0].get("accepted_storage_candidates") != []:
        raise RuntimeError("current build must still show selector owner unaccepted")

    out.mkdir(parents=True)
    (out / "sources").mkdir()
    (out / "objects").mkdir()
    compiler.WORK = out / "cc"
    compiler.WORK.mkdir()

    inputs, seen = [], set()
    profile = compiler.verify_profile("msc600ax")
    for rel, digest in profile["files"].items():
        pin_unique(inputs, seen, Path(profile["directory"]) / rel, digest)
    for name, digest in (profile.get("include_files") or {}).items():
        pin_unique(inputs, seen, compiler.include_root(profile) / name, digest)
    toolchain = compiler.toolchain()
    runner = toolchain["runners"]["dosbox-x"]
    pin_unique(inputs, seen, Path(runner["path"]), runner["sha256"])
    manifest = json.loads((ROOT / "layout/manifest.json").read_text(encoding="utf-8"))
    for path in ("layout/manifest.json", "layout/symbols.json", "layout/toolchain.json",
                 "tools/compiler.py", "tools/omf.py", "tools/dos_source_bindings.py",
                 "tools/source_only_dos.py", str(Path(__file__).relative_to(ROOT)),
                 str(PROBE_PATH.relative_to(ROOT)), str(REVIEW_PATH.relative_to(ROOT)),
                 "work/source-only-dos/saved-sound-state-v19/review.md",
                 str(SOURCE_AUDIT_PATH.relative_to(ROOT)),
                 str(PROVIDER_PATH.relative_to(ROOT)), str(current_report_path.relative_to(ROOT))):
        pin_unique(inputs, seen, ROOT / path)
    for row in review.get("supporting_reviews", []):
        pin_unique(inputs, seen, ROOT / row["path"], row["sha256"])
    for path, digest in review.get("tool_pins", {}).items():
        pin_unique(inputs, seen, ROOT / path, digest)
    for source in source_audit["source_domain"]["sources"]:
        pin_unique(inputs, seen, ROOT / source["path"], source["sha256"])
    runtimes = list(manifest["runtime"]["libraries"].values())
    for row in runtimes:
        pin_unique(inputs, seen, Path(row["path"]), row["sha256"])

    owner = compile_source(OWNER_SOURCE, "SSOWNER", out, inputs, seen)
    nonzero = compile_source(NONZERO_OWNER_SOURCE, "SSINIT", out, inputs, seen)
    wrong_width = compile_source(WRONG_WIDTH_SOURCE, "SSWRONG", out, inputs, seen)
    short = compile_source(SHORT_EXTENT_SOURCE, "SSSHORT", out, inputs, seen)
    alias = compile_source(ALIAS_SOURCE, "SSALIAS", out, inputs, seen)
    main_obj = compile_source(MAIN_SOURCE, "SSMAIN", out, inputs, seen)
    short_main = compile_source(SHORT_MAIN_SOURCE, "SSSHORTM", out, inputs, seen)
    owner_obj, owner_comm = check_communal(owner["obj"])
    expected_comm = [("_fd_50F6_01F0", "far", 7, 2, 14)]
    if owner_comm != expected_comm:
        raise RuntimeError("selector provider COMDEF differs: " + repr(owner_comm))
    if owner_obj.publics or owner_obj.segment_length("SSOWNER_TEXT") != 0:
        raise RuntimeError("selector provider is not solely an uninitialized FAR_BSS common")
    nonzero_obj, nonzero_comm = check_communal(nonzero["obj"])
    if nonzero_comm:
        raise RuntimeError("initialized negative control unexpectedly emitted a FAR_BSS common")
    nonzero_data = [name for name, value in nonzero_obj.segments.items() if value]
    if not nonzero_data:
        raise RuntimeError("initialized negative control emitted no data segment")
    wrong_obj, wrong_comm = check_communal(wrong_width["obj"])
    if wrong_comm != [("_fd_50F6_01F0", "far", 7, 4, 28)]:
        raise RuntimeError("wrong-width control did not emit the expected 28-byte far common")
    short_obj, short_comm = check_communal(short["obj"])
    if short_comm != [("_fd_50F6_01F0", "far", 6, 2, 12)]:
        raise RuntimeError("short-extent control did not emit the expected 12-byte far common")

    runtime_rows = []
    for row in runtimes:
        item = pin(Path(row["path"]), row["sha256"])
        runtime_rows.append({**row, **item})
    cases = []
    for linker_name in ("rtlink400", "rtlink610"):
        linker = toolchain["linkers"][linker_name]
        for rel, digest in linker["files"].items():
            pin_unique(inputs, seen, Path(linker["directory"]) / rel, digest)
        tool_dir = compiler.pinned_tree(linker)
        cases.append(run_fixture(out, linker_name, linker, tool_dir, runner,
                                 runtime_rows, main_obj["path"], alias["path"],
                                 owner["path"], "far_bss_zero_at_main", "PASS", 14, True))
        cases.append(run_fixture(out, linker_name, linker, tool_dir, runner,
                                 runtime_rows, main_obj["path"], alias["path"],
                                 nonzero["path"], "initialized_nonzero_control", "FAIL", None, False))
        cases.append(run_fixture(out, linker_name, linker, tool_dir, runner,
                                 runtime_rows, main_obj["path"], alias["path"],
                                 wrong_width["path"], "wrong_width_control", "PASS", 28, True))
        cases.append(run_fixture(out, linker_name, linker, tool_dir, runner,
                                 runtime_rows, short_main["path"], alias["path"],
                                 short["path"], "short_extent_control", "PASS", 12, True))

    controls = {
        "initialized_nonzero_detected": all(row["actual_log"] == "FAIL" for row in cases
                                             if row["case"] == "initialized_nonzero_control"),
        "wrong_width_shape_rejected": wrong_comm != expected_comm and all(
            row["far_bss_layout"]["owner_far_bss_region_length"] == 28 for row in cases
            if row["case"] == "wrong_width_control"),
        "short_extent_shape_rejected": short_comm != expected_comm and all(
            row["far_bss_layout"]["owner_far_bss_region_length"] == 12 for row in cases
            if row["case"] == "short_extent_control"),
        "all_maps_have_clean_required_publics_and_separate_data_alias": all(
            row["far_bss_layout"] is not None
            and row["far_bss_layout"]["alias_in_data_dgroup"]
            for row in cases),
    }
    result = {
        "schema": "simant-dos-saved-selector-startup-v19",
        "root_decision": review["root_decision"],
        "gate_effect": review["gate_effect"],
        "current_build_selector_owner_accepted": False,
        "candidate_source_contract": {
            "owner_source": OWNER_SOURCE.strip(),
            "pointer_alias_source": ALIAS_SOURCE.strip(),
            "owner_comdef": [dict(zip(("name", "kind", "count", "element_size", "length"), row))
                             for row in owner_comm],
            "nonzero_control_segments": nonzero_data,
            "wrong_width_comdef": [dict(zip(("name", "kind", "count", "element_size", "length"), row))
                                   for row in wrong_comm],
            "short_extent_comdef": [dict(zip(("name", "kind", "count", "element_size", "length"), row))
                                    for row in short_comm],
        },
        "fixtures": cases,
        "controls": controls,
        "denied_oracle_reads": denied,
        "all_required_checks_pass": (not denied and review["root_decision"]["accepted"] is False
                                      and set(review["gate_effect"].values()) == {"UNRESOLVED"}
                                      and owner_comm == expected_comm and len(cases) == 8
                                      and all(row["passed"] for row in cases)
                                      and all(controls.values())),
        "limits": [
            "Tests startup behavior of the root-false source-owned provider candidate; the provider remains outside the current effective build.",
            "Fixture map placement is linker-local and does not prove the original 50F6:01F0 address or historical object order.",
            "The pinned source corpus bounds observed use to words 0 through 6; unobserved external writers remain outside this source boundary.",
            "No original executable, original data, or database assets were compiler/linker/runtime inputs.",
        ],
        "inputs": inputs,
    }
    path = out / "saved-selector-startup-result.json"
    path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"all_required_checks_pass": result["all_required_checks_pass"],
                      "owner_comdef": result["candidate_source_contract"]["owner_comdef"],
                      "controls": result["controls"],
                      "fixtures": [{k: c[k] for k in ("linker", "case", "expected_log", "actual_log", "passed")}
                                  for c in cases], "result": str(path)}, indent=2))
    return 0 if result["all_required_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
