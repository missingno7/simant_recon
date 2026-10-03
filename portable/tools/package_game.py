"""Package verified DOS oracle and native preview as game-directory drop-ins."""
from pathlib import Path
import argparse, hashlib, json, shutil, zipfile

ROOT = Path(__file__).resolve().parents[2]

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def zip_directory(directory, destination):
    with zipfile.ZipFile(destination, 'w', zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(directory.rglob('*')):
            if path.is_file():
                archive.write(path, path.relative_to(directory).as_posix())

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--application', required=True, type=Path)
    ap.add_argument('--out', required=True, type=Path)
    ap.add_argument('--gpl-license', type=Path,
                    default=Path('C:/msys64/usr/share/licenses/libargp/COPYING'))
    args = ap.parse_args()
    application = (ROOT / args.application).resolve()
    out = (ROOT / args.out).resolve()
    if out.exists() or not out.is_relative_to(ROOT / 'build'):
        raise ValueError('new build output directory required')
    build_report = application.parent / 'report.json'
    linked = json.loads(build_report.read_text())
    if not linked['passed'] or linked['executable_sha256'] != sha(application):
        raise ValueError('verified whole-application executable required')
    hybrid = ROOT / 'build/link/SIMANT.HYBRID.EXE'
    oracle = ROOT / 'assets/SIMANT.EXE'
    provenance_path = ROOT / 'build/link/provenance.json'
    provenance = json.loads(provenance_path.read_text())
    oracle_hash = sha(oracle)
    if (not provenance['hybrid_equal'] or provenance['failures'] or
        sha(hybrid) != oracle_hash or provenance['hybrid_sha256'] != oracle_hash):
        raise ValueError('byte-identical hybrid with passing provenance required')
    if not args.gpl_license.is_file():
        raise ValueError('full GPL license text required for DOSBox font bundle')
    dos, native = out / 'dos-hybrid', out / 'sdl3'
    dos.mkdir(parents=True)
    native.mkdir()
    shutil.copyfile(hybrid, dos / 'SIMANTH.EXE')
    (dos / 'RUN-DOS.BAT').write_bytes(b'@echo off\r\nSIMANTH.EXE /dV /s1\r\n')
    (dos / 'README-DOS-ORACLE.txt').write_text(
        'Copy these files into a copy of your original DOS SimAnt game directory.\n'
        'In DOSBox, mount that game directory and run RUN-DOS.BAT, or run:\n'
        '  SIMANTH.EXE /dV /s1\n\n'
        'SIMANTH.EXE is the verified hybrid from dos-semantic-oracle-v1.\n'
        f'It is byte-identical to the original DOS executable: SHA-256 {oracle_hash}.\n'
        'It contains explicitly tracked original-byte historical proof debt.\n'
        'It is not a wholly rebuilt EXE or a native Windows program.\n'
        'Original game resources are required and are not included here.\n'
        'Your existing SIMANT.EXE is not replaced.\n', encoding='utf-8')
    shutil.copyfile(application, native / 'SimAnt-SDL3.exe')
    shutil.copyfile(application.parent / 'SDL3.dll', native / 'SDL3.dll')
    fonts = native / 'simant-sdl3-fonts'
    fonts.mkdir()
    for name in ('font-8x8.bin', 'font-8x14.bin', 'manifest.json',
                 'DOSBox-Staging-LICENSE', 'int10_memory.cpp'):
        shutil.copyfile(application.parent / 'runtime-bios-fonts' / name, fonts / name)
    shutil.copyfile(args.gpl_license, fonts / 'COPYING-GPL.txt')
    licenses = native / 'simant-sdl3-licenses'
    licenses.mkdir()
    shutil.copyfile(ROOT / 'build/sdl3-sdk/SDL3-3.4.16/LICENSE.txt', licenses / 'SDL3.txt')
    (native / 'RUN-SDL3.bat').write_bytes(
        b'@echo off\r\ncd /d "%~dp0"\r\n"%~dp0SimAnt-SDL3.exe" /dV /s1 %*\r\n'
        b'if errorlevel 1 pause\r\n')
    (native / 'README-SDL3.txt').write_text(
        'Windows 64-bit preview. Copy all files and both simant-sdl3 folders\n'
        'into a copy of your original DOS SimAnt game directory.\n'
        'Double-click RUN-SDL3.bat for VGA (640x480), or SimAnt-SDL3.exe for EGA.\n'
        'No compiler, Python, DOSBox, or build directory is needed for SDL3.\n'
        'Original game files are required; they are not bundled or replaced.\n'
        'Use a copy of the game directory: normal config/save/dump writes go there.\n\n'
        'This is the full converted original-main build, currently under testing.\n'
        'Captions and the original menu flow are present. Complete-game acceptance\n'
        'has not been claimed; the stationary 24x16 cursor issue is still being traced.\n'
        'The DOS oracle package is the comparison baseline.\n', encoding='utf-8')
    inventory = {p.relative_to(out).as_posix(): sha(p)
                 for p in sorted(out.rglob('*')) if p.is_file()}
    report = {'schema': 'simant-game-directory-package-v1',
              'scope': 'Verified DOS hybrid plus SDL3 preview; no complete-game claim',
              'oracle_tag': 'dos-semantic-oracle-v1', 'oracle_sha256': oracle_hash,
              'application': args.application.as_posix(),
              'application_sha256': sha(application),
              'build_report_sha256': sha(build_report),
              'hybrid_provenance_sha256': sha(provenance_path),
              'packager_sha256': sha(Path(__file__)), 'files': inventory}
    (out / 'package-report.json').write_text(json.dumps(report, indent=2) + '\n')
    for name, directory in [('simant-dos-oracle.zip', dos), ('simant-sdl3-preview.zip', native)]:
        zip_directory(directory, out / name)
    print(json.dumps({'out': out.relative_to(ROOT).as_posix(),
                      'oracle_sha256': oracle_hash, 'packaged_files': len(inventory)}))

if __name__ == '__main__':
    main()
