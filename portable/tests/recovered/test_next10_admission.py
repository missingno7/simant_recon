"""Negative controls for the one reviewed History profile extension."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from portable.tools.profile_next10 import validate_next10
from portable.tools.profile_next9 import validate_next9


class Next10Admission(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.profile = json.loads((ROOT / "build/workers/recovered_source_next10/generated/provenance.json").read_text())

    def test_current_parent_and_every_actual_input(self):
        parent, pins = validate_next10(self.profile)
        validate_next9(parent)
        for path, digest in pins.items():
            with self.subTest(path=path):
                self.assertEqual(hashlib.sha256((ROOT / path).read_bytes()).hexdigest(), digest)
        self.assertEqual(len(self.profile["modules"]), 25)
        changed = [a["name"] for a, b in zip(self.profile["modules"], parent["modules"])
                   if a["generated_sha256"] != b["generated_sha256"]]
        self.assertEqual(changed, ["S24_m39C7"])

    def test_unreviewed_metadata_is_rejected(self):
        mutations = [
            lambda p: p.update(versioned_profile_extension_next11={}),
            lambda p: p["recovered_state"].update(header_sha256="0" * 64),
            lambda p: p["versioned_profile_extension_next10"].update(parent_profile="Next8"),
            lambda p: p["versioned_profile_extension_next10"]["native_lowering"].update(new_expression="(4 - i) * 2"),
            lambda p: p["versioned_profile_extension_next10"]["snapshot_api"].update(exported_history_color_elements=20),
            lambda p: p["modules"][0].update(generated_sha256="0" * 64),
            lambda p: p["modules"][12]["compile"].update(lowered_object_sha256=p["modules"][12]["compile"]["next9_object_sha256"]),
            lambda p: p["modules"][12].update(generated=p["modules"][12]["generated"].replace("next10", "next9")),
            lambda p: p["modules"].pop(),
        ]
        for i, mutate in enumerate(mutations):
            with self.subTest(control=i):
                candidate = copy.deepcopy(self.profile)
                mutate(candidate)
                with self.assertRaises(SystemExit):
                    validate_next10(candidate)


if __name__ == "__main__":
    unittest.main()
