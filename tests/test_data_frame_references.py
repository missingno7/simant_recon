"""Historical byte equality cannot excuse a wrong private-data linker frame."""
import copy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import canonical
import modules
from omf import OmfReader


class DataFrameReferences(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        program = canonical.load()
        cls.item = next(m for m in program['modules'] if m['key'] == 'root:1B05')
        cls.contract = cls.item['data_frame_references']
        cls.manifest = modules.load_manifest()
        cls.module = cls.manifest['modules'][cls.item['key']]
        cls.text = (ROOT / cls.item['source']).read_bytes().decode('latin1')
        collect = {}
        cls.result = modules.verify_module(cls.text, cls.module, cls.module['claims'],
            man=cls.manifest, collect=collect, data_frame_references=cls.contract)
        cls.obj = OmfReader().read(collect['object'])

    def test_current_whole_module_has_all_fourteen_group_frames(self):
        self.assertTrue(self.result['exact'], self.result.get('module_reasons'))
        self.assertEqual(self.result['data_frame_reference_count'], 14)
        self.assertEqual(canonical.check_data_frame_references(self.contract, self.obj), 14)

    def test_segment_frames_match_history_but_fail_independent_link_contract(self):
        negative = self.text.replace('ss:DGROUP', 'ss:nothing')
        self.assertNotEqual(negative, self.text)
        historical = modules.verify_module(negative, self.module, self.module['claims'], man=self.manifest)
        self.assertTrue(historical['exact'], historical.get('module_reasons'))
        rejected = modules.verify_module(negative, self.module, self.module['claims'],
            man=self.manifest, data_frame_references=self.contract)
        self.assertFalse(rejected['exact'])
        self.assertTrue(any('data frame reference' in r for r in rejected['module_reasons']))

    def test_each_binding_component_and_missing_fixup_is_rejected(self):
        site = self.contract['sites'][0]
        public = next(p for p in self.obj.publics if p['name'] == site['public'])
        index = next(i for i, f in enumerate(self.obj.linker_fixups)
            if f['segment'] == public['segment'] and
            f['offset'] == public['offset'] + site['operand_offset'])
        for field, value in (('frame', '_DATA'), ('frame_kind', 'segment'),
                             ('target', 'LZSS_DATA'), ('displacement', 23),
                             ('loc', 'base16'), ('self_relative', True),
                             ('encoded_addend', '0100')):
            with self.subTest(field=field):
                wrong = copy.deepcopy(self.obj)
                wrong.linker_fixups[index][field] = value
                with self.assertRaisesRegex(ValueError, 'wrong frame/target'):
                    canonical.check_data_frame_references(self.contract, wrong)
        missing = copy.deepcopy(self.obj)
        del missing.linker_fixups[index]
        with self.assertRaisesRegex(ValueError, 'missing'):
            canonical.check_data_frame_references(self.contract, missing)

    def test_duplicate_empty_unanchored_and_outside_group_contracts_fail(self):
        for mutate, message in (
                (lambda c: c['sites'].append(copy.deepcopy(c['sites'][0])), 'duplicate'),
                (lambda c: c['sites'].clear(), 'no references'),
                (lambda c: c['sites'][0].update(public='_missing'), 'procedure public'),
                (lambda c: c.update(frame_group='absent'), 'outside its group'),
                (lambda c: c['sites'][0].update(displacement=288), 'outside')):
            wrong = copy.deepcopy(self.contract)
            mutate(wrong)
            with self.assertRaisesRegex(ValueError, message):
                canonical.check_data_frame_references(wrong, self.obj)


if __name__ == '__main__':
    unittest.main()
