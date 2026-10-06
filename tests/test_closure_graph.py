"""The experiment graph cannot silently omit debt or confer acceptance."""
import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import repository


class ClosureGraph(unittest.TestCase):
    def setUp(self):
        self.program = json.loads((ROOT / 'src/program.json').read_text())
        self.evidence = json.loads((ROOT / 'evidence/canonical/blockers.json').read_text())
        self.platform = json.loads((ROOT / 'portable/platform.json').read_text())

    def issues(self):
        result = []
        repository._check_closure_graph(self.program, self.evidence, self.platform, result)
        return {r['code'] for r in result}

    def test_current_graph_covers_every_active_family(self):
        self.assertEqual(self.issues(), set())

    def test_cycle_and_stale_owner_are_rejected(self):
        roots = self.program['dos']['closure_graph']['roots']
        roots[0]['depends_on'] = [roots[0]['id']]
        roots[0]['members']['imports'] = ['_invented_owner']
        self.assertIn('closure_graph_cycle', self.issues())
        self.assertIn('closure_graph_stale_leaf', self.issues())

    def test_new_debt_requires_a_root_and_reviewed_class(self):
        self.program['dos']['unresolved_data'].append({'id': 'new_debt', 'bytes': 1})
        self.assertIn('closure_graph_unmapped', self.issues())
        self.assertIn('closure_class', self.issues())

    def test_resolved_domain_cannot_lose_scope_or_conflict_with_open_gate(self):
        resolved = self.program['dos']['resolved_domain_contracts'][0]
        self.program['dos']['semantic_gates'].append(dict(resolved, status='UNRESOLVED'))
        self.program['dos']['supported_execution_domain']['premises'] = []
        issues = []
        repository._check_program(self.program, issues)
        self.assertIn('resolved_domain_contract', {r['code'] for r in issues})
        self.assertIn('supported_execution_domain', {r['code'] for r in issues})

    def test_classification_cannot_waive_preflight(self):
        sys.path.insert(0, str(ROOT))
        from dos.build import preflight_blockers
        gates = copy.deepcopy(self.program['dos']['semantic_gates']) or [
            dict(copy.deepcopy(self.program['dos']['resolved_domain_contracts'][0]), status='UNRESOLVED')]
        for row in gates:
            row['closure_class'] = 'HISTORICAL_LAYOUT'
        report = dict(errors=[], unresolved_semantic_gates=gates,
                      unresolved_data=[], translation_units=[])
        self.assertTrue(preflight_blockers(report))
        self.program['dos']['semantic_gates'] = gates
        self.assertIn('closure_class', self.issues())


if __name__ == '__main__':
    unittest.main()
