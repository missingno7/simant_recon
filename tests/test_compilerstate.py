"""The context research harness must reject ambiguous edits and deduplicate work."""
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import compilerstate


class ContextLedgerTests(unittest.TestCase):
    def test_missing_explicit_prior_ledger_cannot_silently_repeat_work(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch.object(compilerstate.modctx, 'under_build', side_effect=Path):
                with self.assertRaises(FileNotFoundError):
                    compilerstate.run({}, root / 'out', root / 'ledger.jsonl',
                                      [root / 'absent.jsonl'])

    def test_ambiguous_edit_rejected(self):
        with self.assertRaises(ValueError):
            compilerstate.edit_source('x x', [{'old': 'x', 'new': 'y'}])
        with self.assertRaises(ValueError):
            compilerstate.edit_source('x', [{'old': 'absent', 'new': 'y'}])

    def test_explicit_multiple_edits_are_sequential(self):
        self.assertEqual(compilerstate.edit_source('x x', [
            {'old': 'x', 'new': 'y', 'count': 2}, {'old': 'y y', 'new': 'z'}]), 'z')

    def test_same_source_context_deduplicated_across_hypothesis_wording(self):
        class Ctx:
            def module_dict(self):
                return {'profile': 'p', 'flags': ['/Og']}
        a = compilerstate.identity(Ctx(), 'f', 'base', 'lifetime', {'count': 0}, 'candidate')
        b = compilerstate.identity(Ctx(), 'f', 'base', 'declarations', {'count': 3}, 'candidate')
        self.assertEqual(a['equivalence_key'], b['equivalence_key'])
        self.assertNotEqual(a['experiment_key'], b['experiment_key'])
        c = compilerstate.identity(Ctx(), 'f', 'base', 'lifetime', {'count': 0}, 'changed')
        self.assertNotEqual(a['equivalence_key'], c['equivalence_key'])

    def test_flags_invalidate_equivalence(self):
        class Ctx:
            def __init__(self, flags):
                self.flags = flags
            def module_dict(self):
                return {'profile': 'p', 'flags': self.flags}
        a = compilerstate.identity(Ctx(['/Og']), 'f', 'b', 'd', {}, 'c')
        b = compilerstate.identity(Ctx(['/Os']), 'f', 'b', 'd', {}, 'c')
        self.assertNotEqual(a['equivalence_key'], b['equivalence_key'])


if __name__ == '__main__':
    unittest.main()
