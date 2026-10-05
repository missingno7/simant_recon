"""Allocation scope and symbolic frame controls for the generic far-data probe."""
import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import probe


class ProbeBindingControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        stem = ROOT / 'evidence/codegen/FARSEG-2-communal-fixup-ownership'
        cls.spec = json.loads(stem.with_suffix('.json').read_bytes())
        cls.record = json.loads(stem.with_suffix('.result.json').read_bytes())

    def test_external_spelling_does_not_hide_changed_allocation_scope(self):
        row = next(r for r in self.record['results'] if r['variant'] == 'communal')
        expected = self.spec['expect_bindings']['communal@0']
        self.assertTrue(all(c['ok'] for c in probe.binding_checks('communal@0', row, expected)))
        mutant = copy.deepcopy(row)
        mutant['bindings']['external_scopes']['_status'] = 'external'
        self.assertFalse(all(c['ok'] for c in probe.binding_checks('communal@0', mutant, expected)))

    def test_wrong_frame_and_missing_compilation_fail_the_binding_gate(self):
        row = next(r for r in self.record['results'] if r['variant'] == 'initialized')
        expected = self.spec['expect_bindings']['initialized@0']
        mutant = copy.deepcopy(row)
        mutant['bindings']['ordered_const_fixups'][0]['frame_kind'] = 'segment'
        self.assertFalse(all(c['ok'] for c in probe.binding_checks('initialized@0', mutant, expected)))
        self.assertFalse(all(c['ok'] for c in probe.binding_checks('initialized@0', {'error': 'failed'}, expected)))
        with self.assertRaisesRegex(ValueError, 'unsupported binding expectation'):
            probe.binding_checks('initialized@0', row, {'unimplemented': True})


if __name__ == '__main__':
    unittest.main()
