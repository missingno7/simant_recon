"""Extract the pinned distribution with its own checksum-verifying DOS installer.

Run from the repository root. Only the scratch output is mounted in the guest.
No historical tool payload is committed or copied to C:/tools by this script.
"""
import hashlib
import os
from pathlib import Path
import subprocess
import sys
import zipfile

ARCHIVE = Path('C:/tools/RTLink-Plus-4.00-DiscMaster/RTLINK40.ZIP')
ARCHIVE_SHA = '065cc748274addd3ac6f4aca314e67305e5f9a05758dee9b9cf76a19de5c69d5'
INSTALL_SHA = 'ae1508859bfd83f3ee97e175699501d39e470f2bcfa98117d9b13f92c43742d8'
RUNNER = Path('C:/tools/dosbox-x/dosbox-x.exe')
RUNNER_SHA = 'b028a4d328302ea270722dec69f3ec3a10ebf76beba72a51970db33a88df2bf6'
EXTRACTOR = Path('C:/program files (x86)/universal extractor/bin/7z.exe')
EXTRACTOR_SHA = 'ce194eb35c6b58248f7e70239a36b037e0711ec1a42ee969e7d1f2d9875ed027'


def main():
    out = Path(sys.argv[1] if len(sys.argv) > 1 else 'build/workers/blockers/rtlink400-clean').resolve()
    root = Path.cwd().resolve()
    if not out.is_relative_to(root / 'build/workers'):
        raise ValueError('installer output must be under this repository build/workers')
    if out.exists():
        raise ValueError('use a fresh output directory to distinguish each installer run')
    for path, expected in ((ARCHIVE, ARCHIVE_SHA), (RUNNER, RUNNER_SHA), (EXTRACTOR, EXTRACTOR_SHA)):
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError(f'pin mismatch: {path}')
    out.mkdir(parents=True)
    with zipfile.ZipFile(ARCHIVE) as outer:
        for disk in range(1, 7):
            part = out / f'RTLINK{disk}.ZIP'
            part.write_bytes(outer.read(part.name))
            # The inner archive's old ZIP compression is unsupported by zipfile.
            members = [f'DISK{disk}.DAT'] + (['INSTALL.EXE'] if disk == 1 else [])
            subprocess.run([str(EXTRACTOR), 'e', '-y', f'-o{out}', str(part), *members],
                           check=True, capture_output=True, timeout=30)
    if hashlib.sha256((out / 'INSTALL.EXE').read_bytes()).hexdigest() != INSTALL_SHA:
        raise ValueError('installer pin mismatch')
    (out / 'dest').mkdir()
    (out / 'ANSWERS.TXT').write_bytes(
        b'C\r\n\r\nY\r\nN\r\nC:\\DEST\r\nY\r\nC:\\DEST\r\nY\r\nC:\\DEST\r\nY\r\nC:\\DEST\r\n' + b'\r\n' * 12)
    conf = ['[sdl]', 'fullscreen=false', 'output=surface', '[dosbox]', 'memsize=32',
            '[cpu]', 'core=normal', 'cputype=386', 'cycles=max', '[autoexec]',
            f'mount c "{out.as_posix()}"', 'c:', 'install.exe <ANSWERS.TXT >INSTALL.LOG', 'exit']
    (out / 'DOSBOX.CONF').write_text('\n'.join(conf) + '\n', encoding='ascii')
    env = os.environ.copy()
    env.update(SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy')
    result = subprocess.run([str(RUNNER), '-conf', str(out / 'DOSBOX.CONF'),
                             '-fastlaunch', '-exit', '-nomenu'], cwd=out, env=env,
                            capture_output=True, timeout=60,
                            creationflags=subprocess.CREATE_NO_WINDOW)
    (out / 'host.log').write_bytes(result.stdout + result.stderr)
    log = (out / 'INSTALL.LOG').read_text(errors='replace')
    if result.returncode or 'Installation complete' not in log:
        raise RuntimeError(f'installation incomplete; inspect {out / "INSTALL.LOG"}')
    print(f'installation complete: {len(list((out / "dest").glob("*")))} files; {out}')


if __name__ == '__main__':
    main()
