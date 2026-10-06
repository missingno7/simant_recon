"""Current source ownership and fail-closed build guarantees."""
import copy
import hashlib
import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
sys.path.insert(0, str(ROOT))
import canonical
import csrc
import modules
from dos import build as dos_build
from omf import OmfReader


class CanonicalProgram(unittest.TestCase):
    def test_queue_result_abi_agrees_across_source_translation_units(self):
        # Byte equality alone cannot reject the old void/split-pointer declaration.
        # The ASM returns AX=0/1 and writes through one far Rect pointer; S26
        # observes that result. Compare source types, ignoring parameter names.
        def signature(text, name):
            fn = csrc.Source(text).function(name)
            header = canonical.tokens(text[fn.head_s:fn.params_s]).split()
            result = tuple(t for t in header[:-1] if t != 'extern')
            params = tuple(canonical.tokens(kind) for kind, _ in fn.params)
            return result, params

        expected = signature('int far lookup(int id, struct Rect far *out) { return 0; }', 'lookup')
        owner = (ROOT / 'src/root/m1FD2.c').read_text()
        self.assertEqual(signature(owner, 'f_1FD2_04B3'), expected)
        caller = (ROOT / 'src/S26/m39C7.c').read_text()
        prototype = re.search(r'extern int far f_1FD2_04B3\([^;]+\);', caller).group(0)
        self.assertEqual(signature(prototype[:-1] + ' { return 0; }', 'f_1FD2_04B3'), expected)
        old = 'void far lookup(int id, int offset, int segment) { }'
        self.assertNotEqual(signature(old, 'lookup'), expected)

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
                  'unresolved_data': [],
                  'translation_units': [{'status': 'COMPILED', 'object': {}}]}
        self.assertTrue(dos_build.preflight_blockers(report))

    def test_data_debt_alone_prevents_a_link(self):
        report = {'errors': [], 'translation_units': [{'status': 'COMPILED', 'object': {}}],
                  'unresolved_data': []}
        self.assertEqual(dos_build.preflight_blockers(report), [])
        report['unresolved_data'] = [{'id': 'unowned_field', 'bytes': 1}]
        self.assertIn('1 unresolved data ranges (1 bytes)', dos_build.preflight_blockers(report))
        del report['unresolved_data']
        self.assertIn('missing functional initialized-data audit', dos_build.preflight_blockers(report))

    def test_historical_layout_debt_is_reported_not_owned(self):
        program = json.loads((ROOT / 'src/program.json').read_text())
        historical = program['dos']['historical_layout_debt']
        self.assertEqual(sum(r['bytes'] for r in historical), 30)
        self.assertEqual(program['dos']['unresolved_data'], [])
        for row in historical:
            self.assertEqual(row['status'], 'HISTORICAL_LAYOUT_DEBT')
            self.assertIn('physical DGROUP layout equivalence is not claimed', row['caveat'])
            self.assertTrue((ROOT / row['decision_evidence']).is_file())
        # Historical debt never relaxes the blocker for genuinely unresolved data.
        report = {'errors': [], 'translation_units': [{'status': 'COMPILED', 'object': {}}],
                  'unresolved_data': [{'id': 'unowned_field', 'bytes': 1}],
                  'historical_layout_debt': historical}
        self.assertIn('1 unresolved data ranges (1 bytes)', dos_build.preflight_blockers(report))
        # No canonical source may define storage for the historical addresses.
        names = {'g_' + r['id'].split('_')[1].upper() for r in historical if r['id'].startswith('dgroup_')}
        for path in (ROOT / 'src').rglob('*.[cC]'):
            text = path.read_text(errors='replace')
            for name in names:
                self.assertNotRegex(text, r'\b_?' + name + r'\b', f'{name} in {path}')


if __name__ == '__main__':
    unittest.main()
