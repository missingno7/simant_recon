"""Read-only audit of the remaining S27 data-debt spans.

Run from the repository root with ``python build/workers/behavior_data_audit/audit.py``.
All generated files remain under build/workers; canonical ownership is untouched.
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

try:
    import capstone
except ImportError:
    sys.path.insert(0, "C:/tools/capstone-5.0.3")
    import capstone
from capstone import Cs, CS_ARCH_X86, CS_MODE_16
from omf import OmfReader


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    outdir = ROOT / "build/workers/behavior_data_audit"
    outdir.mkdir(parents=True, exist_ok=True)
    debt_path = ROOT / "work/takeover/behavioral-oracle/data-debt.json"
    debt = json.loads(debt_path.read_text(encoding="utf-8"))
    oracle = exe.load()
    md = Cs(CS_ARCH_X86, CS_MODE_16)
    md.detail = True

    spans = []
    for item in debt["literal_spans"]:
        if item["id"] == "far_data":
            lo = hi = None
        else:
            lo = int(item["dgroup_offset"], 16)
            hi = lo + item["size"]
        spans.append({"id": item["id"], "lo": lo, "hi": hi, "size": item["size"]})

    refs: dict[str, list[dict]] = {s["id"]: [] for s in spans}
    immediates: dict[str, list[dict]] = {s["id"]: [] for s in spans}
    scanned_functions = 0
    for f in functions.table()["functions"]:
        unit, seg, off, size = f["unit"], f["seg"], f["off"], f["size"]
        base, data = oracle.unit_bytes(unit)
        linear = seg * 16 + off
        body = data[linear - base:linear - base + size]
        scanned_functions += 1
        for ins in md.disasm(body, off):
            for op in ins.operands:
                if op.type == capstone.x86.X86_OP_MEM:
                    mem = op.mem
                    # An absolute or indexed DGROUP/SS reference has a fixed displacement.
                    if mem.segment not in (0, capstone.x86.X86_REG_SS, capstone.x86.X86_REG_CS,
                                           capstone.x86.X86_REG_ES):
                        continue
                    if mem.segment in (capstone.x86.X86_REG_CS, capstone.x86.X86_REG_ES):
                        continue
                    disp = mem.disp & 0xFFFF
                    for s in spans:
                        if s["lo"] is not None and s["lo"] <= disp < s["hi"]:
                            refs[s["id"]].append({
                                "unit": unit, "function": functions.name_of(unit, seg, off),
                                "function_address": f"{seg:04X}:{off:04X}",
                                "instruction_address": f"{ins.address:04X}",
                                "mnemonic": ins.mnemonic, "operands": ins.op_str,
                                "disp": f"{disp:04X}",
                            })
                elif op.type == capstone.x86.X86_OP_IMM:
                    imm = op.imm & 0xFFFF
                    for s in spans:
                        if s["lo"] is not None and s["lo"] <= imm < s["hi"]:
                            immediates[s["id"]].append({
                                "unit": unit, "function": functions.name_of(unit, seg, off),
                                "function_address": f"{seg:04X}:{off:04X}",
                                "instruction_address": f"{ins.address:04X}",
                                "mnemonic": ins.mnemonic, "operands": ins.op_str,
                                "value": f"{imm:04X}",
                            })

    s27 = oracle.sections[27]
    reloc_rows = []
    for item in debt["literal_spans"]:
        for r in item["relocations_inside"]:
            lin = int(r["linear"], 16)
            fileoff = s27.data_file_offset + (lin - s27.load_linear)
            relocs = [{"site": f"{a:04X}:{b:04X}", "linear": f"{a * 16 + b:05X}"}
                      for a, b in s27.relocs if a * 16 + b == lin]
            reloc_rows.append({"span": item["id"], "relative_offset": r["relative_offset"],
                               "linear": r["linear"], "file_offset": fileoff,
                               "word": oracle.raw[fileoff:fileoff + 2].hex(" "),
                               "relocation_sites": relocs})

    # Check the exact pinned MSC library member whose 14-byte _DATA body equals 79F0.
    toolchain = json.loads((ROOT / "layout/toolchain.json").read_text(encoding="utf-8"))
    libpath = Path("C:/tools/msc-6.00/LIB/llibcr.lib")
    library = libpath.read_bytes()
    reader = OmfReader(communals=True)
    fdata = None
    fheap_users = []
    for idx, (name, blob) in enumerate(reader.split_library(library)):
        obj = reader.read(blob, name)
        if name.lower() == "fdata.asm":
            fdata = {
                "member": name, "module_index": idx, "member_sha256": sha(blob),
                "segments": obj.segment_defs,
                "data_hex": obj.segments.get("_DATA", b"").hex(" "),
                "publics": obj.publics, "externals": obj.externals,
            }
        if any("__fheap" in str(e).lower() for e in obj.externals):
            fheap_users.append(name)
    if fdata:
        fdata["library_path"] = str(libpath).replace("\\", "/")
        fdata["library_sha256"] = sha(library)
        fdata["original_span_matches_member_data"] = (
            bytes.fromhex(next(s["bytes_hex"] for s in debt["literal_spans"]
                               if s["id"] == "dgroup_79f0"))
            == bytes.fromhex(fdata["data_hex"]))
        fdata["external_consumers_in_library"] = sorted(fheap_users)

    dgroup_linear = 0x55B30
    adjacent_runtime = []
    verify = ROOT / "build/runtime/verify.json"
    if verify.exists():
        vr = json.loads(verify.read_text(encoding="utf-8"))
        for row in vr.get("data", []):
            linear = row.get("linear")
            size = row.get("size", 0)
            if linear is not None and linear + size >= dgroup_linear + 0x79E0 \
                    and linear <= dgroup_linear + 0x7A10:
                adjacent_runtime.append(row)

    tail = debt["common_tail_overlap"][0]
    evidence = {
        "schema": "s27-data-debt-reference-audit-v1",
        "oracle_sha256": oracle.sha256,
        "data_debt_sha256": sha(debt_path.read_bytes()),
        "manifest_sha256": sha((ROOT / "layout/manifest.json").read_bytes()),
        "provenance_sha256": sha((ROOT / "build/link/provenance.json").read_bytes()),
        "section27": {"load_segment": s27.load_seg,
                       "data_file_offset": s27.data_file_offset,
                       "data_size": len(s27.data), "data_sha256": sha(s27.data)},
        "game_functions_scanned": scanned_functions,
        "function_reference_scan": {"direct_data_operands": refs,
                                     "immediate_address_candidates": immediates,
                                     "scope": "original game code/functions in tools/functions.py; not arbitrary runtime code or dynamic pointers"},
        "data_fixup_sites": reloc_rows,
        "runtime_fdata_member_candidate": fdata,
        "runtime_data_layout_neighbors": adjacent_runtime,
        "common_tail": {
            **tail,
            "section27_file_end": s27.data_file_offset + len(s27.data),
            "file_size": len(oracle.raw),
            "tail_bytes_hex": oracle.raw[tail["file_range"][0]:tail["file_range"][1]].hex(" "),
            "whole_tail_sha256": sha(oracle.raw[tail["file_range"][0]:]),
        },
        "toolchain_library_pin": toolchain.get("libraries", {}).get("llibcr.lib"),
    }
    (outdir / "reference-scan.json").write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
