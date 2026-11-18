"""Frozen Map dirty marks (object 010E): the port reproduces the original's out-of-table read.

portable/whole_program/platform/tests/run_map_frozen_cache_tests.py compares the S00 640
converter against the locked original instructions, keeps the unsupported-colour negative
controls, and replays freeze/move/unfreeze on the bare host and in enhanced mode
(evidence/enhanced-mode/map-frozen-dirty-cells.md). It runs against build/current/portable.
"""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / 'build/current/portable'


class FrozenMapCache(unittest.TestCase):
    @unittest.skipUnless((BUILD / 'report.json').is_file(), 'native build absent (python portable/build.py --out build/current/portable)')
    def test_frozen_map_cache(self):
        parent = ROOT / 'build/scratch'
        parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='mapff-', dir=parent) as scratch:
            run = subprocess.run([sys.executable,
                                  str(ROOT / 'portable/whole_program/platform/tests/run_map_frozen_cache_tests.py'),
                                  '--build', str(BUILD), '--out', str(Path(scratch) / 'run'), '--gui'],
                                 cwd=ROOT, capture_output=True, text=True, timeout=900)
            self.assertEqual(run.returncode, 0, run.stdout[-4000:] + run.stderr[-4000:])


if __name__ == '__main__':
    unittest.main()
