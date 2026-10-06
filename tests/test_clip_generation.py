"""Clip-generation boundary: recomputed bound, controls and rejection mutations."""
from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "src/program.json").is_file())
PACKAGE = ROOT / "evidence/canonical/clip-generation"
sys.path.insert(0, str(PACKAGE))
_SPEC = importlib.util.spec_from_file_location("clip_generation_probe", PACKAGE / "probe.py")
probe = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(probe)


def read_source(path: str) -> str:
    return (ROOT / path).read_text(encoding="latin1")


class ClipGenerationPackageTests(unittest.TestCase):
    def reject_virtual_source(self, path: str, changed: str) -> None:
        with self.assertRaises((AssertionError, ValueError)):
            probe.check_source_overrides({path: changed})

    def test_recomputed_package_facts_and_original_controls(self) -> None:
        facts = probe.check()
        self.assertEqual(facts["window_bound"]["maximum_window_stack"], 9)
        self.assertEqual(facts["window_bound"]["C099_records_before_sentinel"], 172)
        self.assertEqual(facts["window_bound"]["maximum_records_plus_sentinel"], 173)
        self.assertEqual(facts["producer_and_allocator_proof"]["traversal_and_offsets"]["write_end_exclusive"], 10204)
        self.assertTrue(facts["original_instruction_controls"]["replay_results_recomputed"])

    def test_removing_256_precheck_is_rejected(self) -> None:
        path = "src/root/m1E57.c"
        source = read_source(path)
        old = ('        if ((n = p - buf) >= 256)\n'
               '            Punt("CL074:Temp clip overflow in SubExclude");\n')
        changed = source.replace(old, "", 1)
        self.assertNotEqual(changed, source)
        self.reject_virtual_source(path, changed)

    def test_moving_check_before_generation_is_rejected(self) -> None:
        path = "src/root/m1E57.c"
        source = read_source(path)
        old = ('        for (p = buf; g_5AAC->top != (int)0x8000; g_5AAC++)\n'
               '            p = f_1D8E_003F(g_5AAC, r, 0L, p);\n'
               '        if ((n = p - buf) >= 256)\n'
               '            Punt("CL074:Temp clip overflow in SubExclude");\n')
        new = ('        p = buf;\n'
               '        if ((n = p - buf) >= 256)\n'
               '            Punt("CL074:Temp clip overflow in SubExclude");\n'
               '        for (; g_5AAC->top != (int)0x8000; g_5AAC++)\n'
               '            p = f_1D8E_003F(g_5AAC, r, 0L, p);\n')
        changed = source.replace(old, new, 1)
        self.assertNotEqual(changed, source)
        self.reject_virtual_source(path, changed)

    def test_second_longer_08f5_caller_is_rejected(self) -> None:
        path = "src/root/m0250.c"
        source = read_source(path)
        added = ('\nvoid far clip_test_longer_08f5_input(void)\n'
                 '{\n'
                 '    struct Rect rects[5];\n'
                 '    rects[0].top = 0;\n'
                 '    rects[1].top = 0;\n'
                 '    rects[2].top = 0;\n'
                 '    rects[3].top = 0;\n'
                 '    rects[4].top = 0x8000;\n'
                 '    f_1E57_08F5(rects);\n'
                 '}\n')
        self.reject_virtual_source(path, source + added)

    def test_allocator_payload_offset_mutation_is_rejected(self) -> None:
        path = "src/root/m171C.c"
        source = read_source(path)
        changed = source.replace("(long)b + 0x20000L", "(long)b + 0x30000L", 1)
        self.assertNotEqual(changed, source)
        self.reject_virtual_source(path, changed)


if __name__ == "__main__":
    unittest.main()
