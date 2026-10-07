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
    def three_way_dump_control(self,original,canonical,native,original_repeat=None,canonical_repeat=None,
                               raw_state=False,name='state',native_save=None,raw_save=None):
        from portable.tests.acceptance.native_acceptance import three_way_checkpoint
        with tempfile.TemporaryDirectory() as scratch:
            out=Path(scratch)
            # Different image bases AND symbol offsets defeat accidental reuse of
            # canonical addresses when reading the original executable.
            oa={'g_5A9C':dict(dos_address=8),name:dict(dos_address=32)}
            ca={'g_5A9C':12,name:64};specs={name:dict(dos_address=64)}
            def dump(filename,data,base,clip_at,state_at):
                memory=bytearray(256);memory[base+clip_at:base+clip_at+16]=acceptance.SCREEN_CLIP_PATTERN
                memory[base+state_at:base+state_at+len(data)]=data
                path=out/filename;path.write_bytes(memory);return path
            op=dump('original.bin',original,4,8,32)
            cp=dump('canonical.bin',canonical,20,12,64)
            np=out/'native.json';np.write_text(json.dumps(dict(symbols={name:dict(
                status='OK',bytes=len(native),data=native.hex())})))
            if native_save is not None: np.with_suffix('.sav').write_bytes(native_save)
            if raw_save is not None: np.with_suffix('.raw-save.sav').write_bytes(raw_save)
            orepeat=[dump('original-repeat.bin',original_repeat,10,8,32)] if original_repeat is not None else []
            crepeat=[dump('canonical-repeat.bin',canonical_repeat,24,12,64)] if canonical_repeat is not None else []
            return three_way_checkpoint(np,op,cp,ca,specs,raw_state,oa,orepeat,crepeat)

    def test_three_way_original_equal_all(self):
        row=self.three_way_dump_control(b'abc',b'abc',b'abc')
        self.assertEqual(row['symbols']['state']['verdict'],'ORIGINAL_EQUAL_ALL')
        self.assertEqual(row['verdict_counts']['ORIGINAL_EQUAL_ALL'],1)

    def test_three_way_port_introduced(self):
        row=self.three_way_dump_control(b'abc',b'abc',b'aZc')
        detail=row['symbols']['state']
        self.assertEqual(detail['verdict'],'PORT_INTRODUCED')
        self.assertEqual(detail['original_vs_canonical']['status'],'EQUAL')
        self.assertEqual(detail['original_vs_native']['first_offset'],1)

    def test_three_way_save_projection_does_not_hide_raw_serialization_difference(self):
        with patch.object(acceptance,'save_schema',return_value=[(0,0,3,1,'state')]):
            row=self.three_way_dump_control(b'abc',b'abc',b'abc',native_save=b'abc',raw_save=b'aZc')
        self.assertEqual(row['save']['records']['0']['verdict'],'ORIGINAL_EQUAL_ALL')
        self.assertEqual(row['raw_save']['records']['0']['verdict'],'PORT_INTRODUCED')
        self.assertEqual(row['raw_save']['original_vs_canonical']['status'],'EQUAL')

    def test_three_way_reconstruction_introduced(self):
        for native in [b'aZc',b'abc',b'aQc']:
            row=self.three_way_dump_control(b'abc',b'aZc',native)
            self.assertEqual(row['symbols']['state']['verdict'],'RECONSTRUCTION_INTRODUCED')
            self.assertEqual(row['symbols']['state']['nondeterministic_runs'],[])

    def test_three_way_dos_nondeterministic_requires_same_exe_repeat(self):
        row=self.three_way_dump_control(b'abc',b'abc',b'aZc',original_repeat=b'aQc')
        self.assertEqual(row['symbols']['state']['verdict'],'ORIGINAL_DOS_NONDETERMINISTIC')
        self.assertEqual(row['symbols']['state']['nondeterministic_runs'],['original'])
        row=self.three_way_dump_control(b'abc',b'abc',b'aZc',canonical_repeat=b'aQc')
        self.assertEqual(row['symbols']['state']['nondeterministic_runs'],['canonical_dos'])
        row=self.three_way_dump_control(b'abc',b'abc',b'abc',original_repeat=b'abc')
        self.assertEqual(row['symbols']['state']['verdict'],'ORIGINAL_EQUAL_ALL')

    def test_three_way_stack_policy_requires_shared_scope(self):
        a=b'\x00\x01\x00\x80'+bytes(60)
        b=a[:4]+bytes([17])*60
        row=self.three_way_dump_control(a,b,a,name='g_5702')
        self.assertEqual(row['symbols']['g_5702']['verdict'],'ORIGINAL_EQUAL_ALL')
        self.assertEqual(row['partial_exclusions']['g_5702']['raw_verdict']['verdict'],'RECONSTRUCTION_INTRODUCED')
        row=self.three_way_dump_control(a,b,a,name='g_5702',raw_state=True)
        self.assertEqual(row['symbols']['g_5702']['verdict'],'RECONSTRUCTION_INTRODUCED')
        moved=b'\x00\x01\x00\x02\x00\x80'+bytes(58)
        row=self.three_way_dump_control(a,a,moved,name='g_5702')
        self.assertFalse(row['partial_exclusions'])
        self.assertEqual(row['symbols']['g_5702']['verdict'],'PORT_INTRODUCED')

    def test_paired_acceptance_directory_and_original_identity(self):
        from portable.tests.acceptance.native_acceptance import dos_directories
        with tempfile.TemporaryDirectory() as scratch:
            parent=Path(scratch);original=parent/'original';canonical=parent/'reconstructed'
            original.mkdir();canonical.mkdir()
            self.assertEqual(dos_directories(parent),(canonical,original))
            self.assertEqual(dos_directories(canonical),(canonical,original))
            (original/'execution-report.json').write_text(json.dumps(dict(
                inputs=[dict(path='assets/SIMANT.EXE',sha256='original-control')])) )
            (original/'INPUT.SCR').write_text('100 key enter\n200 exit\n')
            oracle_provenance(original,'original-control',executable_name='SIMANT.EXE')
            with self.assertRaisesRegex(ValueError,'executable identity differs'):
                oracle_provenance(original,'canonical-control',executable_name='SIMANT.EXE')

    def test_original_map_missing_never_falls_back_to_canonical(self):
        from portable.tests.acceptance.native_acceptance import three_way_checkpoint
        with tempfile.TemporaryDirectory() as scratch:
            out=Path(scratch);native=out/'native.json'
            native.write_text(json.dumps(dict(symbols={'unknown':dict(status='OK',bytes=1,data='00')})))
            memory=acceptance.SCREEN_CLIP_PATTERN+bytes(16)
            original=out/'original.bin';original.write_bytes(memory)
            canonical=out/'canonical.bin';canonical.write_bytes(memory)
            result=three_way_checkpoint(native,original,canonical,{'g_5A9C':0},
                {'unknown':dict(dos_address=20)},original_specs={'g_5A9C':dict(dos_address=0)})
            self.assertFalse(result['symbols'])
            self.assertEqual(result['unavailable']['unknown']['status'],'ORIGINAL_MAP_MISSING')
            original.unlink()
            result=three_way_checkpoint(native,original,canonical,{}, {})
            self.assertEqual(result['status'],'MISSING')
            self.assertEqual(result['present'],[True,False,True])

    def test_original_canonical_difference_fails_even_when_native_matches_canonical(self):
        from portable.tests.acceptance.native_acceptance import compare
        with tempfile.TemporaryDirectory() as scratch:
            out=Path(scratch);(out/'checkpoints').mkdir()
            (out/'checkpoints/exit.json').write_text(json.dumps(dict(exit_code=0)))
            row=dict(status='EQUAL_SUBSET',symbols={'state':dict(status='EQUAL')})
            three_way=dict(status='COMPARED_DIAGNOSTIC',symbols={'state':dict(verdict='RECONSTRUCTION_INTRODUCED')})
            module=compare.__module__
            with patch.object(acceptance,'record_addresses',return_value={}), \
                 patch(module+'.oracle_provenance',return_value=dict(saved_game_sha256=None)), \
                 patch(module+'.compare_checkpoint',return_value=(row,{},{})), \
                 patch(module+'.three_way_checkpoint',return_value=three_way):
                result=compare(dict(id='control',script='dos/scenarios/new-game-save.scr',saves=[]),
                    out,out/'reconstructed',out/'SOURCE.MAP',{},[123],exe_sha='control',original_dos=out/'original')
            self.assertEqual(result['status'],'FAIL')
            self.assertEqual(result['first_diverging_checkpoint'],123)
            self.assertEqual(result['checkpoints']['123']['symbols']['state']['verdict'],'RECONSTRUCTION_INTRODUCED')

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
            report=out/'build-report.json'
            report.write_text(json.dumps(dict(link=dict(candidate_executable=dict(path='SOURCE.EXE')))))
            for build_report in (None,report):
                with patch.object(acceptance,'scripted_input',return_value=out/'control.scr'), \
                     patch.object(acceptance.subprocess,'run'), \
                     patch.object(acceptance,'record_addresses',return_value={}), \
                     patch.object(acceptance,'virtual_save',return_value=b'save control'):
                    result=acceptance.run_once(scenario,out,build_report)
                self.assertEqual(dump.read_bytes(),b'observation control')
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
