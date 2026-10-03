"""Guarded source-only FAR_BSS ownership audit for lion/sow/pillar arrays.

The probe uses canonical and current effective source files, fresh pinned compiler
outputs, two experimental RTLink profiles and startup/runtime fixtures. It never
reads or patches an existing OBJ/EXE and never modifies canonical source or tools.
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

ROOT = next(parent for parent in Path(__file__).resolve().parents
            if (parent / "layout/manifest.json").is_file())
OUT = ROOT / "build/workers/dos_lion_array_owners"
OUT.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(ROOT / "tools"))
import compiler
from omf import OmfReader

INTAKE_PATH = ROOT / "work/source-only-dos/compile-and-intake-v1.json"
STATIC_INDEX_PATH = ROOT / "work/source-only-dos/static-completeness/index-v1.json"
MANIFEST_PATH = ROOT / "layout/manifest.json"
SYMBOLS_PATH = ROOT / "layout/symbols.json"
ROOT_SOURCE = ROOT / "src/root/m0AD9.c"
SAVE_SOURCE = ROOT / "src/S09/m35F5.c"
PROVIDER_PATH = ROOT / "work/source-only-dos/providers/lion-data.c"
ORIGINAL_FARBSS_REPORT = OUT / "original-farbss-zero.json"

BYTE_ARRAYS = ("LionListM", "LionListS", "LionListT", "LionListX", "LionListY")
WORD_SCALARS = ("PillDir", "PillarSeg")
WORD_ARRAYS = ("PillarMap", "SowDir", "SowSave", "SowX", "SowY")
TARGETS = BYTE_ARRAYS + WORD_SCALARS + WORD_ARRAYS
TARGET_BYTES = {**{n: 10 for n in BYTE_ARRAYS},
                **{n: 2 for n in WORD_SCALARS},
                "PillarMap": 12, **{n: 6 for n in ("SowDir", "SowSave", "SowX", "SowY")}}
SUPPORT_NAMES = ("LionIndex", "PillarState", "InitAntLions", "AddRandAntLion",
                 "AddAntLion", "DoAntLions", "SetAntLion", "FindInLionList",
                 "KillAntLion", "InitSow", "DoSow", "InitPillar", "DoPillar",
                 "StorePillarMap", "ReplacePillarMap", "MakeAPill", "IsValidA", "SRand1")

ROOT_DECLS = {
    "extern int far SowX[3];": "int far SowX[3];",
    "extern int far SowY[3];": "int far SowY[3];",
    "extern int far SowDir[3];": "int far SowDir[3];",
    "extern int far SowSave[3];": "int far SowSave[3];",
    "extern unsigned char far LionListX[];": "unsigned char far LionListX[10];",
    "extern unsigned char far LionListY[];": "unsigned char far LionListY[10];",
    "extern unsigned char far LionListM[];": "unsigned char far LionListM[10];",
    "extern unsigned char far LionListS[];": "unsigned char far LionListS[10];",
    "extern unsigned char far LionListT[];": "unsigned char far LionListT[10];",
    "extern int far PillarSeg;": "int far PillarSeg;",
    "extern int far PillDir;": "int far PillDir;",
    "extern int far PillarMap[6];": "int far PillarMap[6];",
}

SAVE_ROWS = [
    ("LionListM", 1, 10), ("LionListS", 1, 10), ("LionListT", 1, 10),
    ("LionListX", 1, 10), ("LionListY", 1, 10),
    ("PillarMap", 2, 6), ("SowDir", 2, 3), ("SowSave", 2, 3),
    ("SowX", 2, 3), ("SowY", 2, 3),
    ("PillDir", 2, 1), ("PillarSeg", 2, 1),
]

PROVIDER_DECLS = [
    *(f"unsigned char far {name}[10];" for name in BYTE_ARRAYS),
    "int far PillDir;", "int far PillarSeg;", "int far PillarMap[6];",
    "int far SowDir[3];", "int far SowSave[3];", "int far SowX[3];", "int far SowY[3];",
]
PROVIDER_SOURCE = "\n".join(PROVIDER_DECLS) + "\n"
PROVIDER_FLAGS = ["/AL", "/Os", "/Gs"]
SHAPE_SOURCE = """
int far lion_array_shape(void)
{
    return sizeof(LionListM) == 10 && sizeof(LionListS) == 10 &&
           sizeof(LionListT) == 10 && sizeof(LionListX) == 10 &&
           sizeof(LionListY) == 10 && sizeof(PillDir) == 2 &&
           sizeof(PillarSeg) == 2 && sizeof(PillarMap) == 12 &&
           sizeof(SowDir) == 6 && sizeof(SowSave) == 6 &&
           sizeof(SowX) == 6 && sizeof(SowY) == 6;
}
"""


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def pin(path: Path) -> dict:
    raw = path.read_bytes()
    try:
        name = path.relative_to(ROOT).as_posix()
    except ValueError:
        name = str(path).replace("\\", "/")
    return {"path": name, "sha256": sha(raw), "size": len(raw)}


def resolve_repo_path(path: str) -> Path:
    return ROOT / path.replace("\\", "/")


def checked_pin(row: dict, label: str) -> dict:
    path = resolve_repo_path(row["path"])
    raw = path.read_bytes()
    if sha(raw) != row["sha256"] or len(raw) != row["size"]:
        raise RuntimeError(f"{label} input changed: {row['path']}")
    return pin(path)


def registered_effective_behavior_sources() -> tuple[list[dict], list[dict]]:
    """Resolve the 29 effective whole-module sources from the strict static index."""
    index = json.loads(STATIC_INDEX_PATH.read_text(encoding="utf-8"))
    entries = index.get("entries", {})
    if index.get("schema") != "simant-dos-strict-static-index-v1" or len(entries) != 29:
        raise RuntimeError("strict static source index is not the expected 29-entry index")
    receipt_pins = [pin(STATIC_INDEX_PATH)]
    rows = []
    for function, ref in sorted(entries.items()):
        receipt_path = resolve_repo_path(ref["path"])
        receipt_pin = checked_pin({"path": ref["path"], "sha256": ref["sha256"],
                                   "size": ref["size"]}, "strict static receipt")
        receipt_pins.append(receipt_pin)
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        source = receipt.get("registered_source", {})
        # DrawBalloons has a reviewed source correction. The audit source is the
        # effective whole module; the registered source remains a superseded record.
        if function == "DrawBalloons":
            source = receipt.get("audit", {}).get("source", {})
        if not source.get("whole_module"):
            raise RuntimeError(f"{function} lacks an effective whole-module source")
        source_path = resolve_repo_path(source["path"])
        source_pin = pin(source_path)
        if source_pin["sha256"] != source["sha256"]:
            raise RuntimeError(f"effective source {function} changed: {source['path']}")
        rows.append({"path": source_pin["path"], "sha256": source_pin["sha256"],
                     "size": source_pin["size"], "module": source["module"],
                     "function": function,
                     "role": ("registered corrected whole-module behavior source"
                              if function == "DrawBalloons" else
                              "registered whole-module behavior source")})
    return rows, receipt_pins


def source_inventory(intake: dict) -> dict:
    """Scan 127 canonical TUs and the strict index's 29 effective behavior bodies."""
    token = re.compile(r"\b(" + "|".join(map(re.escape, TARGETS + SUPPORT_NAMES)) + r")\b")
    behavior_rows, receipt_pins = registered_effective_behavior_sources()
    sets = {
        "canonical_127": [t["source"] for t in intake["translation_units"]],
        "effective_body_29": behavior_rows,
    }
    result = {"set_counts": {k: len(v) for k, v in sets.items()}, "sets": {},
              "target_hits": {n: [] for n in TARGETS}, "support_hits": {n: [] for n in SUPPORT_NAMES},
              "reviewed_pins": [],
              "effective_source_index": pin(STATIC_INDEX_PATH),
              "effective_source_receipts": receipt_pins,
              "effective_source_paths": [row["path"] for row in behavior_rows]}
    for label, rows in sets.items():
        matches = []
        for row in rows:
            path = resolve_repo_path(row["path"])
            current_pin = checked_pin(row, label)
            result["reviewed_pins"].append(current_pin)
            text = path.read_text(encoding="latin1")
            hits = []
            for number, line in enumerate(text.splitlines(), 1):
                found = token.findall(line)
                if found:
                    hit = {"line": number, "names": found, "text": line.strip()}
                    hits.append(hit)
                    for name in set(found):
                        if name in TARGETS:
                            result["target_hits"][name].append({"set": label, "path": current_pin["path"], **hit})
                        elif name in SUPPORT_NAMES:
                            result["support_hits"][name].append({"set": label, "path": current_pin["path"], **hit})
            if hits:
                matches.append({"path": current_pin["path"], "sha256": current_pin["sha256"], "hits": hits})
        result["sets"][label] = {"scanned": len(rows), "files_with_hits": matches}
    # The exact target source-use inventory must reduce to the canonical root and SaveRec TUs.
    for name, hits in result["target_hits"].items():
        canonical_files = {h["path"] for h in hits if h["set"] == "canonical_127"}
        if canonical_files != {"src/root/m0AD9.c", "src/S09/m35F5.c"}:
            raise RuntimeError(f"unexpected canonical consumer set for {name}: {canonical_files}")
    return result


def alias_inventory() -> dict:
    syms = json.loads(SYMBOLS_PATH.read_text(encoding="utf-8"))["data"]
    starts = {
        "LionListX": 0x0A92, "LionListY": 0x0AA8, "LionListM": 0x0ABA,
        "LionListS": 0x0ACC, "LionListT": 0x0ADE, "PillarSeg": 0x0C36,
        "PillDir": 0x0C3C, "PillarMap": 0x0D9C, "SowX": 0x0EAE,
        "SowY": 0x0F00, "SowDir": 0x0F1A, "SowSave": 0x0F28,
    }
    result = {}
    for name, offset in starts.items():
        length = TARGET_BYTES[name]
        inside = [{"name": key, "segment": val.get("seg"), "offset": val.get("off")}
                  for key, val in syms.items()
                  if val.get("seg") == 0x50F6 and offset <= val.get("off", -1) < offset + length]
        result[name] = {"address": f"50F6:{offset:04X}", "extent_bytes": length,
                        "exact_base_names": [x for x in inside if x["offset"] == offset],
                        "interior_names": [x for x in inside if x["offset"] != offset]}
        if result[name]["exact_base_names"] != [{"name": name, "segment": 0x50F6, "offset": offset}]:
            raise RuntimeError(f"address registry base mismatch for {name}: {inside}")
        if result[name]["interior_names"]:
            raise RuntimeError(f"registered interior alias found for {name}: {inside}")
    return result


def compile_source(name: str, source: str, flags: list[str], profile: str = "msc600ax",
                   compiler_basename: str | None = None) -> bytes:
    (OUT / (name + ".c")).write_text(source, encoding="ascii", newline="\n")
    result = compiler.compile_c(source, profile, flags, basename=compiler_basename or name)
    if not result.ok or result.obj is None:
        (OUT / (name + ".compile.log")).write_text(result.log, encoding="latin1")
        raise RuntimeError(f"compile failed for {name}: {result.log[-2000:]}")
    raw = bytes(result.obj)
    (OUT / (name + ".OBJ")).write_bytes(raw)
    return raw


def omf_view(raw: bytes) -> tuple:
    omf = OmfReader(communals=True).read(raw)
    view = {
        "segments": {k: sha(v) for k, v in sorted(omf.segments.items())},
        "segment_byte_lengths": {k: len(v) for k, v in sorted(omf.segments.items())},
        "segment_lengths": omf.segment_lengths, "segment_defs": omf.segment_defs,
        "groups": omf.groups, "publics": omf.publics, "local_publics": omf.local_publics,
        "fixups": omf.fixups, "linker_fixups": omf.linker_fixups,
        "external_names": omf.externals, "external_scopes": omf.external_scopes,
        "local_externals": omf.local_externals, "communals": omf.communals,
    }
    return omf, view


def full_module_control(manifest: dict) -> dict:
    module = manifest["modules"]["root:0AD9"]
    if module["source"] != "src/root/m0AD9.c" or module["profile"] != "msc600ax":
        raise RuntimeError("root:0AD9 manifest profile/source changed")
    original = ROOT_SOURCE.read_text(encoding="latin1")
    if sha(ROOT_SOURCE.read_bytes()) != module["source_sha256"]:
        raise RuntimeError("root source hash differs from manifest")
    candidate = original
    edits = []
    for before, after in ROOT_DECLS.items():
        if original.count(before) != 1:
            raise RuntimeError(f"owner declaration not unique: {before}")
        candidate = candidate.replace(before, after, 1)
        edits.append({"before": before, "after": after, "count": 1})
    # A separately checked tracked provider avoids changing the functional TU's
    # CodeView and external-name ordering.
    provider_text = PROVIDER_PATH.read_text(encoding="ascii").replace("\r\n", "\n")
    if provider_text != PROVIDER_SOURCE:
        raise RuntimeError("tracked data-only provider differs from the reviewed twelve typed definitions")
    (OUT / "root-m0AD9-owner-candidate.c").write_text(candidate, encoding="latin1", newline="\n")
    flags = list(module["flags"])
    control_obj = compile_source("ROOTCTRL", original, flags, compiler_basename="R0AD9")
    owner_obj = compile_source("ROOTOWNR", candidate, flags, compiler_basename="R0AD9")
    control, control_view = omf_view(control_obj)
    owner, owner_view = omf_view(owner_obj)
    unchanged_fields = ("segments", "segment_byte_lengths", "segment_lengths", "segment_defs",
                        "groups", "publics", "local_publics", "fixups", "linker_fixups",
                        "external_names", "local_externals")
    unchanged = {field: control_view[field] == owner_view[field] for field in unchanged_fields}
    scope_diffs = []
    if len(control.externals) != len(control.external_scopes) or len(owner.externals) != len(owner.external_scopes):
        raise RuntimeError("whole-module external tables do not align with their scope records")
    control_scopes = dict(zip(control.externals, control.external_scopes))
    owner_scopes = dict(zip(owner.externals, owner.external_scopes))
    if len(control_scopes) != len(control.externals) or len(owner_scopes) != len(owner.externals):
        raise RuntimeError("duplicate external names prevent symbol-keyed scope comparison")
    for name in sorted(set(control_scopes) | set(owner_scopes)):
        before, after = control_scopes.get(name), owner_scopes.get(name)
        if before != after:
            scope_diffs.append({"name": name, "before": before, "after": after})
    expected_diffs = [{"name": "_" + n, "before": "external", "after": "communal"} for n in (
        "SowX", "SowY", "SowDir", "SowSave", "LionListX", "LionListY", "LionListM",
        "LionListS", "LionListT", "PillarSeg", "PillDir", "PillarMap")]
    expected_commons = sorted(("_" + n, length) for n, length in TARGET_BYTES.items())
    actual_commons = sorted((c["name"], c["length"]) for c in owner.communals)
    if sorted(scope_diffs, key=lambda x: x["name"]) != sorted(expected_diffs, key=lambda x: x["name"]):
        raise RuntimeError(f"unexpected external/communal scope deltas: {scope_diffs}")
    if actual_commons != expected_commons or len(owner.communals) != len(TARGETS):
        raise RuntimeError(f"candidate communals mismatch: {actual_commons}")

    code_data_segments = {k: v for k, v in control_view["segments"].items() if not k.startswith("$$")}
    owner_code_data_segments = {k: v for k, v in owner_view["segments"].items() if not k.startswith("$$")}
    code_data_bytes_equal = code_data_segments == owner_code_data_segments
    code_data_fixups_equal = ([x for x in control.fixups if not x["segment"].startswith("$$")] ==
                              [x for x in owner.fixups if not x["segment"].startswith("$$")])

    def semantic_linker_fixups(omf):
        rows = []
        for row in omf.linker_fixups:
            if row["segment"].startswith("$$"):
                continue
            normalized = dict(row)
            # These are symbol-table ordinal indices; the target/frame names and
            # locations remain the semantic relocation identity.
            normalized.pop("target_index", None)
            normalized.pop("frame_index", None)
            rows.append(normalized)
        return rows

    linker_fixups_semantically_equal = semantic_linker_fixups(control) == semantic_linker_fixups(owner)
    stable_fields = ("segment_byte_lengths", "segment_lengths", "segment_defs", "groups",
                     "publics", "local_publics", "local_externals")
    stable = {field: control_view[field] == owner_view[field] for field in stable_fields}
    if not code_data_bytes_equal or not code_data_fixups_equal or not linker_fixups_semantically_equal or not all(stable.values()):
        raise RuntimeError("typed owner candidate changed code/data contributions, semantic fixups, or stable OMF topology")
    data_provider_obj = compile_source("LIOWNER", provider_text, PROVIDER_FLAGS)
    data_provider, _ = omf_view(data_provider_obj)
    actual_provider_commons = sorted((c["name"], c["length"]) for c in data_provider.communals)
    provider_nonempty_segments = {k: len(v) for k, v in data_provider.segments.items() if v}
    provider_code_data_bytes = sum(len(v) for k, v in data_provider.segments.items() if not k.startswith("$$"))
    provider_debug_bytes = sum(len(v) for k, v in data_provider.segments.items() if k.startswith("$$"))
    provider_nonzero_segment_lengths = {k: v for k, v in data_provider.segment_lengths.items() if v}
    provider_debug_segment_names = [s["name"] for s in data_provider.segment_defs if s["name"].startswith("$$")]
    required_flags = list(compiler.verify_profile("msc600ax").get("required_flags", []))
    if required_flags != ["/EM"]:
        raise RuntimeError(f"unexpected MSC 6.00AX required flags: {required_flags}")
    provider_invariants = {
        "profile": "msc600ax", "flags": list(PROVIDER_FLAGS),
        "profile_required_flags": required_flags,
        "effective_flags": PROVIDER_FLAGS + required_flags,
        "no_debug_switch": "/Zi" not in PROVIDER_FLAGS + required_flags,
        "communal_rows_exact": actual_provider_commons == expected_commons,
        "communal_rows": data_provider.communals,
        "nonempty_segments": provider_nonempty_segments,
        "segment_lengths": data_provider.segment_lengths,
        "nonzero_segment_lengths": provider_nonzero_segment_lengths,
        "code_data_payload_bytes": provider_code_data_bytes,
        "debug_payload_bytes": provider_debug_bytes,
        "debug_segments": provider_debug_segment_names,
        "public_count": len(data_provider.publics),
        "local_public_count": len(data_provider.local_publics),
        "fixup_count": len(data_provider.fixups),
        "linker_fixup_count": len(data_provider.linker_fixups),
        "external_names": data_provider.externals,
        "external_scopes": data_provider.external_scopes,
        "local_externals": data_provider.local_externals,
    }
    expected_external_names = ["_" + n for n in TARGETS]
    exact_communal_externals = (data_provider.externals == expected_external_names and
                                data_provider.external_scopes == ["communal"] * len(TARGETS))
    provider_invariants["all_expected_communal_externals"] = exact_communal_externals
    provider_invariants["noncommunal_external_count"] = sum(
        1 for scope in data_provider.external_scopes if scope != "communal")
    if (actual_provider_commons != expected_commons or provider_nonempty_segments or
            provider_nonzero_segment_lengths or provider_debug_segment_names or
            provider_code_data_bytes or provider_debug_bytes or data_provider.publics or
            data_provider.local_publics or data_provider.fixups or data_provider.linker_fixups or
            not exact_communal_externals or data_provider.local_externals or "/Zi" in PROVIDER_FLAGS):
        raise RuntimeError(f"pure data-only provider OMF invariant failed: {provider_invariants}")

    wrong_extent = candidate.replace("unsigned char far LionListM[10];", "unsigned char far LionListM[9];", 1)
    wrong_width = candidate.replace("int far SowSave[3];", "unsigned char far SowSave[6];", 1)
    bad_extent_obj = compile_source("ROOTBADX", wrong_extent, flags, compiler_basename="R0AD9")
    bad_width_obj = compile_source("ROOTBADW", wrong_width, flags, compiler_basename="R0AD9")
    bad_extent, bad_extent_view = omf_view(bad_extent_obj)
    bad_width, bad_width_view = omf_view(bad_width_obj)
    if sorted((c["name"], c["length"]) for c in bad_extent.communals) != sorted(
            [("_" + n, length - (1 if n == "LionListM" else 0)) for n, length in TARGET_BYTES.items()]):
        raise RuntimeError("wrong LionListM extent negative control did not shrink one communal")
    bad_width_code_data = {k: v for k, v in bad_width_view["segments"].items() if not k.startswith("$$")}
    if bad_width_code_data == owner_code_data_segments:
        raise RuntimeError("wrong SowSave element width did not change full-module code/data bytes")
    return {
        "module": "root:0AD9", "profile": module["profile"], "flags": flags,
        "source_sha256": module["source_sha256"], "candidate_edits": edits,
        "fresh_control_object": {"sha256": sha(control_obj), "bytes": len(control_obj)},
        "typed_owner_object": {"sha256": sha(owner_obj), "bytes": len(owner_obj)},
        "object_size_delta_bytes": len(owner_obj) - len(control_obj),
        "all_segment_hashes_equal": unchanged["segments"],
        "all_omf_fixups_equal": unchanged["fixups"],
        "all_linker_fixup_records_equal": unchanged["linker_fixups"],
        "debug_segment_hash_changes": {name: {"control": control_view["segments"].get(name),
                                               "owner": owner_view["segments"].get(name)}
                                        for name in sorted(set(control.segments) | set(owner.segments))
                                        if name.startswith("$$") and control.segments.get(name) != owner.segments.get(name)},
        "code_data_segment_hashes_equal": code_data_bytes_equal,
        "code_data_fixups_equal": code_data_fixups_equal,
        "code_data_linker_fixups_equal_ignoring_symbol_ordinals": linker_fixups_semantically_equal,
        "stable_omf_fields": stable, "external_name_order_equal": unchanged["external_names"],
        "external_scope_changes": scope_diffs,
        "candidate_communals": owner.communals,
        "all_segment_bytes_equal": unchanged["segments"],
        "segment_lengths_equal": unchanged["segment_lengths"],
        "definitions_and_groups_equal": unchanged["segment_defs"] and unchanged["groups"],
        "publics_equal": unchanged["publics"], "fixups_equal": unchanged["fixups"],
        "ordered_linker_fixups_equal": unchanged["linker_fixups"],
        "data_only_provider_object": {"sha256": sha(data_provider_obj), "bytes": len(data_provider_obj),
                                      "communals": data_provider.communals,
                                      "compiler": provider_invariants},
        "negative_wrong_extent": {"communal_rows": bad_extent.communals,
                                  "full_module_code_data_equal": bad_extent_view["segments"] == owner_view["segments"]},
        "negative_wrong_element_width": {"full_module_code_data_equal": bad_width_code_data == owner_code_data_segments,
                                         "communal_rows": bad_width.communals},
        "recommendation": "root:0AD9 is the functional source owner, but adding definitions there changes CodeView $$SYMBOLS/$$TYPES bytes and external symbol ordering. Keep the root TU unchanged and use the standalone typed data-only provider for these proven extents. No historical COMDEF translation-unit/order claim is made."
    }


def declarations_for_consumer() -> str:
    return "\n".join([*(f"extern unsigned char far {n}[10];" for n in BYTE_ARRAYS),
                      "extern int far PillDir;", "extern int far PillarSeg;",
                      "extern int far PillarMap[6];", "extern int far SowDir[3];",
                      "extern int far SowSave[3];", "extern int far SowX[3];", "extern int far SowY[3];",
                      "extern int far lion_array_shape(void);"])


WORD_CONSUMER = declarations_for_consumer() + r'''
extern int far puts(char far *text);
int main(void)
{
    int i;
    if (!lion_array_shape()) { puts("FAIL"); return 0; }
    for (i=0; i<10; i++)
        if (LionListM[i] || LionListS[i] || LionListT[i] || LionListX[i] || LionListY[i]) {
            puts("FAIL"); return 0;
        }
    if (PillDir || PillarSeg) { puts("FAIL"); return 0; }
    for (i=0; i<6; i++) if (PillarMap[i]) { puts("FAIL"); return 0; }
    for (i=0; i<3; i++)
        if (SowDir[i] || SowSave[i] || SowX[i] || SowY[i]) { puts("FAIL"); return 0; }
    PillDir = -2;
    PillarSeg = 0x1234;
    PillarMap[0] = 0x2345;
    PillarMap[5] = -3;
    for (i=0; i<10; i++) {
        LionListM[i] = (unsigned char)(i+1);
        LionListS[i] = (unsigned char)(i+11);
        LionListT[i] = (unsigned char)(i+21);
        LionListX[i] = (unsigned char)(i+31);
        LionListY[i] = (unsigned char)(i+41);
    }
    for (i=0; i<3; i++) {
        SowDir[i] = i-1;
        SowSave[i] = 0x1200+i;
        SowX[i] = 20+i;
        SowY[i] = 30+i;
    }
    if (PillDir != -2 || PillarSeg != 0x1234 || PillarMap[0] != 0x2345 ||
        PillarMap[5] != -3 || LionListM[9] != 10 || LionListY[9] != 50 ||
        SowDir[0] != -1 || SowSave[2] != 0x1202 || SowY[2] != 32 ||
        *((unsigned char far *)&PillDir) != 0xfe ||
        *(((unsigned char far *)&PillDir)+1) != 0xff) {
        puts("FAIL"); return 0;
    }
    puts("PASS");
    return 0;
}
'''


def make_byte_consumer(wrong_row: bool = False) -> str:
    rows = []
    for name, size, count in SAVE_ROWS:
        row_count = count + 1 if wrong_row and name == "LionListT" else count
        rows.append(f"    {{ {size}, {row_count}, (void far *)&{name} }},")
    conditions = []
    for index, (name, size, count) in enumerate(SAVE_ROWS):
        conditions.extend([f"rows[{index}].size != {size}", f"rows[{index}].count != {count}",
                           f"rows[{index}].data != (void far *)&{name}"])
    words = []
    for row_index, (name, size, count) in enumerate(SAVE_ROWS):
        if size == 2:
            elems = count
            expression = f"{name}[i]" if name not in WORD_SCALARS else name
            words.append(f"    for (i=0; i<{elems}; i++) {{\n"
                         f"        if ((unsigned int){expression} != (((unsigned int)view[{row_index}][2*i+1] << 8) | view[{row_index}][2*i])) {{ puts(\"FAIL\"); return 0; }}\n"
                         "    }")
    return declarations_for_consumer() + "\n" + r'''
extern int far puts(char far *text);
struct SaveRec { int size; int count; void far *data; };
struct SaveRec far rows[12] = {
''' + "\n".join(rows) + r'''
};
int main(void)
{
    int i;
    int j;
    unsigned char far *view[12];
    if (!lion_array_shape() || ''' + " || ".join(conditions) + r''') {
        puts("FAIL"); return 0;
    }
    for (i=0; i<12; i++) {
        view[i] = (unsigned char far *)rows[i].data;
        for (j=0; j<rows[i].size*rows[i].count; j++)
            if (view[i][j] != 0) { puts("FAIL"); return 0; }
    }
    for (i=0; i<12; i++)
        for (j=0; j<rows[i].size*rows[i].count; j++)
            view[i][j] = (unsigned char)(0x20+i+j*7);
''' + "\n".join(words) + r'''
    if (LionListM[0] != view[0][0] || LionListT[9] != view[2][9] ||
        LionListX[9] != view[3][9] || LionListY[9] != view[4][9]) {
        puts("FAIL"); return 0;
    }
    puts("PASS");
    return 0;
}
'''


def runtime_owner(source: str) -> str:
    return source + "\n" + SHAPE_SOURCE


def compile_runtime_objects() -> dict:
    tc = compiler.toolchain()
    compiler_flags = list(PROVIDER_FLAGS)
    consumer_flags = list(PROVIDER_FLAGS)
    required_flags = list(compiler.verify_profile("msc600ax").get("required_flags", []))
    if required_flags != ["/EM"] or compiler_flags != ["/AL", "/Os", "/Gs"] or consumer_flags != compiler_flags:
        raise RuntimeError("provider/runtime fixture flags differ from the reviewed MSC 6.00AX /AL /Os /Gs + /EM setup")
    owner_good = runtime_owner(PROVIDER_SOURCE)
    owner_bad_lion_extent = runtime_owner(PROVIDER_SOURCE.replace(
        "unsigned char far LionListM[10];", "unsigned char far LionListM[9];", 1))
    owner_bad_sow_extent = runtime_owner(PROVIDER_SOURCE.replace(
        "int far SowX[3];", "int far SowX[2];", 1))
    owner_bad_pill_width = runtime_owner(PROVIDER_SOURCE.replace(
        "int far PillDir;", "unsigned char far PillDir;", 1))
    owner_initialized = runtime_owner(PROVIDER_SOURCE.replace("int far PillDir;", "int far PillDir = 1;", 1))
    if len({owner_good, owner_bad_lion_extent, owner_bad_sow_extent,
            owner_bad_pill_width, owner_initialized}) != 5:
        raise RuntimeError("owner negative controls were not distinct")
    objs = {
        "typed_owner": compile_source("RTOWNER", owner_good, compiler_flags),
        # MSC's DOS compiler requires an 8-character source basename.
        "bad_lion_extent": compile_source("BDLION", owner_bad_lion_extent, compiler_flags),
        "bad_sow_extent": compile_source("BDSOW", owner_bad_sow_extent, compiler_flags),
        "bad_pill_width": compile_source("BDPILL", owner_bad_pill_width, compiler_flags),
        "initialized_owner": compile_source("RTINIT", owner_initialized, compiler_flags),
        "word_consumer": compile_source("RTWORD", WORD_CONSUMER, consumer_flags),
        "byte_consumer": compile_source("RTBYTE", make_byte_consumer(), consumer_flags),
        "bad_row_consumer": compile_source("RTBADROW", make_byte_consumer(wrong_row=True), consumer_flags),
    }
    for key, raw in objs.items():
        omf, _ = omf_view(raw)
        if key == "typed_owner":
            expected = sorted(("_" + name, length) for name, length in TARGET_BYTES.items())
            if sorted((c["name"], c["length"]) for c in omf.communals) != expected:
                raise RuntimeError(f"runtime typed owner OMF mismatch: {omf.communals}")
            if any(name.startswith("$$") and data for name, data in omf.segments.items()):
                raise RuntimeError("runtime helper owner unexpectedly emits debug payload")
        if key == "initialized_owner":
            common_names = {c["name"] for c in omf.communals}
            public_names = {p["name"] for p in omf.publics}
            if "_PillDir" in common_names or "_PillDir" not in public_names:
                raise RuntimeError("initialized control did not move PillDir out of FAR_BSS common storage")
    return {"objects": objs, "compiler_flags": compiler_flags, "consumer_flags": consumer_flags,
            "effective_flags": compiler_flags + required_flags,
            "cases": [
                ("typed_word", "PASS", "word_consumer", "typed_owner"),
                ("typed_SaveRec_bytes", "PASS", "byte_consumer", "typed_owner"),
                ("wrong_LionListM_extent", "FAIL", "word_consumer", "bad_lion_extent"),
                ("wrong_SowX_extent", "FAIL", "word_consumer", "bad_sow_extent"),
                ("wrong_PillDir_width", "FAIL", "word_consumer", "bad_pill_width"),
                ("initialized_nonzero_PillDir", "FAIL", "word_consumer", "initialized_owner"),
                ("wrong_SaveRec_row_count", "FAIL", "bad_row_consumer", "typed_owner"),
            ]}


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
    conf_lines = []
    for section, settings in runner["conf"].items():
        conf_lines.append("[" + section + "]")
        conf_lines += [f"{key}={value}" for key, value in settings.items()]
    conf_lines += ["[autoexec]", f'mount c "{directory}"', f'mount d "{tool_dir}" -ro',
                   "c:", "call RUN.BAT", "exit"]
    conf = directory / "dosbox.conf"
    conf.write_text("\n".join(conf_lines) + "\n", encoding="ascii")
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
    log = (directory / "RUN.LOG").read_text(encoding="latin1").strip() if (directory / "RUN.LOG").exists() else "NO RUN.LOG"
    link_log = (directory / "LINK.LOG").read_text(encoding="latin1", errors="replace") if (directory / "LINK.LOG").exists() else ""
    row = {"linker": profile, "case": case, "expected": expected, "actual": log,
           "emulator_exit": run.returncode, "timed_out": timed_out,
           "passed": log == expected and run.returncode == 0 and not timed_out,
           "link_log_tail": link_log[-500:]}
    print(profile, case, log, flush=True)
    return row


def runtime_controls(compiled: dict) -> dict:
    tc = compiler.toolchain()
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    runtime_rows = list(manifest["runtime"]["libraries"].values())
    runner = tc["runners"]["dosbox-x"]
    results = []
    for profile in ("rtlink400", "rtlink610"):
        linker = tc["linkers"][profile]
        tool_dir = compiler.pinned_tree(linker)
        for case, expected, consumer_key, owner_key in compiled["cases"]:
            results.append(run_link_case(profile, case, expected,
                                         compiled["objects"][consumer_key], compiled["objects"][owner_key],
                                         runtime_rows, linker, runner, tool_dir))
    if len(results) != 14 or not all(x["passed"] for x in results):
        raise RuntimeError("RTLink startup/runtime controls did not meet expected outcomes")
    return {"cases": results, "expected_outcomes_pass": True,
            "runtime_libraries": [pin(Path(row["path"])) for row in runtime_rows],
            "runner": {"path": runner["path"], "sha256": runner["sha256"]},
            "linkers": {name: tc["linkers"][name] for name in ("rtlink400", "rtlink610")}}


def input_pins(inventory: dict) -> list[dict]:
    paths = [ROOT / "README.md", ROOT / "docs/codegen-rules.md", ROOT / "docs/tu-evidence.md",
             ROOT / "layout/manifest.json", ROOT / "layout/toolchain.json", ROOT / "layout/symbols.json",
             ROOT / "layout/oracle.lock.json", ROOT / "tools/farbss.py", ROOT / "work/data/s27_map.md",
             ROOT / "work/source-only-dos/compile-and-intake-v1.json", STATIC_INDEX_PATH,
             ROOT_SOURCE, SAVE_SOURCE,
             ROOT / "src/root/m0093.c", ROOT / "src/root/m10F7.c", ROOT / "src/S18/m384C.c",
             PROVIDER_PATH]
    return ([pin(p) for p in paths] + inventory["effective_source_receipts"] +
            inventory["reviewed_pins"])


def original_initial_state_evidence() -> dict:
    """Read the separate check's summary only; this probe never opens the original image."""
    result = None
    if ORIGINAL_FARBSS_REPORT.is_file():
        result = json.loads(ORIGINAL_FARBSS_REPORT.read_text(encoding="utf-8"))
        if (result.get("frame") != "50F6" or result.get("offset_start") != 0 or
                result.get("size_bytes") != 19408 or result.get("nonzero_bytes") != 0 or
                result.get("all_zero") is not True):
            raise RuntimeError("separate original FAR_BSS zero-fill evidence does not match the reviewed region")
    evidence = {
        "kind": "ORIGINAL_IMAGE_FAR_BSS_ZERO_FILL",
        "range": "original image FAR_BSS [50F6:0000, DGROUP), section 27",
        "size_bytes": 19408, "nonzero_bytes": 0, "all_zero": True,
        "zero_fill_rule": pin(ROOT / "tools/farbss.py"),
        "original_section_map": pin(ROOT / "work/data/s27_map.md"),
        "current_manifest_pin": pin(MANIFEST_PATH),
        "current_oracle_lock_pin": pin(ROOT / "layout/oracle.lock.json"),
        "applies_to_every_reviewed_FAR_BSS_byte_including_Sow_slot_0": True,
        "evidence_basis": "The accepted original section-27 map reports 19,408 FAR_BSS bytes and zero nonzero bytes; tools/farbss.py states and checks that [50F6:0000,DGROUP) is entirely zero linker fill. The latest historical full validation also passed FAR_BSS zero-fill with unchanged oracle/manifest.",
        "scope_limit": "Original startup bytes only; SaveRec-loaded values remain unvalidated and may be out of bounds.",
        "runtime_probe_opened_original_image": False,
    }
    if result is not None:
        evidence["separate_fresh_check"] = {
            "checker": pin(ROOT / "build/workers/dos_lion_array_owners/check-original-farbss-zero.py"),
            "result": pin(ORIGINAL_FARBSS_REPORT),
        }
    return evidence


def main() -> int:
    intake = json.loads(INTAKE_PATH.read_text(encoding="utf-8"))
    if len(intake["translation_units"]) != 127:
        raise RuntimeError("canonical source inventory cardinality changed from 127")
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    inventory = source_inventory(intake)
    aliases = alias_inventory()
    initial_state = original_initial_state_evidence()
    whole_module = full_module_control(manifest)
    compiled = compile_runtime_objects()
    runtime = runtime_controls(compiled)
    cases_by_profile = {}
    for profile in ("rtlink400", "rtlink610"):
        rows = [x for x in runtime["cases"] if x["linker"] == profile]
        cases_by_profile[profile] = {"pass_count": sum(x["expected"] == "PASS" for x in rows),
                                     "fail_count": sum(x["expected"] == "FAIL" for x in rows),
                                     "actuals_match": all(x["actual"] == x["expected"] and x["passed"] for x in rows)}
    if any(x["pass_count"] != 2 or x["fail_count"] != 5 or not x["actuals_match"]
           for x in cases_by_profile.values()):
        raise RuntimeError(f"runtime case balance/outcomes mismatch: {cases_by_profile}")
    report = {
        "schema": "simant-dos-lion-sow-pillar-farbss-review-v1",
        "status": "SOURCE_ONLY_REVIEW_CANDIDATE",
        "scope": {"target_objects": list(TARGETS), "target_count": len(TARGETS),
                  "functional_module": "root:0AD9", "historical_COMDEF_TU_order_claim": False},
            "source_inventory": inventory,
        "source_owner_facts": {
            "root_module": "src/root/m0AD9.c / root:0AD9; actual functions initialize and consume these objects.",
            "save_module": "src/S09/m35F5.c / S09:35F5; one SaveRec row per object, read/write through data pointer and count*size.",
            "source_types_and_extents": {
                **{n: {"declaration": f"extern unsigned char far {n}[];", "logical_extent": 10,
                       "save_rec": {"size": 1, "count": 10, "bytes": 10}} for n in BYTE_ARRAYS},
                "PillDir": {"declaration": "extern int far PillDir;", "logical_extent": 1,
                            "save_rec": {"size": 2, "count": 1, "bytes": 2}},
                "PillarSeg": {"declaration": "extern int far PillarSeg;", "logical_extent": 1,
                              "save_rec": {"size": 2, "count": 1, "bytes": 2}},
                "PillarMap": {"declaration": "extern int far PillarMap[6];", "logical_extent": 6,
                              "save_rec": {"size": 2, "count": 6, "bytes": 12}},
                **{n: {"declaration": f"extern int far {n}[3];", "logical_extent": 3,
                       "save_rec": {"size": 2, "count": 3, "bytes": 6}}
                   for n in ("SowDir", "SowSave", "SowX", "SowY")}
            },
            "all_source_reads_writes_and_save_rows": inventory["target_hits"],
            "save_load_pointer_escape": {
                "LoadGame": "S09:35F5 line 118: read(fd,p->data,p->count*p->size).",
                "SaveGame": "S09:35F5 line 183: write(fd,p->data,p->count*p->size).",
                "pointer_use": "The table stores far addresses; generic I/O uses byte lengths from size*count and does not perform element arithmetic on p->data."
            },
            "registry_aliases": aliases,
            "address_basis": "Each extent is established by typed root declarations/indices plus its SaveRec size*count. Registry-address intervals were checked only for aliases; gaps between registered bases are not used as extent or padding evidence.",
            "sow_slot_zero": "InitSow begins at i=2 and decrements after each accepted seed, so it assigns slots 2 and 1 and leaves slot 0 unchanged. DoSow loops i=0..2 and reads SowDir/SowSave/SowX/SowY slot 0. The separate original-image check establishes zero startup bytes across the complete 50F6:0000..DGROUP FAR_BSS region, including these slot-0 bytes; it does not validate later SaveRec-loaded values.",
            "unchecked_paths": [
                "DoSow reads SowTab[SowDir[i]] and Dx8/Dy8[SowDir[i]] without a local 0..7 check; valid 0..7 initialization is established for slots 1 and 2, not source-reset for slot 0 or arbitrary loaded state.",
                "DoSow uses existing SowX/Y coordinates in MapA before validating the old coordinate; InitSow generates bounded coordinates for slots 1 and 2, while slot 0 and unvalidated SaveRec contents remain unchecked.",
                "DoAntLions directly indexes LionList arrays with i < LionIndex and uses stored x/y in LifeA/MapA expressions without a local bounds check; ordinary AddAntLion paths are capped by ten-entry storage, while arbitrary loaded LionIndex/list data is not range-validated.",
                "StorePillarMap and ReplacePillarMap call IsValidA before indexing PillarMap with x%6 or y%6; IsValidA accepts only x 0..127 and y 0..63, so accepted modulo results are 0..5.",
                "LoadGame copies saved bytes directly through every SaveRec row; no field-range validation was found in this table path."
            ],
            "supporting_bounds": {
                "InitAntLions/AddAntLion": "InitAntLions clamps count to <=10; AddAntLion writes at LionIndex and increments only when LionIndex<9, so its ordinary initial-fill path writes indices 0..9. Negative counts produce no loop iterations. The target arrays' 10-byte SaveRec rows agree.",
                "Sow_coordinate_ranges": "SRand1 returns the remainder modulo its positive unsigned argument; InitSow passes 128 and 64 for x/y and 8 for direction. Root m0093 SRand1 uses DIV and returns DX; its args here are positive.",
                "pillar_map_bounds": "IsValidA source checks 0<=x<=127 and 0<=y<=63 before both pillar map operations."
            },
            "source_resets": {
                "LionListM/S/T/X/Y": "InitAntLions resets LionIndex; each AddAntLion writes all five fields at the new slot before the ordinary DoAntLions loop consumes that slot. It does not clear all ten backing bytes.",
                "PillDir/PillarSeg/PillarMap": "InitPillar assigns PillDir=0 and PillarSeg=0, then clears PillarMap[0..5]. MakeAPill assigns PillDir from SRand1(4); DoPillar uses PillarSeg values 4, decrements to 0, then resets it to 5.",
                "Sow arrays": "InitSow initializes only slots 2 and 1 and does not reset slot 0. Independent original-image FAR_BSS zero-fill evidence establishes the initial slot-0 bytes as zero; runtime SaveRec loads can replace them without range checks."
            },
            "supporting_control_words_not_in_FAR_BSS_scope": {
                "LionIndex": "int far, SaveRec {2,1}; registry address 3D57:0C4A, outside 50F6.",
                "PillarState": "int far, SaveRec {2,1}; registry address 3D57:0C4C, outside 50F6."
            }
        },
        "whole_module_compile_control": whole_module,
        "runtime_probe": {"compiler_flags": compiled["compiler_flags"],
                          "consumer_flags": compiled["consumer_flags"],
                          "effective_flags": compiled["effective_flags"],
                          "debug_switch_used": False,
                          "case_summary": cases_by_profile,
                          "cases": runtime["cases"],
                          "runtime_libraries": runtime["runtime_libraries"],
                          "runner": runtime["runner"],
                          "linkers": runtime["linkers"],
                          "test_owner_scope": "Test-only lion_array_shape size checker; no game-function stubs, whole-game object, or dummy game imports."},
        "source_provider": {
            "functional_owner_candidate": "root:0AD9 is the source-functional owner, but its debug symbol section and external-name order change when definitions are added; do not use the full-module rewrite as the provider.",
            "recommended_data_only_provider": "work/source-only-dos/providers/lion-data.c; exactly the twelve proven typed tentative definitions, no functions.",
            "data_only_provider_communal_rows": whole_module["data_only_provider_object"]["communals"],
            "pure_provider_compiler_invariants": whole_module["data_only_provider_object"]["compiler"],
            "initial_zero_limit": "The controlled tentative provider is zero-filled under the selected test CRTs. Separately, original-image evidence establishes every initial byte in FAR_BSS [50F6:0000,DGROUP) as zero. This does not establish a historical COMDEF owner/order, and it does not bound runtime SaveRec-loaded values."
        },
        "original_initial_state_evidence": initial_state,
        "input_pins": input_pins(inventory),
        "source_runtime_probe_original_EXE_or_existing_OBJ_read": False,
        "separate_original_FAR_BSS_zero_fill_check": "Evidence is a separate historical-image research result; the guarded source/runtime probe does not open the image.",
        "game_stubs_or_full_game_link_used": False,
        "canonical_or_production_files_changed": False
    }
    report["probe_source"] = pin(Path(__file__))
    report_path = OUT / "report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    candidate = {
        "schema": "simant-dos-farbss-source-owner-candidate-v1",
        "scope": report["scope"],
        "recommended_functional_owner": "root:0AD9",
        "candidate_source": "work/source-only-dos/providers/lion-data.c",
        "candidate_source_sha256": sha(PROVIDER_PATH.read_bytes()),
        "edits": whole_module["candidate_edits"],
        "members": list(TARGETS),
        "dos_type_and_extent": report["source_owner_facts"]["source_types_and_extents"],
        "historical_COMDEF_translation_unit_or_order_claim": False,
        "address_gap_used_as_extent_evidence": False,
        "runtime_cases": runtime["cases"],
        "source_runtime_probe_original_EXE_or_existing_OBJ_read": False,
        "original_initial_state_evidence": initial_state,
        "all_runtime_cases_passed_expected_outcomes": True,
        "all_source_hits": inventory["target_hits"],
        "registry_aliases": aliases,
        "whole_module_comparison": whole_module,
        "source_provider": report["source_provider"],
        "limits": [
            "Sow slot 0 is not reset by InitSow and is read by DoSow. Separate original-image FAR_BSS zero-fill evidence establishes its initial bytes only; runtime-loaded values remain unvalidated.",
            "SaveRec load values are not validated by the table loop; bounds statements apply to normal source initialization and ordinary mutations only.",
            "RTLink 4.00 and 6.10 are experimental source-runtime instruments, not claimed as the historical SimAnt linker.",
            "The object address registry is used only to verify same-base/interior aliases within source/table-proven spans; inter-object gaps remain unclaimed."
        ]
    }
    candidate_path = OUT / "candidate.json"
    candidate_path.write_text(json.dumps(candidate, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"report": "build/workers/dos_lion_array_owners/report.json",
                      "candidate": "build/workers/dos_lion_array_owners/candidate.json",
                      "target_count": len(TARGETS), "runtime_cases": len(runtime["cases"]),
                      "runtime_ok": runtime["expected_outcomes_pass"],
                      "root_code_data_equal": whole_module["code_data_segment_hashes_equal"],
                      "root_debug_sections_change": bool(whole_module["debug_segment_hash_changes"])}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
