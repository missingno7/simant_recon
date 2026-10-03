#!/usr/bin/env python3
"""Research-only proof that MSC crt0 clears the input-ring interval before main.

This script deliberately lives outside the source-only build lane. It reads the pinned
oracle through tools.runtime.verify_all() to bind the accepted runtime member, but emits
only hashes, typed ranges, and symbolic disassembly strings. It never writes generated
source, canonical layout, or original instruction/data bytes.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "build" / "workers" / "dos_queue_lifetime" / "report.json"
CAPSTONE_ROOT = Path("C:/tools/capstone-5.0.3")
EXPECTED_CRT0_SHA256 = "2e9a254b9bd00ea59884089e78e951f0e40343e11d24976f32d9582f4ded259d"
QUEUE_STRIDE = 16


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def hx(value: int) -> str:
    return f"0x{value:04x}"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit("queue lifetime research failed closed: " + message)


def integer_literal(source: str, pattern: str, label: str) -> int:
    match = re.search(pattern, source, re.IGNORECASE | re.DOTALL)
    require(match is not None, f"could not locate {label} source anchor")
    return int(match.group(1), 0)


def one_immediate(instructions: list, mnemonic: str, register: str) -> tuple[int, object]:
    hits = [i for i in instructions if i.mnemonic == mnemonic and
            re.match(rf"\s*{re.escape(register)}\s*,\s*0x([0-9a-f]+)\s*$", i.op_str, re.I)]
    require(bool(hits), f"expected {mnemonic} {register}, immediate instruction")
    # __astart has an earlier DI setup for the DGROUP segment; the final DI immediate
    # before REP STOSB is the clear start. The analogous last CX immediate is _end.
    selected = hits[-1]
    return int(re.search(r"0x([0-9a-f]+)", selected.op_str, re.I).group(1), 16), selected


def symbolic(insn) -> str:
    return f"{insn.mnemonic} {insn.op_str}".rstrip()


def main() -> None:
    require(CAPSTONE_ROOT.is_dir(), f"pinned Capstone directory absent: {CAPSTONE_ROOT}")
    sys.path.insert(0, str(CAPSTONE_ROOT))
    sys.path.insert(0, str(ROOT / "tools"))
    import capstone
    import runtime

    from capstone import CS_ARCH_X86, CS_MODE_16, Cs

    lock = json.loads((ROOT / "layout" / "oracle.lock.json").read_text())
    manifest = json.loads((ROOT / "layout" / "manifest.json").read_text())
    oracle_pin = lock["executable"]
    exe = runtime.exemod.load()
    require(exe.sha256 == oracle_pin["sha256"], "loaded oracle differs from oracle.lock.json")

    runtime_pin = manifest["runtime"]["libraries"]["llibcr.lib"]
    runtime_path = Path(runtime.LIBS["llibcr.lib"])
    runtime_hash = sha256(runtime_path.read_bytes())
    require(runtime_hash == runtime_pin["sha256"], "llibcr.lib differs from accepted manifest pin")

    # This is the read-only runtime verifier used by the accepted-library evidence path.
    # collect contains bound code for local disassembly only; no bytes are serialized.
    collect: dict = {}
    rows, derived, conflicts, anchors = runtime.verify_all(collect)
    crt_rows = [r for r in rows if r["member"] == "dos\\crt0.asm"]
    require(len(crt_rows) == 1, "expected one located dos\\crt0.asm row")
    crt = crt_rows[0]
    require(crt["exact"] and not crt["reasons"], "dos\\crt0.asm did not bind exact")
    require(crt["member_sha256"] == EXPECTED_CRT0_SHA256, "crt0 member hash changed")
    accepted = [r for r in manifest["runtime"]["members"]
                if r["member"] == crt["member"] and r["linear"] == crt["linear"]]
    require(len(accepted) == 1 and accepted[0]["member_sha256"] == crt["member_sha256"],
            "exact crt0 is not the accepted manifest member")

    # Match the OMF member corresponding to the exact verifier result, so each placement
    # anchor can be reported with its fixup kind/displacement as well as its instruction.
    selected_obj = None
    for candidates in runtime.load_members():
        for placement, obj, _blob in candidates:
            if (placement["member"], placement["linear"], placement["module_index"]) == (
                    crt["member"], crt["linear"], crt["module_index"]):
                selected_obj = obj
                break
        if selected_obj is not None:
            break
    require(selected_obj is not None, "could not recover selected crt0 OMF metadata")

    # Queue extent comes from the current, accepted source model and accesses in 1B73;
    # this does not claim the historical COMDEF owner or any padding around the ring.
    timer_source = (ROOT / "src" / "root" / "m1FD2.c").read_text()
    asm_source = (ROOT / "src" / "root" / "m1B73.asm").read_text()
    capacity = integer_literal(timer_source,
        r"\bint\s+g_5FF0\s*=\s*(0x[0-9a-f]+|\d+)\s*;", "g_5FF0 capacity")
    queue_base = integer_literal(timer_source,
        r"\bstruct\s+Timer\s+g_5FF2\s*=\s*\{.*?\(int\)\s*(0x[0-9a-f]+|\d+)",
        "g_5FF2 queue-base initializer")
    for proc in ("_f_1B73_032E", "_f_1B73_036E"):
        body_match = re.search(rf"(?ms)^{proc}\s+proc\b(.*?)^{proc}\s+endp\b", asm_source)
        require(body_match is not None, f"missing source procedure {proc}")
        body = body_match.group(1)
        require("mov si, word ptr _g_5FFE" in body and "add si, bx" in body,
                f"{proc} does not source its ring pointer from _g_5FFE")
        require(len(re.findall(r"(?m)^\s*shl bx, 1\s*$", body)) == 4,
                f"{proc} does not scale its slot index by 16")
    require(capacity == 7, "g_5FF0 current source capacity is not 7")
    queue_end = queue_base + capacity * QUEUE_STRIDE

    md = Cs(CS_ARCH_X86, CS_MODE_16)
    instructions_by_member: dict[tuple[str, int], list] = {}
    all_instructions = []
    for key, bound_segments in collect.items():
        for bound in bound_segments:
            insns = list(md.disasm(bound["bytes"], bound["start"]))
            instructions_by_member[key] = instructions_by_member.get(key, []) + insns
            all_instructions.extend((key, insn) for insn in insns)

    # Every data-placement anchor reported by verify_all for _edata/_end, with the
    # instruction which owns the relocation field. No raw code bytes are recorded.
    placement_sites = []
    fixup_at: dict[int, dict] = {}
    for fixup in selected_obj.linker_fixups:
        if fixup["target"] in ("_edata", "_end"):
            fixup_at[crt["linear"] + fixup["offset"]] = fixup
    for symbol in ("_edata", "_end"):
        key = f"ext::{symbol}:DGROUP"
        require(key in derived and len(derived[key]) == 1,
                f"{symbol} has no single verifier-derived DGROUP placement")
        values = derived[key]
        value = next(iter(values))
        for member, site in values[value]:
            matching = [(k, i) for k, i in all_instructions
                        if k[0] == member and i.address <= site < i.address + i.size]
            require(len(matching) == 1, f"could not uniquely decode {symbol} anchor at {site:#x}")
            _, insn = matching[0]
            fixup = fixup_at.get(site)
            require(fixup is not None and fixup["target"] == symbol,
                    f"missing OMF fixup for {symbol} at {site:#x}")
            disp = int(fixup.get("displacement") or 0)
            if disp >= 0x8000:
                disp -= 0x10000
            placement_sites.append({
                "symbol": symbol,
                "derived_dgroup_offset": hx(value),
                "member": member,
                "site_linear": hx(site),
                "fixup": {"loc": fixup["loc"], "width": fixup["width"],
                          "signed_displacement": disp},
                "instruction_linear": hx(insn.address),
                "instruction": symbolic(insn),
            })

    edata = next(iter(derived["ext::_edata:DGROUP"]))
    end = next(iter(derived["ext::_end:DGROUP"]))
    crt_insns = instructions_by_member[(crt["member"], crt["linear"])]
    rep_positions = [n for n, i in enumerate(crt_insns)
                     if "stosb" in i.mnemonic and i.mnemonic.startswith("rep")]
    require(len(rep_positions) == 1, "expected one REP STOSB in crt0")
    rep_index = rep_positions[0]
    rep = crt_insns[rep_index]
    clear_start, mov_di = one_immediate(crt_insns[:rep_index], "mov", "di")
    clear_end, mov_cx = one_immediate(crt_insns[:rep_index], "mov", "cx")
    require(clear_start == edata and clear_end == end,
            "decoded clear bounds disagree with verifier-derived _edata/_end")
    require(any(i.mnemonic == "cld" for i in crt_insns[:rep_index]), "no CLD before REP STOSB")
    require(any(i.mnemonic == "sub" and i.op_str == "cx, di" for i in crt_insns[:rep_index]),
            "no SUB CX,DI before REP STOSB")
    require(any(i.mnemonic == "xor" and i.op_str == "ax, ax" for i in crt_insns[:rep_index]),
            "no zeroing of AL before REP STOSB")
    require(any(i.mnemonic == "push" and i.op_str == "ss" for i in crt_insns[:rep_index]) and
            any(i.mnemonic == "pop" and i.op_str == "es" for i in crt_insns[:rep_index]),
            "no SS-to-ES setup before REP STOSB")
    dgroup_insn = next((i for i in crt_insns if i.mnemonic == "mov" and
                        i.op_str == f"di, {hx(runtime.DGROUP)}"), None)
    ss_insn = next((i for i in crt_insns if i.mnemonic == "mov" and i.op_str == "ss, di"), None)
    require(dgroup_insn is not None and ss_insn is not None and dgroup_insn.address < ss_insn.address < rep.address,
            "could not establish SS=DGROUP before ES receives SS")
    es_setup = None
    for n in range(len(crt_insns) - 2):
        if (crt_insns[n].mnemonic, crt_insns[n].op_str,
                crt_insns[n + 1].mnemonic, crt_insns[n + 1].op_str,
                crt_insns[n + 2].mnemonic) == ("push", "ss", "pop", "es", "cld"):
            if ss_insn.address < crt_insns[n].address < mov_di.address:
                es_setup = crt_insns[n:n + 3]
    require(es_setup is not None, "could not establish ES=SS and DF=0 before REP STOSB")

    main_fixups = [f for f in selected_obj.linker_fixups
                   if f["target"] == "_main" and f["target_kind"] == "external"]
    require(len(main_fixups) == 1 and main_fixups[0]["loc"] == "pointer32",
            "expected one far _main fixup in crt0")
    main_fixup = main_fixups[0]
    main_site = crt["linear"] + main_fixup["offset"]
    main_matches = [(k, i) for k, i in all_instructions
                    if k[0] == crt["member"] and i.address <= main_site < i.address + i.size]
    require(len(main_matches) == 1, "could not decode crt0 _main call site")
    main_insn = main_matches[0][1]
    main_identity = runtime.match.obj_name_lookup("_main")
    require(main_identity is not None and main_identity.get("kind") == "code" and
            main_identity.get("unit") == "root", "_main is not bound to a root code symbol")
    main_claims = [(key, mod, claim) for key, mod in manifest["modules"].items()
                   for claim in mod.get("claims", []) if claim.get("name") == "main"]
    require(len(main_claims) == 1, "expected one accepted canonical main claim")
    main_module_key, main_module, main_claim = main_claims[0]
    require((main_module["unit"], main_module["seg"], main_claim["off"]) ==
            (main_identity["unit"], main_identity["seg"], main_identity["off"]),
            "runtime _main identity disagrees with accepted main claim")
    require(main_insn.address > rep.address, "_main call precedes the clear")
    main_index = next(n for n, i in enumerate(crt_insns) if i.address == main_insn.address)
    post_clear_to_main = [symbolic(i) for i in crt_insns[rep_index:main_index + 1]]

    source_paths = (ROOT / "src" / "root" / "m1FD2.c", ROOT / "src" / "root" / "m1B73.asm")
    report = {
        "schema": "dos-queue-lifetime-research-v1",
        "research_only": True,
        "purpose": "prove startup-zero lifecycle for the source/access-derived 7x16-byte input ring",
        "no_original_bytes_emitted": True,
        "pins": {
            "oracle": {k: oracle_pin[k] for k in ("name", "sha256", "size")},
            "oracle_lock_sha256": sha256((ROOT / "layout" / "oracle.lock.json").read_bytes()),
            "runtime_library": {"name": "llibcr.lib", "path": str(runtime_path).replace("\\", "/"),
                                "sha256": runtime_hash, "matches_accepted_manifest": True},
            "crt0_member": {"member": crt["member"], "module_index": crt["module_index"],
                            "linear": hx(crt["linear"]), "size": crt["size"],
                            "segment": crt["segment"], "sha256": crt["member_sha256"],
                            "exact_runtime_verifier_result": True,
                            "accepted_manifest_match": True},
            "sources": {str(p.relative_to(ROOT)).replace("\\", "/"): sha256(p.read_bytes())
                        for p in source_paths},
            "research_script_sha256": sha256(Path(__file__).read_bytes()),
            "capstone_version": capstone.__version__,
        },
        "runtime_verifier": {
            "exact_members": sum(1 for r in rows if r["exact"]),
            "total_members": len(rows),
            "placement_conflicts": conflicts,
            "edata_end_anchor_counts": {k: anchors.get(k, 0)
                for k in ("ext::_edata:DGROUP", "ext::_end:DGROUP")},
            "all_edata_end_references": sorted(placement_sites,
                key=lambda r: (r["symbol"], int(r["site_linear"], 16))),
        },
        "queue_access_extent": {
            "base_dgroup_offset": hx(queue_base),
            "capacity_slots": capacity,
            "slot_stride_bytes": QUEUE_STRIDE,
            "interval": {"start_inclusive": hx(queue_base), "end_exclusive": hx(queue_end),
                         "length_bytes": queue_end - queue_base},
            "base_source_anchor": "src/root/m1FD2.c: g_5FF2.Timer.ticks initializer; current symbol _g_5FFE",
            "capacity_source_anchor": "src/root/m1FD2.c: g_5FF0 initializer",
            "access_source_anchors": ["src/root/m1B73.asm: _f_1B73_032E", "src/root/m1B73.asm: _f_1B73_036E"],
            "stride_source_fact": "each access shifts BX left four times then adds it to _g_5FFE",
            "base_current_source_symbol": "_g_5FFE (g_5FF2.Timer.ticks field currently carries the pointer value)",
            "original_comdef_owner": "unknown; this is not an ownership claim",
            "padding_extent": "unknown; only the 112-byte accessed interval is established",
        },
        "startup_clear": {
            "function": "__astart",
            "code_segment": crt["segment"],
            "memory_segment": "DGROUP",
            "symbolic_instructions": [
                {"linear": hx(i.address), "text": symbolic(i)}
                for i in [dgroup_insn, ss_insn, *es_setup]
            ] + [
                {"linear": hx(i.address), "text": symbolic(i)}
                for i in crt_insns if mov_di.address <= i.address <= rep.address
            ],
            "clear_interval": {"segment": "DGROUP", "start_inclusive": hx(clear_start),
                               "end_exclusive": hx(clear_end), "length_bytes": clear_end - clear_start,
                               "element": "byte", "fill": 0},
            "clear_instruction": {"linear": hx(rep.address), "text": symbolic(rep)},
            "queue_fully_contained": clear_start <= queue_base and queue_end <= clear_end,
            "queue_intersects_clear": clear_start < queue_end and queue_base < clear_end,
            "main_path_symbolic_instructions": post_clear_to_main,
            "main_call": {
                "instruction_linear": hx(main_insn.address), "text": symbolic(main_insn),
                "fixup_site_linear": hx(main_site), "fixup_kind": main_fixup["loc"],
                "obj_symbol": "_main", "canonical_symbol": main_claim["name"],
                "canonical_module": main_module_key,
                "canonical_location": f"{main_claim['seg']:04X}:{main_claim['off']:04X}",
                "claim_source": main_module["source"],
                "resolved_identity": {"unit": main_identity["unit"],
                                      "segment": f"{main_identity['seg']:04X}",
                                      "offset": f"{main_identity['off']:04X}"},
                "occurs_after_clear": main_insn.address > rep.address,
            },
        },
        "verdict": {
            "startup_zeroing_lifecycle": "confirmed for [DGROUP:0x91b0, DGROUP:0x9220) before the accepted root main call",
            "historical_array_owner": "unresolved; no original COMDEF/TU ownership identity is asserted",
            "per_enqueue_slot_prefix": "not reset by the enqueue writes; this report proves startup zeroing only",
        },
    }
    require(report["queue_access_extent"]["interval"]["length_bytes"] == 112,
            "unexpected queue interval size")
    require(report["startup_clear"]["queue_fully_contained"], "queue is not wholly in clear interval")
    require(main_insn.mnemonic == "lcall", "crt0 main invocation is not a far call")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(f"wrote {OUT}")
    print(f"clear {hx(clear_start)}..{hx(clear_end)} contains queue {hx(queue_base)}..{hx(queue_end)}")
    print(f"crt0 {crt['member_sha256']} exact; main {main_claim['unit']}:{main_claim['seg']:04X}:{main_claim['off']:04X}")


if __name__ == "__main__":
    main()
