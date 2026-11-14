import tempfile
import unittest
from pathlib import Path
from .audio_content import compare_content, opl_channel


class ContentControls(unittest.TestCase):
    def compare(self, a, b, tolerance=1):
        with tempfile.TemporaryDirectory() as directory:
            paths = [Path(directory) / name for name in ('dos', 'native')]
            for path, rows in zip(paths, (a, b)):
                paired=[]
                for row in rows:
                    paired.append(row)
                    if row.startswith('P '):
                        paired.append(' '.join(row.split()[:5])+ ' 1 -1 0 128')
                path.write_text('SIMANT_AUDIO_CONTENT 1\n' + '\n'.join(paired) + '\n')
            return compare_content(*paths, entries=1, tolerance=tolerance)

    def rows(self):
        return ['S 1 1 0 0 0 23 256 0 2 2 0 4 80828486',
                'O 1 1 0 0 0 32 1', 'P 2 2 0 0 0 23 1 130',
                'P 3 3 0 0 0 23 2 132', 'X 4 4 0 0 0',
                'C 4 5 1 1 12345678 ABCDEF01', 'E 4 5 1 1']

    def test_equal_and_one_tick_placement(self):
        a = self.rows()
        self.assertEqual(self.compare(a, a)['status'], 'AUDIO_EQUAL')
        b = [row.replace(' 1 ', ' 1 ', 1) for row in a]
        # Shift the whole voice by exactly one fast tick, keeping values/order.
        b = [' '.join([v[0], str(int(v[1]) + 1), *v[2:]]) for v in map(str.split, b)]
        self.assertEqual(self.compare(a, b)['status'], 'AUDIO_EQUAL')
        self.assertEqual(self.compare(a, b, 0)['status'], 'AUDIO_DIFFERENCE')

    def test_opl_interleaving_is_independent_but_channel_order_is_strict(self):
        a = ['O 1 1 0 0 0 32 1', 'O 1 1 0 0 0 33 2',
             'C 1 2 1 1 1234', 'E 1 2 1 1']
        b = [a[1], a[0], *a[2:]]
        self.assertEqual(self.compare(a, b)['status'], 'AUDIO_EQUAL')
        b[0] = b[0][:-1] + '3'
        self.assertEqual(self.compare(a, b)['first_difference']['kind'], 'OPL_CONTENT')
        self.assertEqual(opl_channel(0x20), opl_channel(0x23))
        self.assertEqual(opl_channel(0x20), opl_channel(0xb0))
        self.assertIsNone(opl_channel(0x26))

    def test_negative_identity_rate_volume_payload_and_output(self):
        a = self.rows()
        for old, new, kind in [('23 256', '24 256', 'SAMPLE_IDENTITY_OR_CONTENT'),
                               ('256 0', '257 0', 'SAMPLE_IDENTITY_OR_CONTENT'),
                               ('256 0', '256 1', 'SAMPLE_IDENTITY_OR_CONTENT'),
                               ('80828486', '80828586', 'SAMPLE_IDENTITY_OR_CONTENT'),
                               ('1 130', '1 131', 'SAMPLE_OUTPUT_BYTE')]:
            with self.subTest(change=new):
                b = [s.replace(old, new) for s in a]
                r = self.compare(a, b)
                # Changing the identity in only the start also violates capture
                # consistency, which must be incomplete rather than accepted.
                self.assertIn(r['status'], ('AUDIO_DIFFERENCE', 'AUDIO_INCOMPLETE'))
                if r['first_difference']:
                    self.assertEqual(r['first_difference']['kind'], kind)

    def test_missing_and_interior_output_not_aligned_away(self):
        a = self.rows()
        self.assertEqual(self.compare(a, a[:-1])['status'], 'AUDIO_INCOMPLETE')
        b = [s for s in a if not s.startswith('P 2')]
        self.assertEqual(self.compare(a, b)['first_difference']['kind'], 'SAMPLE_OUTPUT_BYTE')
        b = [s for s in a if not s.startswith('P 3')]
        self.assertEqual(self.compare(a, b)['status'], 'AUDIO_EQUAL')
        self.assertEqual(self.compare(a, b, 0)['status'], 'AUDIO_DIFFERENCE')

    def test_stop_tolerance_only_allows_terminal_duration_change(self):
        a = self.rows()
        b = a[:4] + ['P 4 4 0 0 0 23 3 134', 'X 5 5 0 0 0',
                     'C 5 6 1 1 12345678 ABCDEF01', 'E 5 6 1 1']
        self.assertEqual(self.compare(a, b)['status'], 'AUDIO_EQUAL')
        self.assertEqual(self.compare(a, b, 0)['status'], 'AUDIO_DIFFERENCE')

    def test_per_entry_progress_needs_observed_nearby_state_symmetrically(self):
        a = ['Q 2 1 0 0 1234', 'C 3 2 1 1 5678', 'E 3 2 1 1']
        b = ['Q 2 1 0 0 5678', 'C 3 2 1 1 1234', 'E 3 2 1 1']
        self.assertEqual(self.compare(a, b)['status'], 'AUDIO_EQUAL')
        self.assertEqual(self.compare(a, b, 0)['first_difference']['kind'], 'MUSIC_PROGRESS')
        b[0] = b[0].replace('5678', '9999')
        self.assertEqual(self.compare(a, b)['status'], 'AUDIO_DIFFERENCE')

    def test_mono_sample_slot_is_not_sample_identity(self):
        a=['S 1 1 0 0 0 23 256 0 2 2 0 4 80828486',
           'P 2 2 0 0 0 23 1 130','P 2 2 0 0 1 -1 0 128',
           'X 3 3 0 0 0','C 3 4 1 1 1234','E 3 4 1 1']
        b=['S 1 1 0 0 1 23 256 0 2 2 0 4 80828486',
           'P 2 2 0 0 0 -1 0 128','P 2 2 0 0 1 23 1 130',
           'X 3 3 0 0 1',*a[4:]]
        with tempfile.TemporaryDirectory() as directory:
            paths=[Path(directory)/n for n in ('dos','native')]
            for p,rows in zip(paths,(a,b)):p.write_text('SIMANT_AUDIO_CONTENT 1\n'+'\n'.join(rows)+'\n')
            self.assertEqual(compare_content(*paths,entries=1)['status'],'AUDIO_EQUAL')

    def test_audible_start_uses_emission_not_setup_instruction(self):
        a=['S 100 1 0 0 0 23 256 0 2 2 0 4 80828486',
           'P 1000 2 0 0 0 23 1 130','X 1002 3 0 0 0',
           'C 1002 4 1 1 1234','E 1002 4 1 1']
        b=[a[0].replace('S 100 ', 'S 200 '),*a[1:]]
        self.assertEqual(self.compare(a,b,0)['status'],'AUDIO_EQUAL')
        b=[b[0]]+[' '.join([f[0],str(int(f[1])+17),*f[2:]]) for f in map(str.split,b[1:])]
        self.assertEqual(self.compare(a,b,16)['status'],'AUDIO_DIFFERENCE')

    def test_device_controls_and_actual_dac_bind_the_observations(self):
        a = ['K 0 0 0 0 556 209', 'P 1 1 0 0 0 -1 0 130',
             'P 1 1 0 0 1 -1 0 128', 'C 1 2 1 1 1234', 'E 1 2 1 1']
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'content'
            path.write_text('SIMANT_AUDIO_CONTENT 1\n' + '\n'.join(a) + '\n')
            raw = Path(directory) / 'raw'
            for value, status in [('81', 'AUDIO_EQUAL'), ('82', 'AUDIO_INCOMPLETE')]:
                raw.write_text('SIMANT_AUDIO_COMMANDS 1\nW 1 0 0 22C 10\n'
                               f'W 1 0 0 22C {value}\nE 2 1 1\n')
                result = compare_content(path, path, 1, raw_dos_path=raw, raw_native_path=raw)
                self.assertEqual(result['status'], status)


if __name__ == '__main__':
    unittest.main()
