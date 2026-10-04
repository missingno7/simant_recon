"""Search must reproduce the verifier's module context before comparing bytes."""
import contextlib
import io
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import functions
import modules
import search


class SearchOptions(unittest.TestCase):
    def setUp(self):
        self.first = {"unit": "root", "seg": 0x10, "lang": "c",
                      "profile": "msc600ax", "flags": ["/AL", "/Oeg", "/Gs"],
                      "placements": {"CONST": {"seg": 0x55B3, "off": 12, "size": 2}}}
        self.later = {"unit": "root", "seg": 0x10, "origin": 0x20, "lang": "asm",
                      "profile": "masm510", "flags": [], "placements": {}}
        self.man = {"modules": {"root:0010": self.first, "root:0010@0020": self.later}}
        self.f = {"unit": "root", "seg": 0x10, "off": 0}

    def resolve(self, f=None, asm=False, profile=None, flags=None, placements=None):
        with patch.object(modules, "load_manifest", return_value=self.man):
            return search.options(f or self.f, asm, profile, flags, placements or {})

    def test_manifest_defaults_and_explicit_overrides(self):
        r = self.resolve()
        self.assertEqual(r["profile"], "msc600ax")
        self.assertEqual(r["flags"], ["/AL", "/Oeg", "/Gs"])
        self.assertEqual(r["placements"], {"CONST": {"seg": 0x55B3, "off": 12}})
        r = self.resolve(profile="msc600a", flags=["/AL", "/Od"],
                         placements={"CONST": {"seg": 0x55B3, "off": 14}})
        self.assertEqual(r["profile"], "msc600a")
        self.assertEqual(r["flags"], ["/AL", "/Od"])
        self.assertEqual(r["placements"]["CONST"]["off"], 14)
        self.assertEqual(self.first["placements"]["CONST"]["off"], 12)
        # Switching compiler generations should keep the module's experiment flags.
        self.assertEqual(self.resolve(profile="msc600a")["flags"], self.first["flags"])

    def test_empty_flags_are_an_explicit_override(self):
        self.assertEqual(self.resolve(flags=[])["flags"], [])

    def test_later_object_uses_its_own_options(self):
        f = {**self.f, "off": 0x25}
        r = self.resolve(f, asm=True)
        self.assertEqual(r["module"], "root:0010@0020")
        self.assertEqual(r["profile"], "masm510")
        self.assertEqual(r["flags"], [])
        self.assertEqual(r["placements"], {})

    def test_different_source_language_does_not_select_wrong_tool(self):
        f = {**self.f, "off": 0x25}
        with patch.object(functions, "profile_flags", return_value=["C-default"]):
            r = self.resolve(f)
        self.assertEqual(r["profile"], functions.DEFAULT_PROFILE)
        self.assertEqual(r["flags"], ["C-default"])
        with patch.object(functions, "profile_flags", return_value=["ASM-default"]):
            r = self.resolve(asm=True)
        self.assertEqual(r["profile"], "masm510")
        self.assertEqual(r["flags"], ["ASM-default"])

    def test_unrecorded_object_retains_profile_defaults(self):
        self.man = {"modules": {}}
        with patch.object(functions, "profile_flags", return_value=["default"]):
            r = self.resolve()
        self.assertEqual(r["profile"], functions.DEFAULT_PROFILE)
        self.assertEqual(r["flags"], ["default"])


class SearchCompilerControls(unittest.TestCase):
    def test_bare_search_matches_accepted_memory_peer_and_preserves_negative(self):
        # The same whole module has an accepted peer and an unclaimed six-byte residue.
        source = ROOT / "tests/fixtures/memory-near-repaired.c"
        with contextlib.redirect_stdout(io.StringIO()):
            peer = search.run("f_171C_2086", [source], None, None, None, {}, quiet=True)[0]
            target = search.run("f_171C_0CF4", [source], None, None, None, {}, quiet=True)[0]
        self.assertEqual(peer["status"], "EXACT", peer)
        self.assertEqual(peer["flags"], ["/AL", "/Oeg", "/Gs", "/Zi"])
        self.assertEqual(target["status"], "MISMATCH", target)
        self.assertEqual(target["unbound"], [])
        self.assertIn("6 differing", " ".join(target["reasons"]))

    def test_explicit_wrong_placement_remains_a_strict_failure(self):
        source = ROOT / "tests/fixtures/memory-near-repaired.c"
        m = modules.load_manifest()["modules"]["root:171C"]
        p = m["placements"]["_DATA"]
        with contextlib.redirect_stdout(io.StringIO()):
            row = search.run("f_171C_2086", [source], None, None, None,
                             {"_DATA": {"seg": p["seg"], "off": p["off"] + 2}}, quiet=True)[0]
        self.assertEqual(row["status"], "MISMATCH", row)


if __name__ == "__main__":
    unittest.main()
