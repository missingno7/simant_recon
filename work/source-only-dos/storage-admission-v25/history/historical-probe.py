"""Bounded source-only owner/RTLink fixture for the v25 scalar audit."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import uuid


WORKER = Path(__file__).resolve().parent
ROOT = WORKER.parents[2]
RUN_ID = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid.uuid4().hex[:8]
RUN = WORKER / ("runtime-v25-" + RUN_ID)
RUN.mkdir(parents=True, exist_ok=False)
sys.path.insert(0, str(ROOT / "tools"))
import compiler
import source_only_dos as dos
from omf import OmfReader

DENIED_READS = dos.install_input_guard()
compiler.WORK = RUN / "compiler-work"
TARGETS = (
    "fd_50F6_0EAC", "fd_50F6_0EB4", "fd_50F6_0EF6", "fd_50F6_0EF8",
    "fd_50F6_0EFA", "fd_50F6_0F06", "fd_50F6_0F0C", "fd_50F6_0F0E",
    "fd_50F6_0F10", "fd_50F6_0F12", "fd_50F6_0F26", "fd_50F6_0F2E",
    "fd_50F6_0F34", "fd_50F6_0F36", "fd_50F6_0F3C", "fd_50F6_0F44",
    "fd_50F6_0F7A", "fd_50F6_0FC0",
)
SAVEREC_TARGETS = (
    "fd_50F6_0EAC", "fd_50F6_0EF8", "fd_50F6_0EFA", "fd_50F6_0F0C",
    "fd_50F6_0F0E", "fd_50F6_0F12", "fd_50F6_0F26", "fd_50F6_0F34",
    "fd_50F6_0F44",
)
WIDTH_FLAGS = ["/AL", "/Os", "/Gs"]
PROFILE = "msc600ax"
TAG_WIDTH = {"fd_50F6_0EB4": 4}


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def pin(path: Path) -> dict:
    raw = path.read_bytes()
    try:
        label = path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        label = str(path.resolve()).replace("\\", "/")
    return {"path": label, "size": len(raw), "sha256": sha(raw)}


def norm_comdefs(rows: list[dict]) -> list[dict]:
    return sorted(({k: row[k] for k in ("name", "kind", "count", "element_size", "length")}
                   for row in rows), key=lambda row: row["name"].lower())


def expected_comdefs(wide: bool = False, initialized: bool = False) -> list[dict]:
    rows = []
    for name in TARGETS:
        if initialized and name == "fd_50F6_0EB4":
            continue
        width = 4 if wide and name == "fd_50F6_0EB4" else 2
        rows.append({"name": "_" + name, "kind": "far", "count": width,
                     "element_size": 1, "length": width})
    return sorted(rows, key=lambda row: row["name"].lower())


def owner_source(wide: bool = False, initialized: bool = False) -> str:
    lines = ["/* Data-only review fixture; not a historical TU identity claim. */"]
    for name in TARGETS:
        typ = "long" if wide and name == "fd_50F6_0EB4" else "int"
        init = " = 1" if initialized and name == "fd_50F6_0EB4" else ""
        lines.append(f"{typ} far {name}{init};")
    return "\n".join(lines) + "\n"


VALUES = {name: (-1 if i == 0 else 0x1200 + i * 3) for i, name in enumerate(TARGETS)}


def declarations(names=TARGETS, overrides: dict[str, str] | None = None) -> str:
    overrides = overrides or {}
    return "".join(f"extern {overrides.get(name, 'int')} far {name};\n" for name in names)


def positive_source() -> str:
    lines = [declarations(),
        "struct SaveRec { int size; int count; void far *data; };",
        f"struct SaveRec far V25Save[{len(SAVEREC_TARGETS)}] = {{"]
    lines += [f"    {{2, 1, (void far *)&{name}}}," for name in SAVEREC_TARGETS]
    lines += ["};", "extern int far puts(char far *text);", "int main(void)", "{",
        "    unsigned char far *p;", "    unsigned int i;",
        "    if (" + " || ".join(f"{name} != 0" for name in TARGETS) + ") goto fail;"]
    for i, name in enumerate(SAVEREC_TARGETS):
        lines.append(f"    if (V25Save[{i}].size != 2 || V25Save[{i}].count != 1 || V25Save[{i}].data != (void far *)&{name}) goto fail;")
    for name in TARGETS:
        lines.append(f"    {name} = {VALUES[name]};")
    lines.append("    if (" + " || ".join(f"{name} != {VALUES[name]}" for name in TARGETS) + ") goto fail;")
    lines.append(f"    if ({TARGETS[0]} >= 0) goto fail;")
    for name in TARGETS:
        word = VALUES[name] & 0xFFFF
        lines.append(f"    p = (unsigned char far *)&{name};")
        lines.append(f"    if (p[0] != 0x{word & 0xff:02x} || p[1] != 0x{word >> 8:02x}) goto fail;")
    lines += ["    i = 0;", "    (void)i;", '    puts("PASS"); return 0;',
        'fail: puts("FAIL"); return 1;', "}"]
    return "\n".join(lines) + "\n"


def signedness_source() -> str:
    name = "fd_50F6_0EB4"
    return (f"extern unsigned int far {name};\n"
        "extern int far puts(char far *text);\nint main(void)\n{\n"
        f"    {name} = 0xffffU;\n"
        f"    if ((long){name} < 0L) {{ puts(\"PASS\"); return 0; }}\n"
        "    puts(\"FAIL\"); return 1;\n}\n")


def wide_source() -> str:
    name = "fd_50F6_0EB4"
    return (declarations(overrides={name: "long"}) +
        "extern int far puts(char far *text);\nint main(void)\n{\n"
        "    unsigned char far *p;\n"
        f"    if ({name} != 0L) goto fail;\n"
        f"    {name} = 0x11223344L;\n"
        f"    if ({name} != 0x11223344L) goto fail;\n"
        f"    p = (unsigned char far *)&{name};\n"
        "    if (p[0] != 0x44 || p[1] != 0x33 || p[2] != 0x22 || p[3] != 0x11) goto fail;\n"
        '    puts("PASS"); return 0;\nfail: puts("FAIL"); return 1;\n}\n')


def shifted_source() -> str:
    name = SAVEREC_TARGETS[0]
    return (declarations() +
        "struct SaveRec { int size; int count; void far *data; };\n"
        "unsigned char far ShiftBk[4];\n"
        "struct SaveRec far ShiftRec[1] = {{2, 1, (void far *)&ShiftBk[2]}};\n"
        "extern int far puts(char far *text);\nint main(void)\n{\n"
        "    unsigned char far *p;\n"
        f"    {name} = 0x1234;\n"
        "    if (ShiftBk[0] || ShiftBk[1] || ShiftBk[2] || ShiftBk[3]) goto fail;\n"
        "    if (ShiftRec[0].size != 2 || ShiftRec[0].count != 1 ||\n"
        "        ShiftRec[0].data != (void far *)&ShiftBk[2] ||\n"
        f"        ShiftRec[0].data == (void far *)&{name}) goto fail;\n"
        "    p = (unsigned char far *)ShiftRec[0].data;\n"
        "    p[0] = 0x78; p[1] = 0x56;\n"
        "    if (p[0] != 0x78 || p[1] != 0x56 ||\n"
        "        ShiftBk[0] || ShiftBk[1] || ShiftBk[2] != 0x78 || ShiftBk[3] != 0x56 ||\n"
        f"        {name} != 0x1234) goto fail;\n"
        '    puts("PASS"); return 0;\nfail: puts("FAIL"); return 1;\n}\n')


def compile_one(tag: str, source: str) -> tuple[bytes, dict, object]:
    if len(tag) > 8:
        raise RuntimeError(f"DOS compiler basename exceeds eight characters: {tag}")
    result = compiler.compile_c(source, PROFILE, WIDTH_FLAGS, basename=tag, keep=True)
    if not result.ok or result.obj is None:
        raise RuntimeError(f"compile failed for {tag}:\n{result.log}")
    folder = RUN / "compile-artifacts"
    folder.mkdir(exist_ok=True)
    src_path, obj_path, log_path = (folder / f"{tag}.C", folder / f"{tag}.OBJ", folder / f"{tag}.LOG")
    src_path.write_text(source, encoding="ascii", newline="\r\n")
    obj_path.write_bytes(result.obj)
    log_path.write_text(result.log, encoding="latin1")
    parsed = OmfReader(communals=True).read(result.obj, f"{tag}.OBJ")
    fixups = [row for row in parsed.linker_fixups if row.get("loc") == "pointer32" and row.get("width") == 4]
    receipt = {"tag": tag, "profile": PROFILE, "flags": result.argv,
        "artifacts": [pin(src_path), pin(obj_path), pin(log_path)],
        "communals": norm_comdefs(parsed.communals), "segment_lengths": parsed.segment_lengths,
        "publics": parsed.publics, "externals": parsed.externals,
        "all_pointer32_fixups": fixups}
    omf_path = folder / f"{tag}-omf.json"
    omf_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    receipt["omf_analysis"] = pin(omf_path)
    return result.obj, receipt, parsed


def map_receipt(text: str) -> dict:
    lines = text.splitlines()
    def publics(header: str) -> dict[str, str]:
        start = next((i for i, line in enumerate(lines) if header in line), None)
        if start is None:
            return {}
        found = {}
        for line in lines[start + 1:]:
            if any(s in line for s in ("Publics by Name", "Publics by Value", "Line Numbers for", "Module Summary")):
                break
            m = re.match(r"\s*([0-9A-F]{4}:[0-9A-F]{4})\s+\w+\s+(_fd_50F6_[0-9A-F]{4})\s*$", line, re.I)
            if m:
                found[m.group(2).lower()] = m.group(1).upper()
        return found
    by_name, by_value = publics("Publics by Name"), publics("Publics by Value")
    targets = {("_" + n).lower() for n in TARGETS}
    named = {n: by_name[n] for n in sorted(targets) if n in by_name}
    valued = {n: by_value[n] for n in sorted(targets) if n in by_value}
    relevant = [line.strip() for line in lines if re.search(r"\b(?:FAR_BSS|FAR_DATA|_BSS|_DATA)\b", line, re.I)]
    return {"target_public_addresses_by_name": named, "target_public_addresses_by_value": valued,
        "Name_and_Value_public_relations_exact": named == valued and len(named) == len(TARGETS),
        "target_public_count": len(named), "data_segment_map_rows": relevant}


def run_case(linker_name: str, case_name: str, consumer: bytes, owner: bytes,
             manifest: dict, tc: dict) -> dict:
    linker = tc["linkers"][linker_name]
    runner = tc["runners"][linker["runner"]]
    tool_dir = compiler.pinned_tree(linker)
    runtimes = list(manifest["runtime"]["libraries"].values())
    directory = RUN / "link-runs" / ("R400" if linker_name == "rtlink400" else "R610") / case_name
    directory.mkdir(parents=True, exist_ok=False)
    for path, raw in ((directory / "CRT.OBJ", consumer), (directory / "OWNER.OBJ", owner)):
        path.write_bytes(raw)
    for row in runtimes:
        shutil.copyfile(row["path"], directory / Path(row["path"]).name.upper())
    (directory / "PROBE.LNK").write_bytes(
        b"OUTPUT PROBE\r\nMAP = PROBE S,N,A,L\r\nNODEFLIB\r\nLIBRARY LLIBCR, LIBH\r\nFILE CRT\r\nBEGINAREA\r\nSECTION FILE OWNER\r\nENDAREA\r\n")
    (directory / "RTLINK.CFG").write_bytes(b"SYNTAX = FREEFORMAT\r\n")
    (directory / "RUN.BAT").write_bytes((f"@echo off\r\nD:\\{linker['executable']} @PROBE.LNK < NUL > LINK.LOG\r\n"
        "PROBE.EXE > RUN.LOG\r\n").encode("ascii"))
    conf = []
    for section, settings in runner["conf"].items():
        conf.append("[" + section + "]")
        conf += [f"{key}={value}" for key, value in settings.items()]
    conf += ["[autoexec]", f'mount c "{directory.resolve()}"', f'mount d "{tool_dir.resolve()}" -ro',
             "c:", "call RUN.BAT", "exit"]
    (directory / "dosbox.conf").write_text("\n".join(conf) + "\n", encoding="ascii")
    env = os.environ.copy()
    env.update(SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy")
    timed_out, exit_code = False, -1
    try:
        done = subprocess.run([runner["path"], "-conf", str(directory / "dosbox.conf"),
            "-fastlaunch", "-exit", "-nomenu"], cwd=directory, env=env,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=90,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        exit_code = done.returncode
    except subprocess.TimeoutExpired:
        timed_out = True
    log_path, link_path, map_path, exe_path = (directory / n for n in ("RUN.LOG", "LINK.LOG", "PROBE.MAP", "PROBE.EXE"))
    actual_bytes = log_path.read_bytes() if log_path.exists() else b""
    link_bytes = link_path.read_bytes() if link_path.exists() else b""
    map_text = map_path.read_text(encoding="latin1", errors="replace") if map_path.exists() else ""
    files = [p for p in directory.iterdir() if p.is_file()]
    return {"linker": linker_name, "case": case_name, "actual": actual_bytes.decode("latin1", "replace").strip(),
        "actual_hex": actual_bytes.hex(), "actual_sha256": sha(actual_bytes),
        "link_log": link_bytes.decode("latin1", "replace"), "link_log_sha256": sha(link_bytes),
        "map_text": map_text, "map_sha256": sha(map_text.encode("latin1", "replace")),
        "map_receipt": map_receipt(map_text), "emulator_exit": exit_code, "timed_out": timed_out,
        "executable_produced": exe_path.exists(), "files": [pin(p) for p in sorted(files)],
        "runtime_libraries": [pin(Path(r["path"])) for r in runtimes],
        "linker_tools": {"executable": pin(Path(linker["directory"]) / linker["executable"]),
            "files": [pin(Path(linker["directory"]) / rel) for rel in linker["files"]]},
        "runner": pin(Path(runner["path"]))}


def main() -> None:
    manifest = json.loads((ROOT / "layout/manifest.json").read_text(encoding="utf-8"))
    tc = compiler.toolchain()
    owner_obj, owner_r, owner_parsed = compile_one("OWNBASE", owner_source())
    init_obj, init_r, init_parsed = compile_one("OWNINIT", owner_source(initialized=True))
    wide_obj, wide_r, wide_parsed = compile_one("OWNWIDE", owner_source(wide=True))
    expected = expected_comdefs()
    if owner_r["communals"] != expected:
        raise RuntimeError("base natural-int owner COMDEF set differs from eighteen 2-byte FAR scalars")
    if init_r["communals"] != expected_comdefs(initialized=True):
        raise RuntimeError("initialized owner did not remove exactly its initialized target COMDEF")
    if wide_r["communals"] != expected_comdefs(wide=True):
        raise RuntimeError("wide owner contrast did not change only the selected scalar COMDEF to four bytes")
    pos_obj, pos_r, pos_parsed = compile_one("CRTPOS", positive_source())
    sign_obj, sign_r, _ = compile_one("CRTSIGN", signedness_source())
    widc_obj, widc_r, widc_parsed = compile_one("CRTWIDE", wide_source())
    initc_obj, initc_r, _ = compile_one("CRTINIT", positive_source())
    shft_obj, shft_r, shft_parsed = compile_one("CRTSHFT", shifted_source())
    source_targets = {"_" + n for n in SAVEREC_TARGETS}
    pos_fix = sorted((f for f in pos_parsed.linker_fixups if f.get("loc") == "pointer32" and f.get("width") == 4
                      and f.get("target") in source_targets), key=lambda f: f.get("offset", -1))
    if len(pos_fix) != len(SAVEREC_TARGETS) or {f.get("target") for f in pos_fix} != source_targets:
        raise RuntimeError("positive source SaveRec fixture lacks the exact nine symbolic target relocations")
    if any(f.get("encoded_addend") != "00000000" for f in pos_fix):
        raise RuntimeError("positive source SaveRec fixture has an unexpected pointer addend")
    shifted_fix = [f for f in shft_parsed.linker_fixups if f.get("loc") == "pointer32" and f.get("width") == 4
                   and f.get("target", "").lower() == "_shiftbk"]
    if len(shifted_fix) != 1 or shifted_fix[0].get("target", "").lower() != "_shiftbk" or shifted_fix[0].get("encoded_addend") != "02000000":
        raise RuntimeError("separate backing SaveRec fixture lacks a symbolic +2 pointer relocation")
    wide_comdef = next(row for row in wide_r["communals"] if row["name"] == "_fd_50F6_0EB4")
    base_comdef = next(row for row in owner_r["communals"] if row["name"] == "_fd_50F6_0EB4")
    if base_comdef["length"] != 2 or wide_comdef["length"] != 4:
        raise RuntimeError("natural-int versus deliberate-long OMF contrast is not 2 vs 4 bytes")
    compile_rows = [owner_r, init_r, wide_r, pos_r, sign_r, widc_r, initc_r, shft_r]
    compile_receipt_path = RUN / "compile-receipts.json"
    compile_receipt_path.write_text(json.dumps(compile_rows, indent=2) + "\n", encoding="utf-8")

    cases = []
    specs = [
        ("POSITIVE", pos_obj, owner_obj, "PASS", "typed/raw-zero-write plus exact known SaveRec pointers"),
        ("SIGNED", sign_obj, owner_obj, "FAIL", "unsigned consumer signedness contrast"),
        ("WIDE", widc_obj, wide_obj, "PASS", "deliberate 4-byte long provider/consumer control"),
        ("INIT", initc_obj, init_obj, "FAIL", "nonzero-initialized owner startup-zero contrast"),
        ("SHIFT02", shft_obj, owner_obj, "PASS", "SaveRec pointer to independent backing plus two bytes"),
    ]
    for linker_name in ("rtlink400", "rtlink610"):
        for label, consumer, owner, expected_output, meaning in specs:
            row = run_case(linker_name, label, consumer, owner, manifest, tc)
            row["expected"] = expected_output
            row["meaning"] = meaning
            # DOSBox-X's exit code is the shell/emulator session status. The C fixture's
            # printed PASS/FAIL marker is the explicit expected result for each control.
            row["passed"] = (row["actual"] == expected_output and not row["timed_out"]
                             and row["executable_produced"]
                             and row["map_receipt"]["Name_and_Value_public_relations_exact"])
            cases.append(row)
    runtime_path = RUN / "runtime-candidate.json"
    runtime_doc = {"schema": "simant-remaining-history-scalars-runtime-v25",
        "status": "ROOT_REVIEW_PENDING_UNADMITTED", "root_reviewed": False, "root_claimed": False,
        "production_source_changed": False, "historical_build_input_used": False,
        "worker": str(WORKER.relative_to(ROOT)).replace("\\", "/"), "run_id": RUN_ID,
        "cohort": list(TARGETS), "known_source_SaveRec_fixture_targets": list(SAVEREC_TARGETS),
        "signed_int_far_count": len(TARGETS), "expected_owner_COMDEFs": expected,
        "actual_owner_COMDEFs": owner_r["communals"],
        "natural_owner_exact_2_byte_COMDEF_set": owner_r["communals"] == expected,
        "compile_controls": {"initialized_owner_exact_COMDEFs": init_r["communals"],
            "initialized_control_removes_only_0EB4": init_r["communals"] == expected_comdefs(initialized=True),
            "wide_owner_exact_COMDEFs": wide_r["communals"],
            "wide_control_changes_0EB4_to_4_bytes": wide_comdef["length"] == 4 and base_comdef["length"] == 2,
            "base_owner": owner_r, "initialized_owner": init_r, "wide_owner": wide_r,
            "positive_fixture": pos_r, "signedness_fixture": sign_r, "wide_consumer_fixture": widc_r,
            "initialized_consumer_fixture": initc_r, "shifted_fixture": shft_r,
            "source_SaveRec_fixture_symbolic_zero_addend_targets": sorted(f["target"] for f in pos_fix),
            "separate_backing_shift_pointer_fixup": shifted_fix},
        "runtime_case_count_per_linker": len(specs), "runtime_cases": cases,
        "all_runtime_markers_and_map_relations_pass": len(cases) == 10 and all(c["passed"] for c in cases),
        "runtime_toolchain": {"compiler": tc["profiles"][PROFILE],
            "linkers": {name: tc["linkers"][name] for name in ("rtlink400", "rtlink610")},
            "runners": {"dosbox-x": tc["runners"]["dosbox-x"]},
            "runtime_libraries": manifest["runtime"]["libraries"]},
        "denied_original_build_reads": list(DENIED_READS),
        "unresolved_domains": ["No historical communal-producing TU identity is inferred.",
            "The source SaveRec rows provide raw byte-span anchors only; LoadGame is not validated.",
            "No gameplay, invalid-load, lifetime, first-use, or lifecycle claim is made.",
            "The 0F38 and 0FB6 candidates remain unresolved because no source writer is proven."]}
    runtime_path.write_text(json.dumps(runtime_doc, indent=2) + "\n", encoding="utf-8")
    md = ["# Remaining history scalar owner runtime v25", "",
        "Status: `ROOT_REVIEW_PENDING_UNADMITTED`. This scratch fixture contains eighteen natural signed `int far` tentative definitions. It is source-only and data-only; it does not build or run the game, use original object/image bytes, or assert historical TU identity.", "",
        "The positive program checks startup zero, typed writes/reads, signed negative behavior, all eighteen 2-byte raw views, and the nine known source SaveRec symbolic pointers. Controls cover unsigned interpretation, one deliberate four-byte long owner/consumer, a nonzero initializer, and a +2 SaveRec pointer into its own separate four-byte backing array.", "",
        "| Linker | Case | Expected marker | Actual marker | Name/Value map | Passed |", "|---|---|---|---|---:|---|"]
    for row in cases:
        md.append(f"| {row['linker']} | `{row['case']}` | `{row['expected']}` | `{row['actual']}` | {row['map_receipt']['Name_and_Value_public_relations_exact']} | {row['passed']} |")
    md += ["", "Each linker ran five cases. The generated C/OBJ/compiler logs, OMF analyses, staged LINK inputs, raw LINK/RUN logs, MAP text and public Name/Value relations, and EXE outputs are preserved beneath this unique run directory. No acceptance, promotion, canonical edit, production link, or Git operation was performed.", ""]
    md_path = RUN / "runtime-candidate.md"
    md_path.write_text("\n".join(md), encoding="utf-8")
    summary = {"schema": "simant-remaining-history-scalars-runtime-index-v25", "run_id": RUN_ID,
        "run_directory": RUN.relative_to(ROOT).as_posix(), "runtime_candidate": pin(runtime_path),
        "markdown": pin(md_path), "compile_receipts": pin(compile_receipt_path),
        "root_reviewed": False, "root_claimed": False,
        "all_runtime_markers_and_map_relations_pass": runtime_doc["all_runtime_markers_and_map_relations_pass"],
        "cases_per_linker": {name: sum(c["linker"] == name for c in cases) for name in ("rtlink400", "rtlink610")}}
    index_path = RUN / "run-index.json"
    index_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    if not summary["all_runtime_markers_and_map_relations_pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
