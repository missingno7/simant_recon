"""Nominal stack preservation and fail-closed window subgraph coverage."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = next(p for p in Path(__file__).resolve().parents if (p / 'src/program.json').is_file())
PROBE_DIR = ROOT / 'evidence/canonical/window-domain'


class WindowStackDomain(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location('nominal_window_stack', PROBE_DIR / 'stack_probe.py')
        cls.probe = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.probe)
        cls.facts = json.loads((PROBE_DIR / 'stack-facts.json').read_text())

    def test_original_mutations_register_forwarding_and_resources(self):
        result = self.probe.run_controls(self.facts)
        self.assertEqual((len(result['mutations']), result['supported_precondition_count'],
                          result['excluded_precondition_count']), (36, 26, 10))
        self.assertEqual(result['implicit_AX'], [{'edit_open': 0, 'AX': 0}, {'edit_open': 1, 'AX': 0}])
        self.assertEqual((result['shipped_windows'], result['initially_open_windows']), (34, 0))
        self.assertEqual((result['save_record_count'], result['stack_save_overlap']), (307, []))
        negative = next(r for r in result['mutations'] if r['function'] == 'f_1E57_0052'
                        and r['count'] == 31 and r['argument'] == 33 << 8)
        self.assertFalse(negative['nominal_preconditions'])
        self.assertEqual((negative['sentinel_index'], negative['following_guard_word']), (32, 0x8000))
        truncation = next(r for r in result['mutations'] if r['function'] == 'f_1E57_00B1'
                          and r['count'] == 31 and r['argument'] == 33 << 8)
        self.assertFalse(truncation['nominal_preconditions'])
        self.assertEqual((truncation['sentinel_index'], truncation['dropped_window']), (31, 30 << 8))

    def test_current_coverage_and_no_truncation_bound(self):
        self.assertEqual(self.probe.validate_coverage(self.facts), 31)
        changed = copy.deepcopy(self.facts)
        changed['noncoexisting_pair'] = []
        with self.assertRaisesRegex(ValueError, 'lifetime exclusion'):
            self.probe.active_bound(changed)
        changed = copy.deepcopy(self.facts)
        changed['possible_open_ids'].append(27)
        with self.assertRaisesRegex(ValueError, 'permits stack truncation'):
            self.probe.active_bound(changed)

    def test_changed_root_registration_and_alias_are_rejected(self):
        new_root = 'void far NewWindow(void) { win_Open(0x1b00); }\n'
        with self.assertRaisesRegex(ValueError, 'coverage changed'):
            self.probe.validate_coverage(self.facts,
                source_overrides={'src/root/new-window.c': new_root})
        path = 'src/root/m00BA.c'
        raw = (ROOT / path).read_text()
        altered = raw.replace('f_20E8_088B(f_00BA_0228)', 'f_20E8_088B(NewWindowHook)')
        self.assertNotEqual(raw, altered)
        with self.assertRaisesRegex(ValueError, 'source_pins'):
            self.probe.validate_coverage(self.facts, source_overrides={path: altered})
        symbols = json.loads((ROOT / 'layout/symbols.json').read_text())['code']
        symbols['new_open_alias'] = {**symbols['win_Open'], 'alias_of': 'win_Open'}
        with self.assertRaisesRegex(ValueError, 'code_alias_subset'):
            self.probe.validate_coverage(self.facts, symbols_override=symbols)
        aliases = json.loads((ROOT / 'src/program.json').read_text())['aliases']
        aliases.append({'alias': '_new_open_alias', 'target': '_win_Open', 'kind': 'code', 'offset': 0})
        with self.assertRaisesRegex(ValueError, 'program_alias_subset'):
            self.probe.validate_coverage(self.facts, program_aliases_override=aliases)

    def test_unrelated_owner_and_inventory_alias_do_not_repin_domain(self):
        aliases = json.loads((ROOT / 'src/program.json').read_text())['aliases']
        aliases.append({'alias': '_unrelated_view', 'target': '_unrelated_owner', 'kind': 'data', 'offset': 0})
        self.assertEqual(self.probe.validate_coverage(self.facts,
            source_overrides={'src/state/unrelated-owner.c': 'int unrelated_owner;\n'},
            program_aliases_override=aliases), 31)


if __name__ == '__main__':
    unittest.main()
