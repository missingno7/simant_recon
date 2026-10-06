from pathlib import Path
import importlib.util
import json
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "fileselect_domain", ROOT / "evidence/canonical/filename-domain/domain_probe.py")
PROBE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PROBE)


class FileSelectDomainTests(unittest.TestCase):
    def test_supported_capacities_fit_and_contrasts_exceed(self):
        facts = PROBE.check()
        self.assertTrue(all(row["fits"] for row in facts["supported_capacities"]))
        tight = {row["write"]: row["bytes"] for row in facts["supported_capacities"]}
        self.assertEqual(tight["initial path+incoming name into buf"], 80)
        self.assertEqual(set(facts["negative_contrasts"]), {
            "incoming_name_strlen_47", "directory_33_chars",
            "directory_66_chars_inherited", "listed_entries_200"})
        self.assertTrue(all(facts["negative_contrasts"].values()))

    def _mutated(self, old, new):
        program = json.loads((ROOT / "src/program.json").read_text())
        raw = (ROOT / PROBE.SOURCE).read_bytes()
        self.assertEqual(raw.count(old), 1)
        changed = raw.replace(old, new)
        next(m for m in program["modules"] if m["source"] == PROBE.SOURCE)["source_sha256"] = PROBE.sha(changed)
        return program, {PROBE.SOURCE: changed}

    def test_smaller_buffer_is_rejected(self):
        program, overrides = self._mutated(b"char buf[80];", b"char buf[70];")
        with self.assertRaises(AssertionError):
            PROBE.collect(program, overrides)

    def test_larger_listing_limit_is_rejected(self):
        program, overrides = self._mutated(b"count >= 200 - s_2968", b"count >= 300 - s_2968")
        with self.assertRaises(AssertionError):
            PROBE.collect(program, overrides)

    def test_removed_redraw_clear_is_rejected(self):
        program, overrides = self._mutated(b"*name = fname[0] = 0;", b"fname[0] = 0;")
        with self.assertRaises(AssertionError):
            PROBE.collect(program, overrides)


if __name__ == "__main__":
    unittest.main()
