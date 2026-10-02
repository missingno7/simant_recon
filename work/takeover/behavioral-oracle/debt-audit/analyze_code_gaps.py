"""Read-only instruction/reference audit of unowned game-code gaps.

Run from repository root. Writes only build/workers/behavior_data_audit/code-gaps.json.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))
import exe
import functions
import inventory
import symbols

try:
    import capstone
except ImportError:
    sys.path.insert(0, "C:/tools/capstone-5.0.3")
    import capstone
from capstone import Cs, CS_ARCH_X86, CS_MODE_16


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def main() -> None:
    x = exe.load()
    sym = symbols.load()
    md = Cs(CS_ARCH_X86, CS_MODE_16)
    md.detail = True
    specs = [
        {"id": "root_0ec11", "unit": "root", "linear": 0x0EC11, "size": 1,
         "frame": 0x0E2E, "description": "zero byte between LessonDone and CompactListA"},
        {"id": "root_1ccbe", "unit": "root", "linear": 0x1CCBE, "size": 8,
         "frame": 0x1C62, "description": "root code gap after f_1C62_0415"},
        {"id": "root_1e578", "unit": "root", "linear": 0x1E578, "size": 1,
         "frame": 0x1E57, "description": "retf between f_1E57_0007 and f_1E57_0009"},
        {"id": "root_1f420", "unit": "root", "linear": 0x1F420, "size": 9,
         "frame": 0x1E57, "description": "root code gap between clip_Push and clip_Pop"},
        {"id": "root_23e5e", "unit": "root", "linear": 0x23E5E, "size": 2,
         "frame": 0x23AE, "description": "root code gap after win_LockWin"},
        {"id": "root_285d7", "unit": "root", "linear": 0x285D7, "size": 1,
         "frame": 0x284A, "description": "root code gap after StopSong"},
        {"id": "s04_368d0", "unit": "S04", "linear": 0x368D0, "size": 32,
         "frame": 0x35F5, "description": "S04 code gap after EraseMiniMapCursor"},
    ]
    gap_targets = {(s["unit"], s["linear"], s["linear"] + s["size"]): s for s in specs}
    for s in specs:
        base, data = x.unit_bytes(s["unit"])
        off = s["linear"] - s["frame"] * 16
        idx = s["linear"] - base
        body = data[idx:idx + s["size"]]
        insns = []
        for i in md.disasm(body, off):
            immed = [o.imm & 0xFFFF for o in i.operands if o.type == capstone.x86.X86_OP_IMM]
            calls = []
            if i.mnemonic == "lcall" and len(immed) == 2:
                target = (immed[0], immed[1])  # Capstone prints segment, offset.
                code_symbol = next((n for n, a in sym["code"].items()
                                    if a.get("seg") == target[0] and a.get("off") == target[1]), None)
                calls.append({"kind": "far", "segment": target[0], "offset": target[1],
                              "symbol": code_symbol})
            elif i.mnemonic == "call" and len(immed) == 1:
                target = (s["frame"], immed[0])
                code_symbol = next((n for n, a in sym["code"].items()
                                    if a.get("unit") == s["unit"] and a.get("seg") == target[0]
                                    and a.get("off") == target[1]), None)
                calls.append({"kind": "near", "segment": target[0], "offset": target[1],
                              "symbol": code_symbol})
            insns.append({"offset": i.address, "bytes": i.bytes.hex(" "), "mnemonic": i.mnemonic,
                          "operands": i.op_str, "calls": calls})
        s["code_offset"] = off
        s["bytes_hex"] = body.hex(" ")
        s["instructions"] = insns

    # Nearby known function extents and bytes at their terminal instructions.
    function_rows = functions.table()["functions"]
    for s in specs:
        prev, nxt = [], []
        for f in function_rows:
            if f["unit"] != s["unit"]:
                continue
            base, data = x.unit_bytes(f["unit"])
            lin = f["seg"] * 16 + f["off"]
            file_key = (lin - base, f)
            target_idx = s["linear"] - base
            end_idx = lin - base + f["size"]
            if end_idx <= target_idx:
                prev.append((end_idx, file_key[1]))
            elif lin - base >= target_idx + s["size"]:
                nxt.append((lin - base, file_key[1]))
        for label, rows, reverse in (("previous", prev, True), ("next", nxt, False)):
            rows.sort(key=lambda p: p[0], reverse=reverse)
            out = []
            for _, f in rows[:1]:
                base, data = x.unit_bytes(f["unit"])
                lin = f["seg"] * 16 + f["off"]
                raw = data[lin - base:lin - base + f["size"]]
                out.append({"name": functions.name_of(f["unit"], f["seg"], f["off"]),
                            "frame": f["seg"], "offset": f["off"], "size": f["size"],
                            "end_offset_exclusive": f["off"] + f["size"],
                            "tail_hex": raw[-12:].hex(" ")})
            s[label + "_function"] = out[0] if out else None

    # Full executable relocation scan: far pointer is the word before a relocated segment word.
    reloc_count = 0
    relocated_targets = []
    timer_near_targets = []
    for unit in x.units():
        base, data = x.unit_bytes(unit)
        for seg, off in x.unit_relocs(unit):
            reloc_count += 1
            idx = seg * 16 + off - base
            if idx < 2 or idx + 2 > len(data):
                continue
            poff = int.from_bytes(data[idx - 2:idx], "little")
            pseg = int.from_bytes(data[idx:idx + 2], "little")
            target = pseg * 16 + poff
            for s in specs:
                # Root coordinates have unique frames. Overlay records require same unit
                # and frame because overlay sections alias linear address ranges.
                exact = pseg == s["frame"] and poff == s["code_offset"]
                if exact:
                    relocated_targets.append({"site_unit": unit, "site_segment": seg,
                                              "site_offset": off, "target": s["id"]})
            if 0x5FF0 <= poff <= 0x60D0:
                timer_near_targets.append({"site_unit": unit, "site_segment": seg,
                                           "site_offset": off, "target_offset": poff,
                                           "target_segment": pseg})

    # Literal near code-pointer and switch-table evidence.
    raw_words = {}
    raw_far_pairs = {}
    for s in specs:
        pat = s["code_offset"].to_bytes(2, "little")
        occurrences = []
        far_pat = pat + s["frame"].to_bytes(2, "little")
        far_occurrences = []
        for unit in x.units():
            base, data = x.unit_bytes(unit)
            pos = 0
            while True:
                i = data.find(pat, pos)
                if i < 0:
                    break
                occurrences.append({"unit": unit, "linear": base + i, "index": i})
                pos = i + 1
            pos = 0
            while True:
                i = data.find(far_pat, pos)
                if i < 0:
                    break
                far_occurrences.append({"unit": unit, "linear": base + i, "index": i})
                pos = i + 1
        raw_words[s["id"]] = occurrences
        raw_far_pairs[s["id"]] = far_occurrences

    inv = inventory.Inventory().run()
    vectors = [{"offset": v.offset, "unit": v.unit, "segment": v.target_seg,
                "target_offset": v.target_off, "section": v.section}
               for v in x.vectors]
    vector_hits = [v for v in vectors for s in specs
                   if v["unit"] == s["unit"] and v["segment"] == s["frame"]
                   and v["target_offset"] == s["code_offset"]]
    jump_tables = []
    switch_hits = []
    for t in inv.jump_tables:
        base, data = x.unit_bytes(t["unit"])
        idx = t["table"] - base
        vals = [int.from_bytes(data[idx + 2 * k:idx + 2 * k + 2], "little")
                for k in range(t["count"])]
        rec = {"unit": t["unit"], "site": t["site"], "table": t["table"],
               "count": t["count"], "values": vals}
        jump_tables.append(rec)
        for s in specs:
            if t["unit"] == s["unit"] and s["code_offset"] in vals:
                switch_hits.append({"table": rec, "target": s["id"]})

    # Incoming direct calls discovered from seeded function extents, kept unit-qualified.
    direct_call_hits = []
    for site_unit, site, target_unit, target, kind in inv.call_sites:
        for s in specs:
            if target_unit == s["unit"] and target == s["linear"]:
                direct_call_hits.append({"site_unit": site_unit, "site": site,
                                         "target": s["id"], "kind": kind})

    # Confirm S04 private state ownership and its Win16 name hint without changing the DOS name.
    mod = json.loads((ROOT / "layout/manifest.json").read_text(encoding="utf-8"))
    s04 = mod["modules"]["S04:35F5"]
    out = {
        "schema": "unowned-code-gap-investigation-v1",
        "oracle_sha256": x.sha256,
        "manifest_sha256": sha((ROOT / "layout/manifest.json").read_bytes()),
        "known_functions_sha256": sha((ROOT / "layout/functions.json").read_bytes()),
        "sources": {
            "root_1C62": sha((ROOT / "src/root/m1C62.c").read_bytes()),
            "root_1E57": sha((ROOT / "src/root/m1E57.c").read_bytes()),
            "S04_35F5": sha((ROOT / "src/S04/m35F5.c").read_bytes()),
            "cross_version_decisions": sha((ROOT / "evidence/cross_version/decisions.json").read_bytes()),
        },
        "spans": specs,
        "reference_audit": {
            "function_extents_scanned": len(function_rows),
            "direct_call_hits_into_spans": direct_call_hits,
            "loader_relocations_scanned": reloc_count,
            "relocated_far_pointer_hits_into_spans": relocated_targets,
            "relocated_offsets_5ff0_60d0": timer_near_targets,
            "rtlink_vectors_scanned": len(vectors), "vector_hits": vector_hits,
            "same_unit_switch_tables_scanned": len(jump_tables), "switch_hits": switch_hits,
            "raw_near_offset_occurrences": raw_words,
            "raw_offset_segment_pair_occurrences": raw_far_pairs,
            "scope": "No direct known-function call, exact relocated far-pointer, vector, switch-table, or raw near-offset hit is evidence of no indirect/computed/unowned entry. Raw offset-only occurrences can be immediates/data and are not classified as pointers.",
        },
        "s04_private_data": {
            "_DATA_placement": s04["placements"]["_DATA"],
            "source_static": "static int miniCursorOn = 0",
            "source_writes": ["DrawMiniMapCursor sets miniCursorOn=1",
                              "EraseMiniMapCursor sets miniCursorOn=0"],
            "span_operand": "DS:2338 read; placement begins at DGROUP 55B3:2338",
            "win16_name_clue": "evidence/cross_version/decisions.json notes ToggleMiniMapCursor follows DrawMiniMapCursor and EraseMiniMapCursor on Win16; this is a clue, not a DOS function-name decision.",
        },
        "interpretation": {
            "root_0ec11": "A single zero byte lies exactly after the accepted LessonDone extent and before CompactListA at root 0EC1:0002, whose next address is even. It is a strong word-alignment candidate, not an instruction/function ownership claim.",
            "root_1ccbe": "Natural C-shaped 8-byte far routine: call f_1C62_0090, return AX=1. Entry starts immediately after f_1C62_0415's retf and ends immediately before f_1C62_06A6. The known source callee conditionally invokes g_9178 when fd_55B3_6262 is set. No entry reference is established.",
            "root_1e578": "A standalone retf between accepted empty far entries f_1E57_0007 at offset 7 and f_1E57_0009 at offset 9 is consistent with a missing empty function at offset 8. The /Gs module profile and verified GS-1 support that source shape, but no entry reference is established.",
            "root_1f420": "Natural C-shaped 9-byte far routine: clip_Push(); clip_Off(); retf. It starts exactly at clip_Push's extent end and ends exactly at clip_Pop's entry. Semantically it saves current clipping state then disables clipping; no entry reference is established.",
            "root_23e5e": "A standalone retf follows the accepted fastcall win_LockWin body; a zero byte follows before the next frame. With this module's /Gs profile the byte shape is compatible with an empty far function plus alignment, but it is not assigned as such without an entry reference.",
            "root_285d7": "A standalone retf follows the accepted StopSong body and immediately precedes f_284A_0138. The module uses /Gs; an empty far function is a plausible source form, but its entry/reference remains unproven.",
            "s04_368d0": "Executable-shaped 24-byte far routine: __aFchkstk(0); if miniCursorOn then EraseMiniMapCursor else DrawMiniMapCursor; retf. S04 profile lacks /Gs, matching the observed stack-check prefix under GS-1. The next eight bytes are zero. Its behavior is supported by exact private DATA placement/source writes and a Win16 ToggleMiniMapCursor clue, but no DOS caller/address-taking reference was found.",
        },
        "function_pointer_scope": "Relocated far pointers, RTLink vectors, and recursive-descent switch tables are checked. Raw near-offset words are separately searched over every executable unit. Dynamic arithmetic, unowned caller bodies, and arbitrary indirect register transfers are outside this proof.",
    }
    (ROOT / "build/workers/behavior_data_audit/code-gaps.json").write_text(
        json.dumps(out, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
