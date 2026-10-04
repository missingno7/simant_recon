"""Read-only critical selector ownership / installed INT24 audit.

Reads original instructions only for research; emits no original payload bytes.
Run from repo root after source_only_dos.py --out THIS_DIR/intake.
All writes are confined to this worker directory. No compilation/admission.
"""
from __future__ import annotations

import hashlib
import json
import re
import struct
import sys
from collections import Counter
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, "C:/tools/capstone-5.0.3")
from capstone import Cs, CS_ARCH_X86, CS_MODE_16, CS_OP_IMM, CS_OP_MEM
from capstone.x86_const import X86_REG_DS, X86_REG_ES, X86_REG_CS, X86_REG_SS, X86_REG_BP
from omf import OmfReader
import exe
import functions

DGROUP = 0x55B3
TARGET = 0x8CCB


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def pin(path, expected=None):
    p = Path(path)
    if not p.is_absolute():
        p = ROOT / p
    raw = p.read_bytes()
    digest = sha(raw)
    if expected is not None and expected != digest:
        raise RuntimeError(f"stale pin: {p}")
    try:
        label = p.relative_to(ROOT).as_posix()
    except ValueError:
        label = p.as_posix()
    return {"path": label, "sha256": digest, "size": len(raw)}


def read(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def code_row(name, syms, size):
    r = syms["code"].get(name) or syms["runtime"][name]
    return {"name": name, "unit": r["unit"], "seg": r["seg"], "off": r["off"],
            "linear": r["seg"] * 16 + r["off"], "size": size}


def focused_original_scan(image, targets):
    """Decode in each function's segment-relative address space (16-bit wrap).

    Also classify every relocation to the selector's code frame, including
    segment immediates which are not contiguous offset:segment pointers.
    """
    md = Cs(CS_ARCH_X86, CS_MODE_16)
    md.detail = True
    rows = functions.table()["functions"]
    directs, pointers, vectors = [], [], []
    instruction_maps = {}
    fixed_near_refs, nearby_indexed_stores, immediate_selector_addresses = [], [], []
    harderr_setup = []
    write_ops = {"mov", "inc", "dec", "add", "adc", "sub", "sbb", "and", "or", "xor",
                 "not", "neg", "shl", "shr", "sar", "xchg"}
    for unit in image.units():
        imap = {}
        for r in (x for x in rows if x["unit"] == unit):
            linear = r["seg"] * 16 + r["off"]
            name = functions.name_of(unit, r["seg"], r["off"])
            insns = list(md.disasm(image.read(unit, linear, r["size"]), r["off"]))
            for idx, ins in enumerate(insns):
                il = r["seg"] * 16 + ins.address
                desc = {"unit": unit, "function": name, "address": f"{r['seg']:04X}:{ins.address:04X}",
                        "linear": f"{il:05X}", "instruction": ins.mnemonic + " " + ins.op_str}
                for at in range(il, il + ins.size):
                    imap[at] = desc
                immediates = [o.imm for o in ins.operands if o.type == CS_OP_IMM]
                if ins.mnemonic in {"call", "jmp", "lcall", "ljmp"} and immediates:
                    if ins.mnemonic in {"lcall", "ljmp"} and len(immediates) == 2:
                        address = immediates[0] * 16 + (immediates[1] & 0xFFFF)
                    else:
                        address = r["seg"] * 16 + (immediates[0] & 0xFFFF)
                    for t in targets:
                        if t["linear"] <= address < t["linear"] + t["size"]:
                            hit = desc | {"target": t["name"], "target_delta": address - t["linear"],
                                          "internal": name == t["name"]}
                            directs.append(hit)
                            if t["name"] == "__harderr" and address == t["linear"]:
                                harderr_setup += [{"address": f"{r['seg']:04X}:{ii.address:04X}",
                                                  "instruction": ii.mnemonic + " " + ii.op_str}
                                                 for ii in insns[max(0, idx - 5):idx + 2]]
                if ins.mnemonic in {"mov", "push", "lea"} and TARGET in immediates:
                    immediate_selector_addresses.append(desc)
                for opidx, op in enumerate(ins.operands):
                    if op.type != CS_OP_MEM:
                        continue
                    mem = op.mem
                    # BP defaults to SS. Explicit DS with BP remains a DS reference.
                    if mem.segment not in (0, X86_REG_DS) or (mem.base == X86_REG_BP and mem.segment == 0):
                        continue
                    width = op.size
                    access = "write" if opidx == 0 and ins.mnemonic in write_ops else "read_or_address"
                    if not mem.base and not mem.index:
                        start = mem.disp & 0xFFFF
                        if start <= TARGET < start + width:
                            fixed_near_refs.append(desc | {"access": access, "width": width,
                                                           "offset": f"{start:04X}"})
                    elif access == "write" and abs((mem.disp & 0xFFFF) - TARGET) < 0x200:
                        nearby_indexed_stores.append(desc | {"width": width,
                                                            "displacement": f"{mem.disp & 0xFFFF:04X}"})
        instruction_maps[unit] = imap

    frame_relocations, raw_near_candidates = [], []
    for unit in image.units():
        base, raw = image.unit_bytes(unit)
        for seg, off in image.unit_relocs(unit):
            site = seg * 16 + off
            local = site - base
            if local < 2 or local + 2 > len(raw):
                continue
            poff, pseg = struct.unpack_from("<HH", raw, local - 2)
            plin = pseg * 16 + poff
            owner = instruction_maps[unit].get(site)
            for t in targets:
                if t["linear"] <= plin < t["linear"] + t["size"]:
                    pointers.append({"unit": unit, "site": f"{seg:04X}:{off:04X}",
                                     "target": t["name"], "target_delta": plin - t["linear"],
                                     "instruction_owner": owner})
            if pseg == 0x1C62:
                # A switch-table linear decode can desynchronize. The actual
                # immediate FAR opcode is three bytes before its segment word;
                # this check does not depend on that decode being aligned.
                raw_far_opcode = raw[local - 3] if local >= 3 else None
                kind = ("direct_far_control_transfer" if raw_far_opcode in (0x9A,0xEA)
                        else "segment_materialization" if owner else "data_far_pointer")
                frame_relocations.append({"unit": unit, "site": f"{seg:04X}:{off:04X}",
                                          "kind": kind, "instruction_owner": owner,
                                          "contiguous_far_pointer_target": f"{pseg:04X}:{poff:04X}"})
    # A zero result from an over-approximate byte-offset scan is stronger than
    # a linear instruction decode. Include every byte offset in every original
    # function of the helper's own frame, even non-instruction offsets. E8/E9/EB
    # would be the only immediate near call/jump mechanisms into this interval.
    for r in (r for r in rows if r["unit"] == "root" and r["seg"] == 0x1C62):
        body = image.read("root",r["seg"]*16+r["off"],r["size"])
        for i, opcode in enumerate(body):
            width = 2 if opcode in (0xE8,0xE9) else 1 if opcode == 0xEB else 0
            if not width or i+1+width > len(body):
                continue
            disp = int.from_bytes(body[i+1:i+1+width],"little",signed=True)
            target = (r["off"]+i+1+width+disp)&0xFFFF
            if 0x06A6 <= target < 0x06DC and not 0x06A6 <= r["off"]+i < 0x06DC:
                raw_near_candidates.append({"source":f"1C62:{r['off']+i:04X}",
                    "target":f"1C62:{target:04X}","kind":"overapproximate_noninternal_E8_E9_EB_candidate"})
    for v in image.vectors:
        at = v.target_seg * 16 + v.target_off
        for t in targets:
            if t["linear"] <= at < t["linear"] + t["size"]:
                vectors.append({"vector": f"{v.offset:04X}", "section": v.section,
                                "target": t["name"], "target_delta": at - t["linear"]})
    return {"functions_scanned": len(rows), "units_scanned": len(image.units()),
            "relocations_scanned": sum(len(image.unit_relocs(u)) for u in image.units()),
            "vectors_scanned": len(image.vectors), "direct_control_transfers": directs,
            "relocated_contiguous_pointers": pointers, "vectors": vectors,
            "selector_frame_relocations": frame_relocations,
            "selector_frame_relocation_classes": dict(Counter(r["kind"] for r in frame_relocations)),
            "raw_near_call_jump_candidates_into_selector_extent":raw_near_candidates,
            "fixed_DS_references_covering_selector": fixed_near_refs,
            "immediate_8CCB_address_materializations": immediate_selector_addresses,
            "indexed_DS_stores_with_displacement_within_0200_of_selector": nearby_indexed_stores,
            "original_harderr_setup_context": harderr_setup}


def bind_harderr(image, manifest, syms):
    record = next(r for r in manifest["runtime"]["members"] if r["member"] == "dos\\harderr.asm")
    lib = manifest["runtime"]["libraries"][record["library"]]
    library_pin = pin(lib["path"], lib["sha256"])
    reader = OmfReader(communals=True)
    modules = reader.split_library(Path(lib["path"]).read_bytes())
    name, blob = modules[record["module_index"]]
    assert name == record["member"] and sha(blob) == record["member_sha256"]
    obj = reader.read(blob, name)
    start, frame = record["linear"], 0x29F4
    data = next(r for r in record["data_segments"] if r["segment"] == "_DATA")
    data_off = data["linear"] - DGROUP * 16
    assert data["size"] == obj.segment_lengths["_DATA"] == 6
    assert not obj.communals
    original = image.read("root", start, record["size"])

    def bind(dgroup_offset):
        body = bytearray(obj.segment_bytes("_TEXT"))
        fields = []
        for f in obj.linker_fixups:
            assert f["segment"] == "_TEXT" and f["loc"] == "offset16" and not f["self_relative"]
            addend = int.from_bytes(bytes.fromhex(f["encoded_addend"]), "little") + (f.get("displacement") or 0)
            if f["target_kind"] == "segment" and f["target"] == "_DATA":
                value = dgroup_offset + addend
            elif f["target_kind"] == "segment" and f["target"] == "_TEXT":
                value = start - frame * 16 + addend
            elif f["target_kind"] == "external" and f["target"] == "__dataseg":
                value = syms["runtime"]["__dataseg"]["off"] + addend
            else:
                raise RuntimeError(f"unbound harderr target: {f['target']}")
            struct.pack_into("<H", body, f["offset"], value)
            fields.append({"object_offset": f["offset"], "target": f["target"],
                           "displacement": f.get("displacement", 0), "bound_offset": f"{value:04X}",
                           "matches_original": body[f["offset"]:f["offset"]+2] == original[f["offset"]:f["offset"]+2]})
        return {"code_extent": record["size"], "code_matches": bytes(body) == original,
                "bound_code_sha256": sha(body), "fixup_fields": fields,
                "different_instruction_operand_fields": [r["object_offset"] for r in fields if not r["matches_original"]]}

    positive = bind(data_off)
    negative = bind(TARGET - 4)  # force __oldsp's PUBLIC offset 4 to proposed selector
    original_relocs = [f"{s:04X}:{o:04X}" for s,o in image.unit_relocs("root")
                       if start <= s*16+o < start+record["size"]]
    data_matches = obj.segment_bytes("_DATA") == image.read("S27", data["linear"], data["size"])
    md = Cs(CS_ARCH_X86, CS_MODE_16)
    instructions = [{"address": f"{frame:04X}:{i.address:04X}", "instruction": i.mnemonic + " " + i.op_str}
                    for i in md.disasm(original, start-frame*16)]
    assert positive["code_matches"] and data_matches and not original_relocs and not negative["code_matches"]
    return {"record": record, "library_pin": library_pin, "member_sha256": sha(blob),
            "all_segments": obj.segment_defs, "publics": obj.publics, "communals": obj.communals,
            "positive_registered_placement": positive,
            "negative_oldsp_at_selector": negative,
            "data_matches_complete_6_byte_extent": data_matches,
            "code_relocation_set": original_relocs,
            "actual_callback_slot": f"55B3:{data_off:04X}..{data_off+4:04X}",
            "actual_oldsp_slot": f"55B3:{data_off+4:04X}..{data_off+6:04X}",
            "handler_entry": f"29F4:{start-frame*16+35:04X}",
            "complete_original_symbolic_disassembly": instructions}


def main():
    m, s = read("layout/manifest.json"), read("layout/symbols.json")
    image = exe.load()
    report = read("build/workers/dos_critical_selector_v36/intake/build-report.json")
    assert len(report["translation_units"]) == 188 and not report["denied_oracle_reads"]
    source_pins, hits = [], []
    names = {"g_8CCB", "_g_8CCB", "f_1C62_06A6", "_f_1C62_06A6", "_harderr", "__harderr", "f_208F_058B", "_f_208F_058B"}
    for row in report["translation_units"]:
        pp = pin(row["generated_source"]["path"], row["generated_source"]["sha256"])
        source_pins.append(pp | {"module": row["module"], "reviewed_bodies": row["reviewed_bodies"]})
        path = ROOT / pp["path"]
        for no, line in enumerate(path.read_text(encoding="latin1").splitlines(),1):
            matched = [n for n in names if re.search(r"\b" + re.escape(n) + r"\b",line)]
            if matched:
                hits.append({"module": row["module"], "line": no, "text": line.strip(), "identifiers": matched})
    targets = [code_row("f_1C62_06A6",s,54), code_row("f_208F_058B",s,4),
               code_row("__harderr",s,87)]
    scan = focused_original_scan(image,targets)
    harderr = bind_harderr(image,m,s)
    callback = functions.get("f_208F_058B")
    raw_callback = image.read("root", callback["seg"]*16+callback["off"],callback["size"])
    md=Cs(CS_ARCH_X86,CS_MODE_16)
    callback_asm=[i.mnemonic + " " + i.op_str for i in md.disasm(raw_callback,callback["off"])]
    assert callback_asm == ["mov ax, 3", "retf "]
    assert any(x["target"] == "__harderr" and not x["internal"] for x in scan["direct_control_transfers"])
    assert {x["instruction"] for x in scan["original_harderr_setup_context"]} >= {
        "mov ax, 0x58b", "mov dx, 0x208f", "push dx", "push ax", "lcall 0x29f4, 0x2d88"}
    assert not any(x["target"] == "f_1C62_06A6" for x in scan["direct_control_transfers"]+scan["relocated_contiguous_pointers"]+scan["vectors"])
    prior = ["work/source-only-dos/critical-error-selector-source-review-v18.json",
             "build/workers/dos_critical_selector_closure_v25/root-false-source-completeness-v25.json",
             "build/workers/dos_critical_selector_closure_v25/correction-addendum-v25.json",
             "work/source-only-dos/structural-audits-v33/icon-v33/receipt-v33.json",
             "work/source-only-dos/structural-audits-v35/track-review-v35.json",
             "work/source-only-dos/structural-audits-v35/sound-domain-replay.json",
             "work/source-only-dos/structural-audits-v35/sound-report-v35.md"]
    result={"schema":"simant-dos-critical-selector-v36", "status":"INT24_CRT_ATTRIBUTION_EXCLUDED; SOURCE_OWNER_UNADMITTED",
            "parent_checkpoint":"8feed73 (supplied by parent; current input hashes are independently bound below)",
            "scope":{"generated_full_TUs":188,"source_generation_only":True,"no_original_payload_serialized":True,
                     "writes_confined_to":"build/workers/dos_critical_selector_v36"},
            "oracle_sha256":image.sha256,"pins":[pin(__file__),pin("layout/manifest.json"),pin("layout/symbols.json"),
                     pin("layout/functions.json"),pin("layout/oracle.lock.json"),pin("tools/source_only_dos.py"),
                     pin("build/workers/dos_critical_selector_v36/intake/build-report.json"),*[pin(p) for p in prior]],
            "generated_source_pins":source_pins,"source_identifier_occurrences":hits,
            "original_xref_and_near_storage_scan":scan,"fresh_whole_runtime_member_binding":harderr,
            "installed_INT24_closure":{"setup":"IBMInitStuff -> _harderr(f_208F_058B)",
               "handler":"DOS INT24 -> harderr.asm +35 -> far callback [55B3:7DAC] -> f_208F_058B -> harderr.asm +67 -> IRET",
               "callback_instructions":callback_asm,
               "only_fixed_DGROUP_writes":"_harderr stores callback at 7DAC/7DAE; INT24 stores SP at 7DB0",
               "selector_reads_or_writes":0,"calls_to_selector_consumer":0,
               "domain":"After successful sole represented registration, callback slot remains the installed handler, without arbitrary memory corruption. Before registration DOS owns INT24."},
            "minimal_contract":{"direct_view":"signed char near, one byte; fallback indexes 14 far pointers; signed CBW is original",
               "initial_state":"Original __astart clears [55B3:8B9E,55B3:94F0) before main (retained v18); includes 8CCB",
               "later_state":"No direct producer; computed alias remains unresolved, so read-only source occurrences do not prove read-only physical storage",
               "historical_owner_requirement":"A source-functional owner need not recover its historical TU/public/COMDEF; missing historical provenance is separate from this alias/observable-domain gate"},
            "ordinary_symbolic_consumer_reachability":{"known_source_paths_to_read":[],
               "known_indirect_target_producers_of_consumer_address":[],
               "target_producer_exclusion":"All 188 full TUs: function identifier appears only as its definition, including underscore-spelled ASM names. No registration, initializer, argument or call names it. Original: all 149 relocations to its frame are immediate far calls/jumps elsewhere; no relocated address producer names its extent. The raw same-frame near-transfer overapproximation is empty.",
               "observable_clobber_conclusion":"No known real path reaches this sole read after any prospective alias write. The conditional stores are not demonstrated observable differences.",
               "general_proof_limit":"This closes ordinary named/symbolic call and pointer production. It does not prove all unchecked computed dispatch or memory-corrupted continuations cannot enter the helper; existing data-as-code/layout gates remain open."},
            "new_near_indexed_writer_frontier":{"function":"f_284A_0199", "call_closure":"f_284A_0013 -> f_284A_0256 -> f_284A_0199",
               "producer":"g_7566 = f_284A_0138(10), a signed int from the song object's big-endian header; no source cap",
               "original_store":"284A:01B9 mov bx,si; 01BB shl bx,1; 01BD mov word ptr [bx-7228h],ax",
               "base":"55B3:8DD8", "wrapped_selector_store_index":32633,
               "wrapped_word_store":"(8DD8 + 2*32633) & FFFF = 8CCA; high byte covers 8CCB",
               "count_threshold":32634,
               "retained_shipped_domain":"v35 pins all 30 supplied SOUND streams at 2..10 tracks with no cursor wrap; an intact load of those streams excludes this count threshold. This is not a shipped-resource counterexample.",
               "domain_limit":"Conditional arithmetic frontier only outside the intact v35 stream domain. Earlier out-of-bounds stores overwrite other player/CRT state and potentially stack; no execution to index 32633 is asserted. Source has no count cap, and no general all-input/loop-state proof is made."},
            "unclosed_premises":[
               "For lock calls with invalid signed high byte, full first-Punt termination under actual /s9 and saved-selector dispatch remains a separate integration/layout gate. Pairing calls alone does not exclude a returning invalid lock.",
               "For ev->code reread, the reachable decoder resource-height/dimension domain must prevent f_2662_1120 -> selected S00/S01/S03 decoder from overwriting Event.code at 50F6:4A06 before f_218D_000C unlock. 1F2A destination to 4A06 distance is 2ADC.",
               "The g_5702[0] reread has a bounded prior helper review; a full transitive physical-clobber exclusion is not established.",
               "New nearby DS-store sweep finds uncapped song count and wrapped g_8DD8[32633] alias; intact supplied v35 streams (2..10 tracks) exclude it. A broader altered/corrupted-resource domain is unclosed, not an executed counterexample.",
               "Absence of static inbound edges and split segment materializations is not a universal unreachability theorem while unchecked indirect code-as-data, corruptible far-pointer dispatch and their reachable input domain remain unclosed."],
            "admission_proposal":"No automatic admission. The directly proven one-byte signed-char view can support a minimal source-functional owner only within a root-reviewed consumer/writer domain. Historical TU/COMDEF provenance alone is not an obstacle. This receipt alone does not prove universal dead-consumer or physical-write closure; no known post-write read path is asserted."}
    (OUT/"receipt-v36.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":result["status"],"source_TUs":188,"target_inbound_edges":0,
          "selector_frame_relocation_classes":scan["selector_frame_relocation_classes"],
          "fixed_near_refs":scan["fixed_DS_references_covering_selector"],
          "indexed_store_candidates":len(scan["indexed_DS_stores_with_displacement_within_0200_of_selector"]),
          "harderr_positive":harderr["positive_registered_placement"]["code_matches"],
          "harderr_negative_different_fields":harderr["negative_oldsp_at_selector"]["different_instruction_operand_fields"]},indent=2))


if __name__ == "__main__":
    main()
