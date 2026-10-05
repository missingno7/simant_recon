"""Old-placement byte equality must not erase source-owned linker references."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import canonical
import modules


class OwnedCodeReferences(unittest.TestCase):
    def test_old_literals_match_history_but_fail_independent_address_contract(self):
        program = canonical.load()
        manifest = modules.load_manifest()
        for key, expected_count in (('S03:3258', 8), ('S03:3126', 4)):
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


if __name__ == '__main__':
    unittest.main()
