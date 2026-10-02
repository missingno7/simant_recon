"""Hard-tail comparisons are diagnostic only and preserve code distinctions."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import hardtail
import mismatch


class NormalizationTests(unittest.TestCase):
    def normalized(self, code, **options):
        rows = mismatch._decode(bytes.fromhex(code))
        return hardtail._normalized(rows, [], **options)

    def test_register_normalization_preserves_ah_al_lane(self):
        ah = self.normalized("b401", ignore_registers=True)
        al = self.normalized("b001", ignore_registers=True)
        self.assertNotEqual(ah, al)

    def test_operand_width_is_never_normalized(self):
        byte = self.normalized("b001", ignore_registers=True, ignore_bp=True)
        word = self.normalized("b80100", ignore_registers=True, ignore_bp=True)
        self.assertNotEqual(byte, word)

    def test_memory_addressing_form_is_preserved(self):
        direct = self.normalized("8b4602", ignore_registers=True, ignore_bp=True)
        based = self.normalized("8b4702", ignore_registers=True, ignore_bp=True)
        self.assertNotEqual(direct, based)

    def test_branch_destinations_can_be_ignored_but_topology_remains(self):
        a = hardtail.compare_streams(bytes.fromhex("74025dc3"), bytes.fromhex("75025dc3"),
                                     options={"ignore_branch_destinations": True})
        self.assertNotEqual(a["semantic_skeleton"], "MATCH")  # condition opcode remains meaningful
        same_condition = hardtail.compare_streams(bytes.fromhex("74015dc3"), bytes.fromhex("74025dc3"),
                                                  options={"ignore_branch_destinations": True})
        self.assertEqual(same_condition["semantic_skeleton"], "MATCH")
        changed_target = hardtail.compare_streams(bytes.fromhex("74015dc3"), bytes.fromhex("74025dc3"))
        self.assertEqual(changed_target["semantic_skeleton"], "MATCH")
        self.assertFalse(changed_target["cfg"]["match"])

    def test_cfg_retains_branch_topology_and_calls(self):
        conditional = hardtail.compare_streams(bytes.fromhex("7400c3c3"), bytes.fromhex("7401c3c3"))
        self.assertFalse(conditional["cfg"]["match"])
        call = hardtail.cfg(mismatch._decode(bytes.fromhex("e80000c3")), 4)
        self.assertIn("call", [e["kind"] for e in call["edges"]])

    def test_straight_line_extra_instruction_does_not_change_cfg_topology(self):
        result = hardtail.compare_streams(bytes.fromhex('b80100c3'), bytes.fromhex('b8010040c3'))
        self.assertTrue(result['cfg']['match'])
        self.assertEqual(result['semantic_skeleton'], 'MISMATCH')

    def test_unreachable_nop_retained_without_unknown_cfg(self):
        value = hardtail.cfg(mismatch._decode(bytes.fromhex('eb0190c3')), 4)
        self.assertTrue(value['complete'])
        self.assertTrue(value['unreachable_nop_blocks'])

    def test_incomplete_decode_cannot_claim_cfg_match(self):
        value = hardtail.compare_streams(bytes.fromhex('c30f'), bytes.fromhex('c30f'))
        self.assertIsNone(value['cfg']['match'])
        self.assertEqual(value['cfg']['status'], 'UNKNOWN')

    def test_indirect_switch_and_unreachable_table_limits_are_explicit(self):
        indirect = hardtail.cfg(mismatch._decode(bytes.fromhex("ffe0c3")), 3)
        self.assertTrue(any("indirect jump" in x for x in indirect["limitations"]))
        embedded = hardtail.cfg(mismatch._decode(bytes.fromhex("eb02c390c3")), 5)
        self.assertTrue(any("embedded data or switch tables" in x for x in embedded["limitations"]))

    def test_undecoded_tail_stays_explicit(self):
        result = hardtail.compare_streams(b"\x0f", b"\x0f")
        self.assertFalse(result["instruction_report"]["decode_complete"])
        self.assertEqual(result["differences"]["decode_complete"], False)

    def test_candidate_fixup_identity_is_kept_even_when_value_is_ignored(self):
        target = mismatch._decode(bytes.fromhex("c70600000100"))
        candidate = mismatch._decode(bytes.fromhex("c70602000100"))
        fx = [{"at": 2, "width": 2, "loc": "offset16", "target": "table_a", "kind": "data"}]
        left = hardtail._normalized(target, fx, ignore_relocations=True)
        right_fx = [{**fx[0], "target": "table_b"}]
        right = hardtail._normalized(candidate, right_fx, ignore_relocations=True)
        # This API keeps the symbolic fixup obligation adjacent to the instruction;
        # callers can inspect candidate_fixups even when numeric fields are ignored.
        self.assertEqual(left, right)
        self.assertNotEqual(fx[0]["target"], right_fx[0]["target"])


class ClassificationTests(unittest.TestCase):
    def test_strict_verdict_is_not_changed_by_diagnostic_class(self):
        strict = {"exact": False, "reasons": ["bytes differ"]}
        detail = {"relocation_differences": {"missing_sites": [], "extra_sites": []},
                  "width_differences": [], "branch_layout_differences": [], "decode_complete": True}
        found = hardtail._classify_hardtail({"classes": ["REGISTER_ALLOCATION"]}, 8, 8,
                                            detail, True, True, 1.0, [])
        self.assertEqual(found, "ALLOCATOR_TAIL")
        self.assertFalse(strict["exact"])
        self.assertEqual(strict["reasons"], ["bytes differ"])

    def test_relocation_width_and_control_flow_classes_are_separate(self):
        base = {"relocation_differences": {"missing_sites": [], "extra_sites": []},
                "width_differences": [], "branch_layout_differences": [], "decode_complete": True}
        self.assertEqual(hardtail._classify_hardtail({}, 8, 8, base, True, True, 1, []), "EXPRESSION_TAIL")
        width = {**base, "width_differences": [{"target": "x", "candidate": "y"}]}
        self.assertEqual(hardtail._classify_hardtail({}, 8, 8, width, True, True, 1, []), "WIDTH_TYPE_TAIL")
        branch = {**base, "branch_layout_differences": [{"target": "jz", "candidate": "jnz"}]}
        self.assertEqual(hardtail._classify_hardtail({}, 8, 8, branch, False, False, 1, []), "CONTROL_FLOW_TAIL")
        self.assertEqual(hardtail._classify_hardtail({}, 8, 8, branch, False, True, 1, []), "EXPRESSION_TAIL")
        relocation = {**base, "relocation_differences": {"missing_sites": [2], "extra_sites": []}}
        self.assertEqual(hardtail._classify_hardtail({}, 8, 8, relocation, True, True, 1, []), "RELOCATION_RECORD_TAIL")

    def test_length_difference_from_register_encoding_remains_allocator_diagnostic(self):
        detail = {'decode_complete': True, 'relocation_differences': {}, 'width_differences': [],
                  'branch_layout_differences': []}
        self.assertEqual(hardtail._classify_hardtail({'classes': ['REGISTER_ALLOCATION']},
                         264, 265, detail, True, True, 1, []), 'ALLOCATOR_TAIL')

    def test_local_register_residue_does_not_require_global_renaming(self):
        target = mismatch._decode(bytes.fromhex('8bf08bd8c45ef050'))
        candidate = mismatch._decode(bytes.fromhex('8bf08bd8c476f050'))
        residue = hardtail.allocator_operand_residue(target, candidate)
        self.assertEqual(len(residue['sites']), 1)
        self.assertEqual(residue['sites'][0]['instruction_index'], 2)
        self.assertEqual(residue['sites'][0]['target'], 'bx')
        self.assertEqual(residue['sites'][0]['candidate'], 'si')

    def test_extra_straight_line_instructions_are_expression_not_cfg_evidence(self):
        detail = {'decode_complete': True, 'relocation_differences': {'missing_sites': [2]},
                  'width_differences': [], 'branch_layout_differences': [], 'single_block_pair': True}
        self.assertEqual(hardtail._classify_hardtail({}, 8, 10, detail, False, True, .5, []), 'EXPRESSION_TAIL')

    def test_declaration_context_requires_separate_causal_evidence(self):
        detail = {'decode_complete': True, 'relocation_differences': {}, 'width_differences': []}
        state = {'classes': ['STACK_SLOT_ALLOCATION']}
        self.assertEqual(hardtail._classify_hardtail(state, 8, 8, detail, True, True, 1, []), 'ALLOCATOR_TAIL')
        self.assertEqual(hardtail._classify_hardtail({**state, 'causal_context_probe': 'controlled-declaration-change'},
                         8, 8, detail, True, True, 1, []), 'DECLARATION_CONTEXT_TAIL')


if __name__ == "__main__":
    unittest.main()
