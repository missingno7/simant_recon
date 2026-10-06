from pathlib import Path
import importlib.util
import json
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "mono_vga", ROOT / "evidence/canonical/monochrome-owner/mode_probe.py")
PROBE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PROBE)


class MonochromeVgaDomainTests(unittest.TestCase):
    def test_supported_mode_excludes_mono_consumers(self):
        facts = PROBE.check()
        self.assertEqual(facts["supported_access_bytes"], 0)
        self.assertEqual(facts["linkage_owner_bytes"], 1)
        self.assertEqual(facts["historical_extent"], "UNCLAIMED")

    def test_original_odd_mode_control_selects_mono_body(self):
        facts = json.loads((ROOT / "evidence/canonical/monochrome-owner/mode-facts.json").read_text())
        self.assertEqual(facts["original_mini_controls"], [
            {"mode": 8, "selected": "o00_3126_06A3"},
            {"mode": 7, "selected": "o01_328E_01D5"},
        ])


if __name__ == "__main__":
    unittest.main()
