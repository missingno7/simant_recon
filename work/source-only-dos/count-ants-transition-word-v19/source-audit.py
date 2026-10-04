"""Pinned, name-specific source review for the v19 saved scalar candidate."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "build/workers/dos_saved_scalar_words_v19"
NAME = "fd_50F6_0354"
IMPORT = "_" + NAME


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def pin(path: Path) -> dict:
    raw = path.read_bytes()
    return {
        "path": path.resolve().relative_to(ROOT).as_posix(),
        "sha256": sha(raw),
        "size": len(raw),
    }


def load(relative: str):
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def main() -> None:
    inventory_rel = "build/workers/dos_far_word_inventory/inventory.json"
    index_rel = "work/source-only-dos/static-completeness/index-v1.json"
    report_rel = "build/source-only-dos/build-report.json"
    symbols_rel = "layout/symbols.json"
    inventory = load(inventory_rel)
    static_index = load(index_rel)
    build_report = load(report_rel)
    symbols = load("layout/symbols.json")
    import_row = next(row for row in inventory["imports"]
                      if row["import"] == IMPORT)
    current_missing = next((row for row in build_report["unresolved_symbols"]
                            if row["name"] == IMPORT), None)
    if current_missing is None:
        raise SystemExit(f"{IMPORT} is no longer in the current missing-symbol report")

    source_pins = inventory["source_receipts"]
    if len(source_pins) != 156 or len({row["path"] for row in source_pins}) != 156:
        raise SystemExit("source receipt set is not the expected 156 unique-path graph")
    canonical = [row for row in source_pins if row["set"] == "canonical_127"]
    effective = [row for row in source_pins if row["set"] == "effective_strict_29"]
    strict_functions = set(static_index["entries"].keys())
    receipt_functions = {row["function"] for row in effective}
    if len(canonical) != 127 or len(effective) != 29 or strict_functions != receipt_functions:
        raise SystemExit("source receipt graph disagrees with the 127+29 static source sets")

    actual_hits = []
    pattern = re.compile(rf"\b{re.escape(NAME)}\b")
    for receipt in source_pins:
        path = ROOT / receipt["path"]
        raw = path.read_bytes()
        if len(raw) != receipt["size"] or sha(raw) != receipt["sha256"]:
            raise SystemExit(f"pinned source changed: {receipt['path']}")
        text = raw.decode("latin1")
        for line_no, line in enumerate(text.splitlines(), 1):
            if pattern.search(line):
                actual_hits.append({"path": receipt["path"], "line": line_no,
                                    "text": line.strip(), "set": receipt["set"]})

    references = import_row["references"]
    expected_hits = [{"path": row["path"], "line": row["line"],
                      "text": row["text"].strip(), "set": row["set"]}
                     for row in references]
    sort_hit = lambda row: (row["path"], row["line"], row["set"])
    if sorted(actual_hits, key=sort_hit) != sorted(expected_hits, key=sort_hit):
        actual_keys = {(row["path"], row["line"], row["text"], row["set"])
                       for row in actual_hits}
        expected_keys = {(row["path"], row["line"], row["text"], row["set"])
                         for row in expected_hits}
        raise SystemExit(json.dumps({
            "error": "exact-name scan across 156 pinned files differs from the source inventory",
            "extra": sorted(actual_keys - expected_keys),
            "missing": sorted(expected_keys - actual_keys),
        }, indent=2))
    if import_row["declaration_group"] != "complete_primitive_scalar_or_array":
        raise SystemExit("candidate declarations are not mechanically complete primitive views")
    if import_row["source_extent_bytes_mechanical"] != 2 or import_row["source_extent_conflicting_or_unknown"]:
        raise SystemExit("candidate does not have a closed source-derived two-byte extent")
    if import_row["registered_interior_names_within_source_extent"]:
        raise SystemExit("candidate has a registered interior symbol")
    if import_row["registry_aliases"] != [NAME]:
        raise SystemExit("candidate has a second/unhandled registered base alias")
    registered = symbols["data"].get(NAME)
    if not registered or registered["seg"] != 0x50F6 or registered["off"] != 0x0354:
        raise SystemExit("symbol registry does not ground this name at 50F6:0354")

    declaration_receipts = []
    for source, line, declaration, view_kind, byte_size, *_ in import_row["declarations"]:
        if declaration != f"extern int far {NAME};" or view_kind != "complete_primitive" or byte_size != 2:
            raise SystemExit(f"unexpected declaration view for {NAME}: {source}:{line}: {declaration}")
        declaration_receipts.append({"path": source, "line": line,
                                     "declaration": declaration, "type": "signed int far",
                                     "bytes": 2})

    save_rows = import_row["save_rec_rows"]
    if len(save_rows) != 1 or save_rows[0]["element_size"] != 2 or save_rows[0]["element_count"] != 1:
        raise SystemExit("candidate does not have exactly one SaveRec {2,1} row")
    row = save_rows[0]
    if row["serialized_bytes"] != 2 or row["target_names"] != [NAME]:
        raise SystemExit("SaveRec row target or serialized extent disagrees with candidate")

    provider_rel = "build/workers/dos_saved_scalar_words_v19/providers/saved-scalar-words-v19.c"
    provider_pin = pin(ROOT / provider_rel)
    provider = (ROOT / provider_rel).read_text(encoding="ascii")
    if provider.count(f"int far {NAME};") != 1 or re.search(r"\b(?:void|int|long)\s+far\s+\w+\s*\(", provider):
        raise SystemExit("provider must remain a data-only single-object candidate")

    consumer_path = ROOT / "src/S09/m35F5.c"
    consumer_text = consumer_path.read_text(encoding="latin1").splitlines()
    save_view = {"path": "src/S09/m35F5.c", "line": row["line"],
                 "text": consumer_text[row["line"] - 1],
                 "size": row["element_size"], "count": row["element_count"],
                 "bytes": row["serialized_bytes"], "table_index_1based": row["table_index"]}
    load_save_views = []
    for line_no in (118, 183):
        load_save_views.append({"path": "src/S09/m35F5.c", "line": line_no,
                                "text": consumer_text[line_no - 1]})

    input_paths = [inventory_rel, index_rel, report_rel, symbols_rel,
                   "layout/manifest.json", "work/source-only-dos/compile-and-intake-v1.json",
                   "tools/dos_source_bindings.py",
                   "build/workers/dos_saved_scalar_words_v19/source_review_v19.py"]
    selection_hash = pin(ROOT / report_rel)
    probe_rel = "build/workers/dos_saved_scalar_words_v19/runtime/durable-v19/saved-scalar-words-probe-v19.json"
    probe_path = ROOT / probe_rel
    probe_pin = pin(probe_path) if probe_path.exists() else None
    if probe_pin:
        probe_doc = load(probe_rel)
        probe_status = {"path": probe_rel, "sha256": probe_pin["sha256"],
                        "all_expected_outcomes_pass": probe_doc["runtime"]["all_expected_outcomes_pass"],
                        "cases": len(probe_doc["runtime"]["cases"])}
    else:
        probe_status = None

    read_refs = [row for row in references if row["access"] in
                 ("read_or_expression", "indexed_or_member", "read_increment")]
    write_refs = [row for row in references if row["access"] in
                  ("write_assignment", "write_increment", "write_decrement")]
    save_escape_refs = [row for row in references if row["access"] == "address_escape"]
    other_refs = [row for row in references if row not in read_refs + write_refs + save_escape_refs
                  and row["access"] != "declaration"]
    if not read_refs or not write_refs or len(save_escape_refs) != 1 or other_refs:
        raise SystemExit("candidate has incomplete direct read/write/SaveRec reference closure")

    review = {
        "schema": "simant-dos-saved-scalar-words-source-review-v19",
        "status": "ROOT_REVIEW_PENDING_UNADMITTED",
        "claim_boundary": "natural source-functional typed storage only; no historical COMDEF TU/order/layout/padding claim",
        "scope": {
            "canonical_translation_units": len(canonical),
            "effective_strict_sources": len(effective),
            "unique_pinned_sources": len(source_pins),
            "static_index_path": index_rel,
            "static_index_sha256": pin(ROOT / index_rel)["sha256"],
            "reference_inventory_path": inventory_rel,
            "reference_inventory_sha256": pin(ROOT / inventory_rel)["sha256"],
            "exact_name_scan_result": "all occurrences in the full 127+29 source graph match the source inventory",
            "exact_name_reference_count": len(references),
            "source_files_with_references": len({row["path"] for row in references}),
        },
        "missing_filter_only": {
            "build_report": selection_hash,
            "name": IMPORT,
            "present_in_current_unresolved_symbols": True,
            "authority_limit": "current mutable build report selects a still-missing name only; type, extent, aliases, producer/consumer graph, and SaveRec are established by the pinned source graph and registry",
            "accepted_storage_candidates": current_missing.get("accepted_storage_candidates", []),
        },
        "candidate_table": [{
            "name": IMPORT,
            "family": "CountAnts transition/suppression latch",
            "registered_address": "50F6:0354",
            "source_type": "signed int far scalar",
            "source_extent_bytes": 2,
            "saved_extent": {"size": 2, "count": 1, "bytes": 2,
                             "table_index_1based": row["table_index"],
                             "path": "src/S09/m35F5.c", "line": row["line"]},
            "provider": provider_pin["path"],
            "import_reduction_ceiling": 1,
            "ownership_basis": "complete declarations and direct read/write graph, CountAnts clear-after-count lifecycle, three transition/reset producers, and exact generic two-byte SaveRec view",
            "limits": ["raw save loads can replace the word; no universal value or scheduling domain is claimed",
                       "no registered interior or alternate-base symbol exists in the 2-byte span",
                       "historical COMDEF producer TU/order, FAR_BSS order, padding, and absolute placement remain unknown"],
        }],
        "source_inventory": {
            "path": inventory_rel,
            "sha256": pin(ROOT / inventory_rel)["sha256"],
            "source_graph_pins": source_pins,
            "target_declarations": declaration_receipts,
            "read_receipts": read_refs,
            "write_receipts": write_refs,
            "save_address_escape": save_escape_refs,
            "all_exact_references": references,
            "other_unclassified_escapes": other_refs,
        },
        "algorithm_and_consumers": {
            "pre_load_reset": {"path": "src/S09/m35F5.c", "function": "o09_35F5_0D7A", "line": 555,
                               "text": consumer_text[554],
                               "context": "comment at line 552 says the routine resets the yard before a saved game is read; it sets this latch to 1 before RandYard"},
            "new_game_producer": {"path": "src/S15/m384C.c", "function": "NewGame", "line": 299,
                                  "text": (ROOT / "src/S15/m384C.c").read_text(encoding="latin1").splitlines()[298]},
            "transfer_producer": {"path": "src/root/m015B.c", "function": "XferPatch", "line": 419,
                                  "text": (ROOT / "src/root/m015B.c").read_text(encoding="latin1").splitlines()[418]},
            "count_algorithm": {"path": "src/root/m0BE8.c", "function": "CountAnts",
                                "read_guards": [references[8], references[9]],
                                "clear_after_recompute": references[10],
                                "behavior": "the latch gates both caste-completion event paths; CountAnts clears it after recomputing both six-slot population vectors"},
            "save_load_view": {"table_row": save_view,
                               "generic_io": load_save_views,
                               "behavior": "LoadGame/SaveGame pass p->data to read/write for p->count * p->size bytes; the candidate row therefore transports exactly two bytes"},
        },
        "alias_and_layout_review": {
            "registered_base": {"segment": registered["seg"], "offset": registered["off"],
                                 "grounding": registered["grounding"]},
            "registry_names_in_candidate_extent": import_row["registry_aliases"],
            "registered_interiors": import_row["registered_interior_names_within_source_extent"],
            "extent_basis": "signed int far scalar declaration in every source view plus {2,1} SaveRec row; no address-gap inference",
            "same_base_alias_handled": True,
            "pointer_array_or_struct_views": False,
            "mixed_width_source_views": False,
            "numeric_or_assembly_escape": False,
            "only_address_escape": "the SaveRec address row, passed through generic byte-counted I/O",
        },
        "provider_boundary": "one tentative int far definition in a scratch data-only source provider; no canonical/provider registry or production build changes",
        "runtime_probe": probe_status,
        "pins": [pin(ROOT / rel) for rel in input_paths],
        "limits": ["SaveRec payload is raw; arbitrary restored 16-bit values remain possible and no legal game-state domain is asserted",
                   "source-functional object ownership does not recover historical COMDEF-producing translation unit or ordering",
                   "this package is unadmitted and does not alter canonical files, production tools, or Git state"],
    }
    json_path = OUT / "source-review-v19.json"
    json_path.write_text(json.dumps(review, indent=2) + "\n", encoding="utf-8")
    md = [
        "# Saved scalar word v19 source review",
        "",
        "Status: `ROOT_REVIEW_PENDING_UNADMITTED`. This is a natural source-functional storage candidate, not a historical COMDEF identity or placement claim.",
        "",
        "The one classified row is `_fd_50F6_0354`, a two-byte signed `int far` scalar. The full pinned graph has 127 canonical TUs plus all 29 strict effective sources (156 unique files); all 13 exact identifier hits match the source inventory. The current build report is used only to confirm that this name remains missing.",
        "",
        "`o09_35F5_0D7A` sets the latch before `RandYard` while preparing to load a saved game. `NewGame` and `XferPatch` also set it. `CountAnts` reads it in both caste-completion guards and clears it after recomputing the population counts. The S09 SaveRec table has one `{2,1,&fd_50F6_0354}` row; generic `LoadGame`/`SaveGame` I/O uses `p->count * p->size`, so this view carries two bytes.",
        "",
        "The only address escape is the SaveRec row. All source declarations are signed `int far`; the registry has only the candidate's exact base spelling and no registered interior. No numeric, assembly, pointer-array, aggregate, or mixed-width storage view was found. The separate `int far` definition is in [saved-scalar-words-v19.c](providers/saved-scalar-words-v19.c).",
        "",
        "The source-supported storage type/extent does not establish a legal value domain or a universal scheduling/lifetime rule: raw save payloads can replace the word. Original COMDEF-producing TU/order, FAR_BSS ordering, padding, and absolute placement remain unknown.",
        "",
        "Machine-readable source receipts and all 156 source pins are in [source-review-v19.json](source-review-v19.json). The latest runtime result is recorded there after the probe completes.",
        "",
    ]
    (OUT / "source-review-v19.md").write_text("\n".join(md), encoding="utf-8")
    print(f"wrote {json_path.relative_to(ROOT)} refs={len(references)} pins={len(source_pins)} probe={bool(probe_status)}")


if __name__ == "__main__":
    main()
