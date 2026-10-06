"""The successful default resource DB domain is a source invariant, not a trace."""
import hashlib
import importlib.util
import json
from pathlib import Path
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('database_domain_replay',
    ROOT / 'evidence/canonical/database-domain/replay.py')
REPLAY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(REPLAY)

class DatabaseDomain(unittest.TestCase):
    def test_source_invariant_and_original_negative_controls(self):
        receipt = REPLAY.probe()
        self.assertEqual(receipt['classification'], 'SUPPORTED_DOMAIN')
        self.assertEqual(receipt['invariant']['record_and_frontend_slots'], [0, 1, 2])
        self.assertEqual(receipt['save_load_destinations']['descriptors'], 307)
        self.assertEqual(receipt['save_load_destinations']['protected_ranges_intersected'], 0)
        self.assertEqual(receipt['first_use_flag_contract']['initializer'], 0)
        self.assertEqual([c['returned_slot'] for c in receipt['original_first_use_clear']['cases']], [0, -1])
        self.assertEqual(receipt['original_lookup_iteration']['original_db_LoadObject_recall_handles'], [0, 1, 2])
        fifth = receipt['original_frontend']['fifth_returning_failure_negative']
        self.assertEqual(fifth['store_address'], '50F6:3B58')
        self.assertFalse(fifth['within_four_slot_owner'])
        self.assertTrue(all(c['observed'] == 'rejected' for c in receipt['negative_controls']))

    def test_promoted_branch_change_still_requires_domain_review(self):
        """Changing both source and inventory hash cannot silently widen scope."""
        path = ROOT / 'src/S20/m39F1.c'
        read = Path.read_bytes
        mutated = read(path).replace(b'if ((i = open("language.dat", 0)) > 0) {', b'if (1) {')
        self.assertNotEqual(mutated, read(path))
        inventory_path = ROOT / 'src/program.json'
        inventory = json.loads(read(inventory_path))
        for item in inventory['modules']:
            if item['source'] == 'src/S20/m39F1.c':
                item['source_sha256'] = hashlib.sha256(mutated).hexdigest()
        registry = json.dumps(inventory).encode()
        def changed(candidate):
            return mutated if candidate == path else registry if candidate == inventory_path else read(candidate)
        with mock.patch.object(Path, 'read_bytes', changed):
            with self.assertRaisesRegex(REPLAY.Reject, 'reviewed source pin differs'):
                REPLAY.probe()

if __name__ == '__main__':
    unittest.main()
