"""Independent source-only ownership and MSC/RTLink probe for InitSimYard scalars."""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import uuid


ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
OUT.mkdir(parents=True, exist_ok=True)
RUN_ID = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid.uuid4().hex[:8]
RUN = OUT / "runs" / RUN_ID
RUN.mkdir(parents=True, exist_ok=False)
sys.path.insert(0, str(ROOT / "tools"))
import compiler
import csrc
import source_only_dos as dos
from omf import OmfReader

DENIED_READS = dos.install_input_guard()
compiler.WORK = RUN / "compiler-work"

INTAKE_PATH = ROOT / "work/source-only-dos/compile-and-intake-v1.json"
STATIC_INDEX_PATH = ROOT / "work/source-only-dos/static-completeness/index-v1.json"
SYMBOLS_PATH = ROOT / "layout/symbols.json"
MANIFEST_PATH = ROOT / "layout/manifest.json"
TOOLCHAIN_PATH = ROOT / "layout/toolchain.json"
INIT_PATH = ROOT / "src/S06/m35F5.c"
SAVE_PATH = ROOT / "src/S09/m35F5.c"
CALLER_PATH = ROOT / "src/S08/m35F5.c"

LONGS = ("fd_50F6_0220", "fd_50F6_107E", "fd_50F6_109C")
INTS = (
    "fd_50F6_0202", "fd_50F6_022C", "fd_50F6_023E", "fd_50F6_0244",
    "fd_50F6_0246", "fd_50F6_0364", "fd_50F6_036E", "fd_50F6_046A",
    "fd_50F6_0470", "fd_50F6_047A", "fd_50F6_04BE", "fd_50F6_04C6",
    "fd_50F6_04E4", "fd_50F6_0506", "fd_50F6_0624", "fd_50F6_07C2",
    "fd_50F6_105C", "fd_50F6_1066", "fd_50F6_108C", "fd_50F6_10A0",
    "fd_50F6_10B0", "fd_50F6_10BC",
)
NAMES = LONGS + INTS
WIDTH = {name: (4 if name in LONGS else 2) for name in NAMES}
INIT_VALUES = {
    "fd_50F6_109C": 0, "fd_50F6_107E": 0, "fd_50F6_0220": 0,
    "fd_50F6_0202": 0, "fd_50F6_022C": 0, "fd_50F6_023E": 0,
    "fd_50F6_0244": 0, "fd_50F6_0246": 0, "fd_50F6_0364": 1,
    "fd_50F6_036E": 1, "fd_50F6_046A": 0, "fd_50F6_0470": 0,
    "fd_50F6_047A": 0, "fd_50F6_04BE": 0xFA, "fd_50F6_04C6": 0x96,
    "fd_50F6_04E4": 0, "fd_50F6_0506": 0, "fd_50F6_0624": 2,
    "fd_50F6_07C2": -1, "fd_50F6_105C": 0, "fd_50F6_1066": 0,
    "fd_50F6_108C": 1, "fd_50F6_10A0": 0, "fd_50F6_10B0": 0,
    "fd_50F6_10BC": -1,
}
PROVIDER_FLAGS = ["/AL", "/Os", "/Gs"]
MASK_RE = re.compile(r"/\*.*?\*/|//[^\n]*|\"(?:\\.|[^\"\\])*\"|'(?:\\.|[^'\\])*'", re.S)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def repo_path(path: str) -> Path:
    return ROOT / path.replace("\\", "/")


def pin(path: Path, expected: str | None = None) -> dict:
    raw, result = dos.pin(path)
    if expected is not None and digest(raw) != expected:
        raise RuntimeError(f"stale pin: {path}")
    return result


def checked_source(ref: dict, label: str) -> dict:
    path = repo_path(ref["path"])
    actual = pin(path, ref["sha256"])
    if ref.get("size") is not None and actual["size"] != ref["size"]:
        raise RuntimeError(f"{label} source size changed: {ref['path']}")
    return {"path": actual["path"].replace("\\", "/"), "sha256": actual["sha256"],
            "size": actual["size"]}


def load_source_sets() -> tuple[list[dict], list[dict], list[dict], list[dict]]:
    intake = json.loads(INTAKE_PATH.read_text(encoding="utf-8"))
    if intake.get("schema") != "simant-source-only-dos-build-v1" or len(intake.get("translation_units", [])) != 127:
        raise RuntimeError("canonical intake no longer contains the pinned 127 translation units")
    canonical = []
    for tu in intake["translation_units"]:
        row = checked_source(tu["source"], "canonical")
        canonical.append(row | {"module": tu["module"]})

    index = json.loads(STATIC_INDEX_PATH.read_text(encoding="utf-8"))
    if (index.get("schema") != "simant-dos-strict-static-index-v1"
            or len(index.get("entries", {})) != 29):
        raise RuntimeError("strict effective-source index changed from 29 entries")
    effective, receipts = [], []
    for function, ref in sorted(index["entries"].items()):
        receipt_path = repo_path(ref["path"])
        receipt_pin = pin(receipt_path, ref["sha256"])
        if receipt_pin["size"] != ref["size"]:
            raise RuntimeError(f"effective receipt size changed: {ref['path']}")
        receipts.append(receipt_pin)
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        selected = receipt.get("registered_source", {})
        role = "registered effective whole module"
        if function == "DrawBalloons":
            selected = receipt.get("audit", {}).get("source", {})
            role = "corrected effective whole module"
        if (not selected.get("whole_module") or not selected.get("path")
                or selected.get("module") is None or selected.get("sha256") is None):
            raise RuntimeError(f"effective whole source is incomplete: {function}")
        src_pin = checked_source(selected, "effective")
        effective.append(src_pin | {"module": selected["module"], "function": function, "role": role})
    if len({r["path"] for r in canonical + effective}) != 156:
        raise RuntimeError("canonical and effective source rows do not resolve to 156 distinct sources")
    asm_paths = sorted((ROOT / "src").rglob("*.asm"))
    if len(asm_paths) != 29:
        raise RuntimeError(f"expected 29 current source ASM files, found {len(asm_paths)}")
    asm_sources = [pin(path) for path in asm_paths]
    for row in asm_sources:
        row["path"] = row["path"].replace("\\", "/")
    return canonical, effective, receipts, asm_sources


def mask_comments_literals(text: str) -> str:
    return MASK_RE.sub(lambda m: "".join("\n" if ch == "\n" else " " for ch in m.group()), text)


def classify(code_line: str, name: str) -> str:
    q = re.escape(name)
    lhs = r"\b" + q + r"\b(?:\s*(?:\[[^\]]+\]|\.\w+|->\w+))*"
    if re.search(r"(?:\+\+|--)\s*" + lhs + r"|" + lhs + r"\s*(?:\+\+|--)", code_line):
        return "write_increment"
    if re.search(lhs + r"\s*(?:[+*/%&|^\-]?=)(?!=)", code_line):
        return "write_assignment"
    if re.search(r"(?<!&)&(?!&)\s*" + q + r"\b", code_line):
        return "address_escape"
    if re.search(r"\b(?:extern|static|typedef)\b[^;\n]*\b" + q + r"\b", code_line):
        return "declaration"
    if re.search(r"\b" + q + r"\s*(?:\[|\.|->)", code_line):
        return "indexed_or_member"
    if re.search(r"\b" + q + r"\b\s*(?:[+\-*/%<>]|&&|\|\||&|\|)", code_line) or re.search(
            r"(?:[+\-*/%<>]|&&|\|\||&|\|)\s*\b" + q + r"\b", code_line):
        return "numeric_expression"
    return "read_or_expression"


def function_ranges(text: str) -> list[tuple[int, int, str]]:
    try:
        src = csrc.Source(text)
        return sorted((fn.s, fn.e, fn.name) for fn in src.functions())
    except Exception:
        # The identifier scan remains complete; some canonical files contain
        # legacy lexical forms that the helper cannot parse for function labels.
        return []


def asm_numeric_scan(asm_sources: list[dict], symbols: dict) -> dict:
    references = {name: {"identifier": [], "offset_literal_coincidences": [], "direct_address_syntax": []} for name in NAMES}
    segment_literals = []
    literal_rx = re.compile(r"(?i)(?<![0-9a-f])(?:0x([0-9a-f]+)|([0-9a-f]+)h)(?![0-9a-f])")
    far_rx = re.compile(r"(?i)\b(?:0x)?50f6h?\s*:\s*(?:0x)?[0-9a-f]+h?\b")
    for source in asm_sources:
        raw_lines = repo_path(source["path"]).read_text(encoding="latin1").splitlines()
        for line_no, raw_line in enumerate(raw_lines, 1):
            code_line = raw_line.split(";", 1)[0]
            for name in NAMES:
                if re.search(r"\b" + re.escape(name) + r"\b", code_line, re.I):
                    references[name]["identifier"].append({"path": source["path"], "line": line_no, "text": raw_line.strip()})
            for hit in literal_rx.finditer(code_line):
                value = int(hit.group(1) or hit.group(2), 16)
                for name in NAMES:
                    row = symbols[name]
                    width = WIDTH[name]
                    if row["off"] <= value < row["off"] + width:
                        receipt = {"path": source["path"], "line": line_no, "literal": hit.group(),
                            "value": value, "text": raw_line.strip()}
                        references[name]["offset_literal_coincidences"].append(receipt)
                        if re.search(r"\[[^\]]*" + re.escape(hit.group()) + r"[^\]]*\]", code_line, re.I) or far_rx.search(code_line):
                            references[name]["direct_address_syntax"].append(receipt)
                if value == 0x50F6:
                    segment_literals.append({"path": source["path"], "line": line_no,
                        "literal": hit.group(), "far_address_context": bool(far_rx.search(code_line)),
                        "text": raw_line.strip()})
            if far_rx.search(code_line):
                segment_literals.append({"path": source["path"], "line": line_no,
                    "literal": "far_address", "far_address_context": True, "text": raw_line.strip()})
    return {"pinned_source_count": len(asm_sources), "source_pins": asm_sources,
        "target_identifier_hits": references,
        "literal_50F6_or_far_address_hits": segment_literals,
        "result": {"target_identifier_hit_count": sum(len(v["identifier"]) for v in references.values()),
            "offset_literal_coincidence_count": sum(len(v["offset_literal_coincidences"]) for v in references.values()),
            "direct_address_syntax_count": sum(len(v["direct_address_syntax"]) for v in references.values()),
            "segment_or_far_address_hit_count": len(segment_literals)},
        "interpretation": "All 29 tracked src ASM files were scanned for selected symbol spellings, hex tokens that numerically coincide with each source-typed byte span, and explicit 50F6:offset far-address syntax. Coincidental immediate/data literals are reported separately; only bracketed or segmented address syntax is counted as a direct-address candidate."}


def source_scan(canonical: list[dict], effective: list[dict], receipts: list[dict],
                asm_sources: list[dict], symbols: dict) -> dict:
    src_sets = (("canonical_127", canonical), ("effective_strict_29", effective))
    addresses: dict[tuple[int, int], list[str]] = {}
    for name, row in symbols.items():
        if row.get("seg") == 0x50F6:
            addresses.setdefault((row["seg"], row["off"]), []).append(name)
    aliases: dict[str, list[str]] = {}
    for name in NAMES:
        row = symbols.get(name)
        if not row:
            raise RuntimeError("selected scalar lacks a FAR_BSS symbol row: " + name)
        exact = sorted(addresses.get((row["seg"], row["off"]), []))
        history = [h.get("was") for h in row.get("history", []) if h.get("was")]
        aliases[name] = sorted(set(exact + history + [name]))

    per_name = {name: [] for name in NAMES}
    for set_name, rows in src_sets:
        for source in rows:
            raw = repo_path(source["path"]).read_text(encoding="latin1")
            code = mask_comments_literals(raw)
            lines = raw.splitlines()
            code_lines = code.splitlines()
            ranges = function_ranges(raw)
            for target in NAMES:
                for alias in aliases[target]:
                    token = re.compile(r"\b" + re.escape(alias) + r"\b")
                    for match in token.finditer(code):
                        line_no = code.count("\n", 0, match.start()) + 1
                        line_start = code.rfind("\n", 0, match.start()) + 1
                        fn = next((f for lo, hi, f in ranges if lo <= match.start() < hi), None)
                        code_line = code_lines[line_no - 1] if line_no <= len(code_lines) else ""
                        text_line = lines[line_no - 1].strip() if line_no <= len(lines) else ""
                        access = classify(code_line, alias)
                        in_asm = bool(re.search(r"(?:__asm|_asm|\basm\b)", code_line, re.I))
                        per_name[target].append({"set": set_name, "path": source["path"],
                            "module": source.get("module"), "function": fn, "line": line_no,
                            "spelling": alias, "access": access, "inline_asm_context": in_asm,
                            "text": text_line})
    for name in NAMES:
        uniq = {}
        for row in per_name[name]:
            key = (row["set"], row["path"], row["line"], row["spelling"])
            uniq[key] = row
        per_name[name] = sorted(uniq.values(), key=lambda r: (r["set"], r["path"], r["line"]))

    input_pins = [pin(path) for path in (INTAKE_PATH, STATIC_INDEX_PATH, SYMBOLS_PATH,
        MANIFEST_PATH, TOOLCHAIN_PATH, ROOT / "tools/compiler.py", ROOT / "tools/csrc.py",
        ROOT / "tools/omf.py", ROOT / "tools/source_only_dos.py", INIT_PATH, SAVE_PATH, CALLER_PATH)]
    source_set_file = RUN / "source-pins.json"
    source_set_doc = {"schema": "simant-init-sim-yard-scalars-source-pins-v22",
        "counts": {"canonical_127": len(canonical), "effective_strict_29": len(effective),
                   "unique_source_paths": len({r["path"] for r in canonical + effective}),
                   "tracked_src_asm": len(asm_sources)},
        "canonical": canonical, "effective": effective, "strict_receipts": receipts,
        "asm_sources": asm_sources}
    source_set_file.write_text(json.dumps(source_set_doc, indent=2) + "\n", encoding="utf-8")
    scan_doc = {"schema": "simant-init-sim-yard-scalars-source-scan-v22",
        "source_pin_artifact": pin(source_set_file), "common_inputs": input_pins,
        "address_rows": {name: {"segment": symbols[name]["seg"], "offset": symbols[name]["off"],
                                 "historical": f"{symbols[name]['seg']:04X}:{symbols[name]['off']:04X}",
                                 "registered_exact_base_names": sorted(addresses[(symbols[name]["seg"], symbols[name]["off"])])}
                         for name in NAMES},
        "targets": per_name, "assembly_numeric_scan": asm_numeric_scan(asm_sources, symbols),
        "scan_limits": ["C identifiers are scanned in all pinned effective source files after masking comments and literals.",
                        "No original executable, reconstructed image, absolute-address cast, or build output was read.",
                        "ASM evidence here covers inline ASM text in the pinned C inputs; binary disassembly is outside this bounded source-only investigation."]}
    out = RUN / "source-scan.json"
    out.write_text(json.dumps(scan_doc, indent=2) + "\n", encoding="utf-8")
    return scan_doc


def save_rec_rows() -> tuple[dict, dict]:
    text = SAVE_PATH.read_text(encoding="latin1")
    lines = text.splitlines()
    start = next(i for i, line in enumerate(lines) if re.search(r"struct SaveRec far fd_4E4B_0000\s*\[\s*308\s*\]", line))
    end = next(i for i in range(start + 1, len(lines)) if lines[i].strip() == "};")
    rows = {name: [] for name in NAMES}
    for i in range(start + 1, end):
        line = lines[i]
        for name in NAMES:
            m = re.search(r"\{\s*(\d+)\s*,\s*(\d+)\s*,\s*\(void\s+far\s*\*\)\s*&\s*" + re.escape(name) + r"\s*\}", line)
            if m:
                size, count = int(m.group(1)), int(m.group(2))
                rows[name].append({"source": "src/S09/m35F5.c", "line": i + 1,
                    "row_number_1based": sum(1 for prior in lines[start + 1:i] if re.match(r"\s*\{", prior)) + 1,
                    "source_text": line.strip(), "size": size, "count": count,
                    "serialized_bytes": size * count})
    for name in NAMES:
        expected = [{"size": WIDTH[name], "count": 1, "serialized_bytes": WIDTH[name]}] if name not in ("fd_50F6_0364", "fd_50F6_036E") else []
        observed = [{k: r[k] for k in ("size", "count", "serialized_bytes")} for r in rows[name]]
        if observed != expected:
            raise RuntimeError(f"SaveRec source view mismatch for {name}: {observed}")
    load_line = next((i + 1, line.strip()) for i, line in enumerate(lines) if "read(fd, p->data" in line)
    save_line = next((i + 1, line.strip()) for i, line in enumerate(lines) if "write(fd, p->data" in line)
    return rows, {"source": pin(SAVE_PATH), "table_declaration": {"line": start + 1, "text": lines[start].strip()},
        "record_definition": {"line": 14, "text": "struct SaveRec { int size; int count; void far *data; };"},
        "target_rows": rows, "saved_target_total_bytes": sum(r[0]["serialized_bytes"] for r in rows.values() if r),
        "raw_load": {"line": load_line[0], "text": load_line[1], "byte_count": "p->count * p->size"},
        "raw_save": {"line": save_line[0], "text": save_line[1], "byte_count": "p->count * p->size"},
        "field_schema_validation": False,
        "interpretation": "The rows expose exact raw byte spans for 23 fields only; they do not close arbitrary LoadGame inputs or gameplay indexing domains."}


def init_reset_receipt(scan: dict) -> dict:
    text = INIT_PATH.read_text(encoding="latin1")
    src = csrc.Source(text)
    fn = src.function("o06_35F5_0000")
    start_line = text.count("\n", 0, fn.head_s) + 1
    body = text[fn.body.s:fn.body.e]
    reset = {}
    for name in NAMES:
        matches = []
        absolute = fn.body.s
        for line in body.splitlines(keepends=True):
            if re.search(r"\b" + re.escape(name) + r"\s*=", line):
                m = re.search(r"\b" + re.escape(name) + r"\s*=\s*([^;]+);", line)
                if m:
                    expr = m.group(1).strip()
                    matches.append({"line": text.count("\n", 0, absolute) + 1,
                                    "source_text": line.strip(), "expression": expr})
            absolute += len(line)
        if len(matches) != 1:
            raise RuntimeError(f"expected one direct InitSimYard reset assignment for {name}")
        reset[name] = matches[0]
    call_refs = []
    for source_path in (CALLER_PATH, ROOT / "src/S09/m35F5.c", ROOT / "src/S15/m384C.c"):
        for no, line in enumerate(source_path.read_text(encoding="latin1").splitlines(), 1):
            if re.search(r"\bo06_35F5_0000\s*\(", line):
                call_refs.append({"path": source_path.relative_to(ROOT).as_posix(), "line": no, "text": line.strip()})
    rand_yard_calls = []
    for row in (ROOT / "src").rglob("*.c"):
        for no, line in enumerate(row.read_text(encoding="latin1").splitlines(), 1):
            if re.search(r"\bRandYard\s*\(", line):
                rand_yard_calls.append({"path": row.relative_to(ROOT).as_posix(), "line": no, "text": line.strip()})
    return {"reset_function": {"source": pin(INIT_PATH), "label_comment": "InitSimYard",
            "identifier": "o06_35F5_0000", "definition_line": start_line,
            "typed_declarations": {name: (lambda r: {"source": r["path"], "line": r["line"],
                "spelling": r["spelling"], "source_text": r["text"]})(next(r for r in scan["targets"][name]
                if r["path"] == "src/S06/m35F5.c" and r["access"] == "declaration")) for name in NAMES},
            "direct_reset_assignments": reset,
            "call_sites_for_reset_identifier": call_refs,
            "RandYard_source_call_sites": rand_yard_calls,
            "dynamic_first_write_claim": False,
            "lifetime_limit": "This is a source reset receipt, not a complete caller-order proof; pre-reset use and load/new-game behavior stay open."}}


def member_candidates(scan: dict, save_rows: dict, reset: dict, symbols: dict) -> list[dict]:
    rows = []
    for name in NAMES:
        refs = scan["targets"][name]
        typed_decl = [r for r in refs if r["access"] == "declaration" and
                      re.search(r"\b" + ("long" if name in LONGS else "int") + r"\s+far\s+" + re.escape(r["spelling"]), r["text"])]
        raw_view_decl = [r for r in refs if r["access"] == "declaration" and
                         re.search(r"unsigned\s+char\s+far\s+" + re.escape(r["spelling"]) + r"\s*\[\s*\]", r["text"])]
        if not typed_decl:
            raise RuntimeError("natural source scalar declaration not found for " + name)
        escaped = [r for r in refs if r["access"] == "address_escape"]
        expected_save = bool(save_rows[name])
        if any(r["path"] != "src/S09/m35F5.c" for r in escaped):
            raise RuntimeError("non-SaveRec escape keeps scalar owner open: " + name)
        if len(escaped) != (1 if expected_save else 0):
            raise RuntimeError("address escapes and raw SaveRec membership disagree: " + name)
        symbol = symbols[name]
        exact = scan["address_rows"][name]["registered_exact_base_names"]
        width = WIDTH[name]
        interior = sorted((n, row["off"] - symbol["off"]) for n, row in symbols.items()
            if row.get("seg") == symbol["seg"] and symbol["off"] < row.get("off", -1) < symbol["off"] + width)
        if exact != [name] or interior:
            raise RuntimeError(f"registry overlap found for {name}: {exact} / {interior}")
        access_counts = Counter(r["access"] for r in refs)
        asm_refs = [r for r in refs if r["inline_asm_context"]]
        if asm_refs:
            raise RuntimeError("source inline-ASM token requires separate review for " + name)
        numeric = [r for r in refs if r["access"] == "numeric_expression"]
        direct_view = next(r for r in typed_decl if r["path"] == "src/S06/m35F5.c")
        rows.append({"name": name, "source_type": "signed long" if name in LONGS else "signed int",
            "source_extent_bytes": width, "extent_basis": ["complete C scalar type declaration in source-only DOS code; MSC large-model width verified by provider COMDEF"] +
                (["one exact SaveRec row has size equal to source width and count=1"] if expected_save else ["no SaveRec view; extent rests on typed scalar declaration and compiler control"]),
            "registered_address": scan["address_rows"][name]["historical"],
            "registered_exact_base_names": exact, "registered_interior_names_within_source_extent": interior,
            "typed_declaration_count": len(typed_decl), "direct_typed_view": {"source": direct_view["path"],
                "line": direct_view["line"], "text": direct_view["text"]},
            "raw_byte_placeholder_declaration_count": len(raw_view_decl), "SaveRec": save_rows[name],
            "init_reset": reset["reset_function"]["direct_reset_assignments"][name],
            "source_access_counts": dict(access_counts), "numeric_expression_count": len(numeric),
            "source_scan_target_ref": f"source-scan.json#/targets/{name}",
            "address_escape_count": len(escaped),
            "address_escape_refs": [{"path": r["path"], "line": r["line"], "spelling": r["spelling"]} for r in escaped],
            "inline_asm_source_reference_count": len(asm_refs),
            "unresolved_domains": ["historical COMDEF-producing module identity is not established",
                "dynamic first-use and full lifetime order across gameplay/caller paths are not closed",
                "raw SaveRec LoadGame accepts byte spans without validating target field layout",
                "numeric/gameplay index ranges are not recovered by this scalar storage owner"]})
    return rows


def save_compile_artifact(tag: str, source: str, profile: str = "msc600ax",
                          flags: list[str] | None = None) -> tuple[bytes, dict, object]:
    result = compiler.compile_c(source, profile, flags or PROVIDER_FLAGS, basename=tag, keep=True)
    if not result.ok or result.obj is None:
        raise RuntimeError(f"compile failed for {tag}:\n{result.log}")
    artifact_dir = RUN / "compile-artifacts"
    artifact_dir.mkdir(exist_ok=True)
    src_path = artifact_dir / f"{tag}.C"
    obj_path = artifact_dir / f"{tag}.OBJ"
    log_path = artifact_dir / f"{tag}.LOG"
    src_path.write_text(source, encoding="ascii", newline="\r\n")
    obj_path.write_bytes(result.obj)
    log_path.write_text(result.log, encoding="latin1")
    artifacts = [pin(src_path), pin(obj_path), pin(log_path)]
    parsed = OmfReader(communals=True).read(result.obj, f"{tag}.OBJ")
    target_pointer_fixups = [row for row in parsed.linker_fixups
        if row.get("target") in {"_" + name for name in NAMES}
        and row.get("loc") == "pointer32" and row.get("width") == 4]
    return result.obj, {"tag": tag, "profile": profile,
        "flags": list(flags or PROVIDER_FLAGS) + list(compiler.toolchain()["profiles"][profile].get("required_flags", [])),
        "argv": result.argv, "artifacts": artifacts,
        "communal_rows": parsed.communals,
        "segment_lengths": parsed.segment_lengths,
        "segment_names": sorted(parsed.segments),
        "publics": parsed.publics,
        "external_symbols": parsed.externals,
        "target_pointer_fixups": target_pointer_fixups}, parsed


def provider_source(type_override: dict[str, str] | None = None,
                    initializer: dict[str, str] | None = None) -> str:
    type_override = type_override or {}
    initializer = initializer or {}
    lines = ["/* Data-only source functional owner candidate: InitSimYard scalars. */"]
    for name in NAMES:
        ctype = type_override.get(name, "long" if name in LONGS else "int")
        suffix = " = " + initializer[name] if name in initializer else ""
        lines.append(f"{ctype} far {name}{suffix};")
    return "\n".join(lines) + "\n"


def expected_comdefs() -> list[dict]:
    # MSC emits scalar FAR commons as a byte-count COMDEF, not a typed array.
    return [{"name": "_" + name, "kind": "far", "count": WIDTH[name],
             "element_size": 1, "length": WIDTH[name]} for name in NAMES]


def normalize_comdefs(rows: list[dict]) -> list[dict]:
    return sorted(({k: row[k] for k in ("name", "kind", "count", "element_size", "length")}
                   for row in rows), key=lambda r: r["name"])


def runtime_sources() -> dict[str, str]:
    owner_decls = "".join(f"extern {'long' if n in LONGS else 'int'} far {n};\n" for n in NAMES)
    patterns = {}
    for i, n in enumerate(NAMES):
        if n in LONGS:
            patterns[n] = 0x11223344 + i * 0x010101
        elif n == "fd_50F6_10BC":
            patterns[n] = -1
        elif n == "fd_50F6_0364":
            patterns[n] = -2
        else:
            patterns[n] = 0x1100 + i * 3
    zero_checks = " || ".join(f"{n} != 0L" if n in LONGS else f"{n} != 0" for n in NAMES)
    writes = "\n".join(f"    {n} = {patterns[n]}{'L' if n in LONGS else ''};" for n in NAMES)
    typed_checks = " || ".join(f"{n} != {patterns[n]}{'L' if n in LONGS else ''}" for n in NAMES)
    raw_rows = [n for n in NAMES if n not in ("fd_50F6_0364", "fd_50F6_036E")]
    row_init = "\n".join(f"    {{{WIDTH[n]}, 1, (void far *)&{n}}}," for n in raw_rows)
    raw_checks = []
    table_checks = []
    for i, n in enumerate(raw_rows):
        value = patterns[n] & ((1 << (8 * WIDTH[n])) - 1)
        table_checks.append(f"    if (InitSimYardSaveRec[{i}].size != {WIDTH[n]} || InitSimYardSaveRec[{i}].count != 1 || InitSimYardSaveRec[{i}].data != (void far *)&{n}) goto fail;")
        raw_checks += [f"p = (unsigned char far *)InitSimYardSaveRec[{i}].data;"]
        for j in range(WIDTH[n]):
            raw_checks.append(f"if (p[{j}] != 0x{(value >> (8*j)) & 0xff:02x}) goto fail;")
    positive = (owner_decls +
        "struct SaveRec { int size; int count; void far *data; };\n"
        f"struct SaveRec far InitSimYardSaveRec[{len(raw_rows)}] = {{\n{row_init}\n}};\n"
        "extern int far puts(char far *text);\nint main(void)\n{\n"
        f"    unsigned char far *p;\n    if ({zero_checks}) goto fail;\n"
        + "\n".join(table_checks) + "\n" + writes + "\n"
        + f"    if ({typed_checks}) goto fail;\n"
        + "    if ((long)fd_50F6_10BC >= 0L || (long)fd_50F6_0364 >= 0L) goto fail;\n"
        + "\n".join("    " + line if not line.startswith("if (") else "    " + line for line in raw_checks)
        + "\n    puts(\"PASS\"); return 0;\nfail: puts(\"FAIL\"); return 1;\n}\n")

    signed_bad = ("extern unsigned int far fd_50F6_10BC;\n"
        "extern int far puts(char far *text);\nint main(void)\n{\n"
        "    fd_50F6_10BC = 0xffffU;\n"
        "    if ((long)fd_50F6_10BC < 0L) { puts(\"PASS\"); return 0; }\n"
        "    puts(\"FAIL\"); return 1;\n}\n")

    shifted = (owner_decls +
        "struct SaveRec { int size; int count; void far *data; };\n"
        "struct SaveRec far ShiftedSaveRec[1] = {\n"
        "    {4, 1, (void far *)((unsigned char far *)&fd_50F6_0220 + 1)}\n};\n"
        "extern int far puts(char far *text);\nint main(void)\n{\n"
        "    unsigned char far *p;\n"
        "    if (fd_50F6_0220 != 0L) goto fail;\n"
        "    fd_50F6_0220 = 0x11223344L;\n"
        "    p = (unsigned char far *)ShiftedSaveRec[0].data;\n"
        "    if (p[0] != 0x44 || p[1] != 0x33 || p[2] != 0x22 || p[3] != 0x11) goto fail;\n"
        "    puts(\"PASS\"); return 0;\nfail: puts(\"FAIL\"); return 1;\n}\n")

    overflow = ("extern long far fd_50F6_0220;\n"
        "extern int far puts(char far *text);\nint main(void)\n{\n"
        "    if (fd_50F6_0220 != 0L) goto fail;\n"
        "    fd_50F6_0220 = 0x11223344L;\n"
        "    if (fd_50F6_0220 != 0x11223344L) goto fail;\n"
        "    puts(\"PASS\"); return 0;\nfail: puts(\"FAIL\"); return 1;\n}\n")
    return {"positive_typed_raw_startup0": positive, "unsigned_semantic_contrast": signed_bad,
            "shifted_saverec_base": shifted, "short_owner_overflow_observation": overflow}


def save_probe_source(tag: str, source: str) -> dict:
    path = RUN / "compile-artifacts" / f"{tag}.C"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source, encoding="ascii", newline="\r\n")
    return pin(path)


def map_data_receipt(map_text: str) -> dict:
    lines = map_text.splitlines()
    section = ""
    resident, overlay = [], []
    data_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped == "Resident":
            section = "resident"
            continue
        if stripped.startswith("Overlay"):
            section = "overlay"
            continue
        if stripped.startswith("Section#"):
            section = "sections"
        relevant = any(re.search(r"\b" + re.escape(n) + r"\b", line, re.I)
                       for n in ("FAR_BSS", "FAR_DATA", "_BSS", "_DATA"))
        if section == "resident" and relevant and re.match(r"^[0-9A-F]{5}H\s", stripped):
            resident.append(stripped)
        elif section == "overlay" and relevant and re.match(r"^[0-9A-F]{5}H\s", stripped):
            overlay.append(stripped)
        if any(re.search(r"\b" + re.escape(n) + r"\b", line, re.I) for n in ("FAR_BSS", "FAR_DATA", "_BSS", "_DATA")):
            if re.match(r"^\s*[0-9A-F]{5}H\s", line):
                data_lines.append(stripped)
    def publics(header: str) -> dict[str, str]:
        start = next((i for i, line in enumerate(lines) if header in line), None)
        if start is None:
            return {}
        found = {}
        for line in lines[start + 1:]:
            if any(title in line for title in ("Publics by Name", "Publics by Value", "Line Numbers for", "Module Summary")):
                break
            m = re.match(r"\s*([0-9A-F]{4}:[0-9A-F]{4})\s+\w+\s+(_fd_50F6_[0-9A-F]{4})\s*$", line, re.I)
            if m:
                found[m.group(2).lower()] = m.group(1).upper()
        return found
    by_name, by_value = publics("Publics by Name"), publics("Publics by Value")
    target_keys = {("_" + n).lower() for n in NAMES}
    picked_name = {key: by_name[key] for key in sorted(target_keys) if key in by_name}
    picked_value = {key: by_value[key] for key in sorted(target_keys) if key in by_value}
    return {"resident_map_section_rows": resident, "overlay_map_section_rows": overlay,
            "relevant_data_segment_rows_from_both_sections": data_lines,
            "target_public_addresses_by_name": picked_name,
            "target_public_addresses_by_value": picked_value,
            "Name_and_Value_public_relations_exact": picked_name == picked_value and len(picked_name) == len(NAMES)}


def run_link_case(profile_name: str, case_name: str, consumer_obj: bytes, owner_obj: bytes,
                  runtimes: list[dict], linker: dict, runner: dict, tool_dir: Path,
                  linker_libs: list[dict]) -> dict:
    directory = RUN / "link-runs" / profile_name / case_name
    directory.mkdir(parents=True, exist_ok=False)
    (directory / "CRT.OBJ").write_bytes(consumer_obj)
    (directory / "OWNER.OBJ").write_bytes(owner_obj)
    for row in runtimes:
        shutil.copyfile(row["path"], directory / Path(row["path"]).name.upper())
    lnk = ("OUTPUT PROBE\r\nMAP = PROBE S,N,A,L\r\nNODEFLIB\r\n"
           "LIBRARY LLIBCR, LIBH\r\nFILE CRT\r\n"
           "BEGINAREA\r\nSECTION FILE OWNER\r\nENDAREA\r\n")
    (directory / "PROBE.LNK").write_bytes(lnk.encode("ascii"))
    (directory / "RTLINK.CFG").write_bytes(b"SYNTAX = FREEFORMAT\r\n")
    (directory / "RUN.BAT").write_bytes((
        f"@echo off\r\nD:\\{linker['executable']} @PROBE.LNK < NUL > LINK.LOG\r\n"
        "PROBE.EXE > RUN.LOG\r\n").encode("ascii"))
    conf_lines = []
    for section, settings in runner["conf"].items():
        conf_lines.append("[" + section + "]")
        conf_lines += [f"{key}={value}" for key, value in settings.items()]
    conf_lines += ["[autoexec]", f'mount c "{directory.resolve()}"',
        f'mount d "{tool_dir.resolve()}" -ro', "c:", "call RUN.BAT", "exit"]
    (directory / "dosbox.conf").write_text("\n".join(conf_lines) + "\n", encoding="ascii")
    env = os.environ.copy()
    env.update(SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy")
    timed_out = False
    try:
        run = subprocess.run([runner["path"], "-conf", str(directory / "dosbox.conf"),
            "-fastlaunch", "-exit", "-nomenu"], cwd=directory, env=env,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=90,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        exit_code = run.returncode
    except subprocess.TimeoutExpired:
        timed_out, exit_code = True, -1
    log_path = directory / "RUN.LOG"
    link_path = directory / "LINK.LOG"
    map_path = directory / "PROBE.MAP"
    exe_path = directory / "PROBE.EXE"
    actual = log_path.read_text(encoding="latin1", errors="replace").strip() if log_path.exists() else "NO RUN.LOG"
    link_log = link_path.read_text(encoding="latin1", errors="replace") if link_path.exists() else ""
    map_text = map_path.read_text(encoding="latin1", errors="replace") if map_path.exists() else ""
    output_paths = [p for p in (exe_path, map_path, link_path, log_path) if p.is_file()]
    input_paths = [directory / name for name in ("CRT.OBJ", "OWNER.OBJ", "PROBE.LNK",
        "RTLINK.CFG", "RUN.BAT", "dosbox.conf") if (directory / name).is_file()]
    return {"linker": profile_name, "case": case_name, "expected_log": None,
        "actual_log": actual, "emulator_exit": exit_code, "timed_out": timed_out,
        "linker_produced_executable": exe_path.exists(),
        "stdout_exact": {"text": log_path.read_bytes().decode("latin1") if log_path.exists() else "",
            "hex": log_path.read_bytes().hex() if log_path.exists() else ""},
        "map_sections": map_data_receipt(map_text),
        "staged_inputs": [pin(p) for p in input_paths],
        "staged_runtime_library_names": sorted(Path(row["path"]).name.upper() for row in runtimes),
        "raw_outputs": [pin(p) for p in output_paths]}


def link_expect(row: dict, expected: str, return_zero: bool = True) -> dict:
    passed = row["actual_log"] == expected and not row["timed_out"] and row["linker_produced_executable"]
    if return_zero:
        passed = passed and row["emulator_exit"] == 0
    passed = passed and row["map_sections"]["Name_and_Value_public_relations_exact"]
    row["expected_log"] = expected
    row["passed"] = passed
    return row


def run_matrix(objects: dict[str, bytes], manifest: dict, tc: dict, save_rows: dict,
               symbols: dict) -> tuple[list[dict], list[dict], dict]:
    runtimes = list(manifest["runtime"]["libraries"].values())
    runtime_names = {Path(row["path"]).stem.upper() for row in runtimes}
    if not {"LLIBCR", "LIBH"}.issubset(runtime_names):
        raise RuntimeError("pinned runtime manifest lacks LLIBCR/LIBH")
    receipts, compile_receipts = [], {}
    sources = runtime_sources()
    crts = {}
    for tag, src in (("CRTPOS", sources["positive_typed_raw_startup0"]),
                     ("CRTSIG", sources["unsigned_semantic_contrast"]),
                     ("CRTSHFT", sources["shifted_saverec_base"]),
                     ("CRTOVR", sources["short_owner_overflow_observation"])):
        save_probe_source(tag, src)
        raw, receipt, parsed = save_compile_artifact(tag, src)
        crts[tag] = raw
        compile_receipts[tag] = receipt
        if tag in ("CRTPOS", "CRTSHFT"):
            data_segment = f"{tag}5_DATA"
            table_fixups = [f for f in parsed.linker_fixups
                if f.get("segment") == data_segment and f.get("loc") == "pointer32" and f.get("width") == 4
                and f.get("target") in {"_" + name for name in NAMES}]
            if tag == "CRTPOS":
                expected_targets = {"_" + n for n in NAMES if n not in ("fd_50F6_0364", "fd_50F6_036E")}
                if {f["target"] for f in table_fixups} != expected_targets or any(f["encoded_addend"] != "00000000" for f in table_fixups):
                    raise RuntimeError("positive test SaveRec OMF pointer target/addend matrix is incomplete or shifted")
                source_saved = [n for n in NAMES if save_rows[n]]
                table_fixups = sorted(table_fixups, key=lambda f: f["offset"])
                if len(source_saved) != len(table_fixups):
                    raise RuntimeError("raw SaveRec source/fixture pointer matrix count differs")
                receipt["saverec_pointer_target_addend_matrix"] = [{
                    "fixture_row_1based": index + 1,
                    "fixture_pointer_fixup_offset": fix["offset"],
                    "target": source_saved[index],
                    "target_registered_address": f"{symbols[source_saved[index]]['seg']:04X}:{symbols[source_saved[index]]['off']:04X}",
                    "source_saverec_row_1based": save_rows[source_saved[index]][0]["row_number_1based"],
                    "source_saverec_line": save_rows[source_saved[index]][0]["line"],
                    "object_target": fix["target"], "fixup_width": fix["width"],
                    "fixup_location": fix["loc"], "encoded_addend": fix["encoded_addend"],
                    "displacement": fix["displacement"]} for index, fix in enumerate(table_fixups)]
            if tag == "CRTSHFT" and (len(table_fixups) != 1 or table_fixups[0]["target"] != "_fd_50F6_0220"
                    or table_fixups[0]["encoded_addend"] != "01000000"):
                raise RuntimeError("shifted SaveRec OMF pointer does not carry the expected +1 addend")
            if tag == "CRTSHFT":
                receipt["saverec_pointer_target_addend_matrix"] = [{
                    "fixture_row_1based": 1, "fixture_pointer_fixup_offset": table_fixups[0]["offset"],
                    "target": "fd_50F6_0220", "target_registered_address": f"{symbols['fd_50F6_0220']['seg']:04X}:{symbols['fd_50F6_0220']['off']:04X}",
                    "source_saverec_row_1based": save_rows["fd_50F6_0220"][0]["row_number_1based"],
                    "source_saverec_line": save_rows["fd_50F6_0220"][0]["line"],
                    "object_target": table_fixups[0]["target"], "fixup_width": table_fixups[0]["width"],
                    "fixup_location": table_fixups[0]["loc"], "encoded_addend": table_fixups[0]["encoded_addend"],
                    "displacement": table_fixups[0]["displacement"], "intentional_shift_bytes": 1}]
            receipt.pop("target_pointer_fixups", None)

    case_specs = [
        ("typed_raw_startup0", crts["CRTPOS"], objects["positive"], "PASS", True),
        ("unsigned_signedness_contrast", crts["CRTSIG"], objects["positive"], "FAIL", True),
        ("shifted_SaveRec_base", crts["CRTSHFT"], objects["positive"], "FAIL", True),
        ("initialized_owner_startup_contrast", crts["CRTPOS"], objects["initialized"], "FAIL", True),
        ("short_owner_overflow_observation_non_gating", crts["CRTOVR"], objects["wrong_width"], "PASS", True),
    ]
    linker_pins = {}
    runtime_pins = [pin(Path(row["path"]), row["sha256"]) for row in runtimes]
    runner_pins = {}
    for linker_name in ("rtlink400", "rtlink610"):
        linker = tc["linkers"][linker_name]
        tool_dir = compiler.pinned_tree(linker)
        linker_libs = [pin(Path(linker["directory"]) / rel, sha)
                       for rel, sha in linker["files"].items()]
        runner = tc["runners"][linker["runner"]]
        runner_pins.setdefault(linker["runner"], pin(Path(runner["path"]), runner["sha256"]))
        linker_pins[linker_name] = {"executable": pin(Path(linker["directory"]) / linker["executable"]),
            "profile_files": linker_libs,
            "pinned_runtime_tree_files": [pin(tool_dir / rel, sha) for rel, sha in linker["files"].items()]}
        for case_name, consumer, owner, expected, gate in case_specs:
            row = run_link_case(linker_name, case_name, consumer, owner, runtimes,
                                linker, runner, tool_dir, linker_libs)
            row = link_expect(row, expected)
            row["gating_for_owner_evidence"] = gate and not case_name.endswith("non_gating")
            if case_name.endswith("non_gating"):
                row["passed"] = row["actual_log"] == expected and not row["timed_out"] and row["linker_produced_executable"]
                row["gating_for_owner_evidence"] = False
                row["interpretation"] = "A successful read/write past the short owner's declared COMDEF is an overread observation only; it is excluded from the extent proof."
            receipts.append(row)
    compiler_profile = tc["profiles"]["msc600ax"]
    compiler_runner = tc["runners"][compiler_profile["runner"]] if compiler_profile.get("runner") else tc["runner"]
    compiler_pins = {"profile_files": [pin(Path(compiler_profile["directory"]) / rel, sha)
            for rel, sha in compiler_profile["files"].items()],
        "runner": pin(Path(compiler_runner["path"]), compiler_runner["sha256"])}
    return receipts, {"runtime_libraries": runtime_pins, "compiler": compiler_pins,
        "linkers": linker_pins, "runners": runner_pins}, compile_receipts


def main() -> None:
    symbols_doc = json.loads(SYMBOLS_PATH.read_text(encoding="utf-8"))
    symbols = symbols_doc["data"]
    canonical, effective, receipts, asm_sources = load_source_sets()
    scan = source_scan(canonical, effective, receipts, asm_sources, symbols)
    save_rows, save_evidence = save_rec_rows()
    reset = init_reset_receipt(scan)
    candidates = member_candidates(scan, save_rows, reset, symbols)

    owner_src = provider_source()
    save_probe_source("OWNV22", owner_src)
    owner_raw, owner_receipt, owner_omf = save_compile_artifact("OWNV22", owner_src)
    expected = expected_comdefs()
    actual = normalize_comdefs(owner_omf.communals)
    if actual != sorted(expected, key=lambda r: r["name"]):
        raise RuntimeError("natural data-only provider COMDEFs differ from exact expected 25 typed far scalars")

    wrong_width_src = provider_source(type_override={"fd_50F6_0220": "int"})
    save_probe_source("WIDBAD", wrong_width_src)
    width_raw, width_receipt, width_omf = save_compile_artifact("WIDBAD", wrong_width_src)
    width_comdefs = normalize_comdefs(width_omf.communals)
    width_should_differ = (width_comdefs != actual and len(width_comdefs) == len(actual)
        and next(r for r in width_comdefs if r["name"] == "_fd_50F6_0220")["length"] == 2)
    if not width_should_differ:
        raise RuntimeError("wrong-width OMF contrast did not change the single long owner's COMDEF")

    signed_src = provider_source(type_override={"fd_50F6_10BC": "unsigned int"})
    save_probe_source("SIGOWN", signed_src)
    signed_raw, signed_receipt, signed_omf = save_compile_artifact("SIGOWN", signed_src)
    signed_shape_same = normalize_comdefs(signed_omf.communals) == actual
    if not signed_shape_same:
        raise RuntimeError("signedness contrast changed a storage shape unexpectedly")

    init_src = provider_source(initializer={"fd_50F6_109C": "1L"})
    save_probe_source("INITBAD", init_src)
    init_raw, init_receipt, init_omf = save_compile_artifact("INITBAD", init_src)
    init_expected_names = {r["name"] for r in actual} - {"_fd_50F6_109C"}
    init_has_no_communal_for_initialized_target = ({r["name"] for r in normalize_comdefs(init_omf.communals)} == init_expected_names)
    if not init_has_no_communal_for_initialized_target:
        raise RuntimeError("initialized owner control retained a COMDEF for initialized long")

    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    tc = compiler.toolchain()
    runtime_rows, runtime_tool_pins, consumer_omf = run_matrix({"positive": owner_raw, "wrong_width": width_raw,
        "signed": signed_raw, "initialized": init_raw}, manifest, tc, save_rows, symbols)

    evidence = {"schema": "simant-init-sim-yard-scalars-owner-candidate-v22",
        "status": "RESEARCH_ONLY_NOT_ADMITTED", "admission_eligible": False,
        "root_reviewed": False, "root_claimed": False, "production_source_changed": False,
        "source_scan_artifact": pin(RUN / "source-scan.json"),
        "source_pin_artifact": pin(RUN / "source-pins.json"),
        "effective_source_counts": {"canonical_127": len(canonical), "effective_strict_29": len(effective),
            "unique_source_paths": len({r["path"] for r in canonical + effective}), "tracked_src_asm": len(asm_sources)},
        "function_and_call_alias_receipt": reset["reset_function"],
        "SaveRec_evidence": save_evidence, "members": candidates,
        "source_extent_basis": {"sum_typed_bytes": sum(WIDTH.values()),
            "signed_int_count": len(INTS), "signed_long_count": len(LONGS),
            "saved_member_count": sum(bool(save_rows[n]) for n in NAMES),
            "saved_raw_byte_total": save_evidence["saved_target_total_bytes"],
            "unsaved_members": [n for n in NAMES if not save_rows[n]],
            "no_extent_from_address_gaps": True},
        "natural_provider": {"source": pin(RUN / "compile-artifacts/OWNV22.C"),
            "source_sha256": pin(RUN / "compile-artifacts/OWNV22.C")["sha256"],
            "source_contents": "25 uninitialized signed int/long far tentative definitions only",
            "data_only": True, "profile": "msc600ax", "flags": owner_receipt["flags"],
            "object": owner_receipt["artifacts"][1], "compiler_log": owner_receipt["artifacts"][2],
            "expected_COMDEFs": expected,
            "actual_COMDEFs": actual, "exact_COMDEF_set_match": True,
            "object_segments": owner_receipt["segment_lengths"],
            "omf_shape": {"communal_rows": normalize_comdefs(owner_omf.communals),
                "segment_lengths": owner_omf.segment_lengths, "publics": owner_omf.publics,
                "external_symbols": owner_omf.externals}},
        "compile_controls": {"wrong_width": {"profile": "msc600ax", "flags": width_receipt["flags"],
                "source": width_receipt["artifacts"][0], "object": width_receipt["artifacts"][1],
                "compiler_log": width_receipt["artifacts"][2],
                "target_COMDEF": next(r for r in width_comdefs if r["name"] == "_fd_50F6_0220"),
                "COMDEF_set_differs_only_by_width_for_target": True, "all_COMDEFs": width_comdefs,
                "segment_lengths": width_omf.segment_lengths},
            "unsigned_same_width": {"profile": "msc600ax", "flags": signed_receipt["flags"],
                "source": signed_receipt["artifacts"][0], "object": signed_receipt["artifacts"][1],
                "compiler_log": signed_receipt["artifacts"][2],
                "COMDEF_shapes_equal_positive": signed_shape_same,
                "all_COMDEFs": normalize_comdefs(signed_omf.communals), "segment_lengths": signed_omf.segment_lengths,
                "meaning": "OMF COMDEF encodes storage width but not signedness; source type plus signed-value operations carry that claim."},
            "initialized_nonzero": {"profile": "msc600ax", "flags": init_receipt["flags"],
                "source": init_receipt["artifacts"][0], "object": init_receipt["artifacts"][1],
                "compiler_log": init_receipt["artifacts"][2],
                "initialized_target_absent_from_COMDEF": True,
                "all_COMDEFs": normalize_comdefs(init_omf.communals), "initialized_object_SEGDEFs": init_omf.segment_lengths},
            "short_owner": {"same_object_as_wrong_width": True, "object": width_receipt["artifacts"][1],
                "all_COMDEFs": width_comdefs, "runtime_interpretation": "overread output is diagnostic and non-gating"}},
        "consumer_omf_shapes": consumer_omf,
        "runtime_cases": runtime_rows, "runtime_tool_pins": runtime_tool_pins,
        "denied_oracle_reads": list(DENIED_READS),
        "unresolved_domains": ["Original historical COMDEF-producing translation unit and its order are not claimed.",
            "Owner extents are source/C type claims corroborated by the fresh provider's own OMF; they do not establish neighboring layout.",
            "Raw LoadGame byte input and unchecked gameplay/index ranges remain unresolved.",
            "SaveRec byte spans corroborate 23 members only; 0364 and 036E remain non-persistent source-owned ints.",
            "Run-time consumers are test fixtures and do not reconstruct or validate the game call graph."]}
    report_path = RUN / "candidate.json"
    report_path.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    md = ["# InitSimYard scalar owner v22", "",
        "This is an unadmitted source-functional storage candidate. The source scan pins 127 canonical and 29 effective complete module sources (156 distinct paths), plus all 29 tracked ASM sources. The ASM scan found zero target identifiers, zero direct address-syntax hits, and five numeric literal coincidences with typed spans; those hits are reported as immediate/table constants, not memory references. It uses no original executable or address-gap extent inference.", "",
        "| Source type | Count | Bytes each | Total |", "|---|---:|---:|---:|",
        f"| signed `int far` | {len(INTS)} | 2 | {2*len(INTS)} |",
        f"| signed `long far` | {len(LONGS)} | 4 | {4*len(LONGS)} |",
        f"| Total | {len(NAMES)} | — | {sum(WIDTH.values())} |", "",
        "`InitSimYard` (`o06_35F5_0000`) writes all 25 fields directly. Twenty-three have one exact SaveRec byte row (52 bytes total); `fd_50F6_0364` and `fd_50F6_036E` have no SaveRec entry. The two absent rows are supported by typed `int far` declarations and compiler shape controls alone.", "",
        "The fresh data-only MSC 6.00AX object emits the exact 25 expected FAR COMDEFs under `/AL /Os /Gs` plus required `/EM`. RTLink 4.00 and 6.10 cases exercise typed values, raw SaveRec byte reads, startup zeroing, unsigned signedness contrast, initialized storage, shifted SaveRec base, and a separately non-gating short-owner overread observation.", "",
        "| Linker | Case | Expected | Actual | Gating |", "|---|---|---|---|---|"]
    for row in runtime_rows:
        md.append(f"| {row['linker']} | `{row['case']}` | `{row['expected_log']}` | `{row['actual_log']}` | {row['gating_for_owner_evidence']} |")
    md += ["", "Source and raw runtime evidence are in `source-pins.json`, `source-scan.json`, `candidate.json`, and the unique run subdirectories. Historical module identity, dynamic first-use/lifetime order, raw LoadGame field validation, and gameplay index ranges remain open.", ""]
    md_path = RUN / "candidate.md"
    md_path.write_text("\n".join(md), encoding="utf-8")
    summary = {"schema": "simant-init-sim-yard-scalars-run-index-v22", "run_id": RUN_ID,
        "candidate": pin(report_path), "markdown": pin(md_path), "source_scan": pin(RUN / "source-scan.json"),
        "source_pins": pin(RUN / "source-pins.json"), "run_directory": RUN.relative_to(ROOT).as_posix(),
        "root_reviewed": False, "root_claimed": False,
        "gating_runtime_cases_pass": all(r["passed"] for r in runtime_rows if r["gating_for_owner_evidence"]),
        "non_gating_short_owner_observations": [{"linker": r["linker"], "actual": r["actual_log"],
            "stdout": r["stdout_exact"], "outputs": r["raw_outputs"]} for r in runtime_rows if not r["gating_for_owner_evidence"]]}
    index_path = OUT / f"run-index-{RUN_ID}.json"
    if index_path.exists():
        raise RuntimeError("run index already exists; refusing to overwrite prior raw output")
    index_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    if not summary["gating_runtime_cases_pass"]:
        raise RuntimeError("one or more gating runtime cases did not meet its expected receipt")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
