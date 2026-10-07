"""Negative controls for named-state exclusions and canonical DOS placement."""
import json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
if __package__:
    from .native_acceptance import differences,save_differences,ROOT,acceptance,oracle_provenance,compare_steps,sha
    from .canonical_dos_layout import canonical_layout
    from .state_policy import state_prefix
    from .save_projection import project_save
else:
    from native_acceptance import differences,save_differences,ROOT,acceptance,oracle_provenance,compare_steps,sha
    from canonical_dos_layout import canonical_layout
    from state_policy import state_prefix
    from save_projection import project_save

class Controls(unittest.TestCase):
    def test_step_alignment_requires_phase_and_input_prefix(self):
        with tempfile.TemporaryDirectory() as scratch:
            out=Path(scratch);(out/'checkpoints').mkdir()
            dump=out/'exec-simstep.1.bin';dump.write_bytes(b'\x01\x00\x01\x00\x00\x00')
            dump.with_suffix('.json').write_text(json.dumps(dict(hit=1,dump_address='0x00000000',emulated_ms=50)))
            (out/'replay.txt').write_text('0 down Return\n100 down Space\n200 exit\n')
            run=dict(script_sha256='script',scenario_sha256='scenario')
            (out/'boundary-manifest.json').write_text(json.dumps(dict(boundary='DoAntSim:entry',steps=1,
                executable_sha256='exe',input_script_sha256='script',scenario_sha256='scenario',snapshots={dump.name:sha(dump)})))
            snapshot=dict(replay_next=1,milliseconds=80,clocks=dict(cycle=1,simulation_calls=1))
            path=out/'checkpoints/step1.json'
            specs={'Cycle':dict(dos_address=0),'fd_50F6_0C26':dict(dos_address=2)}
            module=compare_steps.__module__
            with patch(module+'.compare_checkpoint',return_value=(dict(status='EQUAL_SUBSET'),{},{})), \
                 patch(module+'.memory_base',return_value=0):
                path.write_text(json.dumps(snapshot))
                self.assertEqual(compare_steps(out,out,{},specs,False,run,'exe')['status'],'INCOMPLETE_EQUAL_SUBSET')
                snapshot['replay_next']=2;path.write_text(json.dumps(snapshot))
                self.assertEqual(compare_steps(out,out,{},specs,False,run,'exe')['first_alignment_failed_step'],1)
                snapshot['replay_next']=1;snapshot['clocks']['simulation_calls']=2;path.write_text(json.dumps(snapshot))
                self.assertEqual(compare_steps(out,out,{},specs,False,run,'exe')['first_alignment_failed_step'],1)
                with patch(module+'.compare_checkpoint',return_value=(dict(status='MISSING',present=[True,False]),{},{})):
                    result=compare_steps(out,out,{},specs,False,run,'exe')
                    self.assertEqual(result['first_missing_step'],1)
                    self.assertEqual(result['checkpoints']['1']['dos_boundary']['milliseconds'],50)
    def test_oracle_identity_and_input_history_required(self):
        with tempfile.TemporaryDirectory() as scratch:
            out=Path(scratch);original=out/'original.scr'
            original.write_text('100 key enter\n200 exit\n')
            (out/'INPUT.SCR').write_text('0 dump 0 A0000 cp0\n100 key enter\n200 exit\n')
            report=out/'execution-report.json'
            report.write_text(json.dumps(dict(inputs=[dict(path='SOURCE.EXE',sha256='control')])))
            self.assertTrue(oracle_provenance(out,'control',original)['original_input_operations_verified'])
            with self.assertRaisesRegex(ValueError,'executable identity differs'):
                oracle_provenance(out,'wrong',original)
            (out/'INPUT.SCR').write_text('101 key enter\n200 exit\n')
            with self.assertRaisesRegex(ValueError,'input operations differ'):
                oracle_provenance(out,'control',original)
    def test_byte_delta_and_extent(self):
        self.assertEqual(differences(b'abc',b'abc')['status'],'EQUAL')
        delta=differences(b'abc',b'aZc')
        self.assertEqual((delta['first_offset'],delta['differing_bytes'],delta['max_byte_delta']),(1,1,8))
        self.assertEqual(differences(b'a',b'ab')['status'],'SIZE_MISMATCH')
    def test_canonical_save_record_localization(self):
        from dos.acceptance import save_schema
        schema=save_schema();size=sum(row[2] for row in schema)
        self.assertEqual((len(schema),size),(307,48386))
        original=bytes(size);native=bytearray(original)
        native[schema[113][1]]=30
        delta=save_differences(original,bytes(native))
        self.assertEqual(len(delta['differences']),1)
        row=delta['differences'][0]
        self.assertEqual((row['record'],row['name'],row['native_unsigned']),(113,'fd_50F6_0FFE',30))
    def test_canonical_map_anchors_positive(self):
        result,errors=canonical_layout(ROOT,ROOT/'build/current/dos/build-report.json')
        self.assertFalse(errors)
        self.assertIn('root:0093::seed',result)
        self.assertEqual(result['root:1B73::tick_count']['bytes'],4)
    def test_reordered_link_contributions_rejected(self):
        real_read=Path.read_text
        def changed(path,*args,**kwargs):
            text=real_read(path,*args,**kwargs)
            if path.name=='SOURCE.LNK':
                text=text.replace('U041','ORDER_TEMP').replace('U042','U041').replace('ORDER_TEMP','U042')
            return text
        with patch.object(Path,'read_text',changed):
            with self.assertRaisesRegex(ValueError,'MAP contradicts canonical contribution order'):
                canonical_layout(ROOT,ROOT/'build/current/dos/build-report.json')

    def test_named_stack_tail_and_raw_control(self):
        a=b'\x00\x01\x00\x80'+bytes(60)
        b=a[:4]+bytes([17])*60
        left,right,policy=state_prefix('g_5702',a,b)
        self.assertEqual(left,right)
        self.assertEqual(policy['excluded_range'],[4,64])
        self.assertEqual(policy['excluded_differing_offsets'],list(range(4,64)))
        self.assertEqual(state_prefix('g_5702',a,b,True),(a,b,None))
        self.assertEqual(state_prefix('another_symbol',a,b),(a,b,None))

    def test_live_prefix_and_sentinel_differences_remain_failures(self):
        a=b'\x00\x01\x00\x80'+bytes(60)
        b=b'\x00\x02'+a[2:]
        left,right,policy=state_prefix('g_5702',a,b)
        self.assertEqual(differences(left,right)['status'],'DIFFERS')
        b=b'\x00\x01\x00\x02\x00\x80'+bytes(58)
        left,right,policy=state_prefix('g_5702',a,b)
        self.assertFalse(policy['applied'])
        self.assertEqual((left,right),(a,b))
        _,_,policy=state_prefix('g_5702',bytes(64),a)
        self.assertFalse(policy['applied'])

    def test_dos_acceptance_retains_raw_checkpoint(self):
        with tempfile.TemporaryDirectory() as scratch:
            out=Path(scratch)
            (out/'execution-report.json').write_text('{}')
            dump=out/'dump-cp123';dump.write_bytes(b'observation control')
            scenario=dict(id='control',host_seconds=1,checkpoints=[123],saves=[])
            with patch.object(acceptance,'scripted_input',return_value=out/'control.scr'), \
                 patch.object(acceptance.subprocess,'run'), \
                 patch.object(acceptance,'record_addresses',return_value={}), \
                 patch.object(acceptance,'virtual_save',return_value=b'save control'):
                result=acceptance.run_once(scenario,out,None)
            self.assertEqual(dump.read_bytes(),b'observation control')
            self.assertEqual(result['checkpoints']['cp123'],b'save control')

    def test_save_projection_joins_real_owners_and_cuts_last_owner(self):
        specs={n:dict(dos_address=a) for n,a in [('A',100),('B',102),('C',106)]}
        symbols={n:dict(status='OK',data=d.hex()) for n,d in [('A',b'ab'),('B',b'cdef'),('C',b'ghij')]}
        data,records,errors=project_save([(0,0,8,2,'A')],specs,symbols)
        self.assertEqual(data,b'abcdefgh')
        self.assertFalse(errors)
        self.assertEqual([s['owners'] for s in records[0]['segments']],[['A'],['B'],['C']])
        # No guessed link padding and no conflicting-alias selection.
        specs['B']['dos_address']=103
        data,_,errors=project_save([(0,0,8,2,'A')],specs,symbols)
        self.assertIsNone(data);self.assertEqual(errors[0]['status'],'UNOBSERVED_SAVE_OWNER')
        specs['B']['dos_address']=101
        data,_,errors=project_save([(0,0,8,2,'A')],specs,symbols)
        self.assertIsNone(data);self.assertEqual(errors[0]['status'],'CONFLICTING_NATIVE_OWNER_VIEWS')
    def test_identity_mismatch_rejected(self):
        real_read=Path.read_text
        def changed(path,*args,**kwargs):
            text=real_read(path,*args,**kwargs)
            if path.name=='build-report.json':
                data=json.loads(text);data['link']['candidate_executable']['sha256']='0'*64;text=json.dumps(data)
            return text
        with patch.object(Path,'read_text',changed):
            with self.assertRaisesRegex(ValueError,'executable report identity changed'):
                canonical_layout(ROOT,ROOT/'build/current/dos/build-report.json')

if __name__=='__main__': unittest.main()
