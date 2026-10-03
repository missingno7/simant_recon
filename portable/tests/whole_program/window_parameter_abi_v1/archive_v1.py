from __future__ import annotations
import hashlib, json, shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
SUITE = Path(__file__).resolve().parent
REPORT = SUITE / 'evidence/report-v1.json'
DEST = SUITE / 'evidence/archive-v1'


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> int:
    report = json.loads(REPORT.read_text(encoding='utf-8'))
    if report.get('status') != 'PASS' or report.get('schema') != 'window-parameter-abi-v1':
        raise SystemExit('refusing archive: report is not the expected passing v1 receipt')
    if DEST.exists():
        raise SystemExit(f'refusing to overwrite archive: {DEST}')
    snapshot = ROOT / report['snapshot']
    if not snapshot.is_dir():
        raise SystemExit(f'missing original generated snapshot: {snapshot}')
    DEST.mkdir(parents=True)
    files = []

    for row in report['adapted_modules']:
        module = row['module']
        prefix, rest = module.removeprefix('src/').split('/', 1)
        generated_name = f'{prefix}_{Path(rest).stem}.c'
        source = snapshot / generated_name
        if not source.is_file() or sha(source) != row['input_sha256']:
            raise SystemExit(f'input module hash mismatch before archive: {source}')
        archived_rel = Path('generated') / generated_name
        target = DEST / archived_rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        if sha(target) != row['input_sha256']:
            raise SystemExit(f'copied module hash mismatch: {target}')
        files.append({'kind': 'generated-module', 'module': module,
                      'original_path': str(source.relative_to(ROOT)).replace('\\', '/'),
                      'archive_path': archived_rel.as_posix(),
                      'sha256': row['input_sha256']})

    static_inputs = [
        (Path('portable/whole_program/conversions/window_parameter_abi_v1.py'), 'converter/window_parameter_abi_v1.py'),
        (Path('portable/whole_program/window_parameters.c'), 'helper/window_parameters.c'),
        (Path('portable/whole_program/window_parameters.h'), 'helper/window_parameters.h'),
        (Path('portable/whole_program/window_refs.c'), 'helper/window_refs.c'),
        (Path('portable/whole_program/window_refs.h'), 'helper/window_refs.h'),
        (Path('portable/tests/whole_program/window_parameter_abi_v1/test_parameters.c'), 'tests/test_parameters.c'),
        (Path('portable/tests/whole_program/window_parameter_abi_v1/run_v1.py'), 'tests/run_v1.py'),
    ]
    for original_rel, archived_rel in static_inputs:
        source = ROOT / original_rel
        if not source.is_file():
            raise SystemExit(f'missing static input: {source}')
        expected = report['pins'].get(original_rel.as_posix())
        actual = sha(source)
        if expected is not None and actual != expected:
            raise SystemExit(f'static input hash mismatch against report: {source}')
        if expected is None:
            expected = actual
        target = DEST / archived_rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        if sha(target) != expected:
            raise SystemExit(f'copied static input hash mismatch: {target}')
        files.append({'kind': 'static-input', 'original_path': original_rel.as_posix(),
                      'archive_path': archived_rel, 'sha256': expected, 'pinned_by_receipt': original_rel.as_posix() in report['pins']})

    manifest = {'schema': 'window-parameter-abi-v1-input-archive',
                'receipt': 'report-v1.json', 'receipt_sha256': sha(REPORT),
                'snapshot': report['snapshot'], 'files': files}
    manifest_path = DEST / 'archive-manifest.json'
    manifest_path.write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    # Verify every archived path from the finished manifest, including duplicate checks.
    for row in files:
        archived = DEST / row['archive_path']
        if sha(archived) != row['sha256']:
            raise SystemExit(f'final archive verification failed: {archived}')
    print(f'archived and hash-verified {len(files)} inputs at {DEST}')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())


