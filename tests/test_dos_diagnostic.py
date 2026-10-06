"""Diagnostic admission must never relax canonical DOS acceptance."""
import copy
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from dos import build, diagnostic, run


class DiagnosticPolicy(unittest.TestCase):
    def test_saved_game_is_explicit_user_data_with_safe_guest_name(self):
        path = ROOT / 'build/workers/example/a.ant'
        with patch.object(build, 'read_pin', return_value=(b'save bytes', {'sha256': 'pin'})):
            self.assertEqual(run.saved_game_input(path), ('A.ANT', b'save bytes', {'sha256': 'pin'}))
        for name in ('SOURCE.EXE', 'longfilename.ant', 'a&b.ant', 'A.ANT\nexit'):
            with self.assertRaises(ValueError):
                run.saved_game_input(path.with_name(name))
        for path in ('assets/A.ANT', 'src/A.ANT', 'to_delete/A.ANT'):
            with self.assertRaises(ValueError):
                run.saved_game_input(ROOT / path)
        with patch.object(build, 'prepare_output') as prepare:
            with self.assertRaises(SystemExit):
                run.main(['--original', '--out', 'build/workers/example/run', '--saved-game', 'assets/SIMANT.EXE'])
            prepare.assert_not_called()

    def test_keyboard_recipe_rejects_shell_and_host_actions_before_output(self):
        for key in ('enter > HACK', 'enter\nexit', 'mapper', 'shutdown', '-w', 'ENTER'):
            with self.assertRaises(ValueError):
                run.keyboard_command([key], 5, 2)
        for delay, pace in ((float('nan'), 2), (5, float('inf')), (-1, 2), (31, 2), (5, 11)):
            with self.assertRaises(ValueError):
                run.keyboard_command(['enter'], delay, pace)
        with patch.object(build, 'prepare_output') as prepare:
            with self.assertRaises(SystemExit):
                run.main(['--original', '--out', 'build/workers/example/run', '--key', 'enter&exit'])
            prepare.assert_not_called()

    def test_keyboard_recipe_preserves_pause_and_schedules_guest_keys_only(self):
        self.assertEqual(run.keyboard_command(['enter', ',', 'esc'], 5, 2),
                         'AUTOTYPE -w 5 -p 2 enter , esc > INPUT.LOG')
        self.assertIsNone(run.keyboard_command([], 5, 2))

    def test_video_entry_does_not_hide_later_unhandled_cpu_fault(self):
        prefix = b'1 INT10:Set Video Mode 12\n2 VGA:640x480, 59.94Hz\n'
        fault = b'3 ERROR CPU:Illegal Unhandled Interrupt Called 6\n'
        report = run.runtime_observations(prefix + fault * 20)
        self.assertEqual(len(report['functional_milestones_verified']), 1)
        self.assertEqual(report['runtime_faults']['count'], 20)
        self.assertEqual(len(report['runtime_faults']['first_lines']), 8)
        self.assertEqual(run.runtime_observations(prefix)['runtime_faults']['count'], 0)

    def test_inventory_loader_refuses_provisional_sources(self):
        program = json.loads((ROOT / 'src/program.json').read_text())
        for key, source in (('diagnostic:0', program['modules'][0]['source']),
                            (program['modules'][0]['key'], 'build/workers/example/provider.c')):
            trial = copy.deepcopy(program)
            trial['modules'][0].update(key=key, source=source)
            with patch.object(build, 'read_pin', return_value=(json.dumps(trial).encode(), {})):
                with self.assertRaisesRegex(ValueError, 'cannot be provisional'):
                    build.load_inventory(ROOT / 'src/program.json')

    def test_abort_with_zero_dos_exit_and_segment_loop_are_faults(self):
        segment = run.runtime_observations(b'Segment limit violation\nLimit check ffff+2-1 = 10000 > ffff DS:SI\n')
        self.assertEqual(segment['runtime_faults']['kind_counts']['segment_limit'], 1)
        abort = run.runtime_observations(b'', '\nFATAL ERROR: PROGRAM ABORTED\nanim_Remove objects not found\n')
        self.assertEqual(abort['runtime_faults']['kind_counts']['game_abort'], 1)
        benign = run.runtime_observations(b'Segment limit check passed\n', 'No FATAL ERROR: PROGRAM ABORTED here\n')
        self.assertEqual(benign['runtime_faults']['count'], 0)

    def test_production_cli_refuses_alternate_inventory_before_output(self):
        with patch.object(build, 'prepare_output') as prepare:
            with self.assertRaises(SystemExit):
                build.main(['--inventory', 'build/scratch/hypothesis.json'])
            prepare.assert_not_called()

    def test_production_refuses_all_diagnostic_debt(self):
        report = {'errors': [], 'translation_units': [], 'unresolved_symbols': [{'name': '_missing'}],
                  'unresolved_semantic_gates': [{'id': 'BOUND'}],
                  'unresolved_data': [{'bytes': 4}], 'provisional_assumptions': [{'symbol': '_missing'}]}
        with patch.object(build, '_link_program') as linker:
            build.link_program({}, ROOT / 'build/scratch/unused', report, 'rtlink400')
            linker.assert_not_called()
        self.assertEqual(report['link']['status'], 'REFUSED')
        self.assertEqual(len(report['link']['blockers']), 3)

    def test_provisional_paths_cannot_enter_sources_current_outputs_or_retired_tree(self):
        for name in ('src/state/provisional.c', 'build/current/dos/provisional.c',
                     'to_delete/provisional.c', 'assets/provisional.c'):
            with self.assertRaises(ValueError):
                diagnostic.experimental_path(ROOT / name)
        self.assertEqual(diagnostic.experimental_path(ROOT / 'build/workers/example/input.c'),
                         (ROOT / 'build/workers/example/input.c').resolve())

    def test_provider_must_cover_current_imports_exactly(self):
        report = {'unresolved_symbols': [{'name': '_missing'}]}
        for names in ([], ['_missing', '_extra'], ['_missing', '_missing']):
            with self.assertRaisesRegex(ValueError, 'exactly'):
                diagnostic.verify_providers([], [{'module': 'diagnostic:0', 'symbols': names}], report)

    def test_provider_cannot_contain_game_code_or_imports(self):
        canonical = {'unresolved_symbols': [{'name': '_missing'}]}
        row = {'key': 'diagnostic:0', 'status': 'COMPILED', 'object': {'path': 'unused', 'sha256': 'unused'}}
        assumptions = [{'module': 'diagnostic:0', 'symbols': ['_missing']}]
        clean = {'publics': [], 'communals': [{'name': '_missing'}], 'code_bytes': 0,
                 'local_publics': [], 'imports': [], 'fixups': []}
        with patch.object(build, 'read_pin', return_value=(b'', {})), patch.object(build.OmfReader, 'read'):
            with patch.object(build, 'storage_snapshot', return_value=clean):
                diagnostic.verify_providers([row], copy.deepcopy(assumptions), canonical)
            for key, bad in (('code_bytes', 1), ('imports', ['_function']),
                             ('fixups', [{}]), ('local_publics', [{}])):
                shape = dict(clean, **{key: bad})
                with patch.object(build, 'storage_snapshot', return_value=shape):
                    with self.assertRaisesRegex(ValueError, 'only the declared storage'):
                        diagnostic.verify_providers([row], assumptions, canonical)

    def test_execution_refuses_canonical_or_closure_receipts(self):
        with patch.object(run.diagnostic, 'experimental_path', side_effect=lambda p: Path(p)):
            for receipt in ({'target': 'CANONICAL_DOS'}, {'target': 'DIAGNOSTIC_DOS', 'closure_eligible': True}):
                with patch.object(build, 'read_pin', return_value=(json.dumps(receipt).encode(), {})):
                    with self.assertRaisesRegex(ValueError, 'successful diagnostic build receipt'):
                        run.diagnostic_image(ROOT / 'build/workers/example/build-report.json')

    def test_unknown_link_diagnostics_remain_fatal(self):
        for log in ("warning wrt0011: Public symbol '__ffree' doubly defined",
                    "warning wrt0011: Public symbol '__other' doubly defined", 'error wrt0031: unresolved _x',
                    'fixup error', 'fatal error', 'cannot open input'):
            self.assertTrue(build.linker_diagnostics(log))

    def test_execution_refuses_former_waived_link_warning(self):
        receipt = ROOT / 'build/workers/example/link/build-report.json'
        report = {'schema': 'simant-diagnostic-dos-build-v1', 'target': 'DIAGNOSTIC_DOS',
                  'status': 'DIAGNOSTIC_LINKED', 'closure_eligible': False, 'errors': [],
                  'original_exe_bytes_used': dict.fromkeys(
                      ('game_code', 'game_data', 'fallback_debt', 'executable_fragments'), 0),
                  'link': {'log': {'path': 'build/workers/example/link/link/LINK.LOG', 'sha256': 'pin'}}}
        for log in (b'', b"warning wrt0011: Public symbol '__ffree' doubly defined"):
            with patch.object(build, 'read_pin', side_effect=[(json.dumps(report).encode(), {}), (log, {})]):
                with self.assertRaisesRegex(ValueError, 'no linker warnings'):
                    run.diagnostic_image(receipt)

    def test_runtime_observations_distinguish_assets_from_overlay_reads(self):
        log = (b'931647 INT10:Set Video Mode 12\n938009 VGA:640x480, 59.94Hz\n'
               b'249 DEBUG FILES:Reading 880 bytes from SOURCE.EXE\n'
               b'250 DEBUG FILES:Reading 256 bytes from SHARED.DAT\n')
        observations = run.runtime_observations(log)
        self.assertEqual(len(observations['video_log_lines']), 2)
        self.assertEqual(observations['resource_read_events'], [{'file': 'SHARED.DAT', 'bytes': 256}])
        self.assertEqual(observations['functional_milestones_verified'][0]['id'], 'VGA_640X480_ENTRY')
        for invalid in (b'', log.replace(b'Mode 12', b'Mode 3'),
                        log.replace(b'640x480', b'320x200'),
                        b'VGA:640x480\nINT10:Set Video Mode 12\n'):
            self.assertEqual(run.runtime_observations(invalid)['functional_milestones_verified'], [])



if __name__ == '__main__':
    unittest.main()
