#!/usr/bin/env python3
"""Reproduce one archived dialog case in an isolated scratch clone.

The original DOS assets are referenced through a local assets directory junction;
they are never copied into the evidence archive or clone. The suite and runtime
components are taken from the archived snapshots, then their ROOT is determined
from the isolated clone layout before imports execute.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def canonical_sha(value) -> str:
    def normalize(item):
        if isinstance(item, dict):
            return {str(k): normalize(v) for k, v in sorted(item.items(), key=lambda kv: str(kv[0]))}
        if isinstance(item, (list, tuple)):
            return [normalize(v) for v in item]
        return item
    raw = json.dumps(normalize(value), sort_keys=True, separators=(',', ':')).encode('utf-8')
    return hashlib.sha256(raw).hexdigest()


def copy_tree(src: Path, dst: Path) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--repo', type=Path, required=True)
    ap.add_argument('--archive', type=Path, required=True)
    ap.add_argument('--clone', type=Path, required=True)
    args = ap.parse_args()
    repo, archive, clone = args.repo.resolve(), args.archive.resolve(), args.clone.resolve()
    deps = archive / 'dependencies'
    try:
        rel_clone = clone.relative_to(repo)
    except ValueError:
        rel_clone = None
    if rel_clone is None or not rel_clone.parts or rel_clone.parts[:2] != ('build', 'workers'):
        raise SystemExit('clone must be a scratch path under repository build/workers')
    if clone.exists():
        raise SystemExit(f'scratch clone already exists; choose a fresh path: {clone}')
    clone.mkdir(parents=True)

    # Verify immutable package inputs before copying or importing any code.
    index = json.loads((archive / 'ready-index.json').read_text(encoding='utf-8'))
    checked = []
    for row in index.get('source_and_tool_snapshots', []):
        p = repo / row['path']
        # The two original resource files intentionally live only at their
        # ignored repository asset paths and are pinned separately below.
        if row.get('asset_reference'):
            p = repo / row['source_path']
        if not p.is_file() or sha(p) != row['sha256']:
            raise SystemExit(f"snapshot mismatch/missing: {row['path']}")
        checked.append({'path': row['path'], 'sha256': row['sha256']})
    source = archive / 'candidate-source.c'
    if sha(source) != index['run_identity']['source_sha256']:
        raise SystemExit('candidate source pin mismatch')
    suite_snapshot = archive / 'suite.py'
    if sha(suite_snapshot) != index['suite']['sha256']:
        raise SystemExit('suite snapshot pin mismatch')
    harness_snapshot = archive / 'harness.py'
    if sha(harness_snapshot) != index['harness']['sha256']:
        raise SystemExit('harness snapshot pin mismatch')

    # Copy exact archived components. Assets are not part of dependencies and
    # are supplied only through the already-existing repository assets folder.
    for name in ('tools', 'src', 'layout'):
        src = deps / name
        if src.exists():
            copy_tree(src, clone / name)
    extra_layout = repo / 'layout'
    for name in ('functions.json', 'symbols.json'):
        shutil.copy2(extra_layout / name, clone / 'layout' / name)
    shutil.copy2(source, clone / 'candidate-source.c')
    # The helper fixture is part of the archived runtime tree, not a live import.
    # Ensure the suite resolves ROOT as the clone, then adds clone/tools itself.
    (clone / 'repro' / 'scripts').mkdir(parents=True, exist_ok=True)
    shutil.copy2(suite_snapshot, clone / 'repro' / 'scripts' / 'suite.py')

    # The build-only Python dependency is a runtime prerequisite, not evidence.
    dep_src = repo / 'build' / 'behavior' / 'deps'
    if dep_src.exists():
        copy_tree(dep_src, clone / 'build' / 'behavior' / 'deps')
    else:
        raise SystemExit('pinned Unicorn runtime is unavailable under build/behavior/deps')

    # The assets directory must be a junction/symlink to the user's local,
    # ignored originals. Refuse an ordinary copied directory.
    asset_link = clone / 'assets'
    command = ('& { param($p,$t) New-Item -ItemType Junction -Path $p -Target $t | Out-Null }')
    made = subprocess.run(['powershell', '-NoProfile', '-Command', command,
                           str(asset_link), str(repo / 'assets')],
                          capture_output=True, text=True)
    if made.returncode or not asset_link.exists() or asset_link.resolve() != (repo / 'assets').resolve():
        raise SystemExit(f'could not create verified local asset junction: {made.stderr or made.stdout}')
    asset_pin_path = archive / 'dependencies' / 'assets' / 'original-asset-pins.json'
    pins = json.loads(asset_pin_path.read_text(encoding='utf-8'))
    asset_records = []
    for row in pins['assets']:
        p = repo / row['path']
        if not p.is_file() or sha(p) != row['sha256']:
            raise SystemExit(f"original asset pin mismatch/missing: {row['path']}")
        if sha(asset_link / Path(row['path']).name) != row['sha256']:
            raise SystemExit(f"clone asset junction does not resolve pinned original: {row['path']}")
        asset_records.append({'path': row['path'], 'sha256': row['sha256'], 'bytes': p.stat().st_size})

    # Populate the archived candidate at the historical whole-module seed path.
    seed = clone / 'work' / 'takeover' / 'hardtail' / 'seeds' / 'S15_384C_01b51eecedcd.c'
    seed.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, seed)

    # Correct ROOT is established by the suite's isolated clone-relative path:
    # clone/repro/scripts/suite.py -> parents[2] == clone. Import only now.
    if (clone / 'repro' / 'scripts' / 'suite.py').resolve().parents[2] != clone:
        raise SystemExit('suite placement failed to establish clone ROOT')
    sys.path.insert(0, str(clone / 'repro' / 'scripts'))
    spec = importlib.util.spec_from_file_location('archived_dialog_suite', clone / 'repro' / 'scripts' / 'suite.py')
    suite = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = suite
    spec.loader.exec_module(suite)
    if suite.ROOT.resolve() != clone:
        raise SystemExit(f'suite ROOT is {suite.ROOT}, expected clone {clone}')

    # Its imports resolve to clone/tools snapshots; reject accidental live tools.
    import behavior as runner
    if Path(runner.__file__).resolve() != (clone / 'tools' / 'behavior.py').resolve():
        raise SystemExit(f'runner imported outside isolated clone: {runner.__file__}')

    out = clone / 'build' / 'freshclone-directed-replay'
    source = clone / 'candidate-source.c'
    pair = runner.PreparedPair(suite.FUNCTION, source=source, out=out / 'pair')
    group, fixture = next(suite.cases(1, 944505401))
    hooks = runner.symbol('win_drawHooks')
    hook_slot_at = hooks['seg'] * 16 + hooks['off'] + 0x21 * 4
    hook_slot_before_case = pair.original_machine.read(hook_slot_at, 4).hex()
    lock_writes, lock_init = suite._actual_lock_init_writes(pair, fixture)
    fixture.writes.extend(lock_writes)
    result = pair.compare(fixture)
    if not result.equal:
        raise SystemExit('fresh-clone directed replay mismatch')
    row = {
        'schema': 'dialog-freshclone-reproduction-v1',
        'status': 'REPRODUCED_PENDING_ROOT_REVIEW',
        'acceptance_claim': False,
        'fresh_clone_root': str(clone),
        'root_correct_before_imports': True,
        'suite_snapshot_sha256': sha(suite_snapshot),
        'candidate_source_sha256': sha(source),
        'harness_snapshot_sha256': sha(harness_snapshot),
        'runner_import_path': str(Path(runner.__file__).resolve()),
        'runner_sha256': sha(Path(runner.__file__).resolve()),
        'component_snapshot_count': len(checked),
        'component_snapshots': checked,
        'asset_original_references': asset_records,
        'asset_junction_target': str(asset_link.resolve()),
        'win_2100_draw_hook_pointer_before_case': {
            'address': hook_slot_at, 'bytes': hook_slot_before_case,
            'is_null': hook_slot_before_case == '00000000'},
        'oracle_sha256': pair.identity['oracle_sha256'],
        'compiled_object_sha256': pair.identity['object_sha256'],
        'linked_code_sha256': pair.identity['linked_code_sha256'],
        'lock_init_setup': lock_init,
        'directed_case': fixture.label,
        'case_lane': group,
        'original_observation_sha256': canonical_sha(result.original),
        'candidate_observation_sha256': canonical_sha(result.candidate),
        'equal': result.equal,
        'mismatch_categories': result.diff,
        'original': result.original,
        'candidate': result.candidate,
    }
    result_path = out / 'repro.json'
    result_path.parent.mkdir(parents=True, exist_ok=True)
    result_path.write_text(json.dumps(row, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'result': str(result_path), 'equal': result.equal,
                      'case': fixture.label, 'root': str(suite.ROOT),
                      'oracle': pair.identity['oracle_sha256']}, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
