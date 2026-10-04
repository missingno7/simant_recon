"""Current source ownership and fail-closed build guarantees."""
import copy
import hashlib
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
sys.path.insert(0, str(ROOT))
import canonical
import modules
from dos import build as dos_build
from omf import OmfReader


class CanonicalProgram(unittest.TestCase):
    def test_one_inventory_owns_all_live_sources(self):
        program = canonical.load()
        listed = {m['source'] for m in program['modules']} | {'src/program.json'}
        actual = {p.relative_to(ROOT).as_posix() for p in (ROOT / 'src').rglob('*') if p.is_file()}
        self.assertEqual(listed, actual)
        man = modules.load_manifest()
        for item in program['modules']:
            self.assertEqual(hashlib.sha256((ROOT / item['source']).read_bytes()).hexdigest(), item['source_sha256'])
            if item['key'] in man['modules']:
                self.assertEqual(item['source_sha256'], man['modules'][item['key']]['source_sha256'])
            else:
                self.assertIn('storage_contract', item)

    def test_current_semantics_are_reviewed_canonical_definitions(self):
        program = canonical.load()
        bykey = {m['key']: m for m in program['modules']}
        for item in program['semantics']:
            text = (ROOT / bykey[item['module']]['source']).read_bytes().decode('latin1')
            self.assertEqual(canonical.definition_sha(text, item['function']), item['definition_sha256'])
            receipt = json.loads((ROOT / item['receipt']).read_text())
            self.assertEqual(receipt['status'], 'BEHAVIOR_EXACT_CONFIRMED')
            self.assertEqual(receipt['definition_sha256'], item['definition_sha256'])
            self.assertEqual(receipt['audit']['unexplained_semantic_differences'], [])
            for axis in ('complete_cfg', 'complete_data_widths', 'complete_calls_effects', 'codegen_only_residue'):
                self.assertIs(receipt['root_review'][axis], True)

    def test_storage_contract_rejects_changed_values_and_extra_imports(self):
        program = canonical.load()
        initialized = next(m for m in program['modules'] if m.get('storage_contract', {}).get('live_initialized_bytes'))
        import compiler
        source = (ROOT / initialized['source']).read_bytes().decode('latin1')
        result = compiler.compile_c(source, initialized['profile'], initialized['flags'])
        self.assertTrue(result.ok, result.log)
        obj = OmfReader(communals=True).read(result.obj)
        contract = initialized['storage_contract']
        self.assertEqual(dos_build.verify_storage(obj, contract)['status'], 'PASS')
        wrong = copy.deepcopy(contract)
        wrong['value_sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'initialized storage values'):
            dos_build.verify_storage(obj, wrong)
        obj.externals.append('_unproved_owner')
        obj.external_scopes.append('global')
        with self.assertRaisesRegex(ValueError, 'import'):
            dos_build.verify_storage(obj, contract)

    def test_open_semantics_prevent_an_independent_link(self):
        report = {'errors': [], 'unresolved_symbols': [{'name': '_unproved_owner'}],
                  'duplicate_publics': {}, 'duplicate_communals': {}, 'mixed_storage_owners': {},
                  'unresolved_semantic_gates': [{'id': 'live-layout-assumption', 'status': 'UNRESOLVED'}],
                  'translation_units': [{'status': 'COMPILED', 'object': {}}]}
        self.assertTrue(dos_build.preflight_blockers(report))


if __name__ == '__main__':
    unittest.main()
