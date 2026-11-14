import tempfile
import unittest
from pathlib import Path
from .sound_calls import read_calls


class SoundCallControls(unittest.TestCase):
    def test_qualified_and_diagnostic_paths_remain_visible(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'calls'
            path.write_text('SIMANT_SOUND_CALLS 1\nC 1 0 0 111 2 8240\nC 2 0 0 7 5 8240\nE 3 1 1\n')
            row=read_calls(path,ids=bytes([20]))
            self.assertEqual((row['calls'],row['pcm_calls'],row['nonpcm_calls']),(2,1,1))
            self.assertEqual(read_calls(path,service_limit=2)['calls'],1)
            with self.assertRaises(ValueError):read_calls(path,ids=b'')

    def test_incomplete_or_invalid_capture_cannot_pass(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'calls'
            for text in ('SIMANT_SOUND_CALLS 1\n',
                         'SIMANT_SOUND_CALLS 1\nE 3 1 1\nC 4 1 1 1 2 8240\n',
                         'SIMANT_SOUND_CALLS 1\nC 3 0 1 1 2 8240\nE 3 1 1\n',
                         'SIMANT_SOUND_CALLS 1\nC 2 0 0 1 65536 8240\nE 3 1 1\n'):
                path.write_text(text)
                with self.assertRaises(ValueError):read_calls(path)
