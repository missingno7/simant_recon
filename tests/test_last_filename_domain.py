from pathlib import Path
import importlib.util
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "last_filename", ROOT / "evidence/canonical/last-filename/replay.py")
PROBE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PROBE)


class LastFilenameDomainTests(unittest.TestCase):
    def test_owner_and_fixed_object_domain(self):
        facts = PROBE.check()
        self.assertEqual(facts["owner"]["extent_bytes"], 100)
        self.assertEqual(facts["safe_selector_result"]["returned_name_bytes"], 79)

    def test_path_overflow_remains_a_gate(self):
        facts = PROBE.check()
        self.assertEqual(facts["path_contrast"]["positive_required_bytes"], 67)
        self.assertEqual(facts["path_contrast"]["negative_required_bytes"], 69)
        self.assertEqual(facts["path_contrast"]["negative_gate"],
                         "filename-selector-local-capacity")


if __name__ == "__main__":
    unittest.main()
