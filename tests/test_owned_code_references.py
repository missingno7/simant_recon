"""Old-placement byte equality must not erase source-owned linker references."""
import copy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import canonical
import modules
from omf import OmfReader


class OwnedCodeReferences(unittest.TestCase):
    def test_old_literals_match_history_but_fail_independent_address_contract(self):
        program = canonical.load()
        manifest = modules.load_manifest()
        for key, expected_count in (('S03:3258', 8), ('S03:3126', 7)):
            with self.subTest(module=key):
                item = next(m for m in program['modules'] if m['key'] == key)
                contract = item['owned_code_references']
                module = manifest['modules'][key]
                text = (ROOT / item['source']).read_text()
                result = modules.verify_module(text, module, module['claims'], man=manifest,
                                               code_references=contract)
                self.assertTrue(result['exact'], result.get('module_reasons'))
                self.assertEqual(result['owned_code_reference_count'], expected_count)
                if key == 'S03:3258':
                    for reg, delta, literal in (('dx', '', '0Ch'), ('bx', '+512', '20Ch'),
                                                ('bx', '+256', '10Ch'), ('bx', '+768', '30Ch')):
                        expression = f'lea {reg}, xlat_tabs{delta}'
                        self.assertEqual(text.count(expression), 2)
                        text = text.replace(expression, f'lea {reg}, ds:[{literal}]')
                else:
                    for reg in ('di', 'si'):
                        expression = f'lea {reg}, linebuf'
                        self.assertEqual(text.count(expression), 2)
                        text = text.replace(expression, f'lea {reg}, ds:[0]')
                historical = modules.verify_module(text, module, module['claims'], man=manifest)
                self.assertTrue(historical['exact'], historical.get('module_reasons'))
                rejected = modules.verify_module(text, module, module['claims'], man=manifest,
                                                 code_references=contract)
                self.assertFalse(rejected['exact'])
                self.assertTrue(any('owned code reference' in r
                                    for r in rejected['module_reasons']))


    def test_callback_literals_match_history_but_fail_far_pointer_contract(self):
        recipes = {
            'S00:31AD': [('_gfx_planar_dither_box', '_gfx_planar_dither_box_raw', '1Ch'),
                         ('_gfx_planar_gpatbox', '_gfx_planar_pattern_box_raw', '13Ah'),
                         ('_gfx_planar_ginvbox', '_gfx_planar_invert_box_raw', '394h'),
                         ('_gfx_planar_gboxfill', 'L16C1', '16C1h'),
                         ('_gfx_planar_fill_box_unsorted', '_gfx_planar_fill_box_raw', '16FCh')],
            'S01:3126': [('_gfx_mono_fill_or_pattern_box', 'L0264', '264h')],
            'S02:3126': [('_gfx_vga8_dither_box', '_gfx_vga8_dither_box_raw', '0AEh'),
                         ('_gfx_vga8_gpatbox', '_gfx_vga8_pattern_box_raw', '19Dh'),
                         ('_gfx_vga8_gboxfill', 'L0294', '294h')],
            'S03:3126': [('_gfx_tandy_dither_box', '_gfx_tandy_dither_box_raw', '210h'),
                         ('_gfx_tandy_gpatbox', '_gfx_tandy_pattern_box_raw', '3DAh'),
                         ('_gfx_tandy_gboxfill', 'L05B4', '5B4h')],
        }
        program = canonical.load()
        manifest = modules.load_manifest()
        for key, sites in recipes.items():
            with self.subTest(module=key):
                item = next(m for m in program['modules'] if m['key'] == key)
                module = manifest['modules'][key]
                contract = item['owned_code_references']
                text = (ROOT / item['source']).read_text()
                result = modules.verify_module(text, module, module['claims'], man=manifest,
                                               code_references=contract)
                self.assertTrue(result['exact'], result.get('module_reasons'))
                self.assertEqual(result['owned_code_reference_count'],
                                 len(sites) + (4 if key == 'S03:3126' else 0))
                for public, label, literal in sites:
                    begin = text.index(public + '\tproc')
                    end = text.index(public + '\tendp', begin)
                    body = text[begin:end]
                    expression = 'mov ax, OFFSET ' + label
                    self.assertEqual(body.count(expression), 1)
                    text = text[:begin] + body.replace(expression, 'mov ax, ' + literal) + text[end:]
                historical = modules.verify_module(text, module, module['claims'], man=manifest)
                self.assertTrue(historical['exact'], historical.get('module_reasons'))
                rejected = modules.verify_module(text, module, module['claims'], man=manifest,
                                                 code_references=contract)
                self.assertFalse(rejected['exact'])
                self.assertTrue(any('owned code reference' in r
                                    for r in rejected['module_reasons']))

    def test_callback_anchor_and_paired_segment_are_required(self):
        program = canonical.load()
        manifest = modules.load_manifest()
        item = next(m for m in program['modules'] if m['key'] == 'S00:31AD')
        module = manifest['modules'][item['key']]
        contract = item['owned_code_references']
        collect = {}
        result = modules.verify_module((ROOT / item['source']).read_text(), module,
                                       module['claims'], man=manifest,
                                       code_references=contract, collect=collect)
        self.assertTrue(result['exact'], result.get('module_reasons'))
        obj = OmfReader().read(collect['object'])
        wrong_anchor = copy.deepcopy(contract)
        wrong_anchor['owners'][0]['anchor_delta'] += 1
        with self.assertRaisesRegex(ValueError, 'public anchor'):
            canonical.check_owned_code_references(wrong_anchor, obj)
        wrong_pair = copy.deepcopy(obj)
        owner = contract['owners'][0]
        site = owner['references'][0]
        public = next(p for p in wrong_pair.publics if p['name'] == site['public'])
        fixup = next(f for f in wrong_pair.linker_fixups
                     if f['segment'] == owner['segment'] and
                     f['offset'] == public['offset'] + site['segment_operand_offset'])
        fixup['frame'] = '_DATA'
        with self.assertRaisesRegex(ValueError, 'paired segment word'):
            canonical.check_owned_code_references(contract, wrong_pair)


if __name__ == '__main__':
    unittest.main()
