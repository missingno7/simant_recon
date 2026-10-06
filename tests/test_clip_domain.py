"""Original clip generation must preserve the pre-diagnostic sentinel overrun."""
import importlib.util
import json
from pathlib import Path
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('clip_domain_replay',
    ROOT/'evidence/canonical/clip-domain/replay.py')
REPLAY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(REPLAY)


class ClipDomain(unittest.TestCase):
    def test_original_threshold_and_write_before_diagnostic(self):
        positive, negative = REPLAY.controls()
        self.assertEqual((positive['windows'], positive['visible_rectangles']), (29, 225))
        self.assertTrue(positive['completed'])
        self.assertEqual(positive['boundary_events'], [])
        self.assertEqual((negative['windows'], negative['visible_rectangles']), (31, 256))
        self.assertFalse(negative['completed'])
        write, diagnostic = negative['boundary_events']
        self.assertEqual((write['displacement'], write['bytes'], write['pc']), (2050, 2, '1D8E:02AD'))
        self.assertEqual((diagnostic['message'], diagnostic['count']), ('C097: Clip overflow %d', 256))
        self.assertTrue(all(case['pairwise_nonoverlap'] for case in (positive, negative)))

    def test_changed_reviewed_source_is_rejected(self):
        read = Path.read_bytes
        for relative in REPLAY.SOURCE_PINS:
            def changed(path):
                raw = read(path)
                return raw+b'\n/* source mutation */\n' if path == ROOT/relative else raw
            with self.subTest(source=relative), mock.patch.object(Path, 'read_bytes', changed):
                with self.assertRaisesRegex(ValueError, 'reviewed source pin differs'):
                    REPLAY.controls()

    def test_changed_oracle_is_rejected(self):
        with mock.patch.object(REPLAY, 'ORACLE_PIN', '0'*64):
            with self.assertRaisesRegex(ValueError, 'reviewed oracle pin differs'):
                REPLAY.controls()
        read = Path.read_bytes
        def changed(path):
            raw = read(path)
            return raw+b'oracle mutation' if path == REPLAY.exe.load().path else raw
        with mock.patch.object(Path, 'read_bytes', changed):
            with self.assertRaisesRegex(ValueError, 'reviewed oracle pin differs'):
                REPLAY.controls()

    def test_stale_canonical_inventory_is_rejected(self):
        read = Path.read_bytes
        def changed(path):
            raw = read(path)
            if path == ROOT/'src/program.json':
                program = json.loads(raw)
                for row in program['modules']:
                    if row['source'] in REPLAY.SOURCE_PINS:
                        row['source_sha256'] = '0'*64
                return json.dumps(program).encode()
            return raw
        with mock.patch.object(Path, 'read_bytes', changed):
            with self.assertRaisesRegex(ValueError, 'canonical inventory pin differs'):
                REPLAY.controls()


if __name__ == '__main__':
    unittest.main()
