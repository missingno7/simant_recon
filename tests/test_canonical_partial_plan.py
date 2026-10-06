"""Partial publication still loads and verifies every pinned canonical TU."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import canonical


class ReachedSemanticReview(Exception):
    pass


class PartialPlan(unittest.TestCase):
    def setUp(self):
        self.program = canonical.load()
        self.plan = {'program': copy.deepcopy(self.program), 'files': [],
                     'prior_program_sha256': canonical.sha(canonical.PROGRAM.read_bytes()),
                     'prior_manifest_sha256': canonical.sha((ROOT / 'layout/manifest.json').read_bytes())}

    def run_plan(self):
        with tempfile.TemporaryDirectory(dir=ROOT / 'build/scratch') as folder:
            path = Path(folder) / 'plan.json'
            path.write_text(json.dumps(self.plan))
            canonical.publish(path, True)

    def test_omission_loads_all_current_modules_before_review(self):
        def review(program, payloads, previous, pin):
            self.assertEqual(set(payloads), {m['key'] for m in self.program['modules']})
            for module in self.program['modules']:
                self.assertEqual(canonical.sha(payloads[module['key']]), module['source_sha256'])
            raise ReachedSemanticReview
        with patch.object(canonical, 'check_semantic_publication', review):
            with self.assertRaises(ReachedSemanticReview):
                self.run_plan()

    def test_omission_cannot_change_compiler_or_storage_contract(self):
        self.plan['program']['modules'][0]['flags'] = ['/invented']
        with self.assertRaisesRegex(ValueError, 'omitted module differs'):
            self.run_plan()

    def test_omission_cannot_add_unreviewed_module(self):
        self.plan['program']['modules'].append(dict(self.program['modules'][0], key='invented'))
        with self.assertRaisesRegex(ValueError, 'omitted module differs'):
            self.run_plan()


if __name__ == '__main__':
    unittest.main()
