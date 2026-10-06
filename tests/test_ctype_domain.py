"""Acceptance tests for evidence/canonical/ctype-domain/probe.py."""
from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path


def load_probe():
    here = Path(__file__).resolve()
    probe_path = next((p / "probe.py" for p in here.parents if (p / "probe.py").is_file()), None)
    if probe_path is None:
        root = next(p for p in here.parents if (p / "src/program.json").is_file())
        probe_path = root / "evidence/canonical/ctype-domain/probe.py"
    spec = importlib.util.spec_from_file_location("ctype_domain_probe_under_test", probe_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


probe = load_probe()
ROOT = next(p for p in Path(__file__).resolve().parents if (p / "src/program.json").is_file())


class CtypeDomainReplayTests(unittest.TestCase):
    def test_reviewed_facts_replay(self):
        result = probe.check()
        self.assertEqual(result["site_census"]["count"], 11)
        self.assertTrue(result["source_assumptions"]["m1C62_170_lemma"]["unobservable"])

    def test_removing_s10_high_key_guard_fails(self):
        path = "src/S10/m35F5.c"
        original = (ROOT / path).read_text(encoding="latin1")
        old = "if (!(key & 0x800) && islower(key))"
        self.assertIn(old, original)
        mutated = original.replace(old, "if (islower(key))", 1)
        with self.assertRaisesRegex(ValueError, "S10 lower-key guard"):
            probe.collect(source_overrides={path: mutated})

    def test_negative_switch_case_breaks_unobservability_lemma(self):
        path = "src/root/m1C62.c"
        original = (ROOT / path).read_text(encoding="latin1")
        old = "case 'C':"
        self.assertIn(old, original)
        # D1 becomes -47 through the signed-byte reader, so this added case is reachable.
        mutated = original.replace(old, "case 'C': case -47:", 1)
        with self.assertRaisesRegex(ValueError, "negative case label"):
            probe.collect(source_overrides={path: mutated})

    def test_renderer_rewind_only_prefix_high_byte_fails(self):
        text = b"x(\xD1abcDEFz"
        runs = [[0, 0, 0, 0, 0], [4, 0, 0, 0, 0x100], [8, 0, 0, 0, 0]]
        ideal = probe.renderer_style_spans(text, runs, expand_left=False)
        self.assertFalse(any(row["ideal_high_byte_counts"] for row in ideal))
        with self.assertRaisesRegex(ValueError, "conservative renderer span contains a high byte"):
            probe.require_renderer_spans_ascii(text, runs, "synthetic-rewind-prefix")
        control = probe.renderer_rewind_negative_control()
        self.assertTrue(control["expanded_span_fails_check"])

    def test_probe_accepts_resolved_and_unresolved_ledger_states(self):
        program = json.loads((ROOT / "src/program.json").read_text(encoding="utf8"))
        dos = program["dos"]
        gate = next(row for row in dos["resolved_domain_contracts"]
                    if row["id"] == "ctype-out-of-range-index-layout")
        debt = next(row for row in dos.get("resolved_data", []) if row["id"] == "dgroup_79f0")
        self.assertEqual(gate["domain"], dos["supported_execution_domain"]["id"])
        current = probe.check()
        self.assertEqual(current["gate"]["ledger_state"], "UNRESOLVED_OR_RESOLVED_SUPPORTED_DOMAIN")
        self.assertEqual(current["data_debt"]["bytes"], 14)
        dos["resolved_domain_contracts"].remove(gate)
        dos["semantic_gates"].append({**gate, "status": "UNRESOLVED"})
        dos["resolved_data"].remove(debt)
        dos["unresolved_data"].append(debt)
        reverted = probe.collect(program_override=program)
        self.assertEqual(reverted["data_debt"]["bytes"], 14)


if __name__ == "__main__":
    unittest.main()
