"""Original palette footprint plus fail-closed source/alias/input controls."""
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

class WindowPaletteDomainTests(unittest.TestCase):
    def test_single_canonical_owner_and_retired_native_allocator(self):
        program = json.loads((ROOT/'src/program.json').read_text())
        owners = [m for m in program['modules'] if m['key']=='source-owned:window-palette']
        self.assertEqual(len(owners), 1)
        self.assertEqual(owners[0]['storage_contract']['communals'], [dict(
            name='_win_colors', kind='far', length=96, count=96, element_size=1)])
        blockers = json.loads((ROOT/'evidence/canonical/blockers.json').read_text())
        self.assertNotIn('_win_colors', [r['name'] for r in blockers['imports']])
        self.assertNotIn('_win_handles', [r['name'] for r in blockers['imports']])
        # Reinserting the former allocation sidecar must not restore a second
        # source of palette lifetime or a synthetic failure branch.
        for path in (ROOT/'portable').rglob('*'):
            if path.suffix in ('.py', '.c', '.h'):
                self.assertNotIn('sim_window_source_reserve_colors', path.read_text(), str(path))

    def test_reviewed_original_footprint_and_negative_controls(self):
        spec = importlib.util.spec_from_file_location('window_palette_domain', ROOT/'evidence/canonical/window-domain/palette_probe.py')
        probe = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(probe)
        result = probe.collect()
        expected = json.loads((ROOT/'evidence/canonical/window-domain/palette-facts.json').read_text())
        # Inventory count is snapshot metadata; unrelated owners do not alter this domain.
        result.pop('source_inventory_count')
        expected.pop('source_inventory_count')
        self.assertEqual(result, expected)
        self.assertEqual(result['status'], 'PASS')
        self.assertEqual(result['original_controls']['original_checked_objects'], 285)
        self.assertEqual(result['original_controls']['selected63_contrast_pointer_offset'], 378)
        self.assertEqual(result['original_controls']['numeric16_contrast_pointer_offset'], 96)
        self.assertIn('legacy_alias_setter', result['negative_controls'])
        self.assertIn('rogue_state_owner_function', result['negative_controls'])
        aliases = json.loads((ROOT/'src/program.json').read_text())['aliases']
        aliases.append(dict(alias='@new_palette_entry', target='@win_SetColorFromObj',
                            offset=0, kind='code'))
        self.assertEqual(probe.alias_map(aliases)['new_palette_entry'], 'win_SetColorFromObj')

if __name__ == '__main__': unittest.main()
