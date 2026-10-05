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
ALLOWED_BUILD_ROOTS = {"current", "deps", "workers", "scratch", "locks"}
REQUIRED_ENTRY_POINTS = {
    "dos/build.py", "portable/build.py", "tools/validate.py",
    "tools/context.py", "tools/search.py", "tools/promote.py",
}
CLOSED_STATUSES = {"RESOLVED", "CLOSED", "RETIRED", "COMPLETE"}


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
    return active_ids


def _module_name(value: Any) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return None
    normalized = value.replace("\\", "/").removesuffix(".py")
    prefix = "portable/canonical_native_abi/"
    if normalized.startswith(prefix):
        normalized = normalized[len(prefix):]
    return Path(normalized).stem


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
    if evidence.get('semantic_gates') != program.get('dos', {}).get('semantic_gates'):
        issues.append(_issue('blocker_projection_drift','evidence/canonical/blockers.json','Semantic gates must match the canonical inventory.'))
    debt = program.get('dos', {}).get('unresolved_data', [])
    if [(r.get('id'),r.get('bytes')) for r in evidence.get('data_debt',[])] != [(r.get('id'),r.get('bytes')) for r in debt]:
        issues.append(_issue('data_projection_drift','evidence/canonical/blockers.json','Functional data membership/bytes must match the canonical inventory.'))
    _check_spec(spec, issues)
    live_ids = _check_program(program, issues)
    live_ids.update(_check_platform(platform, live_ids, issues))
    _check_lowering(spec, live_ids, issues)
    _check_build_root(issues)
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
    """Render membership/counts from the current authorities, never edit claims."""
    program = json.loads((ROOT / 'src/program.json').read_text())
    platform = json.loads((ROOT / 'portable/platform.json').read_text())
    evidence = json.loads((ROOT / 'evidence/canonical/blockers.json').read_text())
    gates, debt = program['dos']['semantic_gates'], program['dos']['unresolved_data']
    lines = [
        '# Current reconstruction status', '',
        'Generated by `python tools/repository.py --write-status`. Membership comes from',
        '`src/program.json`; import grounding comes from `evidence/canonical/blockers.json`;',
        'native exceptions come from `portable/platform.json`. This page is a view, not',
        'another inventory. Validation results and cleanup metrics are in [cleanup.md](cleanup.md).', '',
        f'The shared program has {len(program["modules"])} whole source TUs and '
        f'{len(program["semantics"])} strict semantic registrations.',
        f'Independent DOS linking remains blocked by {len(evidence["imports"])} storage imports, '
        f'{len(gates)} semantic gates and {sum(r["bytes"] for r in debt)} functional bytes '
        f'in {len(debt)} ranges. No standalone DOS game or human acceptance is established.', '',
        'Manual SDL3 playtesting found broken sound, a logo-click hang and a discrepancy',
        'in the intended 640x480 VGA path. [Playtest report](../evidence/canonical/validation/manual-playtest.json).',
        'Standalone reconstructed DOS closure takes priority over native symptom fixes.',
        'Bounded native passing flows do not close the exceptions below.',
        '`functional-source-oracle-v1` is pending.', '',
        '## SEMANTIC / PORT-BLOCKING', '', '### Source storage imports', '',
        '| Symbol | Required resolution |', '| --- | --- |',
    ]
    def cell(value):
        return str(value).replace('|', '\\|').replace('\n', ' ')
    lines += [f'| `{row["name"]}` | {cell(row["grounding"])} |' for row in evidence['imports']]
    lines += ['', '### DOS address and ownership gates', '', '| ID | Reason |', '| --- | --- |']
    lines += [f'| `{row["id"]}` | {cell(row["reason"])} |' for row in gates]
    lines += ['', '### Unowned functional data', '', '| ID | Bytes | Reason |', '| --- | ---: | --- |']
    lines += [f'| `{row["id"]}` | {row["bytes"]} | {cell(row["reason"])} |' for row in debt]
    lines += ['', '### Native exceptions', '', '| ID | Scope |', '| --- | --- |']
    lines += [f'| `{row["id"]}` | {cell(row["detail"])} |' for row in platform['preview_limitations']]
    lines += [
        '', 'Each temporary lowering module has named blocker IDs and a deletion condition',
        'in `layout/repository.json`. The architecture guard rejects absent/closed IDs',
        'while their temporary converters remain. Classification is not a semantic waiver.', '',
        '## HISTORICAL-BINARY-ONLY', '',
        'Reviewed declaration/codegen residue, original segment/communal ordering,',
        'RTLink placement/relocation ordering and alignment remain historical build facts.',
        'They do not block the native build. [Generated progress](progress.md) tracks',
        'historical byte debt separately from the functional ranges above.', '',
        'Only independently admitted facts may close a semantic gate. The existing',
        'hot-box, mono-tail, viewport, index-adjacency and heap investigations grant',
        'no guessed owner, initializer, extent or whole-game equivalence.', '',
    ]
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
