"""Package the current Windows preview for a drop-in human playtest."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from workspace import prepare_output


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', type=Path, default=ROOT / 'build/current/portable')
    args = parser.parse_args()
    build = args.build.resolve()
    report_path = build / 'report.json'
    report = json.loads(report_path.read_text(encoding='utf-8'))
    if not report.get('passed') or not report['input_stability']['at_end']:
        raise ValueError('Successful stable native build required')
    for name, pin in report['input_pins'].items():
        path = Path(name)
        if not path.is_absolute():
            path = ROOT / path
        if sha(path) != pin:
            raise ValueError('Changed build input: ' + name)
    exe = build / 'simant-canonical.exe'
    dll = build / 'SDL3.dll'
    if sha(exe) != report['executable']['sha256'] or sha(dll) != report['sdk']['runtime_sha256']:
        raise ValueError('Executable or SDL runtime differs from build report')
    fonts = build / 'runtime-bios-fonts'
    font_files = sorted(name.removeprefix('portable/runtime/bios-reference/')
                        for name in report['input_pins']
                        if name.startswith('portable/runtime/bios-reference/'))
    for name in font_files:
        if sha(fonts / name) != report['input_pins']['portable/runtime/bios-reference/' + name]:
            raise ValueError('Changed font support: ' + name)
    platform = json.loads((ROOT / 'portable/platform.json').read_text())
    out = prepare_output(ROOT / 'build/current/playtest', ROOT / 'build/current/playtest')
    payload = out / 'files'
    payload.mkdir()
    identity = build / 'simant-build-id.txt'
    expected_identity = ''.join(f'{key}={value}\n' for key, value in report['build_identity'].items())
    if identity.read_text(encoding='ascii') != expected_identity:
        raise ValueError('Build identity receipt differs from build report')
    for source in (exe, dll, identity):
        shutil.copyfile(source, payload / source.name)
    (payload / 'simant-sdl3-fonts').mkdir()
    for name in font_files:
        (payload / 'simant-sdl3-fonts' / name).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(fonts / name, payload / 'simant-sdl3-fonts' / name)
    license_file = Path(report['sdk']['path']).parent / 'LICENSE.txt'
    shutil.copyfile(license_file, payload / 'SDL3-LICENSE.txt')
    shutil.copyfile(ROOT / 'portable/audio/ymfm/LICENSE', payload / 'ymfm-LICENSE.txt')
    required = ' '.join(platform['runtime_assets'])
    launcher = f'''@echo off
setlocal
cd /d "%~dp0"
for %%F in ({required}) do if not exist "%%F" (
  echo Missing game resource: %%F
  echo Extract this package into your DOS SimAnt game folder.
  pause
  exit /b 2
)
rem Original startup only opens this file; its bytes are never read or executed.
if not exist "INSTALL.EXE" type nul > "INSTALL.EXE"
"simant-canonical.exe" %* > "simant-sdl3.log" 2>&1
set "result=%errorlevel%"
if not "%result%"=="0" (
  echo SimAnt SDL3 exited with code %result%.
  echo Please ZIP the newest folder in diagnostics with your report.
  pause
)
exit /b %result%
'''
    (payload / 'Play-SimAnt-SDL3.cmd').write_text(launcher, encoding='ascii', newline='\r\n')
    debug_launcher = launcher.replace('"simant-canonical.exe" %*', '"simant-canonical.exe" --debug %*')
    (payload / 'Play-SimAnt-SDL3-debug.cmd').write_text(debug_launcher, encoding='ascii', newline='\r\n')
    windows_launcher = launcher.replace('"simant-canonical.exe" %*', '"simant-canonical.exe" --windows %*')
    (payload / 'Play-SimAnt-Windows.cmd').write_text(windows_launcher, encoding='ascii', newline='\r\n')
    (payload / 'Play-SimAnt-Windows-debug.cmd').write_text(
        windows_launcher.replace('--windows %*', '--windows --debug %*'), encoding='ascii', newline='\r\n')
    readme = '''SIMANT SDL3 - WINDOWS 64-BIT PLAYTEST PREVIEW

Extract all files beside your original DOS SimAnt game data, keeping the
simant-sdl3-fonts directory. Double-click Play-SimAnt-SDL3.cmd.
No Python, compiler, DOSBox or separate SDL installation is needed.

For bug reports, launch Play-SimAnt-SDL3-debug.cmd. Every launch creates a unique
diagnostics/simant-DATE-TIME-PID folder beside the executable (or under local
application data if the game folder is not writable). After a crash or problem,
ZIP the newest diagnostics folder and include it with your report. Debug sessions
save stderr/SDL output and input.txt; F12 saves the last presented frame and its
palette in capture-NNNN. Without debug, F12 retains its ordinary behavior.
Crash reports preserve crash.txt, a best-effort crash.dmp and simant-crashed.exe.
Logs include paths, command line and SIMANT.CFG; input recording grows as you play.

To approximately replay a debug session from the same assets/configuration:
simant-canonical.exe --seed N --input-script "diagnostics\\SESSION\\input.txt"
Use the seed shown in session.log. Host timing and asynchronous audio may differ;
input recordings are not full simulation snapshots. --diagnostics-dir=PATH
chooses another diagnostics destination. Forced termination cannot write a dump.

Use a copy of your game folder, preferably a short path such as C:\\Games\\SimAnt.
Original file dialogs still have a 67-character path domain. The package contains
no original game databases, configuration, saves or FONT1-4 files and does not
replace them. The launcher creates an empty INSTALL.EXE only when absent, for
the source startup's file-availability probe; an existing installer is preserved.

The launcher leaves display and sound selection to the original SIMANT.CFG and
source command-line rules (shipped: VGA and Sound Blaster mode 6). Audio renders the
guest OPL and direct DSP DAC commands through ymfm and SDL3. Startup dialogs and game menus are
the reconstructed game. This preview has passed scripted startup, VGA/input,
Save/Load, resource, RNG and bounded simulation checks. Complete gameplay,
long-run stability and full DOS/native behavior equivalence are not established.

MODERN WINDOWS PROTOTYPE: Play-SimAnt-Windows.cmd (and -debug) runs the same
game with its main panels (edit view, map, info, behavior, caste, history,
score, yard, examine) as separate Windows windows owned by the main window,
like SimAnt for Windows: native caption with the game's title, normal
Windows move, close button (closes the game window as its close box does) and
a sizing frame on the edit view (the game applies its own size rules). The
first click on a window that is behind another one brings it to the front
(as SimAnt for Windows did); the next click acts. The normal Windows cursor
is used. The main window stays as the desktop: menu bar, dialogs and the
remaining windows. --scale=N (1..8, default 2) sets one scale for every
window; --windows=ID,ID... (hex logical IDs, e.g. 1200,1300) chooses the
hosted windows. Known prototype gaps: the menu bar is still the game's own,
no native scroll bars or tool cursors yet; map edge-scrolling works only from
the main window.

Useful feedback: exact actions before the issue, game mode, visible symptom,
screenshot/video, and simant-sdl3.log. For Save/Load problems, include the new
save and whether it reloads or behaves differently. Test menus, mouse/keyboard,
window movement, sound, simulation speed and longer sessions. Close the SDL
window to stop. Logs are written locally; nothing is uploaded automatically.
'''
    (payload / 'README-PLAYTEST.txt').write_text(readme, encoding='ascii', newline='\r\n')
    revision = subprocess.check_output(['git', '-c', 'safe.directory=' + ROOT.as_posix(),
                                        'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    manifest = {'schema': 'simant-human-playtest-package-v1', 'source_revision': revision,
                'build_report_sha256': sha(report_path), 'executable_sha256': sha(exe),
                'platform': 'Windows x86_64', 'claim': 'BOUNDED_PLAYTEST_PREVIEW',
                'required_game_files': platform['runtime_assets'],
                'files': {p.relative_to(payload).as_posix(): sha(p)
                          for p in sorted(payload.rglob('*')) if p.is_file()}}
    (payload / 'package-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    archive = out / 'simant-sdl3-playtest-win64.zip'
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as package:
        for file in sorted(payload.rglob('*')):
            if file.is_file():
                package.write(file, file.relative_to(payload).as_posix())
    print(json.dumps({'archive': str(archive), 'bytes': archive.stat().st_size,
                      'sha256': sha(archive), 'original_game_assets_included': False}, indent=2))


if __name__ == '__main__':
    main()
