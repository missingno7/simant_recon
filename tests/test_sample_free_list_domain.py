from pathlib import Path
import importlib.util
import json
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "sample_free_list", ROOT / "evidence/canonical/sample-free-list/replay.py")
PROBE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PROBE)


class SampleFreeListDomainTests(unittest.TestCase):
    def test_supported_extent_and_original_boundary(self):
        facts = PROBE.check()
        self.assertEqual(facts["owner"]["entries"], 39)
        self.assertEqual(facts["owner"]["extent_bytes"], 156)
        controls = facts["original_boundary_controls"]
        self.assertEqual([c["store_completed"] for c in controls],
                         [True, True, False, True])

    def test_shipped_mode6_streams_do_not_issue_DAC_notes(self):
        facts = json.loads((ROOT / "evidence/canonical/sample-free-list/facts.json").read_text())
        self.assertEqual(facts["song_control"], {
            "metadata_records": 33,
            "distinct_streams": 30,
            "max_tracks": 10,
            "mode6_DAC_note_ons": 0,
        })


if __name__ == "__main__":
    unittest.main()
