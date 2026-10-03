"""The standalone lane must expose debt and never import the hybrid oracle."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import csrc
import compiler
import dos_source_bindings as bindings
from omf import OmfReader
import source_only_dos as dos


class SourceOnlyDosTests(unittest.TestCase):
    def test_oracle_read_guard_in_isolated_process(self):
        # The audit hook is intentionally permanent: isolate it from historical tests.
        program = (
            "import sys; from pathlib import Path; sys.path.insert(0,'tools'); "
            "import source_only_dos as d; denied=d.install_input_guard(); "
            "p=d.ROOT/'assets'/'SIMANT.EXE'; "
            "\ntry: p.read_bytes()\nexcept PermissionError: pass\n"
            "else: raise AssertionError('oracle read allowed')\n"
            "assert len(denied)==1\n"
        )
        run = subprocess.run([sys.executable, '-c', program], cwd=ROOT,
                             capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)

    def test_aliases_do_not_rewrite_literals_or_comments(self):
        source = '/* old_name */ char *s="old_name"; int old_name;'
        self.assertEqual(dos.rename_identifiers(source, {'old_name': 'new_name'}),
                         '/* old_name */ char *s="old_name"; int new_name;')

    def test_preparation_uses_registered_bodies_and_preserves_module_order(self):
        worker = ROOT / 'build/workers/source_only_dos_tests'
        worker.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=worker) as directory:
            report = {'inputs': [], 'generated_files': [], 'translation_units': [],
                      'semantic_substitutions': []}
            manifest, symbols = dos.prepare(Path(directory), report)
            self.assertEqual(len(report['translation_units']), len(manifest['modules']))
            self.assertEqual(report['function_dispositions'], {
                'EXACT_C': 1244, 'GENUINE_ASM': 367, 'BEHAVIOR_EXACT': 29, 'UNRESOLVED': 0})
            self.assertEqual(len(report['semantic_substitutions']), 29)
            aliases = dos.identifier_aliases(symbols)
            for row in report['translation_units']:
                original = (ROOT / row['source']['path']).read_text(encoding='latin1')
                generated = (ROOT / row['generated_source']['path']).read_text(encoding='latin1')
                if row['lang'] == 'asm':
                    if not row.get('source_binding'):
                        self.assertEqual(generated, original)
                elif row['reviewed_bodies']:
                    names_before = [aliases.get(f.name, f.name) for f in csrc.Source(original).functions()]
                    names_after = [f.name for f in csrc.Source(generated).functions()]
                    self.assertEqual(names_before, names_after, row['module'])
                    self.assertNotIn('SCAFFOLD BEGIN', generated)
            # Live/unknown data dispositions must remain visible, never emitted as bytes.
            self.assertEqual(sum(r['size'] for r in report['unresolved_data']), 113)
            self.assertTrue(any(r['classification'] == 'UNKNOWN_FIELD_SEMANTICS'
                                for r in report['unresolved_data']))

    def test_stale_registered_source_rejected(self):
        with self.assertRaisesRegex(ValueError, 'stale source/evidence pin'):
            dos.pin(ROOT / 'README.md', '0' * 64)

    def test_reviewed_body_cannot_use_different_macro_or_type_context(self):
        original = '#define WIDTH 2\nstruct X { int a; };\nint f(int n) { return n; }'
        self.assertEqual(dos.reviewed_context(original, original, 'f')['status'], 'MATCH')
        for changed in (original.replace('WIDTH 2', 'WIDTH 4'),
                        original.replace('int a;', 'long a;'),
                        original.replace('int n)', 'long n)')):
            with self.assertRaises(ValueError):
                dos.reviewed_context(original, changed, 'f')

    def test_link_refuses_debt_before_launching_tool(self):
        report = {'errors': [], 'unresolved_functions': [], 'unresolved_data': [{'id': 'unknown'}],
                  'translation_units': []}
        dos.link_units(ROOT / 'build/workers/source_only_dos_tests/never-link', report, 'rtlink400')
        self.assertIn('independent link refused: incomplete source/data preflight', report['errors'])

    def test_binding_proof_rejects_wrong_frames_and_unrelated_instruction_changes(self):
        packet = json.loads((ROOT / 'work/source-only-dos/source-bindings-v1.json').read_text())
        binding = next(r for r in packet['bindings'] if r['module'] == 'S01:3126')
        module = json.loads((ROOT / 'layout/manifest.json').read_text())['modules'][binding['module']]
        canonical = dos.pin(ROOT / binding['source'], binding['source_sha256'])[0].decode('latin1')
        generated = bindings.apply_binding(canonical.replace('\r\n', '\n'), binding)
        def assemble(text):
            result = compiler.assemble(text, module['profile'], module['flags'], basename='CONTROL')
            self.assertTrue(result.ok, result.log)
            return OmfReader().read(result.obj)
        control = assemble(canonical)
        self.assertEqual(bindings.verify_objects(control, assemble(generated), binding)['status'], 'PASS')
        # These are separately assembled source contrasts, never patched objects.
        for contrast in (generated.replace('assume ss:DGROUP', 'assume ss:nothing'),
                         generated.replace('OFFSET DGROUP:_g_3DFC', 'OFFSET _g_3DFC'),
                         generated.replace('mov cx, 4000h', 'mov cx, 4001h')):
            self.assertTrue(contrast != generated, 'contrast did not change source')
            with self.assertRaises(ValueError):
                bindings.verify_objects(control, assemble(contrast), binding)

    def test_binding_proof_rejects_exporting_a_different_timer_word(self):
        packet = json.loads((ROOT / 'work/source-only-dos/source-bindings-v1.json').read_text())
        binding = next(r for r in packet['bindings'] if r['module'] == 'root:1B73')
        module = json.loads((ROOT / 'layout/manifest.json').read_text())['modules'][binding['module']]
        canonical = dos.pin(ROOT / binding['source'], binding['source_sha256'])[0].decode('latin1')
        generated = bindings.apply_binding(canonical.replace('\r\n', '\n'), binding)
        label = '_fd_1B73_0006 label word\n'
        contrast = generated.replace(label, '').replace('mickey_mode\tdb', label+'mickey_mode\tdb')
        def assemble(text):
            result = compiler.assemble(text, module['profile'], module['flags'], basename='TIMER')
            self.assertTrue(result.ok, result.log)
            return OmfReader().read(result.obj)
        control = assemble(canonical)
        self.assertEqual(bindings.verify_objects(control, assemble(generated), binding)['status'], 'PASS')
        with self.assertRaisesRegex(ValueError, 'exported wrong storage'):
            bindings.verify_objects(control, assemble(contrast), binding)


if __name__ == '__main__':
    unittest.main()
