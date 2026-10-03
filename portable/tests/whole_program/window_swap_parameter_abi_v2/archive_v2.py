from __future__ import annotations
import hashlib, json, shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
SUITE = Path(__file__).resolve().parent
REPORT = SUITE / 'evidence/report-v2.json'
DEST = SUITE / 'evidence/archive-v2'


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def copy_checked(source: Path, archived_rel: str, expected: str, files: list[dict], kind: str) -> None:
    if not source.is_file() or sha(source) != expected:
        raise SystemExit(f'input hash mismatch before archive: {source}')
    target = DEST / archived_rel
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)
    if sha(target) != expected:
        raise SystemExit(f'copied input hash mismatch: {target}')
    files.append({'kind': kind,
                  'original_path': str(source.relative_to(ROOT)).replace('\\', '/'),
                  'archive_path': archived_rel, 'sha256': expected})


def main() -> int:
    report = json.loads(REPORT.read_text(encoding='utf-8'))
    if report.get('schema') != 'window-swap-parameter-abi-v2' or report.get('status') != 'PASS':
        raise SystemExit('refusing archive: unexpected report schema/status')
    if DEST.exists():
        raise SystemExit(f'refusing to overwrite archive: {DEST}')
    snapshot = ROOT / report['snapshot']
    if not snapshot.is_dir():
        raise SystemExit(f'missing generated source snapshot: {snapshot}')
    DEST.mkdir(parents=True)
    files: list[dict] = []
    for row in report['adapted_modules']:
        module = row['module']
        prefix, rest = module.removeprefix('src/').split('/', 1)
        generated_name = f'{prefix}_{Path(rest).stem}.c'
        source = snapshot / generated_name
        copy_checked(source, f'generated/{generated_name}', row['input_sha256'], files,
                     'generated-module')
    for row in report['pins']:
        source = ROOT / row['path']
        expected = row['sha256']
        rel = row['path']
        if rel == 'assets/HCEGANT.DAT':
            archive_rel = 'assets/HCEGANT.DAT'
        elif rel == 'assets/HCEGANT.NDX':
            archive_rel = 'assets/HCEGANT.NDX'
        elif rel.endswith('test_parameters_v2.exe'):
            archive_rel = 'results/test_parameters_v2.exe'
        else:
            archive_rel = 'inputs/' + rel
        copy_checked(source, archive_rel, expected, files, 'report-pinned-input')
    runner = SUITE / 'run_v2.py'
    runner_hash = sha(runner)
    copy_checked(runner, 'tests/run_v2.py', runner_hash, files, 'runner-not-receipt-pinned')
    manifest = {'schema': 'window-swap-parameter-abi-v2-input-archive',
                'receipt_path': REPORT.relative_to(ROOT).as_posix(),
                'receipt_sha256': sha(REPORT),
                'snapshot_path': report['snapshot'],
                'files': files}
    (DEST / 'archive-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    for row in files:
        if sha(DEST / row['archive_path']) != row['sha256']:
            raise SystemExit(f'final archive verification failed: {row["archive_path"]}')
    print(f'archived and hash-verified {len(files)} inputs at {DEST}')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
