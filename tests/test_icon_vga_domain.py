"""Default VGA icon exclusion, with state-ingress and non-VGA controls."""
from pathlib import Path
import copy
import importlib.util
import json
import struct
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('icon_vga',
    ROOT/'evidence/canonical/icon-handle-view/vga_probe.py')
PROBE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PROBE)

class IconVgaDomain(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.texts, cls.program, cls.registry = PROBE.inventory()
        cls.expected = json.loads((ROOT/'evidence/canonical/icon-handle-view/vga-facts.json').read_text())

    def test_original_pointer_load_exclusion_and_other_mode_contrast(self):
        self.assertEqual(PROBE.check(), self.expected)
        rows = self.expected['original_controls']
        self.assertEqual(len(rows), 24)
        for row in rows:
            self.assertEqual(row['slot_reads'], [] if row['mode']==8 else [[0,2],[2,2]])

    def test_new_writer_escape_caller_and_assembly_are_detected(self):
        for suffix, text in [
            ('c','void bad(void){g_5A97=2;}'),
            ('c','char *escape(void){return &g_5A97;}'),
            ('c','void again(void){ReadConfig();}'),
            ('asm','MOV BYTE PTR _G_5A97,2'),
            ('asm','MOV WORD PTR _G_6298,1')]:
            with self.subTest(text=text):
                changed={**self.texts, 'src/new-ingress.'+suffix:text}
                self.assertNotEqual(PROBE.census(changed,self.program,self.registry),self.expected['census'])
        with self.assertRaisesRegex(ValueError,'preprocessor escape'):
            PROBE.census({**self.texts,'src/new-macro.c':'#define MODE g_5A97\n'},self.program,self.registry)

    def test_alias_chains_interior_and_other_base_are_detected(self):
        mode=self.registry['data']['g_5A97']
        for target,offset in [('g_5A97',0),('fd_50F6_46D2',2),('other_base',1)]:
            with self.subTest(target=target):
                program=copy.deepcopy(self.program)
                registry=copy.deepcopy(self.registry)
                registry['data']['other_base']={**mode,'off':mode['off']-1}
                program['aliases'].extend([
                    dict(alias='_hidden',target='_'+target,offset=offset),
                    dict(alias='_indirect',target='_hidden',offset=0)])
                actual=PROBE.census(self.texts,program,registry)
                self.assertIn('indirect',actual['aliases'])
                self.assertNotEqual(actual,self.expected['census'])

    def test_startup_branch_change_requires_fresh_review(self):
        path='src/root/m205F.c'
        changed={**self.texts,path:self.texts[path].replace('if (g_6298) {','if (!g_6298) {',1)}
        self.assertNotEqual(changed[path],self.texts[path])
        self.assertNotEqual(PROBE.census(changed,self.program,self.registry),self.expected['census'])

    def test_unsymbolized_ingress_and_updated_inventory_require_review(self):
        # Deliberately invalid source fixture: no protected identifier appears.
        path='src/new-hidden.c'
        text='void bad(void){*(char far *)0x55B35A97UL=2;}'
        texts={**self.texts,path:text}
        program=copy.deepcopy(self.program)
        program['modules'].append(dict(key='fixture',source=path,source_sha256=PROBE.sha(text.encode())))
        self.assertEqual(PROBE.census(texts,program,self.registry),self.expected['census'])
        self.assertNotEqual(PROBE.inventory_pins(texts,program,self.registry),self.expected['inventory'])
        registry=copy.deepcopy(self.registry)
        registry['data']['hidden_state']={'seg':0x55b3,'off':0x5a97}
        self.assertNotEqual(PROBE.inventory_pins(self.texts,self.program,registry),self.expected['inventory'])

    def test_save_record_cannot_restore_mode_compatibility_or_icon_slot(self):
        db=PROBE.load('icon_test_db','evidence/canonical/database-domain/replay.py')
        m=db.oracle_machine('OpenDB')
        raw=m.read(PROBE.b.symbol_address('fd_4E4B_0000'),308*8)
        for name in ['g_5A97','g_6298','fd_50F6_46D2']:
            with self.subTest(name=name):
                symbol=PROBE.b.symbol(name)
                changed=bytearray(raw)
                struct.pack_into('<HHHH',changed,0,1,1,symbol['off'],symbol['seg'])
                with self.assertRaisesRegex(ValueError,'save reaches protected state'):
                    PROBE.saves(self.texts,bytes(changed))

    def test_foreign_config_is_rejected(self):
        db=PROBE.load('icon_test_config','evidence/canonical/database-domain/replay.py')
        read=Path.read_bytes
        def changed(path):
            raw=read(path)
            return raw.replace(b'Display Mode: V',b'Display Mode: T') if path==ROOT/'assets/SIMANT.CFG' else raw
        with mock.patch.object(Path,'read_bytes',changed):
            with self.assertRaises(db.Reject):db.verify_resource_domain()

    def test_domain_resolution_keeps_canonical_slot_and_other_gates(self):
        ids={'icon-handle-computed-alias-and-activation','icon-handle-cell-and-payload-lifetime'}
        dos=self.program['dos']
        self.assertFalse(ids & {g['id'] for g in dos['semantic_gates']})
        resolved={g['id']:g for g in dos['resolved_domain_contracts']}
        for name in ids:
            self.assertEqual(resolved[name]['domain'],dos['supported_execution_domain']['id'])
            self.assertEqual(resolved[name]['status'],'RESOLVED_SUPPORTED_DOMAIN')
        self.assertIn('graphics-computed-copy-layout',{g['id'] for g in dos['semantic_gates']})
        self.assertTrue(any(m['source']=='src/state/icon-handle-cell-view.c' for m in self.program['modules']))
        platform=json.loads((ROOT/'portable/platform.json').read_text())
        self.assertNotIn('native-icon-lifetime',{g['id'] for g in platform['preview_limitations']})

if __name__=='__main__':unittest.main()
