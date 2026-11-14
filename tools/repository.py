"""Check current architecture, explicit native exceptions and disposable output hygiene."""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ABI = ROOT / "portable" / "canonical_native_abi"
ALLOWED_BUILD_ROOTS = {"current", "deps", "workers", "scratch", "locks", "reference"}
REQUIRED_ENTRY_POINTS = {
    "dos/build.py", "portable/build.py", "tools/validate.py",
    "tools/context.py", "tools/search.py", "tools/promote.py",
}
CLOSED_STATUSES = {"RESOLVED", "CLOSED", "RETIRED", "COMPLETE"}
CLOSURE_CLASSES = {"SOURCE_REQUIRED", "SUPPORTED_DOMAIN", "LAYOUT_SENSITIVE", "UNATTRIBUTED_STATE"}


def _issue(code: str, path: str, detail: str) -> dict[str, str]:
    return {"code": code, "path": path, "detail": detail}


def _repo_path(value: Any, issues: list[dict[str, str]], label: str) -> Path | None:
    if not isinstance(value, str) or not value.strip():
        issues.append(_issue("invalid_path", label, "Expected a non-empty project-relative path."))
        return None
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        issues.append(_issue("path_escape", label, "Path must remain project-relative."))
        return None
    result = (ROOT / path).resolve()
    try:
        result.relative_to(ROOT.resolve())
    except ValueError:
        issues.append(_issue("path_escape", label, "Resolved path leaves the project."))
        return None
    return result


def _load_json(path: Path, issues: list[dict[str, str]], code: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        issues.append(_issue(code, path.relative_to(ROOT).as_posix(), str(exc)))
        return {}
    if not isinstance(value, dict):
        issues.append(_issue(code, path.relative_to(ROOT).as_posix(), "Expected a JSON object."))
        return {}
    return value


def _check_program(program: dict[str, Any], issues: list[dict[str, str]]) -> set[str]:
    modules = program.get("modules")
    if program.get("schema") != "simant-canonical-program-v1" or not isinstance(modules, list):
        issues.append(_issue("canonical_inventory", "src/program.json", "Unsupported or incomplete canonical program inventory."))
        return set()
    keys: set[str] = set()
    sources: set[str] = set()
    for row in modules:
        if not isinstance(row, dict):
            issues.append(_issue("canonical_module", "src/program.json", "Module row is not an object."))
            continue
        key, source = row.get("key"), row.get("source")
        if not isinstance(key, str) or not key or key in keys:
            issues.append(_issue("canonical_module_key", "src/program.json", f"Missing or duplicate module key: {key!r}."))
        else:
            keys.add(key)
        if not isinstance(source, str) or not source or source in sources:
            issues.append(_issue("canonical_module_source", "src/program.json", f"Missing or duplicate source: {source!r}."))
            continue
        sources.add(source)
        file = _repo_path(source, issues, "src/program.json:" + str(key))
        if file is None:
            continue
        if not file.is_file():
            issues.append(_issue("canonical_source_missing", source, "Inventory source does not exist."))
        elif row.get("source_sha256") and hashlib.sha256(file.read_bytes()).hexdigest() != row["source_sha256"]:
            issues.append(_issue("canonical_source_hash", source, "Source differs from src/program.json pin."))
    actual = {
        p.relative_to(ROOT).as_posix()
        for p in (ROOT / "src").rglob("*")
        if p.is_file() and p.suffix.lower() in {".c", ".asm"}
    }
    if actual != sources:
        issues.append(_issue(
            "canonical_source_parity", "src/",
            f"Inventory/source mismatch; unlisted={sorted(actual - sources)[:8]}, missing={sorted(sources - actual)[:8]}.",
        ))
    dos = program.get("dos")
    if not isinstance(dos, dict):
        issues.append(_issue("dos_blocker_inventory", "src/program.json", "Missing DOS blocker inventory."))
        return set()
    active_ids: set[str] = set()
    for field in ("semantic_gates", "unresolved_data"):
        rows = dos.get(field)
        if not isinstance(rows, list):
            issues.append(_issue("dos_blocker_inventory", "src/program.json:dos." + field, "Expected a list."))
            continue
        seen: set[str] = set()
        for row in rows:
            if not isinstance(row, dict) or not isinstance(row.get("id"), str) or not row["id"].strip():
                issues.append(_issue("dos_blocker_id", "src/program.json:dos." + field, "Every blocker needs a stable non-empty id."))
                continue
            blocker_id = row["id"]
            if blocker_id in seen:
                issues.append(_issue("duplicate_blocker_id", "src/program.json:dos." + field, blocker_id))
            seen.add(blocker_id)
            status = str(row.get("status", "UNRESOLVED" if field == "unresolved_data" else "")).upper()
            if field == "semantic_gates" and not status:
                issues.append(_issue("dos_gate_status", "src/program.json:dos.semantic_gates", blocker_id + " has no status."))
            if status not in CLOSED_STATUSES:
                active_ids.add(blocker_id)
            if field == "unresolved_data" and (not isinstance(row.get("bytes"), int) or row["bytes"] <= 0):
                issues.append(_issue("dos_data_debt", "src/program.json:dos.unresolved_data", blocker_id + " must retain a positive byte count."))
    resolved = dos.get('resolved_domain_contracts', [])
    if resolved:
        domain = dos.get('supported_execution_domain', {})
        if not domain.get('id') or not domain.get('premises') or domain.get('launch_arguments') != []:
            issues.append(_issue('supported_execution_domain', 'src/program.json', 'Resolved domain contracts require the reviewed default-launch scope.'))
        seen = set()
        for row in resolved:
            identity = row.get('id')
            proof = _repo_path(row.get('resolution_evidence', ''), issues, 'resolved domain proof')
            if (not identity or identity in seen or identity in active_ids or
                    row.get('status') != 'RESOLVED_SUPPORTED_DOMAIN' or
                    row.get('domain') != domain.get('id') or not row.get('resolution') or
                    proof is None or not proof.is_file()):
                issues.append(_issue('resolved_domain_contract', str(identity), 'Missing, duplicate or conflicting reviewed domain resolution.'))
            seen.add(identity)
    return active_ids


def _module_name(value: Any) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return None
    normalized = value.replace("\\", "/").removesuffix(".py")
    prefix = "portable/canonical_native_abi/"
    if normalized.startswith(prefix):
        normalized = normalized[len(prefix):]
    return Path(normalized).stem


def _check_closure_graph(program, evidence, platform, issues):
    """Check the root-question view without granting any acceptance authority.

    Edges mean prerequisite evidence, not that closing a parent closes a leaf.
    Inventory membership and the existing DOS preflight remain authoritative.
    """
    graph = program.get('dos', {}).get('closure_graph', {})
    roots = graph.get('roots', [])
    if graph.get('schema') != 'simant-closure-graph-v1' or not roots:
        issues.append(_issue('closure_graph', 'src/program.json', 'Missing root-question graph.'))
        return
    inventories = {
        'imports': {r['name'] for r in evidence.get('imports', [])},
        'gates': {r['id'] for r in program['dos']['semantic_gates']},
        'data': {r['id'] for r in program['dos']['unresolved_data']},
        'native': {r['id'] for r in platform.get('preview_limitations', [])},
    }
    ids = [r.get('id') for r in roots]
    if any(not isinstance(x, str) or not re.fullmatch('[a-z][a-z0-9_-]*', x) for x in ids) or len(set(ids)) != len(ids):
        issues.append(_issue('closure_graph_ids', 'src/program.json', 'Invalid/duplicate root IDs.'))
        return
    by_id = {r['id']: r for r in roots}
    covered = {kind: set() for kind in inventories}
    for row in roots:
        for field in ('question', 'next_experiment', 'scope'):
            if not isinstance(row.get(field), str) or not row[field].strip():
                issues.append(_issue('closure_graph_question', row['id'], 'Missing ' + field))
        for dependency in row.get('depends_on', []):
            if dependency not in by_id:
                issues.append(_issue('closure_graph_edge', row['id'], str(dependency)))
        for kind, members in row.get('members', {}).items():
            if kind not in inventories or not isinstance(members, list):
                issues.append(_issue('closure_graph_members', row['id'], str(kind)))
                continue
            unknown = set(members) - inventories[kind]
            if unknown:
                issues.append(_issue('closure_graph_stale_leaf', row['id'], str(sorted(unknown))))
            covered[kind].update(members)
    visiting, visited = set(), set()
    def visit(key):
        if key in visiting:
            issues.append(_issue('closure_graph_cycle', key, 'Evidence prerequisites must form a DAG.'))
            return
        if key in visited or key not in by_id:
            return
        visiting.add(key)
        for parent in by_id[key].get('depends_on', []):
            visit(parent)
        visiting.remove(key)
        visited.add(key)
    for key in by_id:
        visit(key)
    for kind, members in inventories.items():
        if members - covered[kind]:
            issues.append(_issue('closure_graph_unmapped', kind, str(sorted(members - covered[kind]))))
    for rows in (evidence.get('imports', []), program['dos']['semantic_gates'], program['dos']['unresolved_data']):
        for row in rows:
            if row.get('closure_class') not in CLOSURE_CLASSES or not row.get('closure_basis'):
                issues.append(_issue('closure_class', row.get('id', row.get('name', '?')), 'Missing reviewed class/basis.'))


def _imported_abi_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.name.replace("\\", "/")
                prefix = "canonical_native_abi."
                if name.startswith(prefix):
                    found.add(name[len(prefix):].split(".", 1)[0])
        elif isinstance(node, ast.ImportFrom) and node.level and path.parent == ABI:
            if node.module:
                found.add(node.module.split(".", 1)[0])
            else:
                found.update(alias.name for alias in node.names if (ABI / (alias.name + ".py")).is_file())
        elif isinstance(node, ast.ImportFrom) and node.module:
            module = node.module.replace("\\", "/")
            prefix = "canonical_native_abi."
            if module.startswith(prefix):
                found.add(module[len(prefix):].split(".", 1)[0])
            elif module == "canonical_native_abi":
                for alias in node.names:
                    if (ABI / (alias.name + ".py")).is_file():
                        found.add(alias.name)
    return {name for name in found if (ABI / (name + ".py")).is_file()}


def _check_lowering(spec: dict[str, Any], live_ids: set[str], issues: list[dict[str, str]]) -> None:
    files = {p.stem: p for p in ABI.glob("*.py") if p.name != "__init__.py"}
    rows = spec.get("lowering")
    if not isinstance(rows, list):
        issues.append(_issue("lowering_registry", "layout/repository.json", "Expected lowering list."))
        return
    registered: set[str] = set()
    for row in rows:
        if not isinstance(row, dict):
            issues.append(_issue("lowering_row", "layout/repository.json:lowering", "Entry is not an object."))
            continue
        name = _module_name(row.get("module"))
        if not name:
            issues.append(_issue("lowering_module", "layout/repository.json:lowering", "Every entry needs a module."))
            continue
        if name in registered:
            issues.append(_issue("lowering_duplicate", "layout/repository.json:lowering", name))
        registered.add(name)
        if name not in files:
            issues.append(_issue("lowering_module_missing", "layout/repository.json:lowering", name + " is not an ABI Python module."))
        if row.get("classification") not in {
            'GENERIC_LOWERING', 'TRUE_PLATFORM_BOUNDARY', 'TEMPORARY_EXCEPTION',
            'SHOULD_BE_ABSORBED_INTO_CANONICAL_SOURCE',
        }:
            issues.append(_issue("lowering_classification", name, "Classification is required."))
        if not isinstance(row.get("reason"), str) or not row["reason"].strip():
            issues.append(_issue("lowering_reason", name, "Reason is required."))
        if not isinstance(row.get("deletion_condition"), str) or not row["deletion_condition"].strip():
            issues.append(_issue("lowering_deletion_condition", name, "Deletion condition is required."))
        classification = str(row.get("classification", "")).lower().replace("-", "_").replace(" ", "_")
        blocker_ids = row.get("blocker_ids", [])
        if not isinstance(blocker_ids, list) or any(not isinstance(x, str) for x in blocker_ids):
            issues.append(_issue("lowering_blocker_ids", name, "blocker_ids must be a list of IDs."))
            blocker_ids = []
        if "temporary" in classification or "exception" in classification:
            if not blocker_ids:
                issues.append(_issue("exception_without_blocker", name, "Temporary exception needs live blocker IDs."))
            for blocker_id in blocker_ids:
                if blocker_id not in live_ids:
                    issues.append(_issue("exception_blocker_not_live", name, blocker_id + " is absent, closed, or unknown."))
        if any(token in classification for token in ("game_algorithm", "ordinary_state", "game_state")):
            issues.append(_issue("game_logic_in_lowering", name, "Ordinary game algorithms/state belong in canonical source."))
    missing = sorted(set(files) - registered)
    if missing:
        issues.append(_issue("abi_module_unregistered", "portable/canonical_native_abi/", ", ".join(missing)))
    try:
        closure: set[str] = set()
        pending = [ROOT / "portable/build.py"]
        seen_paths: set[Path] = set()
        while pending:
            path = pending.pop()
            if path in seen_paths or not path.is_file():
                continue
            seen_paths.add(path)
            imports = _imported_abi_modules(path)
            for name in imports - closure:
                closure.add(name)
                pending.append(files[name])
        unused = sorted(set(files) - closure)
        if unused:
            issues.append(_issue("abi_module_unreachable", "portable/canonical_native_abi/", ", ".join(unused)))
        not_registered = sorted(closure - registered)
        if not_registered:
            issues.append(_issue("build_abi_unregistered", "portable/build.py", ", ".join(not_registered)))
    except (OSError, SyntaxError) as exc:
        issues.append(_issue("abi_import_graph", "portable/build.py", str(exc)))


def _check_platform(platform: dict[str, Any], live_ids: set[str], issues: list[dict[str, str]]) -> set[str]:
    for field in ("services", "headers"):
        rows = platform.get(field)
        if (not isinstance(rows, list) or
                any(not isinstance(value, str) for value in rows) or
                len(rows) != len(set(rows))):
            issues.append(_issue("platform_file_list", "portable/platform.json:" + field, "Expected a duplicate-free path list."))
            continue
        for value in rows:
            path = _repo_path(value, issues, "portable/platform.json:" + field)
            if path is not None and not path.is_file():
                issues.append(_issue("platform_file_missing", value, "Registered platform file does not exist."))
    limitations = platform.get("preview_limitations")
    if not isinstance(limitations, list):
        issues.append(_issue("preview_blocker_inventory", "portable/platform.json", "Expected preview_limitations list."))
        return set()
    ids: set[str] = set()
    active: set[str] = set()
    for row in limitations:
        if not isinstance(row, dict):
            issues.append(_issue("preview_blocker_row", "portable/platform.json:preview_limitations", "Entry is not an object."))
            continue
        blocker_id = row.get("id")
        if not isinstance(blocker_id, str) or not blocker_id.strip():
            issues.append(_issue("preview_blocker_id", "portable/platform.json:preview_limitations", "Every open preview limitation needs a stable id."))
        elif blocker_id in ids:
            issues.append(_issue("preview_blocker_duplicate", "portable/platform.json:preview_limitations", blocker_id))
        else:
            ids.add(blocker_id)
        if str(row.get("status", "")).upper() != "OPEN":
            issues.append(_issue("preview_blocker_status", "portable/platform.json:preview_limitations", str(blocker_id) + " must be OPEN until resolved."))
        elif isinstance(blocker_id, str) and blocker_id.strip():
            active.add(blocker_id)
    return active


def _check_spec(spec: dict[str, Any], issues: list[dict[str, str]]) -> None:
    retired = spec.get("retired_paths")
    if not isinstance(retired, list):
        issues.append(_issue("retired_paths", "layout/repository.json", "Expected retired_paths list."))
    else:
        for value in retired:
            item = value.get("path") if isinstance(value, dict) else value
            path = _repo_path(item, issues, "layout/repository.json:retired_paths")
            if path is not None and path.exists():
                issues.append(_issue("retired_path_present", str(item), "Retired path must be absent from active tree."))
    entries = spec.get("entry_points")
    if not isinstance(entries, list):
        issues.append(_issue("entry_point_registry", "layout/repository.json", "Expected entry_points list."))
        entries = []
    paths: set[str] = set()
    for row in entries:
        if not isinstance(row, dict):
            issues.append(_issue("entry_point_row", "layout/repository.json:entry_points", "Entry is not an object."))
            continue
        value, role = row.get("path"), row.get("role")
        path = _repo_path(value, issues, "layout/repository.json:entry_points")
        if path is not None and not path.is_file():
            issues.append(_issue("entry_point_missing", str(value), "Registered entry point does not exist."))
        if isinstance(value, str):
            paths.add(value.replace("\\", "/"))
        if not isinstance(role, str) or not role.strip():
            issues.append(_issue("entry_point_role", str(value), "Entry point needs a role."))
    for required in sorted(REQUIRED_ENTRY_POINTS - paths):
        issues.append(_issue("entry_point_unregistered", required, "Supported workflow entry point is absent from registry."))


def _check_build_root(issues: list[dict[str, str]]) -> None:
    build = ROOT / "build"
    if not build.exists():
        return
    unexpected = sorted(p.name for p in build.iterdir() if p.name not in ALLOWED_BUILD_ROOTS)
    if unexpected:
        issues.append(_issue("build_root_layout", "build/", "Unexpected active roots: " + ", ".join(unexpected)))


def _check_behavior_attribution(spec, platform, issues):
    """Validate ledger bookkeeping/evidence requirements, never infer a verdict."""
    label='layout/repository.json:behavior_attribution_ledger'
    path=_repo_path(spec.get('behavior_attribution_ledger'),issues,label)
    if path is None: return
    ledger=_load_json(path,issues,'behavior_attribution_ledger')
    if ledger.get('schema')!='simant-behavior-attribution-v1' or not isinstance(ledger.get('items'),list):
        issues.append(_issue('behavior_attribution_schema',label,'Expected v1 ledger with items.'));return
    oracle=_load_json(ROOT/'layout/oracle.lock.json',issues,'behavior_attribution_oracle')
    original_sha=oracle.get('inputs',{}).get('SIMANT.EXE',{}).get('sha256')
    categories={'ORIGINAL','RECONSTRUCTION_INTRODUCED','PORT_INTRODUCED','PORT_DEVIATION_DOCUMENTED','UNATTRIBUTED'}
    counts={};ids=set()
    for row in ledger['items']:
        if not isinstance(row,dict):
            issues.append(_issue('behavior_attribution_row',label,'Expected object row.'));continue
        item=row.get('id');where=path.relative_to(ROOT).as_posix()+':'+str(item)
        if not isinstance(item,str) or not item or item in ids:
            issues.append(_issue('behavior_attribution_id',where,'Expected unique nonempty id.'))
        else: ids.add(item)
        classification=row.get('classification')
        if not isinstance(classification,str) or classification not in categories:
            issues.append(_issue('behavior_attribution_classification',where,str(classification)))
        else: counts[classification]=counts.get(classification,0)+1
        if row.get('status') not in {'fixed','preserved','open'} or not row.get('description') or not row.get('scope'):
            issues.append(_issue('behavior_attribution_scope',where,'Status, description and scoped claim required.'))
        evidence=row.get('evidence',{})
        if not isinstance(evidence,dict):
            issues.append(_issue('behavior_attribution_evidence',where,'Expected evidence object.'));continue
        original=evidence.get('original_exe',{});canonical=evidence.get('canonical_dos',{})
        if classification=='ORIGINAL' and (not isinstance(original,dict) or
                original.get('path')!='assets/SIMANT.EXE' or original.get('sha256')!=original_sha or
                not original.get('observation') or original.get('method') not in
                {'STATIC_INSTRUCTION_PROOF','RUNTIME_OBSERVATION'} or not evidence.get('paths') or
                not isinstance(canonical,dict) or not canonical.get('observation') or
                canonical.get('relation_to_original') not in {'STATIC_CONTRACT_EQUAL','OBSERVED_EQUAL'}):
            issues.append(_issue('behavior_attribution_original_evidence',where,
                                 'ORIGINAL needs pinned original-EXE proof and explicit canonical equality evidence.'))
        if classification=='UNATTRIBUTED' and not row.get('decisive_experiment'):
            issues.append(_issue('behavior_attribution_experiment',where,'Unattributed rows need a decisive experiment.'))
        if classification=='PORT_DEVIATION_DOCUMENTED' and (not row.get('exception_reason') or not row.get('observability')):
            issues.append(_issue('behavior_attribution_exception',where,'Document why the native exception exists and its observability.'))
    if ledger.get('counts')!=counts:
        issues.append(_issue('behavior_attribution_counts',label,'Counts differ from classified rows.'))
    for limitation in platform.get('preview_limitations',[]):
        if limitation['id'] not in ids:
            issues.append(_issue('behavior_attribution_missing_exception',label,limitation['id']))


def _check_production_literals(issues: list[dict[str, str]]) -> None:
    paths = [ROOT / "dos/build.py", ROOT / "portable/build.py"]
    paths.extend(p for p in ABI.glob("*.py") if p.name != "__init__.py")
    paths.extend(p for p in (ROOT / "portable/whole_program").rglob("*.py") if "tests" not in p.parts)
    forbidden = re.compile(r"(?i)(?:to_delete[/\\]|build[/\\](?:workers|scratch)(?:[/\\]|$)|tools[/\\]research[/\\])")
    output_line = re.compile(r"(?i)(?:\b(?:out|output|work|scratch)\s*=|\bmkdir\b|write_text|write_bytes|--out|copyfile\s*\()")
    for path in paths:
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (OSError, SyntaxError) as exc:
            issues.append(_issue("production_source_parse", path.relative_to(ROOT).as_posix(), str(exc)))
            continue
        lines = path.read_text(encoding="utf-8").splitlines()
        copy_inputs = set()
        for call in ast.walk(tree):
            if not isinstance(call, ast.Call):
                continue
            name = call.func.attr if isinstance(call.func, ast.Attribute) else getattr(call.func, 'id', '')
            if name != 'copyfile':
                continue
            inputs = call.args[:1] + [keyword.value for keyword in call.keywords if keyword.arg == 'src']
            copy_inputs.update(node for argument in inputs for node in ast.walk(argument))
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str) and forbidden.search(node.value):
                line = lines[node.lineno - 1] if node.lineno <= len(lines) else ""
                if node in copy_inputs or not output_line.search(line):
                    issues.append(_issue("retired_or_scratch_input", path.relative_to(ROOT).as_posix() + ":" + str(node.lineno), node.value[:160]))


def _check_file_roles(spec, program, platform, issues):
    """Classify every retained non-document file without traversing ignored trees.

    Source and service reachability comes from their actual inventories. Tool,
    test and proof families have explicit audited roles; this is a static check,
    not a claim that every runtime path has executed.
    """
    names = subprocess.check_output(
        ['git', '-c', f'safe.directory={ROOT.as_posix()}', 'ls-files', '-co',
         '--exclude-standard'], cwd=ROOT, text=True).splitlines()
    exact = {row['source'] for row in program.get('modules', [])}
    exact.update(platform.get('services', []) + platform.get('headers', []))
    exact.update(row['path'] for row in spec.get('entry_points', []))
    exact.update({'src/program.json', 'portable/platform.json',
                  'portable/whole_program/application.c',
                  'portable/canonical_native_abi/__init__.py',
                  '.gitignore', '.gitattributes', 'docs/progress.json'})
    exact.update('portable/canonical_native_abi/' + row['module'] + '.py'
                 for row in spec.get('lowering', []))
    roots = spec.get('role_roots', {})
    counts = {}
    for name in sorted(set(names)):
        if not (ROOT / name).is_file() or Path(name).suffix == '.md':
            continue
        role = 'inventory/workflow' if name in exact else next(
            (reason for prefix, reason in roots.items() if name.startswith(prefix)), None)
        if role is None:
            issues.append(_issue('file_without_active_role', name,
                                 'Register an actual consumer/proof role or retire the file.'))
        else:
            counts[role] = counts.get(role, 0) + 1
    return counts


def audit(spec_path: Path) -> dict[str, Any]:
    issues: list[dict[str, str]] = []
    spec = _load_json(spec_path, issues, "repository_spec")
    program = _load_json(ROOT / "src/program.json", issues, "canonical_inventory")
    platform = _load_json(ROOT / "portable/platform.json", issues, "platform_inventory")
    evidence = _load_json(ROOT / 'evidence/canonical/blockers.json', issues, 'blocker_projection')
    # evidence/canonical/blockers.json is the projection of the earlier supported-domain
    # proofs. It is kept as evidence for docs/data-adjacency.md and no longer has to mirror
    # the inventory, whose identifiers change as names are recovered.
    for row in program.get('dos', {}).get('historical_layout_debt', []):
        if row.get('status') != 'HISTORICAL_LAYOUT_DEBT' or not row.get('caveat') or \
                not (ROOT / str(row.get('decision_evidence', ''))).is_file():
            issues.append(_issue('historical_layout_debt', 'src/program.json', str(row.get('id'))))
    debt = program.get('dos', {}).get('unresolved_data', [])
    if [(r.get('id'),r.get('bytes')) for r in evidence.get('data_debt',[])] != [(r.get('id'),r.get('bytes')) for r in debt]:
        issues.append(_issue('data_projection_drift','evidence/canonical/blockers.json','Functional data membership/bytes must match the canonical inventory.'))
    _check_spec(spec, issues)
    live_ids = _check_program(program, issues)
    live_ids.update(_check_platform(platform, live_ids, issues))
    _check_closure_graph(program, evidence, platform, issues)
    _check_lowering(spec, live_ids, issues)
    _check_build_root(issues)
    _check_behavior_attribution(spec, platform, issues)
    _check_production_literals(issues)
    roles = _check_file_roles(spec, program, platform, issues)
    return {
        "schema": "simant-repository-guard-report-v1",
        "passed": not issues,
        "issues": issues,
        "summary": {"issue_count": len(issues), "live_blockers": len(live_ids),
                    "retained_file_roles": roles},
    }


def write_status():
    """Render what is left to a full match from the current ledgers; never edit claims."""
    import re
    program = json.loads((ROOT / 'src/program.json').read_text())
    manifest = json.loads((ROOT / 'layout/manifest.json').read_text())
    progress = json.loads((ROOT / 'docs/progress.json').read_text())
    symbols = json.loads((ROOT / 'layout/symbols.json').read_text())
    functions = json.loads((ROOT / 'layout/functions.json').read_text())['functions']
    platform = json.loads((ROOT / 'portable/platform.json').read_text())
    size_at = {(f['unit'], f['seg'], f['off']): f['size'] for f in functions}

    def cell(value):
        return str(value).replace('|', '\\|').replace('\n', ' ')

    def num(value):
        return f'{value:,}'

    # 1. functions that are not exact
    inexact = []
    for row in program['semantics']:
        at = symbols['code'].get(row['function'], {})
        inexact.append((row['module'], row['function'],
                        size_at.get((at.get('unit'), at.get('seg'), at.get('off')), 0)))
    inexact.sort()
    # 2. claims by proof quality
    claims = [(key, c) for key, m in manifest['modules'].items() for c in m['claims']
              if c.get('kind') != 'DATA_IN_CODE']
    steered = sorted((key, c['name'], c['size'], c.get('steered', '')) for key, c in claims
                     if c.get('provenance') == 'EXACT_STEERED')
    order_pending = sorted((key, c['name']) for key, c in claims
                           if c.get('reloc_order') == 'WITHIN_GROUP_PENDING')
    code_modules = {key: m for key, m in manifest['modules'].items() if m['claims']}
    partial = sorted(key for key, m in code_modules.items() if not m.get('extent'))
    game_functions = progress['known_game_functions']
    exact_functions = sum(1 for _, c in claims)
    # 3. data we defined ourselves
    own = [m for m in program['modules'] if m['key'].startswith('source-owned:')]
    own_objects = sum(len((m.get('storage_contract') or {}).get('communals', [])) +
                      len((m.get('storage_contract') or {}).get('publics', [])) for m in own)
    own_bytes = sum(c.get('length', 0) for m in own
                    for c in (m.get('storage_contract') or {}).get('communals', []))
    residual = program['dos'].get('historical_layout_debt', [])
    # 4. names
    placeholder_code = re.compile(r'^(f|o\d\d)_[0-9A-F]{4}_[0-9A-F]{4}$')
    placeholder_data = re.compile(r'^(g|s|fd|d)_[0-9A-F]{4}(_[0-9A-F]{4})?$')
    named = {'C': [0, 0], 'ASM': [0, 0]}
    for _, c in claims:
        named[c['kind']][bool(placeholder_code.match(c['name']))] += 1
    data_rows = [n for n, r in symbols['data'].items() if not r.get('alias_of')]
    data_named = sum(1 for n in data_rows if not placeholder_data.match(n))
    decisions = json.loads((ROOT / 'evidence/cross_version/decisions.json').read_text())['pairs']
    confirmed = sum(1 for v in decisions.values() if v.get('confidence') == 'CONFIRMED')
    # A confirmed pair is pending only while the DOS object at its address still has an
    # address-based identifier.  Keys are UNIT:SEG:OFF; data pairs use the data segment.
    primary = {}
    for name, rec in symbols['code'].items():
        if not rec.get('alias_of'):
            primary[(rec.get('unit'), rec.get('seg'), rec.get('off'))] = (name, placeholder_code)
    for name, rec in symbols['data'].items():
        if not rec.get('alias_of'):
            primary.setdefault(('root', rec.get('seg'), rec.get('off')), (name, placeholder_data))

    def pair_pending(key):
        unit, seg, off = key.split(':')
        hit = primary.get((unit, int(seg, 16), int(off, 16)))
        return hit is None or bool(hit[1].match(hit[0]))

    pending_names = sum(1 for k, v in decisions.items() if v.get('confidence') == 'CONFIRMED' and v.get('win16')
                        and pair_pending(k))

    adjacency = ROOT / 'docs/data-adjacency.md'
    adjacency_entries = sum(1 for line in adjacency.read_text(encoding='utf-8').splitlines()
                            if line.startswith('### ')) if adjacency.exists() else 0
    lines = [
        '# What is left to a full match', '',
        'Generated by `python tools/repository.py --write-status` from `src/program.json`,',
        '`layout/manifest.json`, `layout/symbols.json` and `docs/progress.json` (written by',
        '`python tools/validate.py`). It is a view of those ledgers, not another inventory, and is',
        'never edited by hand. The completion checklist it follows is in [AGENTS.md](../AGENTS.md).', '',
        f'Oracle: the original `SIMANT.EXE`, SHA-256 `{progress["oracle_sha256"]}`.',
        f'Last gate result: **{progress["validation"]}** ({progress["generated"]}).', '',
        '## Checklist', '',
        '| Item | State | Open |', '| --- | --- | --- |',
        f'| 1. Code exact | {num(exact_functions)} of {num(game_functions)} game functions | '
        f'{len(inexact)} functions, {num(sum(b for _, _, b in inexact))} bytes; '
        f'{len(partial)} of {len(code_modules)} code modules are not yet complete translation units |',
        f'| 2. No unexplained steering | {len(steered)} exact functions depend on a steering construct | '
        f'{num(sum(b for _, _, b, _ in steered))} bytes |',
        f'| 3. Data: one owner, type, size | {num(progress["data_bytes_accepted"])} initialised bytes exact | '
        f'{len(own)} storage units of our own ({own_objects} objects, {num(own_bytes)} bytes) without a '
        f'proven owning file; uninitialised far data sizes unverified for '
        f'{num(progress["far_bss_sizes_unverified_bytes"])} of {num(progress["far_bss_zero_fill_bytes"])} bytes; '
        f'{num(progress["data_bytes_opaque_unmarked"])} exact bytes with no known meaning; '
        f'{num(progress["unresolved_data_bytes"])} bytes unresolved |',
        f'| 4. Layout assumptions explained | {adjacency_entries} dependencies on neighbouring data, residue or '
        'undeclared results are catalogued in [data-adjacency.md](data-adjacency.md) | none is yet '
        f'confirmed by a reproduced layout; {sum(r["bytes"] for r in residual)} unattributed bytes in '
        f'{len(residual)} ranges |',
        '| 5. Layout reproduced | not reproduced: the working DOS build orders data its own way | '
        f'relocation order inside a group unproven for {len(order_pending)} functions |',
        '| 6. Whole executable | not built | the linker release is not in hand (bracketed to RTLink/Plus 5.00 or 4.15, see [toolchain](toolchain-fingerprint.md)); its '
        f'{num(progress["rtlink_manager_bytes_unaccepted"])}-byte overlay manager is not reproduced |',
        f'| 7. Names and comments | functions: {named["C"][0]} C and {named["ASM"][0]} assembly named; '
        f'data: {data_named} named | {named["C"][1]} C and {named["ASM"][1]} assembly functions and '
        f'{len(data_rows) - data_named} data objects keep address-based identifiers; '
        f'{pending_names} confirmed Windows names not applied yet |',
        '| 8. Reproducibility | `python tools/validate.py` re-proves every claim from the current source '
        'and prints separate verdicts for code, data, layout and whole executable | no image is built, so '
        'the layout and whole-executable verdicts have nothing to compare yet |', '',
        '## What each number proves', '',
        '* **Exact** means the pinned compiler or assembler built the whole module from the current',
        '  source and the function or data bytes, fixups and relocations equal the original. It says',
        '  nothing about where the linker would place the module.',
        '* **Behaviour-reviewed** functions were compared with the original instructions by review and',
        '  by differential execution over finite cases. That is a test, not proof, and they count as open.',
        '* The working DOS build (`dos/build.py --link`) contains no original executable bytes, but its',
        '  data layout is ours. Replays matching the original are regression checks only.',
        f'* Not rebuilt from source: {progress["historical_runtime_members_accepted"]} members of the pinned',
        f'  Microsoft C 6.00 runtime libraries ({num(progress["historical_runtime_bytes_accepted"])} code bytes,',
        f'  {num(progress["historical_runtime_data_bytes_accepted"])} data bytes), which the original also linked',
        '  from those libraries, and the linker\'s overlay manager.', '',
        '## Functions that are not exact', '',
        '| Module | Function | Bytes |', '| --- | --- | ---: |',
    ]
    lines += [f'| `{module}` | `{name}` | {size} |' for module, name, size in inexact]
    lines += ['', '## Exact only with a steering construct', '',
              'These match byte for byte but contain something that has no other reason to exist.',
              'They stay here until a natural spelling replaces it.', '',
              '| Module | Function | Bytes | Construct |', '| --- | --- | ---: | --- |']
    lines += [f'| `{module}` | `{name}` | {size} | {cell(why)} |' for module, name, size, why in steered]
    lines += ['', '## Code modules that are not complete translation units', '',
              'Their accepted functions are exact, but the module as a whole is not yet shown to be one',
              'original source file from first byte to last.', '',
              ', '.join('`' + key + '`' for key in partial) or 'None.', '',
              '## Data we defined ourselves', '',
              f'{len(own)} storage units hold {own_objects} objects whose owning source file is not',
              'recovered. They exist so the working DOS build links. Their sizes are lower bounds from',
              'use, not original sizes.', '',
              '| Unit | Objects | Bytes |', '| --- | ---: | ---: |']
    for m in sorted(own, key=lambda m: m['key']):
        contract = m.get('storage_contract') or {}
        communals = contract.get('communals', [])
        lines.append(f'| `{m["key"].split(":", 1)[1]}` | {len(communals) + len(contract.get("publics", []))} | '
                     f'{sum(c.get("length", 0) for c in communals)} |')
    lines += ['', '## Bytes nobody owns', '',
              '| Range | Bytes | What is known |', '| --- | ---: | --- |']
    lines += [f'| `{row["id"]}` | {row["bytes"]} | [{cell(row["caveat"])}](../{row["decision_evidence"]}) |'
              for row in residual]
    lines += ['', '## Relocation order still unproven', '',
              ', '.join(f'`{name}`' for _, name in order_pending) or 'None.', '',
              '## Upper layers', '',
              'The SDL3 port and the native presentation are not maintained while this layer is being',
              f'completed and may be stale. The port records {len(platform["preview_limitations"])} known',
              'differences from DOS behaviour in `portable/platform.json`.', '']
    (ROOT / 'docs/status.md').write_text('\n'.join(lines), encoding='utf-8', newline='\n')


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", type=Path, default=ROOT / "layout/repository.json")
    parser.add_argument("--json", type=Path, help="write the report to a disposable output path")
    parser.add_argument('--write-status', action='store_true', help='render docs/status.md from current authorities')
    args = parser.parse_args()
    result = audit(args.spec.resolve())
    rendered = json.dumps(result, indent=2) + "\n"
    if args.write_status and result['passed']:
        write_status()
    if args.json:
        args.json.resolve().relative_to(ROOT / 'build')
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
