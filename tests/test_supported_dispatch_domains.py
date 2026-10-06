"""Composed sound/window domains preserve foreign-state counterexamples."""
from pathlib import Path
import copy, importlib.util, json, struct, unittest
from unittest import mock

ROOT=Path(__file__).resolve().parents[1]
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,ROOT/path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module
SOUND=load('sound_selector_test','evidence/canonical/audio-track-owner/selector_probe.py')
WINDOW=load('window_array_test','evidence/canonical/window-domain/array_gate_probe.py')
CRITICAL=load('critical_selector_test','evidence/canonical/error-continuation/selector_probe.py')

class SupportedDispatchDomains(unittest.TestCase):
    def test_critical_alias_threshold_and_complete_producers(self):
        result=CRITICAL.check()
        self.assertEqual([r['original_instructions_changed_selector'] for r in result['original_song_store_controls']], [False,False,True])
        self.assertEqual(max(result['songs']['track_counts'].values()),10)

    def test_critical_writer_count_and_unrelated_numeric_ingress_are_detected(self):
        helper=CRITICAL.support();texts,program,registry=helper.inventory()
        expected=helper.census(texts,program,registry)
        for text in ['void bad(void){g_8CCB=9;}', 'void bad(void){g_7566=32634;}',
                     'void bad(void){g_8CF2[-10]=0;}']:
            self.assertNotEqual(helper.census({**texts,'src/new.c':text},program,registry),expected)
        self.assertNotEqual(helper.inventory_pins({**texts,'src/new.c':'void bad(void){*(char*)0x8ccb=9;}'},program,registry),helper.inventory_pins(texts,program,registry))

    def test_original_sound_transitions_tables_and_s9_contrast(self):
        result=SOUND.check()
        rows=result['original_controls']['default_setup_original_prefixes']
        self.assertEqual([r['local_and_stored_mode'] for r in rows],[1,6])
        negative=result['original_controls']['s9_negative_control']
        self.assertEqual((negative['index'],negative['target_segment'],negative['target_offset']),(9,0x50f6,0x1f0))

    def test_sound_writer_reentry_and_pointer_escape_require_review(self):
        helper=SOUND.support();texts,program,registry=helper.inventory()
        expected=helper.census(texts,program,registry)
        for text in ['void bad(void){fd_50F6_01F0[0]=9;}',
                     'void bad(void){f_277E_0000(9,0);}',
                     'int *escape=g_68B6;',
                     'void bad(void){g_610A=9;}']:
            with self.subTest(text=text):
                self.assertNotEqual(helper.census({**texts,'src/new.c':text},program,registry),expected)
        changed=copy.deepcopy(registry)
        changed['data']['hidden']=dict(registry['data']['fd_50F6_01F0'])
        self.assertNotEqual(helper.inventory_pins(texts,program,changed),helper.inventory_pins(texts,program,registry))

    def test_foreign_sound_configuration_is_rejected(self):
        db=SOUND.load('sound_config_negative','evidence/canonical/database-domain/replay.py')
        read=Path.read_bytes
        def changed(path):
            raw=read(path)
            return raw.replace(b'Sound Mode: 6',b'Sound Mode: 9') if path==ROOT/'assets/SIMANT.CFG' else raw
        with mock.patch.object(Path,'read_bytes',changed):
            with self.assertRaises(db.Reject):db.verify_resource_domain()

    def test_original_window_store_and_composed_producer_domain(self):
        result=WINDOW.check()
        rows=result['original_hook_stores']
        self.assertEqual([r['within_45'] for r in rows],[True,True,False,False])
        self.assertEqual([r['writes'][0][0] for r in rows],[0,132,180,-4])

    def test_new_window_writers_counts_aliases_and_asm_are_detected(self):
        helper=WINDOW.support();texts,program,registry=helper.inventory()
        expected=helper.census(texts,program,registry)
        for suffix,text in [('c','void bad(void){win_drawHooks[45]=0;}'),
                            ('c','void bad(void){win_offsets[45].left=0;}'),
                            ('c','void bad(void){win_numOfWindows=45;}'),
                            ('c','void *escape=fd_50F6_4892;'),
                            ('asm','MOV WORD PTR _WIN_NUMOFCOLORS,63')]:
            with self.subTest(text=text):
                self.assertNotEqual(helper.census({**texts,'src/new.'+suffix:text},program,registry),expected)
        with self.assertRaisesRegex(ValueError,'preprocessor escape'):
            helper.census({**texts,'src/new.c':'#define hidden win_offsets\n'},program,registry)

    def test_save_cannot_overwrite_protected_dispatch_state(self):
        texts,_,_=SOUND.support().inventory()
        db=SOUND.load('dispatch_save_negative','evidence/canonical/database-domain/replay.py')
        raw=db.oracle_machine('OpenDB').read(SOUND.b.symbol_address('fd_4E4B_0000'),308*8)
        for module in [SOUND,WINDOW,CRITICAL]:
            for name in module.PROTECTED:
                with self.subTest(name=name):
                    at=module.protected_address(name) if module is CRITICAL else SOUND.b.symbol_address(name)
                    changed=bytearray(raw)
                    struct.pack_into('<HHHH',changed,0,1,1,at%16,at//16)
                    with self.assertRaisesRegex(ValueError,'save overlaps'):
                        module.save_ranges(texts,bytes(changed))

    def test_resolved_array_contracts_preserve_independent_gates(self):
        dos=json.loads((ROOT/'src/program.json').read_text())['dos']
        active={g['id'] for g in dos['semantic_gates']}
        resolved={g['id']:g for g in dos['resolved_domain_contracts']}
        for name in ['sound-selector-out-of-range-layout','window-index-resource-cross-owner-layout','critical-selector-computed-alias-layout']:
            self.assertNotIn(name,active)
            self.assertEqual(resolved[name]['domain'],dos['supported_execution_domain']['id'])
        self.assertIn('graphics-computed-copy-layout',active)
        self.assertEqual(resolved['map-viewport-grid-layout']['domain'],dos['supported_execution_domain']['id'])
        platform=json.loads((ROOT/'portable/platform.json').read_text())
        self.assertTrue({'native-window-object-domain','native-window-optional-words'}<={g['id'] for g in platform['preview_limitations']})

if __name__=='__main__':unittest.main()
