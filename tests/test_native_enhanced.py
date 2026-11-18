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

    @unittest.skipUnless((BUILD / 'report.json').is_file(), 'native build absent (python portable/build.py --out build/current/portable)')
    def test_enhanced_native_content(self):
        """Native content windows (Map, Yard family, Behavior/Caste, History, Info, Status): portable/tests/enhanced/content.py."""
        parent = ROOT / 'build/scratch'
        parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='enc-', dir=parent) as scratch:
            run = subprocess.run([sys.executable, str(ROOT / 'portable/tests/enhanced/content.py'),
                                  '--build', str(BUILD), '--out', str(Path(scratch) / 'r')],
                                 cwd=ROOT, capture_output=True, text=True, timeout=1200)
            self.assertEqual(run.returncode, 0, run.stdout[-4000:] + run.stderr[-4000:])

    @unittest.skipUnless((BUILD / 'report.json').is_file(), 'native build absent (python portable/build.py --out build/current/portable)')
    def test_enhanced_proximity_menus(self):
        """Native ant/queen/spider/scent/tools/magnify menus deliver the source choice: portable/tests/enhanced/menus.py."""
        parent = ROOT / 'build/scratch'
        parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='enm-', dir=parent) as scratch:
            run = subprocess.run([sys.executable, str(ROOT / 'portable/tests/enhanced/menus.py'),
                                  '--build', str(BUILD), '--out', str(Path(scratch) / 'r')],
                                 cwd=ROOT, capture_output=True, text=True, timeout=2400)
            self.assertEqual(run.returncode, 0, run.stdout[-4000:] + run.stderr[-4000:])

    @unittest.skipUnless((BUILD / 'report.json').is_file(), 'native build absent (python portable/build.py --out build/current/portable)')
    def test_enhanced_presentation(self):
        """Start flow without world windows, transparent map icons, allocation windows complete on their first frame: portable/tests/enhanced/presentation.py."""
        parent = ROOT / 'build/scratch'
        parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='enp-', dir=parent) as scratch:
            run = subprocess.run([sys.executable, str(ROOT / 'portable/tests/enhanced/presentation.py'),
                                  '--build', str(BUILD), '--out', str(Path(scratch) / 'r')],
                                 cwd=ROOT, capture_output=True, text=True, timeout=1800)
            self.assertEqual(run.returncode, 0, run.stdout[-4000:] + run.stderr[-4000:])

    @unittest.skipUnless((BUILD / 'report.json').is_file(), 'native build absent (python portable/build.py --out build/current/portable)')
    def test_enhanced_minimap(self):
        """MAP button popup: click/drag/cancel and every edge reach the source loop (Quick Game; all modes take ~37 min)."""
        parent = ROOT / 'build/scratch'
        parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='enmm-', dir=parent) as scratch:
            run = subprocess.run([sys.executable, str(ROOT / 'portable/tests/enhanced/minimap.py'),
                                  '--build', str(BUILD), '--out', str(Path(scratch) / 'r'), '--modes', 'quick'],
                                 cwd=ROOT, capture_output=True, text=True, timeout=1800)
            self.assertEqual(run.returncode, 0, run.stdout[-4000:] + run.stderr[-4000:])

    @unittest.skipUnless((BUILD / 'report.json').is_file(), 'native build absent (python portable/build.py --out build/current/portable)')
    def test_enhanced_ui_scale(self):
        """Options > UI Scale and --ui-scale: full panel clients, hit-tests and source state at every scale: portable/tests/enhanced/ui_scale.py."""
        parent = ROOT / 'build/scratch'
        parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='enu-', dir=parent) as scratch:
            run = subprocess.run([sys.executable, str(ROOT / 'portable/tests/enhanced/ui_scale.py'),
                                  '--build', str(BUILD), '--out', str(Path(scratch) / 'r')],
                                 cwd=ROOT, capture_output=True, text=True, timeout=1200)
            self.assertEqual(run.returncode, 0, run.stdout[-4000:] + run.stderr[-4000:])

    @unittest.skipUnless((BUILD / 'report.json').is_file(), 'native build absent (python portable/build.py --out build/current/portable)')
    def test_enhanced_classic_look(self):
        """Options > Look (Classic/Native): menu and caption fit, overflow placement, persistence: portable/tests/enhanced/classic.py."""
        parent = ROOT / 'build/scratch'
        parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='encl-', dir=parent) as scratch:
            run = subprocess.run([sys.executable, str(ROOT / 'portable/tests/enhanced/classic.py'),
                                  '--build', str(BUILD), '--out', str(Path(scratch) / 'r')],
                                 cwd=ROOT, capture_output=True, text=True, timeout=1200)
            self.assertEqual(run.returncode, 0, run.stdout[-4000:] + run.stderr[-4000:])

    @unittest.skipUnless((BUILD / 'report.json').is_file(), 'native build absent (python portable/build.py --out build/current/portable)')
    def test_enhanced_control_sweep(self):
        """Every panel control and menu item leaves the game visible and interactive (Quick Game; each mode takes ~75 min)."""
        parent = ROOT / 'build/scratch'
        parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='ens-', dir=parent) as scratch:
            run = subprocess.run([sys.executable, str(ROOT / 'portable/tests/enhanced/sweep.py'),
                                  '--build', str(BUILD), '--out', str(Path(scratch) / 'r'), '--modes', 'quick'],
                                 cwd=ROOT, capture_output=True, text=True, timeout=7200)
            self.assertEqual(run.returncode, 0, run.stdout[-4000:] + run.stderr[-4000:])


if __name__ == '__main__':
    unittest.main()
