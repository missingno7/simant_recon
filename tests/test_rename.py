"""Invented canonical modules; publication is confined to a temporary root."""
from contextlib import ExitStack, redirect_stdout
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / 'build/workers/rename-tool/tests'
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / 'tools'))
sys.path.insert(0, str(ROOT))
import rename as r
import canonical
import lockfile
from omf import ObjectModule


def row(old='old', new='fresh', kind='descriptive'):
    return {'old': old, 'new': new, 'kind': kind, 'why': 'invented DOS evidence'}


class TokenControls(unittest.TestCase):
    def test_c_tokens_literals_comments_and_preprocessor(self):
        text = ('int old, old_suffix; char *s = "old \\"old";\n'
                "int ch = 'o'; /* old prose, `old`, old(), function old */\n"
                '#define ALIAS old\n#include <old.h>\n#include "old.h"\n'
                'int f(void) { _asm { mov ax,old ; old prose\n } return old; }\n')
        new = r.replace_tokens(text, {'old': 'fresh'})
        self.assertIn('int fresh, old_suffix;', new)
        self.assertIn('/* old prose, `fresh`, fresh(), function fresh */', new)
        self.assertIn('#define ALIAS fresh', new)
        self.assertIn('#include <old.h>', new)
        self.assertIn('#include "old.h"', new)
        self.assertIn('mov ax,fresh ; old prose', new)
        self.assertIn('return fresh;', new)
        self.assertEqual(new.count('"old'), text.count('"old'))

    def test_asm_decorations_quoted_data_and_comment_blocks(self):
        text = ('PUBLIC _old\n_old PROC FAR\n call @old\n mov ax,old\n'
                " db 'old', 'isn''t old', \"old\" ; `old`, ordinary old\n"
                'COMMENT !\nold is prose\n!\n_old ENDP\n')
        new = r.replace_tokens(text, r.spellings({'old': 'fresh'}, {}), 'asm')
        self.assertIn('PUBLIC _fresh\n_fresh PROC', new)
        self.assertIn('call @fresh', new)
        self.assertIn("db 'old', 'isn''t old', \"old\" ; `fresh`, ordinary old", new)
        self.assertIn('old is prose', new)

    def test_pascal_and_address_comment(self):
        mapping = r.spellings({'f_0001_0000': 'ReadIt'}, {'code': {'f_0001_0000': {'convention': 'pascal'}}})
        self.assertEqual(mapping['F_0001_0000'], 'READIT')
        self.assertEqual(r.replace_tokens('/* f_0001_0000 */', mapping), '/* ReadIt */')

    def test_metadata_schema_fields_and_evidence_paths_are_not_symbols(self):
        data = {'name': 'name', 'status': 'status', 'receipt': 'evidence/name/status.json',
                'kind': 'code',
                'claims': {'name': {'name': 'name', 'status': 'status'}}}
        actual = r.renamed(data, {'name': 'fresh_name', 'status': 'fresh_status', 'code': 'fresh_code'})
        self.assertEqual(actual, {'name': 'fresh_name', 'status': 'status', 'kind': 'code',
            'receipt': 'evidence/name/status.json',
            'claims': {'fresh_name': {'name': 'fresh_name', 'status': 'status'}}})

    def test_identifier_shaped_comment_references_preserve_ordinary_prose(self):
        text = '/* ReadMap uses RRand and word_count, and retains the value. */'
        self.assertEqual(r.replace_tokens(text, {'ReadMap': 'RenderMap', 'RRand': 'Random',
            'word_count': 'count', 'value': 'total'}),
            '/* RenderMap uses Random and count, and retains the value. */')


class TransactionControls(unittest.TestCase):
    def setUp(self):
        HERE.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=HERE)
        self.root = Path(self.temp.name)
        self.stack = ExitStack()
        self.stack.enter_context(patch.object(r, 'ROOT', self.root))
        self.stack.enter_context(patch.multiple(canonical, ROOT=self.root, PROGRAM=self.root / 'src/program.json'))
        self.stack.enter_context(patch.multiple(lockfile, ROOT=self.root, LOCK=self.root / 'build/locks/canonical.lock'))
        self.stack.enter_context(patch.object(r.modules, 'link_after_reasons', return_value=[]))
        self.stack.enter_context(patch.object(r.modules, 'placement_overlap_reasons', return_value=[]))
        self.key = 'root:0001'
        self.source = 'src/root/m0001.c'
        self.text = 'extern int value;\nint old(void) { return value; }\nint peer(void) { return old(); }\n'
        self.module = {'unit': 'root', 'seg': 1, 'source': self.source,
                       'source_sha256': canonical.sha(self.text.encode()), 'lang': 'c',
                       'profile': 'msc600ax', 'flags': ['/AL', '/Os', '/Zi'],
                       'placements': {'_DATA': {'seg': 2, 'off': 0, 'size': 2}},
                       'extent': {'start': 16, 'end': 22},
                       'claims': [{'name': 'old', 'unit': 'root', 'seg': 1, 'off': 0, 'size': 3,
                                   'steered': 'old requires original declaration order'},
                                  {'name': 'peer', 'unit': 'root', 'seg': 1, 'off': 3, 'size': 3}]}
        self.program = {'schema': 'simant-canonical-program-v1', 'modules': [
            {'key': self.key, **{f: self.module[f] for f in
                ('source', 'source_sha256', 'lang', 'profile', 'flags', 'unit')}}],
            'aliases': [{'alias': '_view', 'target': '_old'}], 'semantics': []}
        self.man = {'modules': {self.key: self.module}}
        self.syms = {'code': {'old': {'unit': 'root', 'seg': 1, 'off': 0},
                              'peer': {'unit': 'root', 'seg': 1, 'off': 3}},
                     'data': {'value': {'seg': 2, 'off': 0}}, 'runtime': {'_malloc': {'seg': 3, 'off': 0}}}
        self.write(self.source, self.text)
        self.persist()
        self.verifier = self.stack.enter_context(patch.object(r.modules, 'verify_module', side_effect=self.verify))
        self.fail_when = lambda text: False

    def tearDown(self):
        self.stack.close()
        self.temp.cleanup()

    def write(self, rel, content):
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content if isinstance(content, bytes) else content.encode())

    def persist(self):
        self.write('layout/manifest.json', json.dumps(self.man))
        self.write('layout/symbols.json', json.dumps(self.syms))
        self.write('src/program.json', json.dumps(self.program))

    def read(self, rel):
        return json.loads((self.root / rel).read_bytes())

    def snapshot(self):
        return {p.relative_to(self.root).as_posix(): p.read_bytes() for folder in ('src', 'layout', 'evidence')
                for p in (self.root / folder).rglob('*') if p.is_file()}

    def verify(self, text, module, claims, **kwargs):
        failed = self.fail_when(text)
        name = claims[0]['name']
        self.assertIn('_' + name, r.match.symbols())
        self.assertIn(name, r.symbols.load()['code'])
        result = {'compile_ok': True, 'exact': not failed, 'claims': {
            c['name']: {'exact': not (failed and c['name'] == name),
                        'reasons': ['bytes differ'] if failed and c['name'] == name else [],
                        'reloc_order': 'EXACT'} for c in claims},
            'data': {'_DATA': {'exact': True, 'reasons': [], 'align': 'word', 'size': 2}},
            'extent': {'exact': not failed, 'reasons': ['length differs'] if failed else [],
                       'reloc_order': 'GROUPED'},
            'scaffold': [], 'object_sha256': canonical.sha(text.encode()), 'contribution_sha256': 'live'}
        collect = kwargs['collect']
        collect['code'] = [{'name': name, 'bytes': b'\x90\xcb' if not failed else b'\x91\xcb'}]
        collect['object'] = b'invented'
        return result

    def run_batch(self, rows=None, **kwargs):
        output = io.StringIO()
        with redirect_stdout(output):
            code = r.run(rows or [row()], **kwargs)
        return code, output.getvalue()

    def test_success_updates_all_ledgers_and_journal_once(self):
        code, output = self.run_batch([row(kind='recovered')])
        self.assertEqual(code, 0)
        self.assertIn('python portable/refresh_pins.py', output)
        self.assertIn('python tools/validate.py', output)
        symbols = self.read('layout/symbols.json')['code']
        self.assertNotIn('old', symbols)
        self.assertEqual(symbols['fresh']['history'], [{'was': 'old', 'why': 'invented DOS evidence'}])
        self.assertEqual(symbols['fresh']['name_kind'], 'recovered')
        program = self.read('src/program.json')
        module = self.read('layout/manifest.json')['modules'][self.key]
        raw = (self.root / self.source).read_bytes()
        self.assertEqual(module['source_sha256'], canonical.sha(raw))
        self.assertEqual(program['modules'][0]['source_sha256'], canonical.sha(raw))
        self.assertEqual(module['object_sha256'], canonical.sha(raw))
        self.assertEqual(module['claims'][0]['name'], 'fresh')
        self.assertEqual(module['claims'][0]['steered'], 'fresh requires original declaration order')
        self.assertEqual(program['aliases'][0]['target'], '_fresh')
        self.assertEqual(len((self.root / 'evidence/promotions.jsonl').read_text().splitlines()), 1)
        self.assertEqual(len(self.verifier.call_args_list), 2)
        self.assertEqual(self.verifier.call_args_list[1].args[1]['flags'], ['/AL', '/Os', '/Zi'])
        self.assertEqual(self.verifier.call_args_list[1].args[1]['extent'], self.module['extent'])

    def test_collision_in_local_registry_runtime_and_keywords(self):
        for new in ('value', 'peer', 'malloc', 'int', 'x' * 32, 'bad-name'):
            before = self.snapshot()
            with self.assertRaises(r.RenameError):
                self.run_batch([row(new=new)])
            self.assertEqual(self.snapshot(), before)
        self.text += 'int local_name;\n'
        self.module['source_sha256'] = canonical.sha(self.text.encode())
        self.program['modules'][0]['source_sha256'] = self.module['source_sha256']
        self.write(self.source, self.text)
        self.persist()
        with self.assertRaisesRegex(r.RenameError, 'identifier collision'):
            self.run_batch([row(new='local_name')])

    def test_failed_rename_leaves_every_file_untouched(self):
        self.fail_when = lambda text: 'fresh' in text
        before = self.snapshot()
        original_symbols = r.match.symbols
        code, output = self.run_batch()
        self.assertEqual(code, 1)
        self.assertIn('REFUSED SET: old=fresh', output)
        self.assertIn('fresh: first differing bytes +0x0: before=90cb after=91cb', output)
        self.assertEqual(self.snapshot(), before)
        self.assertIs(r.match.symbols, original_symbols)

    def test_verify_only_writes_nothing_outside_own_scratch(self):
        before = {p.relative_to(self.root): p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        code, _ = self.run_batch(verify_only=True)
        self.assertEqual(code, 0)
        for p in self.root.rglob('*'):
            if p.is_file() and not p.is_relative_to(self.root / 'build/scratch'):
                self.assertEqual(p.read_bytes(), before[p.relative_to(self.root)])
        self.assertEqual(self.snapshot(), {str(k).replace('\\', '/'): v for k, v in before.items()})
        self.assertFalse((self.root / 'build/locks').exists())

    def test_keep_going_reverifies_surviving_batch(self):
        self.fail_when = lambda text: 'fresh' in text
        code, _ = self.run_batch([row(), row('peer', 'renamed_peer')], keep_going=True)
        self.assertEqual(code, 1)
        symbols = self.read('layout/symbols.json')['code']
        self.assertIn('old', symbols)
        self.assertIn('renamed_peer', symbols)
        self.assertNotIn('fresh', symbols)
        journal = json.loads((self.root / 'evidence/promotions.jsonl').read_bytes())
        self.assertEqual(journal['renames'], [row('peer', 'renamed_peer')])

    def test_interacting_pair_failure_is_not_lost(self):
        self.fail_when = lambda text: 'fresh' in text and 'renamed_peer' in text
        before = self.snapshot()
        code, output = self.run_batch([row(), row('peer', 'renamed_peer')])
        self.assertEqual(code, 1)
        self.assertIn('old=fresh, peer=renamed_peer', output)
        self.assertEqual(self.snapshot(), before)

    def test_keep_going_retains_a_proven_member_of_an_interacting_pair(self):
        self.fail_when = lambda text: 'fresh' in text and 'renamed_peer' in text
        code, _ = self.run_batch([row(), row('peer', 'renamed_peer')], keep_going=True)
        self.assertEqual(code, 1)
        symbols = self.read('layout/symbols.json')['code']
        self.assertIn('fresh', symbols)
        self.assertIn('peer', symbols)
        self.assertNotIn('renamed_peer', symbols)

    def test_semantic_pin_changes_when_callee_or_function_is_renamed(self):
        semantic = {'function': 'peer', 'module': self.key, 'status': 'BEHAVIOR_EXACT_CONFIRMED',
                    'definition_sha256': canonical.definition_sha(self.text, 'peer'), 'receipt': 'evidence/peer.json'}
        self.program['semantics'] = [semantic]
        self.write(semantic['receipt'], json.dumps({
            'schema': 'simant-canonical-semantic-review-v1', **semantic,
            'audit': {'status': 'BEHAVIOR_EXACT_CONFIRMED', 'unexplained_semantic_differences': []},
            'root_review': {'reviewer': 'root', 'complete_cfg': True, 'complete_data_widths': True,
                            'complete_calls_effects': True, 'codegen_only_residue': True}}))
        self.persist()
        code, _ = self.run_batch([row(), row('peer', 'renamed_peer')])
        self.assertEqual(code, 0)
        current = self.read('src/program.json')['semantics'][0]
        receipt = self.read('evidence/peer.json')
        self.assertEqual(current['function'], 'renamed_peer')
        self.assertNotEqual(current['definition_sha256'], semantic['definition_sha256'])
        self.assertEqual(current['definition_sha256'], receipt['definition_sha256'])
        self.assertTrue(receipt['renamed'])
        canonical.check_semantic_review(current, (self.root / self.source).read_text())

    def test_concurrent_edit_is_preserved_before_any_write(self):
        before = self.snapshot()
        original = r.Session.stage_metadata
        def edited(session, rows, outcome):
            changes = original(session, rows, outcome)
            self.write(self.source, self.text + '/* concurrent */')
            return changes
        with patch.object(r.Session, 'stage_metadata', edited):
            with self.assertRaisesRegex(r.RenameError, 'changed during rename'):
                self.run_batch()
        after = self.snapshot()
        self.assertEqual(after.pop(self.source), (self.text + '/* concurrent */').encode())
        before.pop(self.source)
        self.assertEqual(after, before)

    def test_file_replace_failure_rolls_back_every_ledger(self):
        before = self.snapshot()
        original = r.os.replace
        count = 0
        def failing(source, target):
            nonlocal count
            count += 1
            if count == 3:
                raise OSError('invented I/O failure')
            return original(source, target)
        with patch.object(r.os, 'replace', side_effect=failing):
            with self.assertRaisesRegex(OSError, 'invented'):
                self.run_batch()
        self.assertEqual(self.snapshot(), before)

    def test_reviewed_context_rewrites_receipt_only_after_full_comparison(self):
        admission = {'receipt': 'evidence/admission.json', 'current_byte_exact': False}
        self.module['canonical_admission'] = admission
        # A reviewed extent failure is allowed only if already in the receipt.
        original = self.verify
        def reviewed(*args, **kwargs):
            result = original(*args, **kwargs)
            result['exact'] = False
            result['extent'] = {'exact': False, 'reasons': ['reviewed historical residue']}
            return result
        self.verifier.side_effect = reviewed
        with r.binding(self.syms):
            result = reviewed(self.text, self.module, self.module['claims'], collect={})
        self.write(admission['receipt'], json.dumps({'historical_comparisons': {self.key: {
            'contribution_sha256': 'live', 'comparison': canonical.observed(result)}}}))
        self.persist()
        obj = ObjectModule({}, [], [], [])
        obj.linker_fixups = []
        with patch.object(r.OmfReader, 'read', return_value=obj):
            code, output = self.run_batch()
        self.assertEqual(code, 0)
        self.assertIn('REVIEWED CONTEXT PRESERVED', output)
        receipt = self.read(admission['receipt'])
        self.assertIn('fresh', receipt['historical_comparisons'][self.key]['comparison']['claims'])
        self.assertFalse(receipt['historical_comparisons'][self.key]['comparison']['exact'])
        self.assertIn('renamed', receipt)

    def test_storage_contract_names_and_aliases_are_checked(self):
        from dos import build
        key, source = 'source-owned:invented', 'src/state/invented.c'
        text = 'int value;\n'
        contract = {'communals': [{'name': '_value', 'kind': 'near', 'length': 2}], 'publics': [],
                    'fixups': [], 'code_bytes': 0, 'live_initialized_bytes': 0}
        self.program['modules'].append({'key': key, 'source': source, 'lang': 'c', 'profile': 'msc600ax',
                                       'flags': ['/AL'], 'source_sha256': canonical.sha(text.encode()),
                                       'storage_contract': contract})
        self.program['aliases'].append({'alias': '_view2', 'target': '_value'})
        self.write(source, text)
        self.persist()
        obj = ObjectModule({}, [], [], [])
        obj.linker_fixups = []
        obj.communals = [{'name': '_fresh_value', 'kind': 'near', 'length': 2}]
        compiled = r.compiler.Result(True, b'invented', '', self.root, [])
        def parse(raw):
            return obj
        def compile_storage(text, *args):
            obj.communals[0]['name'] = '_fresh_value' if 'fresh_value' in text else '_value'
            return compiled
        # Baseline and candidate gates see their own recorded contract names.
        with patch.object(r.compiler, 'compile_c', side_effect=compile_storage), \
                patch.object(r.OmfReader, 'read', side_effect=parse), \
                patch.object(build, 'verify_storage', wraps=build.verify_storage) as storage_gate:
            code, _ = self.run_batch([row('value', 'fresh_value')])
        self.assertEqual(code, 0)
        current = self.read('src/program.json')
        storage = next(m for m in current['modules'] if m['key'] == key)
        self.assertEqual(storage['storage_contract']['communals'][0]['name'], '_fresh_value')
        self.assertEqual(current['aliases'][1]['target'], '_fresh_value')
        self.assertEqual(storage_gate.call_count, 2)

    def test_private_data_extent_and_relocation_failures_are_all_protected(self):
        original = self.verify
        for axis in ('data', 'extent', 'relocations', 'compile'):
            def fail(text, *args, **kwargs):
                result = original(text, *args, **kwargs)
                if 'fresh' not in text:
                    return result
                result['exact'] = False
                if axis == 'data':
                    result['data']['_DATA'].update(exact=False, reasons=['private data bytes differ'])
                elif axis == 'extent':
                    result['extent'].update(exact=False, reasons=['extent is not completely tiled'])
                elif axis == 'relocations':
                    result['extent'].update(exact=False, reasons=['relocation order differs'])
                else:
                    result.update(compile_ok=False, log='invented compilation failure')
                return result
            self.verifier.side_effect = fail
            before = self.snapshot()
            code, output = self.run_batch()
            self.assertEqual(code, 1, axis)
            self.assertEqual(before, self.snapshot(), axis)
            self.assertIn('REFUSED SET', output)

    def test_repeated_receipt_read_cannot_repin_a_concurrent_edit(self):
        self.write('evidence/receipt.json', '{}')
        session = r.Session(self.root / 'unused')
        session.receipt('evidence/receipt.json')
        self.write('evidence/receipt.json', '{"changed": true}')
        with self.assertRaisesRegex(r.RenameError, 'changed during rename'):
            session.receipt('evidence/receipt.json')

    def test_contract_reference_names_are_forwarded_to_verifier(self):
        item = self.program['modules'][0]
        item['owned_code_references'] = {'owners': [{'anchor_public': '_old'}]}
        item['data_frame_references'] = {'sites': [{'public': '_old'}]}
        self.persist()
        self.run_batch(verify_only=True)
        kwargs = self.verifier.call_args_list[1].kwargs
        self.assertEqual(kwargs['code_references']['owners'][0]['anchor_public'], '_fresh')
        self.assertEqual(kwargs['data_frame_references']['sites'][0]['public'], '_fresh')

    def test_source_pin_or_stale_semantic_receipt_refuses(self):
        before = self.snapshot()
        self.write(self.source, self.text + '/* stale */')
        with self.assertRaisesRegex(r.RenameError, 'source pin differs'):
            self.run_batch()
        self.write(self.source, before[self.source])
        self.program['semantics'] = [{'function': 'peer', 'module': self.key, 'status': 'BEHAVIOR_EXACT_CONFIRMED',
                                     'definition_sha256': 'stale', 'receipt': 'evidence/bad.json'}]
        self.write('evidence/bad.json', '{}')
        self.persist()
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, 'definition/review differs'):
            self.run_batch()
        self.assertEqual(self.snapshot(), before)


if __name__ == '__main__':
    unittest.main()
