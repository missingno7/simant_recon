from __future__ import annotations

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from portable.whole_program.conversions.findindex_native_guard import (
    GUARD, REVIEWED_BODY_SHA256, REVIEWED_MODULE_SHA256,
    adapt_dos_source, adapt_host_source, adapt_whole_source,
)
from portable.tools.whole_program import function_heads


class FindIndexGuardConversionTests(unittest.TestCase):
    def setUp(self):
        self.source = (ROOT / "evidence/behavior/functions/FindIndex/module.c").read_text(
            encoding="latin1")

    def test_reviewed_function_and_guard_location_are_pinned(self):
        host, provenance = adapt_host_source(self.source)
        self.assertEqual(provenance["reviewed_module_sha256"], REVIEWED_MODULE_SHA256)
        self.assertEqual(provenance["reviewed_body_sha256"], REVIEWED_BODY_SHA256)
        assignment = host.index("fd_50F6_3952 = &fd_50F6_3958[db].index[fd_50F6_3956];")
        guard = host.index(GUARD)
        final_field_read = host.rindex("if (fd_50F6_3952->id == id")
        self.assertLess(assignment, guard)
        self.assertLess(guard, final_field_read)
        self.assertIn("int16_t id", host)
        self.assertIn("int16_t kind", host)

    def test_dos_control_uses_reviewed_function_and_retains_module_declarations(self):
        candidate, provenance = adapt_dos_source(self.source)
        self.assertIn(GUARD, candidate)
        self.assertIn("typedef struct {", candidate)
        self.assertIn("FindIndex", candidate)
        self.assertEqual(provenance["compiled_scope"],
                         "reviewed FindIndex body only; source ABI declarations retained")
        self.assertNotIn("void far OpenIndex", candidate)

    def test_source_and_body_mutations_fail_closed(self):
        with self.assertRaises(ValueError):
            adapt_host_source(self.source.replace(
                "fd_50F6_3956 = mid + 1;", "fd_50F6_3956 = mid + 2;", 1))
        with self.assertRaises(ValueError):
            adapt_host_source(self.source.replace(
                "fd_50F6_3952 = &fd_50F6_3958[db].index[fd_50F6_3956];",
                "fd_50F6_3952 = &fd_50F6_3958[db].index[fd_50F6_3956];\n    " + GUARD,
                1))

    def test_whole_module_adapter_validates_two_identities_and_changes_only_target(self):
        canonical = (ROOT / "src/root/m1986.c").read_text(encoding="latin1")
        canonical_head = next(f for f in function_heads(canonical) if f["name"] == "FindIndex")
        reviewed_head = next(f for f in function_heads(self.source) if f["name"] == "FindIndex")
        overlay = (canonical[:canonical_head["start"]] +
                   self.source[reviewed_head["start"]:reviewed_head["end"]] +
                   canonical[canonical_head["end"]:])
        guarded, provenance = adapt_whole_source(overlay)
        self.assertTrue(provenance["only_findindex_body_changed"])
        self.assertEqual(guarded.count(GUARD), 1)
        self.assertEqual(guarded.replace("\n    " + GUARD, "", 1), overlay)
        with self.assertRaises(ValueError):
            adapt_whole_source(overlay.replace("fd_50F6_3956 = mid + 1;",
                                               "fd_50F6_3956 = mid + 2;", 1))
        with self.assertRaises(ValueError):
            adapt_whole_source(overlay, module_path="src/root/m1986-copy.c")


if __name__ == "__main__":
    unittest.main()
