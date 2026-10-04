#!/usr/bin/env python3
"""Pinned source-domain audit for six sound-control FAR_BSS word candidates."""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "build/workers/dos_sound_control_words_v20"
TARGETS = [
    ("fd_50F6_4A46", 0x4A46, "derived-port word (source stores 4B14 + 2; no direct read found)"),
    ("fd_50F6_4A48", 0x4A48, "channel-count word (source writes 2 or 4; read as a loop bound)"),
    ("fd_50F6_4A4A", 0x4A4A, "sound-selection flag candidate (source writes 0 and tests it)"),
    ("fd_50F6_4A4C", 0x4A4C, "record-index word (source resets/increments it; indexes 4A4E records)"),
    ("fd_50F6_4B14", 0x4B14, "port word (source stores a detected port or defaults and passes/reads it)"),
    ("fd_50F6_4B16", 0x4B16, "signed level-adjustment candidate (source stores -40 and adds it to volume)"),
]
INVENTORY = "build/workers/dos_far_word_inventory/inventory.json"
STATIC_INDEX = "work/source-only-dos/static-completeness/index-v1.json"
MANIFEST = "layout/manifest.json"
SYMBOLS = "layout/symbols.json"
BUILD_REPORT = "build/source-only-dos/build-report.json"

sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / "tools"))
import csrc  # noqa: E402


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def pin(path: Path, display: str | None = None) -> dict:
    raw = path.read_bytes()
    return {"path": display or path.resolve().relative_to(ROOT).as_posix(),
            "sha256": digest(raw), "size": len(raw)}


def load(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def source_domain() -> tuple[list[dict], list[dict], dict]:
    manifest = load(MANIFEST)
    canonical = []
    for module, row in manifest["modules"].items():
        rel = row["source"].replace("\\", "/")
        actual = pin(ROOT / rel, rel)
        if actual["sha256"] != row["source_sha256"]:
            raise RuntimeError("canonical source pin drift: " + rel)
        canonical.append(actual | {"set": "canonical_127", "module": module})
    if len(canonical) != 127:
        raise RuntimeError(f"expected 127 canonical sources, found {len(canonical)}")

    index = load(STATIC_INDEX)
    if index.get("schema") != "simant-dos-strict-static-index-v1" or len(index.get("entries", {})) != 29:
        raise RuntimeError("strict-effective index is not the expected 29-entry source set")
    build_report = load(BUILD_REPORT)
    substitutions = build_report.get("semantic_substitutions", [])
    strict_rows = {row["function"]: row for row in substitutions}
    if set(strict_rows) != set(index["entries"]):
        raise RuntimeError("current effective source rows disagree with strict index function identities")
    effective = []
    for function, ref in sorted(index["entries"].items()):
        review_path = ref["path"]
        review_pin = pin(ROOT / review_path, review_path)
        if review_pin["sha256"] != ref["sha256"] or review_pin["size"] != ref["size"]:
            raise RuntimeError("strict receipt pin drift: " + review_path)
        review = json.loads((ROOT / review_path).read_text(encoding="utf-8"))
        registered_source = review.get("registered_source") or review.get("audit", {}).get("source")
        if not registered_source:
            raise RuntimeError("strict receipt has no registered source: " + function)
        source = strict_rows[function]["source"]
        rel = source["path"].replace("\\", "/")
        actual = pin(ROOT / rel, rel)
        if actual["sha256"] != source["sha256"] or actual["size"] != source["size"]:
            raise RuntimeError("strict-effective source pin drift: " + rel)
        effective.append(actual | {"set": "effective_strict_29", "function": function,
                                  "module": strict_rows[function]["module"],
                                  "static_receipt": review_pin,
                                  "registered_source": registered_source})
    if len(effective) != 29:
        raise RuntimeError("strict-effective source count changed")
    paths = [row["path"] for row in canonical + effective]
    if len(set(paths)) != 156:
        raise RuntimeError(f"source graph must have 156 unique paths, found {len(set(paths))}")
    existing_inventory = load(INVENTORY)
    inventory_pins = {row["path"].replace("\\", "/"): row["sha256"]
                      for row in existing_inventory["source_receipts"]}
    fresh_pins = {row["path"]: row["sha256"] for row in canonical + effective}
    if inventory_pins != fresh_pins:
        raise RuntimeError("current 127+29 graph differs from the FAR-word inventory source pins")
    return canonical, effective, existing_inventory


def token_hits(rel: str, raw: bytes, names: set[str]) -> list[dict]:
    text = raw.decode("latin1")
    hits = []
    if Path(rel).suffix.lower() == ".asm":
        for line_no, line in enumerate(text.splitlines(), 1):
            for name in names:
                if re.search(r"(?<![A-Za-z0-9_$])" + re.escape(name) + r"(?![A-Za-z0-9_$])",
                             line, re.I):
                    hits.append({"path": rel, "line": line_no, "name": name,
                                 "text": line.strip(), "lexical_domain": "assembly-text"})
        return hits
    for tok in csrc.tokenize(text):
        line_no = text.count("\n", 0, tok.s) + 1
        if tok.kind == "id" and tok.text in names:
            line = text.splitlines()[line_no - 1] if line_no <= len(text.splitlines()) else ""
            hits.append({"path": rel, "line": line_no, "name": tok.text,
                         "text": line.strip(), "lexical_domain": "C-identifier"})
        elif tok.kind == "asm":
            for name in names:
                if re.search(r"(?<![A-Za-z0-9_$])" + re.escape(name) + r"(?![A-Za-z0-9_$])",
                             tok.text, re.I):
                    hits.append({"path": rel, "line": line_no, "name": name,
                                 "text": tok.text.strip(), "lexical_domain": "inline-assembly"})
    return hits


def numeric_hits(rel: str, raw: bytes, offsets: set[int]) -> list[dict]:
    text = raw.decode("latin1")
    found = []
    for line_no, line in enumerate(text.splitlines(), 1):
        low = line.lower()
        for off in offsets:
            h = f"{off:04x}"
            decimal = str(off)
            pats = [rf"(?<![a-z0-9_])0x0*{h}(?![a-z0-9_])",
                    rf"(?<![a-z0-9_])0*{h}h(?![a-z0-9_])",
                    rf"(?<![a-z0-9_]){decimal}(?![a-z0-9_])",
                    rf"(?<![a-z0-9_])(?:0x)?50f6h?\s*:\s*(?:0x)?0*{h}h?(?![a-z0-9_])",
                    rf"(?<![a-z0-9_])0x0*{(0x50F60000 + off):08x}(?![a-z0-9_])",
                    rf"(?<![a-z0-9_])0x0*{((0x50F6 << 4) + off):x}(?![a-z0-9_])"]
            if any(re.search(pat, low, re.I) for pat in pats):
                found.append({"path": rel, "line": line_no, "offset_token": h.upper(),
                              "text": line.strip()})
    return found


def main() -> None:
    canonical, effective, inventory = source_domain()
    symbols_all = load(SYMBOLS)["data"]
    build_report = load(BUILD_REPORT)
    symbols_at: dict[tuple[int, int], list[str]] = {}
    for name, row in symbols_all.items():
        if isinstance(row.get("seg"), int) and isinstance(row.get("off"), int):
            symbols_at.setdefault((row["seg"], row["off"]), []).append(name)

    all_scoped_names = set()
    targets = []
    address_occupants = []
    for name, offset, gloss in TARGETS:
        row = next((r for r in inventory["imports"] if r["import"] == "_" + name), None)
        if row is None:
            raise RuntimeError("target absent from source inventory: " + name)
        if row["source_extent_bytes_mechanical"] != 2 or row["source_extent_conflicting_or_unknown"]:
            raise RuntimeError("not a mechanically complete two-byte source view: " + name)
        if row["declaration_group"] != "complete_primitive_scalar_or_array":
            raise RuntimeError("unexpected declaration group: " + name)
        if any(d[2] != f"extern int far {name};" or d[3] != "complete_primitive" or d[4] != 2
               for d in row["declarations"]):
            raise RuntimeError("source declarations are not consistent signed int far scalars: " + name)
        registered = symbols_all.get(name)
        if not registered or registered["seg"] != 0x50F6 or registered["off"] != offset:
            raise RuntimeError("registered exact base is missing or moved: " + name)
        exact_aliases = sorted(symbols_at.get((0x50F6, offset), []))
        if name not in exact_aliases:
            raise RuntimeError("candidate absent from same-address registry names: " + name)
        all_scoped_names.update(exact_aliases)
        overlaps = sorted((n, s["off"]) for n, s in symbols_all.items()
                          if s.get("seg") == 0x50F6 and offset <= s.get("off", -1) < offset + 2)
        address_occupants.append({"name": name, "span_used_for_overlap_only":
                                  {"segment": "50F6", "start": f"{offset:04X}", "bytes": 2},
                                  "registered_names_inside_span": overlaps,
                                  "same_address_registered_names": exact_aliases,
                                  "next_registered_names_after_start": sorted(
                                      (n, s["off"]) for n, s in symbols_all.items()
                                      if s.get("seg") == 0x50F6 and s.get("off") == offset + 2)})
        target_row = next((r for r in build_report.get("unresolved_symbols", [])
                           if r.get("name") == "_" + name), None)
        targets.append({
            "name": name, "import": "_" + name, "registered_address": f"50F6:{offset:04X}",
            "tentative_semantic_label": gloss, "source_type": "signed int far scalar",
            "source_extent_bytes": 2, "registry_aliases_at_exact_base": exact_aliases,
            "registry_grounding": registered.get("grounding", ""),
            "mechanical_declaration_receipts": [
                {"path": d[0], "line": d[1], "declaration": d[2], "kind": d[3], "bytes": d[4]}
                for d in row["declarations"]],
            "references": row["references"],
            "source_extent_interiors": row["registered_interior_names_within_source_extent"],
            "save_rec_rows": row["save_rec_rows"],
            "inventory_classification": row["declaration_group"],
            "current_missing_import_observation": target_row is not None,
        })

    references = []
    inventory_reference_keys = set()
    for target in targets:
        for ref in target["references"]:
            if ref["access"] != "declaration":
                references.append(ref)
            inventory_reference_keys.add((ref["path"].replace("\\", "/"), ref["line"],
                                          ref["name"], ref["text"].strip()))
    lexical_hits = []
    numeric = []
    for receipt in canonical + effective:
        raw = (ROOT / receipt["path"]).read_bytes()
        lexical_hits.extend(token_hits(receipt["path"], raw, all_scoped_names))
        numeric.extend(numeric_hits(receipt["path"], raw, {off for _, off, _ in TARGETS}))
    scanned_reference_keys = {(h["path"], h["line"], h["name"], h["text"])
                              for h in lexical_hits}
    inventory_refs_scanned = {(p, line, name, text) for p, line, name, text in inventory_reference_keys
                              if name in all_scoped_names}
    # The inventory's six raw names and the fresh token scan must agree exactly.
    target_inventory_keys = {(ref["path"].replace("\\", "/"), ref["line"], ref["name"],
                              ref["text"].strip())
                             for target in targets for ref in target["references"]}
    target_scanned_keys = {(h["path"], h["line"], h["name"], h["text"])
                           for h in lexical_hits if h["name"] in {t[0] for t in TARGETS}}
    if target_scanned_keys != target_inventory_keys:
        raise RuntimeError("fresh 156-source identifier scan differs from inventory; extra=" +
                           repr(sorted(target_scanned_keys - target_inventory_keys)) +
                           " missing=" + repr(sorted(target_inventory_keys - target_scanned_keys)))

    asm_hits = [h for h in lexical_hits if h["lexical_domain"] in ("assembly-text", "inline-assembly")]
    non_declaration_refs = [r for r in references if r["access"] != "declaration"]
    address_escapes = [r for r in references if r["access"] == "address_escape"]
    save_rec_rows = [{"name": t["name"], "rows": t["save_rec_rows"]} for t in targets]
    provider_path = OUT / "providers/SNDCTRL.C"
    provider_text = provider_path.read_text(encoding="ascii")
    if any(provider_text.count(f"int far {name};") != 1 for name, _, _ in TARGETS):
        raise RuntimeError("candidate provider does not define each target once")
    if re.search(r"\b(?:void|char|int|long)\s+far\s+\w+\s*\(", provider_text):
        raise RuntimeError("candidate provider contains a function definition")
    probe_path = OUT / "runtime/probe-v20.json"
    runtime = None
    if probe_path.exists():
        runtime_doc = json.loads(probe_path.read_text(encoding="utf-8"))
        runtime = pin(probe_path) | {"all_expected_outcomes_pass":
                                     runtime_doc["runtime"]["all_expected_outcomes_pass"]}

    result = {
        "schema": "simant-dos-sound-control-words-source-review-v20",
        "status": "ROOT_REVIEW_PENDING_UNADMITTED",
        "root_reviewed": False,
        "claim_boundary": "source-functional scalar ownership only; no historical COMDEF translation unit/order, original physical placement, or arbitrary-raw-value safety claim",
        "source_graph": {
            "canonical_translation_units": len(canonical),
            "effective_strict_sources": len(effective),
            "unique_pinned_source_paths": len(canonical + effective),
            "static_index": pin(ROOT / STATIC_INDEX),
            "source_only_manifest": pin(ROOT / MANIFEST),
            "strict_static_index_entries": len(load(STATIC_INDEX)["entries"]),
            "source_pins": canonical + effective,
            "all_source_pins_match": True,
        },
        "candidate_provider": {
            "path": pin(provider_path)["path"], "sha256": pin(provider_path)["sha256"],
            "basename": "SNDCTRL", "module_id": "source-owned:sound-control-words",
            "source_shape": "six independent uninitialized int far tentative definitions; no functions; one data-only candidate source",
            "expected_comdef_bytes_total": 12,
            "extent_basis": "each complete source declaration plus independent registry base; no adjacent-gap or array-span inference",
            "historical_definition_owner": "unknown",
        },
        "candidate_words": targets,
        "source_reference_census": {
            "all_target_identifier_hits_match_inventory": True,
            "non_declaration_reference_count": len(non_declaration_refs),
            "raw_identifier_hits_including_exact_base_registry_aliases": lexical_hits,
            "target_references_from_mechanical_inventory": references,
            "same_address_registered_name_hits": [h for h in lexical_hits if h["name"] not in {t[0] for t in TARGETS}],
            "asm_and_inline_asm_hits": asm_hits,
            "address_escape_references": address_escapes,
            "save_rec_rows_by_target": save_rec_rows,
            "numeric_offset_token_hits_for_review": numeric,
            "numeric_hits_are_not_extents": True,
            "registered_overlap_census_without_gap_extent_inference": address_occupants,
        },
        "source_graph_findings": {
            "4A46": "only the direct source write fd_50F6_4A46 = fd_50F6_4B14 + 2 was found; source-function consumer/initial value was not found in the pinned graph",
            "4A48": "f_277E_0000 selects 2 or 4; sound setup bodies copy the word into saved selector word 1 and use it as a 4A4E record-loop bound",
            "4A4A": "source writes zero in f_277E_01FA and reads it as a conditional selector; no serialized SaveRec view was found",
            "4A4C": "setup resets/increments the word and uses it as an index into the separate fd_50F6_4A4E record array; this provider does not own that array or prove a bound for arbitrary values",
            "4B14": "f_293A_015E copies a detected port; f_277E setup also selects 01E0/C0 or 0220 values, then consumers pass/read it as a port",
            "4B16": "f_277E_040E stores -40; f_2815_0165 adds this signed int view to volume before clamping in that function",
            "address_escapes": "the inventory contains no target address_escape rows, SaveRec rows, registered interior names, or alternate-base aliases",
            "asm": "the fresh 156-source token census found no target or same-address alias reference in standalone or inline assembly" if not asm_hits else "assembly/inline-assembly references are enumerated above and require review",
        },
        "startup_zero_contract": {
            "candidate": "uninitialized FAR_BSS commons; no initializers in provider",
            "scope": "the fresh MSC 6.00AX + pinned CRT + RTLink fixtures below check zero at main for test-owned candidate storage; this does not prove historical COMDEF ownership or every foreign write path",
            "runtime_probe": runtime,
        },
        "current_missing_symbol_report": {
            "path": BUILD_REPORT, "sha256": pin(ROOT / BUILD_REPORT)["sha256"],
            "authority_limit": "observational selection only; source type and ownership come from pinned source/registry evidence",
            "all_six_still_missing": all(t["current_missing_import_observation"] for t in targets),
        },
        "pins": [pin(ROOT / INVENTORY), pin(ROOT / STATIC_INDEX), pin(ROOT / MANIFEST),
                 pin(ROOT / SYMBOLS), pin(ROOT / BUILD_REPORT), pin(provider_path), pin(Path(__file__))],
        "limits": [
            "the scalar storage shapes do not constrain values restored or written through untracked aliases, hooks, or outside the pinned source graph",
            "4A48 and 4A4C participate in indexed access; this review does not claim those accesses are safe for arbitrary 16-bit values",
            "no SaveRec row is used to enlarge or shrink any scalar; the adjacent fd_50F6_4A4E array is an independent object owned by the sibling review",
            "no historical COMDEF-producing TU, FAR_BSS ordering, padding, original address mapping, or original executable bytes are claimed or used",
            "candidate has not been integrated into the effective source build; all six imports remain unresolved and the report is unadmitted",
        ],
    }
    (OUT / "source-review-v20.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    target_lines = []
    for t in targets:
        refs = [r for r in references if r["name"] == t["name"] and r["access"] != "declaration"]
        target_lines.append(f"| `{t['registered_address']}` | `{t['name']}` | signed `int far`, 2 bytes | {len(refs)} | none |")
    md = [
        "# Sound-control word ownership candidate v20", "",
        "**Status: `ROOT_REVIEW_PENDING_UNADMITTED`; `root_reviewed: false`.** The bounded result supports six source-functional signed two-byte FAR_BSS scalars and one scratch data-only provider. It makes no historical object-order or physical-address claim.", "",
        "| Address | Registered name | Source type and extent | Non-declaration references | SaveRec |",
        "|---|---|---|---:|---|", *target_lines, "",
        "The source census pins 127 canonical translation units plus all 29 strict-effective implementations (156 unique files). A fresh C/ASM identifier pass over that graph agrees with the existing FAR_BSS inventory for every target name. The registry has no same-address alternate names or registered names inside any two-byte span. No address escape, SaveRec row, numeric target-offset operand, standalone assembly reference, or inline-assembly reference was found. Extents come from complete `int far` source declarations and exact registry bases; gaps between addresses were not used.", "",
        "The scratch provider defines each symbol once as an uninitialized `int far` and defines no functions. MSC 6.00AX object shape and the two pinned RTLink startup fixtures are in the probe receipt. Those fixtures check typed reads and raw byte views from zero at `main`, plus signedness, width, initializer, and shifted-base contrasts. The raw byte view is a storage test; it does not imply a SaveRec entry.", "",
        "Source labels remain tentative. `4A48` is written as 2 or 4 and used by setup loops; `4A4C` indexes the separate `4A4E` record array. Their ownership does not establish safety for arbitrary 16-bit contents. `4A46` is only written as `4B14 + 2` in the source graph. See the JSON for every reference and pin.", "",
        "The six words remain missing in the observed source-only report. The candidate does not close external writers, runtime callbacks, value ranges, historical COMDEF owner/order, FAR_BSS placement, or original address identity. The adjacent `4A4E` array and sound instrument table are outside this provider.", "",
        "Files: [provider](providers/SNDCTRL.C), [source census](source-review-v20.json), [probe](probe_v20.py), [raw runtime and OMF receipt](runtime/probe-v20.json).", "",
    ]
    (OUT / "source-review-v20.md").write_text("\n".join(md), encoding="utf-8")
    print(json.dumps({"report": str((OUT / "source-review-v20.json").relative_to(ROOT)),
                      "targets": len(targets), "source_pins": len(canonical + effective),
                      "identifier_hits": len(lexical_hits), "non_declaration_refs": len(references),
                      "numeric_hits": len(numeric), "asm_hits": len(asm_hits),
                      "address_escapes": len(address_escapes),
                      "save_rows": sum(len(t["save_rec_rows"]) for t in targets)}, indent=2))


if __name__ == "__main__":
    main()
