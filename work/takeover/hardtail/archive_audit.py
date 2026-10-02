#!/usr/bin/env python3
"""Read-only index of archived hardtail experiment reports and generator sources.

This script deliberately does not compile, run searches, or write canonical files.
It follows exact function identifiers in JSON fields / claims dictionaries and Python
string constants; it does not infer associations from a function-name prefix.
"""
from __future__ import annotations

import ast
import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
CATALOG = ROOT / "work/takeover/hardtail/catalog.json"
OUT = ROOT / "build/workers/hardtail_catalog_audit"

REPORT_ROOTS = [
    ROOT / "work/takeover/residue-controls",
    ROOT / "work/takeover/blockers",
    ROOT / "work/takeover/fleet-lifetimes",
    ROOT / "work/takeover/phase-next",
    ROOT / "work/takeover/pointer-forms",
    ROOT / "work/takeover/context-next",
    ROOT / "work/takeover/full-search",
]
PRIOR_DRAFT_ROOTS = [
    ROOT / "build/workers/hardtail_root/fresh",
    ROOT / "build/workers/hardtail_root/refreshed",
    ROOT / "build/workers/takeover",
]
SKIP_PARTS = {"cache", ".git", "__pycache__"}
FUNC_KEYS = {
    "function", "func", "function_name", "target_function", "target_func",
    "target_name", "target_symbol", "claim_name", "symbol_name",
}


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return str(path)


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def walk_files(roots: list[Path], suffixes: set[str]) -> list[Path]:
    found: list[Path] = []
    for base in roots:
        if not base.exists():
            continue
        for p in base.rglob("*"):
            if not p.is_file() or p.suffix.lower() not in suffixes:
                continue
            if any(part.lower() in SKIP_PARTS for part in p.relative_to(base).parts):
                continue
            found.append(p)
    return sorted(set(found), key=lambda p: rel(p).lower())


def exact_path_matches(path_text: str, targets: set[str]) -> set[str]:
    # Identifiers are bounded by non-identifier characters; this is an exact-name
    # reference, unlike a prefix or substring association.
    return {name for name in targets if re.search(rf"(?<![A-Za-z0-9_]){re.escape(name)}(?![A-Za-z0-9_])", path_text)}


def false_claim(value: Any) -> bool:
    if value is False:
        return True
    if isinstance(value, dict):
        if value.get("exact") is False or value.get("all_exact") is False:
            return True
        if value.get("target_exact") is False:
            return True
    return False


def json_evidence(data: Any, targets: set[str], path: str = "$", out: dict[str, list[str]] | None = None) -> dict[str, list[str]]:
    out = out if out is not None else defaultdict(list)
    if isinstance(data, dict):
        for k, v in data.items():
            kl = str(k).lower()
            if kl in FUNC_KEYS and isinstance(v, str) and v in targets:
                out[v].append(f"{path}.{k}={v}")
            if kl == "claims" and isinstance(v, dict):
                for name, claim in v.items():
                    if name in targets and false_claim(claim):
                        out[name].append(f"{path}.claims.{name}=inexact")
            # Exact function names encoded as report keys are useful only when the
            # corresponding value is a claim/result object with an inexact verdict.
            for name, value in data.items():
                if name in targets and false_claim(value):
                    out[name].append(f"{path}.{name}=inexact")
            json_evidence(v, targets, f"{path}.{k}", out)
    elif isinstance(data, list):
        for i, v in enumerate(data):
            json_evidence(v, targets, f"{path}[{i}]", out)
    return out


def python_evidence(path: Path, targets: set[str]) -> dict[str, list[str]]:
    try:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
    except (OSError, UnicodeError, SyntaxError):
        return {}
    found: dict[str, list[str]] = defaultdict(list)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and node.value in targets:
            found[node.value].append(f"Python string constant line {node.lineno}")
    # A script's own basename is an association only on exact identifier equality.
    found.update({n: found.get(n, []) for n in exact_path_matches(path.name, targets)})
    return found


def iter_rows(data: Any):
    """Yield likely variant records while preserving their container path."""
    if isinstance(data, list):
        for i, row in enumerate(data):
            if isinstance(row, dict):
                yield f"$[{i}]", row
    elif isinstance(data, dict):
        if isinstance(data.get("variants"), list):
            for i, row in enumerate(data["variants"]):
                if isinstance(row, dict):
                    yield f"$.variants[{i}]", row
        elif isinstance(data.get("results"), list):
            for i, row in enumerate(data["results"]):
                if isinstance(row, dict):
                    yield f"$.results[{i}]", row


def claim_for(row: dict[str, Any], function: str) -> Any:
    for holder in (row, row.get("result"), row.get("report")):
        if not isinstance(holder, dict):
            continue
        claims = holder.get("claims")
        if isinstance(claims, dict) and function in claims:
            return claims[function]
    # Context-next uses the target field for the root function and peer_losses for
    # other claims. It is safe here because the exact function association came
    # independently from the enclosing function field.
    if row.get("target") is not None:
        target = row["target"]
        if isinstance(target, dict):
            return target
    return None


def exact_for(row: dict[str, Any], function: str) -> bool | None:
    claim = claim_for(row, function)
    if claim is False:
        return False
    if claim is True:
        return True
    if isinstance(claim, dict) and isinstance(claim.get("exact"), bool):
        return claim["exact"]
    if isinstance(claim, dict) and isinstance(claim.get("all_exact"), bool):
        return claim["all_exact"]
    if isinstance(row.get("exact"), bool) and (row.get("function") == function or row.get("target") is not None):
        return row["exact"]
    if isinstance(row.get("all_exact"), bool) and (row.get("function") == function or row.get("target") is not None):
        return row["all_exact"]
    return None


def compile_for(row: dict[str, Any], function: str) -> bool | None:
    claim = claim_for(row, function)
    for holder in (claim, row.get("result"), row):
        if isinstance(holder, dict) and isinstance(holder.get("compile_ok"), bool):
            return holder["compile_ok"]
    return None


def reasons_for(row: dict[str, Any], function: str) -> list[str]:
    claim = claim_for(row, function)
    if isinstance(claim, dict) and isinstance(claim.get("reasons"), list):
        return [str(x) for x in claim["reasons"]]
    result = row.get("result")
    if isinstance(result, dict):
        claims = result.get("claims")
        if isinstance(claims, dict) and isinstance(claims.get(function), dict):
            return [str(x) for x in claims[function].get("reasons", [])]
    return [str(x) for x in row.get("reasons", [])] if isinstance(row.get("reasons"), list) else []


def candidate_length(row: dict[str, Any], function: str) -> Any:
    claim = claim_for(row, function)
    if isinstance(claim, dict):
        for k in ("length", "candidate_bytes", "size"):
            if k in claim:
                return claim[k]
    for k in ("length", "candidate_bytes"):
        if k in row:
            return row[k]
    reasons = reasons_for(row, function)
    for reason in reasons:
        m = re.match(r"length (\d+) != target", reason)
        if m:
            return int(m.group(1))
    return None


def score_for(row: dict[str, Any]) -> list[Any] | None:
    score = row.get("score")
    if isinstance(score, list):
        return score
    result = row.get("result")
    if isinstance(result, dict) and isinstance(result.get("score"), list):
        return result["score"]
    return None


def target_row(data: Any, function: str) -> list[dict[str, Any]]:
    result = []
    for where, row in iter_rows(data):
        exact = exact_for(row, function)
        if exact is None and not (isinstance(data, dict) and data.get("function") == function):
            continue
        result.append({
            "where": where,
            "name": row.get("name"),
            "parameters": row.get("meta", row.get("parameters", row.get("why"))),
            "compile_ok": compile_for(row, function),
            "exact": exact,
            "score": score_for(row),
            "length": candidate_length(row, function),
            "all_exact": row.get("all_exact", row.get("exact")),
            "module_exact": (row.get("result", {}).get("exact") if isinstance(row.get("result"), dict) else row.get("module_exact")),
            "reasons": reasons_for(row, function),
            "source": row.get("file", row.get("source")),
        })
    return result


def compact_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    compiled = [r for r in rows if r.get("compile_ok") is True]
    target_exact = [r for r in rows if r.get("exact") is True]
    whole_exact = [r for r in rows if r.get("all_exact") is True or r.get("module_exact") is True]
    rejected = [r for r in rows if r.get("exact") is False]
    rejected_scored = [r for r in rejected if isinstance(r.get("score"), list)]
    closest = min(rejected_scored, key=lambda r: tuple(r["score"]), default=None)
    best_target = min((r for r in target_exact if isinstance(r.get("score"), list)), key=lambda r: tuple(r["score"]), default=None)
    params: list[Any] = []
    seen: set[str] = set()
    for row in rows:
        p = row.get("parameters")
        if p is None:
            continue
        val = json.dumps(p, sort_keys=True, ensure_ascii=False)
        if val not in seen:
            seen.add(val)
            params.append(p)
    keep = ("name", "parameters", "score", "length", "reasons", "source")
    return {
        "variant_rows": len(rows),
        "compiled": len(compiled),
        "target_exact": len(target_exact),
        "whole_module_or_all_claims_exact": len(whole_exact),
        "parameter_values_seen": len(params),
        "parameter_samples": params[:8],
        "closest_rejected_control": ({k: closest.get(k) for k in keep} if closest else None),
        "best_target_exact": ({k: best_target.get(k) for k in keep} if best_target else None),
    }


def normalize_stem(value: str) -> str:
    return re.sub(r"[-_]", "", Path(value).stem).lower()


def sibling_generators(report: Path, scripts: list[Path]) -> list[Path]:
    key = normalize_stem(report.name)
    direct = [p for p in scripts if p.parent == report.parent and normalize_stem(p.name) == key]
    return direct


def generators_for_report(report: Path, scripts: list[Path]) -> list[Path]:
    """Find a sibling generator by exact stem or explicit output-name literal."""
    found = set(sibling_generators(report, scripts))
    key = normalize_stem(report.name)
    for script in scripts:
        if script.parent != report.parent:
            continue
        try:
            tree = ast.parse(script.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, SyntaxError):
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str) and normalize_stem(node.value) == key:
                found.add(script)
                break
    # Some shared generators take the target and series name on the command line;
    # their run log is the exact report-stem mate and records the script path.
    log = report.with_suffix(".log")
    if log.exists():
        try:
            log_text = log.read_text(encoding="utf-8", errors="replace")
        except OSError:
            log_text = ""
        for ref in re.findall(r"[A-Za-z0-9_.\\/-]+\.py", log_text):
            p = Path(ref.replace("\\", "/"))
            for candidate in (p, ROOT / p, report.parent / p.name):
                try:
                    resolved = candidate.resolve()
                except OSError:
                    continue
                if resolved.is_file() and resolved.suffix.lower() == ".py":
                    found.add(resolved)
    return sorted(found, key=lambda p: rel(p).lower())


def series_key(artifact: str) -> str | None:
    p = Path(artifact)
    if p.name.lower() in {"index.json", "sources.json"}:
        return None
    if p.name.lower() == "results.json":
        parent = p.parent.name
        if re.fullmatch(r"round\d+-results", parent, re.I):
            return p.parent.parent.name + "/" + parent
        return parent
    return p.stem


def slug(value: str) -> str:
    return re.sub(r"[-_]", "", value).lower()


KNOWN_CAVEATS = {
    "win_PrintStyleTextInRect": [
        {"source": "work/takeover/residue-controls/README.md", "note": "The old full-search best caches a character before the space-skipping loop and does not refresh it as the index advances; it can loop forever on a space. The later loop-cache controls update the character each iteration."},
    ],
    "f_171C_0CF4": [
        {"source": "work/takeover/context-next/README.md", "note": "The retained wide moved-flag and low-word return-view forms are unclaimed type hypotheses; the six-byte residue remains and original types are not established."},
    ],
    "f_2815_0165": [
        {"source": "work/takeover/pointer-forms/README.md", "note": "Ten nested volume-assignment forms were discarded because they did not establish a C89 sequence point between writes; only comma-sequenced replacements remain as controls."},
    ],
}


def referenced_source_files(data: Any, candidates: dict[str, Path]) -> list[str]:
    found: set[str] = set()
    def visit(x: Any):
        if isinstance(x, dict):
            for k, v in x.items():
                if isinstance(v, str) and (k.lower() in {"file", "source", "path", "best_source", "best_path", "draft"} or v.lower().endswith((".c", ".asm"))):
                    p = Path(v)
                    choices = [p, ROOT / p]
                    for candidate in choices:
                        try:
                            key = str(candidate.resolve()).lower()
                        except OSError:
                            continue
                        if key in candidates:
                            found.add(rel(candidates[key]))
                visit(v)
        elif isinstance(x, list):
            for v in x:
                visit(v)
    visit(data)
    return sorted(found)


def main() -> None:
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    records = catalog["records"]
    functions = {r["function"] for r in records}
    json_paths = walk_files(REPORT_ROOTS, {".json"})
    py_paths = walk_files(REPORT_ROOTS, {".py"})
    all_json_paths = sorted(set(json_paths + walk_files(PRIOR_DRAFT_ROOTS, {".json"})), key=lambda p: rel(p).lower())
    all_py_paths = sorted(set(py_paths + walk_files(PRIOR_DRAFT_ROOTS, {".py"})), key=lambda p: rel(p).lower())
    source_roots = REPORT_ROOTS + PRIOR_DRAFT_ROOTS
    source_paths = walk_files(source_roots, {".c", ".asm"})
    source_map = {str(p.resolve()).lower(): p for p in source_paths}

    json_index = []
    associations: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for path in all_json_paths:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            continue
        evidence = json_evidence(data, functions)
        if not evidence:
            continue
        digest = sha(path)
        generators = generators_for_report(path, all_py_paths)
        for function, why in evidence.items():
            rows = target_row(data, function)
            # A target report row is report data only when it exposes actual
            # candidate verdicts. Claim-map-only artifacts remain evidence links.
            report_entry = {
                "artifact": rel(path),
                "series": series_key(rel(path)),
                "sha256": digest,
                "evidence": sorted(set(why)),
                "generator_candidates": [rel(x) for x in generators],
                "target_summary": compact_rows(rows),
                "source_reference_count": len(referenced_source_files(data, source_map)),
                "referenced_source_sample": referenced_source_files(data, source_map)[:12],
            }
            associations[function].append(report_entry)
            for generator in generators:
                associations[function].append({
                    "artifact": rel(generator), "kind": "report_generator", "sha256": sha(generator),
                    "evidence": [f"linked from {rel(path)} via exact target claim and sibling/log source"],
                    "generator_candidates": [],
                    "referenced_sources": [],
                })
        json_index.append({"artifact": rel(path), "sha256": digest, "functions": sorted(evidence)})

    for path in all_py_paths:
        evidence = python_evidence(path, functions)
        for function, why in evidence.items():
            associations[function].append({
                "artifact": rel(path), "kind": "generator_or_helper", "sha256": sha(path),
                "evidence": sorted(set(why)), "generator_candidates": [],
                "referenced_sources": [],
            })

    # Attribute each direct archived report by exact target and report path, then
    # compare ownership with the catalog's manually maintained series index.
    owners_by_series: dict[str, set[str]] = defaultdict(set)
    for fn, entries in associations.items():
        for entry in entries:
            if "kind" in entry:
                continue
            if not entry["artifact"].startswith("work/takeover/") or entry["artifact"].startswith(("work/takeover/full-search/", "work/takeover/fleet-lifetimes/")):
                continue
            key = entry.get("series")
            if key:
                owners_by_series[slug(key.split("/")[0])].add(fn)

    catalog_series = {}
    audit_records = []
    for record in records:
        fn = record["function"]
        entries = associations.get(fn, [])
        reports = [x for x in entries if "target_summary" in x]
        scripts = [x for x in entries if x.get("kind") == "generator_or_helper"]
        residue_current = {x.get("series") for x in record.get("superseded_series_index", record.get("residue_series_index", []))}
        found_series = {
            x.get("series") for x in reports
            if x.get("artifact", "").startswith("work/takeover/")
            and not x.get("artifact", "").startswith(("work/takeover/full-search/", "work/takeover/fleet-lifetimes/"))
            and x.get("series")
        }
        not_indexed = sorted((x for x in found_series if slug(str(x).split("/")[0]) not in {slug(str(y)) for y in residue_current}), key=str.lower)
        stale = sorted((x for x in residue_current if slug(str(x)) not in {slug(str(y).split("/")[0]) for y in found_series}), key=str.lower)
        wrong_owner = []
        for series in stale:
            owners = sorted(owners_by_series.get(slug(str(series)), set()))
            if owners and owners != [fn]:
                wrong_owner.append({"series": series, "actually_associated_functions": owners})
        fleet_reports = [x for x in reports if x.get("artifact", "").startswith("work/takeover/fleet-lifetimes/")]
        fleet_catalog = record.get("fleet_series_index", [])
        fleet_report_paths = {x["artifact"] for x in fleet_reports}
        fleet_coverage = []
        for item in fleet_catalog:
            report_path = item.get("report", "")
            suffix = "work/takeover/fleet-lifetimes/" + report_path
            fleet_coverage.append({
                "catalog_name": item.get("name"),
                "report": report_path,
                "archived_report_found": any(p.endswith(suffix) for p in fleet_report_paths),
                "catalog_rows": item.get("rows"),
                "compiled": item.get("compiled"),
                "target_exact": item.get("target_exact"),
            })
        catalog_series[fn] = sorted(str(x) for x in residue_current if x)
        audit_records.append({
            "function": fn,
            "module": record.get("module"),
            "target_bytes": record.get("target_bytes"),
            "catalog_best_source": record.get("best_source"),
            "catalog_best_candidate_bytes": record.get("best_candidate_bytes"),
            "fresh_diagnostic": record.get("fresh_main_diagnostic"),
            "catalog_residue_series": catalog_series[fn],
            "exact_target_archived_series": sorted(found_series, key=str.lower),
            "catalog_archived_alternatives": [{
                "series": x.get("series"), "source": x.get("source"),
                "candidate_bytes": x.get("candidate_bytes"), "score": x.get("score"),
                "target_reasons": x.get("target_reasons"),
                "historical_status": x.get("historical_status"),
            } for x in record.get("archived_alternatives", [])],
            "archived_report_artifacts": reports,
            "script_associations": scripts,
            "archived_series_missing_from_catalog": not_indexed,
            "catalog_series_without_exact_target_report": stale,
            "catalog_series_associated_to_other_target": wrong_owner,
            "fleet_series_coverage": fleet_coverage,
            "known_semantic_caveats": KNOWN_CAVEATS.get(fn, []),
        })

    payload = {
        "schema": "hardtail-archive-audit-v1",
        "catalog": rel(CATALOG),
        "catalog_records": len(records),
        "association_policy": "Exact function identifiers only: explicit function/target fields, inexact per-function entries under claims, or exact literals in generator code. Prefix-only association is prohibited.",
        "interpretation": "closest_rejected_control is the lowest reported score among target-inexact rows, not a proof of semantic inequivalence. Variant parameters and source-level rewrites remain hypotheses unless semantics and the strict byte/fixup/relocation gate are established.",
        "report_roots": [rel(p) for p in REPORT_ROOTS],
        "prior_draft_roots": [rel(p) for p in PRIOR_DRAFT_ROOTS],
        "json_artifacts_indexed": len(json_index),
        "records": audit_records,
        "json_artifacts": json_index,
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "exhaustion-index.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_markdown(audit_records)
    print(f"catalog functions: {len(records)}; JSON artifacts associated: {len(json_index)}")
    print(f"index: {rel(OUT / 'exhaustion-index.json')}")
    for r in audit_records:
        print(f"{r['function']}: report artifacts={len(r['archived_report_artifacts'])}, scripts={len(r['script_associations'])}, archived series missing from catalog={len(r['archived_series_missing_from_catalog'])}, catalog series without exact target report={len(r['catalog_series_without_exact_target_report'])}")


def write_markdown(records: list[dict[str, Any]]) -> None:
    lines = [
        "# Hardtail archive coverage audit",
        "",
        "Read-only cross-index of the 29 catalog functions against archived JSON results and generator scripts. The index follows exact function identifiers in report fields, inexact per-function `claims` entries, and Python string constants. It does not associate artifacts by filename prefix. No compiler, search, promotion, or canonical-source operation was run.",
        "",
        "| Function | Target bytes | Catalog residue series | Exact-target archived series | Missing from catalog | Catalog series with no exact-target report |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for r in records:
        lines.append("| {function} | {target_bytes} | {catalog_count} | {actual_count} | {missing_count} | {stale_count} |".format(
            function=r["function"], target_bytes=r.get("target_bytes"),
            catalog_count=len(r["catalog_residue_series"]), actual_count=len(r["exact_target_archived_series"]),
            missing_count=len(r["archived_series_missing_from_catalog"]), stale_count=len(r["catalog_series_without_exact_target_report"])))
    lines.extend(["", "The JSON index records each report path and SHA-256, a generator path when linked, variant/compile/exact counts, up to eight parameter examples, the closest rejected row with its reasons, and source paths referenced by the report. The closest rejection is the best-scored failure, not proof of semantic inequivalence. Candidate similarity is diagnostic; an inexact row is never treated as accepted.", ""])
    for r in records:
        lines.extend([f"## {r['function']} ({r.get('module')})", "", f"Target size: {r.get('target_bytes')} bytes. Catalog seed: `{r.get('catalog_best_candidate_bytes')}` bytes from `{r.get('catalog_best_source')}`.", ""])
        if r["archived_series_missing_from_catalog"]:
            lines.append("Archived exact-target dimensions absent from the catalog index: " + ", ".join(f"`{x}`" for x in r["archived_series_missing_from_catalog"]) + ".")
        if r["catalog_series_associated_to_other_target"]:
            lines.append("Catalog ownership mismatch: " + "; ".join(f"`{x['series']}` is associated with {', '.join(x['actually_associated_functions'])}" for x in r["catalog_series_associated_to_other_target"]) + ".")
        if r["catalog_series_without_exact_target_report"] and not r["catalog_series_associated_to_other_target"]:
            lines.append("Catalog-listed series without a matching exact-target JSON report: " + ", ".join(f"`{x}`" for x in r["catalog_series_without_exact_target_report"]) + ".")
        if r["catalog_archived_alternatives"]:
            alt = r["catalog_archived_alternatives"]
            lines.append("Prior best draft(s): " + "; ".join(f"`{x['source']}` ({x.get('candidate_bytes')} bytes, score {x.get('score')}, {x.get('historical_status')})" for x in alt) + ".")
        if r["fleet_series_coverage"]:
            good = sum(bool(x["archived_report_found"]) for x in r["fleet_series_coverage"])
            lines.append(f"Fleet rounds: {good}/{len(r['fleet_series_coverage'])} catalog report paths exist and are associated with this target.")
        if r["known_semantic_caveats"]:
            lines.append("Known semantic caveat(s): " + "; ".join(f"{x['note']} (see `{x['source']}`)" for x in r["known_semantic_caveats"]))
        lines.append("")
        # One concise row per distinct source report; work archives take precedence
        # over duplicate build output reports but all copies stay in the JSON index.
        chosen: dict[str, dict[str, Any]] = {}
        for a in r["archived_report_artifacts"]:
            key = a.get("series") or a["artifact"]
            old = chosen.get(key)
            if old is None or (a["artifact"].startswith("work/") and not old["artifact"].startswith("work/")):
                chosen[key] = a
        if chosen:
            lines.append("| Dimension/report | Generator | Counts | Closest rejected control |")
            lines.append("|---|---|---|---|")
            for key, a in sorted(chosen.items()):
                summary = a["target_summary"]
                generator = ", ".join(f"`{x}`" for x in a["generator_candidates"]) or "not linked"
                counts = f"{summary['variant_rows']} rows / {summary['compiled']} compiled / {summary['target_exact']} target-exact / {summary['whole_module_or_all_claims_exact']} whole-exact"
                close = summary.get("closest_rejected_control")
                if close:
                    close_text = f"`{close.get('name')}` {close.get('length')} B; score {close.get('score')}; " + "; ".join(close.get("reasons") or [])
                    if close.get("parameters") is not None:
                        close_text += f"; params `{json.dumps(close['parameters'], ensure_ascii=False)}`"
                else:
                    close_text = "no scored rejected row"
                lines.append(f"| `{key}` ([report]({a['artifact']})) | {generator} | {counts} | {close_text} |")
            lines.append("")
        if not chosen:
            lines.extend(["No archived per-variant report row is associated with this function under the exact-identifier policy.", ""])
        lines.append("Generator/helper paths associated by exact identifier: " + (", ".join(f"`{x['artifact']}`" for x in r["script_associations"]) or "none") + ".")
        lines.append("")

    # The source review for LessonDone is grounded in its archived report and row data.
    lesson = next((r for r in records if r["function"] == "LessonDone"), None)
    if lesson:
        lines.extend([
            "## LessonDone seed review",
            "",
            "The archived fleet report identifies a 56-word switch table at `+0x1e..+0x8d`, with code resuming at `+0x8e`; strict verification still compares those words. The canonical 739-byte seed retains 9 relocations versus the 723-byte target and fails the strict claim. The old full-search 715-byte draft is 8 bytes short and loses one relocation entry. The case-group variants with the observed anchors are semantically reviewable because they group cases whose source bodies are identical, but their best row is 710 bytes and has 8 versus 9 relocation entries.",
            "",
            "The strongest current merge seed by body-aware score among near-length, relocation-count-preserving, semantics-preserving rows is `build/workers/takeover/lesson-boolean-returns/v7.c`: metadata `[\"simple\", \"break\", true]`, 727 bytes, score `[1,31,531,4]` in `lesson-body-aware-controls.json`; its recorded failure is 4 bytes over target with a relocation-set mismatch despite both sets containing 9 entries. In this function the rewritten `if (condition) return 1;` predicates are comparisons, the merged 8/43/46/50 bodies are identical, and case 54's `return 0` to `break` reaches the existing final `return 0`. The table remains subject to strict verification; this score masks it only for ranking. This is a seed only, not acceptance evidence.",
            "",
        ])
    (OUT / "audit-report.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
