from pathlib import Path
import copy
import importlib.util
import json
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "clip_owner", ROOT / "evidence/canonical/clip-owner/replay.py")
PROBE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PROBE)


class ClipOwnerTests(unittest.TestCase):
    def test_owner_extent_and_original_boundary(self):
        facts = PROBE.check()
        self.assertEqual(facts["owner"]["extent_bytes"], 2048)
        positive, fatal, returning = facts["original_boundary_controls"]
        self.assertEqual(positive["destination_bytes_written"], 2048)
        self.assertEqual(fatal["destination_bytes_written"], 0)
        self.assertTrue(fatal["temporary_overrun_before_fatal"])
        self.assertEqual(returning["beyond_owner_bytes"], 8)

    def test_smaller_owner_is_rejected(self):
        program = json.loads((ROOT / "src/program.json").read_text())
        row = next(m for m in program["modules"] if m["key"] == PROBE.OWNER_KEY)
        smaller = copy.deepcopy(program)
        target = next(m for m in smaller["modules"] if m["key"] == PROBE.OWNER_KEY)
        target["storage_contract"]["communals"][0].update(length=2040, count=255)
        with self.assertRaises(AssertionError):
            PROBE.collect(smaller, run_original=False)
        source = (ROOT / row["source"]).read_bytes().replace(b"[256]", b"[255]")
        shrunk = copy.deepcopy(program)
        next(m for m in shrunk["modules"] if m["key"] == PROBE.OWNER_KEY)[
            "source_sha256"] = PROBE.sha(source)
        with self.assertRaises(AssertionError):
            PROBE.collect(shrunk, {row["source"]: source}, run_original=False)

    def test_unchecked_destination_copy_is_rejected(self):
        path = "src/root/m1E57.c"
        program = json.loads((ROOT / "src/program.json").read_text())
        raw = (ROOT / path).read_bytes()
        changed = raw.replace(b'Punt("CL074:Temp clip overflow in SubExclude")', b";", 1)
        self.assertNotEqual(raw, changed)
        mutated = copy.deepcopy(program)
        row = next(m for m in mutated["modules"] if m["source"] == path)
        row["source_sha256"] = PROBE.sha(changed)
        with self.assertRaises(AssertionError):
            PROBE.collect(mutated, {path: changed}, run_original=False)


if __name__ == "__main__":
    unittest.main()
