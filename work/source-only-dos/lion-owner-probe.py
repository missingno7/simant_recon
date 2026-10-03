"""Bounded FAR_BSS ownership controls for AntsEatenByLions/InitialLions.

This is a research-only worker probe. It compiles the exact canonical root
module with tentative far-int definitions, compares every parsed OMF code/data
contribution to a fresh control, and runs clean test-owned runtime controls.
No canonical source, manifest, link input, or original executable is changed or
used as a byte capsule.
"""
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
OUT = ROOT / "build/workers/dos_lion_scalar_owners"
OUT.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(ROOT / "tools"))
import compiler
from omf import OmfReader

NAMES = ("AntsEatenByLions", "InitialLions")
EXPECTED_LENGTHS = {"_AntsEatenByLions": 2, "_InitialLions": 2}
ROOT_SOURCE = ROOT / "src/root/m0AD9.c"
SAVE_SOURCE = ROOT / "src/S09/m35F5.c"
MANIFEST_PATH = ROOT / "layout/manifest.json"
SYMBOLS_PATH = ROOT / "layout/symbols.json"

WORD_CONSUMER = r'''extern int far AntsEatenByLions;
extern int far InitialLions;
extern int far lion_owner_extent(void);
extern int far lion_pair_sum(void);
extern int far puts(char far *text);
int main(void)
{
    if (lion_owner_extent() != 4 || AntsEatenByLions != 0 ||
        InitialLions != 0 || lion_pair_sum() != 0) {
        puts("FAIL");
        return 1;
    }
    AntsEatenByLions = 0x1234;
    InitialLions = 0x5678;
    if (AntsEatenByLions != 0x1234 || InitialLions != 0x5678 ||
        lion_pair_sum() != 0x68AC) {
        puts("FAIL");
        return 1;
    }
    puts("PASS");
    return 0;
}
'''

BYTE_CONSUMER = r'''extern int far AntsEatenByLions;
extern int far InitialLions;
extern int far lion_owner_extent(void);
extern int far lion_pair_sum(void);
extern int far puts(char far *text);
struct SaveRec { int size; int count; void far *data; };
struct SaveRec far LionSaveRows[2] = {
    {2, 1, (void far *)&AntsEatenByLions},
    {2, 1, (void far *)&InitialLions}
};
int main(void)
{
    unsigned char far *eaten;
    unsigned char far *initial;
    eaten = (unsigned char far *)LionSaveRows[0].data;
    initial = (unsigned char far *)LionSaveRows[1].data;
    if (lion_owner_extent() != 4 ||
        LionSaveRows[0].size != 2 || LionSaveRows[0].count != 1 ||
        LionSaveRows[1].size != 2 || LionSaveRows[1].count != 1 ||
        eaten != (unsigned char far *)&AntsEatenByLions ||
        initial != (unsigned char far *)&InitialLions ||
        eaten[0] != 0 || eaten[1] != 0 || initial[0] != 0 || initial[1] != 0 ||
        lion_pair_sum() != 0) {
        puts("FAIL");
        return 1;
    }
    eaten[0] = 0x34;
    eaten[1] = 0x12;
    initial[0] = 0x78;
    initial[1] = 0x56;
    if (AntsEatenByLions != 0x1234 || InitialLions != 0x5678 ||
        lion_pair_sum() != 0x68AC) {
        puts("FAIL");
        return 1;
    }
    InitialLions = 0x2468;
    if (initial[0] != 0x68 || initial[1] != 0x24 ||
        lion_pair_sum() != 0x369C) {
        puts("FAIL");
        return 1;
    }
    puts("PASS");
    return 0;
}
'''

BAD_EXTENT_BYTE_CONSUMER = BYTE_CONSUMER.replace(
    "{2, 1, (void far *)&AntsEatenByLions}",
    "{2, 2, (void far *)&AntsEatenByLions}")

OWNER = r'''int far AntsEatenByLions;
int far InitialLions;
int far lion_pair_sum(void)
{
    return AntsEatenByLions + InitialLions;
}
int far lion_owner_extent(void)
{
    return sizeof(AntsEatenByLions) + sizeof(InitialLions);
}
'''

WRONG_TYPE_OWNER = r'''long far AntsEatenByLions;
int far InitialLions;
int far lion_pair_sum(void)
{
    return (int)AntsEatenByLions + InitialLions;
}
int far lion_owner_extent(void)
{
    return sizeof(AntsEatenByLions) + sizeof(InitialLions);
}
'''

WRONG_EXTENT_OWNER = r'''int far AntsEatenByLions[2];
int far InitialLions;
int far lion_pair_sum(void)
{
    return AntsEatenByLions[0] + InitialLions;
}
int far lion_owner_extent(void)
{
    return sizeof(AntsEatenByLions) + sizeof(InitialLions);
}
'''

INITIALIZED_OWNER = r'''int far AntsEatenByLions = 1;
int far InitialLions = 2;
int far lion_pair_sum(void)
{
    return AntsEatenByLions + InitialLions;
}
int far lion_owner_extent(void)
{
    return sizeof(AntsEatenByLions) + sizeof(InitialLions);
}
'''


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_pin(path: Path) -> dict:
    raw = path.read_bytes()
    return {"path": path.relative_to(ROOT).as_posix(), "sha256": sha(raw), "bytes": len(raw)}


def compile_source(name: str, source: str, flags: list[str], compiler_basename: str | None = None) -> bytes:
    (OUT / (name + ".c")).write_text(source, encoding="ascii", newline="\n")
    result = compiler.compile_c(source, "msc600ax", flags, basename=compiler_basename or name)
    if not result.ok or result.obj is None:
        (OUT / (name + ".compile.log")).write_text(result.log, encoding="latin1")
        raise RuntimeError(f"compile failed for {name}: {result.log[-3000:]}")
    raw = bytes(result.obj)
    (OUT / (name + ".OBJ")).write_bytes(raw)
    return raw


def object_view(raw: bytes) -> tuple:
    omf = OmfReader(communals=True).read(raw)
    view = {
        "segments": {k: sha(v) for k, v in sorted(omf.segments.items())},
        "segment_byte_lengths": {k: len(v) for k, v in sorted(omf.segments.items())},
        "segment_lengths": omf.segment_lengths,
        "segment_defs": omf.segment_defs,
        "groups": omf.groups,
        "publics": omf.publics,
        "local_publics": omf.local_publics,
        "fixups": omf.fixups,
        "linker_fixups": omf.linker_fixups,
        "external_names": omf.externals,
        "external_scopes": omf.external_scopes,
        "local_externals": omf.local_externals,
        "communals": omf.communals,
    }
    return omf, view


def extent_records(omf) -> list[dict]:
    return [{"name": c["name"], "kind": c["kind"], "length": c["length"],
             "count": c.get("count"), "element_size": c.get("element_size")}
            for c in omf.communals]


def source_use_inventory() -> dict:
    token = re.compile(r"\b(?:AntsEatenByLions|InitialLions)\b")
    users = {}
    all_users = {}
    occurrences = {}
    for path in sorted(p for p in (ROOT / "src").rglob("*")
                       if p.is_file() and p.suffix.lower() in {".c", ".asm", ".h", ".inc"}):
        raw = path.read_text(encoding="latin1")
        hits = []
        for n, line in enumerate(raw.splitlines(), 1):
            names = token.findall(line)
            if names:
                hits.append({"line": n, "text": line.strip(), "names": names})
        if hits:
            rel = path.relative_to(ROOT).as_posix()
            all_users[rel] = hits
            if path.suffix.lower() != ".c":
                continue
            users[rel] = hits
            for name in NAMES:
                occurrences[name] = occurrences.get(name, 0) + sum(name in h["names"] for h in hits)
    return {"canonical_c_users": users, "canonical_occurrence_count": occurrences,
            "all_source_users": all_users}


def address_aliases() -> dict:
    syms = json.loads(SYMBOLS_PATH.read_text(encoding="utf-8"))["data"]
    targets = {"AntsEatenByLions": (0x50F6, 0x0A08),
               "InitialLions": (0x50F6, 0x08EA)}
    result = {}
    for name, (segment, offset) in targets.items():
        rows = [{"name": key, "seg": val.get("seg"), "off": val.get("off")}
                for key, val in syms.items()
                if val.get("seg") == segment and offset <= val.get("off", -1) < offset + 2]
        result[name] = {"within_two_byte_extent": rows,
                        "exact_base": [row for row in rows if row["off"] == offset],
                        "interior": [row for row in rows if row["off"] != offset]}
    return result


def compile_runtime_fixtures() -> dict:
    m = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    tc = compiler.toolchain()
    flags_owner = ["/AL", "/Os", "/Oe", "/Og", "/Zi"]
    flags_consumer = ["/AL", "/Os", "/Zi"]
    owner_obj = compile_source("LIONOWNR", OWNER, flags_owner)
    wrong_type_obj = compile_source("LIONTYPE", WRONG_TYPE_OWNER, flags_owner)
    wrong_extent_obj = compile_source("LIONEXNT", WRONG_EXTENT_OWNER, flags_owner)
    initialized_obj = compile_source("LIONINIT", INITIALIZED_OWNER, flags_owner)
    word_obj = compile_source("LIONWORD", WORD_CONSUMER, flags_consumer)
    byte_obj = compile_source("LIONBYTE", BYTE_CONSUMER, flags_consumer)
    bad_extent_byte_obj = compile_source("LIONBADX", BAD_EXTENT_BYTE_CONSUMER, flags_consumer)

    owner_omf, _ = object_view(owner_obj)
    wrong_type_omf, _ = object_view(wrong_type_obj)
    wrong_extent_omf, _ = object_view(wrong_extent_obj)
    initialized_omf, _ = object_view(initialized_obj)
    expected = sorted(EXPECTED_LENGTHS.items())
    owner_shape = sorted((c["name"], c["length"]) for c in owner_omf.communals)
    if owner_shape != expected or len(owner_omf.communals) != 2:
        raise RuntimeError(f"minimal typed owner communal mismatch: {owner_shape}")
    wrong_type_shape = sorted((c["name"], c["length"]) for c in wrong_type_omf.communals)
    wrong_extent_shape = sorted((c["name"], c["length"]) for c in wrong_extent_omf.communals)
    if wrong_type_shape != [("_AntsEatenByLions", 4), ("_InitialLions", 2)]:
        raise RuntimeError(f"wrong-type control did not produce 4+2 byte commons: {wrong_type_shape}")
    if wrong_extent_shape != [("_AntsEatenByLions", 4), ("_InitialLions", 2)]:
        raise RuntimeError(f"wrong-extent control did not produce 4+2 byte commons: {wrong_extent_shape}")
    init_names = {p["name"] for p in initialized_omf.publics}
    if initialized_omf.communals or not set(EXPECTED_LENGTHS) <= init_names:
        raise RuntimeError("initialized contrast did not become initialized public storage")

    inputs = []
    for path in (MANIFEST_PATH, ROOT / "layout/toolchain.json", ROOT / "src/root/m0AD9.c",
                 ROOT / "src/S09/m35F5.c"):
        inputs.append(file_pin(path))
    cases = []
    runtime_rows = list(m["runtime"]["libraries"].values())
    runner = tc["runners"]["dosbox-x"]
    for runtime_row in runtime_rows:
        inputs.append({"path": runtime_row["path"], "sha256": runtime_row["sha256"]})
    inputs.append({"path": runner["path"], "sha256": runner["sha256"]})
    for profile in ("rtlink400", "rtlink610"):
        linker = tc["linkers"][profile]
        for rel, digest in linker["files"].items():
            inputs.append({"path": str(Path(linker["directory"]) / rel), "sha256": digest})
        tool_dir = compiler.pinned_tree(linker)
        for case, client, owner, expected_text in (
                ("typed_word", word_obj, owner_obj, "PASS"),
                ("typed_SaveRec_byte", byte_obj, owner_obj, "PASS"),
                ("wrong_type_extent", word_obj, wrong_type_obj, "FAIL"),
                ("wrong_array_extent", byte_obj, wrong_extent_obj, "FAIL"),
                ("wrong_SaveRec_row_extent", bad_extent_byte_obj, owner_obj, "FAIL"),
                ("initialized_nonzero_owner", byte_obj, initialized_obj, "FAIL")):
            cases.append(run_link_case(profile, case, client, owner, expected_text,
                                       runtime_rows, linker, runner, tool_dir))
    if len(cases) != 12 or not all(row["passed"] for row in cases):
        raise RuntimeError("runtime owner/SaveRec controls did not meet expected outcomes")
    return {
        "profile_flags": {"owner": flags_owner, "consumers": flags_consumer},
        "owner_objects": {
            "typed": {"sha256": sha(owner_obj), "bytes": len(owner_obj),
                      "communals": owner_omf.communals, "full_canonical_module_linked": False},
            "wrong_type": {"sha256": sha(wrong_type_obj), "communals": wrong_type_omf.communals},
            "wrong_extent": {"sha256": sha(wrong_extent_obj), "communals": wrong_extent_omf.communals},
            "initialized": {"sha256": sha(initialized_obj), "communals": initialized_omf.communals,
                            "publics": [p for p in initialized_omf.publics if p["name"] in EXPECTED_LENGTHS]},
        },
        "cases": cases,
        "runtime_inputs": inputs,
        "expected_outcomes_pass": True,
        "limitations": [
            "The fixture uses a minimal typed owner and one test-only accessor, not game functions or game-module link stubs.",
            "It exercises startup zero-fill, word access, and a SaveRec-shaped byte pointer; it does not execute InitAntLions, LoadGame, or SaveGame.",
            "The full canonical root module is measured separately and is never linked into these runtime fixtures.",
            "RTLink alias DEFINE controls are unnecessary: the registry has no second name at either exact address."
        ]
    }


def run_link_case(profile: str, case: str, consumer: bytes, owner: bytes,
                  expected_text: str, runtime_rows: list, linker: dict,
                  runner: dict, tool_dir: Path) -> dict:
    directory = OUT / profile / case
    directory.mkdir(parents=True, exist_ok=True)
    for name in ("PROBE.EXE", "PROBE.MAP", "RUN.LOG", "LINK.LOG"):
        (directory / name).unlink(missing_ok=True)
    (directory / "CRT.OBJ").write_bytes(consumer)
    (directory / "OWNER.OBJ").write_bytes(owner)
    for row in runtime_rows:
        shutil.copyfile(row["path"], directory / Path(row["path"]).name.upper())
    script = ("OUTPUT PROBE\r\nMAP = PROBE S,N,A,L\r\nNODEFLIB\r\n"
              "LIBRARY LLIBCR, LIBH\r\n"
              "FILE CRT\r\n"
              "BEGINAREA\r\nSECTION FILE OWNER\r\nENDAREA\r\n")
    (directory / "PROBE.LNK").write_bytes(script.encode("ascii"))
    (directory / "RTLINK.CFG").write_bytes(b"SYNTAX = FREEFORMAT\r\n")
    (directory / "RUN.BAT").write_bytes((
        f"@echo off\r\nD:\\{linker['executable']} @PROBE.LNK < NUL > LINK.LOG\r\n"
        "PROBE.EXE > RUN.LOG\r\n").encode("ascii"))
    config = []
    for section, settings in runner["conf"].items():
        config.append("[" + section + "]")
        config += [f"{k}={v}" for k, v in settings.items()]
    config += ["[autoexec]", f'mount c "{directory}"', f'mount d "{tool_dir}" -ro',
               "c:", "call RUN.BAT", "exit"]
    conf = directory / "dosbox.conf"
    conf.write_text("\n".join(config) + "\n", encoding="ascii")
    env = os.environ.copy()
    env.update(SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy")
    timed_out = False
    try:
        run = subprocess.run([runner["path"], "-conf", str(conf), "-fastlaunch", "-exit", "-nomenu"],
                             cwd=directory, env=env, stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL, timeout=60,
                             creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    except subprocess.TimeoutExpired:
        timed_out = True
        run = type("TimedOut", (), {"returncode": -1})()
    log_path = directory / "RUN.LOG"
    actual = log_path.read_text(encoding="latin1").strip() if log_path.exists() else "NO RUN.LOG"
    link_path = directory / "LINK.LOG"
    link_log = link_path.read_text(encoding="latin1", errors="replace") if link_path.exists() else ""
    row = {"linker": profile, "case": case, "expected": expected_text, "actual": actual,
           "emulator_exit": run.returncode, "timed_out": timed_out,
           "passed": actual == expected_text and run.returncode == 0 and not timed_out,
           "link_log_tail": link_log[-800:]}
    print(profile, case, actual, flush=True)
    return row


def main() -> int:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    module = manifest["modules"]["root:0AD9"]
    if module["source"] != "src/root/m0AD9.c":
        raise RuntimeError("manifest source owner changed")
    if sha(ROOT_SOURCE.read_bytes()) != module["source_sha256"]:
        raise RuntimeError("canonical root source hash differs from manifest")
    root_text = ROOT_SOURCE.read_text(encoding="latin1")
    for name in NAMES:
        expected_decl = f"extern int far {name};"
        if root_text.count(expected_decl) != 1:
            raise RuntimeError(f"expected one canonical declaration: {expected_decl}")
    candidate_text = root_text
    for name in NAMES:
        candidate_text = candidate_text.replace(f"extern int far {name};", f"int far {name};", 1)
    wrong_type_text = root_text.replace("extern int far InitialLions;", "long far InitialLions;", 1)
    if candidate_text == root_text or root_text.replace(
            "extern int far AntsEatenByLions;", "", 1).replace(
            "extern int far InitialLions;", "", 1) != candidate_text.replace(
            "int far AntsEatenByLions;", "", 1).replace("int far InitialLions;", "", 1):
        raise RuntimeError("typed owner candidate must differ only in the two tentative declarations")

    flags = list(module["flags"])
    control_obj = compile_source("ROOTCTRL", root_text, flags, compiler_basename="R0AD9")
    candidate_obj = compile_source("ROOTOWNR", candidate_text, flags, compiler_basename="R0AD9")
    wrong_type_full_obj = compile_source("ROOTWRNG", wrong_type_text, flags, compiler_basename="R0AD9")
    control, control_view = object_view(control_obj)
    candidate, candidate_view = object_view(candidate_obj)
    wrong_type, wrong_type_view = object_view(wrong_type_full_obj)

    unchanged_fields = ("segments", "segment_byte_lengths", "segment_lengths", "segment_defs",
                        "groups", "publics", "local_publics", "fixups", "linker_fixups",
                        "external_names", "local_externals")
    unchanged = {field: control_view[field] == candidate_view[field] for field in unchanged_fields}
    scope_diffs = []
    if len(control.externals) != len(candidate.externals) or len(control.external_scopes) != len(candidate.external_scopes):
        raise RuntimeError("external scope table changed length")
    for name, before, after in zip(control.externals, control.external_scopes, candidate.external_scopes):
        if before != after:
            scope_diffs.append({"name": name, "before": before, "after": after})
    expected_scopes = [{"name": "_AntsEatenByLions", "before": "external", "after": "communal"},
                       {"name": "_InitialLions", "before": "external", "after": "communal"}]
    communal_rows = sorted((c["name"], c["length"]) for c in candidate.communals)
    expected_rows = sorted(EXPECTED_LENGTHS.items())
    delta_bytes = len(candidate_obj) - len(control_obj)
    if not all(unchanged.values()):
        raise RuntimeError(f"typed owner unexpectedly changed object fields: {unchanged}")
    if scope_diffs != expected_scopes or communal_rows != expected_rows:
        raise RuntimeError(f"typed owner OMF result mismatch: scopes={scope_diffs}, commons={communal_rows}, delta={delta_bytes}")
    if wrong_type_view["segments"] == control_view["segments"]:
        raise RuntimeError("wrong-type full-module control unexpectedly preserved all segment bytes")
    wrong_type_rows = sorted((c["name"], c["length"]) for c in wrong_type.communals)
    if wrong_type_rows != [("_InitialLions", 4)]:
        raise RuntimeError(f"wrong-type full-module control has unexpected communal rows: {wrong_type_rows}")

    source_inventory = source_use_inventory()
    aliases = address_aliases()
    runtime = compile_runtime_fixtures()
    report = {
        "schema": "simant-dos-farbss-lion-scalar-ownership-review-v1",
        "status": "RESEARCH_ONLY_NOT_ADMITTED",
        "scope": "Only AntsEatenByLions and InitialLions. Source-functional candidate is the already complete canonical root:0AD9 module. No historical COMDEF-producing object is asserted.",
        "owner_hypothesis": {
            "functional_owner": "root:0AD9 / src/root/m0AD9.c",
            "basis": "InitAntLions resets AntsEatenByLions, clamps count to 10, spawns that many lions, then assigns InitialLions=count; DoAntLions reads InitialLions for regeneration and increments AntsEatenByLions when a lion completes emergence.",
            "historical_COMDEF_TU_identity": "NOT_CLAIMED",
            "source_change_under_probe": "Only the two extern int far declarations become tentative int far definitions in a scratch full-module copy."
        },
        "initializer_and_regeneration": {
            "InitAntLions": "LionIndex=0; AntsEatenByLions=0; clamp count to 10; call AddRandAntLion count times; then InitialLions=count.",
            "DoAntLions_regeneration": "If no lions remain and InitialLions>0, SRand1(0x400)==0 calls AddRandAntLion. When a lion's emergence countdown ends, increment AntsEatenByLions; below 9 active lions, low nibble 0xF calls AddRandAntLion.",
            "all_known_call_sites": [
                {"source": "src/S18/m384C.c", "caller": "MakeHousePatch", "line": 65, "call": "InitAntLions(0)"},
                {"source": "src/S18/m384C.c", "caller": "MakeYardPatch", "line": 407, "call": "InitAntLions(SRand4() + 1)"}
            ]
        },
        "source_uses": source_inventory,
        "addresses_and_aliases": {
            "AntsEatenByLions": {"address": "50F6:0A08", "semantic_type": "int far", "save_rec": {"line": 995, "size": 2, "count": 1}, "same_address_registered_names": aliases["AntsEatenByLions"]["exact_base"], "interior_registered_names": aliases["AntsEatenByLions"]["interior"]},
            "InitialLions": {"address": "50F6:08EA", "semantic_type": "int far", "save_rec": {"line": 1066, "size": 2, "count": 1}, "same_address_registered_names": aliases["InitialLions"]["exact_base"], "interior_registered_names": aliases["InitialLions"]["interior"]},
            "alias_finding": "Each 2-byte registry extent contains only its semantic name; no exact-base numeric fd_ alias or interior alias was found. The similarly named fd_3D57_0A08 belongs to another segment and is unrelated."
        },
        "save_load_lifetime": {
            "table_owner": "S09:35F5 fd_4E4B_0000 SaveRec table; each scalar has exactly one {size=2,count=1,&scalar} row.",
            "pointer_escape": "Each address is stored in the static SaveRec table and later passed as p->data to generic read(fd, p->data, p->count*p->size) and write(fd, p->data, p->count*p->size). The data pointer is not used for arithmetic at either scalar.",
            "lifetime": "The pair lives in FAR_BSS between loads/saves; InitAntLions resets AntsEatenByLions and refreshes InitialLions on lion reinitialization; LoadGame overwrites both through the two-byte rows; SaveGame serializes both rows.",
            "limits": "Source flow is established, but the runtime fixture does not execute the actual game InitAntLions/LoadGame/SaveGame routines."
        },
        "manifest_module": {"key": "root:0AD9", "profile": module["profile"], "flags": flags,
                            "source_sha256": module["source_sha256"], "extent": module["extent"],
                            "full_TU": module.get("extent") is not None},
        "whole_module_compile_control": {
            "compiler_profile": module["profile"], "flags": flags,
            "control_source": "src/root/m0AD9.c (fresh copied compile)",
            "candidate_source": "ROOTOWNR.c (full module; two declarations changed)",
            "control_object": {"path": "build/workers/dos_lion_scalar_owners/ROOTCTRL.OBJ", "sha256": sha(control_obj), "bytes": len(control_obj)},
            "candidate_object": {"path": "build/workers/dos_lion_scalar_owners/ROOTOWNR.OBJ", "sha256": sha(candidate_obj), "bytes": len(candidate_obj)},
            "fresh_control_matches_manifest_source_hash": sha(ROOT_SOURCE.read_bytes()) == module["source_sha256"],
            "unchanged_OMF_fields": unchanged,
            "communal_rows": candidate.communals,
            "external_scope_differences": scope_diffs,
            "object_size_delta_bytes": delta_bytes,
            "all_emitted_segment_bytes_equal": unchanged["segments"],
            "segment_lengths_equal": unchanged["segment_lengths"],
            "segment_defs_and_groups_equal": unchanged["segment_defs"] and unchanged["groups"],
            "existing_publics_equal": unchanged["publics"],
            "fixups_equal": unchanged["fixups"],
            "ordered_linker_fixups_equal": unchanged["linker_fixups"],
            "interpretation": "At parsed-object level, the only symbol changes are the two named external-to-communal scope transitions and two 2-byte far COMDEF rows. Code/data LEDATA, segment definitions/lengths/groups, publics and both fixup views remain identical. This proves compiler-shape compatibility, not historical object identity."
        },
        "negative_controls": {
            "wrong_type_full_module": {"source_change": "InitialLions declared long far", "communal_rows": wrong_type.communals,
                                        "code_segment_bytes_equal": wrong_type_view["segments"] == control_view["segments"],
                                        "segment_lengths_equal": wrong_type_view["segment_lengths"] == control_view["segment_lengths"],
                                        "object_sha256": sha(wrong_type_full_obj)},
            "wrong_extent_owner": {"source_change": "AntsEatenByLions declared int far[2]", "communal_rows": runtime["owner_objects"]["wrong_extent"]["communals"],
                                    "runtime_control": "The SaveRec consumer rejects the 4+2 byte owner against its 2+2 byte source rows."},
            "initialized_owner": {"source_change": "Both typed far globals initialized to nonzero values", "communals": runtime["owner_objects"]["initialized"]["communals"],
                                  "publics": runtime["owner_objects"]["initialized"]["publics"],
                                  "runtime_control": "Zero-initialized word and byte consumers reject the initialized owner."},
            "wrong_SaveRec_extent": "The byte consumer's AntsEatenByLions SaveRec count is changed from 1 to 2; both linkers must report FAIL."
        },
        "runtime_probe": runtime,
        "inputs_reviewed": [file_pin(ROOT / "README.md"), file_pin(ROOT / "docs/codegen-rules.md"),
                            file_pin(ROOT / "docs/tu-evidence.md"), file_pin(ROOT_SOURCE),
                            file_pin(SAVE_SOURCE), file_pin(ROOT / "src/S18/m384C.c"),
                            file_pin(SYMBOLS_PATH), file_pin(MANIFEST_PATH)],
        "original_executable_bytes_copied_into_sources_or_probe_inputs": False,
        "ignored_build_objects_or_original_link_inputs_used": False,
        "canonical_files_or_production_link_inputs_changed": False
    }
    report["probe_script_sha256"] = sha(Path(__file__).read_bytes())
    (OUT / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"report": "build/workers/dos_lion_scalar_owners/report.json",
                      "delta_bytes": delta_bytes, "communal_rows": candidate.communals,
                      "runtime_cases": len(runtime["cases"]), "runtime_ok": runtime["expected_outcomes_pass"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
