"""Bounded ownership/liveness audit for the legacy DOS icon pointer.

Run from the repository root:
    python build/workers/dos_icon_handle_owner_v33/audit_v33.py

Reads the pinned original for disassembly/xref analysis and the 127 canonical plus
29 strict-effective source set. Writes only receipt-v33.json and review-v33.md here.
No original bytes are copied into the outputs.
"""
from __future__ import annotations

import hashlib
import json
import re
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / "tools"))

import dataref  # noqa: E402
import exe  # noqa: E402
import functions  # noqa: E402
import modules  # noqa: E402
import symbols as symbols_mod  # noqa: E402

try:
    from capstone import Cs, CS_ARCH_X86, CS_MODE_16, CS_OP_IMM
except ImportError:
    sys.path.insert(0, "C:/tools/capstone-5.0.3")
    from capstone import Cs, CS_ARCH_X86, CS_MODE_16, CS_OP_IMM


TARGET_DATA = "fd_50F6_46D2"
TARGET_FUNCS = ("f_208F_027F", "f_208F_02F0")
RELATED_FUNC = "f_1C62_06A6"
TARGET_SIZE = 4
STRICT_INDEX = ROOT / "work/source-only-dos/static-completeness/index-v1.json"
CURRENT_188_EXTFIXUPS = ROOT / "work/source-only-dos/structural-audits-v32/heap-v38/extdef-census-v38.json"
PREVIOUS_RECEIPTS = (
    ROOT / "work/source-only-dos/structural-audits-v27/dos_delay_word_owner_v33/source-addendum-v33.json",
    ROOT / "work/source-only-dos/structural-audits-v28/readonly-words/receipt-v33.json",
    ROOT / "work/source-only-dos/structural-audits-v28/readonly-words/disasm-sweep-v33.json",
    ROOT / "work/source-only-dos/structural-audits-v28/menu/review-v34.md",
)
WRITE_MNEMONICS = {
    "mov", "add", "adc", "sub", "sbb", "and", "or", "xor", "inc", "dec",
    "not", "neg", "shl", "sal", "shr", "sar", "rol", "ror", "rcl", "rcr",
    "xchg", "xadd", "cmpxchg", "btc", "btr", "bts", "stosb", "stosw", "stosd",
    "movsb", "movsw", "movsd",
}
STRING_WRITES = {"stosb", "stosw", "stosd", "movsb", "movsw", "movsd"}


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def pin(path: Path, expected: str | None = None) -> dict:
    raw = path.read_bytes()
    digest = sha(raw)
    if expected is not None and digest != expected:
        raise RuntimeError(f"pinned input changed: {path}")
    try:
        label = path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        label = str(path.resolve()).replace("\\", "/")
    return {"path": label, "sha256": digest, "size": len(raw)}


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def source_set(manifest: dict) -> tuple[list[dict], list[dict]]:
    index = read_json(STRICT_INDEX)
    if index.get("schema") != "simant-dos-strict-static-index-v1" or len(index.get("entries", {})) != 29:
        raise RuntimeError("strict-static index is not the reviewed 29-entry index")
    behavior, extra_pins = [], [pin(STRICT_INDEX)]
    for function, ref in sorted(index["entries"].items()):
        receipt_path = ROOT / ref["path"]
        extra_pins.append(pin(receipt_path, ref["sha256"]))
        receipt = read_json(receipt_path)
        src = (receipt.get("audit", {}).get("source", {}) if function == "DrawBalloons"
               else receipt.get("registered_source", {}))
        if not src.get("whole_module"):
            raise RuntimeError(f"{function} has no whole-module effective source")
        p = pin(ROOT / src["path"], src["sha256"])
        behavior.append({"path": src["path"], "sha256": p["sha256"],
                         "module": src["module"], "function": function})
    rows = [{"path": m["source"], "sha256": m["source_sha256"], "module": key,
             "set": "canonical_127"} for key, m in manifest["modules"].items()]
    rows += [row | {"set": "strict_effective_29"} for row in behavior]
    unique: dict[str, dict] = {}
    for row in rows:
        old = unique.get(row["path"])
        if old and old["sha256"] != row["sha256"]:
            raise RuntimeError(f"source hash conflict for {row['path']}")
        unique.setdefault(row["path"], row)
    result = sorted(unique.values(), key=lambda r: r["path"])
    if len(manifest["modules"]) != 127 or len(behavior) != 29 or len(result) != 156:
        raise RuntimeError("expected 127 canonical + 29 strict-effective / 156 distinct paths")
    for row in result:
        pin(ROOT / row["path"], row["sha256"])
    return result, extra_pins


def physical_aliases(data_symbols: dict, linear: int, size: int) -> dict:
    hits = []
    frames = set()
    for name, row in data_symbols.items():
        seg, off = row.get("seg"), row.get("off")
        if not isinstance(seg, int) or not isinstance(off, int):
            continue
        frames.add(seg)
        at = seg * 16 + off
        if linear - 3 <= at < linear + size:
            hits.append({"name": name, "address": f"{seg:04X}:{off:04X}",
                         "linear": f"{at:05X}", "delta_from_target": at - linear,
                         "alias_of": row.get("alias_of")})
    frame_aliases = []
    for seg in sorted(frames):
        off = linear - seg * 16
        if 0 <= off <= 0xFFFF:
            frame_aliases.append({"address": f"{seg:04X}:{off:04X}",
                                  "segment": seg, "offset": off,
                                  "linear": f"{seg * 16 + off:05X}"})
    return {"target_linear": f"{linear:05X}", "slot_size_bytes": size,
            "registered_starts_near_slot": sorted(hits, key=lambda x: (x["delta_from_target"], x["name"])),
            "equivalent_registered_data_frames": frame_aliases}


def source_hits(rows: list[dict], spellings: set[str]) -> tuple[dict, list[dict]]:
    hits = {name: [] for name in sorted(spellings)}
    number_hits = []
    for row in rows:
        text = (ROOT / row["path"]).read_text(encoding="latin1")
        for lineno, line in enumerate(text.splitlines(), 1):
            for name in spellings:
                if re.search(r"\b" + re.escape(name) + r"\b", line):
                    hits[name].append({"source": row["path"], "line": lineno,
                                       "text": line.strip(), "set": row["set"]})
            if re.search(r"(?i)(?:0x50f6|\b50f6h\b|0x46d2|\b46d2h\b)", line):
                number_hits.append({"source": row["path"], "line": lineno,
                                    "text": line.strip(), "set": row["set"]})
    return hits, number_hits


def classify_access(insn) -> str:
    ops = insn.op_str.strip().lower()
    first = ops.split(",", 1)[0].strip()
    if insn.mnemonic in STRING_WRITES:
        return "implicit_destination_write"
    if "es:[" in first and insn.mnemonic in WRITE_MNEMONICS:
        return "write"
    if "es:[" in ops:
        return "read"
    return "unknown"


def original_scan(target_linear: int, data_size: int, target_code: list[dict]) -> dict:
    image = exe.load()
    rows = functions.table()["functions"]
    md = Cs(CS_ARCH_X86, CS_MODE_16)
    md.detail = True
    code_addresses = {r["name"]: (r["seg"] * 16 + r["off"], r["extent"])
                      for r in target_code}
    calls, self_branches, data_ptrs, vectors = [], [], [], []
    target_ranges = [(lin, lin + size, name) for name, (lin, size) in code_addresses.items()]

    for unit in image.units():
        base, raw = image.unit_bytes(unit)
        for r in (z for z in rows if z["unit"] == unit):
            lin = r["seg"] * 16 + r["off"]
            name = functions.name_of(unit, r["seg"], r["off"])
            body = raw[lin - base:lin - base + r["size"]]
            for insn in md.disasm(body, lin):
                if insn.mnemonic not in {"call", "lcall", "jmp", "ljmp"}:
                    continue
                possible = []
                immediates = [o.imm for o in insn.operands if o.type == CS_OP_IMM]
                if insn.mnemonic in {"lcall", "ljmp"}:
                    m = re.fullmatch(r"(?:far )?(0x[0-9a-f]+|[0-9]+), (0x[0-9a-f]+|[0-9]+)", insn.op_str)
                    if m:
                        seg = int(m.group(1), 0)
                        off = int(m.group(2), 0)
                        possible.append(seg * 16 + off)
                elif immediates:
                    possible.append(immediates[0])
                for addr in possible:
                    for lo, hi, target_name in target_ranges:
                        if lo <= addr < hi:
                            edge = {"caller": name, "caller_unit": unit,
                                          "instruction": insn.mnemonic + " " + insn.op_str,
                                          "instruction_linear": f"{insn.address:05X}",
                                          "target": target_name,
                                          "target_linear": f"{addr:05X}",
                                          "target_delta": addr - lo}
                            if name == target_name and lo <= insn.address < hi:
                                self_branches.append(edge)
                            else:
                                calls.append(edge)

        # An MZ/overlay relocation on the segment word of a far pointer lets us
        # recover its offset+segment target without copying or exporting bytes.
        for seg, off in image.unit_relocs(unit):
            site = seg * 16 + off
            local = site - base
            if local < 2 or local + 2 > len(raw):
                continue
            ptr_off, ptr_seg = struct.unpack_from("<HH", raw, local - 2)
            ptr_linear = ptr_seg * 16 + ptr_off
            for lo, hi, target_name in target_ranges:
                if lo <= ptr_linear < hi:
                    data_ptrs.append({"unit": unit, "relocation_site": f"{seg:04X}:{off:04X}",
                                      "target": target_name, "target_linear": f"{ptr_linear:05X}",
                                      "target_delta": ptr_linear - lo})

    for v in image.vectors:
        linear = v.target_seg * 16 + v.target_off
        for lo, hi, target_name in target_ranges:
            if lo <= linear < hi:
                vectors.append({"vector_offset": f"{v.offset:04X}", "section": v.section,
                                "target": target_name, "target_linear": f"{linear:05X}"})

    # Follow compiler-proven far-segment loads and fixed ES displacements, then
    # translate all hits through physical addresses so segment aliases count.
    es_refs, es_words, les_refs = [], [], []
    for unit in image.units():
        unit_rows = [r for r in rows if r["unit"] == unit]
        refs, words = dataref.far_refs(unit, unit_rows)
        base, raw = image.unit_bytes(unit)
        by_name = {functions.name_of(unit, r["seg"], r["off"]): r for r in unit_rows}
        relevant_users: dict[str, set[tuple[int, int]]] = {}
        for (frame, off), info in refs.items():
            physical = frame * 16 + off
            if target_linear <= physical < target_linear + data_size:
                for user in info["users"]:
                    relevant_users.setdefault(user, set()).add((frame, off))
        for user, pairs in relevant_users.items():
            r = by_name[user]
            lin = r["seg"] * 16 + r["off"]
            for insn in md.disasm(raw[lin - base:lin - base + r["size"]], lin):
                for frame, off in pairs:
                    # dataref uses the constant displacement as the far-frame offset;
                    # preserve indexed forms as candidate aliases and do not infer index values.
                    token = f"0x{off:x}"
                    if token in insn.op_str.lower() or re.search(rf"(?<![0-9a-f]){off}(?![0-9a-f])", insn.op_str.lower()):
                        if ("es:[" in insn.op_str.lower() and
                                not re.search(r"es:\[[^\]]*\b(bx|si|di|bp)\b", insn.op_str.lower())):
                            es_refs.append({"unit": unit, "function": user,
                                            "function_address": f"{r['seg']:04X}:{r['off']:04X}",
                                            "instruction": insn.mnemonic + " " + insn.op_str,
                                            "access": classify_access(insn),
                                            "far_address": f"{frame:04X}:{off:04X}",
                                            "far_linear": f"{frame * 16 + off:05X}",
                                            "delta_from_slot": frame * 16 + off - target_linear})
        # dataref.far_refs skips the memory read performed by LES. Revisit those
        # instructions using the same compiler-registered CONST frame loads, and
        # record any fixed ES displacement that physically lands in the slot.
        frame_by_word = {word: info["frame"] for word, info in words.items()
                         if isinstance(info.get("frame"), int)}
        for r in unit_rows:
            user = functions.name_of(unit, r["seg"], r["off"])
            lin = r["seg"] * 16 + r["off"]
            es_frame = None
            for insn in md.disasm(raw[lin - base:lin - base + r["size"]], lin):
                op = insn.op_str.lower()
                # The CONST far-frame loads relevant to this proof are direct
                # mov es,[DGROUP relocation] forms; calls and other ES writes
                # invalidate this local tracking.
                if insn.mnemonic in {"call", "lcall", "int", "iret", "ret", "retf"}:
                    es_frame = None
                elif insn.mnemonic == "mov" and op.startswith("es, word ptr ["):
                    mm = re.search(r"\[(0x[0-9a-f]+|[0-9]+)\]", op)
                    es_frame = frame_by_word.get(int(mm.group(1), 0)) if mm else None
                elif insn.mnemonic == "mov" and op.startswith("es,"):
                    es_frame = None
                elif insn.mnemonic == "pop" and op == "es":
                    es_frame = None
                if es_frame is not None and "es:[" in op:
                    inner = re.search(r"es:\[([^\]]+)\]", op)
                    if inner and re.search(r"\b(bx|si|di|bp)\b", inner.group(1)):
                        continue
                    mm = re.search(r"es:\[(?:(?:bx|si|di|bp)(?: \+ (?:si|di))?(?: [+-] )?)?(0x[0-9a-f]+|[0-9]+)?\]", op)
                    if mm:
                        off = int(mm.group(1), 0) if mm.group(1) else 0
                        if "- " + (mm.group(1) or "") in op:
                            off = -off & 0xFFFF
                        physical = es_frame * 16 + off
                        if target_linear <= physical < target_linear + data_size:
                            les_refs.append({"unit": unit, "function": user,
                                             "function_address": f"{r['seg']:04X}:{r['off']:04X}",
                                             "instruction": insn.mnemonic + " " + insn.op_str,
                                             "access": classify_access(insn),
                                             "far_address": f"{es_frame:04X}:{off:04X}",
                                             "far_linear": f"{physical:05X}",
                                             "delta_from_slot": physical - target_linear})
                if insn.mnemonic == "les":
                    es_frame = None
        frame_words = [info for info in words.values() if info.get("frame") == 0x50F6]
        es_words.append({"unit": unit, "const_word_count_for_frame_50f6": len(frame_words),
                         "functions_loading_frame_50f6": len(set().union(*(x["users"] for x in frame_words))) if frame_words else 0})

    return {
        "original_sha256": image.sha256,
        "function_rows_scanned": len(rows),
        "units_scanned": len(image.units()),
        "external_direct_control_transfers_into_consumers": calls,
        "internal_branches_in_consumer_extents": self_branches,
        "relocated_far_code_pointers_into_consumers": data_ptrs,
        "rtlink_overlay_vectors_into_consumers": vectors,
        "physical_slot_address_references_from_tracked_far_segments": es_refs + les_refs,
        "tracked_frame_50f6_summary": es_words,
        "pointer_scan_method": "Every relocation site in root and overlay units; read only the relocated far-pointer words immediately preceding a segment-word relocation and compare normalized physical target addresses.",
        "call_scan_method": "Every function-table extent in all executable units; direct near/far call and jump immediates normalized to linear addresses.",
        "vector_scan_method": "All RTLink manager vectors, target segment:offset normalized to linear addresses.",
        "far_data_scan_method": "tools/dataref.far_refs over every original function, normalized by segment*16+offset; an additional instruction scan covers LES reads skipped by dataref and records computed indexed ES references in target-equivalent frames as candidates only.",
    }


def main() -> int:
    manifest_path = ROOT / "layout/manifest.json"
    symbols_path = ROOT / "layout/symbols.json"
    functions_path = ROOT / "layout/functions.json"
    lock_path = ROOT / "layout/oracle.lock.json"
    manifest, symbol_doc = read_json(manifest_path), read_json(symbols_path)
    sources, strict_pins = source_set(manifest)
    target = symbol_doc["data"][TARGET_DATA]
    if (target.get("seg"), target.get("off")) != (0x50F6, 0x46D2):
        raise RuntimeError("target registry address changed")
    target_linear = target["seg"] * 16 + target["off"]
    code_symbols = symbol_doc["code"]
    target_code = []
    for name in TARGET_FUNCS:
        r = code_symbols[name]
        target_code.append({"name": name, "unit": r["unit"], "seg": r["seg"], "off": r["off"],
                            "linear": f"{r['seg'] * 16 + r['off']:05X}",
                            "extent": next((f["size"] for f in read_json(functions_path)["functions"]
                                            if (f["unit"], f["seg"], f["off"]) ==
                                            (r["unit"], r["seg"], r["off"])), None)})
    code_aliases = sorted(n for n, r in code_symbols.items()
                          if any((r.get("unit"), r.get("seg"), r.get("off")) ==
                                 (x["unit"], x["seg"], x["off"]) for x in target_code))
    data_aliases = physical_aliases(symbol_doc["data"], target_linear, TARGET_SIZE)
    spellings = {TARGET_DATA, *TARGET_FUNCS, *code_aliases, RELATED_FUNC, "g_8CCB",
                 "f_1FD2_0663", "fd_50F6_46A8", "fd_50F6_46BC", "g_6054", "g_604C"}
    spellings.update(x["name"] for x in data_aliases["registered_starts_near_slot"])
    src_hits, numeric_hits = source_hits(sources, spellings)
    original = original_scan(target_linear, TARGET_SIZE, target_code)

    related_symbol = code_symbols[RELATED_FUNC]
    related_row = next(f for f in read_json(functions_path)["functions"]
                       if (f["unit"], f["seg"], f["off"]) ==
                       (related_symbol["unit"], related_symbol["seg"], related_symbol["off"]))
    related_code = [{"name": RELATED_FUNC, "unit": related_symbol["unit"],
                     "seg": related_symbol["seg"], "off": related_symbol["off"],
                     "linear": f"{related_symbol['seg'] * 16 + related_symbol['off']:05X}",
                     "extent": related_row["size"]}]
    related_original = original_scan(0x55B3 * 16 + 0x8CCB, 1, related_code)
    extfix = read_json(CURRENT_188_EXTFIXUPS)
    if extfix.get("census", {}).get("application_object_count") != 188 or len(extfix["census"]["all_objects"]) != 188:
        raise RuntimeError("current OMF EXTDEF/live-fixup census is not the pinned 188-object set")

    def omf_symbol_rows(symbol: str) -> list[dict]:
        wanted = symbol.casefold()
        found = []
        for obj in extfix["census"]["all_objects"]:
            extdefs = [x for x in obj["external_extdefs"] if x.casefold() == wanted]
            fixups = [x for x in obj["live_external_fixups"] if x["symbol"].casefold() == wanted]
            if extdefs or fixups:
                found.append({"module": obj["module"], "basename": obj["basename"],
                              "source_path": obj["source_path"], "object_sha256": obj["object_sha256"],
                              "extdef_count": len(extdefs), "live_external_fixups": fixups})
        return found

    pinned_paths = [manifest_path, symbols_path, functions_path, lock_path, STRICT_INDEX]
    pinned_paths += [ROOT / p for p in ("src/root/m208F.c", "src/root/m205F.c", "src/root/m1B28.c",
                                         "src/root/m1A53.c", "src/S20/m39C7.c", "src/S20/m39F1.c",
                                         "src/root/m21FA.c", "src/root/m259D.c", "src/root/m1FD2.c")]
    pinned_paths += list(PREVIOUS_RECEIPTS)
    pinned_paths += [CURRENT_188_EXTFIXUPS,
                     ROOT / "work/source-only-dos/critical-error-selector-source-review-v18.json"]
    evidence_pins = [pin(p) for p in pinned_paths]
    w16_path = Path("D:/Prog/simantw_recon/src/recovered/win_DrawWinIcons.c")
    win16 = {"path": str(w16_path).replace("\\", "/"),
             "sha256": sha(w16_path.read_bytes()),
             "finding": "Win16 counterpart is an empty stub; DOS-specific table owner is not evidenced there."} if w16_path.is_file() else None

    status = "NO_OBSERVED_SOURCE_INBOUND_PATH; HISTORICAL_OWNER_UNRESOLVED; CONDITIONAL_MENU_CLOBBER"
    result = {
        "schema": "simant-dos-icon-handle-owner-audit-v33",
        "created_utc": "2026-10-04",
        "status": status,
        "scope": {
            "source_selection": "127 canonical manifest modules + 29 whole-module sources selected by strict-completeness/index-v1.json; DrawBalloons uses audit.source; no superseded variants.",
            "source_count": len(sources),
            "original_code_scope": "All 1730 function-table extents in 29 executable units (root plus S00-S27), all unit relocations and all RTLink vectors.",
            "no_original_bytes_serialized": True,
            "no_canonical_or_layout_writes": True,
        },
        "target": {
            "name": TARGET_DATA,
            "address": f"{target['seg']:04X}:{target['off']:04X}",
            "physical_linear": f"{target_linear:05X}",
            "type_evidence": "f_208F_027F executes LES BX,ES:[46D2] and loads offset+segment from [BX] and [BX+2]; the C view is a far pointer to a far pointer (4 bytes).",
            "consumer_functions": target_code,
            "registered_same_address_code_aliases": code_aliases,
            "registered_physical_data_aliases": data_aliases,
        },
        "source_identifier_hits": src_hits,
        "source_numeric_hits_for_50f6_or_46d2": numeric_hits,
        "source_initialization_route_review": {
            "f_205F_0004": [
                "After db_SetDataBase(path), calls f_1B28_0006 to cache six cursor image/mask handle pairs (objects 0..5, kinds 8/7).",
                "Then mode-selected video initialization and S20 font callback run; no selected source writes fd_50F6_46D2 or registers f_208F_027F/02F0.",
            ],
            "f_1B28_0006": "Loads/unhooks cursor objects into near arrays g_8C7C/g_8C9C; no assignment or address escape to the target slot.",
            "S20_callbacks": "The effective S20 m39C7 callbacks load font objects 0x13..0x15 kind 9 into DGROUP globals g_3DA4/g_3DA8; they do not store to the target slot.",
            "db_LoadObject": "The selected root implementation returns a cache handle from DBRecall/ch_LookUpId and registers it in db_cacheTable; it does not assign the global target slot.",
        },
        "source_menu_clobber_review": {
            "writer": "f_1FD2_0663 in src/root/m1FD2.c has two uncapped null-sentinel passes over g_6054->titles.",
            "first_pass": "widths[i] is stored before g_604C records the count; widths[11] writes bytes 46D2-46D3 and widths[12] writes 46D4-46D5.",
            "second_pass": "xpos[i] is stored after resetting i; xpos[21] writes bytes 46D2-46D3 and xpos[22] writes 46D4-46D5.",
            "whole_slot_thresholds": "At least 13 titles for widths[11]+widths[12], or 23 titles for xpos[21]+xpos[22], are required for sequential source stores to cover all four bytes; 12 or 22 titles respectively reach only the low word.",
            "runtime_bound": "These source loops have no cap. The v28 menu receipt bounds the exact supplied SHARED kind-6 object 0 to five non-null titles; it does not bound every resource/domain or prove no other caller supplies a larger title list.",
            "disposition": "Conditional physical clobber path, separately unresolved; do not exclude the handle slot based on registered symbol starts.",
        },
        "current_188_omf_external_fixups_for_icon_consumers": {
            "census_path": CURRENT_188_EXTFIXUPS.relative_to(ROOT).as_posix(),
            "objects": len(extfix["census"]["all_objects"]),
            "consumers": {"_" + name: omf_symbol_rows("_" + name) for name in TARGET_FUNCS},
            "interpretation": "Both function EXTDEFs occur only in their own U099 root:208F object and have no live external fixup; no other current188 object references either consumer by OMF symbol.",
        },
        "original_xref_and_alias_audit": original,
        "related_g8CCB_inbound_probe": {
            "source_only_scope": "Exact identifier scan over the same 156 selected sources; this is not a global execution-closure claim.",
            "function": related_code,
            "function_identifier_hits": src_hits[RELATED_FUNC],
            "selector_identifier_hits": src_hits["g_8CCB"],
            "original_xref_scan": {
                "external_direct_control_transfers_into_consumer": related_original["external_direct_control_transfers_into_consumers"],
                "internal_branches_in_consumer_extent": related_original["internal_branches_in_consumer_extents"],
                "relocated_far_code_pointers_into_consumer": related_original["relocated_far_code_pointers_into_consumers"],
                "rtlink_overlay_vectors_into_consumer": related_original["rtlink_overlay_vectors_into_consumers"],
            },
            "current_188_omf_external_fixups": {
                "census_path": CURRENT_188_EXTFIXUPS.relative_to(ROOT).as_posix(),
                "objects": len(extfix["census"]["all_objects"]),
                "function_symbol": "_f_1C62_06A6",
                "function_symbol_object_rows": omf_symbol_rows("_f_1C62_06A6"),
                "selector_symbol": "_g_8CCB",
                "selector_symbol_object_rows": omf_symbol_rows("_g_8CCB"),
                "interpretation": "No other current188 object declares or fixes the function symbol. The only current188 g_8CCB fixup is the selector read in its consumer object. This closes only the bounded current object-set external-fixup question, not historical ownership or unchecked-runtime execution.",
            },
        },
        "win16_readonly_crosscheck": win16,
        "pins": {
            "audit_script": pin(OUT / "audit_v33.py"),
            "source_census": [{"path": x["path"], "sha256": x["sha256"],
                                "set": x["set"], "module": x["module"]} for x in sources],
            "strict_receipts_and_index": strict_pins,
            "reviewed_evidence": evidence_pins,
            "oracle_executable_sha256": read_json(lock_path)["executable"]["sha256"],
        },
        "limitations": [
            "No selected source calls or registers either consumer by the exact identifiers, and original direct transfers, relocated far-code pointers and RTLink vectors show no external inbound edge; unresolved data-as-code and zero-target callback gates prevent global runtime control closure.",
            "The fixed far-frame sweep normalizes segment:offset references by physical linear address and separately scans LES memory reads. Computed register-indexed ES addresses, indirect non-relocated data tables and runtime index ranges remain open.",
            "The historical defining TU, initializer, object identity and source lifetime are still unknown. A natural `char far * far * far` declaration expresses the observed 4-byte view only; current evidence does not place a definition at 50F6:46D2 or establish its initializer.",
            "The uncapped menu table source has conditional writes into the slot: widths[11]/xpos[21] hit the low word, and widths[12]/xpos[22] hit the upper word if the title count reaches those indices. The exact supplied SHARED object 0 has five titles, but this is not a global source-domain cap.",
        ],
    }
    receipt_path = OUT / "receipt-v33.json"
    receipt_path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    def count_items(name: str) -> int:
        value = result["original_xref_and_alias_audit"][name]
        return len(value)

    review = [
        "# DOS small-icon handle ownership audit v33",
        "",
        f"Status: **{status}**. The original dereference sequence establishes a 4-byte far-pointer view, but no historical defining TU, initializer, or owner lifetime was found.",
        "",
        "The strict-effective source set is selected from `work/source-only-dos/static-completeness/index-v1.json`: 127 canonical manifest modules plus 29 registered whole-module behavior sources (156 distinct files). The current `f_205F_0004` setup opens the selected database, loads/unhooks six cursor image/mask pairs through `f_1B28_0006`, and then initializes the selected video driver and S20 font callbacks. Those paths write cursor/font globals; the selected sources contain no exact call or function-address registration for either icon consumer and no direct assignment to `fd_50F6_46D2`.",
        "",
        f"Original-image scan covered {original['function_rows_scanned']} function extents in {original['units_scanned']} executable units, every unit relocation, and all {len(exe.load().vectors)} RTLink vectors. Excluding internal conditional branches, it found {count_items('external_direct_control_transfers_into_consumers')} external direct calls/jumps, {count_items('relocated_far_code_pointers_into_consumers')} relocated far-code pointers, and {count_items('rtlink_overlay_vectors_into_consumers')} vectors into `f_208F_027F`/`f_208F_02F0`. The pinned current188 OMF census likewise finds each EXTDEF only in its own U099 object, with no live fixup to either consumer.",
        "",
        f"The bounded related `g_8CCB` probe finds no source caller or original direct/far-pointer/vector inbound edge to `f_1C62_06A6`. In the pinned current188 OMF census, only U088 declares its own function symbol and has no live external fixup to it; the sole `_g_8CCB` live fixup is U088's selector read. This supplements the pinned v18 startup-zero evidence without reopening or closing its separate computed-clobber/error-gate review.",
        "",
        f"The pointer slot is at physical linear `0x{target_linear:05X}`. The only registered data starts within the slot neighborhood are `fd_50F6_46D0` (two bytes before) and the target symbol itself; the JSON lists equivalent `segment:offset` frames for every registered far-data segment and tracked fixed ES references after physical normalization, including LES reads. The menu table does overlap this slot conditionally: uncapped `widths[11]` / `xpos[21]` writes hit 46D2-46D3, and `widths[12]` / `xpos[22]` hit 46D4-46D5. Thus 12 or 22 titles reach the low word; 13 or 23 can sequentially overwrite all four bytes. Only the exact supplied SHARED kind-6 object 0 is bounded to five titles by the v28 receipt.",
        "",
        "This establishes only that the reviewed selected source graph has no observed inbound source path to these helpers. It does not close arbitrary data-as-code, zero-target callbacks, computed pointer tables, external/assembly initialization, or historical owner identity. The scalar `char far * far * far` view is source-functional type evidence only; the defining TU, storage placement and initializer remain unproved. Preserve the separate conditional menu clobber: it is a possible write to the same physical slot for sufficiently large title lists, not proof that such a list is actually reachable in the supplied runtime.",
        "",
        "Reproduce with `python build/workers/dos_icon_handle_owner_v33/audit_v33.py`. The JSON pins the selected sources, strict-effective receipts, current registries and prior storage receipts; it records no original payload bytes.",
        "",
    ]
    review_path = OUT / "review-v33.md"
    review_path.write_text("\n".join(review), encoding="utf-8")
    result["pins"]["review_artifact"] = pin(review_path)
    receipt_path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {receipt_path.relative_to(ROOT)}")
    print(f"wrote {review_path.relative_to(ROOT)}")
    print(f"selected sources: {len(sources)}; external direct calls: {count_items('external_direct_control_transfers_into_consumers')}; "
          f"relocated far pointers: {count_items('relocated_far_code_pointers_into_consumers')}; "
          f"vectors: {count_items('rtlink_overlay_vectors_into_consumers')}; "
          f"tracked ES refs to slot: {count_items('physical_slot_address_references_from_tracked_far_segments')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
