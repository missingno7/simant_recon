"""Punt guard semantics and the four-slot exhaustion prefix stay explicit."""
import importlib.util
from pathlib import Path
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('error_continuation_replay',
    ROOT / 'evidence/canonical/error-continuation/replay.py')
REPLAY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(REPLAY)

class ErrorContinuation(unittest.TestCase):
    def test_original_guard_and_record_prefix_controls(self):
        receipt = REPLAY.probe()
        cases = receipt['cases']
        self.assertEqual(cases['Punt_guard'][0]['returns'], 'UNPROVED')
        self.assertTrue(all(c['returns'] for c in cases['Punt_guard'][1:]))
        self.assertEqual([c['Punt_calls'] for c in cases['DosPunt_guard']], [1, 2])
        self.assertEqual([c['out_of_record_owner'] for c in cases['OpenDB_copy_prefix']],
                         [False, False, False, False, True])
        self.assertEqual(cases['OpenDB_copy_prefix'][-1]['name_destination'], '50F6:38DC')

    def test_mutated_source_input_is_rejected_before_execution(self):
        original_read = Path.read_bytes
        for relative in REPLAY.SOURCE_PINS:
            target = ROOT / relative
            def changed(path):
                raw = original_read(path)
                return raw + b'\n/* pin mutation control */\n' if path == target else raw
            with self.subTest(source=relative), mock.patch.object(Path, 'read_bytes', changed):
                with self.assertRaisesRegex(ValueError, 'reviewed input pin differs'):
                    REPLAY.probe()

    def test_changed_oracle_identity_is_rejected_before_execution(self):
        with mock.patch.object(REPLAY, 'ORACLE_PIN', '0' * 64):
            with self.assertRaisesRegex(ValueError, 'reviewed oracle pin differs'):
                REPLAY.probe()

    def test_mutated_oracle_bytes_are_rejected_before_execution(self):
        original_read = Path.read_bytes
        def changed(path):
            raw = original_read(path)
            return raw + b'pin mutation' if path == REPLAY.IMAGE.path else raw
        with mock.patch.object(Path, 'read_bytes', changed):
            with self.assertRaisesRegex(ValueError, 'reviewed input pin differs: oracle'):
                REPLAY.probe()

if __name__ == '__main__':
    unittest.main()
