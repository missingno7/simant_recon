"""Complete supported Handle footprint and preserved original counterexamples."""
from pathlib import Path
import importlib.util
import json
import unittest

ROOT = Path(__file__).resolve().parents[1]
PROOF = ROOT/'evidence/canonical/window-domain'

def load(name):
    spec = importlib.util.spec_from_file_location('window_handle_'+name, PROOF/(name+'.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def facts(name):
    return json.loads((PROOF/name).read_text())

class WindowHandleDomainTests(unittest.TestCase):
    def test_canonical_owner_and_native_duplicate_retirement(self):
        program = json.loads((ROOT/'src/program.json').read_text())
        owners = [m for m in program['modules'] if m['key']=='source-owned:window-handles']
        self.assertEqual(len(owners), 1)
        self.assertEqual(owners[0]['storage_contract']['communals'],
                         [dict(name='_win_handles',kind='near',length=136)])
        blockers = json.loads((ROOT/'evidence/canonical/blockers.json').read_text())
        self.assertNotIn('_win_handles', [r['name'] for r in blockers['imports']])
        self.assertEqual(blockers['counts']['imports'], len(blockers['imports']))
        storage = json.loads((ROOT/'evidence/canonical/storage.json').read_text())
        shapes = [m['expected_object_shape'] for m in storage['providers']]
        self.assertEqual(storage['counts']['providers'], len(shapes))
        self.assertEqual(storage['counts']['provider_objects'],
                         sum(len(m['communals']) + len(m['publics']) for m in shapes))
        retired = 'portable/whole_program/conversions/pointer_globals.c'
        self.assertFalse((ROOT/retired).exists())
        platform = json.loads((ROOT/'portable/platform.json').read_text())
        self.assertNotIn(retired, platform['services'])
        for path in (ROOT/'portable').rglob('*'):
            if path.suffix in ('.py','.c','.h'):
                self.assertNotIn('SIM_SOURCE_WINDOW_COUNT', path.read_text(), str(path))

    def test_original_initial_state_read_order_save_and_escape_controls(self):
        actual = load('handle_owner_probe').collect()
        self.assertEqual(actual, facts('handle-owner-facts.json'))
        self.assertTrue(actual['initialization'][0]['proposed_table_zero'])
        self.assertFalse(actual['initialization'][1]['proposed_table_zero'])
        self.assertFalse(actual['original_read_controls'][1]['events'][0]['within_proposed_136_bytes'])
        self.assertEqual(actual['save_load']['intersections'], 0)

    def test_complete_caller_guard_and_new_indirect_ingress(self):
        guard = load('handle_ids_guard')
        actual = guard.check()
        self.assertEqual(actual, facts('handle-id-facts.json'))
        self.assertTrue(actual['pass'])
        # New-file ingress cannot hide behind unchanged hashes of existing TUs.
        changed = guard.collect({'src/new-callback.c': 'void (*escape)(void) = f_2505_033C;'})
        self.assertEqual(len(changed['bare_refs']), 8)
        changed = guard.collect({'src/new-macro.c': '#define hidden win_LockWin\n'})
        self.assertTrue(changed['parse_errors'])

    def test_original_event_resource_roots_and_rejected_new_producers(self):
        probe = load('event_ids_probe')
        expected = facts('event-ids.json')
        self.assertEqual(probe.collect(), expected)
        self.assertEqual(expected['domain']['mode_1_to_4_refs'], 1076)
        self.assertEqual(expected['controls']['fabricated_descriptor_selected_code'], 0x2201)
        for suffix, text in [('c','void bad(int x){g_6368=x;}'),
                             ('c','void bad(void){f_22BF_0967(0x3501,0);}'),
                             ('asm','EXTRN _WIN_GETEVENT:FAR')]:
            self.assertNotEqual(probe.census_summary(probe.census({'src/new-event.'+suffix:text})),
                                expected['census'])

    def test_original_local_state_induction_and_foreign_state_contrast(self):
        probe = load('local_ids_probe')
        expected = facts('local-ids.json')
        self.assertEqual(probe.collect(), expected)
        self.assertEqual(expected['history_removals']['count'], 40)
        self.assertEqual(expected['history_evictions']['count'], 10)
        self.assertEqual(expected['yard_modes'][5]['selected'], [0x5241])
        self.assertFalse(expected['yard_modes'][5]['supported'])
        self.assertEqual(expected['SaveRec']['overlap']['YardMode'][0]['stream_offset'], 48342)
        for path,text in [('src/new-state.c','void bad(void){YardMode=5;}'),
                          ('src/new-state.asm','MOV WORD PTR _YARDMODE,5')]:
            self.assertNotEqual(probe.coverage(source_overrides={path:text}), expected['coverage'])

if __name__=='__main__': unittest.main()
