"""Controls for exact per-entry audio writes and separate service coordinates."""
import json
from pathlib import Path
import tempfile
import unittest

from .audio_commands import HEADER, compare_commands, decoded_commands, read_commands


class AudioCommands(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.out = Path(self.directory.name)

    def capture(self, name, lines, end='E 12 3 1'):
        path = self.out / name
        path.write_text(HEADER + '\n' + '\n'.join(lines) + '\n' + end + '\n')
        return path

    def test_exact_empty_intervals_and_opl_registers(self):
        lines = ['W 0 0 0 388 A0', 'W 0 0 0 389 8F',
                 'W 5 1 0 388 B0', 'W 5 1 0 389 2E']
        a = self.capture('dos', lines)
        b = self.capture('native', lines)
        result = compare_commands(a, b, self.out, entries=3)
        self.assertEqual(result['status'], 'AUDIO_COMMANDS_EQUAL')
        self.assertEqual([r['raw_writes'] for r in result['rows']], [[2, 2], [2, 2], [0, 0]])
        self.assertEqual(json.loads((self.out / 'audio-commands.json').read_text()), result)
        b = self.capture('native', lines[:-1] + ['W 5 1 0 389 2F'])
        result = compare_commands(a, b, entries=3)
        self.assertEqual(result['first_differing_entry'], 2)
        first = result['first_difference']
        self.assertEqual(first['write_index'], 1)
        self.assertEqual(first['native']['decoded']['register'], 0xb0)
        self.assertEqual(first['native']['decoded']['value'], 0x2f)

    def test_same_commands_other_entry_fail_and_ordinals_are_separate(self):
        a = self.capture('dos', ['W 2 0 0 22C D1'])
        b = self.capture('native', ['W 3 0 0 22C D1'])
        result = compare_commands(a, b)
        self.assertEqual(result['status'], 'AUDIO_COMMANDS_EQUAL')
        self.assertEqual(result['coordinates_status'], 'ORDINAL_DRIFT')
        self.assertEqual(result['first_coordinate_drift']['entry'], 1)
        b = self.capture('native', ['W 3 1 1 22C D1'])
        result = compare_commands(a, b)
        self.assertEqual(result['status'], 'AUDIO_COMMANDS_DIFFERENCE')
        self.assertEqual(result['first_differing_entry'], 1)
        self.assertIsNone(result['first_difference']['native'])

    def test_no_reordering_deduplication_or_dropped_selector_writes(self):
        a = self.capture('dos', ['W 0 0 0 388 20', 'W 0 0 0 389 21',
                                 'W 0 0 0 388 20', 'W 0 0 0 389 21'])
        b = self.capture('native', ['W 0 0 0 388 20', 'W 0 0 0 389 21'])
        self.assertEqual(compare_commands(a, b)['status'], 'AUDIO_COMMANDS_DIFFERENCE')
        b = self.capture('native', ['W 0 0 0 389 21', 'W 0 0 0 388 20',
                                    'W 0 0 0 388 20', 'W 0 0 0 389 21'])
        self.assertEqual(compare_commands(a, b)['first_difference']['write_index'], 0)

    def test_dsp_argument_crosses_entry_and_dma_start_is_reported(self):
        lines = ['W 0 0 0 22C 10', 'W 2 1 0 22C D1',
                 'W 3 1 0 00C 00', 'W 3 1 0 002 34', 'W 3 1 0 002 12',
                 'W 3 1 0 00A 01', 'W 3 1 0 22C 14',
                 'W 3 1 0 22C FF', 'W 3 1 0 22C 00']
        a = self.capture('dos', lines)
        writes, _ = read_commands(a)
        events = list(decoded_commands(writes))
        direct = events[0]
        self.assertEqual((direct['command'], direct['arguments']), (0x10, [0xd1]))
        self.assertEqual(direct['raw_indices'], [0, 1])
        self.assertEqual(sum(e['kind'] == 'dma_unmask' for e in events), 1)
        dma = next(e for e in events if e['kind'] == 'dsp_dma_start')
        self.assertEqual(dma['arguments'], [255, 0])
        b = self.capture('native', lines[:1] + ['W 2 1 0 22C D3'] + lines[2:])
        result = compare_commands(a, b)
        self.assertEqual(result['first_difference']['native']['decoded']['command'], 0x10)
        self.assertEqual(result['first_difference']['native']['decoded']['arguments'], [0xd3])

    def test_prefix_and_incomplete_replay_never_claim_equality(self):
        a = self.capture('dos', [], end='E 12 3 1')
        b = self.capture('native', [], end='E 5 2 1')
        self.assertEqual(compare_commands(a, b, entries=3)['status'], 'AUDIO_COMMANDS_INCOMPLETE')
        self.assertEqual(compare_commands(a, b, entries=2)['status'], 'AUDIO_COMMANDS_EQUAL')
        self.assertEqual(compare_commands(a, b, entries=2, replay_complete=False)['status'], 'AUDIO_COMMANDS_INCOMPLETE')
        self.assertEqual(compare_commands(a, self.out / 'absent')['status'], 'AUDIO_COMMANDS_INCOMPLETE')

    def test_malformed_or_truncated_capture_fails_closed(self):
        for lines, end in [([], ''), (['W 0 0 0 388 100'], 'E 1 1 1'),
                           (['W 3 1 1 388 20', 'W 2 1 1 389 21'], 'E 5 2 1'),
                           (['W 0 0 0 388 20'], 'E 1 0 2'),
                           (['W 0 0 0 999 00'], 'E 1 1 1'),
                           ([], 'E 1 1 1\nW 1 1 1 388 00')]:
            with self.subTest(lines=lines, end=end):
                path = self.capture('bad', lines, end)
                with self.assertRaises(ValueError):
                    read_commands(path)


if __name__ == '__main__':
    unittest.main()
