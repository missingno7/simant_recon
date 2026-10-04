from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pin(path: str) -> dict:
    p = ROOT / path
    return {"path": path.replace("\\", "/"), "sha256": sha(p), "size_bytes": p.stat().st_size}


receipt = json.loads((ROOT / "build/workers/dos_mono_8ed8_owner_v32/receipt.json").read_text())
src12 = (ROOT / "src/S12/m384C.c").read_text(encoding="latin1")
def function_body(symbol: str) -> str:
    at = src12.index(symbol + "(")
    brace = src12.index("{", at)
    depth = 1
    i = brace + 1
    while depth:
        if src12[i] == "{":
            depth += 1
        elif src12[i] == "}":
            depth -= 1
        i += 1
    return src12[brace + 1:i - 1]

call = function_body("o12_384C_0B76")
if not re.search(r"\bo12_384C_03D0\s*\(", call):
    raise SystemExit("source does not prove 0B76 calls 03D0")
dispatch = function_body("o12_384C_03D0")
if re.search(r"\bo12_384C_0B76\s*\(", dispatch):
    raise SystemExit("unexpected reverse edge; inspect source manually")

# Recompute the canonical-source mutator inventory independently from the pinned report.
source_paths = sorted(p for p in (ROOT / "src").rglob("*")
                      if p.is_file() and p.suffix.lower() in {".asm", ".c", ".h", ".inc"})
mut = re.compile(r"\b(?:mov\s+ss\s*,|pop\s+ss\b|lss\b)", re.I)
hits = []
for path in source_paths:
    for line_no, line in enumerate(path.read_text(encoding="latin1").splitlines(), 1):
        if mut.search(line.split(";", 1)[0]):
            hits.append((path.relative_to(ROOT).as_posix(), line_no))
if len(source_paths) != 127 or len(hits) != 12:
    raise SystemExit(f"canonical source scan changed: files={len(source_paths)} writes={len(hits)}")

# Accepted assembler source edits are literal substitutions from these pinned
# packets. Verify no replacement text introduces MOV/POP SS or LSS.
src_tool = (ROOT / "tools/source_only_dos.py").read_text(encoding="utf-8")
list_block = re.search(r"for filename in \((.*?)\):", src_tool, re.S)
if not list_block:
    raise SystemExit("could not locate source-only binding packet registry")
packet_names = re.findall(r"'([^']+\.json)'", list_block.group(1))
packet_audit = []
inserted_mutators = []
for name in packet_names:
    path = ROOT / "work/source-only-dos" / name
    packet = json.loads(path.read_text(encoding="utf-8"))
    edits = [edit for binding in packet.get("bindings", []) for edit in binding.get("edits", [])]
    for edit_index, edit in enumerate(edits):
        if mut.search(edit.get("after", "")):
            inserted_mutators.append({"packet": name, "edit_index": edit_index})
    packet_audit.append({"path": path.relative_to(ROOT).as_posix(), "sha256": sha(path),
                         "edit_count": len(edits)})
if inserted_mutators:
    raise SystemExit(f"binding substitution introduces SS mutator(s): {inserted_mutators}")

# Static-completeness substitutions replace/import C bodies only. Validate that
# each reviewed source input/override is C and that it contains no inline SS setter.
index_path = ROOT / "work/source-only-dos/static-completeness/index-v1.json"
index = json.loads(index_path.read_text(encoding="utf-8"))
strict_receipts = []
strict_source_inputs = []
inline_mutators = []
for name, entry in sorted(index["entries"].items()):
    path = ROOT / entry["path"]
    receipt_body = json.loads(path.read_text(encoding="utf-8"))
    strict_receipts.append({"path": path.relative_to(ROOT).as_posix(), "sha256": sha(path)})
    for key in ("registered_source", "source_override"):
        source = receipt_body.get(key)
        if not source or not source.get("path"):
            continue
        srcpath = ROOT / source["path"]
        if srcpath.suffix.lower() != ".c":
            raise SystemExit(f"strict static source input is not C: {source['path']}")
        raw = srcpath.read_text(encoding="latin1")
        # Strict bodies are C; only flag actual inline assembler forms or raw
        # machine-stack instruction mnemonics that a compiler extension could emit.
        body = re.sub(r"/\*.*?\*/|//[^\n]*|\"(?:\\.|[^\"])*\"|'(?:\\.|[^'])*'", " ", raw, flags=re.S)
        if re.search(r"(?:__asm|_asm|\basm\s*\{|\bmov\s+ss\s*,|\bpop\s+ss\b|\blss\b)", body, re.I):
            inline_mutators.append(source["path"])
        strict_source_inputs.append({"path": source["path"].replace("\\", "/"), "sha256": sha(srcpath)})
if inline_mutators:
    raise SystemExit(f"strict C substitutions contain possible inline SS mutator: {inline_mutators}")

static_report = "build/workers/dos_assembly_frame_inventory/ss_provenance_report.json"
static_summary = "build/workers/dos_assembly_frame_inventory/ss_provenance_summary.md"
pins = [pin(p) for p in [
    "build/workers/dos_mono_8ed8_owner_v32/receipt.json",
    "src/S12/m384C.c",
    "tools/source_only_dos.py",
    "tools/dos_source_bindings.py",
    "work/source-only-dos/static-completeness/index-v1.json",
    static_report,
    static_summary,
    "src/root/m1B73.asm",
    "src/root/m28BC.asm",
    "src/S01/m328E.asm",
]]
strict_receipt_digest = hashlib.sha256(json.dumps(strict_receipts, sort_keys=True).encode()).hexdigest()
strict_source_digest = hashlib.sha256(json.dumps(sorted(strict_source_inputs, key=lambda x: x["path"]), sort_keys=True).encode()).hexdigest()

actual_edges = {
    "call_edge": "o12_384C_0B76 -> o12_384C_03D0",
    "caller_edges": ["o12_384C_100A -> o12_384C_0B76", "o12_384C_1035 -> o12_384C_0B76"],
    "source_anchor": "src/S12/m384C.c: source body of o12_384C_0B76 calls o12_384C_03D0; o12_384C_03D0 does not call o12_384C_0B76.",
    "correction": "v32 receipt dispatch_edges first arrow is a display-direction typo; receipt is retained unchanged.",
}
addendum = {
    "schema": "simant-dos-mono-8ed8-entry-ss-v32-correction-addendum-v1",
    "status": "ADDENDUM_ONLY_V32_RECEIPT_UNCHANGED",
    "v32_receipt": pins[0],
    "dispatch_direction": actual_edges,
    "mutator_scan_scope": {
        "canonical_scan": {"extensions": [".asm", ".c", ".h", ".inc"], "files_scanned": len(source_paths),
                            "direct_setter_count": len(hits), "setter_modules": ["src/root/m1B73.asm", "src/root/m28BC.asm"],
                            "report_and_summary_pins": [pins[5], pins[6]]},
        "strict_static_substitutions": {
            "index_pin": pins[4], "review_receipt_count": len(strict_receipts),
            "review_receipt_set_sha256": strict_receipt_digest,
            "source_input_count": len(strict_source_inputs), "source_input_set_sha256": strict_source_digest,
            "all_inputs_are_c": True, "inline_ss_setter_count": len(inline_mutators),
            "interpretation": "These reviewed substitutions import C function bodies; no inline assembly or SS-setting instruction was found in their pinned source inputs/overrides.",
        },
        "accepted_source_binding_substitutions": {
            "packet_count": len(packet_audit), "packets": packet_audit,
            "replacement_text_ss_setter_count": len(inserted_mutators),
            "interpretation": "The assembler binding substitutions are pinned literal edits; their replacement text adds no MOV SS, POP SS, or LSS setter. Thus the 127-file canonical scan is complete for runtime SS mutators after the reviewed strict substitutions.",
        },
    },
    "evidence_pins": pins[1:] + [pin("work/source-only-dos/driver-ss-frame-bindings-v1.json")],
}
out_path = OUT / "correction-addendum-v1.json"
out_path.write_text(json.dumps(addendum, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"path": str(out_path.relative_to(ROOT)), "sha256": sha(out_path),
                  "canonical_files": len(source_paths), "canonical_setters": len(hits),
                  "strict_receipts": len(strict_receipts), "strict_source_inputs": len(strict_source_inputs),
                  "binding_packets": len(packet_audit), "addendum_pins": len(addendum["evidence_pins"])}, indent=2))
