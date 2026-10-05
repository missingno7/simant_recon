"""Permanent negative controls for architecture and move-only output hygiene."""
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
sys.path.insert(0, str(ROOT / 'portable'))
import repository
import workspace
from canonical_native_abi import lexical, window_parameters


class OutputLifecycle(unittest.TestCase):
    def test_default_rotation_preserves_previous_output(self):
        with tempfile.TemporaryDirectory(dir=ROOT / 'build/workers') as folder:
            root = Path(folder)
            out = root / 'build/current/portable'
            out.mkdir(parents=True)
            (out / 'report.json').write_bytes(b'previous complete output')
            workspace.prepare_output(out, out, root)
            self.assertFalse((out / 'report.json').exists())
            self.assertEqual((root / 'to_delete/build/current/portable/report.json').read_bytes(),
                             b'previous complete output')
            (out / 'report.json').write_bytes(b'next output')
            workspace.prepare_output(out, out, root)
            self.assertEqual((root / 'to_delete/build/current/portable.1/report.json').read_bytes(),
                             b'next output')
            self.assertEqual(len((root / 'to_delete/moves.jsonl').read_text().splitlines()), 2)

    def test_explicit_existing_output_is_refused(self):
        with tempfile.TemporaryDirectory(dir=ROOT / 'build/workers') as folder:
            root = Path(folder)
            out = root / 'build/workers/task'
            out.mkdir(parents=True)
            with self.assertRaises(ValueError):
                workspace.prepare_output(out, root / 'build/current/portable', root)
            self.assertTrue(out.is_dir())

    def test_source_dependencies_and_outside_targets_are_protected(self):
        with tempfile.TemporaryDirectory(dir=ROOT / 'build/workers') as folder:
            root = Path(folder)
            for name in ('src/module.c', 'layout/manifest.json', '.git/index', 'assets/a.dat',
                         'to_delete/anything'):
                with self.assertRaises(ValueError, msg=name):
                    workspace.retire(root / name, root)
            with self.assertRaises(ValueError):
                workspace.retire(root.parent / 'outside', root)
            with self.assertRaises(ValueError):
                workspace.prepare_output(root / 'build/deps/sdk', root / 'build/current/portable', root)

    def test_build_ancestor_cannot_retire_dependencies(self):
        with tempfile.TemporaryDirectory(dir=ROOT / 'build/workers') as folder:
            root = Path(folder)
            dependency = root / 'build/deps/sdk/pinned.txt'
            dependency.parent.mkdir(parents=True)
            dependency.write_bytes(b'pinned dependency')
            with self.assertRaises(ValueError):
                workspace.retire(root / 'build', root)
            self.assertEqual(dependency.read_bytes(), b'pinned dependency')
            self.assertFalse((root / 'to_delete').exists())

    def test_prepare_output_rejects_redirect_before_resolving(self):
        with tempfile.TemporaryDirectory(dir=ROOT / 'build/workers') as folder:
            root = Path(folder).resolve()
            target = root / 'build/current/portable'
            target.mkdir(parents=True)
            marker = target / 'report.json'
            marker.write_bytes(b'previous complete output')
            alias = root / 'build/current/redirect'
            resolve = Path.resolve
            # Model a redirect without requiring Windows symlink privileges.
            def redirected_resolve(path, *args, **kwargs):
                return target if path == alias else resolve(path, *args, **kwargs)
            with patch.object(Path, 'resolve', redirected_resolve), \
                 patch.object(Path, 'is_symlink', lambda path: path == alias):
                with self.assertRaisesRegex(ValueError, 'redirected retirement target'):
                    workspace.prepare_output(alias, alias, root)
            self.assertEqual(marker.read_bytes(), b'previous complete output')
            self.assertFalse((root / 'to_delete').exists())

    def test_redirect_cannot_target_source_or_dependencies(self):
        with tempfile.TemporaryDirectory(dir=ROOT / 'build/workers') as folder:
            root = Path(folder).resolve()
            alias = root / 'build/current/redirect'
            resolve = Path.resolve
            for relative in ('src', 'build/deps/sdk'):
                target = root / relative
                target.mkdir(parents=True)
                marker = target / 'pinned.txt'
                marker.write_bytes(b'protected input')
                def redirected_resolve(path, *args, **kwargs):
                    return target if path == alias else resolve(path, *args, **kwargs)
                with patch.object(Path, 'resolve', redirected_resolve):
                    with self.assertRaises(ValueError, msg=relative):
                        workspace.prepare_output(alias, alias, root)
                self.assertEqual(marker.read_bytes(), b'protected input')

    def test_fresh_default_descendant_can_be_created(self):
        with tempfile.TemporaryDirectory(dir=ROOT / 'build/workers') as folder:
            root = Path(folder)
            default = root / 'build/current/portable'
            default.mkdir(parents=True)
            marker = default / 'report.json'
            marker.write_bytes(b'previous complete output')
            output = workspace.prepare_output(default / 'experiment', default, root)
            self.assertTrue(output.is_dir())
            self.assertEqual(marker.read_bytes(), b'previous complete output')

    def test_junction_detection_on_supported_python_runtime(self):
        path = ROOT / 'build/current/redirect'
        junction_tag = getattr(workspace.stat, 'IO_REPARSE_TAG_MOUNT_POINT', -1)
        with patch.object(Path, 'is_symlink', return_value=False), \
             patch.object(Path, 'lstat', return_value=SimpleNamespace(st_reparse_tag=junction_tag)):
            self.assertTrue(workspace._redirected(path))
        with patch.object(Path, 'is_symlink', return_value=False), \
             patch.object(Path, 'lstat', return_value=SimpleNamespace(st_reparse_tag=0)):
            self.assertFalse(workspace._redirected(path))


class ArchitectureControls(unittest.TestCase):
    def setUp(self):
        self.spec = json.loads((ROOT / 'layout/repository.json').read_text())
        self.live = {row['id'] for row in json.loads((ROOT / 'portable/platform.json').read_text())['preview_limitations']}

    def test_current_architecture(self):
        result = repository.audit(ROOT / 'layout/repository.json')
        self.assertTrue(result['passed'], result['issues'])

    def test_closed_contract_cannot_retain_temporary_adapter(self):
        issues = []
        repository._check_lowering(self.spec, self.live - {'native-index-adjacency'}, issues)
        self.assertTrue(any(row['code'] == 'exception_blocker_not_live' and
                            row['path'] == 'findindex_native_guard' for row in issues))

    def test_unregistered_transform_is_detected(self):
        self.spec['lowering'] = [row for row in self.spec['lowering'] if row['module'] != 'scalar']
        issues = []
        repository._check_lowering(self.spec, self.live, issues)
        self.assertTrue(any(row['code'] == 'abi_module_unregistered' for row in issues))

    def test_retired_api_cannot_reappear(self):
        issues = []
        with patch.object(Path, 'exists', lambda p: p == ROOT / 'tools/rename.py'):
            repository._check_spec(self.spec, issues)
        self.assertTrue(any(row['code'] == 'retired_path_present' for row in issues))

    def test_default_root_rejects_old_generations(self):
        issues = []
        with patch.object(Path, 'exists', return_value=True), \
             patch.object(Path, 'iterdir', return_value=iter([ROOT / 'build/portable-final2'])):
            repository._check_build_root(issues)
        self.assertEqual(issues[0]['code'], 'build_root_layout')

    def test_copy_source_is_checked_even_on_output_lines(self):
        fixture = (
            "out = shutil.copyfile(ROOT / 'to_delete/source.c', destination)\n"
            "shutil.copyfile(src=ROOT / 'build/scratch/source.c', dst=destination)\n"
            "shutil.copyfile(source, ROOT / 'build/scratch/output.c')\n"
        )
        issues = []
        with patch.object(Path, 'glob', return_value=[]), \
             patch.object(Path, 'rglob', return_value=[]), \
             patch.object(Path, 'read_text', lambda path, **kwargs:
                          fixture if path == ROOT / 'dos/build.py' else 'pass\n'):
            repository._check_production_literals(issues)
        self.assertEqual([(row['code'], row['detail']) for row in issues], [
            ('retired_or_scratch_input', 'to_delete/source.c'),
            ('retired_or_scratch_input', 'build/scratch/source.c'),
        ])


class SharedLexicalControls(unittest.TestCase):
    def test_literals_and_comments_cannot_be_lowered_as_calls(self):
        source = '/* win_Swap(1,2) */\nchar *s = "win_Open(3)";\nwin_Open(w, x+1, f(2,3));\n'
        output, _ = window_parameters.adapt(source, 'test.c')
        self.assertIn('/* win_Swap(1,2) */', output)
        self.assertIn('"win_Open(3)"', output)
        self.assertIn('win_Open(w, 2, x+1, f(2,3), 0, 0)', output)

    def test_unproved_argument_count_fails_closed(self):
        with self.assertRaises(ValueError):
            window_parameters.adapt('win_Open(w, x);', 'test.c')

    def test_mask_preserves_offsets_and_newlines(self):
        source = '#define X "escaped \\\" quote"\n/* a\nb */ f(\'x\'); // tail\n'
        masked = lexical.mask_literals(source)
        self.assertEqual(len(masked), len(source))
        self.assertEqual([i for i,c in enumerate(source) if c == '\n'],
                         [i for i,c in enumerate(masked) if c == '\n'])
        self.assertIn('#define X', masked)
        self.assertIn('f(   );', masked)


if __name__ == '__main__':
    unittest.main()
