"""Keep the object-index gate distinct from independent storage ownership."""
from pathlib import Path
import hashlib
import importlib.util
import json
import sys
import unittest

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
PROOF = ROOT / 'evidence/canonical/window-domain'


class WindowDriveDomain(unittest.TestCase):
    def test_reviewed_sources_resources_and_window_count(self):
        facts = json.loads((PROOF / 'facts.json').read_text())
        self.assertEqual(facts['status'], 'OPEN_COUNTEREXAMPLE')
        self.assertFalse(facts['provider_proposed'])
        for field in ('source_sha256', 'asset_sha256'):
            for path, digest in facts[field].items():
                self.assertEqual(hashlib.sha256((ROOT / path).read_bytes()).hexdigest(), digest, path)
        sys.path.insert(0, str(ROOT / 'tools'))
        import resource_domains as r
        raw = next(x['payload'] for x in r.decoder().parse_records('HCEGANT')[1]
                   if (x['id'], x['kind']) == (22, 0))
        self.assertEqual(hashlib.sha256(raw).hexdigest(), facts['window']['payload_sha256'])
        self.assertEqual(len(r.window_domain(raw)['objects']), 21)

    def test_original_successful_drive_prefix_and_object_lookup(self):
        spec = importlib.util.spec_from_file_location('window_drive_probe', PROOF / 'drive_selection_probe.py')
        probe = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(probe)
        positive, contrast = probe.controls()
        facts = json.loads((PROOF / 'facts.json').read_text())
        self.assertEqual(probe.exe.load().sha256, facts['oracle_sha256'])
        self.assertEqual([positive, contrast], facts['results'])
        self.assertEqual(positive['successful_directory_calls'], [3])
        self.assertEqual(positive['selected_argument'], 0x160d)
        self.assertTrue(positive['consumer']['pointer_is_shipped_object'])
        self.assertEqual(positive['consumer']['diagnostics'], [])
        self.assertEqual(contrast['successful_directory_calls'], [11])
        self.assertEqual(contrast['selected_argument'], 0x1615)
        self.assertEqual(contrast['object'], contrast['consumer']['count'])
        self.assertFalse(contrast['consumer']['pointer_is_shipped_object'])
        self.assertEqual(contrast['consumer']['diagnostics'], ['Attempt to get obj address outsize window'])
        # This object-index spill retains window high byte16. It supplies no
        # FE event producer and does not invalidate the five-title menu proof.
        self.assertEqual(contrast['selected_argument'] & 0xff00, 0x1600)

    def test_actual_first_fatal_shutdown_and_reentrant_contrast(self):
        spec = importlib.util.spec_from_file_location('window_fatal_probe', PROOF / 'drive_selection_probe.py')
        probe = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(probe)
        actual = probe.fatal_controls()
        facts = json.loads((PROOF / 'facts.json').read_text())
        self.assertEqual(actual, facts['fatal_results'])
        self.assertTrue(actual[0]['reaches_CRT_exit'])
        self.assertEqual(actual[0]['exit_code'], 0)
        self.assertFalse(actual[1]['reaches_CRT_exit'])
        self.assertFalse(facts['ownership_question']['drive_counterexample_prevents_independent_owner'])

    def test_storage_consumers_and_resource_reference_roots(self):
        facts = json.loads((PROOF / 'facts.json').read_text())
        for name, field in (('win_handles', 'handle_consumers'), ('win_colors', 'color_consumers')):
            consumers = sorted(path.relative_to(ROOT).as_posix()
                for path in (ROOT / 'src').rglob('*')
                if path.suffix in ('.c', '.asm') and (ROOT / 'src/state') not in path.parents
                and name in path.read_text())
            self.assertEqual(consumers, facts['ownership_question'][field])
        sys.path.insert(0, str(ROOT / 'tools'))
        import resource_domains as r
        records = [x for x in r.decoder().parse_records('HCEGANT')[1]
            if x['kind'] == 0 and 0 <= x['id'] < 128]
        self.assertEqual(sorted(x['id'] for x in records), list(range(34)))
        links = []
        import struct
        for record in records:
            raw = record['payload']
            self.assertFalse(struct.unpack_from('<H', raw, 28)[0] & 0x200)
            for obj in r.window_domain(raw)['objects']:
                for mode, reference in zip(obj['modes'], obj['refs']):
                    if mode in (1, 2, 3, 4):
                        self.assertIn(reference >> 8, range(34))
                if obj['type'] in (7, 8):
                    links.append((record['id'], obj['index'], struct.unpack_from('<h', raw, obj['offset'] + 40)[0]))
        self.assertEqual(links, [(22, 8, 0x1609)])


if __name__ == '__main__':
    unittest.main()
