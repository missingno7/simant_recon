"""Isolated metadata controls; no canonical production file is modified."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / 'build/workers/canonical_promotion_tests'
sys.path.insert(0, str(ROOT / 'tools'))
sys.path.insert(0, str(ROOT))
import canonical as c
import promote as p


class PromotionInventoryControls(unittest.TestCase):
    def setUp(self):
        HERE.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=HERE)
        self.root = Path(self.temp.name)
        self.patch = patch.multiple(c, ROOT=self.root, PROGRAM=self.root / 'src/program.json')
        self.patch.start()
        self.key = 'root:0001'
        self.source = 'src/root/m0001.c'
        self.text = 'extern int value;\nint strict(void) { return value; }\nint helper(void) { return 1; }\n'
        self.raw = self.text.encode('latin1')
        self.module = {'unit': 'root', 'seg': 1, 'source': self.source,
                       'source_sha256': c.sha(self.raw), 'lang': 'c', 'profile': 'msc600ax',
                       'flags': ['/AL'], 'placements': {}, 'claims': []}
        self.program = {'schema': 'simant-canonical-program-v1',
                        'modules': [{'key': self.key, **{k: self.module[k] for k in
                            ('unit', 'source', 'source_sha256', 'lang', 'profile', 'flags')}}],
                        'semantics': [self.semantic('strict', self.text, 'evidence/strict.json')]}
        self.write(self.source, self.raw)
        self.write('src/program.json', json.dumps(self.program))
        self.review(self.program['semantics'][0])

    def tearDown(self):
        self.patch.stop()
        self.temp.cleanup()

    def write(self, path, value):
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(value if isinstance(value, bytes) else value.encode())

    def semantic(self, function, text, receipt):
        return {'function': function, 'module': self.key, 'status': 'BEHAVIOR_EXACT_CONFIRMED',
                'definition_sha256': c.definition_sha(text, function), 'receipt': receipt}

    def review(self, row, **extra):
        data = {'schema': 'simant-canonical-semantic-review-v1',
                **{k: row[k] for k in ('function', 'module', 'status', 'definition_sha256')},
                'audit': {'status': 'BEHAVIOR_EXACT_CONFIRMED', 'unexplained_semantic_differences': []},
                'root_review': {'reviewer': 'root', 'complete_cfg': True, 'complete_data_widths': True,
                                'complete_calls_effects': True, 'codegen_only_residue': True}}
        data.update(extra)
        self.write(row['receipt'], json.dumps(data))
        return data

    def update(self, text, module=None):
        return c.exact_inventory(self.program, self.key, module or self.module,
                                 text.encode('latin1'), self.module, source=self.source)

    def test_exact_helper_improvement_updates_pin_and_compiler_context(self):
        text = self.text.replace('return 1;', 'return 2;')
        after = self.update(text)
        self.assertEqual(after['modules'][0]['source_sha256'], c.sha(text.encode()))
        self.assertEqual(after['semantics'], self.program['semantics'])
        self.assertEqual(self.program['modules'][0]['source_sha256'], c.sha(self.raw))
        self.program['semantics'] = []
        after = self.update(text, {**self.module, 'flags': ['/AL', '/Zi']})
        self.assertEqual(after['modules'][0]['flags'], ['/AL', '/Zi'])

    def test_changed_registered_body_and_declaration_context_are_refused(self):
        with self.assertRaisesRegex(ValueError, 'definition/review differs'):
            self.update(self.text.replace('return value;', 'return value + 1;'))
        with self.assertRaisesRegex(ValueError, 'declaration context changed'):
            self.update(self.text.replace('extern int value;', 'extern unsigned int value;'))
        with self.assertRaisesRegex(ValueError, 'declaration context changed'):
            self.update(self.text, {**self.module, 'flags': ['/AL', '/J']})

    def test_macro_inside_unregistered_helper_still_is_context(self):
        changed = self.text.replace('return 1;', '\n#define VALUE 2\nreturn 1;')
        with self.assertRaisesRegex(ValueError, 'declaration context changed'):
            self.update(changed)

    def test_stale_source_or_disagreeing_inventory_fails(self):
        self.write(self.source, self.raw + b'/* unpublished */')
        with self.assertRaisesRegex(ValueError, 'source pin differs'):
            self.update(self.text)
        self.write(self.source, self.raw)
        self.program['modules'][0]['profile'] = 'another'
        with self.assertRaisesRegex(ValueError, 'canonical/historical context differs'):
            self.update(self.text)

    def test_new_exact_module_registers_one_inventory_entry(self):
        module = {**self.module, 'unit': 'S01'}
        after = c.exact_inventory(self.program, 'S01:0002', module, b'int added(void) { return 0; }',
                                  None, source='src/S01/m0002.c')
        self.assertEqual(len(after['modules']), 2)
        self.assertEqual(after['modules'][0]['key'], 'S01:0002')
        self.assertEqual(after['modules'][0]['unit'], 'S01')
        self.assertEqual(after['modules'][1]['key'], self.key)

    def test_registered_body_revision_requires_fresh_superseding_root_review(self):
        text = self.text.replace('return value;', 'return value + 1;')
        after = copy.deepcopy(self.program)
        after['semantics'] = [self.semantic('strict', text, 'evidence/strict-v2.json')]
        row = after['semantics'][0]
        self.review(row)
        pin = c.sha((self.root / 'src/program.json').read_bytes())
        with self.assertRaisesRegex(ValueError, 'prior canonical context'):
            c.check_semantic_publication(after, {self.key: text.encode()}, self.program, pin)
        old = self.program['semantics'][0]
        review = self.review(row, supersedes={'program_sha256': pin,
            'source_sha256': self.module['source_sha256'], 'definition_sha256': old['definition_sha256'],
            'receipt_sha256': c.sha((self.root / old['receipt']).read_bytes())})
        review['root_review']['source_correction_reviewed'] = True
        self.write(row['receipt'], json.dumps(review))
        c.check_semantic_publication(after, {self.key: text.encode()}, self.program, pin)
        with self.assertRaisesRegex(ValueError, 'prior canonical context'):
            c.check_semantic_publication(after, {self.key: text.encode()}, self.program, 'stale')

    def test_full_review_axes_cannot_be_removed_by_revision(self):
        row = self.program['semantics'][0]
        review = self.review(row)
        review['root_review']['complete_cfg'] = False
        self.write(row['receipt'], json.dumps(review))
        with self.assertRaisesRegex(ValueError, 'incomplete'):
            self.update(self.text)

    def test_bulk_requires_prior_program_pin_before_any_publication(self):
        import modules
        manifest = self.root / 'layout/manifest.json'
        self.write('layout/manifest.json', json.dumps({'modules': {self.key: self.module}}))
        plan = {'prior_manifest_sha256': c.sha(manifest.read_bytes()), 'program': self.program, 'files': []}
        plan_path = self.root / 'plan.json'
        plan_path.write_text(json.dumps(plan))
        with patch.object(modules, 'MANIFEST', manifest), patch.object(modules, 'load_manifest',
                return_value={'modules': {self.key: self.module}}):
            with self.assertRaisesRegex(ValueError, 'stale or missing program pin'):
                c.publish(plan_path, False)
        self.assertEqual((self.root / self.source).read_bytes(), self.raw)

    def run_exact(self, module, result, *, prior_result=None):
        import modules
        candidate = self.root / 'candidate.c'
        candidate.write_text(self.text.replace('return 1;', 'return 2;'))
        manifest = self.root / 'layout/manifest.json'
        self.write('layout/manifest.json', json.dumps({'modules': {self.key: module}}))
        def save(man):
            manifest.write_text(json.dumps(man))
        verification = [result] if prior_result is None else [result, prior_result]
        with patch.multiple(p, ROOT=self.root, JOURNAL=self.root / 'evidence/promotions.jsonl', Lock=p._NoLock), \
                patch.dict(sys.modules, {'canonical': c}), \
                patch.object(p.exemod, 'load', return_value=object()), \
                patch.object(modules, 'load_manifest', return_value={'modules': {self.key: module}}), \
                patch.object(modules, 'write_manifest', side_effect=save), \
                patch.object(modules, 'object_range', return_value=(0, 65536)), \
                patch.object(modules, 'verify_module', side_effect=verification) as verifier, \
                patch.object(sys, 'argv', ['promote.py', str(candidate), '--module', self.key]):
            self.assertEqual(p.main(), 0)
        return json.loads(manifest.read_text()), verifier

    def test_exact_entry_point_writes_both_inventories_and_retains_data_public_gate(self):
        claim = {'name': 'helper', 'unit': 'root', 'seg': 1, 'off': 0, 'size': 3,
                 'current_proof': 'HISTORICAL_EXACT_SOURCE_REBUILT'}
        module = {**self.module, 'claims': [claim], 'code_data_publics': {'view': {'claim': 'cd_root'}}}
        result = {'compile_ok': True, 'exact': True, 'claims': {'helper': {'exact': True, 'reloc_order': 'EXACT'}},
                  'data': {}, 'scaffold': [], 'object_sha256': 'current-object'}
        manifest, verifier = self.run_exact(module, result)
        record = manifest['modules'][self.key]
        program = json.loads((self.root / 'src/program.json').read_text())
        self.assertEqual(record['source_sha256'], program['modules'][0]['source_sha256'])
        self.assertEqual(record['source_sha256'], c.sha((self.root / self.source).read_bytes()))
        self.assertEqual(record['code_data_publics'], module['code_data_publics'])
        self.assertEqual(verifier.call_args_list[0].args[1]['code_data_publics'], module['code_data_publics'])
        self.assertNotIn('current_proof', record['claims'][0])
        self.assertEqual(program['semantics'], self.program['semantics'])

    def test_stale_prior_context_receipt_refuses_before_writing_source_or_inventory(self):
        claim = {'name': 'helper', 'unit': 'root', 'seg': 1, 'off': 0, 'size': 3}
        module = {**self.module, 'claims': [claim],
                  'canonical_admission': {'receipt': 'evidence/context.json'}}
        result = {'compile_ok': True, 'exact': True, 'claims': {'helper': {'exact': True, 'reloc_order': 'EXACT'}},
                  'data': {}, 'scaffold': [], 'object_sha256': 'current-object', 'contribution_sha256': 'current'}
        self.write('evidence/context.json', json.dumps({'historical_comparisons': {
            self.key: {'contribution_sha256': 'stale', 'comparison': c.observed(result)}}}))
        program_before = (self.root / 'src/program.json').read_bytes()
        with self.assertRaisesRegex(SystemExit, 'prior canonical context receipt differs'):
            self.run_exact(module, result, prior_result=result)
        self.assertEqual((self.root / self.source).read_bytes(), self.raw)
        self.assertEqual((self.root / 'src/program.json').read_bytes(), program_before)

    def test_bulk_storage_gate_refuses_wrong_initialized_values(self):
        # Exercise the publisher's actual storage branch and complete DOS gate.
        import compiler
        import modules
        from dos import build
        from omf import OmfReader
        with patch.object(c, 'ROOT', ROOT), patch.object(c, 'PROGRAM', ROOT / 'src/program.json'):
            live = c.load()
        item = copy.deepcopy(next(m for m in live['modules'] if
                                 m.get('storage_contract', {}).get('live_initialized_bytes')))
        text = (ROOT / item['source']).read_bytes()
        compiled = compiler.compile_c(text.decode('latin1'), item['profile'], item['flags'])
        self.assertTrue(compiled.ok, compiled.log)
        item['storage_contract']['value_sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'initialized storage values'):
            build.verify_storage(OmfReader(communals=True).read(compiled.obj), item['storage_contract'])
        # A minimal first publication avoids modifying any live inventory.
        (self.root / 'src/program.json').unlink()
        item['source'] = 'src/state/control.c'
        self.write('candidate-storage.c', text)
        manifest = self.root / 'layout/manifest.json'
        self.write('layout/manifest.json', json.dumps({'modules': {}}))
        plan = {'prior_manifest_sha256': c.sha(manifest.read_bytes()),
                'program': {'modules': [item], 'semantics': []},
                'files': [{'key': item['key'], 'candidate': 'candidate-storage.c',
                           'source': item['source'], 'sha256': c.sha(text)}],
                'anchors': [], 'reviewed_context_changes': {}, 'receipt': {}}
        path = self.root / 'plan-storage.json'
        path.write_text(json.dumps(plan))
        with patch.object(modules, 'MANIFEST', manifest), patch.object(modules, 'load_manifest',
                return_value={'modules': {}}), patch.object(compiler, 'compile_c', return_value=compiled):
            with self.assertRaisesRegex(ValueError, 'canonical storage contract differs.*initialized storage values'):
                c.publish(path, False)
        self.assertFalse((self.root / item['source']).exists())

    def test_real_current_inventory_satisfies_unchanged_review_controls(self):
        # Read actual current evidence; use no production writes or recompiles.
        with patch.object(c, 'ROOT', ROOT), patch.object(c, 'PROGRAM', ROOT / 'src/program.json'):
            program = c.load()
            payloads = {m['key']: (ROOT / m['source']).read_bytes() for m in program['modules']}
            c.check_semantic_publication(program, payloads, program, c.sha(c.PROGRAM.read_bytes()))


if __name__ == '__main__':
    unittest.main()
