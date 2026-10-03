"""Resolve normal CRT/SDL imports and report remaining real native dependencies.

This attempts a strict shared-library link of the complete partial core. It
adds no placeholder symbols and never claims a runnable game. A failed link
is useful evidence: it separates ordinary library imports from port work.
"""
from pathlib import Path
import argparse
import hashlib
import json
import re
import subprocess

ROOT = Path(__file__).resolve().parents[2]

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out', required=True)
    args = ap.parse_args()
    out = (ROOT / args.out).resolve()
    if out.exists() or not out.is_relative_to(ROOT / 'build/workers'):
        raise ValueError('new scratch directory required')
    migration = ROOT / 'build/workers/whole_program/generated/migration.json'
    report = json.loads(migration.read_text())
    core = ROOT / report['partial_core_link']['object']
    if not report['inputs_stable'] or sha(core) != report['partial_core_link']['object_sha256']:
        raise ValueError('stable current core required')
    changed = [name for name, expected in report['inputs'].items()
               if not (ROOT / name).is_file() or sha(ROOT / name) != expected]
    changed += [r['generated'] for r in report['modules']
                if sha(ROOT / r['generated']) != r['generated_sha256']]
    if changed:
        raise ValueError(f'rebuild required: migration inputs changed: {changed}')
    sdk = ROOT / 'build/sdl3-sdk/SDL3-3.4.16/x86_64-w64-mingw32'
    library = sdk / 'lib/libSDL3.dll.a'
    out.mkdir(parents=True)
    command = [report['compiler']['path'], '-shared', str(core), str(library),
               '-Wl,--no-undefined', '-o', str(out / 'diagnostic-core.dll')]
    result = subprocess.run(command, capture_output=True, text=True)
    log = out / 'link.txt'
    log.write_text(result.stdout + result.stderr, encoding='utf-8')
    missing = sorted(set(re.findall(r"undefined reference to [`']([^'`]+)['`]", result.stderr)))
    contracts = report['unprovided_symbol_contracts']
    receipt = {
        'schema': 'simant-whole-core-host-link-audit-v1',
        'scope': 'Strict diagnostic library link only; no executable, runtime binding, or game admission',
        'link_passed': result.returncode == 0,
        'inputs': {migration.relative_to(ROOT).as_posix(): sha(migration),
                   core.relative_to(ROOT).as_posix(): sha(core),
                   library.relative_to(ROOT).as_posix(): sha(library),
                   Path(__file__).relative_to(ROOT).as_posix(): sha(Path(__file__))},
        'command': command, 'log_sha256': sha(log),
        'partial_core_import_count': len(report['unprovided_object_symbols']),
        'remaining_dependency_count': len(missing),
        'remaining_dependencies': {name: contracts.get(name, {'classification': 'LINKER_DIAGNOSTIC_ONLY'})
                                   for name in missing}}
    (out / 'report.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'link_passed': receipt['link_passed'],
                      'remaining_dependencies': len(missing)}))
    if result.returncode and not missing:
        raise RuntimeError('link failed without classified undefined references; inspect log')

if __name__ == '__main__':
    main()
