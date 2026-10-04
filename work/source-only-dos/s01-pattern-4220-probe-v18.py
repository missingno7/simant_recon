"""Scratch-only source-owner and RTLink proof for S01's 4220h operand."""
from __future__ import annotations

from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "work/source-only-dos"
OUT = ROOT / "build/workers/dos_s01_pattern_4220/durable-v18"
SOURCES = OUT / "sources"
OBJECTS = OUT / "objects"
CASES = OUT / "linkers"
TOOL_COPIES = OUT / "pinned-linkers"
RECEIPT_PATH = PACKAGE / "s01-pattern-4220-proof-candidate-v18.json"
REVIEW_PATH = PACKAGE / "s01-pattern-4220-review-v18.md"
BINDING_PATH = PACKAGE / "s01-pattern-4220-bindings-candidate-v18.json"

sys.path.insert(0, str(ROOT / "tools"))
import compiler  # noqa: E402
from omf import OmfReader  # noqa: E402

TARGET_SOURCE = "build/source-only-dos/sources/U004.asm"
OWNER_SOURCE = "build/source-only-dos/sources/U086.asm"
TARGET_MODULE = "S01:3126"
OWNER_MODULE = "root:1B4E"
ACTIVE_TARGET = {
    "module": TARGET_MODULE, "basename": "U004",
    "canonical_path": "src/S01/m3126.asm",
    "canonical_sha256": "ac99ea7821999d034e64201798d49dfaf64632f34e5f5dee428c9b6dec01a44a",
    "generated_path": "build/source-only-dos/sources/U004.asm",
    "generated_sha256": "f14c1ebb3391f9188e388105916979f3b3a1c5c9a6a0222686bf15dd404edccb",
    "object_path": "build/source-only-dos/objects/U004.OBJ",
    "object_sha256": "7fd7972dc8ab587f3d34de9e0ef08b763d207245b8f237223b235cf61c84670f",
}
ACTIVE_OWNER = {
    "module": OWNER_MODULE, "basename": "U086",
    "canonical_path": "src/root/m1B4E.asm",
    "canonical_sha256": "a32d75d2d4ea36980b659d26e9ddd86bcde65d9e250ebac4cdc29c0e847c67a2",
    "generated_path": "build/source-only-dos/sources/U086.asm",
    "generated_sha256": "9f18195ddfa42822f0e54c8a3edf016a751dd7c23b67620c647c75de02c12714",
    "object_path": "build/source-only-dos/objects/U086.OBJ",
    "object_sha256": "afaf236194c2951920ecf9cf9915e8c174c6cf75a56a324d0fe4f7dc457b52b9",
}
LITERAL = "\tmov bh, byte ptr ss:[bx+4220h]"
SYMBOLIC = ("\tassume ss:DGROUP\n"
            "\tmov bh, byte ptr ss:[bx+_g_4220]\n"
            "\tassume ss:nothing")


def require(ok: bool, message: str) -> None:
    if not ok:
        raise SystemExit("S01 4220 scratch proof failed closed: " + message)


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def pin(path: Path, expected: str | None = None) -> dict:
    raw = path.read_bytes()
    digest = sha(raw)
    require(expected is None or digest == expected,
            f"pin mismatch for {path}: {digest} != {expected}")
    return {"path": path.resolve().relative_to(ROOT.resolve()).as_posix(),
            "sha256": digest, "size": len(raw)}


def write_source(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.replace("\r\n", "\n").replace("\n", "\r\n").encode("ascii"))


def asm(text: str, basename: str):
    result = compiler.assemble(text, "masm510", ["/Mx"], basename=basename, keep=False)
    require(result.ok, f"MASM failed for {basename}: {result.log}")
    return result


def object_pin(raw: bytes, path: Path) -> dict:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)
    return pin(path)


def c_commentless(path: Path, text: str) -> list[tuple[int, str]]:
    is_c = path.suffix.lower() == ".c"
    block = False
    out = []
    for number, line in enumerate(text.splitlines(), 1):
        if is_c:
            kept = []
            i = 0
            while i < len(line):
                if block:
                    end = line.find("*/", i)
                    if end < 0:
                        i = len(line)
                    else:
                        block = False
                        i = end + 2
                elif line.startswith("/*", i):
                    block = True
                    i += 2
                elif line.startswith("//", i):
                    break
                else:
                    kept.append(line[i])
                    i += 1
            line = "".join(kept)
        else:
            line = line.split(";", 1)[0]
        if line.strip():
            out.append((number, line.strip()))
    return out


def source_census(report: dict) -> dict:
    units = report["translation_units"]
    generated_pins = []
    source_input_pins = []
    paths: set[Path] = set()
    generated_paths: set[Path] = set()
    for tu in units:
        generated = tu.get("generated_source")
        canonical = tu.get("source")
        if generated:
            path = ROOT / generated["path"].replace("\\", "/")
            p = pin(path, generated["sha256"])
            require(p["size"] == generated["size"], f"generated source size changed: {path}")
            generated_pins.append(p)
            paths.add(path)
            generated_paths.add(path)
        if canonical:
            path = ROOT / canonical["path"].replace("\\", "/")
            p = pin(path, canonical["sha256"])
            require(p["size"] == canonical["size"], f"canonical source size changed: {path}")
            source_input_pins.append(p)
            paths.add(path)

    token = re.compile(
        r"(?i)(?<![A-Za-z0-9_])(?:_?g_3DE[45]|3DE[45]h)(?![A-Za-z0-9_])")
    hits = []
    for path in sorted(paths, key=lambda p: p.as_posix().lower()):
        raw = path.read_bytes()
        text = raw.decode("latin1")
        for number, line in c_commentless(path, text):
            if token.search(line):
                hits.append({"path": path.resolve().relative_to(ROOT.resolve()).as_posix(),
                             "line": number, "text": line})

    generated_set_sha = sha("\n".join(
        f"{row['path']}|{row['sha256']}|{row['size']}" for row in
        sorted(generated_pins, key=lambda x: x["path"])).encode("utf-8"))
    source_input_set_sha = sha("\n".join(
        f"{row['path']}|{row['sha256']}|{row['size']}" for row in
        sorted(source_input_pins, key=lambda x: x["path"])).encode("utf-8"))

    expected_hits = {
        "src/S01/m3126.asm": {"_g_3DE4", "_g_3DE5"},
        "src/root/m1B4E.asm": {"_g_3DE4", "_g_3DE5"},
        "src/root/m1B73.asm": {"_g_3DE4"},
        "src/root/m1FD2.c": {"g_3DE4"},
        "src/root/m259D.c": {"g_3DE4"},
        "src/S10/m35F5.c": {"g_3DE4"},
        "build/source-only-dos/sources/U004.asm": {"_g_3DE4", "_g_3DE5"},
        "build/source-only-dos/sources/U086.asm": {"_g_3DE4", "_g_3DE5"},
        "build/source-only-dos/sources/U087.asm": {"_g_3DE4"},
        "build/source-only-dos/sources/U019.c": {"g_3DE4"},
        "build/source-only-dos/sources/U097.c": {"g_3DE4"},
        "build/source-only-dos/sources/U109.c": {"g_3DE4"},
    }
    observed: dict[str, set[str]] = {}
    for row in hits:
        observed.setdefault(row["path"], set()).update(
            match.group(0).lower() for match in token.finditer(row["text"]))
    require(set(observed) == set(expected_hits),
            f"overlapping-view source path set changed: missing={sorted(set(expected_hits)-set(observed))}, "
            f"unexpected={sorted(set(observed)-set(expected_hits))}")
    for path, names in expected_hits.items():
        for name in names:
            require(any(name.lower() in found for found in observed[path]),
                    f"expected overlap token {name} absent at {path}")

    # Classify every direct source alias reference so an additional byte/word
    # writer or an unfamiliar pointer-shaped alias fails closed. This catches
    # the overlapping high byte even where the token is spelled as g_3DE4.
    def alias_role(row: dict) -> str:
        line = " ".join(row["text"].lower().split()).rstrip(";")
        if line.startswith(("extrn ", "extern ", "public ")):
            return "declaration"
        if re.fullmatch(r"_g_3de[45]\s+db\s+0", line):
            return "zero_initializer"
        if line == "mov bx, word ptr _g_3de4":
            return "word_view_read"
        if line == "mov word ptr _g_3de4, ax":
            return "word_view_write"
        if line == "push word ptr _g_3de4":
            return "word_view_read"
        if line == "add bl, byte ptr ss:_g_3de5":
            return "high_byte_read"
        if re.fullmatch(r"extern (?:int|char) near g_3de4", line):
            return "declaration"
        if line in {
            "(*g_9128)(g_3de2, g_3de0, g_3de4)",
            "f_1ce2_046d(&fd_50f6_393c, g_3de2 | g_3de4)",
            "f_1ce2_046d(rect, g_3de4 | g_3de0)",
        }:
            return "c_value_read"
        raise SystemExit("S01 4220 scratch proof failed closed: unclassified g_3DE4/g_3DE5 alias: "
                         + row["path"] + ":" + str(row["line"]) + ": " + row["text"])

    for row in hits:
        row["role"] = alias_role(row)

    direct_numeric = [row for row in hits if re.search(r"(?i)\b3DE[45]h\b", row["text"])]
    require(not direct_numeric, f"unexpected direct numeric 3DE4/3DE5 memory operand: {direct_numeric}")
    # A source-wide write-shape check is limited to the two selected owner bytes.
    byte_writes = [row for row in hits if re.search(
        r"(?i)(?:mov\s+byte\s+ptr(?:\s+ss:)?\s*_?g_3DE5\s*,|\b_?g_3DE5\s*(?:=(?!=)|\+\+|--|\+=|-=))",
        row["text"])]
    require(not byte_writes, f"direct byte write to g_3DE5 requires reclassification: {byte_writes}")
    word_writes = [row for row in hits if re.search(
        r"(?i)mov\s+word\s+ptr\s+_?g_3DE4\s*,", row["text"])]
    require(len(word_writes) == 2 and {row["path"] for row in word_writes} ==
            {"build/source-only-dos/sources/U004.asm", "src/S01/m3126.asm"},
            f"word-alias writer set changed: {word_writes}")
    require(len([row for row in hits if row["role"] == "word_view_write"]) == 2,
            "overlapping g_3DE4 word writer was not exhaustively role-classified")

    target_tokens = [row for row in hits if "U004.asm" in row["path"]]
    owner_tokens = [row for row in hits if "U086.asm" in row["path"]]
    alias_tokens = list(hits)
    return {
        "scope": "At this historical SOURCE_ONLY_DOS report snapshot, every listed translation-unit source input and generated effective source is independently pinned; exact g_3DE4/g_3DE5 aliases and 3DE4h/3DE5h numeric view tokens only. The whole-report hash and TU counts are observational metadata, not the S01 candidate proof identity.",
        "translation_unit_count": len(units),
        "generated_effective_source_count": len(generated_paths),
        "strict_effective_binding_count": len(report.get("strict_static_audit", {})),
        "generated_source_set_sha256": generated_set_sha,
        "translation_unit_source_input_set_sha256": source_input_set_sha,
        "all_listed_source_pins_verified": True,
        "direct_source_pins": {"generated_effective_sources": sorted(generated_pins, key=lambda x: x["path"]),
                               "translation_unit_source_inputs": sorted(source_input_pins, key=lambda x: x["path"])},
        "overlap_source_hits": hits,
        "target_and_owner_hit_counts": {"S01_U004": len(target_tokens), "owner_U086": len(owner_tokens),
                                        "all_g3DE4_g3DE5_alias_hits": len(alias_tokens)},
        "direct_numeric_g3DE4_g3DE5_memory_operands": direct_numeric,
        "direct_byte_writes_to_g3DE5": byte_writes,
        "word_alias_writes_through_g3DE4": word_writes,
        "direct_alias_role_counts": dict(Counter(row["role"] for row in hits)),
        "interpretation": [
            "The complete provider initializes adjacent one-byte fields g_3DE4=0 and g_3DE5=0 at _DATA offsets 00C4h/00C5h.",
            "S01's word read/write through g_3DE4 spans exactly those two bytes; the word store is the sole direct writer and its mask is 70F0h.",
            "Thus the upper byte g_3DE5 is initialized zero, then written only by the upper half of the masked word store; reachable values are 00h,10h,20h,30h,40h,50h,60h,70h.",
            "All direct alias occurrences across the pinned canonical/effective source set are classified as declarations, initialization, direct byte/word reads/writes, or C value reads; no additional write-shaped or unclassified alias occurs. This does not claim arbitrary runtime pointer aliasing is absent.",
            "The adjacent far-word views begin at 3DE6h and 3DE8h; the complete provider object pins their starts after g_3DE5.",
        ],
    }


def fixup_key(row: dict) -> tuple:
    return tuple(row.get(k) for k in (
        "segment", "offset", "width", "loc", "self_relative", "target_kind", "target",
        "displacement", "frame_method", "frame_index", "target_method", "target_index",
        "frame_kind", "frame", "encoded_addend"))


def candidate_object(report: dict) -> dict:
    report_observations = {}
    for active in (ACTIVE_TARGET, ACTIVE_OWNER):
        row = next((r for r in report.get("translation_units", [])
                    if r.get("module") == active["module"]), None)
        report_observations[active["module"]] = bool(row
            and row.get("basename") == active["basename"]
            and row.get("source", {}).get("path", "").replace("\\", "/") == active["canonical_path"]
            and row.get("source", {}).get("sha256") == active["canonical_sha256"]
            and row.get("generated_source", {}).get("path", "").replace("\\", "/") == active["generated_path"]
            and row.get("generated_source", {}).get("sha256") == active["generated_sha256"]
            and row.get("object", {}).get("path", "").replace("\\", "/") == active["object_path"]
            and row.get("object", {}).get("sha256") == active["object_sha256"])
    target_path = ROOT / ACTIVE_TARGET["generated_path"]
    owner_path = ROOT / ACTIVE_OWNER["generated_path"]
    target_text = target_path.read_text(encoding="ascii")
    require(target_text.count(LITERAL) == 1, "current fully bound U004 literal site is not unique")
    candidate_text = target_text.replace(LITERAL, SYMBOLIC, 1)
    require(candidate_text.count("mov bh, byte ptr ss:[bx+_g_4220]") == 1
            and candidate_text.count("[bx+_g_4220]") == target_text.count("[bx+_g_4220]") + 1,
            "candidate did not add exactly one symbolic _g_4220 read")
    write_source(SOURCES / "U004_CONTROL.ASM", target_text)
    write_source(SOURCES / "U004_CANDIDATE.ASM", candidate_text)
    control_result = asm(target_text, ACTIVE_TARGET["basename"])
    owner_result = asm(owner_path.read_text(encoding="ascii"), ACTIVE_OWNER["basename"])
    candidate_result = asm(candidate_text, "S01CAND")
    require(sha(control_result.obj) == ACTIVE_TARGET["object_sha256"],
            "rebuilt current U004 control differs from its accepted current build object")
    require(sha(owner_result.obj) == ACTIVE_OWNER["object_sha256"],
            "rebuilt current U086 provider differs from its accepted current build object")
    control_model = OmfReader().read(control_result.obj, "current fully bound U004 control")
    candidate_model = OmfReader().read(candidate_result.obj, "S01 symbolic 4220 candidate")
    owner_model = OmfReader().read(owner_result.obj, "complete current U086 data provider")

    target_rows = [row for row in candidate_model.linker_fixups
                   if row.get("target_kind") == "external" and row.get("target") == "_g_4220"]
    new_rows = [row for row in target_rows if row["offset"] not in
                {f["offset"] for f in control_model.linker_fixups
                 if f.get("segment") == row.get("segment") and f.get("target") == "_g_4220"}]
    require(len(new_rows) == 1, f"candidate does not add exactly one _g_4220 fixup: {new_rows}")
    site = new_rows[0]
    require((site["segment"], site["width"], site["loc"], site["target_kind"], site["target"],
             site["displacement"], site["frame_kind"], site["frame"], site["encoded_addend"]) ==
            ("S01A_TEXT", 2, "offset16", "external", "_g_4220", 0, "group", "DGROUP", "0000"),
            f"new operand is not a zero-addend DGROUP OFFSET16 fixup: {site}")
    filtered = [row for row in candidate_model.linker_fixups if row is not site]
    require([fixup_key(row) for row in filtered] ==
            [fixup_key(row) for row in control_model.linker_fixups],
            "other ordered whole-object fixups differ")
    structure = {
        "segment_lengths_equal": control_model.segment_lengths == candidate_model.segment_lengths,
        "segment_definitions_equal": control_model.segment_defs == candidate_model.segment_defs,
        "groups_equal": control_model.groups == candidate_model.groups,
        "publics_equal": control_model.publics == candidate_model.publics,
        "local_publics_equal": control_model.local_publics == candidate_model.local_publics,
        "externals_equal": control_model.externals == candidate_model.externals,
        "external_scopes_equal": control_model.external_scopes == candidate_model.external_scopes,
        "local_externals_equal": control_model.local_externals == candidate_model.local_externals,
        "communals_equal": control_model.communals == candidate_model.communals,
    }
    require(all(structure.values()), f"candidate changes whole-object structure: {structure}")
    require(set(control_model.segments) == set(candidate_model.segments), "segment byte payload set changed")
    changed = {}
    for segment in control_model.segments:
        a, b = control_model.segment_bytes(segment), candidate_model.segment_bytes(segment)
        require(len(a) == len(b), f"payload length changed in {segment}")
        different = [i for i, (x, y) in enumerate(zip(a, b)) if x != y]
        if different:
            changed[segment] = different
    require(changed == {site["segment"]: [site["offset"], site["offset"] + 1]},
            f"byte differences are not exactly the displacement word: {changed}")
    before = control_model.segment_bytes(site["segment"])
    after = candidate_model.segment_bytes(site["segment"])
    require(before[site["offset"]:site["offset"] + 2] == b"\x20\x42"
            and after[site["offset"]:site["offset"] + 2] == b"\x00\x00",
            "changed field is not the literal 4220h displacement replaced by a zero addend")

    owner_publics = {row["name"]: row for row in owner_model.publics}
    for name, off in {"_g_3DE4": 0x00C4, "_g_3DE5": 0x00C5,
                      "_fd_55B3_3DE6": 0x00C6, "_fd_55B3_3DE8": 0x00C8,
                      "_g_41D0": 0x04B0, "_g_4220": 0x0500}.items():
        require(owner_publics.get(name, {}).get("segment") == "_DATA"
                and owner_publics[name]["offset"] == off,
                f"source owner public moved: {name} expected _DATA:{off:04X}")
    owner_data = owner_model.segment_bytes("_DATA")
    require(owner_model.segment_length("_DATA") == 1545, "complete owner _DATA extent changed")
    require(owner_data[owner_publics["_g_4220"]["offset"]:
                       owner_publics["_g_4220"]["offset"] + 16] == bytes(16),
            "the existing 16-byte _g_4220 row is no longer sixteen zero bytes")
    require(owner_publics["_g_4220"]["offset"] - owner_publics["_g_41D0"]["offset"] == 80,
            "_g_4220 is not the existing +80 view into _g_41D0")

    return {
        "observed_build_report_rows_match_direct_active_pins": report_observations,
        "control": {"source": pin(target_path, ACTIVE_TARGET["generated_sha256"]),
                    "object": object_pin(control_result.obj, OBJECTS / "U004_CONTROL.OBJ"),
                    "matches_current_build_object": True},
        "candidate": {"source_sha256": sha(candidate_text.encode("ascii")),
                      "object": object_pin(candidate_result.obj, OBJECTS / "U004_CANDIDATE.OBJ"),
                      "source_edit": {"before": LITERAL.strip(), "after": SYMBOLIC.strip().splitlines(),
                                      "count": 1}},
        "whole_object": {"structure_equal": structure, "all_unrelated_ordered_fixups_identical": True,
                         "only_changed_segment_bytes": changed,
                         "literal_before": before[site["offset"]:site["offset"]+2].hex(" "),
                         "unresolved_after": after[site["offset"]:site["offset"]+2].hex(" "),
                         "new_fixup": site, "passed": True},
        "owner": {"source": pin(owner_path, ACTIVE_OWNER["generated_sha256"]),
                  "object": object_pin(owner_result.obj, OBJECTS / "U086_COMPLETE_PROVIDER.OBJ"),
                  "matches_current_build_object": True,
                  "data_segment_length": owner_model.segment_length("_DATA"),
                  "public_offsets": {k: owner_publics[k]["offset"] for k in
                      ("_g_3DE4", "_g_3DE5", "_fd_55B3_3DE6", "_fd_55B3_3DE8", "_g_41D0", "_g_4220")},
                  "pattern_bank_length": 256, "g_4220_view_length": 16,
                  "g_4220_offset_in_bank": 80,
                  "reachable_max_offset_from_g_4220": 0x76,
                  "reachable_max_offset_in_bank": 80 + 0x76,
                  "bank_last_offset_exclusive": 256,
                  "reaches_within_existing_bank": 80 + 0x76 < 256,
                  "source_initializer_g_4220_first_16_bytes": owner_data[1280:1296].hex(" ")},
        "runtime_owner_model": owner_model,
        "owner_obj": owner_result.obj,
    }


def prefix_source() -> str:
    return "\n".join([
        "NULL segment word public 'BEGDATA'", "db 4 dup (0)",
        "public _wrong_frame_marker", "_wrong_frame_marker dw 0A5A5h", "NULL ends",
        "PREFIX segment word public 'DATA'", "public _prefix_start,_prefix_end",
        "_prefix_start label byte", "db 16 dup (0A5h)", "_prefix_end label byte", "PREFIX ends",
        "_DATA segment word public 'DATA'", "public _g_914C,_g_9154,_g_9128",
        "_g_914C label byte", "_g_9154 label byte", "_g_9128 label byte", "_DATA ends",
        "DGROUP group NULL,PREFIX,_DATA", "end", ""])


def checker_source(frame: str, addend: int = 0) -> str:
    assume = "DGROUP" if frame == "group" else "_DATA"
    expression = "_g_4220" + ("+1" if addend else "")
    lines = [
        "_DATA segment word public 'DATA'", "extrn _g_3DE4:word", "extrn _g_3DE5:byte",
        "extrn _g_4220:byte", "_DATA ends", "DGROUP group _DATA",
        "CHECK_TEXT segment word public 'CODE'", "assume cs:CHECK_TEXT,ds:DGROUP",
        "public _FrameProbe,_f_1FBD_0000", "_f_1FBD_0000 label byte",
        "_FrameProbe proc far", "push bx", "push cx", "push dx", "push si", "push di", "push ds", "push es",
        "mov byte ptr cs:Observation,0", "mov byte ptr cs:Observation+1,0",
        "mov word ptr cs:Observation+2,0", "mov word ptr cs:Observation+4,0",
        "mov bx,DGROUP", "mov ax,ss", "cmp ax,bx", "je StackOK", "or byte ptr cs:Observation+5,1", "StackOK:",
        "mov ax,ds", "cmp ax,bx", "je DataOK", "or byte ptr cs:Observation+5,2", "DataOK:",
        "mov ax,DGROUP", "mov es,ax", "assume es:DGROUP", "xor si,si", "StyleLoop:",
        "mov ax,si", "mov cl,4", "shl al,cl", "mov ah,al", "and ax,70F0h",
        "assume ss:DGROUP", "mov word ptr ss:_g_3DE4,ax", "xor di,di", "SelectorLoop:",
        "mov bx,di", "and bx,3", "shl bx,1", "add bl,byte ptr ss:_g_3DE5", "mov cx,8", "PhaseLoop:",
        "mov dl,byte ptr es:[bx+_g_4220]", "push bx", "call ReadOwnerByte", "mov al,bh", "pop bx",
        "cmp al,dl", "jne FormulaMismatch", "inc bx", "inc bx", "and bx,0F7h", "loop PhaseLoop",
        "inc di", "cmp di,4", "jb SelectorLoop", "inc si", "cmp si,8", "jb StyleLoop",
        "mov word ptr ss:_g_3DE4,0", "xor bx,bx", "mov cx,16", "ViewLoop:",
        "mov dl,byte ptr es:[bx+_g_4220]", "push bx", "call ReadOwnerByte", "mov al,bh", "pop bx",
        "cmp al,dl", "jne ViewMismatch", "inc bx", "loop ViewLoop", "jmp ProbeDone",
        "FormulaMismatch:", "mov byte ptr cs:Observation+1,1", "jmp SaveMismatch",
        "ViewMismatch:", "mov byte ptr cs:Observation+1,2", "SaveMismatch:",
        "mov byte ptr cs:Observation,1", "mov byte ptr cs:Observation+2,dl", "mov byte ptr cs:Observation+3,al",
        "mov byte ptr cs:Observation+4,bl", "ProbeDone:", "push ds", "push cs", "pop ds",
        "mov dx,offset Observation", "mov cx,6", "mov bx,1", "mov ah,40h", "int 21h", "pop ds",
        "cmp byte ptr cs:Observation,0", "jne ProbeFail", "xor ax,ax", "jmp ProbeReturn",
        "ProbeFail:", "mov ax,1", "ProbeReturn:", "pop es", "pop ds", "pop di", "pop si", "pop dx", "pop cx", "pop bx",
        "retf", "_FrameProbe endp", "assume ss:" + assume, "ReadOwnerByte proc near",
        f"mov bh,byte ptr ss:[bx+{expression}]", "ret", "ReadOwnerByte endp", "assume ss:nothing",
        "Observation db 0,0,0,0,0,0", "CHECK_TEXT ends", "end", ""]
    return "\n".join(lines)


def runtime_fixup_contrast(base_raw: bytes, changed_raw: bytes, target_frame: str,
                           target_addend: int) -> dict:
    base = OmfReader().read(base_raw, "group-frame runtime control")
    changed = OmfReader().read(changed_raw, "runtime negative control")
    require(base.segment_lengths == changed.segment_lengths and base.segment_defs == changed.segment_defs
            and base.groups == changed.groups and base.publics == changed.publics
            and base.externals == changed.externals,
            "runtime control source changed module structure")
    require(base.segment_bytes("CHECK_TEXT") == changed.segment_bytes("CHECK_TEXT"),
            "runtime frame/addend control changed instruction bytes")
    old, new = list(base.linker_fixups), list(changed.linker_fixups)
    require(len(old) == len(new), "runtime negative control changed the fixup count")
    deltas = [i for i, (a, b) in enumerate(zip(old, new)) if fixup_key(a) != fixup_key(b)]
    require(len(deltas) == 1, f"runtime contrast changes {len(deltas)} fixups, expected exactly one")
    old_site, new_site = old[deltas[0]], new[deltas[0]]
    require(old_site.get("segment") == new_site.get("segment") == "CHECK_TEXT"
            and old_site.get("target") == new_site.get("target") == "_g_4220"
            and old_site.get("offset") == new_site.get("offset"),
            f"runtime contrast changed a fixup other than the SS _g_4220 load: {old_site} => {new_site}")
    changed_fields = {key for key in set(old_site) | set(new_site)
                      if old_site.get(key) != new_site.get(key)}
    if target_frame == "_DATA":
        require(changed_fields <= {"frame_method", "frame_index", "frame_kind", "frame"}
                and old_site.get("frame") == "DGROUP" and new_site.get("frame") == "_DATA",
                f"wrong-frame control changed unexpected fixup fields: {changed_fields}")
    else:
        require(changed_fields == {"displacement"} and old_site.get("displacement") == 0
                and new_site.get("displacement") == target_addend,
                f"wrong-base control changed unexpected fixup fields: {changed_fields}")
    old_target = [row for row in base.linker_fixups if row.get("target") == "_g_4220"
                  and row.get("segment") == "CHECK_TEXT"]
    new_target = [row for row in changed.linker_fixups if row.get("target") == "_g_4220"
                  and row.get("segment") == "CHECK_TEXT"]
    require(len(old_target) == len(new_target) == 3,
            f"runtime fixture should have two expected-view and one candidate table fixups: {len(old_target)}, {len(new_target)}")
    # The expected ES view is fixed to DGROUP in both objects. Only the second,
    # SS-based source instruction is varied by the negative control.
    old_ss = [row for row in base.linker_fixups if row.get("target") == "_g_4220"
              and row.get("segment") == "CHECK_TEXT" and row.get("frame") == "DGROUP"]
    require(len(old_ss) == 3, "runtime fixture table fixup anchor set changed")
    new_all = list(changed.linker_fixups)
    candidates = [row for row in new_all if row.get("target") == "_g_4220"
                  and row.get("segment") == "CHECK_TEXT"]
    expected_groups = [row for row in candidates if row.get("frame_kind") == "group"
                       and row.get("frame") == "DGROUP"]
    expected_segments = [row for row in candidates if row.get("frame_kind") == "segment"
                         and row.get("frame") == "_DATA"]
    if target_frame == "DGROUP":
        require(len(expected_groups) == 3 and not expected_segments,
                f"runtime _g4220 fixups are not DGROUP framed: {candidates}")
    else:
        require(len(expected_groups) == 2 and len(expected_segments) == 1,
                f"runtime wrong-frame control changed more than SS candidate frame: {candidates}")
        require(expected_segments[0]["displacement"] == 0 and expected_segments[0]["encoded_addend"] == "0000",
                "wrong-frame control has unexpected displacement/addend")
    if target_addend:
        candidate = max(candidates, key=lambda row: row["offset"])
        require(candidate["displacement"] == target_addend
                and all(row["displacement"] == 0 for row in candidates if row is not candidate),
                f"wrong-base control lost the expected +{target_addend} displacement: {candidates}")
    else:
        require(all(row["encoded_addend"] == "0000" for row in candidates),
                f"runtime control has a nonzero table addend: {candidates}")
    return {"same_instruction_bytes": True, "segment_definitions_groups_publics_externals_equal": True,
            "expected_ES_group_view_preserved": True, "candidate_operand_fixups": candidates,
            "negative_changes_only_frame_or_addend": True,
            "exact_changed_fixup": {"before": old_site, "after": new_site,
                                     "changed_fields": sorted(changed_fields)}}


def parse_map(path: Path) -> dict:
    text = path.read_text(encoding="latin1", errors="replace")
    sections: dict[str, dict] = {}
    publics: dict[str, tuple[int, int]] = {}
    in_segments = in_origin = in_publics = False
    origin = None
    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith("Start  Stop   Length Name"):
            in_segments, in_origin, in_publics = True, False, False
            continue
        if line.startswith("Section# Fname"):
            in_segments = False
        if line == "Origin   Group":
            in_origin, in_segments, in_publics = True, False, False
            continue
        if line == "Address         Publics by Name":
            in_publics, in_origin, in_segments = True, False, False
            continue
        if line.startswith("Address         Publics by Value"):
            in_publics = False
        if in_segments:
            fields = line.split()
            if len(fields) >= 6 and fields[0].endswith("H") and fields[1].endswith("H"):
                try:
                    sections[fields[3]] = {"start": int(fields[0][:-1], 16),
                                           "stop": int(fields[1][:-1], 16),
                                           "length": int(fields[2][:-1], 16),
                                           "class": fields[4], "group": fields[5]}
                except ValueError:
                    pass
        elif in_origin and line:
            fields = line.split()
            if len(fields) == 2 and ":" in fields[0]:
                seg, off = fields[0].split(":", 1)
                try:
                    origin = {"segment": int(seg, 16), "offset": int(off, 16), "group": fields[1]}
                except ValueError:
                    pass
        elif in_publics and line:
            fields = line.split()
            if len(fields) >= 2 and ":" in fields[0]:
                seg, off = fields[0].split(":", 1)
                try:
                    publics[fields[1].upper()] = (int(seg, 16), int(off, 16))
                except ValueError:
                    pass
    require(origin is not None and all(name in sections for name in ("NULL", "PREFIX", "_DATA")),
            f"map sections or origin absent: {list(sections)} / {origin}")
    linear = origin["segment"] * 16 + origin["offset"]
    delta = sections["_DATA"]["start"] - linear
    g4220 = publics.get("_G_4220")
    g41d0 = publics.get("_G_41D0")
    return {"origin": origin, "sections": sections,
            "group_origin_linear": linear, "data_group_delta": delta,
            "g_4220_public": [f"{g4220[0]:04X}", f"{g4220[1]:04X}"] if g4220 else None,
            "g_41D0_public": [f"{g41d0[0]:04X}", f"{g41d0[1]:04X}"] if g41d0 else None,
            "public_offsets": {name: off for name, (_, off) in publics.items()
                               if name in {"_G_4220", "_G_41D0"}},
            "passed": (origin["group"].upper() == "DGROUP"
                       and sections["_DATA"]["group"].upper() == "DGROUP"
                       and delta >= 16 and g4220 is not None and g41d0 is not None)}


def tool_receipts(tc: dict) -> tuple[dict, dict]:
    copies = {}
    rows = {}
    for name in ("rtlink400", "rtlink610"):
        profile = tc["linkers"][name]
        source_root = Path(profile["directory"])
        dest = TOOL_COPIES / name
        dest.mkdir(parents=True, exist_ok=True)
        copied = {}
        for rel, digest in profile["files"].items():
            source = source_root / rel
            raw = source.read_bytes()
            require(sha(raw) == digest, f"pinned {name} file mismatch: {source}")
            target = dest / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
            copied[rel] = {"sha256": sha(raw), "size": len(raw)}
        present = {p.relative_to(dest).as_posix() for p in dest.rglob("*") if p.is_file()}
        require(present == set(profile["files"]), f"copied {name} linker tree has extra/missing files")
        copies[name] = {"path": dest.resolve().relative_to(ROOT.resolve()).as_posix(),
                        "files": copied}
        rows[name] = profile
    runtime = json.loads((ROOT / "layout/manifest.json").read_text(encoding="utf-8"))["runtime"]["libraries"]
    libraries = {}
    for name, row in runtime.items():
        source = Path(row["path"])
        raw = source.read_bytes()
        require(sha(raw) == row["sha256"], f"runtime library pin mismatch: {source}")
        libraries[name] = {"path": str(source), "sha256": sha(raw), "size": len(raw)}
    runner = tc["runners"]["dosbox-x"]
    runner_path = Path(runner["path"])
    require(sha(runner_path.read_bytes()) == runner["sha256"], "DOSBox-X pin mismatch")
    return rows, {"pinned_linker_tool_copies": copies,
                  "runtime_libraries": libraries,
                  "dosbox_x": {"path": str(runner_path), "sha256": runner["sha256"],
                               "size": runner_path.stat().st_size}}


def runtime_source_pins(report: dict, target_src: str, owner_src: str) -> dict:
    require(target_src == ACTIVE_TARGET["generated_path"]
            and owner_src == ACTIVE_OWNER["generated_path"],
            "directly pinned active source paths changed")
    return {"target_canonical_source": pin(ROOT / ACTIVE_TARGET["canonical_path"],
                                          ACTIVE_TARGET["canonical_sha256"]),
            "target_generated_control": pin(ROOT / ACTIVE_TARGET["generated_path"],
                                              ACTIVE_TARGET["generated_sha256"]),
            "target_current_build_object": pin(ROOT / ACTIVE_TARGET["object_path"],
                                                 ACTIVE_TARGET["object_sha256"]),
            "owner_canonical_source": pin(ROOT / ACTIVE_OWNER["canonical_path"],
                                         ACTIVE_OWNER["canonical_sha256"]),
            "owner_generated_provider": pin(ROOT / ACTIVE_OWNER["generated_path"],
                                              ACTIVE_OWNER["generated_sha256"]),
            "owner_current_build_object": pin(ROOT / ACTIVE_OWNER["object_path"],
                                                ACTIVE_OWNER["object_sha256"])}


def effective_source_chain(report: dict) -> dict:
    """Replay the three accepted S01 source/frame packets to the exact active U004."""
    import dos_source_bindings

    observed_current = next((row for row in report.get("translation_units", [])
                             if row.get("module") == TARGET_MODULE), None)
    packet_paths = [
        "work/source-only-dos/source-bindings-v1.json",
        "work/source-only-dos/driver-ss-frame-bindings-v1.json",
        "work/source-only-dos/driver-local-frame-bindings-v1.json",
    ]
    packet_pins = [pin(ROOT / path) for path in packet_paths]
    packets = [json.loads((ROOT / path).read_text(encoding="utf-8")) for path in packet_paths]
    base, external, local = packets
    require(base.get("schema") == "simant-dos-source-bindings-v1"
            and base.get("category") == "REVIEWED_SOURCE_LINK_BINDING",
            "S01 base binding packet is not the reviewed packet")
    require(external.get("schema") == "simant-driver-ss-frame-binding-extension-v1"
            and external.get("status") == "ROOT_REVIEWED",
            "S01 external-frame packet is not the reviewed extension")
    require(local.get("schema") == "simant-dos-driver-local-frame-bindings-v1"
            and local.get("status") == "ROOT_REVIEWED",
            "S01 local-frame packet is not the reviewed extension")
    require(external.get("extends_packet") == packet_pins[0],
            "external-frame packet does not extend the exact base packet")
    require(local.get("extends_packets") == packet_pins[:2],
            "local-frame packet does not extend the exact base and external packets")

    entries = []
    for packet in packets:
        matches = [row for row in packet.get("bindings", []) if row.get("module") == TARGET_MODULE]
        require(len(matches) == 1, "each S01 binding packet must have one S01:3126 entry")
        entries.append(matches[0])
    base_entry, external_entry, local_entry = entries
    canonical_path = ACTIVE_TARGET["canonical_path"]
    require(canonical_path == "src/S01/m3126.asm"
            and all(entry.get("source", "").replace("\\", "/") == canonical_path
                    and entry.get("source_sha256") == ACTIVE_TARGET["canonical_sha256"]
                    for entry in entries),
            "S01 binding packets are not tied to the directly pinned canonical S01 source")
    require(external_entry.get("extends_module_binding") == TARGET_MODULE
            and external_entry.get("apply_after") ==
                "work/source-only-dos/source-bindings-v1.json binding for this module"
            and local_entry.get("extends_module_binding") == TARGET_MODULE,
            "S01 frame packet application order or module identity changed")

    def merge(previous: dict, extension: dict) -> dict:
        combined = dict(previous)
        keys = ("edits", "exports", "relocations", "reframes", "communals")
        if "local_reframes" in previous or "local_reframes" in extension:
            keys += ("local_reframes",)
        if "segment_corrections" in previous or "segment_corrections" in extension:
            keys += ("segment_corrections",)
        for key in keys:
            combined[key] = previous.get(key, []) + extension.get(key, [])
        if extension.get("reframes"):
            combined["frame_review"] = extension["frame_review"]
        return combined

    canonical = (ROOT / canonical_path).read_bytes().decode("latin1").replace("\r\n", "\n")
    base_text = dos_source_bindings.apply_binding(canonical, base_entry)
    external_text = dos_source_bindings.apply_binding(base_text, external_entry)
    effective_text = dos_source_bindings.apply_binding(external_text, local_entry)
    generated_path = ROOT / ACTIVE_TARGET["generated_path"]
    generated_text = generated_path.read_text(encoding="latin1")
    require(effective_text == generated_text,
            "replayed canonical->base->external-frame->local-frame text differs from active U004")

    base_effective_binding = merge(base_entry, external_entry)
    base_effective_hash = sha(json.dumps(base_effective_binding, sort_keys=True,
                                         separators=(",", ":")).encode("utf-8"))
    require(local_entry.get("extends_effective_binding_sha256") == base_effective_hash,
            "local-frame extension does not pin the exact base+external effective binding")
    final_binding = merge(base_effective_binding, local_entry)
    report_binding_matches = bool(observed_current
                                  and observed_current.get("source_binding") == final_binding)
    counts = {
        "base_binding_edits": len(base_entry.get("edits", [])),
        "external_frame_edits": len(external_entry.get("edits", [])),
        "external_frame_sites": len(external_entry.get("reframes", [])),
        "local_frame_edits": len(local_entry.get("edits", [])),
        "local_frame_sites": len(local_entry.get("local_reframes", [])),
        "effective_edit_rows": len(final_binding.get("edits", [])),
    }
    require(counts == {"base_binding_edits": 3, "external_frame_edits": 18,
                       "external_frame_sites": 36, "local_frame_edits": 2,
                       "local_frame_sites": 2, "effective_edit_rows": 23},
            f"S01 source/frame packet counts changed: {counts}")

    contract_rows = [
        external["contract"], external["runtime_contract"], local["runtime_contract"],
    ]
    contracts = []
    for row in contract_rows:
        path = row["path"].replace("\\", "/")
        contract_pin = pin(ROOT / path, row["sha256"])
        require(contract_pin["size"] == row["size"], f"review contract size changed: {path}")
        contracts.append(contract_pin)
    tool_pins = [pin(ROOT / path) for path in (
        "tools/source_only_dos.py", "tools/dos_source_bindings.py", "tools/compiler.py",
        "tools/omf.py", "layout/manifest.json", "layout/toolchain.json")]
    pattern_packet_path = "work/source-only-dos/pattern-bank-bindings-v1.json"
    pattern_packet_pin = pin(ROOT / pattern_packet_path)
    pattern_packet = json.loads((ROOT / pattern_packet_path).read_text(encoding="utf-8"))
    pattern_contract_row = pattern_packet["runtime_contract"]
    pattern_contract_path = pattern_contract_row["path"].replace("\\", "/")
    pattern_contract_pin = pin(ROOT / pattern_contract_path, pattern_contract_row["sha256"])
    require(pattern_contract_pin["size"] == pattern_contract_row["size"],
            "source-owner pattern-bank contract size changed")
    pattern_contract = json.loads((ROOT / pattern_contract_path).read_text(encoding="utf-8"))
    owner_contract = pattern_contract.get("owner", {})
    require(pattern_contract.get("root_reviewed") and pattern_contract.get("all_required_checks_pass")
            and owner_contract == {"name": "_g_41D0", "segment": "_DATA", "offset": 1200,
                                  "length": 256, "interior": "_g_4220", "interior_delta": 80},
            "existing _g_41D0/_g_4220 owner contract is not the reviewed 256-byte bank")
    pattern_probe = pattern_contract["probe_source"]
    pattern_probe_path = pattern_probe["path"].replace("\\", "/")
    pattern_probe_pin = pin(ROOT / pattern_probe_path, pattern_probe["sha256"])
    owner_contract_pins = {"pattern_bank_bindings": pattern_packet_pin,
                           "pattern_bank_contract": pattern_contract_pin,
                           "pattern_bank_probe": pattern_probe_pin}
    return {
        "canonical_source": pin(ROOT / canonical_path, ACTIVE_TARGET["canonical_sha256"]),
        "active_generated_control": pin(generated_path, ACTIVE_TARGET["generated_sha256"]),
        "current_build_object": pin(ROOT / ACTIVE_TARGET["object_path"], ACTIVE_TARGET["object_sha256"]),
        "packet_pins": packet_pins,
        "packet_entries": entries,
        "review_contract_pins": contracts,
        "generation_tool_pins": tool_pins,
        "source_owner_contract": {"contract": owner_contract,
                                   "root_reviewed": True,
                                   "all_required_checks_pass": True,
                                   "pins": owner_contract_pins},
        "application_order": [
            "canonical src/S01/m3126.asm",
            "source-bindings-v1 S01:3126",
            "driver-ss-frame-bindings-v1 S01:3126 (36 external frames)",
            "driver-local-frame-bindings-v1 S01:3126 (2 local frames)",
        ],
        "packet_merge": {"effective_binding_sha256": sha(json.dumps(
            final_binding, sort_keys=True, separators=(",", ":")).encode("utf-8")),
            "matches_observed_build_report_binding_row": report_binding_matches,
            "base_plus_external_binding_sha256": base_effective_hash,
            "local_extension_parent_hash_matches": True,
            "counts": counts},
        "replayed_source": {"effective_text_sha256": sha(effective_text.encode("latin1")),
                            "active_generated_sha256": ACTIVE_TARGET["generated_sha256"],
                            "exact_text_match": True},
        "observed_build_report_S01_row": ({"module": TARGET_MODULE,
            "canonical_source": observed_current.get("source") if observed_current else None,
            "generated_source": observed_current.get("generated_source") if observed_current else None,
            "object": observed_current.get("object") if observed_current else None,
            "binding_matches_packet_merge": report_binding_matches} if observed_current else None),
        "packet_entries_are_full": True,
    }


def run_case(linker_name: str, linker: dict, runtime_pins: dict,
             objects: dict[str, bytes], checker_name: str) -> dict:
    directory = CASES / linker_name / checker_name
    directory.mkdir(parents=True, exist_ok=True)
    for name in ("OWNER.OBJ", "SETUP.OBJ", "CRT.OBJ", checker_name.upper() + ".OBJ",
                 "PROBE.EXE", "PROBE.MAP", "LINK.LOG", "RUN.LOG", "OBS.BIN"):
        (directory / name).unlink(missing_ok=True)
    mapping = {"OWNER.OBJ": "OWNER.OBJ", "SETUP.OBJ": "SETUP.OBJ", "CRT.OBJ": "CRT.OBJ",
               checker_name.upper() + ".OBJ": checker_name.upper() + ".OBJ"}
    for source_name, dest_name in mapping.items():
        raw = objects[source_name]
        (directory / dest_name).write_bytes(raw)
    manifest = json.loads((ROOT / "layout/manifest.json").read_text(encoding="utf-8"))
    runtime_rows = manifest["runtime"]["libraries"]
    for key, dest_name in (("llibcr.lib", "LLIBCR.LIB"), ("libh.lib", "LIBH.LIB")):
        row = runtime_rows[key]
        raw = Path(row["path"]).read_bytes()
        require(sha(raw) == row["sha256"], f"runtime library changed before case: {key}")
        (directory / dest_name).write_bytes(raw)
    lib_name = Path(linker["executable"]).name
    (directory / "PROBE.LNK").write_bytes("\r\n".join((
        "OUTPUT PROBE", "MAP = PROBE S,N,A,L", "NODEFLIB", "LIBRARY LLIBCR, LIBH",
        "FILE SETUP", "FILE OWNER", "FILE CRT", "FILE " + checker_name.upper(), "")).encode("ascii"))
    (directory / "RTLINK.CFG").write_bytes(b"SYNTAX = FREEFORMAT\r\n")
    batch = (f"@echo off\r\nD:\\{lib_name} @PROBE.LNK < NUL > LINK.LOG\r\n"
             "if not exist PROBE.EXE goto noexe\r\n"
             "PROBE.EXE > OBS.BIN\r\necho EXECUTED > RUN.LOG\r\ngoto done\r\n"
             ":noexe\r\necho NOEXE > RUN.LOG\r\n:done\r\n")
    (directory / "RUN.BAT").write_bytes(batch.encode("ascii"))
    config = []
    for section, options in runtime_pins["dosbox_conf"].items():
        config.append("[" + section + "]")
        config.extend(f"{key}={value}" for key, value in options.items())
    tool_dir = TOOL_COPIES / linker_name
    config += ["[autoexec]", f'mount c "{directory}"', f'mount d "{tool_dir}" -ro',
               "c:", "call RUN.BAT", "exit"]
    conf = directory / "dosbox.conf"
    conf.write_text("\n".join(config) + "\n", encoding="utf-8")
    env = dict(os.environ)
    env.update(SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy")
    runner = subprocess.run([runtime_pins["dosbox_path"], "-conf", str(conf),
                             "-fastlaunch", "-exit", "-nomenu"], cwd=directory,
                            env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                            timeout=120, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    observed = (directory / "OBS.BIN").read_bytes() if (directory / "OBS.BIN").exists() else b""
    run_log = (directory / "RUN.LOG").read_text(encoding="latin1").strip() \
        if (directory / "RUN.LOG").exists() else "NO_RUN_LOG"
    link_log = (directory / "LINK.LOG").read_text(encoding="latin1", errors="replace") \
        if (directory / "LINK.LOG").exists() else "NO_LINK_LOG"
    map_path = directory / "PROBE.MAP"
    map_info = parse_map(map_path) if map_path.is_file() else {"passed": False, "missing": True}
    require(runner.returncode == 0 and run_log == "EXECUTED" and len(observed) == 6
            and map_info.get("passed"),
            f"link/run failed {linker_name}/{checker_name}: rc={runner.returncode}, run={run_log}, "
            f"obs={observed.hex()}, map={map_info}, log={link_log[-1500:]}")
    mismatch = observed[0] != 0
    expected_fail = checker_name in {"SOBSEG", "SOBPLUS"}
    require(mismatch == expected_fail,
            f"runtime behavior unexpected {linker_name}/{checker_name}: {observed.hex()}")
    return {"linker": linker_name, "checker": checker_name, "runner_returncode": runner.returncode,
            "run_log": run_log, "observation_hex": observed.hex(),
            "expected": "FAIL" if expected_fail else "PASS",
            "actual": "FAIL" if mismatch else "PASS", "passed": True,
            "dgroup_data_shift": map_info["data_group_delta"],
            "actual_DS_SS_DGROUP": observed[5] == 0,
            "mismatch": ({"stage": observed[1], "expected_byte": observed[2],
                          "actual_byte": observed[3], "offset": int.from_bytes(observed[4:6], "little")}
                         if mismatch else None),
            "map": map_info,
            "link_log_tail": link_log[-800:],
            "artifacts": {name: pin(directory / name) for name in
                          ("PROBE.MAP", "OBS.BIN", "RUN.LOG", "LINK.LOG", "PROBE.EXE")}}


def runtime_proofs(owner_result: dict, source_pins: dict) -> dict:
    tc = compiler.toolchain()
    linker_rows, support_pins = tool_receipts(tc)
    dosbox = tc["runners"]["dosbox-x"]
    support_pins["dosbox_path"] = dosbox["path"]
    support_pins["dosbox_conf"] = dosbox["conf"]
    setup_text = prefix_source()
    check_texts = {"SOBGROUP": checker_source("group"),
                   "SOBSEG": checker_source("segment"),
                   "SOBPLUS": checker_source("group", 1)}
    write_source(SOURCES / "SHIFTED_SETUP.ASM", setup_text)
    setup_result = asm(setup_text, "SETUP")
    main_source = "extern int far FrameProbe(void);\nint main(void) { return FrameProbe(); }\n"
    write_source(SOURCES / "CRT.C", main_source)
    main_result = compiler.compile_c(main_source, "msc600ax", ["/AL", "/Os", "/Zi"],
                                     basename="CRT", keep=False)
    require(main_result.ok, "MSC 6.00AX CRT main failed: " + main_result.log)
    checker_results = {}
    for name, text in check_texts.items():
        write_source(SOURCES / (name + ".ASM"), text)
        checker_results[name] = asm(text, name)
    checker_contrasts = {
        "wrong_frame": runtime_fixup_contrast(checker_results["SOBGROUP"].obj,
                                              checker_results["SOBSEG"].obj, "_DATA", 0),
        "wrong_base_plus_one": runtime_fixup_contrast(checker_results["SOBGROUP"].obj,
                                                      checker_results["SOBPLUS"].obj, "DGROUP", 1),
    }
    owner_model = owner_result["runtime_owner_model"]
    owner_bytes = owner_model.segment_bytes("_DATA")
    owner_publics = {row["name"]: row["offset"] for row in owner_model.publics}
    base = owner_publics["_g_4220"]
    bank_base = owner_publics["_g_41D0"]
    reachable = [16 * style + 2 * phase for style in range(8) for phase in range(4)]
    require(max(reachable) == 0x76 and min(reachable) == 0,
            "effective selector/state domain arithmetic changed")
    expected_values = [owner_bytes[base + displacement] for displacement in reachable]
    expected_view = owner_bytes[base:base + 16]
    require(len(expected_values) == 32 and len(expected_view) == 16,
            "source owner test windows changed length")
    require(owner_bytes[base:base + 16] == bytes(16), "_g4220 source view no longer has zero initializer")
    require(owner_bytes[base + 16] == 0x44,
            "the actual adjacent pattern row no longer discriminates the +1 view-edge contrast")
    run_objects = {"OWNER.OBJ": owner_result["owner_obj"],
                   "SETUP.OBJ": setup_result.obj, "CRT.OBJ": main_result.obj}
    for name, result in checker_results.items():
        run_objects[name + ".OBJ"] = result.obj
        object_pin(result.obj, OBJECTS / (name + ".OBJ"))
    object_pin(setup_result.obj, OBJECTS / "SETUP.OBJ")
    object_pin(main_result.obj, OBJECTS / "CRT.OBJ")

    outputs = []
    for linker_name, linker in linker_rows.items():
        for checker in ("SOBGROUP", "SOBSEG", "SOBPLUS"):
            row = run_case(linker_name, linker, support_pins, run_objects, checker)
            outputs.append(row)
            print(linker_name, checker, row["actual"], row["observation_hex"],
                  "DGROUP+", row["dgroup_data_shift"], flush=True)
    return {
        "scope": "Test-only startup/checker against the complete accepted root:1B4E provider object built from the current generated source; no table bytes or provider allocation synthesized.",
        "owner_data_expectations": {
            "_g_4220_view_16_bytes": expected_view.hex(" "),
            "_g_4220_view_first_16_sha256": sha(expected_view),
            "adjacent_byte_at_view_plus_16": f"{owner_bytes[base+16]:02X}",
            "reachable_test_offsets": reachable,
            "reachable_source_bank_values": [f"{value:02X}" for value in expected_values],
            "source_bank_absolute_window": {"start": bank_base, "exclusive_end": bank_base + 256},
            "max_read_bank_offset": base - bank_base + 0x76,
            "within_existing_bank": base - bank_base + 0x76 < 256,
        },
        "runtime_checker_fixup_contrasts": checker_contrasts,
        "cases": outputs,
        "case_count": len(outputs),
        "all_required_cases_pass": len(outputs) == 6 and all(row["passed"] for row in outputs),
        "tools": support_pins,
        "source_pins": source_pins,
        "test_only_allocation": "One 16-byte PREFIX segment shifts DGROUP in the isolated link fixture. Empty public labels resolve the provider's unrelated unexecuted imports; they allocate no storage. The complete U086 provider is used as-is.",
    }


def main() -> int:
    for path in (OUT, SOURCES, OBJECTS, CASES, TOOL_COPIES):
        path.mkdir(parents=True, exist_ok=True)
    report_path = ROOT / "build/source-only-dos/build-report.json"
    report_raw = report_path.read_bytes()
    report = json.loads(report_raw)
    census = source_census(report)
    source_chain = effective_source_chain(report)
    owner_result = candidate_object(report)
    source_pins = runtime_source_pins(report, TARGET_SOURCE, OWNER_SOURCE)
    runtime = runtime_proofs(owner_result, source_pins)
    manifest_path = ROOT / "layout/manifest.json"
    toolchain_path = ROOT / "layout/toolchain.json"
    runner_path = Path(__file__).resolve()
    new_fixup = owner_result["whole_object"]["new_fixup"]
    binding_doc = {
        "schema": "simant-dos-s01-pattern-4220-binding-candidate-v18",
        "status": "UNADMITTED_SCRATCH_CANDIDATE",
        "root_reviewed": False,
        "module": TARGET_MODULE,
        "current_effective_control": source_chain,
        "candidate_extension": {
            "applies_after": "the exact active generated U004 source reconstructed by current source-bindings, driver-ss-frame, and driver-local-frame packets",
            "canonical_source_edit": False,
            "generated_source_edit": {
                "before": LITERAL.strip(),
                "after": SYMBOLIC.strip().splitlines(),
                "count": 1,
                "effective_control_source_sha256": ACTIVE_TARGET["generated_sha256"],
                "candidate_source_sha256": owner_result["candidate"]["source_sha256"],
            },
            "new_relocation": new_fixup,
            "existing_external_declaration": {"path": "src/S01/m3126.asm", "line": 44,
                                               "name": "_g_4220", "type": "byte"},
            "existing_owner": {
                "provider_module": OWNER_MODULE,
                "canonical_source": source_pins["owner_canonical_source"],
                "generated_provider": source_pins["owner_generated_provider"],
                "existing_owner_contract": source_chain["source_owner_contract"],
                "data_public_offsets": owner_result["owner"]["public_offsets"],
                "_g_41D0_bank_length": owner_result["owner"]["pattern_bank_length"],
                "_g_4220_relative_offset": owner_result["owner"]["g_4220_offset_in_bank"],
                "_g_4220_existing_view_length": owner_result["owner"]["g_4220_view_length"],
                "new_storage_or_allocation": False,
            },
            "whole_object_comparison": owner_result["whole_object"],
            "provider_object_matches_active_build": owner_result["owner"]["matches_current_build_object"],
            "runtime_cases": runtime["cases"],
        },
        "review_limits": [
            "This packet proposes a one-site source binding only; root_reviewed remains false.",
            "Do not treat the candidate as canonical, admitted, or a SOURCE_ONLY_DOS gate resolution.",
            "The existing 8ED8h monochrome base/frame/extent questions remain outside this candidate.",
        ],
    }
    PACKAGE.mkdir(parents=True, exist_ok=True)
    BINDING_PATH.write_text(json.dumps(binding_doc, indent=2) + "\n", encoding="utf-8")
    binding_pin = pin(BINDING_PATH)
    report_obj = {
        "schema": "dos-s01-pattern-4220-proof-candidate-v18",
        "status": "BOUNDED_SCRATCH_PROOF_CANDIDATE_PENDING_ROOT_REVIEW",
        "root_reviewed": False,
        "scope": "One candidate S01:3126 read at canonical line 792 / generated U004 line 800. The canonical-to-effective S01 binding chain is replayed and matched exactly to the active U004, followed by a one-site candidate extension; all direct g_3DE4/g_3DE5 byte/word alias occurrences are classified.",
        "build_report_observation": {"pin": pin(report_path, sha(report_raw)),
                                     "translation_unit_count": len(report["translation_units"]),
                                     "strict_effective_binding_count": len(report.get("strict_static_audit", {})),
                                     "role": "historical run input and source-list observation only; S01 proof invariants are directly pinned by packet/source/object hashes"},
        "input_pins": {"manifest": pin(manifest_path), "toolchain": pin(toolchain_path),
                       "compiler": pin(ROOT / "tools/compiler.py"),
                       "omf_reader": pin(ROOT / "tools/omf.py"),
                       "scratch_probe": pin(runner_path),
                       "binding_packets": source_chain["packet_pins"],
                       "binding_review_contracts": source_chain["review_contract_pins"],
                       "binding_generation_tools": source_chain["generation_tool_pins"],
                       "pattern_bank_owner_evidence": source_chain["source_owner_contract"]["pins"],
                       "canonical_S01": source_pins["target_canonical_source"],
                       "generated_S01_control": source_pins["target_generated_control"],
                       "canonical_provider": source_pins["owner_canonical_source"],
                       "generated_complete_provider": source_pins["owner_generated_provider"]},
        "effective_S01_binding_chain": source_chain,
        "g3de5_overlap_census": census,
        "input_policy": {"original_game_executable_used": False,
                         "original_executable_or_fragment_compiler_inputs": [],
                         "original_executable_or_fragment_linker_inputs": [],
                         "original_game_code_or_data_bytes_used": 0,
                         "owner_storage_added_by_candidate": False,
                         "test_only_shift_storage": "A separate 16-byte PREFIX in the isolated linker fixture shifts DGROUP; it does not alter or extend the real provider."},
        "unadmitted_candidate_bindings": binding_pin,
        "symbolic_whole_object_candidate": {k: v for k, v in owner_result.items()
                                             if k != "runtime_owner_model" and k != "owner_obj"},
        "shifted_dgroup_runtime": runtime,
        "all_required_checks_pass": bool(owner_result["whole_object"]["passed"]
                                         and runtime["all_required_cases_pass"]),
        "claim_limits": [
            "No production/canonical/admission files are modified.",
            "The symbolic source is a one-site candidate derived from the fully bound generated U004 control; no historical TU ownership or source-only debt reduction is claimed.",
            "The build report hash and whole-graph TU counts are retained as historical run observations; direct S01 canonical/effective/object hashes and packet replay are the proof identity anchors.",
            "Runtime checks validate the candidate relocation and bounded read interval against the real existing source bank; they do not prove arbitrary far-pointer aliasing is absent.",
            "The wider 8ED8h mono base/frame/extent work remains separate and unresolved.",
        ],
    }
    owner_result["runtime_owner_model"] = None
    owner_result["owner_obj"] = None
    receipt_path = RECEIPT_PATH
    receipt_path.write_text(json.dumps(report_obj, indent=2) + "\n", encoding="utf-8")
    review = [
        "# S01 4220h binding candidate v18 (pending review)", "",
        "This is a bounded, unadmitted one-site binding candidate. The current S01 control is reconstructed from the canonical source through the exact accepted source-binding, external-frame, and local-frame packets. The rebuilt control object matches the directly pinned active U004 object; the build report is retained as an observational run input.", "",
        f"- Receipt: `{receipt_path.relative_to(ROOT).as_posix()}` (`{sha(receipt_path.read_bytes())}`).",
        f"- Candidate binding packet: `{BINDING_PATH.relative_to(ROOT).as_posix()}` (`{binding_pin['sha256']}`). Root review is false.",
        f"- Apply-chain counts: 3 base edits; 18 external-frame edits/36 frame sites; 2 local-frame edits/sites. Replayed text equals current U004 exactly; the observed report row binding merge check is {source_chain['packet_merge']['matches_observed_build_report_binding_row']}.",
        f"- U004 control object reproduces the current build object; candidate adds one DGROUP-framed OFFSET16 fixup at `S01A_TEXT:{report_obj['symbolic_whole_object_candidate']['whole_object']['new_fixup']['offset']:04X}`.",
        "- Candidate module extents, segment definitions, groups, publics, externals, and every other ordered fixup match the U004 control. Only the displacement word changes from `20 42` to `00 00`.",
        f"- The complete alias census classified {sum(census['direct_alias_role_counts'].values())} direct `_g_3DE4/_g_3DE5` occurrences across {len({row['path'] for row in census['overlap_source_hits']})} pinned source files; only the canonical/effective setter writes through the overlapping word, and no direct byte writer or unclassified alias remains. Its `70F0h` mask bounds `_g_3DE5` to 00h..70h by 10h.",
        "- The selector contributes 0,2,4,6; the loop transition `+2; AND 00F7h` cycles within that phase band for any positive count, so the largest displacement from `_g_4220` is 76h.",
        "- `_g_4220` is the existing 16-byte zero row at `_g_41D0+80`; the reachable addresses continue into following existing rows but remain below the bank's 256-byte end. The complete owner U086 source/object is rebuilt and matched to the directly pinned active provider source/object.",
        "- RTLink 4.00 and 6.10 each pass the shifted-DGROUP group-frame case and detect both a segment-frame negative and a +1 base negative. The boundary contrast uses the actual adjacent 44h row byte after the existing 16-byte zero view.",
        "- The fixture has one separate 16-byte prefix solely to shift DGROUP. Empty support labels satisfy the complete provider's unrelated, unexecuted imports; they add no owner storage.",
        f"- Candidate linker/runtime outputs are in `{OUT.relative_to(ROOT).as_posix()}`; the full root:1B4E provider is used as-is, and the checker adds only a 16-byte shift prefix, no owner storage.",
        "- No canonical or production build input is edited; this packet does not resolve the wider numeric-address gate. The 8ED8h mono base/frame/extent work remains open.", ""
    ]
    REVIEW_PATH.write_text("\n".join(review), encoding="utf-8")
    print("4220 owner proof", report_obj["all_required_checks_pass"],
          "runtime cases", runtime["case_count"], "receipt", receipt_path, flush=True)
    return 0 if report_obj["all_required_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
