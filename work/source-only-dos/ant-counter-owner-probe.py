"""Guarded source/storage and RTLink controls for two FAR_BSS counters and a timer.

The source audit uses the 127 canonical TUs plus the 29 strict-index effective
whole modules (including the corrected DrawBalloons source). Runtime objects are
freshly compiled test fixtures; no game function is stubbed or linked.
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

ROOT = next((p for p in Path(__file__).resolve().parents if (p / 'layout/manifest.json').is_file()), None)
if ROOT is None:
    raise RuntimeError('repository root not found')
OUT = ROOT / 'build/workers/dos_ant_counter_owners'
OUT.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(ROOT / "tools"))
import compiler
import modules
import source_only_dos as dos
from omf import OmfReader

INTAKE_PATH = ROOT / "work/source-only-dos/compile-and-intake-v1.json"
STATIC_INDEX_PATH = ROOT / "work/source-only-dos/static-completeness/index-v1.json"
MANIFEST_PATH = ROOT / "layout/manifest.json"
SYMBOLS_PATH = ROOT / "layout/symbols.json"
SAVE_SOURCE = ROOT / "src/S09/m35F5.c"
PROVIDER_PATH = ROOT / 'work/source-only-dos/providers/ant-counters-timer.c'
ZERO_RECEIPT_PATH = ROOT / "build/workers/dos_lion_array_owners/original-farbss-zero.json"
ZERO_CHECKER_PATH = ROOT / "build/workers/dos_lion_array_owners/check-original-farbss-zero.py"

COUNTERS = ("BAntsEaten", "RAntsEaten")
TIMER = "fd_50F6_0620"
STATE = "fd_50F6_0F10"
TARGETS = COUNTERS + (TIMER,)
SUPPORT = ("ClearHistory", "InitAntLions", "DoAntLions", "YellowDeath",
           "SpiderScan", "DrawCurBalloons", "DoAntSim", "LoadGame", "SaveGame",
           "TickCount", "SRand32", STATE)
PROVIDER_FLAGS = ["/AL", "/Os", "/Gs"]
PROVIDER_SOURCE = PROVIDER_PATH.read_text(encoding='ascii')


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def pin(path: Path) -> dict:
    raw = path.read_bytes()
    try:
        shown = path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        shown = str(path.resolve()).replace("\\", "/")
    return {"path": shown, "sha256": sha(raw), "size": len(raw)}


def repo_path(name: str) -> Path:
    return ROOT / name.replace("\\", "/")


def checked_pin(row: dict, label: str) -> dict:
    path = repo_path(row["path"])
    actual = pin(path)
    if actual["sha256"] != row["sha256"] or actual["size"] != row["size"]:
        raise RuntimeError(f"{label} pin changed: {row['path']}")
    return actual


def strict_behavior_sources() -> tuple[list[dict], list[dict]]:
    index = json.loads(STATIC_INDEX_PATH.read_text(encoding="utf-8"))
    if index.get("schema") != "simant-dos-strict-static-index-v1" or len(index.get("entries", {})) != 29:
        raise RuntimeError("strict static index is not the expected 29-entry source set")
    receipts = [pin(STATIC_INDEX_PATH)]
    sources = []
    for function, ref in sorted(index["entries"].items()):
        rp = checked_pin({"path": ref["path"], "sha256": ref["sha256"], "size": ref["size"]},
                         "strict source receipt")
        receipts.append(rp)
        receipt = json.loads(repo_path(ref["path"]).read_text(encoding="utf-8"))
        source = receipt.get("registered_source", {})
        # DrawBalloons' registered source is superseded; the reviewed audit source
        # is the current effective whole-module implementation.
        if function == "DrawBalloons":
            source = receipt.get("audit", {}).get("source", {})
        if not source.get("whole_module") or not source.get("path") or not source.get("sha256"):
            raise RuntimeError(f"{function} lacks a pinned effective whole module")
        sp = pin(repo_path(source["path"]))
        if sp["sha256"] != source["sha256"]:
            raise RuntimeError(f"effective source hash differs from receipt for {function}")
        sources.append({"path": sp["path"], "sha256": sp["sha256"], "size": sp["size"],
                        "module": source.get("module"), "function": function,
                        "role": ("corrected effective whole module" if function == "DrawBalloons"
                                 else "registered effective whole module")})
    return sources, receipts


def all_source_rows(intake: dict) -> tuple[list[dict], list[dict], list[dict]]:
    if len(intake.get("translation_units", [])) != 127:
        raise RuntimeError("canonical translation-unit inventory changed from 127")
    canonical = [checked_pin(tu["source"], "canonical source") | {"module": tu["module"]}
                 for tu in intake["translation_units"]]
    effective, receipts = strict_behavior_sources()
    return canonical, effective, receipts


def _classify(name: str, line: str) -> str:
    if re.search(r"(?:\+\+|--)\s*" + re.escape(name) + r"\b|\b" + re.escape(name) + r"\s*(?:\+\+|--)", line):
        return "write_increment"
    if re.search(r"\b" + re.escape(name) + r"\s*(?:[+*/%-]?=)(?!=)", line):
        return "write_assignment"
    if re.search(r"(?<!&)\&(?!&)\s*" + re.escape(name) + r"\b", line):
        return "address_escape"
    return "read_or_expression"


def scan_sources(canonical: list[dict], effective: list[dict]) -> dict:
    token = re.compile(r"\b(" + "|".join(map(re.escape, TARGETS + SUPPORT)) + r")\b")
    sets = {"canonical_127": canonical, "effective_body_29": effective}
    hits = {name: [] for name in TARGETS + SUPPORT}
    set_report = {}
    for label, rows in sets.items():
        files = []
        for row in rows:
            path = repo_path(row["path"])
            text = path.read_text(encoding="latin1")
            row_hits = []
            for number, line in enumerate(text.splitlines(), 1):
                found = sorted(set(token.findall(line)))
                if not found:
                    continue
                context = {"line": number, "text": line.strip(), "names": found}
                row_hits.append(context)
                for name in found:
                    hits[name].append({"set": label, "path": row["path"],
                                       "line": number, "text": line.strip(),
                                       "access": _classify(name, line) if name in TARGETS else "source_context"})
            if row_hits:
                files.append({"path": row["path"], "sha256": row["sha256"], "hits": row_hits})
        set_report[label] = {"scanned": len(rows), "files_with_hits": files}
    expected_canonical = {
        "BAntsEaten": {"src/S09/m35F5.c", "src/S22/m39C7.c", "src/S24/m39C7.c",
                       "src/root/m0AD9.c", "src/root/m0CDB.c"},
        "RAntsEaten": {"src/S09/m35F5.c", "src/S24/m39C7.c",
                       "src/root/m0AD9.c", "src/root/m0CDB.c"},
        "fd_50F6_0620": {"src/root/m0250.c"},
    }
    for name, expected in expected_canonical.items():
        actual = {h["path"] for h in hits[name] if h["set"] == "canonical_127"}
        if actual != expected:
            raise RuntimeError(f"canonical consumer inventory for {name} changed: {actual}")
    paths = [r["path"] for r in canonical + effective]
    return {"set_counts": {k: len(v) for k, v in sets.items()},
            "unique_source_paths": len(set(paths)), "sets": set_report,
            "target_hits": {name: hits[name] for name in TARGETS},
            "support_hits": {name: hits[name] for name in SUPPORT},
            "canonical_source_pins": canonical, "effective_source_pins": effective}


def save_record_evidence() -> dict:
    text = SAVE_SOURCE.read_text(encoding="latin1")
    rows = {}
    for name in COUNTERS + (TIMER,):
        rx = re.compile(r"\{\s*(\d+)\s*,\s*(\d+)\s*,\s*\(void\s+far\s*\*\)\s*&\s*" +
                        re.escape(name) + r"\s*\}")
        matches = [{"size": int(m.group(1)), "count": int(m.group(2)),
                    "bytes": int(m.group(1)) * int(m.group(2)),
                    "line": text[:m.start()].count("\n") + 1} for m in rx.finditer(text)]
        rows[name] = matches
    if (len(rows["BAntsEaten"]) != 1 or rows["BAntsEaten"][0]["size"] != 4 or
            rows["BAntsEaten"][0]["count"] != 1):
        raise RuntimeError("BAntsEaten SaveRec row is not exactly {4,1}")
    if len(rows["RAntsEaten"]) != 1 or rows["RAntsEaten"][0]["size"] != 4 or rows["RAntsEaten"][0]["count"] != 1:
        raise RuntimeError("RAntsEaten SaveRec row is not exactly {4,1}")
    if rows[TIMER]:
        raise RuntimeError("timer unexpectedly appears in the SaveRec source table")
    source_lines = text.splitlines()
    return {"path": pin(SAVE_SOURCE), "target_rows": rows,
            "generic_io": {
                "load_read": next({"line": i, "text": line.strip()} for i, line in enumerate(source_lines, 1)
                                  if "read(fd, p->data" in line),
                "save_write": next({"line": i, "text": line.strip()} for i, line in enumerate(source_lines, 1)
                                   if "write(fd, p->data" in line),
                "byte_count": "p->count * p->size",
                "field_validation_in_table_loop": False,
                "meaning": "LoadGame reads raw bytes through each SaveRec pointer; SaveGame writes the same size*count byte span."}}


def alias_evidence() -> dict:
    symbols = json.loads(SYMBOLS_PATH.read_text(encoding="utf-8"))["data"]
    result = {}
    for name in TARGETS:
        row = symbols[name]
        segment, offset = row["seg"], row["off"]
        exact = sorted(n for n, value in symbols.items()
                       if value.get("seg") == segment and value.get("off") == offset)
        inside = sorted((n, value["off"] - offset) for n, value in symbols.items()
                        if value.get("seg") == segment and offset < value.get("off", -1) < offset + 4)
        boundary = sorted(n for n, value in symbols.items()
                          if value.get("seg") == segment and value.get("off") == offset + 4)
        if exact != [name] or inside:
            raise RuntimeError(f"same-base or interior registry alias for {name}: {exact}/{inside}")
        result[name] = {"segment": segment, "offset": offset,
                        "historical_address": f"{segment:04X}:{offset:04X}",
                        "source_extent_bytes": 4, "exact_base_names": exact,
                        "registered_names_inside_source_extent": inside,
                        "names_at_extent_boundary_not_used_as_extent_evidence": boundary}
    return result


def source_lifetime_facts(inventory: dict) -> dict:
    root_text = (ROOT / "src/root/m0AD9.c").read_text(encoding="latin1")
    spider_text = (ROOT / "src/S22/m39C7.c").read_text(encoding="latin1")
    history_text = (ROOT / "src/S24/m39C7.c").read_text(encoding="latin1")
    sim_text = (ROOT / "src/root/m0894.c").read_text(encoding="latin1")
    balloon_text = (ROOT / "src/root/m0250.c").read_text(encoding="latin1")
    save_text = SAVE_SOURCE.read_text(encoding="latin1")
    def matching(text: str, pattern: str) -> list[dict]:
        return [{"line": i, "text": line.strip()} for i, line in enumerate(text.splitlines(), 1)
                if re.search(pattern, line)]
    source_callers = []
    for name in (r"ClearHistory", r"InitAntLions", r"DrawCurBalloons"):
        found = []
        for label in ("canonical_127", "effective_body_29"):
            for row in inventory["sets"][label]["files_with_hits"]:
                for hit in row["hits"]:
                    if name in hit["names"]:
                        found.append({"set": label, "path": row["path"], **hit})
        source_callers.append({"name_pattern": name, "occurrences": found})
    return {
        "BAntsEaten": {
            "declared_type": "signed long far (MSC 6.00: 32-bit long)",
            "writes": "DoAntLions increments when the eaten ant is black; SpiderScan increments on black-ant eating; YellowDeath increments for its two ant death causes; ClearHistory assigns zero.",
            "read": "HistUpdate stores (int)BAntsEaten in the history series; SaveRec takes its address for raw persistence.",
            "reset_fact": "ClearHistory assigns zero unconditionally. The exact-name scan misses its o24_39C7_01B8 alias: registry/code-address joins establish calls in RandWorld and RandYard (src/S08/m35F5.c:359,378). Raw SaveRec load can overwrite the reset counters afterward; no universal reset schedule is inferred.",
            "persistence": "One 4-byte SaveRec row. Generic LoadGame can replace it with any 32-bit byte pattern without range checks."},
        "RAntsEaten": {
            "declared_type": "signed long far (MSC 6.00: 32-bit long)",
            "writes": "DoAntLions increments for red ants; SpiderScan increments on red-ant eating; ClearHistory assigns zero.",
            "read": "SaveRec takes its address for raw persistence; no additional canonical value read was found in the 156-source scan.",
            "reset_fact": "ClearHistory assigns zero unconditionally. The exact-name scan misses its o24_39C7_01B8 alias: registry/code-address joins establish calls in RandWorld and RandYard (src/S08/m35F5.c:359,378). Raw SaveRec load can overwrite the reset counters afterward; no universal reset schedule is inferred.",
            "persistence": "One 4-byte SaveRec row. Generic LoadGame can replace it with any 32-bit byte pattern without range checks."},
        TIMER: {
            "declared_type": "signed long far (MSC 6.00: 32-bit long)",
            "writes": "DrawCurBalloons assigns zero when the balloon state transitions from fd_50F6_0F10==0 to an eligible active state, then schedules TickCount()+SRand32()+180.",
            "reads": "The active-state branch compares fd_50F6_0620 < TickCount() before rescheduling; no index arithmetic or source aliases escape.",
            "save_table": "No SaveRec row exists for this timer, so the reviewed game save/load table does not overwrite it.",
            "lifetime": "DoAntSim clears fd_50F6_0F10 in its mode-reset branch without clearing the timer. DrawCurBalloons tests the state before reading the timer and resets the timer to zero on the next eligible activation before the timer comparison. Initial FAR_BSS zero-fill is separate startup evidence."},
        "source_reset_write_lines": {
            "InitAntLions_counter_resets": matching(root_text, r"AntsEatenByLions\s*=\s*0"),
            "ClearHistory_counter_resets": matching(history_text, r"(?:BAntsEaten|RAntsEaten)\s*=\s*0"),
            "DoAntSim_balloon_state_reset": matching(sim_text, rf"{STATE}\s*=\s*0"),
            "balloon_timer_state_reset_and_schedule": matching(balloon_text, rf"{TIMER}\s*(?:=|<)"),
            "InitAntLions_calls": matching((ROOT / "src/S18/m384C.c").read_text(encoding="latin1"), r"InitAntLions\s*\("),
            "all_direct_reset_call_candidates": source_callers,
            "SaveRec_load_save_lines": save_record_evidence()["generic_io"]}
    }


def compile_fixture(name: str, source: str, flags: list[str], profile: str = "msc600ax") -> bytes:
    if len(name) > 8:
        raise RuntimeError("DOS compiler basename must fit 8.3")
    (OUT / (name + ".c")).write_text(source, encoding="ascii", newline="\n")
    result = compiler.compile_c(source, profile, flags, basename=name)
    if not result.ok or result.obj is None:
        (OUT / (name + ".compile.log")).write_text(result.log, encoding="latin1")
        raise RuntimeError(f"{name} compile failed: {result.log[-1800:]}")
    raw = bytes(result.obj)
    (OUT / (name + ".OBJ")).write_bytes(raw)
    return raw


def omf_details(raw: bytes) -> tuple[OmfReader, dict]:
    omf = OmfReader(communals=True).read(raw)
    nonempty = {name: len(data) for name, data in omf.segments.items() if data}
    debug = {name: len(data) for name, data in omf.segments.items()
             if name.startswith("$$") and data}
    return omf, {"object_sha256": sha(raw), "object_bytes": len(raw),
                 "communal_rows": omf.communals, "nonempty_segments": nonempty,
                 "segment_lengths": omf.segment_lengths,
                 "public_count": len(omf.publics), "local_public_count": len(omf.local_publics),
                 "fixup_count": len(omf.fixups), "linker_fixup_count": len(omf.linker_fixups),
                 "external_names": omf.externals, "external_scopes": omf.external_scopes,
                 "debug_segments": debug}


def canonical_consumer_type_controls(manifest: dict) -> dict:
    specs = [("root:0AD9", "A0BASE", "A0SIGN", "A0WID"),
             ("root:0CDB", "C0BASE", "C0SIGN", "C0WID"),
             ("S22:39C7", "S2BASE", "S2SIGN", "S2WID"),
             ("S24:39C7", "S4BASE", "S4SIGN", "S4WID"),
             ("root:0250", "R0BASE", "R0SIGN", "R0WID")]
    results = {}
    for module_key, base_name, unsigned_name, width_name in specs:
        module = manifest["modules"][module_key]
        source_path = ROOT / module["source"]
        original = source_path.read_text(encoding="latin1")
        targets = [TIMER] if module_key == "root:0250" else [n for n in COUNTERS if f"extern long far {n};" in original]
        if not targets:
            continue
        def variant(ctype: str) -> str:
            text = original
            for name in targets:
                old = f"extern long far {name};"
                new = f"extern {ctype} far {name};"
                if text.count(old) != 1:
                    raise RuntimeError(f"expected one declaration {old!r} in {module_key}")
                text = text.replace(old, new, 1)
            return text
        outputs = {}
        for label, basename, source in (("signed_long", base_name, original),
                                        ("unsigned_long", unsigned_name, variant("unsigned long")),
                                        ("int_width_negative", width_name, variant("int"))):
            obj = compile_fixture(basename, source, list(module["flags"]), module["profile"])
            omf = OmfReader(communals=True).read(obj)
            code_rows = sorted((row for row in omf.segment_defs
                                if str(row.get("class", "")).upper() == "CODE"),
                               key=lambda row: row["index"])
            image = [{"length": row["length"],
                      "sha256": sha(omf.segments.get(row["name"], b""))}
                     for row in code_rows]
            outputs[label] = {"source_sha256": sha(source.encode("latin1")),
                              "object_sha256": sha(obj), "code_segment_sha256": image,
                              "non_debug_code_data_changed_from_base": False if label == "signed_long" else None}
        base = outputs["signed_long"]["code_segment_sha256"]
        for label in ("unsigned_long", "int_width_negative"):
            outputs[label]["non_debug_code_data_changed_from_base"] = outputs[label]["code_segment_sha256"] != base
        results[module_key] = {"source": pin(source_path), "profile": module["profile"],
                               "flags": list(module["flags"]), "target_declarations": targets,
                               "variants": outputs,
                               "interpretation": ("Source compiler contrast only; it is not a historical object or byte identity claim.")}
    return results


STARTUP_CONSUMER = r'''extern long far BAntsEaten;
extern long far RAntsEaten;
extern long far fd_50F6_0620;
extern int far puts(char far *text);
int main(void)
{
    if (sizeof(BAntsEaten) != 4 || sizeof(RAntsEaten) != 4 ||
        sizeof(fd_50F6_0620) != 4 || BAntsEaten != 0 ||
        RAntsEaten != 0 || fd_50F6_0620 != 0) { puts("FAIL"); return 0; }
    BAntsEaten = 0x12345678L;
    RAntsEaten = 0x23456789L;
    fd_50F6_0620 = 0x3456789aL;
    if (BAntsEaten != 0x12345678L || RAntsEaten != 0x23456789L ||
        fd_50F6_0620 != 0x3456789aL) { puts("FAIL"); return 0; }
    BAntsEaten++; RAntsEaten++; fd_50F6_0620++;
    if (BAntsEaten != 0x12345679L || RAntsEaten != 0x2345678aL ||
        fd_50F6_0620 != 0x3456789bL) { puts("FAIL"); return 0; }
    puts("PASS"); return 0;
}
'''

BYTE_SAVEREC_CONSUMER = r'''extern long far BAntsEaten;
extern long far RAntsEaten;
extern long far fd_50F6_0620;
extern int far puts(char far *text);
struct SaveRec { int size; int count; void far *data; };
struct SaveRec far TestSaveRows[2] = {
    { 4, 1, (void far *)&BAntsEaten },
    { 4, 1, (void far *)&RAntsEaten }
};
int main(void)
{
    unsigned char far *b;
    unsigned char far *r;
    unsigned char far *t;
    b = (unsigned char far *)TestSaveRows[0].data;
    r = (unsigned char far *)TestSaveRows[1].data;
    t = (unsigned char far *)&fd_50F6_0620;
    if (TestSaveRows[0].size != 4 || TestSaveRows[0].count != 1 ||
        TestSaveRows[0].data != (void far *)&BAntsEaten ||
        TestSaveRows[1].size != 4 || TestSaveRows[1].count != 1 ||
        TestSaveRows[1].data != (void far *)&RAntsEaten ||
        BAntsEaten != 0 || RAntsEaten != 0 || fd_50F6_0620 != 0 ||
        b[0] || b[1] || b[2] || b[3] || r[0] || r[1] || r[2] || r[3] ||
        t[0] || t[1] || t[2] || t[3]) { puts("FAIL"); return 0; }
    b[0] = 0x78; b[1] = 0x56; b[2] = 0x34; b[3] = 0x12;
    r[0] = 0x89; r[1] = 0x67; r[2] = 0x45; r[3] = 0x23;
    t[0] = 0x9a; t[1] = 0x78; t[2] = 0x56; t[3] = 0x34;
    if (BAntsEaten != 0x12345678L || RAntsEaten != 0x23456789L ||
        fd_50F6_0620 != 0x3456789aL) { puts("FAIL"); return 0; }
    BAntsEaten = 0x10203040L;
    if (b[0] != 0x40 || b[1] != 0x30 || b[2] != 0x20 || b[3] != 0x10) {
        puts("FAIL"); return 0;
    }
    puts("PASS"); return 0;
}
'''

SIGNED_CONSUMER = r'''extern long far BAntsEaten;
extern long far RAntsEaten;
extern long far fd_50F6_0620;
extern int far puts(char far *text);
int main(void)
{
    unsigned char far *b = (unsigned char far *)&BAntsEaten;
    unsigned char far *r = (unsigned char far *)&RAntsEaten;
    unsigned char far *t = (unsigned char far *)&fd_50F6_0620;
    b[0]=0xff; b[1]=0xff; b[2]=0xff; b[3]=0xff;
    r[0]=0; r[1]=0; r[2]=0; r[3]=0x80;
    t[0]=0xff; t[1]=0xff; t[2]=0xff; t[3]=0xff;
    if (BAntsEaten < 0L && RAntsEaten < 0L && fd_50F6_0620 < 0L) {
        puts("PASS"); return 0;
    }
    puts("FAIL"); return 0;
}
'''

UNSIGNED_CONSUMER = SIGNED_CONSUMER.replace("extern long far BAntsEaten;", "extern unsigned long far BAntsEaten;")
UNSIGNED_CONSUMER = UNSIGNED_CONSUMER.replace("extern long far RAntsEaten;", "extern unsigned long far RAntsEaten;")
UNSIGNED_CONSUMER = UNSIGNED_CONSUMER.replace("extern long far fd_50F6_0620;", "extern unsigned long far fd_50F6_0620;")

WRONG_WIDTH_CONSUMER = r'''extern int far BAntsEaten;
extern int far RAntsEaten;
extern int far fd_50F6_0620;
extern int far puts(char far *text);
int main(void)
{
    if (sizeof(BAntsEaten) == 4 && sizeof(RAntsEaten) == 4 &&
        sizeof(fd_50F6_0620) == 4) { puts("PASS"); return 0; }
    puts("FAIL"); return 0;
}
'''


def wrong_saverec_consumer(size: int, count: int) -> str:
    return f'''extern long far BAntsEaten;\nextern long far RAntsEaten;\nextern int far puts(char far *text);\nstruct SaveRec {{ int size; int count; void far *data; }};\nstruct SaveRec far TestSaveRows[2] = {{\n    {{ {size}, {count}, (void far *)&BAntsEaten }},\n    {{ 4, 1, (void far *)&RAntsEaten }}\n}};\nint main(void)\n{{\n    if (TestSaveRows[0].size == 4 && TestSaveRows[0].count == 1 &&\n        TestSaveRows[1].size == 4 && TestSaveRows[1].count == 1) {{ puts("PASS"); return 0; }}\n    puts("FAIL"); return 0;\n}}\n'''


BAD_WIDTH_OWNER = "int far BAntsEaten;\nlong far RAntsEaten;\nlong far fd_50F6_0620;\nlong far AntOwnerFence;\n"
BAD_WIDTH_OWNER_CONSUMER = r'''extern long far BAntsEaten;
extern long far RAntsEaten;
extern long far fd_50F6_0620;
extern long far AntOwnerFence;
extern int far puts(char far *text);
int main(void)
{
    if (BAntsEaten || RAntsEaten || fd_50F6_0620 || AntOwnerFence) {
        puts("FAIL"); return 0;
    }
    RAntsEaten = 0x24681357L;
    AntOwnerFence = 0x13572468L;
    BAntsEaten = 0x12345678L;
    if (BAntsEaten != 0x12345678L || RAntsEaten != 0x24681357L ||
        AntOwnerFence != 0x13572468L) { puts("FAIL"); return 0; }
    puts("PASS"); return 0;
}
'''


def compile_runtime_objects() -> tuple[dict, dict]:
    required = list(compiler.verify_profile("msc600ax").get("required_flags", []))
    if required != ["/EM"]:
        raise RuntimeError(f"unexpected 6.00AX required flags: {required}")
    flags = list(PROVIDER_FLAGS)
    sources = {
        "owner": PROVIDER_SOURCE,
        "init_owner": "long far BAntsEaten=1L;\nlong far RAntsEaten=2L;\nlong far fd_50F6_0620=3L;\n",
        "bad_width_owner": BAD_WIDTH_OWNER,
        "typed": STARTUP_CONSUMER,
        "bytes": BYTE_SAVEREC_CONSUMER,
        "signed": SIGNED_CONSUMER,
        "unsigned": UNSIGNED_CONSUMER,
        "bad_width_view": WRONG_WIDTH_CONSUMER,
        "bad_save_size": wrong_saverec_consumer(2, 1),
        "bad_save_count": wrong_saverec_consumer(4, 2),
        "bad_width_probe": BAD_WIDTH_OWNER_CONSUMER,
    }
    names = {"owner": "ANTOWN", "init_owner": "ANTINIT", "bad_width_owner": "ANTWID",
             "typed": "ANTTYPE", "bytes": "ANTBYTE", "signed": "ANTSIGN",
             "unsigned": "ANTUNSG", "bad_width_view": "ANTSMAL",
             "bad_save_size": "ANTSIZE", "bad_save_count": "ANTCNT",
             "bad_width_probe": "ANTWPRB"}
    objects = {key: compile_fixture(names[key], source, flags)
               for key, source in sources.items()}
    owner_omf, owner_facts = omf_details(objects["owner"])
    expected = {"_BAntsEaten": ("far", 4, 4, 1),
                "_RAntsEaten": ("far", 4, 4, 1),
                "_fd_50F6_0620": ("far", 4, 4, 1)}
    measured = {x["name"]: (x["kind"], x["length"], x["count"], x["element_size"])
                for x in owner_omf.communals}
    if measured != expected or len(owner_omf.communals) != 3:
        raise RuntimeError(f"typed owner COMDEF rows differ: {owner_omf.communals}")
    if (owner_omf.segments or owner_omf.publics or owner_omf.local_publics or
            owner_omf.fixups or owner_omf.linker_fixups):
        raise RuntimeError("data-only tentative owner unexpectedly emits payload/code/publics/fixups")
    if (set(owner_omf.externals) != set(expected) or
            any(scope != "communal" for scope in owner_omf.external_scopes)):
        raise RuntimeError("provider external scopes are not exactly the three far communals")
    bad_omf, bad_view = omf_details(objects["bad_width_owner"])
    wrong_width = {x["name"]: (x["kind"], x["length"], x["count"], x["element_size"])
                   for x in bad_omf.communals}
    if wrong_width.get("_BAntsEaten") != ("far", 2, 2, 1):
        raise RuntimeError(f"wrong-width owner does not produce a measured 2-byte counter: {bad_omf.communals}")
    signed_same_shape, unsigned_shape = measured, {
        x["name"]: (x["kind"], x["length"], x["count"], x["element_size"])
        for x in OmfReader(communals=True).read(compile_fixture("ANTUNOWN",
            "unsigned long far BAntsEaten;\nunsigned long far RAntsEaten;\nunsigned long far fd_50F6_0620;\n",
            flags)).communals}
    if signed_same_shape != unsigned_shape:
        raise RuntimeError("signed and unsigned 32-bit tentative storage do not have matching OMF shape")
    init_omf = OmfReader(communals=True).read(objects["init_owner"])
    init_names = {p["name"] for p in init_omf.publics}
    if {c["name"] for c in owner_omf.communals} & {c["name"] for c in init_omf.communals}:
        raise RuntimeError("initialized owner unexpectedly retains communal definitions")
    compiler_facts = {"profile": "msc600ax", "flags": flags,
                      "required_flags": required, "effective_flags": flags + required,
                      "no_debug_switch": True,
                      "measured_owner_facts": owner_facts,
                      "wrong_width_owner_facts": bad_view,
                      "initialized_owner_publics": sorted(init_names),
                      "signed_unsigned_communal_shape_equal": True,
                      "unsigned_owner_shape": unsigned_shape}
    cases = [
        ("typed_owner_startup_roundtrip", "PASS", "typed", "owner"),
        ("SaveRec_four_byte_view", "PASS", "bytes", "owner"),
        ("signed_long_semantics", "PASS", "signed", "owner"),
        ("unsigned_long_view_negative", "FAIL", "unsigned", "owner"),
        ("wrong_two_byte_consumer_view", "FAIL", "bad_width_view", "owner"),
        ("wrong_SaveRec_size", "FAIL", "bad_save_size", "owner"),
        ("wrong_SaveRec_count", "FAIL", "bad_save_count", "owner"),
        ("initialized_owner_startup_negative", "FAIL", "typed", "init_owner"),
    ]
    return {"objects": objects, "cases": cases, "flags": flags,
            "effective_flags": flags + required}, compiler_facts


def run_link_case(profile: str, case: str, expected: str, consumer: bytes, owner: bytes,
                  runtime_rows: list, linker: dict, runner: dict, tool_dir: Path) -> dict:
    directory = OUT / profile / case
    directory.mkdir(parents=True, exist_ok=True)
    for name in ("PROBE.EXE", "PROBE.MAP", "RUN.LOG", "LINK.LOG"):
        (directory / name).unlink(missing_ok=True)
    (directory / "CRT.OBJ").write_bytes(consumer)
    (directory / "OWNER.OBJ").write_bytes(owner)
    for row in runtime_rows:
        shutil.copyfile(row["path"], directory / Path(row["path"]).name.upper())
    script = ("OUTPUT PROBE\r\nMAP = PROBE S,N,A,L\r\nNODEFLIB\r\n"
              "LIBRARY LLIBCR, LIBH\r\nFILE CRT\r\nBEGINAREA\r\nSECTION FILE OWNER\r\nENDAREA\r\n")
    (directory / "PROBE.LNK").write_bytes(script.encode("ascii"))
    (directory / "RTLINK.CFG").write_bytes(b"SYNTAX = FREEFORMAT\r\n")
    (directory / "RUN.BAT").write_bytes((
        f"@echo off\r\nD:\\{linker['executable']} @PROBE.LNK < NUL > LINK.LOG\r\n"
        "PROBE.EXE > RUN.LOG\r\n").encode("ascii"))
    lines = []
    for section, settings in runner["conf"].items():
        lines.append("[" + section + "]")
        lines += [f"{key}={value}" for key, value in settings.items()]
    lines += ["[autoexec]", f'mount c "{directory}"', f'mount d "{tool_dir}" -ro',
              "c:", "call RUN.BAT", "exit"]
    conf = directory / "dosbox.conf"
    conf.write_text("\n".join(lines) + "\n", encoding="ascii")
    env = os.environ.copy()
    env.update(SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy")
    timeout = False
    try:
        run = subprocess.run([runner["path"], "-conf", str(conf), "-fastlaunch", "-exit", "-nomenu"],
                             cwd=directory, env=env, stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL, timeout=60,
                             creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    except subprocess.TimeoutExpired:
        timeout = True
        run = type("Timeout", (), {"returncode": -1})()
    runlog = directory / "RUN.LOG"
    actual = runlog.read_text(encoding="latin1").strip() if runlog.exists() else "NO RUN.LOG"
    linklog = directory / "LINK.LOG"
    link_text = linklog.read_text(encoding="latin1", errors="replace") if linklog.exists() else ""
    artifacts = []
    for name in ("PROBE.EXE", "PROBE.MAP", "RUN.LOG", "LINK.LOG", "PROBE.LNK"):
        p = directory / name
        if p.is_file():
            artifacts.append(pin(p))
    result = {"linker": profile, "case": case, "expected": expected, "actual": actual,
              "emulator_exit": run.returncode, "timed_out": timeout,
              "passed": actual == expected and run.returncode == 0 and not timeout,
              "link_log_tail": link_text[-600:], "artifacts": artifacts}
    print(profile, case, actual, flush=True)
    return result


def run_runtime(compiled: dict) -> dict:
    tc = compiler.toolchain()
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    runtime_rows = list(manifest["runtime"]["libraries"].values())
    runner = tc["runners"]["dosbox-x"]
    cases = []
    for profile in ("rtlink400", "rtlink610"):
        linker = tc["linkers"][profile]
        tool_dir = compiler.pinned_tree(linker)
        for case, expected, consumer_key, owner_key in compiled["cases"]:
            cases.append(run_link_case(profile, case, expected,
                                       compiled["objects"][consumer_key],
                                       compiled["objects"][owner_key], runtime_rows,
                                       linker, runner, tool_dir))
    # This deliberately under-sized owner is retained as a non-gating
    # diagnostic: RTLink permits the consumer to read/write beyond a 2-byte
    # FAR common, so runtime output cannot prove an object extent. OMF shape
    # and the typed-consumer control are the extent evidence instead.
    diagnostics = []
    for profile in ("rtlink400", "rtlink610"):
        linker = tc["linkers"][profile]
        tool_dir = compiler.pinned_tree(linker)
        row = run_link_case(profile, "wrong_two_byte_owner_extent_diagnostic", "FAIL",
                            compiled["objects"]["bad_width_probe"],
                            compiled["objects"]["bad_width_owner"], runtime_rows,
                            linker, runner, tool_dir)
        row["gating"] = False
        row["interpretation"] = ("Observed runtime PASS despite a measured 2-byte BAntsEaten COMDEF; "
                                 "this probe cannot detect a far-memory overrun and is not extent evidence.")
        diagnostics.append(row)
    if len(cases) != 16 or not all(x["passed"] for x in cases):
        raise RuntimeError("RTLink startup/type/byte/signedness controls did not meet expected outcomes")
    all_runtime_pins = [pin(Path(row["path"])) for row in runtime_rows]
    all_runtime_pins.append(pin(Path(runner["path"])))
    linker_files = {}
    for name in ("rtlink400", "rtlink610"):
        linker = tc["linkers"][name]
        linker_files[name] = {"executable": linker["executable"],
                              "status": linker.get("status"),
                              "files": [pin(Path(linker["directory"]) / rel)
                                        for rel in linker["files"]]}
    return {"cases": cases, "non_gating_extent_diagnostics": diagnostics,
            "case_counts": {
                name: {"pass_count": sum(x["expected"] == "PASS" for x in cases if x["linker"] == name),
                       "fail_count": sum(x["expected"] == "FAIL" for x in cases if x["linker"] == name),
                       "actuals_match": all(x["actual"] == x["expected"] and x["passed"]
                                            for x in cases if x["linker"] == name)}
                for name in ("rtlink400", "rtlink610")},
            "libraries_and_runner": all_runtime_pins,
            "linkers": linker_files,
            "runner_configuration": runner["conf"],
            "no_game_stubs_or_full_game_link": True}


def input_pins(canonical: list[dict], effective: list[dict], receipts: list[dict],
               runtime: dict) -> list[dict]:
    rows = [pin(ROOT / path) for path in (
        "README.md", "docs/codegen-rules.md", "docs/tu-evidence.md",
        "layout/manifest.json", "layout/toolchain.json", "layout/symbols.json",
        "layout/oracle.lock.json", "work/source-only-dos/compile-and-intake-v1.json",
        "work/source-only-dos/static-completeness/index-v1.json",
        "src/root/m0AD9.c", "src/root/m0CDB.c", "src/root/m0250.c",
        "src/root/m0894.c", "src/S09/m35F5.c", "src/S18/m384C.c",
        "src/S22/m39C7.c", "src/S24/m39C7.c",
        "tools/compiler.py", "tools/omf.py", "tools/modules.py",
        "tools/source_only_dos.py", "work/data/s27_map.md", "tools/farbss.py",
        "build/workers/dos_lion_array_owners/original-farbss-zero.json",
        "build/workers/dos_lion_array_owners/check-original-farbss-zero.py")]
    rows.extend(canonical)
    rows.extend(effective)
    rows.extend(receipts)
    tc = compiler.toolchain()
    prof = compiler.verify_profile("msc600ax")
    for rel, digest in prof["files"].items():
        p = Path(prof["directory"]) / rel
        row = pin(p)
        if row["sha256"] != digest:
            raise RuntimeError(f"compiler tool pin mismatch: {p}")
        rows.append(row)
    rows.extend(runtime["libraries_and_runner"])
    for linker in runtime["linkers"].values():
        rows.extend(linker["files"])
    rows.append(pin(PROVIDER_PATH))
    # Keep each path once, and refuse conflicting hashes in the source/tool ledger.
    unique = {}
    for row in rows:
        old = unique.get(row["path"])
        if old and old["sha256"] != row["sha256"]:
            raise RuntimeError(f"input pin conflict at {row['path']}")
        unique.setdefault(row["path"], row)
    return sorted(unique.values(), key=lambda row: row["path"])


def separate_startup_zero_evidence() -> dict:
    result = json.loads(ZERO_RECEIPT_PATH.read_text(encoding="utf-8"))
    if (result.get("frame") != "50F6" or result.get("offset_start") != 0 or
            result.get("size_bytes") != 19408 or result.get("nonzero_bytes") != 0 or
            result.get("all_zero") is not True):
        raise RuntimeError("separately pinned original FAR_BSS startup-zero receipt is invalid")
    return {"kind": "separate original-image pre-instruction FAR_BSS zero-fill evidence",
            "range": "[50F6:0000, DGROUP), section 27", "bytes": 19408,
            "nonzero_bytes": 0, "all_zero_before_instructions": True,
            "applies_to_all_three_targets": True,
            "checker": pin(ZERO_CHECKER_PATH), "receipt": pin(ZERO_RECEIPT_PATH),
            "map": pin(ROOT / "work/data/s27_map.md"),
            "rule": pin(ROOT / "tools/farbss.py"),
            "runtime_probe_directly_read_original_image": False,
            "limit": "Initial bytes only; counter SaveRec loads can replace persistent values, and the timer's activation/update rules govern later state."}


def main() -> int:
    denied = dos.install_input_guard()
    intake = json.loads(INTAKE_PATH.read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    canonical, effective, receipts = all_source_rows(intake)
    inventory = scan_sources(canonical, effective)
    save_rows = save_record_evidence()
    aliases = alias_evidence()
    lifecycle = source_lifetime_facts(inventory)
    code_controls = canonical_consumer_type_controls(manifest)
    compiled, provider_facts = compile_runtime_objects()
    runtime = run_runtime(compiled)
    if any(not row["actuals_match"] for row in runtime["case_counts"].values()):
        raise RuntimeError("runtime case expectation mismatch")
    report = {
        "schema": "simant-dos-ant-counter-balloon-timer-owner-review-v1",
        "status": "SOURCE_ONLY_CANDIDATE",
        "scope": {"members": list(TARGETS), "typed_extent_bytes_each": 4,
                  "functional_consumer_modules": ["root:0AD9", "root:0CDB", "S22:39C7",
                                                   "S24:39C7", "root:0250"],
                  "historical_COMDEF_TU_or_order_claim": False},
        "source_inventory": inventory,
        "source_ownership_and_lifecycle": lifecycle,
        "save_record_evidence": save_rows,
        "registry_alias_and_extent_checks": aliases,
        "original_initial_state_evidence": separate_startup_zero_evidence(),
        "provider": {"source": pin(PROVIDER_PATH), "source_shape": "three signed long far tentative definitions; no functions or initializers;",
                     "compiler": provider_facts},
        "canonical_source_compiler_controls": code_controls,
        "runtime": {"profile": "msc600ax", "flags": compiled["flags"],
                    "effective_flags": compiled["effective_flags"],
                    "cases": runtime["cases"], "case_counts": runtime["case_counts"],
                    "non_gating_extent_diagnostics": runtime["non_gating_extent_diagnostics"],
                    "libraries_and_runner": runtime["libraries_and_runner"],
                    "linkers": runtime["linkers"],
                    "runner_configuration": runtime["runner_configuration"],
                    "game_stubs_or_full_game_link_used": False},
        "input_pins": input_pins(canonical, effective, receipts, runtime),
        "denied_original_image_or_existing_object_reads": denied,
        "runtime_probe_original_EXE_or_existing_OBJ_read": False,
        "canonical_or_production_files_changed": False,
        "limits": [
            "The provider OMF communal records prove far storage widths, not a historical COMDEF-producing translation unit or communal order.",
            "The counters' signed long declarations are shared by every reviewed active source, but their current operations are increments, zero resets and a low-word history cast; no original-code signedness distinction is claimed for those counters.",
            "BAntsEaten and RAntsEaten are persistent SaveRec values. LoadGame copies raw bytes and does not range-check them; ordinary reset and increment paths do not bound arbitrary loaded values.",
            "ClearHistory is called through registered alias o24_39C7_01B8 in RandWorld and RandYard. Exact-name-only caller lists are incomplete and cannot establish absence; raw load still overwrites the reset values.",
            "The timer is absent from the SaveRec table. Its source establishes startup/activation reset ordering and signed-long TickCount comparison, but does not establish a numeric upper bound or prevent 32-bit wrap.",
            "RTLink/Plus 4.00 and 6.10 are experimental runtime instruments, not asserted to be the historical SimAnt linker."
        ]
    }
    report["probe_source"] = pin(Path(__file__))
    report_path = OUT / "report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    candidate = {
        "schema": "simant-dos-farbss-ant-counter-timer-owner-candidate-v1",
        "status": "CANDIDATE_PENDING_REVIEW",
        "members": list(TARGETS),
        "provider": report["provider"],
        "source_inventory_counts": {"canonical_translation_units": 127,
                                    "effective_behavior_sources": 29,
                                    "strict_index": pin(STATIC_INDEX_PATH),
                                    "drawballoons_effective_path": "work/source-only-dos/corrections/DrawBalloons/module.c"},
        "save_record_rows": save_rows["target_rows"],
        "historical_addresses": {name: aliases[name]["historical_address"] for name in TARGETS},
        "runtime_case_counts": runtime["case_counts"],
        "runtime_cases": runtime["cases"],
        "non_gating_extent_diagnostics": runtime["non_gating_extent_diagnostics"],
        "report": pin(report_path),
        "probe_source": pin(Path(__file__)),
        "source_runtime_original_image_or_existing_object_read": False,
        "game_stubs_or_full_game_link_used": False,
        "historical_COMDEF_TU_or_order_claim": False,
        "limitations": report["limits"]
    }
    candidate_path = OUT / "candidate.json"
    candidate_path.write_text(json.dumps(candidate, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"report": str(report_path.relative_to(ROOT)),
                      "candidate": str(candidate_path.relative_to(ROOT)),
                      "members": list(TARGETS), "runtime_cases": len(runtime["cases"]),
                      "all_expected_runtime_outcomes_pass": all(x["passed"] for x in runtime["cases"]),
                      "source_set_counts": inventory["set_counts"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
