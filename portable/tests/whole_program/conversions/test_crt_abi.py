from __future__ import annotations

import ast
import json
from pathlib import Path
import re
import sys
import unittest

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from portable.whole_program.conversions.crt_abi import adapt


class CrtAbiConversionTests(unittest.TestCase):
    def adapt_path(self, rel):
        return adapt((ROOT / rel).read_text(encoding="latin1"), rel)

    def test_error_table_names_are_redirected_without_changing_uses(self):
        for rel in ("src/root/m15F8.c", "src/root/m1A28.c", "src/S09/m35F5.c"):
            with self.subTest(rel=rel):
                converted, ledger = self.adapt_path(rel)
                self.assertIn('#include "portable/whole_program/platform/crt_abi.h"', converted)
                self.assertNotRegex(converted, r"\bsys_errlist\b")
                self.assertIn("sim_sys_errlist", converted)
                self.assertGreater(ledger["changes"]["sys_errlist_names"], 0)

    def test_ascii_ctype_accesses_are_narrowed_and_harderr_is_registered(self):
        root, root_ledger = self.adapt_path("src/root/m1C62.c")
        self.assertNotRegex(root, r"\b_ctype\b")
        self.assertEqual(root_ledger["changes"]["ctype_lower_uses"], 2)
        self.assertIn("if (sim_msc_ctype_is_lower_ascii((unsigned char)c))", root)
        self.assertIn("switch ((sim_msc_ctype_is_lower_ascii((unsigned char)c)) ?", root)
        self.assertEqual(root_ledger["changes"]["sys_nerr_names"], 2)
        s23, s23_ledger = self.adapt_path("src/S23/m39C7.c")
        self.assertNotRegex(s23, r"\b_ctype\b")
        self.assertEqual(s23_ledger["changes"]["ctype_lower_uses"], 1)
        s20, harderr = self.adapt_path("src/S20/m39F1.c")
        self.assertNotRegex(s20, r"\b_harderr\b")
        self.assertIn("sim_crt_harderr_install(f_208F_058B);", s20)
        self.assertEqual(harderr["changes"]["harderr_registration_calls"], 1)

    def test_adapter_rejects_unknown_paths_and_ctype_shape_drift(self):
        with self.assertRaises(ValueError):
            adapt("int x;", "src/root/unrelated.c")
        source = (ROOT / "src/root/m1C62.c").read_text(encoding="latin1")
        with self.assertRaises(ValueError):
            adapt(source.replace("_ctype[c + 1] & 2", "_ctype[c] & 2", 1),
                  "src/root/m1C62.c")

    def test_provider_text_and_lowercase_domain_match_original_memory_observation(self):
        observation = json.loads((ROOT / "portable/tests/whole_program/platform/evidence/"
                                  "crt-abi-v2/original-runtime-observation.json").read_text())
        provider = (ROOT / "portable/whole_program/platform/crt_abi.c").read_text()
        block = re.search(r"char \*sim_sys_errlist\[38\] = \{(.*?)\n\};", provider, re.S)
        self.assertIsNotNone(block)
        texts = [ast.literal_eval(item) for item in
                 re.findall(r'"(?:\\.|[^"\\])*"', block.group(1))]
        self.assertEqual(texts, [entry["text"] for entry in observation["sys_errlist"]["entries"]])
        self.assertEqual(observation["sys_nerr"]["value"], 37)
        self.assertEqual(observation["ctype"]["ascii_lowercase_bytes"],
                         list("abcdefghijklmnopqrstuvwxyz"))
        self.assertIn("return 3;", (ROOT / "src/root/m208F.c").read_text(encoding="latin1"))


if __name__ == "__main__":
    unittest.main()
