#!/usr/bin/env python3
"""Inventory frozen function routes against the current native source profile.

This is a read-only route census. It does not compile, regenerate, or admit code.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
from collections import Counter, defaultdict

ROOT = Path(__file__).resolve().parents[2]
FUNCTIONS = ROOT / "layout/functions.json"
SYMBOLS = ROOT / "layout/symbols.json"
MANIFEST = ROOT / "layout/manifest.json"
GENERATOR = ROOT / "portable/tools/recover_source.py"
PROFILE_DIR = ROOT / "build/workers/recovered_source_next10/generated"
PROVENANCE = PROFILE_DIR / "provenance.json"
BUILD = ROOT / "portable/build.py"
BUILD_RECEIPT = ROOT / "build/portable/simant-sdl3.build.json"
BUILD_EXE = ROOT / "build/portable/simant-sdl3.exe"
SDL_LIBRARY = ROOT / "build/sdl3-sdk/SDL3-3.4.16/x86_64-w64-mingw32/bin/SDL3.dll"
EVIDENCE = ROOT / "portable/tests/recovered/evidence/source-port-inventory-v1"
MODELS = {
    "drawHistGraph": {
        "path": "portable/ui_model/windows/history_render.c",
        "basis": "history_render paired command/raster receipts tie the S24 drawHistGraph route to this model; the captured Next10 executable includes the provider TU",
    },
    "MenuQuit": {
        "path": "portable/ui_model/dialogs/menu_quit.c",
        "basis": "portable/ui_model/dialogs/menu_quit.h states this model implements S15 MenuQuit",
    },
    "o26_39C7_022F": {
        "path": "portable/ui_model/windows/zoom.c",
        "basis": "zoom.h names S26 o26_39C7_022F as the modeled source constraint routine",
    },
    "ProcCasteEvent": {
        "path": "portable/ui_model/windows/control_events.c",
        "basis": "control_events.h explicitly names ProcCasteEvent as a model boundary; controls-next4 paired source report is finite-domain evidence",
        "evidence": "portable/tests/recovered/evidence/controls-next4/setup_reuse_differential.py",
        "limit": "bounded event inputs and supplied geometry/providers; this handwritten model is not the recovered source body",
    },
    "ProcModeEvent": {
        "path": "portable/ui_model/windows/control_events.c",
        "basis": "control_events.h explicitly names ProcModeEvent as a model boundary; controls-next4 paired source report is finite-domain evidence",
        "evidence": "portable/tests/recovered/evidence/controls-next4/setup_reuse_differential.py",
        "limit": "bounded event inputs and supplied geometry/providers; this handwritten model is not the recovered source body",
    },
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(path: str) -> Path:
    return (ROOT / path).resolve()


def func_key(unit: str, seg: int, off: int) -> str:
    return f"{unit}:{seg:04X}:{off:04X}"


def module_key(unit: str, seg: int) -> str:
    return f"{unit}:{seg:04X}"


def module_key_from_profile_row(row: dict) -> str | None:
    source = row.get("source", "")
    match = re.search(r"(?:^|/)src/(root|S\d+)/m([0-9A-Fa-f]{4})\.c$", source)
    if match:
        return module_key(match.group(1), int(match.group(2), 16))
    match = re.match(r"(root|S\d+)_m([0-9A-Fa-f]{4})(?:_|$)", row.get("name", ""))
    if match:
        return module_key(match.group(1), int(match.group(2), 16))
    return None


def provider_definitions(paths: list[Path]) -> dict[str, list[str]]:
    """Collect readable top-level function definitions (candidate names only)."""
    result: dict[str, set[str]] = defaultdict(set)
    for path in paths:
        text = path.read_text(encoding="utf-8", errors="replace")
        lines = text.splitlines()
        i = 0
        while i < len(lines):
            line = lines[i]
            if not line or line[0].isspace() or line.startswith(("#", "//", "/*", "*")):
                i += 1
                continue
            chunk = line
            j = i
            while j + 1 < len(lines) and not any(x in chunk for x in ("{", ";")) and j - i < 12:
                j += 1
                chunk += "\n" + lines[j]
            head = chunk.split("{", 1)[0]
            if "{" in chunk and ";" not in head and "(" in head:
                prefix = head.split("(", 1)[0].strip()
                match = re.search(r"([A-Za-z_]\w*)\s*$", prefix)
                if match and match.group(1) not in {"if", "for", "while", "switch"}:
                    result[match.group(1)].add(path.relative_to(ROOT).as_posix())
            i = max(i + 1, j + 1)
    return {name: sorted(files) for name, files in result.items()}


def source_risks(paths: list[Path]) -> dict:
    bare_unsigned = re.compile(r"\bunsigned\s+(?!char\b|short\b|int\b|long\b)([A-Za-z_]\w*)")
    shift = re.compile(r"(?:<<|>>)")
    unsigned_hits, shift_hits = [], []
    for path in paths:
        text = path.read_text(encoding="utf-8", errors="replace")
        for line_no, line in enumerate(text.splitlines(), 1):
            for match in bare_unsigned.finditer(line):
                unsigned_hits.append({"path": path.relative_to(ROOT).as_posix(),
                    "line": line_no, "declaration_or_use": line.strip(),
                    "identifier_after_bare_unsigned": match.group(1)})
            if shift.search(line):
                shift_hits.append({"path": path.relative_to(ROOT).as_posix(),
                    "line": line_no, "expression_line": line.strip(),
                    "review_reason": "integer promotions and host-width operands can differ from DOS 16-bit int semantics"})
    return {"bare_unsigned_count": len(unsigned_hits), "bare_unsigned": unsigned_hits,
        "shift_site_count": len(shift_hits), "shift_sites": shift_hits,
        "policy": "These are mechanical review candidates, not diagnosed semantic mismatches."}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", required=True,
        help="new JSON receipt path under portable/tests/recovered/evidence/source-port-inventory-v1")
    args = parser.parse_args()
    target = Path(args.report)
    if not target.is_absolute():
        target = ROOT / target
    target = target.resolve()
    if EVIDENCE.resolve() not in target.parents:
        raise RuntimeError("--report must be inside source-port-inventory-v1")
    if target.exists():
        raise FileExistsError(f"refusing to overwrite source-route receipt: {target}")

    function_db = json.loads(FUNCTIONS.read_text(encoding="utf-8"))
    symbol_db = json.loads(SYMBOLS.read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))["modules"]
    provenance = json.loads(PROVENANCE.read_text(encoding="utf-8"))
    build_receipt = json.loads(BUILD_RECEIPT.read_text(encoding="utf-8"))
    if not build_receipt.get("sources_stable_during_build"):
        raise RuntimeError("captured production build receipt did not record stable sources")
    build_input_hashes = build_receipt.get("inputs", {})
    if not build_input_hashes:
        raise RuntimeError("captured production build receipt has no input pins")
    captured_input_checks = []
    for rel, expected in sorted(build_input_hashes.items()):
        path = canonical(rel)
        actual = sha(path) if path.is_file() else None
        captured_input_checks.append({"path": rel, "receipt_sha256": expected,
                                      "current_sha256": actual, "matches": actual == expected})
    stale_inputs = [row for row in captured_input_checks if not row["matches"]]
    if stale_inputs:
        raise RuntimeError(f"captured production build has {len(stale_inputs)} stale/missing input pins")
    command = build_receipt.get("command", [])
    compiled_sources = {Path(token).resolve() for token in command
                        if token.lower().endswith(".c") and Path(token).is_absolute()}
    compiled_source_hash_mismatches = []
    for path in sorted(compiled_sources):
        rel = path.relative_to(ROOT).as_posix()
        expected = build_input_hashes.get(rel)
        actual = sha(path) if path.is_file() else None
        if expected is None or actual != expected:
            compiled_source_hash_mismatches.append({"path": rel, "receipt": expected, "current": actual})
    if compiled_source_hash_mismatches:
        raise RuntimeError(f"captured production build has {len(compiled_source_hash_mismatches)} stale/missing source pins")
    if BUILD_EXE.is_file() and sha(BUILD_EXE) != build_receipt.get("executable_sha256"):
        raise RuntimeError("captured production build executable no longer matches its receipt")
    compiler_path = Path(command[0]).resolve() if command else None
    compiler_sha = sha(compiler_path) if compiler_path and compiler_path.is_file() else None
    if compiler_sha != build_receipt.get("compiler_sha256"):
        raise RuntimeError("captured production build compiler no longer matches its receipt")
    sdl_library_sha = sha(SDL_LIBRARY) if SDL_LIBRARY.is_file() else None
    if sdl_library_sha != build_receipt.get("sdl_library_sha256"):
        raise RuntimeError("captured production build SDL library no longer matches its receipt")
    current_rows = provenance["modules"]
    current_by_source = {row["source"]: row for row in current_rows}
    profile_names_by_module: dict[str, dict[str, list[dict]]] = defaultdict(lambda: defaultdict(list))
    profile_scaffold_by_module: dict[str, set[str]] = defaultdict(set)
    current_names: dict[str, set[str]] = {}
    current_scaffold: dict[str, set[str]] = {}
    current_adaptations: dict[str, dict] = {}
    for row in current_rows:
        current_names[row["source"]] = set(row.get("defined_functions", []))
        source_module = module_key_from_profile_row(row)
        for name in row.get("defined_functions", []):
            if source_module:
                profile_names_by_module[source_module][name].append(row)
        if source_module:
            profile_scaffold_by_module[source_module].update(
                row.get("scaffold_functions_excluded_from_semantics", []))
        current_scaffold[row["source"]] = set(row.get("scaffold_functions_excluded_from_semantics", []))
        current_adaptations[row["source"]] = {
            "source_semantics": row.get("source_semantics_adaptations", []),
            "source_type_views": row.get("source_type_view_adaptations", []),
            "platform_boundaries": row.get("platform_boundary_adaptations", []),
            "wrappers": row.get("entry_wrappers", []),
        }

    generated_source_paths = {canonical(row["generated"]) for row in current_rows}
    if len(current_rows) != 25:
        raise RuntimeError(f"expected exactly 25 current generated TUs, got {len(current_rows)}")

    by_address: dict[tuple[str, int, int], list[str]] = defaultdict(list)
    for name, row in symbol_db["code"].items():
        if {"unit", "seg", "off"} <= row.keys():
            by_address[(row["unit"], row["seg"], row["off"])].append(name)
    aliases: dict[str, set[str]] = defaultdict(set)
    for row in current_rows:
        for alias, canonical_name in row.get("layout_grounded_function_aliases_applied", {}).items():
            aliases[canonical_name].add(alias)

    portable_c = sorted((ROOT / "portable").rglob("*.c"))
    portable_c = [p for p in portable_c if "build" not in p.parts and "tests" not in p.parts]
    provider_defs = provider_definitions(portable_c)
    unintegrated = set()
    build_text = BUILD.read_text(encoding="utf-8")
    build_match = re.search(r"UNINTEGRATED_MODELS\s*=\s*\{(.*?)\n\}", build_text, re.S)
    if build_match:
        unintegrated = set(re.findall(r"\"(portable/[^\"]+\.c)\"", build_match.group(1)))
    compiled_source_rel = {p.relative_to(ROOT).as_posix() for p in compiled_sources}

    adapter_route: dict[str, dict] = {}
    for adapter in provenance.get("native_adapters", []):
        for name in adapter.get("functions", [adapter.get("function")]):
            if name:
                adapter_route[name] = {"adapter": adapter.get("adapter"),
                                       "binding": adapter.get("binding"),
                                       "historical_source": adapter.get("historical_source"),
                                       "limits": adapter.get("limits")}

    routes = []
    modules_seen = Counter()
    module_function_rows: dict[str, list[dict]] = defaultdict(list)
    source_files = set()
    for historical in function_db["functions"]:
        unit, seg, off = historical["unit"], historical["seg"], historical["off"]
        source_mod = manifest.get(module_key(unit, seg))
        names = sorted(by_address.get((unit, seg, off), []))
        source_path = source_mod.get("source") if source_mod else None
        if source_path:
            source_files.add(canonical(source_path))
        candidates = names[:]
        if source_mod:
            for claim in source_mod.get("claims", []):
                if claim.get("off") == off and claim.get("name") not in candidates:
                    candidates.append(claim["name"])
        original_module_key = module_key(unit, seg)
        names_for_module = profile_names_by_module[original_module_key]
        profile_name_candidates = {name for name in candidates if name in names_for_module}
        profile_name_candidates |= {canonical_name for canonical_name, old_names in aliases.items()
                                    if canonical_name in names_for_module and old_names.intersection(candidates)}
        profile_rows_for_function = {row["name"]: row for name in profile_name_candidates
                                     for row in names_for_module[name]}
        current_row = next(iter(profile_rows_for_function.values()), None)

        model = next((MODELS[name] | {"historical_name": name}
                      for name in candidates if name in MODELS), None)
        matched_provider = {name: provider_defs[name] for name in candidates if name in provider_defs}
        if historical.get("region", "").startswith("msc_runtime") or historical.get("extent") == "RUNTIME_MEMBER":
            route, rationale = "compiler_runtime_member", "historical row is an MSC runtime library member, not a game C/ASM TU"
        elif not source_mod:
            route, rationale = "missing_historical_source_route", "no canonical source module in the frozen manifest"
        elif profile_name_candidates:
            scaffold_names = profile_scaffold_by_module[original_module_key]
            if profile_name_candidates & scaffold_names:
                route, rationale = "generated_scaffolded_body", "function definition is present but profile excludes this body from semantics"
            else:
                route, rationale = "generated_source_body_candidate", "identifier joins to a definition in one of the 25 Next10 generated TUs; no equivalence claim"
        elif model:
            model_path = model["path"]
            model["linked_in_captured_build"] = model_path in compiled_source_rel
            if model_path not in compiled_source_rel:
                route, rationale = "unlinked_native_contract_model", model["basis"]
            else:
                route, rationale = "linked_native_model_provider", model["basis"] + "; provider TU occurs in the captured executable command, but this remains a model rather than the source body"
        elif any(path in compiled_source_rel for files in matched_provider.values() for path in files):
            route, rationale = "linked_exact_name_provider_candidate", "same-name portable C definition is in captured executable command; this inventory does not prove call/link binding"
        elif matched_provider:
            route, rationale = "unlinked_provider_draft_candidate", "same-name portable C definition exists outside captured executable source list"
        elif candidates and any(name in adapter_route for name in candidates):
            route, rationale = "explicit_native_adapter", "Next10 provenance declares a named adapter; source body is not used for this route"
        else:
            route, rationale = "missing_native_route", "no current generated body, explicit adapter, source-linked model, or exact-name provider candidate"

        row = {"function_key": func_key(unit, seg, off), "unit": unit,
            "seg": f"{seg:04X}", "off": f"{off:04X}", "size": historical["size"],
            "region": historical.get("region"), "extent": historical.get("extent"),
            "historical_symbol_candidates": names, "manifest_module": module_key(unit, seg) if source_mod else None,
            "source": source_path, "source_language": source_mod.get("lang") if source_mod else None,
            "source_module_claim_kind": next((c.get("kind") for c in source_mod.get("claims", [])
                                                if c.get("off") == off), None) if source_mod else None,
            "route": route, "route_basis": rationale,
            "generated_profile": current_row["name"] if current_row else None,
            "generated_profile_name_matches": sorted(profile_name_candidates),
            "source_name_join_ambiguous": len(names) > 1 and not profile_name_candidates,
            "model_route": model,
            "exact_name_provider_candidates": matched_provider,
            "exact_name_provider_linked_paths": sorted(path for files in matched_provider.values()
                for path in files if path in compiled_source_rel),
            "declared_adapter": next((adapter_route[n] for n in candidates if n in adapter_route), None),
        }
        routes.append(row)
        modules_seen[route] += 1
        if source_mod:
            module_function_rows[module_key(unit, seg)].append(row)

    # Build transparent provider/source-edge summaries for unselected C TUs.
    known_source_names: dict[str, tuple[str, str]] = {}
    for row in routes:
        for name in row["historical_symbol_candidates"]:
            known_source_names[name] = (row["manifest_module"] or "", row["route"])
        current_sources = set(current_by_source)
    module_summaries = []
    for key, mod in sorted(manifest.items()):
        path = mod.get("source", "")
        if not path or not path.endswith(".c"):
            continue
        source_path = canonical(path)
        if not source_path.is_file():
            continue
        text = source_path.read_text(encoding="utf-8", errors="replace")
        called = set(re.findall(r"\b([A-Za-z_]\w*)\s*\(", text))
        local_names = {r["historical_symbol_candidates"][0] for r in module_function_rows.get(key, [])
                       if r["historical_symbol_candidates"]}
        edges, available_edges = [], []
        for name in sorted(called & known_source_names.keys()):
            owner, route = known_source_names[name]
            if name in local_names or owner == key:
                continue
            edge = {"symbol": name, "target_module": owner, "target_route": route}
            if route in {"generated_source_body_candidate", "generated_scaffolded_body",
                         "linked_exact_name_provider_candidate", "linked_native_model_provider",
                         "unlinked_native_contract_model", "explicit_native_adapter"}:
                available_edges.append(edge)
            else:
                edges.append(edge)
        rows = module_function_rows.get(key, [])
        profiled_count = sum(r["route"] in {"generated_source_body_candidate",
            "generated_scaffolded_body"} for r in rows)
        module_summaries.append({"module": key, "source": path, "source_sha256": sha(source_path),
            "source_language": mod.get("lang"), "historical_function_count": len(rows),
            "claim_count": len(mod.get("claims", [])),
            "scaffold_entries": mod.get("scaffold", []),
            "profiled_function_count": profiled_count,
            "remaining_historical_function_count": len(rows) - profiled_count,
            "in_current_profile": profiled_count > 0,
            "fully_routed_by_current_profile": bool(rows) and profiled_count == len(rows),
            "available_source_edges": available_edges,
            "available_source_edge_count": len(available_edges),
            "unsupported_source_edges": edges,
            "unsupported_edge_count": len(edges),
            "function_route_counts": dict(Counter(r["route"] for r in rows)),
        })

    candidate_c = [m for m in module_summaries if m["remaining_historical_function_count"] > 0]
    # Name dependency-ready source-preserving module batches separately from
    # the whole-TU backlog ranking. Readiness is bounded to explicit edge
    # facts and does not claim that a body or provider is equivalent.
    summary_by_module = {row["module"]: row for row in module_summaries}
    immediate_keys = ["root:00BA", "root:00F8", "root:0250", "root:0798"]
    immediate_reasons = {
        "root:00BA": "Small application-hook TU: retain all five bodies and their order, then resolve listed host/window callback imports.",
        "root:00F8": "Scheduler/event-host TU: preserve all 40 source members and order, retain MapToYard's existing route, then resolve listed imports.",
        "root:0250": "Resource/cache TU: preserve all 53 source members including three scaffolded bodies; resolve listed memory/resource/graphics edges without semantic substitution.",
        "root:0798": "Full controls TU: recover all source bodies, including ProcModeEvent and ProcCasteEvent, to replace separate handwritten model routes; current profile covers eight of 18 members.",
    }
    immediate = []
    for key in immediate_keys:
        row = summary_by_module.get(key)
        if not row:
            raise RuntimeError(f"required source batch is absent from frozen manifest: {key}")
        immediate.append({"module": key, "source": row["source"],
            "historical_function_count": row["historical_function_count"],
            "manifest_claim_count": row["claim_count"],
            "scaffold_entry_count": len(row["scaffold_entries"]),
            "profiled_function_count": row["profiled_function_count"],
            "remaining_historical_function_count": row["remaining_historical_function_count"],
            "available_source_edges": row["available_source_edges"],
            "unsupported_edges": row["unsupported_source_edges"],
            "selection_basis": immediate_reasons[key]})
    # Backlog candidates are sorted by remaining member count; their blockers
    # remain explicit and this ranking does not imply dependency readiness.
    backlog = sorted(candidate_c,
        key=lambda m: (m["remaining_historical_function_count"],
                       m["available_source_edge_count"],
                       -m["unsupported_edge_count"], m["module"]),
        reverse=True)[:3]

    current_source_paths = sorted({canonical(row["source"]) for row in current_rows if row.get("source")
                                   and canonical(row["source"]).is_file()})
    current_generated_paths = sorted(p for p in generated_source_paths if p.is_file())
    risks = {"historical_selected_sources": source_risks(sorted(source_files)),
             "next10_generated_sources": source_risks(current_generated_paths)}
    source_files_hashes = {p.relative_to(ROOT).as_posix(): sha(p) for p in sorted(source_files)
                           if p.is_file()}
    current_source_hashes = {p.relative_to(ROOT).as_posix(): sha(p) for p in current_source_paths
                             if p.is_file()}
    generated_hashes = {p.relative_to(ROOT).as_posix(): sha(p) for p in current_generated_paths}
    portable_source_hashes = {path.relative_to(ROOT).as_posix(): sha(path) for path in portable_c
                              if path.is_file()}
    inputs = {FUNCTIONS: sha(FUNCTIONS), SYMBOLS: sha(SYMBOLS), MANIFEST: sha(MANIFEST),
        GENERATOR: sha(GENERATOR), PROVENANCE: sha(PROVENANCE), BUILD: sha(BUILD),
        BUILD_RECEIPT: sha(BUILD_RECEIPT), BUILD_EXE: sha(BUILD_EXE)}
    inputs.update({canonical(path): digest for path, digest in source_files_hashes.items()})
    inputs.update({canonical(path): digest for path, digest in current_source_hashes.items()})
    inputs.update({canonical(path): digest for path, digest in generated_hashes.items()})
    inputs.update({canonical(path): digest for path, digest in portable_source_hashes.items()})
    inputs[Path(__file__).resolve()] = sha(Path(__file__).resolve())
    input_hashes = {p.relative_to(ROOT).as_posix(): digest for p, digest in sorted(inputs.items())}

    report = {
        "schema": "simant-source-port-inventory-v2", "status": "PASS_INVENTORY_ONLY",
        "claim_limit": "Static route inventory only. It does not compile sources, establish link reachability, or claim semantic/pixel equivalence.",
        "counts": {"historical_function_rows": len(routes),
            "historical_game_source_routes": sum(r["source"] is not None for r in routes),
            "historical_source_routes_by_language": dict(Counter(
                r["source_language"] for r in routes if r["source"] is not None)),
            "compiler_runtime_rows": modules_seen["compiler_runtime_member"],
            "current_generated_translation_units": len(current_rows),
            "current_generated_definition_names": sum(len(x) for x in current_names.values()),
            "source_joined_current_generated_functions": modules_seen["generated_source_body_candidate"],
            "generated_scaffolded_function_routes": modules_seen["generated_scaffolded_body"],
            "explicit_adapter_routes": modules_seen["explicit_native_adapter"],
            "unlinked_native_contract_models": modules_seen["unlinked_native_contract_model"],
            "exact_name_native_provider_candidates": modules_seen["linked_exact_name_provider_candidate"] +
                modules_seen["unlinked_provider_draft_candidate"],
            "captured_build_linked_exact_name_provider_candidates": modules_seen["linked_exact_name_provider_candidate"],
            "missing_native_routes": modules_seen["missing_native_route"],
            "missing_historical_source_routes": modules_seen["missing_historical_source_route"],
            "ambiguous_name_joins": sum(bool(r["source_name_join_ambiguous"]) for r in routes)},
        "route_counts": dict(modules_seen),
        "profile": {"provenance": "build/workers/recovered_source_next10/generated/provenance.json",
            "provenance_sha256": sha(PROVENANCE), "all_25_modules": [
                {"name": row["name"], "source": row["source"],
                 "source_sha256": row["source_sha256"], "generated_sha256": row["generated_sha256"],
                 "defined_function_count": len(row.get("defined_functions", [])),
                 "scaffold_excluded_functions": row.get("scaffold_functions_excluded_from_semantics", []),
                 "source_semantics_adaptations": row.get("source_semantics_adaptations", []),
                 "source_type_view_adaptations": row.get("source_type_view_adaptations", []),
                 "platform_boundary_adaptations": row.get("platform_boundary_adaptations", []),
                 "entry_wrappers": row.get("entry_wrappers", []),
                 "unresolved_callable_dependencies": row.get("unresolved_callable_dependencies", [])}
                for row in current_rows],
            "mechanical_generator_transform_anchors": {
                "unsigned_int_to_uint16_t": True, "plain_int_to_int16_t": True,
                "bare_unsigned_rewritten": False,
                "source": "portable/tools/recover_source.py: transform()"}},
        "captured_production_build": {"receipt": BUILD_RECEIPT.relative_to(ROOT).as_posix(),
            "receipt_sha256": sha(BUILD_RECEIPT), "executable": BUILD_EXE.relative_to(ROOT).as_posix(),
            "executable_sha256": sha(BUILD_EXE), "input_count": len(build_input_hashes),
            "all_input_hashes_checked": True,
            "all_input_hash_mismatch_count": len(stale_inputs),
            "all_input_hashes": captured_input_checks,
            "translation_unit_source_count_from_exact_command": len(compiled_sources),
            "source_hash_mismatch_count": len(compiled_source_hash_mismatches),
            "source_hash_mismatches": compiled_source_hash_mismatches,
            "compiled_source_paths": sorted(compiled_source_rel),
            "compiler_path": str(compiler_path), "compiler_sha256": compiler_sha,
            "sdl_library_path": SDL_LIBRARY.relative_to(ROOT).as_posix(),
            "sdl_library_sha256": sdl_library_sha,
            "unlinked_portable_c_files": sorted(p.relative_to(ROOT).as_posix() for p in portable_c
                if p.relative_to(ROOT).as_posix() not in compiled_source_rel and
                   p.relative_to(ROOT).as_posix() not in unintegrated),
            "control_event_route": {"native_provider": "portable/game/recovered/control_adapter.c calls sim_control_process_event in portable/ui_model/windows/control_events.c",
                "route_kind": "linked_native_model_provider",
                "source_body_status": "ProcModeEvent and ProcCasteEvent are not mechanically converted by Next10; the handwritten model is distinct from those source bodies",
                "finite_evidence": "portable/tests/recovered/evidence/controls-next4/setup_reuse_differential.py"}},
        "route_policy": {"generated_source_body_candidate": "Exact address/name join to a definition listed in a Next10 generated TU. This is not a semantic claim; scaffold exclusions and recorded adaptations remain visible.",
            "generated_scaffolded_body": "Generated TU lists the name but provenance excludes the body from semantic consideration.",
            "explicit_native_adapter": "Provenance names an adapter for a source function; do not imply the source body is executed.",
            "linked_exact_name_provider_candidate": "Same-name portable C definition is one of the exact source files in the captured executable command; this is a route candidate, not proof of a particular call binding.",
            "unlinked_provider_draft_candidate": "Same-name portable C definition exists outside the captured executable source list.",
            "linked_native_model_provider": "Documented handwritten model route occurs in the captured build command; it is not a mechanically converted source body.",
            "unlinked_native_contract_model": "One of three documented source-to-model correspondences exists; model is excluded by portable/build.py.",
            "missing_native_route": "No exact generated body, named adapter, explicitly mapped model, or same-name portable definition was found.",
            "compiler_runtime_member": "MSC runtime/library row, separated from game C/ASM translation routes."},
        "documented_model_routes": [{"function": name, **value,
            "listed_in_build_unintegrated_models_set": value["path"] in unintegrated,
            "linked_in_captured_build": value["path"] in compiled_source_rel}
            for name, value in MODELS.items()],
        "immediate_mechanical_batches": immediate,
        "whole_tu_backlog_candidates": [{"rank": index + 1, "module": row["module"],
            "source": row["source"], "historical_function_count": row["historical_function_count"],
            "remaining_historical_function_count": row["remaining_historical_function_count"],
            "unsupported_edge_count": row["unsupported_edge_count"],
            "available_source_edges": row["available_source_edges"],
            "unsupported_edges": row["unsupported_source_edges"],
            "selection_basis": "backlog only: ranked by remaining whole-TU member count and existing routed edges; unmatched source edges are blockers and this ranking does not imply dependency readiness"}
            for index, row in enumerate(backlog)],
        "module_routes": module_summaries,
        "functions": routes,
        "width_and_promotion_review": risks,
        "inputs": input_hashes,
    }
    with target.open("x", encoding="utf-8", newline="") as stream:
        stream.write(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"status": report["status"], "functions": len(routes),
        "routes": report["route_counts"], "report": target.relative_to(ROOT).as_posix()}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
