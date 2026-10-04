#!/usr/bin/env python3
"""Bounded, report-pinned SOURCE_ONLY_DOS address/frame inventory v30.

Reads the current build report, its generated sources and objects, and a small
explicit set of address-bearing operand forms. It is not a generic numeric
constant search and does not inspect original executable bytes. It writes only
the JSON/Markdown receipts beside this script.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent / "numeric-frame-inventory-v30.json"
MD = Path(__file__).resolve().parent / "numeric-frame-inventory-v30.md"
REPORT_REL = "build/source-only-dos/build-report.json"
EXPECTED_COUNTS = {"translation_units": 186, "canonical": 127, "strict": 29,
                   "providers": 59, "unresolved_symbols": 22}
PACKETS = [
    "source-bindings-v1.json", "driver-ss-frame-bindings-v1.json",
    "driver-local-frame-bindings-v1.json", "pattern-bank-bindings-v1.json",
    "driver-indexed-address-bindings-v1.json", "s01-pattern-4220-bindings-v1.json",
    "graphics-formula-bindings-v1.json", "queue-storage-bindings-v1.json",
    "assembly-frame-bindings-v1.json", "dgroup-rect-frame-bindings-v1.json",
]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def resolve(rel: str) -> Path:
    return ROOT / rel.replace("\\", "/")


def pin(rel: str, expected: str | None = None) -> dict:
    path = resolve(rel)
    digest = sha(path)
    if expected is not None and digest != expected:
        raise SystemExit(f"stale input pin: {rel}: {digest} != {expected}")
    return {"path": rel.replace("\\", "/"), "sha256": digest,
            "size": path.stat().st_size}


def canonical_json_hash(rows) -> str:
    body = json.dumps(rows, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(body).hexdigest()


def source_lines(path: Path):
    for number, raw in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        yield number, raw.split(";", 1)[0]


def source_path(tu: dict) -> str:
    return tu["source"]["path"].replace("\\", "/")


def module_objects(tus: list[dict]):
    sys.path.insert(0, str(ROOT / "tools"))
    from omf import OmfReader
    reader = OmfReader(communals=True)
    by_module = {}
    object_pins = []
    for tu in tus:
        rel = tu["object"]["path"]
        object_pins.append({"module": tu["module"], **pin(rel, tu["object"]["sha256"])})
        by_module[tu["module"]] = reader.read_file(resolve(rel))
    return by_module, object_pins


def match_relocation(obj, row: dict, exact_count: bool = True) -> dict:
    """Verify one active report/packet relocation against actual object OMF."""
    segment = row.get("segment")
    offsets = row.get("offsets")
    if offsets is None and "offset" in row:
        offsets = [row["offset"]]
    expected_count = int(row.get("count", len(offsets) if offsets is not None else 1))
    def field_matches(f):
        for key in ("target_kind", "target", "loc", "width", "self_relative",
                    "frame_kind", "frame", "displacement", "encoded_addend"):
            if key in row and f.get(key) != row[key]:
                return False
        return True
    candidates = [f for f in obj.linker_fixups if field_matches(f)]
    if segment is not None:
        candidates = [f for f in candidates if f["segment"] == segment]
    if offsets is not None:
        wanted = set(int(x) for x in offsets)
        found = [f for f in candidates if f["offset"] in wanted]
        if {f["offset"] for f in found} != wanted:
            raise AssertionError(f"relocation offset mismatch in {obj.name}: wanted {sorted(wanted)}, found {[(f['segment'], f['offset'], f['target'], f['frame_kind'], f['frame']) for f in found]}")
        if len(found) != expected_count:
            raise AssertionError(f"relocation count mismatch in {obj.name}: {len(found)} != {expected_count}")
    else:
        found = candidates
        if exact_count and len(found) < expected_count:
            raise AssertionError(f"relocation identity lower-bound mismatch in {obj.name}: expected at least {expected_count} for {row}, found {len(found)}")
        if not found:
            raise AssertionError(f"missing relocation in {obj.name}: {row}")
    return {"count": len(found), "segment": segment or (found[0]["segment"] if len(found) == 1 else None),
            "offsets": [f["offset"] for f in found],
            "site_offsets_exact": offsets is not None,
            "declared_count": expected_count,
            "target_kind": found[0]["target_kind"], "target": found[0]["target"],
            "loc": found[0]["loc"], "displacement": found[0]["displacement"],
            "frame_kind": found[0]["frame_kind"], "frame": found[0]["frame"],
            "encoded_addend": found[0]["encoded_addend"]}


def main() -> None:
    report_path = resolve(REPORT_REL)
    report_raw = report_path.read_bytes()
    report = json.loads(report_raw)
    tus = report["translation_units"]
    canonical = [x for x in tus if source_path(x).startswith("src/")]
    providers = [x for x in tus if x["module"].startswith("source-owned:")]
    strict = report.get("semantic_substitutions", [])
    got_counts = {"translation_units": len(tus), "canonical": len(canonical),
                  "strict": len(strict), "providers": len(providers),
                  "unresolved_symbols": len(report.get("unresolved_symbols", []))}
    if got_counts != EXPECTED_COUNTS:
        raise SystemExit(f"current report scope changed: {got_counts} != {EXPECTED_COUNTS}")
    gate = next((x for x in report.get("layout_dependencies", [])
                 if x.get("id") == "remaining-assembly-address-audit"), None)
    if not gate or gate.get("status") != "UNRESOLVED":
        raise SystemExit("the assembly address audit gate changed; review this inventory explicitly")
    original_bytes = report.get("original_exe_bytes_used", {})
    if not isinstance(original_bytes, dict) or any(int(v) != 0 for v in original_bytes.values()):
        raise SystemExit("current report claims original EXE bytes were used")

    # Freshly pin every effective TU source, generated source and object.
    source_rows, generated_rows, strict_rows = [], [], []
    by_module = {x["module"]: x for x in tus}
    for tu in tus:
        s = pin(tu["source"]["path"], tu["source"]["sha256"])
        g = pin(tu["generated_source"]["path"], tu["generated_source"]["sha256"])
        source_rows.append({"module": tu["module"], **s})
        generated_rows.append({"module": tu["module"], **g})
    for row in strict:
        strict_rows.append({"function": row["function"], "module": row["module"],
                            **pin(row["source"]["path"], row["source"]["sha256"])})
    objects, object_pins = module_objects(tus)

    # All source-binding relocations embedded by the current prepare report
    # are checked against actual OMF fields; exact offsets are honored when
    # supplied and otherwise target/frame/addend identities are counted.
    report_binding_checks = []
    for tu in tus:
        binding = tu.get("source_binding") or {}
        for row in binding.get("relocations", []):
            actual = match_relocation(objects[tu["module"]], row)
            if actual["loc"] != "offset16":
                raise AssertionError(f"unexpected source-binding relocation type in {tu['module']}: {actual}")
            report_binding_checks.append({"module": tu["module"], "declared": row,
                                          "actual": actual})

    packet_pins = []
    packet_checks = []
    packet_json = {}
    for name in PACKETS:
        rel = f"work/source-only-dos/{name}"
        path = resolve(rel)
        if not path.exists():
            raise SystemExit(f"required active binding packet missing: {rel}")
        packet_pins.append(pin(rel))
        packet_json[name] = json.loads(path.read_text(encoding="utf-8"))
    for name, packet in packet_json.items():
        for binding in packet.get("bindings", []):
            mod = binding.get("module")
            if mod not in objects:
                continue
            obj = objects[mod]
            for row in binding.get("relocations", []):
                actual = match_relocation(obj, row)
                if actual["loc"] != "offset16":
                    raise AssertionError(f"unexpected packet relocation type {name}/{mod}: {actual}")
                packet_checks.append({"packet": name, "module": mod,
                                      "kind": "relocation", "declared": row,
                                      "actual": actual})
            for row in binding.get("reframes", []):
                expected = {"segment": row["segment"], "offset": row["offset"],
                            "target": row["target"], "frame_kind": row["frame_kind"],
                            "frame": row["frame"]}
                found = [f for f in obj.linker_fixups if all(f.get(k) == v for k, v in expected.items())]
                if len(found) != 1:
                    raise AssertionError(f"reframe site mismatch {mod} {expected}: {found}")
                if found[0]["loc"] != "offset16":
                    raise AssertionError(f"unexpected reframe location type {mod}: {found[0]}")
                packet_checks.append({"packet": name, "module": mod,
                                      "kind": "reframe", "actual": found[0]})
            for row in binding.get("local_reframes", []):
                expected = {"segment": row["segment"], "offset": row["offset"],
                            "target_kind": row["target_kind"], "target": row["target"],
                            "displacement": row["displacement"],
                            "frame_kind": row["frame_kind"], "frame": row["frame"],
                            "encoded_addend": row["encoded_addend"]}
                found = [f for f in obj.linker_fixups if all(f.get(k) == v for k, v in expected.items())]
                if len(found) != 1:
                    raise AssertionError(f"local reframe site mismatch {mod} {expected}: {found}")
                if found[0]["loc"] != "offset16":
                    raise AssertionError(f"unexpected local reframe location type {mod}: {found[0]}")
                packet_checks.append({"packet": name, "module": mod,
                                      "kind": "local_reframe", "actual": found[0]})
            for row in binding.get("segment_corrections", []):
                old = row["old"]
                new = row["new"]
                expected = {"segment": row["segment"], "offset": row["offset"],
                            "width": new["width"], "loc": new["loc"],
                            "self_relative": new["self_relative"],
                            "target_kind": new["target_kind"], "target": new["target"],
                            "displacement": new["displacement"],
                            "frame_kind": new["frame_kind"], "frame": new["frame"],
                            "encoded_addend": new["encoded_addend"]}
                found = [f for f in obj.linker_fixups if all(f.get(k) == v for k, v in expected.items())]
                if len(found) != 1:
                    raise AssertionError(f"segment correction mismatch {mod} {expected}: {found}")
                packet_checks.append({"packet": name, "module": mod,
                                      "kind": "segment_correction", "old": old,
                                      "actual": found[0]})

    # Exact 148-site SS/frame set: external 128 plus local 10 plus indexed
    # 10. The set must stay disjoint and every current OMF frame is DGROUP.
    tuple_sets = {}
    for key, filename, rowkey in [
        ("external", "driver-ss-frame-bindings-v1.json", "reframes"),
        ("local", "driver-local-frame-bindings-v1.json", "local_reframes"),
        ("indexed", "driver-indexed-address-bindings-v1.json", "relocations"),
    ]:
        tuples = set()
        packet = packet_json[filename]
        for binding in packet.get("bindings", []):
            mod = binding.get("module")
            for row in binding.get(rowkey, []):
                offsets = row.get("offsets", [row.get("offset")])
                for off in offsets:
                    tuples.add((mod, row["segment"], int(off), row.get("target")))
        tuple_sets[key] = tuples
    tuple_counts = {key: len(value) for key, value in tuple_sets.items()}
    if tuple_counts != {"external": 128, "local": 10, "indexed": 10}:
        raise SystemExit(f"reviewed SS/indexed tuple totals changed: {tuple_counts}")
    intersections = {"external_local": len(tuple_sets["external"] & tuple_sets["local"]),
                     "external_indexed": len(tuple_sets["external"] & tuple_sets["indexed"]),
                     "local_indexed": len(tuple_sets["local"] & tuple_sets["indexed"])}
    if any(intersections.values()):
        raise SystemExit(f"reviewed tuples overlap: {intersections}")
    if len(set.union(*tuple_sets.values())) != 148:
        raise SystemExit("the reviewed tuple union changed")

    # Address-bearing ASM shapes are explicit and count-guarded. The first
    # form catches direct numeric segment bases; the 8ED8 ADD base is kept
    # distinct because its following memory reads are indexed through SS.
    expected_raw_ss = {
        ("S00:31AD", "3DCAH"): 1, ("S00:31AD", "41D0H"): 3,
        ("S00:35A6", "6778H"): 1, ("S01:3126", "4220H"): 1,
        ("S01:32B5", "68ACH"): 1, ("S03:3126", "2226H"): 8,
        ("S03:3258", "68B4H"): 1,
    }
    source_raw = Counter()
    generated_raw = Counter()
    generated_numeric_ss = []
    raw_ss_re = re.compile(r"(?i)\bss\s*:\s*\[[^\]]*\b([0-9a-f]{1,4}h)\s*\]")
    direct_seg_re = re.compile(r"(?i)\b(cs|ds|es|ss)\s*:\s*\[\s*([0-9a-f]{1,4}h)\s*\]")
    direct_numeric_bracket_re = re.compile(r"(?i)\[\s*([0-9a-f]{1,4}h)\s*\]")
    direct_es = []
    direct_seg = []
    unsegmented_direct = []
    selector_leas = []
    add_immediates = []
    indexed_operand_counts = Counter()
    for tu in tus:
        mod = tu["module"]
        if tu["lang"] != "asm":
            continue
        for n, line in source_lines(resolve(tu["source"]["path"])):
            for m in raw_ss_re.finditer(line):
                key = (mod, m.group(1).upper())
                if key in expected_raw_ss:
                    source_raw[key] += 1
        for n, line in source_lines(resolve(tu["generated_source"]["path"])):
            for m in raw_ss_re.finditer(line):
                key = (mod, m.group(1).upper())
                generated_raw[key] += 1
                generated_numeric_ss.append({"module": mod, "line": n,
                                             "operand": m.group(1).upper(),
                                             "instruction": line.strip()})
            m = direct_seg_re.search(line)
            if m:
                row = {"module": mod, "line": n, "segment": m.group(1).upper(),
                       "offset": m.group(2).upper(), "instruction": line.strip()}
                direct_seg.append(row)
                if row["segment"] == "ES":
                    direct_es.append(row)
            for mb in direct_numeric_bracket_re.finditer(line):
                if not re.search(r"(?i)\b(?:cs|ds|es|ss)\s*:\s*$", line[:mb.start()]):
                    unsegmented_direct.append({"module": mod, "line": n,
                                              "operand": mb.group(1).upper(),
                                              "instruction": line.strip()})
            if re.search(r"(?i)\blea\s+\w+\s*,\s*ds\s*:\s*\[(?:0Ch|10Ch|20Ch|30Ch)\]", line):
                selector_leas.append({"module": mod, "line": n, "instruction": line.strip()})
            if re.search(r"(?i)\badd\s+(?:bx|si|di|bp)\s*,\s*[0-9a-f]{1,4}h\b", line):
                m_add = re.search(r"(?i)\badd\s+(bx|si|di|bp)\s*,\s*([0-9a-f]{1,4}h)\b", line)
                add_immediates.append({"module": mod, "line": n, "register": m_add.group(1).upper(),
                                       "immediate": m_add.group(2).upper(),
                                       "instruction": line.strip()})
            for m in re.finditer(r"(?i)\b(cs|ds|es|ss)\s*:\s*\[\s*([a-z]{2})\s*\+\s*([0-9a-f]{1,4}h)\s*\]", line):
                indexed_operand_counts[(m.group(1).upper(), m.group(2).upper())] += 1
    for site, expected in expected_raw_ss.items():
        if source_raw[site] != expected or generated_raw[site] != 0:
            raise SystemExit(f"numeric SS-site count changed {site}: source={source_raw[site]}, generated={generated_raw[site]}")
    if generated_numeric_ss:
        raise SystemExit(f"unclassified numeric SS memory operand in effective sources: {generated_numeric_ss[:8]}")
    if len(direct_seg) != 51 or len(direct_es) != 43 or len(selector_leas) != 8 or unsegmented_direct:
        raise SystemExit(f"direct segment-address scan changed: direct={len(direct_seg)}, ES={len(direct_es)}, selector LEA={len(selector_leas)}, unsegmented={len(unsegmented_direct)}")
    # Register-state anchors for each direct ES hardware family. Each anchor
    # is checked against the current canonical source line; assignment pairs
    # show the segment value immediately before representative direct sites.
    es_anchor_specs = [
        {"module": "S00:31AD", "source": "src/S00/m31AD.asm", "es": "0000h",
         "offsets": ["487H"], "anchors": [(2755, "xor ax, ax"), (2756, "mov es, ax")]},
        {"module": "S01:3126", "source": "src/S01/m3126.asm", "es": "0000h",
         "offsets": ["449H", "463H", "44AH"],
         "anchors": [(174, "xor ax, ax"), (175, "mov es, ax"), (213, "xor ax, ax"), (214, "mov es, ax"),
                     (239, "xor ax, ax"), (240, "mov es, ax"), (301, "xor ax, ax"), (302, "mov es, ax"),
                     (2688, "xor ax, ax"), (2689, "mov es, ax"), (2701, "xor ax, ax"), (2702, "mov es, ax")]},
        {"module": "root:1B4E", "source": "src/root/m1B4E.asm", "es": "0000h",
         "offsets": ["449H"], "anchors": [(406, "xor ax, ax"), (407, "mov es, ax"), (419, "xor ax, ax"), (420, "mov es, ax")]},
        {"module": "root:1B73", "source": "src/root/m1B73.asm", "es": "0000h",
         "offsets": ["0CCH", "0CEH", "449H", "417H", "24H", "26H"],
         "anchors": [(240, "xor ax, ax"), (241, "mov es, ax"), (264, "xor ax, ax"), (265, "mov es, ax"),
                     (268, "xor ax, ax"), (269, "mov es, ax"), (482, "xor ax, ax"), (483, "mov es, ax"),
                     (527, "xor ax, ax"), (528, "mov es, ax"), (1019, "xor dx, dx"), (1021, "mov es, dx"),
                     (1149, "xor cx, cx"), (1150, "mov es, cx"), (2044, "xor ax, ax"), (2045, "mov es, ax")]},
        {"module": "root:1B73", "source": "src/root/m1B73.asm", "es": "0040h",
         "offsets": ["17H", "6CH", "1AH", "1CH"],
         "anchors": [(658, "mov ax, 40h"), (659, "mov es, ax"), (1069, "mov ax, 40h"), (1070, "mov es, ax")]},
        {"module": "root:1F58", "source": "src/root/m1F58.asm", "es": "0000h",
         "offsets": ["46CH", "46EH", "417H", "8CH", "8EH"],
         "anchors": [(31, "xor ax, ax"), (32, "mov es, ax"), (79, "xor bx, bx"), (80, "mov es, bx"),
                     (131, "xor ax, ax"), (132, "mov es, ax"), (147, "xor ax, ax"), (148, "mov es, ax")]},
        {"module": "root:1F66", "source": "src/root/m1F66.asm", "es": "B000h",
         "offsets": ["40H"], "anchors": [(246, "mov ax, 0B000h"), (247, "mov es, ax")]},
        {"module": "root:28BC", "source": "src/root/m28BC.asm", "es": "0000h",
         "offsets": ["20H", "22H"],
         "anchors": [(693, "xor ax, ax"), (694, "mov es, ax"), (748, "xor ax, ax"), (749, "mov es, ax")]},
    ]
    es_anchor_rows = []
    for group in es_anchor_specs:
        src_lines = {n: " ".join(line.strip().lower().split()) for n, line in source_lines(resolve(group["source"]))}
        for n, expected in group["anchors"]:
            if src_lines.get(n) != " ".join(expected.lower().split()):
                raise SystemExit(f"ES state anchor changed at {group['source']}:{n}: {src_lines.get(n)!r} != {expected!r}")
        es_anchor_rows.append({"module": group["module"], "source": group["source"],
                               "es": group["es"], "offsets": group["offsets"],
                               "verified_source_instructions": [{"line": n, "instruction": expected}
                                                                 for n, expected in group["anchors"]],
                               "class": "BDA/IVT hardware" if group["module"] != "root:1F66" else "B000h video aperture"})
    for row in direct_es:
        matching = [g for g in es_anchor_rows if g["module"] == row["module"] and row["offset"] in g["offsets"]]
        if not matching:
            raise SystemExit(f"direct ES hardware operand lacks a state anchor: {row}")
        row["es_state"] = matching[0]["es"] if len(matching) == 1 else "multiple anchored values"
        row["classification"] = matching[0]["class"]
    eight_sites = []
    eight_loads = []
    tu_328e = by_module["S01:328E"]
    for n, line in source_lines(resolve(tu_328e["source"]["path"])):
        if re.search(r"(?i)\badd\s+bx\s*,\s*8ED8h\b", line):
            eight_sites.append({"source_line": n, "instruction": line.strip()})
        if re.search(r"(?i)\bmov\s+dl\s*,\s*byte\s+ptr\s+ss:\[bx(?:\+[0-3])?\]", line):
            eight_loads.append({"source_line": n, "instruction": line.strip()})
    eight_generated = [n for n, line in source_lines(resolve(tu_328e["generated_source"]["path"]))
                       if re.search(r"(?i)\badd\s+bx\s*,\s*8ED8h\b", line)]
    if (len(eight_sites), len(eight_generated), len(eight_loads)) != (4, 4, 32):
        raise SystemExit(f"S01:328E 8ED8 scope changed: adds={len(eight_sites)}/{len(eight_generated)}, SS reads={len(eight_loads)}")
    add_hist = Counter(x["immediate"] for x in add_immediates)
    if len(add_immediates) != 64 or add_hist["8ED8H"] != 4:
        raise SystemExit(f"register-base immediate inventory changed: total={len(add_immediates)}, 8ED8={add_hist['8ED8H']}")

    # C far-pointer literals: only explicit numeric far pointer casts qualify.
    c_files = {}
    for tu in tus:
        if tu["lang"] == "c":
            c_files[source_path(tu)] = tu["source"]["sha256"]
    for row in strict:
        rel = row["source"]["path"].replace("\\", "/")
        c_files[rel] = row["source"]["sha256"]
    far_cast_re = re.compile(r"(?i)\(\s*(?:unsigned\s+)?(?:char|int|long|void)\s+far\s*\*+\s*\)\s*(0x[0-9a-f]+[lLuU]*)")
    far_cast_sites = []
    for rel, digest in sorted(c_files.items()):
        pin(rel, digest)
        c_lines = resolve(rel).read_text(encoding="utf-8", errors="replace").splitlines()
        for n, raw in enumerate(c_lines, 1):
            code = raw.split("//", 1)[0]
            for m in far_cast_re.finditer(code):
                far_cast_sites.append({"source": rel, "line": n, "literal": m.group(1).lower(),
                                       "text": raw.strip()})
    far_cast_counts = Counter(x["literal"] for x in far_cast_sites)
    expected_far = Counter({"0x417l": 22, "0x00000417l": 10, "0x00000410l": 1,
                            "0x046c0000l": 1, "0xf000fffel": 1, "0xfc000000l": 1})
    if far_cast_counts != expected_far:
        raise SystemExit(f"absolute far-pointer-cast inventory changed: {far_cast_counts}")

    # C TUs do contain a small, bounded set of MSC inline-assembly blocks.
    # Parse only the emitted _asm braces in the report's generated C files;
    # preserve each block's instruction text, then inspect segment-memory and
    # IN/OUT forms separately from C numeric far-pointer casts.
    generated_c_asm = []
    for tu in tus:
        if tu["lang"] != "c":
            continue
        rel = tu["generated_source"]["path"].replace("\\", "/")
        lines = resolve(rel).read_text(encoding="utf-8", errors="replace").splitlines()
        i = 0
        while i < len(lines):
            if not re.search(r"(?i)\b_asm\s*\{", lines[i]):
                i += 1
                continue
            start = i + 1
            body = []
            depth = 0
            while i < len(lines):
                raw = lines[i]
                if i == start - 1:
                    # Strip the opening token so inline instructions on a
                    # single line are scanned the same way as block lines.
                    raw_body = re.sub(r"(?i).*?\b_asm\s*\{", "", raw, count=1)
                else:
                    raw_body = raw
                depth += raw.count("{") - raw.count("}")
                raw_body = re.sub(r"}\s*.*$", "", raw_body, count=1)
                text = raw_body.strip().rstrip("\\").strip()
                if text:
                    body.append({"line": i + 1, "instruction": text})
                i += 1
                if depth == 0:
                    break
            generated_c_asm.append({"module": tu["module"], "source": tu["source"]["path"].replace("\\", "/"),
                                    "generated_source": rel, "start_line": start,
                                    "instructions": body})
    c_asm_counts = Counter(x["module"] for x in generated_c_asm)
    expected_c_asm_counts = Counter({"S15:384C": 1, "root:0093": 8, "root:277E": 4,
                                     "root:293A": 2, "root:29D6": 1, "root:29F0": 2})
    if c_asm_counts != expected_c_asm_counts or len(generated_c_asm) != 18:
        raise SystemExit(f"generated C inline-assembly scope changed: {c_asm_counts}")
    inline_segment_memory = []
    inline_io_instructions = []
    for block in generated_c_asm:
        for item in block["instructions"]:
            line = item["instruction"]
            for m in re.finditer(r"(?i)\b(cs|ds|es|ss)\s*:\s*\[([^\]]+)\]", line):
                inline_segment_memory.append({"module": block["module"], "source_line": item["line"],
                                              "segment": m.group(1).upper(), "effective_offset_expression": m.group(2).strip(),
                                              "instruction": line})
            if re.search(r"(?i)^\s*(?:in|out)\s+", line):
                inline_io_instructions.append({"module": block["module"], "source_line": item["line"],
                                               "instruction": line})
    expected_inline_segment_memory = 2
    if len(inline_segment_memory) != expected_inline_segment_memory:
        raise SystemExit(f"inline C ASM segment-memory operand count changed: {inline_segment_memory}")
    u114 = next(x for x in generated_c_asm if x["module"] == "root:277E" and x["start_line"] == 348)
    u120 = next(x for x in generated_c_asm if x["module"] == "root:293A" and x["start_line"] == 56)
    norm = lambda rows: [" ".join(x["instruction"].lower().split()) for x in rows]
    if not all(text in norm(u114["instructions"]) for text in ["sub bx, bx", "mov es, bx", "mov bx, 408h", "mov ax, es:[bx]"]):
        raise SystemExit("root:277E inline ES:[BX] BDA state anchor changed")
    if not all(text in norm(u120["instructions"]) for text in ["mov ax, 0c000h", "int 15h", "add bx, 2", "mov ax, es:[bx]"]):
        raise SystemExit("root:293A inline ES:[BX] BIOS-returned pointer anchor changed")

    # Source-bound owner anchors for applied families, current direct OMF PUBDEF
    # locations and the exact unresolved 8ED8/5A9C imported references.
    direct_publics = defaultdict(list)
    unresolved_ref_counts = Counter()
    all_fixups = []
    segment_count = Counter()
    loc_count = Counter()
    frame_count = Counter()
    for mod, obj in objects.items():
        for pub in obj.publics:
            direct_publics[pub["name"]].append({"module": mod, "segment": pub["segment"],
                                                 "offset": pub["offset"]})
        for f in obj.linker_fixups:
            all_fixups.append((mod, f))
            segment_count[(mod, f["segment"])] += 1
            loc_count[f["loc"]] += 1
            frame_count[(f["frame_kind"], f["frame"])] += 1
            if f["target_kind"] == "external" and f["target"] not in direct_publics:
                # Recomputed below after all direct publics are indexed.
                pass
    communal_names = defaultdict(list)
    for mod, obj in objects.items():
        for c in obj.communals:
            communal_names[c["name"]].append({"module": mod, **c})
    externally_defined = set(direct_publics) | set(communal_names)
    # Use the build report's actual unresolved-symbol roster here. An external
    # target absent from direct PUBDEF/COMDEFs can be a CRT/LIBH export, an
    # alias, or another selected runtime symbol; calling every such reference
    # unresolved would inflate this census with thousands of valid imports.
    unresolved_names = {x["name"] for x in report.get("unresolved_symbols", [])}
    unresolved_external_refs = Counter()
    for mod, f in all_fixups:
        if f["target_kind"] == "external" and f["target"] in unresolved_names:
            unresolved_external_refs[f["target"]] += 1
    if len(unresolved_names) != 22 or len(unresolved_external_refs) != 22 or sum(unresolved_external_refs.values()) != 254:
        raise SystemExit(f"report-grounded unresolved OMF import census changed: names={len(unresolved_names)}, seen={len(unresolved_external_refs)}, refs={sum(unresolved_external_refs.values())}")

    expected_owners = {
        "_g_3DCA": ("root:1B4E", "_DATA", 170),
        "_g_3DFC": ("root:1B4E", "_DATA", 220),
        "_g_41D0": ("root:1B4E", "_DATA", 1200),
        "_g_4220": ("root:1B4E", "_DATA", 1280),
        "_glyph_edge_masks": ("root:2650", "_DATA", 12),
        "_mono_tail_masks": ("source-owned:graphics-formulas", "_DATA", 8),
        "_packed_tail_masks": ("source-owned:graphics-formulas", "_DATA", 16),
    }
    owner_rows = {}
    for symbol, expected in expected_owners.items():
        matches = direct_publics.get(symbol, [])
        if not any((x["module"], x["segment"], x["offset"]) == expected for x in matches):
            raise AssertionError(f"expected positive owner anchor absent for {symbol}: {matches}")
        matched = next(x for x in matches if (x["module"], x["segment"], x["offset"]) == expected)
        owner_obj = objects[matched["module"]]
        groups = [g["name"] for g in owner_obj.groups if matched["segment"] in g.get("segments", [])]
        if "DGROUP" not in groups:
            raise AssertionError(f"data anchor {symbol} is not in DGROUP: {groups}")
        owner_rows[symbol] = {"direct_publics": matches, "accepted_source_anchor": expected,
                              "segment_length": owner_obj.segment_length(matched["segment"]),
                              "segment_groups": groups,
                              "meaning": "existing source storage view; current OMF PUBDEF verified"}
    if "_g_8ED8" not in unresolved_external_refs or "_g_5A9C" not in unresolved_external_refs:
        raise AssertionError("unresolved 8ED8/5A9C owners unexpectedly changed in current OMF")
    if direct_publics.get("_input_queue") or not communal_names.get("_input_queue"):
        raise AssertionError("reviewed near-communal _input_queue owner missing")
    queue = communal_names["_input_queue"]
    if not any(x.get("kind") == "near" and x.get("length") == 112 for x in queue):
        raise AssertionError(f"queue owner anchor changed: {queue}")

    def compact_fixup(module: str, fixup: dict) -> dict:
        return {"module": module, "segment": fixup["segment"], "offset": fixup["offset"],
                "target_kind": fixup["target_kind"], "target": fixup["target"],
                "loc": fixup["loc"], "width": fixup["width"],
                "displacement": fixup["displacement"], "frame_kind": fixup["frame_kind"],
                "frame": fixup["frame"], "encoded_addend": fixup["encoded_addend"]}

    signed_frame_site_rows = []
    for tuple_group in tuple_sets.values():
        for mod, seg, off, target in sorted(tuple_group):
            found = [f for f in objects[mod].linker_fixups
                     if f["segment"] == seg and f["offset"] == off and f["target"] == target]
            if len(found) != 1 or found[0]["frame_kind"] != "group" or found[0]["frame"] != "DGROUP":
                raise AssertionError(f"signed frame tuple does not have one DGROUP OMF fixup: {mod} {seg}+{off:04X} {target}: {found}")
            signed_frame_site_rows.append(compact_fixup(mod, found[0]))
    if len(signed_frame_site_rows) != 148:
        raise AssertionError(f"signed frame site OMF row count changed: {len(signed_frame_site_rows)}")
    if any(x["loc"] != "offset16" for x in signed_frame_site_rows):
        raise AssertionError("one of the 148 signed frame sites is no longer an OFFSET16 fixup")
    frame_tuple_keys = {(x["module"], x["segment"], x["offset"], x["target"]) for x in signed_frame_site_rows}
    additional_exact_packet_sites = {}
    for check in packet_checks:
        if check["kind"] == "relocation" and not check["actual"].get("site_offsets_exact"):
            continue
        if check["kind"] not in ("relocation", "segment_correction"):
            continue
        actual = check["actual"]
        mod = check["module"]
        if not actual.get("segment"):
            continue
        for off in actual.get("offsets", [actual.get("offset")]):
            candidates = [f for f in objects[mod].linker_fixups
                          if f["segment"] == actual["segment"] and f["offset"] == off
                          and f["target"] == actual["target"]]
            if len(candidates) != 1:
                raise AssertionError(f"exact packet site no longer unique: {mod} {actual}")
            row = compact_fixup(mod, candidates[0])
            key = (mod, row["segment"], row["offset"], row["target"])
            if key not in frame_tuple_keys:
                additional_exact_packet_sites[key] = row
    packet_check_counts = Counter((x["packet"], x["kind"]) for x in packet_checks)

    # Confirm indexed-source symbolic changes and exact source-level footprints.
    symbolic_checks = {
        "S00:31AD": [("_g_3DCA", 1), ("_g_41D0", 3)],
        "S00:35A6": [("_glyph_edge_masks", 1)],
        "S01:3126": [("_g_4220", 1)],
        "S01:32B5": [("_mono_tail_masks", 1)],
        "S03:3126": [("_g_2226", 8)],
        "S03:3258": [("_packed_tail_masks", 1)],
    }
    symbolic_generated = {}
    for mod, expected in symbolic_checks.items():
        lines = [line.lower() for _, line in source_lines(resolve(by_module[mod]["generated_source"]["path"]))]
        counts = {}
        for symbol, count in expected:
            found = sum(symbol.lower() in line and "ss:" in line for line in lines)
            if found != count:
                raise AssertionError(f"effective symbolic SS site changed {mod} {symbol}: {found} != {count}")
            counts[symbol] = found
        symbolic_generated[mod] = counts

    # Prior inventories are pinned as historical scope references only.
    previous_rel = "work/source-only-dos/remaining-numeric-address-audit-candidate-v18.json"
    previous_md_rel = "work/source-only-dos/remaining-numeric-address-audit-candidate-v18.md"
    previous_numeric_rel = "work/source-only-dos/numeric-address-audit-v1.md"
    previous_json = json.loads(resolve(previous_rel).read_text(encoding="utf-8"))
    previous_scope = previous_json.get("scope", previous_json.get("input_scope", {}))
    historical_pins = [pin(previous_rel), pin(previous_md_rel), pin(previous_numeric_rel)]

    report_pin = {"path": REPORT_REL, "sha256": hashlib.sha256(report_raw).hexdigest(),
                  "size": len(report_raw)}
    script_rel = str(Path(__file__).resolve().relative_to(ROOT)).replace("\\", "/")
    script_pin = pin(script_rel)
    reported_inputs = {x["path"].replace("\\", "/"): x for x in report.get("inputs", [])}
    tooling_snapshot = []
    for rel in ("tools/source_only_dos.py", "tools/dos_source_bindings.py", "tools/omf.py"):
        snap = reported_inputs.get(rel)
        if snap is None:
            raise SystemExit(f"current report no longer pins expected build tool: {rel}")
        current = pin(rel)
        tooling_snapshot.append({"path": rel,
                                 "report_input_pin": {"sha256": snap["sha256"], "size": snap["size"]},
                                 "current_file_pin": {"sha256": current["sha256"], "size": current["size"]},
                                 "changed_since_report_snapshot": current["sha256"] != snap["sha256"]})
    if next(x for x in tooling_snapshot if x["path"] == "tools/omf.py")["changed_since_report_snapshot"]:
        raise SystemExit("the OMF reader changed since the frozen 186-TU report; repeatable object parse unavailable")
    # Keep 046C statement distinct from the hardware BDA timer alias; the
    # historical no-relocation result is inherited from pinned audit v1.
    unresolved_candidates = {
        "S01_328E_8ED8": {
            "classification": "UNRESOLVED_LINK_LAYOUT_TABLE_BASE_OWNER_EXTENT_AND_ENTRY_SS_FRAME",
            "source": "src/S01/m328E.asm",
            "sites": eight_sites,
            "generated_sites": eight_generated,
            "related_ss_indexed_reads": eight_loads,
            "actual_omf_fixup": "none for ADD BX,8ED8h immediate; the following explicit SS:[BX(+0..3)] reads use SS as frame",
            "owner": "unresolved _g_8ED8 import; no current source-owned PUBDEF/COMDEF candidate",
            "prior_bounded_range": "The pinned v19 receipt bounds one producer path conditionally to <=0x3F8 bytes for nonnegative header byte; it does not prove input/resource domain or consumer range.",
            "neighbor": "accepted _g_8EC0 covers 0x8EC0..0x8ED7 (24 bytes); adjacency does not establish the next object's owner/extent.",
            "entry_frame": "The 148 signed SS/DGROUP tuples exclude S01:328E. This receipt does not prove all relevant entries or resource index ranges; retain the per-entry SS and source-bound questions.",
            "report_external_references": unresolved_external_refs["_g_8ED8"],
        },
        "absolute_046c": {
            "classification": "PRESERVED_ABSOLUTE_RAM_LINEAR_0x46C0_INTENT_OWNER_UNRESOLVED",
            "source": "src/root/m0093.c:79",
            "operation": "far pointer cast 0x046C0000L => 046C:0000 => physical 0x46C0",
            "contrast": "BDA timer ticks are 0040:006C / linear 0x046C; that is not this operand.",
            "original_mz_relocation": "Prior bounded address audit reports no MZ relocation; v30 did not inspect original EXE bytes.",
            "status": "purpose and runtime RAM owner unresolved; this address is not a link-layout dependency",
        },
        "g_5A9C": {
            "classification": "SEGMENT_FRAME_CORRECTION_APPLIED_STORAGE_AND_INITIALIZERS_UNRESOLVED",
            "source": "src/root/m1B73.asm: f_1B73_032E segment source at generated MOUSE_TEXT+0x133",
            "omf_site": next((x["actual"] for x in packet_checks if x["packet"] == "dgroup-rect-frame-bindings-v1.json" and x["kind"] == "segment_correction"), None),
            "owner": "Unresolved; current build report does not accept storage/initializer ownership.",
            "scope": "The frame fix validates only the BASE16 SEG target/frame pair. It does not close the original literal's complete placement or functional rectangle state.",
        },
    }

    # Save compact, reproducible current evidence.
    receipt = {
        "schema": "simant-dos-numeric-frame-inventory-v30",
        "root_reviewed": False,
        "classification": "OBSERVATION_ONLY_GATE_REMAINS_UNRESOLVED",
        "scope": {
            **got_counts,
            "report_status": report.get("status"),
            "remaining_assembly_address_audit": gate,
            "original_exe_bytes_used_by_this_audit": 0,
            "repeatable_checker": script_pin,
            "report_pinned_tools_vs_current_file_state": tooling_snapshot,
            "build_report": report_pin,
            "current_tu_source_manifest": {"entries": len(source_rows), "sha256": canonical_json_hash(sorted(source_rows, key=lambda x: (x["module"], x["path"])))},
            "current_generated_source_manifest": {"entries": len(generated_rows), "sha256": canonical_json_hash(sorted(generated_rows, key=lambda x: (x["module"], x["path"])))},
            "current_object_manifest": {"entries": len(object_pins), "sha256": canonical_json_hash(sorted(object_pins, key=lambda x: (x["module"], x["path"])))},
            "strict_source_manifest": {"entries": len(strict_rows), "sha256": canonical_json_hash(sorted(strict_rows, key=lambda x: (x["module"], x["function"])))},
            "prior_inventory_scope_reference": {"v18_previous_candidate_scope": previous_scope, "pins": historical_pins},
        },
        "effective_address_inventory": {
            "numeric_ss_memory_operands": {"canonical_source_sites": {f"{m}:{o}": c for (m, o), c in sorted(source_raw.items())},
                                            "generated_numeric_operand_count": len(generated_numeric_ss),
                                            "generated_numeric_operands": generated_numeric_ss,
                                            "result": "All seven previously numeric SS families are now symbolic; no numeric SS displacement memory operands were found in effective generated ASM."},
            "applied_symbolic_ss_families": symbolic_generated,
            "register_add_immediates": {"total_sites": len(add_immediates), "literal_histogram": dict(sorted(add_hist.items())),
                                         "8ED8_sites": eight_sites,
                                         "classification": "8ED8 is the sole retained fixed table-base ADD identified by this focused operand inventory; other ADD immediates are recorded as register-relative stride/page calculations pending any separate functional issue."},
            "direct_segment_memory_operands": {"count": len(direct_seg), "counts_by_segment": dict(sorted(Counter(x["segment"] for x in direct_seg).items())),
                                                "sites": direct_seg,
                                                "unsegmented_direct_numeric_operands": unsegmented_direct,
                                                "classification": "43 direct ES sites are BDA/IVT/video hardware with module-local ES anchors. Eight direct DS forms are LEA selector-address materializations, not DS dereferences."},
            "es_segment_state_anchors": es_anchor_rows,
            "selector_leas": selector_leas,
            "c_input_audit": {"distinct_current_c_sources": len(c_files),
                              "inline_assembly_scope": {"generated_block_count": len(generated_c_asm),
                                                        "blocks_by_module": dict(sorted(c_asm_counts.items())),
                                                        "explicit_segment_memory_operands": inline_segment_memory,
                                                        "io_instruction_count": len(inline_io_instructions),
                                                        "io_instructions": inline_io_instructions,
                                                        "classification": "root:277E sets ES=0000 and BX=0408 before ES:[BX], a BDA read. root:293A reads ES:[BX+2] after INT 15h returns the ES:BX information pointer; runtime-derived, not a fixed DGROUP base. IN/OUT literals and DX values are hardware I/O ports. Remaining ASM statements use locals/registers or service values."},
                              "scope": "numeric far-pointer casts plus the actual generated C inline-ASM blocks; ordinary constants/structure offsets/runtime pointer arithmetic are not classed as fixed segment bases"},
            "indexed_register_relative_operands": {"counts_by_segment_and_base_register": {f"{seg}:{base}": count for (seg, base), count in sorted(indexed_operand_counts.items())},
                                                    "interpretation": "Register-indexed ES destinations and stack/member/raster accesses. These are not fixed segment bases; the 8ED8 SS table-base family is itemized separately."},
            "absolute_far_pointer_casts": {"count": len(far_cast_sites), "counts_by_literal": dict(sorted(far_cast_counts.items())),
                                            "sites": far_cast_sites,
                                            "classification": {"0x417l": "BDA 0000:0417 keyboard flags", "0x00000417l": "BDA 0000:0417 keyboard flags", "0x00000410l": "BDA 0000:0410 equipment flags", "0x046c0000l": "absolute RAM 046C:0000 / physical 0x46C0; owner/intent unresolved", "0xf000fffel": "BIOS ROM F000:FFFE", "0xfc000000l": "Tandy ROM FC00:0000"}},
        },
        "applied_binding_omf_validation": {
            "report_source_binding_relocations_checked": len(report_binding_checks),
            "packet_site_checks": len(packet_checks),
            "external_ss_tuples": tuple_counts["external"], "local_ss_tuples": tuple_counts["local"],
            "indexed_symbolic_tuples": tuple_counts["indexed"], "disjoint_intersections": intersections,
            "tuple_union_count": 148,
            "all_declared_target_frame_addend_identities_match_current_omf": True,
            "all_signed_sites_are_offset16_and_framed_dgroup": True,
            "positive_owner_anchors": owner_rows,
            "queue_owner_anchor": {"symbol": "_input_queue", "communals": queue},
            "unresolved_external_fixups": {"symbol_count": len(unresolved_external_refs),
                                             "reference_count": sum(unresolved_external_refs.values()),
                                             "high_priority": {k: unresolved_external_refs[k] for k in ("_g_5A9C", "_g_8ED8")}},
            "omf_fixups_by_location_kind": dict(sorted(loc_count.items())),
            "omf_fixups_by_frame": {f"{k}:{v}": n for (k, v), n in sorted(frame_count.items(), key=lambda kv: (kv[0][0], str(kv[0][1])))},
            "report_source_binding_check_summary": {"checks": len(report_binding_checks),
                                                       "checks_by_module": dict(sorted(Counter(x["module"] for x in report_binding_checks).items())),
                                                       "identity_sha256": canonical_json_hash(report_binding_checks),
                                                       "site_offsets_are_exact_only_when_declared": True},
            "packet_check_summary": {"checks": len(packet_checks),
                                     "counts_by_packet_and_kind": {f"{p}:{k}": n for (p, k), n in sorted(packet_check_counts.items())},
                                     "identity_sha256": canonical_json_hash(packet_checks)},
            "signed_frame_site_omf_rows": signed_frame_site_rows,
            "additional_exact_packet_site_omf_rows": list(additional_exact_packet_sites.values()),
        },
        "concrete_unresolved_frontier": unresolved_candidates,
        "separate_open_non_address_dependencies": [
            "The build report still lists remaining-assembly-address-audit as UNRESOLVED.",
            "The unresolved g_8ED8 owner/extent/resource relationship and S01:328E entry SS state remain separate from the accepted 148-site frames.",
            "g_5A9C storage and initializer ownership remain unresolved despite the reviewed DGROUP segment-frame correction.",
            "The 046C:0000 purpose/runtime owner remains unknown; the prior no-MZ-relocation result is only cited, not rechecked from original bytes.",
            "Unchecked error-path addresses and missing-provider / computed-alias questions are not closed by this inventory.",
        ],
        "active_binding_packet_pins": packet_pins,
        "claim_limit": "Bounded full-current-report receipt plus exact operand families and actual OMF fixup identities; classifications are evidence-backed for listed sites only. No claim that all possible computed aliases, missing providers, owner extents, or future indirect entry paths are closed.",
    }
    OUT.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    script_sha = script_pin["sha256"]
    tool_drift_text = "Report/current tool pins: " + "; ".join(
        f"`{x['path']}` {x['report_input_pin']['sha256']} -> {x['current_file_pin']['sha256']}" +
        (" (changed after report snapshot)" if x["changed_since_report_snapshot"] else " (same)")
        for x in tooling_snapshot)
    lines = [
        "# SOURCE_ONLY_DOS numeric/frame inventory v30", "",
        "**Observation only; root review false.** This fresh census pins the current build report and every one of its 186 effective sources, generated sources, and OMF objects. It keeps `remaining-assembly-address-audit` **UNRESOLVED**. No original executable bytes, compiler/linker reruns, production edits, or canonical writes were used.", "",
        f"Current report SHA-256: `{report_pin['sha256']}`. Current scope: 127 canonical TUs, 29 strict substitutions, 59 source-owned providers, and 22 unresolved external names. The prior v18 inventory covers 154 TUs and is pinned only as historical comparison: `{historical_pins[0]['sha256']}`. The prior address classification is separately pinned at `{historical_pins[2]['sha256']}`.",
        tool_drift_text, "",
        "The focused generated-source census finds no numeric `SS:[...+literal]` memory operand remaining. The seven known source families (3DCA, 41D0, 6778, 4220, 68AC, 2226, 68B4) are symbolic. The current report's applied relocation identities and root-reviewed frame/index packets were checked against actual OMF. The 128 external, 10 local, and 10 indexed SS/DGROUP tuples are disjoint; each exact tuple resolves to one OFFSET16 fixup framed by DGROUP with its expected target and addend. Packet offsets are exact; source-binding report rows without offsets are recorded as target/frame/addend identity lower-bound checks. Positive current PUBDEF anchors exist for `_g_3DCA`, `_g_3DFC`, `_g_41D0`, `_g_4220`, `_glyph_edge_masks`, `_mono_tail_masks`, and `_packed_tail_masks`; all are in the actual OMF DGROUP, and tail-mask rows establish current functional views, not historical storage identity.", "",
        "The remaining concrete link-layout address family is `S01:328E`, `add bx, 8ED8h`, at source lines " + ", ".join(str(x['source_line']) for x in eight_sites) + ". Its 32 following indexed reads use explicit SS, but the ADD immediates have no OMF relocation; `_g_8ED8` remains an unresolved owner with no accepted extent. The adjacent `_g_8EC0` prefix ends at 8ED8 and does not prove the next owner. Retain the independent resource extent and per-entry SS questions.", "",
        "The 43 direct ES addresses are BDA/IVT/video-aperture operations with source-line-verified ES state anchors; the generated-source census finds no other unsegmented direct numeric memory bracket. Eight direct DS forms in S03:3258 are LEAs constructing selectors. The six generated C modules contain 18 inline-ASM blocks: one `ES:[BX]` is anchored by `ES=0, BX=0408h` (BDA), and one uses the ES:BX pointer returned by INT 15h (runtime-derived); other inline forms are I/O ports, BIOS calls, or local/register arithmetic. Thirty-six far-pointer casts classify as BDA, BIOS ROM, Tandy ROM, or the separate absolute read `046C:0000` (physical 0x46C0). Its purpose and runtime owner remain unknown. The earlier no-MZ-relocation result is cited from the pinned audit and was not revalidated against original executable bytes.", "",
        "`_g_5A9C` has the exact BASE16 segment target/frame correction in OMF, but its storage/initializers remain unresolved. Unknown computed aliases, unchecked error-path addresses, missing-provider cases, and the report's other layout gates remain outside this bounded classification.", "",
        f"Repeatable checker: `{script_rel}` (SHA-256 `{script_sha}`). Machine receipt: `numeric-frame-inventory-v30.json`.",
    ]
    MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"report_sha256": report_pin["sha256"], "scope": got_counts,
                      "raw_numeric_ss_generated": len(generated_numeric_ss),
                      "direct_segment_memory": len(direct_seg), "direct_es": len(direct_es),
                      "selector_leas": len(selector_leas), "far_casts": len(far_cast_sites),
                      "add_immediates": len(add_immediates), "8ed8_adds": len(eight_sites),
                      "omf_source_binding_checks": len(report_binding_checks),
                      "omf_packet_checks": len(packet_checks), "unresolved_ext_refs": sum(unresolved_external_refs.values()),
                      "gate": gate["status"], "root_reviewed": False}, indent=2))


if __name__ == "__main__":
    main()
