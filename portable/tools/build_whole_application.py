"""Link original whole-source main to real providers; unresolved imports fail."""
from pathlib import Path
import argparse
import hashlib
import json
import re
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[2]

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out', required=True)
    args = ap.parse_args()
    out = (ROOT / args.out).resolve()
    if out.exists() or not out.is_relative_to(ROOT / 'build'):
        raise ValueError('new build output required')
    migration = ROOT / 'build/workers/whole_program/generated/migration.json'
    report = json.loads(migration.read_text())
    changed = [name for name, expected in report['inputs'].items()
               if not (ROOT / name).is_file() or sha(ROOT / name) != expected]
    changed += [r['generated'] for r in report['modules']
                if sha(ROOT / r['generated']) != r['generated_sha256']]
    if changed or not report['inputs_stable']:
        raise ValueError(f'regenerate stable whole-source core first: {changed}')
    rejected = [r['source'] for r in report['modules']
                if not r.get('compile', {}).get('passed')]
    if rejected != ['src/root/m171C.c']:
        raise ValueError(f'expected only replaced DOS allocator exclusion: {rejected}')
    core = ROOT / report['partial_core_link']['object']
    if sha(core) != report['partial_core_link']['object_sha256']:
        raise ValueError('compiled core identity changed')
    sdk = ROOT / 'build/sdl3-sdk/SDL3-3.4.16/x86_64-w64-mingw32'
    application = ROOT / 'portable/whole_program/application.c'
    pinned = dict(report['inputs'])
    pinned.update({row['generated']: row['generated_sha256'] for row in report['modules']})
    pinned.update({path.relative_to(ROOT).as_posix(): sha(path)
                   for path in [application, migration, core, Path(__file__)]})
    out.mkdir(parents=True)
    exe = out / 'simant-whole-sdl3.exe'
    command = [report['compiler']['path'], '-std=c11', '-g', '-fsigned-char',
               '-fno-builtin', '-fno-strict-aliasing', '-Werror=implicit-function-declaration',
               '-I', str(ROOT), '-I', str(ROOT / 'portable/whole_program'),
               '-I', str(sdk / 'include'), str(application), str(core),
               str(sdk / 'lib/libSDL3.dll.a'), '-o', str(exe)]
    result = subprocess.run(command, capture_output=True, text=True)
    log = out / 'link.txt'
    log.write_text(result.stdout + result.stderr, encoding='utf-8')
    receipt = {'schema': 'simant-whole-application-link-v1',
               'scope': 'Full executable link; runtime flows require separate verification',
               'passed': result.returncode == 0, 'command': command,
               'inputs': {str(p.relative_to(ROOT)).replace('\\', '/'): sha(p)
                          for p in [application, migration, core, Path(__file__)]},
               'log_sha256': sha(log),
               'missing': sorted(set(re.findall(r"undefined reference to [`']([^'`]+)['`]", result.stderr)))}
    if result.returncode == 0:
        shutil.copyfile(sdk / 'bin/SDL3.dll', out / 'SDL3.dll')
        receipt['executable_sha256'] = sha(exe)
        shutil.copyfile(migration, out / 'migration.json')
        readable = {ROOT / name for name in report['inputs']}
        readable.update(ROOT / row['generated'] for row in report['modules'])
        readable.update(ROOT / row['source'] for row in report['native_support'])
        readable.update(migration.parent.glob('*.h'))
        readable.update([application, Path(__file__)])
        receipt['source_snapshot'] = {}
        for source in sorted(readable):
            if source.suffix.lower() not in {'.c', '.h', '.py', '.json', '.asm'}:
                continue
            relative = source.relative_to(ROOT)
            if relative.parts[:2] == ('build', 'sdl3-sdk'):
                continue
            destination = out / 'inputs' / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, destination)
            receipt['source_snapshot'][relative.as_posix()] = sha(destination)
            if relative.as_posix() in pinned and sha(destination) != pinned[relative.as_posix()]:
                raise ValueError(f'input changed before archival: {relative}')
        # Source startup can write configuration and diagnostic dumps. Keep
        # those writes away from the hash-pinned historical oracle inputs.
        assets = out / 'runtime-assets'
        assets.mkdir()
        receipt['runtime_assets'] = {}
        for original in sorted((ROOT / 'assets').iterdir()):
            if original.is_file():
                shutil.copyfile(original, assets / original.name)
                receipt['runtime_assets'][original.name] = sha(original)
        fonts = out / 'runtime-bios-fonts'
        fonts.mkdir()
        receipt['runtime_bios_fonts'] = {}
        for original in sorted((ROOT / 'build/bios-reference/dosbox-staging-v0.83.0').iterdir()):
            if original.is_file():
                shutil.copyfile(original, fonts / original.name)
                receipt['runtime_bios_fonts'][original.name] = sha(original)
    elif exe.exists():
        exe.unlink()
    receipt['changed_inputs_during_build'] = [name for name, identity in pinned.items()
        if not (ROOT / name).is_file() or sha(ROOT / name) != identity]
    if receipt['changed_inputs_during_build']:
        receipt['passed'] = False
    (out / 'report.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps({'passed': receipt['passed'], 'missing': receipt['missing']}))
    return int(not receipt['passed'])

if __name__ == '__main__':
    raise SystemExit(main())
