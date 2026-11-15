"""Include the enhanced-mode phase regressions in repository discovery.

portable/tests/enhanced/run.py checks the snapshot/action contracts and carries strict
expected failures for presentation bugs that later phases fix (docs/enhanced-mode.md).
It runs against build/current/portable.
"""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / 'build/current/portable'


class EnhancedMode(unittest.TestCase):
    @unittest.skipUnless((BUILD / 'report.json').is_file(), 'native build absent (python portable/build.py --out build/current/portable)')
    def test_enhanced_phase_regressions(self):
        parent = ROOT / 'build/scratch'
        parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='en-', dir=parent) as scratch:
            run = subprocess.run([sys.executable, str(ROOT / 'portable/tests/enhanced/run.py'),
                                  '--build', str(BUILD), '--out', str(Path(scratch) / 'r')],
                                 cwd=ROOT, capture_output=True, text=True, timeout=1200)
            self.assertEqual(run.returncode, 0, run.stdout[-4000:] + run.stderr[-4000:])


if __name__ == '__main__':
    unittest.main()
