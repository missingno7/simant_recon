"""Include the native edge-scroll pacing regression in repository discovery.

portable/tests/runtime/run_edge.py replays Quick Game edge holds and checks, among others,
that held edge scrolling advances one step per emulated 59.94 Hz display refresh
(scroll_steps_paced_by_VGA_refresh). It runs against build/current/portable.
"""
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / 'build/current/portable/report.json'
GDB = Path('C:/msys64/mingw64/bin/gdb.exe')


class EdgeScroll(unittest.TestCase):
    @unittest.skipUnless(REPORT.is_file(), 'native build absent (python portable/build.py --out build/current/portable)')
    @unittest.skipUnless(GDB.is_file() or shutil.which('gdb'), 'GDB with Python support absent')
    def test_edge_scroll_paced_by_display_refresh(self):
        parent = ROOT / 'build/scratch'
        parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='edge-', dir=parent) as scratch:
            out = Path(scratch) / 'run'
            run = subprocess.run([sys.executable, str(ROOT / 'portable/tests/runtime/run_edge.py'),
                                  '--report', str(REPORT), '--out', str(out)],
                                 cwd=ROOT, capture_output=True, text=True, timeout=600)
            self.assertEqual(run.returncode, 0, run.stdout[-4000:] + run.stderr[-4000:])


if __name__ == '__main__':
    unittest.main()
