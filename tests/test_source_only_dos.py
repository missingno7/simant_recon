"""The standalone lane must expose debt and never import the hybrid oracle."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import csrc
import compiler
import dos_source_bindings as bindings
from omf import OmfReader
import source_only_dos as dos
import dos_alignment_debt as alignment


class SourceOnlyDosTests(unittest.TestCase):
    def test_partial_link_images_do_not_override_structural_diagnostics(self):
        # RTLink writes an MZ file after these actual diagnostic classes.
        # Neither the file nor exit status proves an independent link succeeded.
        for log in (
            "warning wrt0082: Illegal fixup: Target MOUSE_TEXT, Relative to DGROUP",
            "wrt0011: Public symbol '__ffree' doubly defined",
            "Warning: unresolved public _missing_owner",
            "Fatal: cannot open input object",
        ):
            with self.subTest(log=log):
                self.assertTrue(dos.independent_link_diagnostics(log))
        self.assertFalse(dos.independent_link_diagnostics(
            'RTLink/Plus 6.10\nProcessing SOURCE.LNK\nFile: U087.OBJ\nCreating SOURCE.EXE\n'))

    def test_v25_whole_storage_controls_reject_semantic_and_metadata_drift(self):
        import copy
        import hashlib
        worker = ROOT/'build/workers/source_only_dos_tests'
        worker.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=worker) as directory:
            report = {'inputs': [], 'generated_files': [], 'translation_units': [], 'semantic_substitutions': []}
            dos.prepare(Path(directory), report)
            report['runtime_components'] = []
            tools = compiler.toolchain()['linkers']
            for profile in ('rtlink400', 'rtlink610'):
                bindings.require_v25_storage_contracts(report, profile, tools[profile])
            for module, (key, _) in bindings.V25_STORAGE_CONTRACTS.items():
                for change in ('review', 'missing-case', 'raw-with-consistent-hash', 'map',
                               'extra-owner', 'width', 'initializer', 'warning', 'scope', 'tools'):
                    wrong = copy.deepcopy(report); c = wrong[key]; row = c['cases'][0]
                    natural = next(o for o in c['compiler_controls'].values() if o['communals'])
                    if change == 'review': c['root_reviewed'] = False
                    elif change == 'missing-case': c['cases'].pop()
                    elif change == 'raw-with-consistent-hash':
                        raw = bytes.fromhex(row['raw']['hex']) + b'EXTRA\r\n'
                        digest = hashlib.sha256(raw).hexdigest()
                        row['raw'].update(hex=raw.hex(), sha256=digest, size=len(raw))
                        row['raw']['artifact_pin'].update(sha256=digest, size=len(raw))
                    elif change == 'map': row['public_address_matrix']['Value'].pop(next(iter(row['public_address_matrix']['Value'])))
                    elif change == 'extra-owner': natural['communals'].append(dict(natural['communals'][0], name='_unproved_object'))
                    elif change == 'width': natural['communals'][0]['element_size'] += 1
                    elif change == 'initializer': natural['initialized_data_hex']['invented_DATA'] = '01'
                    elif change == 'warning': row['linker_diagnostics'] = ['warning wrt0052']
                    elif change == 'scope': c['game_lifecycle_claimed'] = True
                    elif change == 'tools': c['inputs'] = []
                    with self.subTest(module=module, change=change):
                        with self.assertRaises(ValueError):
                            bindings.require_v25_storage_contracts(wrong, 'rtlink400', tools['rtlink400'])
                if report[key]['save_rec_pointer_fixups']:
                    wrong = copy.deepcopy(report)
                    wrong[key]['save_rec_pointer_fixups'][0]['encoded_addend'] = '01000000'
                    with self.assertRaises(ValueError): bindings.require_v25_storage_contracts(wrong, 'rtlink400', tools['rtlink400'])
            geo = report['ui_geometry_state_contract']
            self.assertIn(b'ZERO32=', bytes.fromhex(geo['cases'][0]['raw']['hex']))
            self.assertIn(b'POST32=', bytes.fromhex(geo['cases'][0]['raw']['hex']))
            # The isolated world backing contrast deliberately links only the
            # one tested owner. Every complete-provider case still needs 17.
            world = report['remaining_world_state_contract']
            self.assertEqual(len(next(r for r in world['cases'] if r['case']=='plus2_independent_saverec_backing')['expected_owner_publics']), 1)
            self.assertEqual(len(next(r for r in world['cases'] if r['case']=='typed_raw_startup_saverec_pointer32')['expected_owner_publics']), 17)

    def test_v24_pointer_and_yard_owners_require_complete_storage_controls(self):
        worker = ROOT/'build/workers/source_only_dos_tests'
        worker.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=worker) as directory:
            report = {'inputs': [], 'generated_files': [], 'translation_units': [], 'semantic_substitutions': []}
            _, symbols = dos.prepare(Path(directory), report)
            tools = compiler.toolchain()['linkers']
            report['runtime_components'] = []
            for module, (key, _) in bindings.V24_STORAGE_CONTRACTS.items():
                row = next(r for r in report['translation_units'] if r['module'] == module)
                provider = row['storage_provider']
                source = (ROOT/row['source']['path']).read_text(encoding='ascii')
                def compile(text):
                    result = compiler.compile_c(text,row['profile'],row['flags'],basename=row['basename'])
                    self.assertTrue(result.ok,result.log)
                    return OmfReader(communals=True).read(result.obj)
                bindings.review_provider_source(source,provider,symbols)
                self.assertEqual(bindings.verify_provider(compile(source),provider)['communals'],
                                 bindings.provider_communals(module))
                if module.endswith('string-pointers'):
                    bad = source.replace('far * far *StrList','far * near *StrList')
                    same_shape = source.replace('typedef char far','typedef void far')
                elif module.endswith('yard-init-state'):
                    bad = source.replace('long far fd_50F6_0220','int far fd_50F6_0220')
                    same_shape = source.replace('long far fd_50F6_0220','unsigned long far fd_50F6_0220')
                else:
                    bad = source.replace('0334[12]','0334[11]')
                    same_shape = source.replace('int far fd_50F6_0334','unsigned int far fd_50F6_0334')
                with self.assertRaises(ValueError): bindings.verify_provider(compile(bad),provider)
                self.assertEqual(bindings.verify_provider(compile(same_shape),provider)['status'],'PASS')
                with self.assertRaises(ValueError): bindings.review_provider_source(same_shape,provider,symbols)
                for change in ('root','case','duplicate','raw','hash','pin','warning','timeout',
                               'public','heading','map-count','common','extra-storage','initializer','scope','tools'):
                    wrong = json.loads(json.dumps(report)); c=wrong[key]; case=c['cases'][0]
                    control=next(iter(c['compiler_controls'].values()))
                    if change=='root':c['root_reviewed']=False
                    elif change=='case':c['cases'].pop()
                    elif change=='duplicate':c['cases'].append(case)
                    elif change=='raw':case['raw']['hex']='504153530a'
                    elif change=='hash':case['raw']['sha256']='0'*64
                    elif change=='pin':case['raw']['artifact_pin']['size']=0
                    elif change=='warning':case['linker_diagnostics']=['warning']
                    elif change=='timeout':case['timed_out']=True
                    elif change=='public':case['public_address_matrix']['Name'].pop(case['expected_owner_publics'][0].lower())
                    elif change=='heading':case['map_sections']['Value']['heading_count']=0
                    elif change=='map-count':case['map_sections']['Name']['public_count']+=1
                    elif change=='common':control['communals'][0]['count']+=1
                    elif change=='extra-storage':control['communals'].append(dict(control['communals'][0],name='_invented_owner'))
                    elif change=='initializer':control['initialized_data_hex']['unexpected']='01'
                    elif change=='scope':c['historical_producer_or_placement_claimed']=True
                    elif change=='tools':c['inputs']=[]
                    with self.subTest(module=module,change=change):
                        with self.assertRaises(ValueError):
                            bindings.require_v24_storage_contracts(wrong,'rtlink400',tools['rtlink400'])
                c=report[key]
                alias_case=next((r for r in c['cases'] if r['aliases']),None)
                if alias_case:
                    wrong=json.loads(json.dumps(report));case=next(r for r in wrong[key]['cases'] if r['aliases'])
                    case['aliases'][0]['delta']+=1
                    with self.assertRaises(ValueError):bindings.require_v24_storage_contracts(wrong,'rtlink400',tools['rtlink400'])
                if c['save_rec_pointer_fixups']:
                    wrong=json.loads(json.dumps(report));wrong[key]['save_rec_pointer_fixups'][0]['encoded_addend']='02000000'
                    with self.assertRaises(ValueError):bindings.require_v24_storage_contracts(wrong,'rtlink400',tools['rtlink400'])
            for profile in ('rtlink400','rtlink610'):
                bindings.require_v24_storage_contracts(report,profile,tools[profile])

    def test_v23_event_records_require_complete_typed_storage_and_symbolic_bases(self):
        worker = ROOT/'build/workers/source_only_dos_tests'
        worker.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=worker) as directory:
            report = {'inputs': [], 'generated_files': [], 'translation_units': [], 'semantic_substitutions': []}
            _, symbols = dos.prepare(Path(directory), report)
            row = next(r for r in report['translation_units'] if r['module'] == 'source-owned:event-records')
            provider = row['storage_provider']
            source = (ROOT/row['source']['path']).read_text(encoding='ascii')
            def compile(text):
                result = compiler.compile_c(text, row['profile'], row['flags'], basename=row['basename'])
                self.assertTrue(result.ok, result.log)
                return OmfReader(communals=True).read(result.obj)
            bindings.review_provider_source(source, provider, symbols)
            proof = bindings.verify_provider(compile(source), provider)
            self.assertEqual(proof['communals'], [
                {'name': n, 'kind': 'far', 'count': 16, 'element_size': 1, 'length': 16}
                for n in ('_fd_50F6_49FA','_fd_50F6_4A0A')])
            for wrong in (source.replace('int code;', 'long code;'),
                          source.replace('fd_50F6_4A0A;', 'fd_50F6_4A0A = {0,0,0,0,0,0,0,1};')):
                with self.assertRaises(ValueError): bindings.verify_provider(compile(wrong), provider)
            # COMDEF cannot encode field order or signedness: the reviewed natural
            # source, separately from allocation geometry, must reject both.
            for wrong in (source.replace('int code;', 'unsigned int code;'),
                          source.replace('int h;\n    int v;', 'int v;\n    int h;')):
                self.assertEqual(bindings.verify_provider(compile(wrong), provider)['status'], 'PASS')
                with self.assertRaises(ValueError): bindings.review_provider_source(wrong, provider, symbols)
            for delta in (0,2):
                wrong = json.loads(json.dumps(symbols))
                wrong['data']['event_extra_view'] = dict(wrong['data']['fd_50F6_49FA'], off=0x49FA+delta)
                with self.assertRaises(ValueError): bindings.review_provider_source(source, provider, wrong)
            report['runtime_components'] = []
            tools = compiler.toolchain()['linkers']
            for profile in ('rtlink400','rtlink610'):
                bindings.require_v23_storage_contracts(report, profile, tools[profile])
            for change in ('root','case','duplicate','raw','hash','timeout','warning','abi','common',
                           'initialized','public','section','slot','target','addend','fixup','pad','shift','tool','scope'):
                wrong = json.loads(json.dumps(report)); contract = wrong['event_records_contract']
                case = next(r for r in contract['cases'] if r['linker'] == 'rtlink400' and r['case'] == 'positive')
                if change == 'root': contract['root_reviewed'] = False
                elif change == 'case': contract['cases'].remove(case)
                elif change == 'duplicate': contract['cases'].append(case)
                elif change == 'raw': case['runtime_log']['exact_raw_bytes_hex'] = '504153530a'
                elif change == 'hash': case['runtime_log']['sha256'] = '0'*64
                elif change == 'timeout': case['timed_out'] = True
                elif change == 'warning': case['linker_diagnostics'] = ['warning']
                elif change == 'abi': contract['source_abi']['offsets'][-1] = 16
                elif change == 'common': case['owner_omf']['communals'][0]['count'] = 15
                elif change == 'initialized': case['owner_omf']['initialized_segment_hex'] = {'extra':'00'}
                elif change == 'public': case['public_address_matrix']['Name'].pop('_fd_50F6_49FA')
                elif change == 'section': case['map_sections']['Value']['heading_present'] = False
                elif change == 'slot': case['pointer_fixups'][0]['eventBases_far_pointer_slot_offset'] = 2
                elif change == 'target': case['pointer_fixups'][0]['target_symbol'] = '_fd_50F6_4A0A'
                elif change == 'addend': case['pointer_fixups'][0]['encoded_addend_hex'] = '02000000'
                elif change == 'fixup': case['base_initializer_omf']['linker_fixups'].pop()
                elif change == 'pad': contract['positive_layout_shift']['rtlink400']['pad_communals'][0]['count'] = 1
                elif change == 'shift':
                    shifted = next(r for r in contract['cases'] if r['linker'] == 'rtlink400' and r['case'] == 'positive_shifted')
                    shifted['public_address_matrix']['Name']['_fd_50F6_49FA'] = '0000:0000'
                elif change == 'tool': contract['inputs'] = []
                elif change == 'scope': contract['event_code_stability_claimed'] = True
                with self.subTest(change=change):
                    with self.assertRaises(ValueError):
                        bindings.require_v23_storage_contracts(wrong, 'rtlink400', tools['rtlink400'])

    def test_v22_histogram_requires_source_extent_and_complete_runtime_evidence(self):
        worker = ROOT/'build/workers/source_only_dos_tests'
        worker.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=worker) as directory:
            report = {'inputs': [], 'generated_files': [], 'translation_units': [], 'semantic_substitutions': []}
            _, symbols = dos.prepare(Path(directory), report)
            row = next(r for r in report['translation_units'] if r['module'] == 'source-owned:ant-class-histogram')
            provider = row['storage_provider']
            source = (ROOT/row['source']['path']).read_text(encoding='ascii')
            def compile(text):
                result = compiler.compile_c(text, row['profile'], row['flags'], basename=row['basename'])
                self.assertTrue(result.ok, result.log)
                return OmfReader(communals=True).read(result.obj)
            bindings.review_provider_source(source, provider, symbols)
            proof = bindings.verify_provider(compile(source), provider)
            self.assertEqual(proof['communals'], [{'name': '_fd_50F6_0EB6', 'kind': 'far',
                'count': 32, 'element_size': 2, 'length': 64}])
            for wrong in (source.replace('[32]', '[31]'), source.replace('int far', 'unsigned char far').replace('[32]', '[64]'),
                          source.replace('[32];', '[32] = {1};')):
                with self.assertRaises(ValueError): bindings.verify_provider(compile(wrong), provider)
            unsigned = source.replace('int far', 'unsigned int far')
            self.assertEqual(bindings.verify_provider(compile(unsigned), provider)['status'], 'PASS')
            with self.assertRaises(ValueError): bindings.review_provider_source(unsigned, provider, symbols)
            for delta in (0, 2):
                wrong = json.loads(json.dumps(symbols))
                wrong['data']['histogram_extra_view'] = dict(wrong['data']['fd_50F6_0EB6'], off=0x0EB6+delta)
                with self.assertRaises(ValueError): bindings.review_provider_source(source, provider, wrong)
            report['runtime_components'] = []
            tool = compiler.toolchain()['linkers']
            for profile in ('rtlink400', 'rtlink610'):
                bindings.require_v22_storage_contracts(report, profile, tool[profile])
            for change in ('root', 'missing', 'duplicate', 'result', 'raw', 'hash', 'timeout', 'warning',
                           'shape', 'initializer', 'public', 'section', 'delta', 'empty_relations', 'tool'):
                wrong = json.loads(json.dumps(report)); contract = wrong['ant_class_histogram_contract']
                case = next(r for r in contract['cases'] if r['linker'] == 'rtlink400')
                if change == 'root': contract['root_reviewed'] = False
                elif change == 'missing': contract['cases'].remove(case)
                elif change == 'duplicate': contract['cases'].append(case)
                elif change == 'result': case['actual'] = 'FAIL'
                elif change == 'raw': case['actual_marker_bytes_hex'] = '504153530a'
                elif change == 'hash': case['run_log_pin']['sha256'] = '0'*64
                elif change == 'timeout': case['timed_out'] = True
                elif change == 'warning': case['linker_diagnostics'] = ['warning']
                elif change == 'shape': contract['compiler_controls']['fixtures']['BYTE']['actual_communals'][0]['element_size'] = 2
                elif change == 'initializer': contract['compiler_controls']['fixtures']['INITIALIZED']['initialized_segments_hex'] = {}
                elif change == 'public': case['public_address_matrix']['Name'].pop('_fd_50f6_0eb6')
                elif change == 'section': case['map_public_sections']['Value']['heading_present'] = False
                elif change == 'delta': case['alias_map_relations'][0]['expected_offset_delta'] = 2
                elif change == 'empty_relations': case['alias_map_relations'] = []
                elif change == 'tool': contract['inputs'] = []
                with self.subTest(change=change):
                    with self.assertRaises(ValueError):
                        bindings.require_v22_storage_contracts(wrong, 'rtlink400', tool['rtlink400'])

    def test_v21_scalar_cohorts_require_typed_owners_and_complete_raw_map_controls(self):
        worker=ROOT/'build/workers/source_only_dos_tests'
        worker.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=worker) as directory:
            report={'inputs': [], 'generated_files': [], 'translation_units': [], 'semantic_substitutions': []}
            _,symbols=dos.prepare(Path(directory),report)
            rows=[r for r in report['translation_units'] if r['module'] in bindings.V21_SCALAR_CONTRACTS]
            self.assertEqual(len(rows),3)
            self.assertEqual(sum(len(r['storage_provider']['communals']) for r in rows),44)
            self.assertEqual(sum(c['length'] for r in rows for c in r['storage_provider']['communals']),112)
            for row in rows:
                provider=row['storage_provider'];source=(ROOT/row['source']['path']).read_text(encoding='ascii')
                first=provider['communals'][0]['name'][1:]
                def compile(text):
                    result=compiler.compile_c(text,row['profile'],row['flags'],basename=row['basename'])
                    self.assertTrue(result.ok,result.log)
                    return OmfReader(communals=True).read(result.obj)
                bindings.review_provider_source(source,provider,symbols)
                self.assertEqual(bindings.verify_provider(compile(source),provider)['status'],'PASS')
                wide=source.replace('int far '+first,'long far '+first)
                with self.assertRaises(ValueError):bindings.verify_provider(compile(wide),provider)
                unsigned=source.replace('int far '+first,'unsigned int far '+first)
                self.assertEqual(bindings.verify_provider(compile(unsigned),provider)['status'],'PASS')
                with self.assertRaises(ValueError):bindings.review_provider_source(unsigned,provider,symbols)
                initialized=source.replace(first+';',first+' = 1;')
                with self.assertRaises(ValueError):bindings.verify_provider(compile(initialized),provider)
                for offset in (0,1):
                    registry=json.loads(json.dumps(symbols))
                    registry['data']['unreviewed_scalar_alias']=dict(registry['data'][first],off=registry['data'][first]['off']+offset)
                    with self.assertRaises(ValueError):bindings.review_provider_source(source,provider,registry)
            report['runtime_components']=[];tc=compiler.toolchain()
            for profile in ('rtlink400','rtlink610'):
                bindings.require_v21_storage_contracts(report,profile,tc['linkers'][profile])
            for module,(key,_) in bindings.V21_SCALAR_CONTRACTS.items():
                for change in ('root','missing','duplicate','result','raw_result','warning','tool',
                               'shape','public','section','empty_aliases','delta','address'):
                    wrong=json.loads(json.dumps(report));contract=wrong[key]
                    case=next(r for r in contract['cases'] if r['linker']=='rtlink400' and r['reviewed_alias_relations'])
                    if change=='root':contract['root_reviewed']=False
                    elif change=='missing':contract['cases'].remove(case)
                    elif change=='duplicate':contract['cases'].append(dict(case))
                    elif change=='result':case['actual']='UNREVIEWED'
                    elif change=='raw_result':case['actual_marker_bytes_hex']='00'
                    elif change=='warning':case['linker_diagnostics']=['Unresolved external']
                    elif change=='tool':
                        for identity in contract['inputs']:identity['sha256']='0'*64
                    elif change=='shape':contract['compiler_controls']['wide'][0]['length']=2
                    elif change=='public':case['required_publics'].pop()
                    elif change=='section':case['public_address_matrix'].pop('Value')
                    elif change=='empty_aliases':case['reviewed_alias_relations']=[]
                    elif change=='delta':case['reviewed_alias_relations'][0]['delta']+=1
                    else:case['reviewed_alias_relations'][0]['name_alias']='FFFF:0000'
                    with self.assertRaises(ValueError,msg=module+' '+change):
                        bindings.require_v21_storage_contracts(wrong,'rtlink400',tc['linkers']['rtlink400'])
            wrong=json.loads(json.dumps(report))
            wrong['ant_movement_words_contract']['compiler_controls']['save_rec_pointer_fixups']['shifted_rows'][0]['raw_offset_addend']=0
            with self.assertRaises(ValueError):
                bindings.require_v21_storage_contracts(wrong,'rtlink400',tc['linkers']['rtlink400'])

    def test_v21_sound_records_require_complete_views_extents_and_unexecuted_failure(self):
        worker=ROOT/'build/workers/source_only_dos_tests'
        worker.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=worker) as directory:
            report={'inputs': [], 'generated_files': [], 'translation_units': [], 'semantic_substitutions': []}
            _,symbols=dos.prepare(Path(directory),report)
            row=next(r for r in report['translation_units'] if r['module']=='source-owned:sound-record-arrays')
            dos.audit_layout(report)
            # Complete data owners cannot discharge an executable overread.
            dependency=next(r for r in report['layout_dependencies'] if r['id']=='sound-selector-out-of-range-layout')
            self.assertEqual(dependency['status'],'UNRESOLVED')
            provider=row['storage_provider'];source=(ROOT/row['source']['path']).read_text(encoding='ascii')
            def compile(text):
                result=compiler.compile_c(text,row['profile'],row['flags'],basename=row['basename'])
                self.assertTrue(result.ok,result.log)
                return OmfReader(communals=True).read(result.obj)
            bindings.review_provider_source(source,provider,symbols)
            self.assertEqual(bindings.verify_provider(compile(source),provider)['status'],'PASS')
            for wrong in (source.replace('[56]','[57]'),source.replace('[33]','[32]'),
                          source.replace('union VoicePayload payload','char near *payload'),
                          source.replace('fd_50F6_0000[56];','fd_50F6_0000[56] = { 1 };')):
                with self.assertRaises(ValueError): bindings.verify_provider(compile(wrong),provider)
            unsigned=source.replace('int kind','unsigned int kind')
            self.assertEqual(bindings.verify_provider(compile(unsigned),provider)['status'],'PASS')
            with self.assertRaises(ValueError): bindings.review_provider_source(unsigned,provider,symbols)
            near_union=source.replace('char far *sample','char near *sample')
            self.assertEqual(bindings.verify_provider(compile(near_union),provider)['status'],'PASS')
            with self.assertRaises(ValueError): bindings.review_provider_source(near_union,provider,symbols)
            for off in (0,2):
                registry=json.loads(json.dumps(symbols))
                registry['data']['unreviewed_voice_view']=dict(registry['data']['fd_50F6_0000'],off=off)
                with self.assertRaises(ValueError): bindings.review_provider_source(source,provider,registry)
            report['runtime_components']=[];tc=compiler.toolchain()
            for profile in ('rtlink400','rtlink610'):
                bindings.require_v21_storage_contracts(report,profile,tc['linkers'][profile])
            for change in ('root','missing','duplicate','result','warning','tool','shape','view',
                           'heading','public','address','length','range','overlap','negative_missing',
                           'negative_executed','negative_symbol','negative_run'):
                wrong=json.loads(json.dumps(report));contract=wrong['sound_record_arrays_contract']
                case=next(r for r in contract['cases'] if r['linker']=='rtlink400' and r['case']=='positive_exact_provider')
                if change=='root':contract['root_reviewed']=False
                elif change=='missing':contract['cases'].remove(case)
                elif change=='duplicate':contract['cases'].append(dict(case))
                elif change=='result':case['actual']='UNREVIEWED'
                elif change=='warning':case['linker_diagnostics']=['Unresolved external']
                elif change=='tool':
                    for identity in contract['inputs']:identity['sha256']='0'*64
                elif change=='shape':contract['compiler_controls']['SNDS4']['communals'][0]['length']=336
                elif change=='view':contract['sizeof_offsetof_assertions'].pop()
                elif change=='heading':case['map_public_sections']['Name']['heading_present']=False
                elif change=='public':case['map_public_sections']['Name']['publics'].pop('_fd_50F6_0000')
                elif change=='address':case['map_public_sections']['Value']['publics']['_fd_50F6_0000']='FFFF:0000'
                elif change=='length':case['far_bss_layout']['length']=540
                elif change=='range':case['far_bss_layout']['stop_linear']-=1
                elif change=='overlap':
                    case['far_bss_layout']['symbols']['_FD_50F6_0000']=dict(case['far_bss_layout']['symbols']['_FD_50F6_4A4E'])
                    for section in case['map_public_sections'].values():
                        section['publics']['_fd_50F6_0000']=section['publics']['_fd_50F6_4A4E']
                else:
                    negative=next(r for r in contract['link_binding_negative_controls'] if r['linker']=='rtlink400')
                    if change=='negative_missing':contract['link_binding_negative_controls'].remove(negative)
                    elif change=='negative_executed':negative['executed']=True
                    elif change=='negative_symbol':negative['diagnosed_symbol']='_fd_50F6_0002'
                    else:negative['run_log_absent']=False
                with self.assertRaises(ValueError,msg=change):
                    bindings.require_v21_storage_contracts(wrong,'rtlink400',tc['linkers']['rtlink400'])

    def test_v20_sound_words_require_types_shapes_and_complete_alias_maps(self):
        worker=ROOT/'build/workers/source_only_dos_tests'
        worker.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=worker) as directory:
            report={'inputs': [], 'generated_files': [], 'translation_units': [], 'semantic_substitutions': []}
            _,symbols=dos.prepare(Path(directory),report)
            row=next(r for r in report['translation_units'] if r['module']=='source-owned:sound-control-words')
            provider=row['storage_provider'];source=(ROOT/row['source']['path']).read_text(encoding='ascii')
            def compile(text):
                result=compiler.compile_c(text,row['profile'],row['flags'],basename=row['basename'])
                self.assertTrue(result.ok,result.log)
                return OmfReader(communals=True).read(result.obj)
            bindings.review_provider_source(source,provider,symbols)
            self.assertEqual(bindings.verify_provider(compile(source),provider)['status'],'PASS')
            wide=source.replace('int far','long far')
            with self.assertRaises(ValueError): bindings.verify_provider(compile(wide),provider)
            unsigned=source.replace('int far','unsigned int far')
            self.assertEqual(bindings.verify_provider(compile(unsigned),provider)['status'],'PASS')
            with self.assertRaises(ValueError): bindings.review_provider_source(unsigned,provider,symbols)
            initialized=source.replace('fd_50F6_4A46;','fd_50F6_4A46 = 1;')
            with self.assertRaises(ValueError): bindings.verify_provider(compile(initialized),provider)
            for off in (0,1):
                registry=json.loads(json.dumps(symbols))
                registry['data']['unreviewed_view']=dict(registry['data']['fd_50F6_4A46'],off=0x4A46+off)
                with self.assertRaises(ValueError): bindings.review_provider_source(source,provider,registry)
            report['runtime_components']=[];tc=compiler.toolchain()
            for profile in ('rtlink400','rtlink610'):
                bindings.require_v20_storage_contracts(report,profile,tc['linkers'][profile])
            for change in ('root','missing','duplicate','result','warning','tool','shape','heading',
                           'required_public','empty_aliases','missing_alias','delta','address','section'):
                wrong=json.loads(json.dumps(report));contract=wrong['sound_control_words_contract']
                case=next(r for r in contract['cases'] if r['linker']=='rtlink400' and r['case']=='typed_raw_positive')
                if change=='root':contract['root_reviewed']=False
                elif change=='missing':contract['cases'].remove(case)
                elif change=='duplicate':contract['cases'].append(dict(case))
                elif change=='result':case['actual']='UNREVIEWED'
                elif change=='warning':case['linker_diagnostics']=['Unresolved external']
                elif change=='tool':
                    for identity in contract['inputs']:identity['sha256']='0'*64
                elif change=='shape':contract['compiler_controls']['wider_communals'][0]['length']=2
                elif change=='heading':case['map_public_sections']['Name']['heading_present']=False
                elif change=='required_public':case['required_publics'].pop()
                elif change=='empty_aliases':case['alias_map_relations']=[]
                elif change=='missing_alias':case['alias_map_relations'].pop()
                elif change=='delta':case['alias_map_relations'][0]['expected_offset_delta']=2
                elif change=='address':case['alias_map_relations'][0]['alias_address_name_section']='FFFF:0000'
                else:case['alias_map_relations'][0]['alias_address_value_section']='FFFF:0000'
                with self.assertRaises(ValueError,msg=change):
                    bindings.require_v20_storage_contracts(wrong,'rtlink400',tc['linkers']['rtlink400'])

    def test_v19_storage_rejects_wrong_shapes_and_incomplete_control_receipts(self):
        worker=ROOT/'build/workers/source_only_dos_tests'
        worker.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=worker) as directory:
            report={'inputs': [], 'generated_files': [], 'translation_units': [], 'semantic_substitutions': []}
            _,symbols=dos.prepare(Path(directory),report)
            rows=[r for r in report['translation_units'] if r['module'] in bindings.V19_STORAGE_CONTRACTS]
            self.assertEqual(len(rows),3)
            self.assertEqual(sum(c['length'] for r in rows for c in r['storage_provider']['communals']),22)
            for row in rows:
                provider=row['storage_provider']
                source=(ROOT/row['source']['path']).read_text(encoding='ascii')
                def compile(text):
                    result=compiler.compile_c(text,row['profile'],row['flags'],basename=row['basename'])
                    self.assertTrue(result.ok,result.log)
                    return OmfReader(communals=True).read(result.obj)
                bindings.review_provider_source(source,provider,symbols)
                self.assertEqual(bindings.verify_provider(compile(source),provider)['status'],'PASS')
                # A scalar's wider allocation and an array's identical-byte,
                # wrong-element allocation cannot replace their recovered types.
                wrong=(source.replace('int far','unsigned char far').replace('[7]','[14]')
                       if row['module'].endswith('saved-sound-state') else source.replace('int far','long far'))
                with self.assertRaises(ValueError): bindings.verify_provider(compile(wrong),provider)
                with self.assertRaises(ValueError): bindings.review_provider_source(wrong,provider,symbols)
                unsigned=source.replace('int far','unsigned int far')
                # Signedness is invisible in OMF, so source and runtime evidence
                # must enforce it rather than claiming a size check does so.
                self.assertEqual(bindings.verify_provider(compile(unsigned),provider)['status'],'PASS')
                with self.assertRaises(ValueError): bindings.review_provider_source(unsigned,provider,symbols)
                registry=json.loads(json.dumps(symbols)); name=provider['communals'][0]['name'][1:]
                registry['data']['unreviewed_interior']=dict(registry['data'][name],off=registry['data'][name]['off']+1)
                with self.assertRaises(ValueError): bindings.review_provider_source(source,provider,registry)
            report['runtime_components']=[]
            tc=compiler.toolchain()
            for profile in ('rtlink400','rtlink610'):
                bindings.require_v19_storage_contracts(report,profile,tc['linkers'][profile])
            for module,(key,required) in bindings.V19_STORAGE_CONTRACTS.items():
                for change in ('root','missing','duplicate','result','map','warning','tool'):
                    wrong=json.loads(json.dumps(report)); contract=wrong[key]
                    index=next(i for i,r in enumerate(contract['cases']) if r['linker']=='rtlink400')
                    if change=='root': contract['root_reviewed']=False
                    elif change=='missing': contract['cases'].pop(index)
                    elif change=='duplicate': contract['cases'].append(dict(contract['cases'][index]))
                    elif change=='result': contract['cases'][index]['actual']='UNREVIEWED'
                    elif change=='map': contract['cases'][index]['owner_publics_found_in_map'].pop()
                    elif change=='warning': contract['cases'][index]['linker_diagnostics']=['Unresolved external']
                    else:
                        for identity in contract['inputs']: identity['sha256']='0'*64
                    with self.assertRaisesRegex(ValueError,'startup contract'):
                        bindings.require_v19_storage_contracts(wrong,'rtlink400',tc['linkers']['rtlink400'])
            for change in ('short','width','missing_shape','measurement','alias','zero_relabel'):
                wrong=json.loads(json.dumps(report)); contract=wrong['saved_sound_state_contract']
                if change=='short': contract['candidate_source_contract']['short_extent_comdef'][0]['length']=14
                elif change=='width': contract['candidate_source_contract']['wrong_width_comdef'][0]['element_size']=2
                elif change=='missing_shape': contract['controls'].pop('short_extent_shape_rejected')
                else:
                    case=next(r for r in contract['cases'] if r['linker']=='rtlink400' and r['case']=='short_extent_control')
                    if change=='measurement': case['far_bss_layout']['owner_far_bss_region_length']=14
                    elif change=='alias': case['far_bss_layout']['required_publics'].pop('_fd_55B3_74FE')
                    else: case['actual']='FAIL'
                with self.assertRaises(ValueError): bindings.require_v19_storage_contracts(wrong,'rtlink400',tc['linkers']['rtlink400'])
            wrong=json.loads(json.dumps(report))
            wrong['control_flag_words_contract']['compiler_negative_controls'][1]['observed']['length']=2
            with self.assertRaisesRegex(ValueError,'rejected compiler shapes'):
                bindings.require_v19_storage_contracts(wrong,'rtlink400',tc['linkers']['rtlink400'])

    def test_s01_pattern_view_adds_only_the_closed_fixup_in_alternate_output(self):
        worker=ROOT/'build/workers/source_only_dos_tests'
        worker.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=worker) as directory:
            report={'inputs': [], 'generated_files': [], 'translation_units': [], 'semantic_substitutions': []}
            manifest,symbols=dos.prepare(Path(directory),report)
            row=next(r for r in report['translation_units'] if r['module']=='S01:3126')
            binding=row['source_binding']
            self.assertTrue(binding['s01_pattern_view_operands'])
            self.assertTrue((ROOT/row['generated_source']['path']).is_relative_to(Path(directory)))
            before=(ROOT/row['binding_control_source']['path']).read_text(encoding='latin1')
            after=(ROOT/row['generated_source']['path']).read_text(encoding='latin1')
            def assemble(text):
                result=compiler.assemble(text,row['profile'],row['flags'],basename=row['basename'])
                self.assertTrue(result.ok,result.log)
                return OmfReader(communals=True).read(result.obj)
            control=assemble(before)
            self.assertEqual(bindings.verify_objects(control,assemble(after),binding)['status'],'PASS')
            operand='mov bh, byte ptr ss:[bx+_g_4220]'
            self.assertEqual(after.count(operand),1)
            for text in (after.replace(operand,operand.replace('_g_4220','_g_4220+1')),
                         after.replace('assume ss:DGROUP\n\t'+operand,'assume ss:_DATA\n\t'+operand)):
                self.assertNotEqual(text,after)
                with self.assertRaises(ValueError): bindings.verify_objects(control,assemble(text),binding)
            wrong=json.loads(json.dumps(binding))
            site=next(s for s in wrong['relocations'] if s.get('s01_pattern_view_operand'))
            site['offsets']=[0x5A9]
            with self.assertRaisesRegex(ValueError,'unreviewed S01'):
                bindings.review_addresses(wrong,manifest['modules'][row['module']],symbols)
            report['runtime_components']=[]
            tc=compiler.toolchain()
            for profile in ('rtlink400','rtlink610'):
                bindings.require_s01_pattern_view_contract(report,profile,tc['linkers'][profile])
            for change in ('root','site','missing','frame','map','warning'):
                wrong=json.loads(json.dumps(report)); c=wrong['s01_pattern_view_contract']
                if change=='root': c['root_reviewed']=False
                elif change=='site': c['sites'][0][2]+=1
                elif change=='missing': c['cases'].pop(0)
                elif change=='frame': c['cases'][0]['actual_DS_SS_DGROUP']=False
                elif change=='map': c['cases'][0]['map']['passed']=False
                else: c['cases'][0]['linker_diagnostics']=['Unresolved external']
                with self.assertRaisesRegex(ValueError,'S01 pattern view'):
                    bindings.require_s01_pattern_view_contract(wrong,'rtlink400',tc['linkers']['rtlink400'])

    def test_serialized_owners_require_element_shape_and_complete_clean_runtime_matrix(self):
        worker=ROOT/'build/workers/source_only_dos_tests'
        worker.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=worker) as directory:
            report={'inputs': [], 'generated_files': [], 'translation_units': [], 'semantic_substitutions': []}
            _,symbols=dos.prepare(Path(directory),report)
            rows=[r for r in report['translation_units'] if r['module'] in bindings.V18_STORAGE_CONTRACTS]
            self.assertEqual(len(rows),2)
            self.assertEqual(sum(c['length'] for r in rows for c in r['storage_provider']['communals']),224)
            for row in rows:
                provider=row['storage_provider']
                source=(ROOT/row['source']['path']).read_text(encoding='ascii')
                def compile(text):
                    r=compiler.compile_c(text,row['profile'],row['flags'],basename=row['basename'])
                    self.assertTrue(r.ok,r.log)
                    return OmfReader(communals=True).read(r.obj)
                bindings.review_provider_source(source,provider,symbols)
                self.assertEqual(bindings.verify_provider(compile(source),provider)['status'],'PASS')
                contrast=(source.replace('unsigned char far','unsigned int far').replace('[50]','[25]')
                          if row['module'].endswith('swarm-serialized-buffers') else
                          source.replace('int far','unsigned char far').replace('[6]','[12]'))
                # Equal total extent cannot replace the recovered element width.
                with self.assertRaises(ValueError): bindings.verify_provider(compile(contrast),provider)
                with self.assertRaises(ValueError): bindings.review_provider_source(contrast,provider,symbols)
                wrong=json.loads(json.dumps(symbols))
                name=provider['communals'][0]['name'][1:]
                wrong['data']['unreviewed_interior']=dict(wrong['data'][name],off=wrong['data'][name]['off']+1)
                with self.assertRaises(ValueError): bindings.review_provider_source(source,provider,wrong)
            report['runtime_components']=[]
            tc=compiler.toolchain()
            for profile in ('rtlink400','rtlink610'):
                bindings.require_v18_storage_contracts(report,profile,tc['linkers'][profile])
            for module,(key,required) in bindings.V18_STORAGE_CONTRACTS.items():
                for change in ('root','missing','duplicate','result','map','warning','tool'):
                    wrong=json.loads(json.dumps(report)); contract=wrong[key]
                    index=next(i for i,r in enumerate(contract['cases']) if r['linker']=='rtlink400')
                    if change=='root': contract['root_reviewed']=False
                    elif change=='missing': contract['cases'].pop(index)
                    elif change=='duplicate': contract['cases'].append(dict(contract['cases'][index]))
                    elif change=='result': contract['cases'][index]['actual']='UNREVIEWED'
                    elif change=='map': contract['cases'][index]['owner_publics_found_in_map'].pop()
                    elif change=='warning': contract['cases'][index]['linker_diagnostics']=['Unresolved external']
                    else:
                        for identity in contract['inputs']: identity['sha256']='0'*64
                    with self.assertRaisesRegex(ValueError,'startup contract'):
                        bindings.require_v18_storage_contracts(wrong,'rtlink400',tc['linkers']['rtlink400'])

    def test_far_data_gap_requires_real_source_object_and_exact_linker_contrast(self):
        contract = json.loads((ROOT/'work/source-only-dos/far-data-paragraph-fill-contract-v1.json').read_text())
        tc = compiler.toolchain()
        for profile in ('rtlink400', 'rtlink610'):
            tool = tc['linkers'][profile]
            components = [(str(Path(tool['directory'])/name), digest) for name,digest in tool['files'].items()]
            alignment.require_contract(contract, profile, components)
        for change in ('root', 'missing', 'duplicate', 'gap', 'map', 'warning', 'extra_owner', 'moved_bss'):
            wrong = json.loads(json.dumps(contract))
            rows = wrong['controls']['linker_results']
            if change == 'root': wrong['root_reviewed'] = False
            elif change == 'missing': rows.pop()
            elif change == 'duplicate': rows[1] = dict(rows[0])
            elif change == 'gap': rows[0]['gap_bytes'] = 0
            elif change == 'map': rows[0]['map_rows_asserted'].pop()
            elif change == 'warning': rows[0]['linker_diagnostics'] = ['unresolved symbol']
            elif change == 'extra_owner': wrong['extra_storage_bytes'] = 12
            else: rows[1]['far_bss']['start_offset'] += 16
            with self.assertRaises(ValueError): alignment.require_contract(wrong)
        with self.assertRaises(ValueError):
            alignment.require_contract(contract, 'rtlink400', [('unknown-linker', '0'*64)])
        worker = ROOT/'build/workers/source_only_dos_tests'
        worker.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=worker) as directory:
            report = {'inputs': [], 'generated_files': [], 'translation_units': [], 'semantic_substitutions': []}
            dos.prepare(Path(directory), report)
            row = next(r for r in report['translation_units'] if r['module']=='root:1F80')
            source = (ROOT/row['generated_source']['path']).read_text(encoding='latin1')
            def object_for(text):
                result=compiler.compile_c(text, row['profile'], row['flags'], basename=row['basename'])
                self.assertTrue(result.ok, result.log)
                path=Path(directory)/'owner.obj'
                path.write_bytes(result.obj)
                row['object']=dos.pin(path)[1]
            object_for(source)
            self.assertEqual(alignment.verify_source_object(ROOT, report)['functional_fill_bytes'],12)
            # The original source declares a 100-byte static far text buffer.
            self.assertIn('[100]',source)
            object_for(source.replace('[100]', '[112]'))
            with self.assertRaisesRegex(ValueError,'OMF extent/alignment'):
                alignment.verify_source_object(ROOT, report)
            object_for(source)
            row['generated_source']['sha256']='0'*64
            with self.assertRaisesRegex(ValueError,'generated source'):
                alignment.verify_source_object(ROOT, report)

    def test_control_resource_terrain_owners_require_source_types_and_full_control_matrix(self):
        worker = ROOT / 'build/workers/source_only_dos_tests'
        worker.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=worker) as directory:
            report = {'inputs': [], 'generated_files': [], 'translation_units': [], 'semantic_substitutions': []}
            _, symbols = dos.prepare(Path(directory), report)
            rows = [r for r in report['translation_units'] if r['module'] in bindings.V17_STORAGE_CONTRACTS]
            self.assertEqual(len(rows), 3)
            self.assertEqual(sum(len(r['storage_provider']['communals']) for r in rows), 20)
            self.assertEqual(sum(c['length'] for r in rows for c in r['storage_provider']['communals']), 82)
            for row in rows:
                provider = row['storage_provider']
                source = (ROOT / row['source']['path']).read_text(encoding='ascii')
                result = compiler.compile_c(source, row['profile'], row['flags'], basename=row['basename'])
                self.assertTrue(result.ok, result.log)
                bindings.review_provider_source(source, provider, symbols)
                bindings.verify_provider(OmfReader(communals=True).read(result.obj), provider)
                # Equal-width C types can have distinct semantics despite
                # identical COMDEFs. The exact producer ABI must be guarded.
                if 'TriLevel' in source:
                    changed = source.replace('unsigned frac;', 'int frac;')
                elif 'EmsSlot' in source:
                    changed = source.replace('EmsSlot far * far * far', 'EmsSlot far * near * far')
                else:
                    changed = source.replace('int far Barrier;', 'unsigned int far Barrier;')
                with self.assertRaises(ValueError):
                    bindings.review_provider_source(changed, provider, symbols)
                changed_symbols = json.loads(json.dumps(symbols))
                name = provider['communals'][0]['name'][1:]
                changed_symbols['data']['new_interior'] = dict(changed_symbols['data'][name], off=changed_symbols['data'][name]['off']+1)
                with self.assertRaises(ValueError):
                    bindings.review_provider_source(source, provider, changed_symbols)
            tc = compiler.toolchain()
            for profile in ('rtlink400', 'rtlink610'):
                bindings.require_v17_storage_contracts(report, profile, tc['linkers'][profile])
            for module, (key, required) in bindings.V17_STORAGE_CONTRACTS.items():
                for change in ('missing', 'duplicate', 'result', 'dictionary', 'tool', 'unreviewed', 'unresolved', 'map'):
                    wrong = json.loads(json.dumps(report))
                    contract = wrong[key]
                    index = next(i for i,r in enumerate(contract['cases']) if r['linker'] == 'rtlink400')
                    if change == 'missing': contract['cases'].pop(index)
                    elif change == 'duplicate': contract['cases'].append(dict(contract['cases'][index]))
                    elif change == 'result': contract['cases'][index]['actual'] = 'UNREVIEWED'
                    elif change == 'dictionary': contract['required_cases']['extra'] = 'PASS'
                    elif change == 'unreviewed': contract['root_reviewed'] = False
                    elif change == 'unresolved': contract['cases'][index]['linker_diagnostics'] = ['Unresolved external']
                    elif change == 'map': contract['cases'][index]['owner_publics_found_in_map'].pop()
                    else:
                        for pin in contract['inputs']: pin['sha256'] = '0'*64
                    with self.assertRaisesRegex(ValueError, 'startup contract'):
                        bindings.require_v17_storage_contracts(wrong, 'rtlink400', tc['linkers']['rtlink400'])
            wrong = json.loads(json.dumps(report))
            wrong['ant_ui_control_state_contract']['compiler_negative_controls'][0]['actual_communal']['length'] = 6
            with self.assertRaisesRegex(ValueError, 'compiler negative controls'):
                bindings.require_v17_storage_contracts(wrong, 'rtlink400', tc['linkers']['rtlink400'])

    def test_display_selector_owner_requires_closed_producer_and_partial_debt_proof(self):
        worker = ROOT / 'build/workers/source_only_dos_tests'
        worker.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=worker) as directory:
            report = {'inputs': [], 'generated_files': [], 'translation_units': [], 'semantic_substitutions': []}
            _, symbols = dos.prepare(Path(directory), report)
            row = next(r for r in report['translation_units'] if r['module'] == 'source-owned:display-mode-selector')
            provider = row['storage_provider']
            source = (ROOT / row['source']['path']).read_text(encoding='ascii')
            def compile(text):
                result = compiler.compile_c(text, row['profile'], row['flags'], basename=row['basename'])
                self.assertTrue(result.ok, result.log)
                return OmfReader(communals=True).read(result.obj)
            self.assertEqual(bindings.verify_provider(compile(source), provider)['status'], 'PASS')
            for text in ('int near g_5A97;', 'unsigned char near g_5A97;', 'char far g_5A97;', 'char near g_5A97 = -1;'):
                with self.assertRaises(ValueError):
                    bindings.review_provider_source(text, provider, symbols)
            with self.assertRaises(ValueError):
                bindings.verify_provider(compile(source + '\nchar near extra_owner;\n'), provider)
            report['runtime_components'] = []
            for profile in ('rtlink400', 'rtlink610'):
                bindings.require_display_selector_contract(report, profile, compiler.toolchain()['linkers'][profile])
            for change in ('missing', 'duplicate', 'question_unsigned', 'status', 'message', 'dictionary', 'tool'):
                wrong = json.loads(json.dumps(report))
                c = wrong['display_mode_selector_contract']
                if change == 'missing': c['cases'].pop(0)
                elif change == 'duplicate': c['cases'].append(dict(c['cases'][0]))
                elif change == 'question_unsigned': c['cases'][0]['actual_after'] = [255, 255, 255]
                elif change == 'status': c['cases'][16]['actual_status'] = 0
                elif change == 'message': c['cases'][16]['actual_before_and_after_log'] = 'BEFORE=0/0/0'
                elif change == 'dictionary': c['required_cases']['rtlink400:C99'] = {}
                else:
                    for identity in c['inputs']: identity['sha256'] = '0' * 64
                with self.assertRaisesRegex(ValueError, 'closed producer/runtime'):
                    bindings.require_display_selector_contract(wrong, 'rtlink400', compiler.toolchain()['linkers']['rtlink400'])
            # Admission removes precisely the overwritten selector byte. It
            # cannot turn ownership into initialization of the neighboring Rect.
            report['translation_units'] = [row]
            row['provider_verification'] = {'status': 'PASS'}
            report['layout_dependencies'] = [{'id': 'graphics-computed-copy-layout', 'status': 'UNRESOLVED'}]
            report['unresolved_data'] = [{'id': 'dgroup_5a96', 'size': 26}]
            # accept_binding_checks also requires an actual bound TU.
            report['translation_units'].append({'source_binding': {'module': 'root:15F8'}, 'binding_verification': {'status': 'PASS'}})
            dos.accept_binding_checks(report)
            self.assertEqual(report['unresolved_data'][0]['size'], 25)
            self.assertEqual(report['resolved_source_state'][0]['offset'], 1)
            self.assertEqual(report['layout_dependencies'][0]['status'], 'UNRESOLVED')

    def test_v15_far_owners_reject_type_extent_and_registry_view_guesses(self):
        worker = ROOT / 'build/workers/source_only_dos_tests'
        worker.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=worker) as directory:
            report = {'inputs': [], 'generated_files': [], 'translation_units': [], 'semantic_substitutions': []}
            _, symbols = dos.prepare(Path(directory), report)
            rows = [r for r in report['translation_units'] if r['module'] in bindings.V15_STORAGE_CONTRACTS]
            self.assertEqual(len(rows), 7)
            self.assertEqual(sum(len(r['storage_provider']['communals']) for r in rows), 33)
            for row in rows:
                provider = row['storage_provider']
                source = (ROOT / row['source']['path']).read_text(encoding='ascii')
                def compile(text):
                    result = compiler.compile_c(text, row['profile'], row['flags'], basename=row['basename'])
                    self.assertTrue(result.ok, result.log)
                    return OmfReader(communals=True).read(result.obj)
                bindings.review_provider_source(source, provider, symbols)
                self.assertEqual(bindings.verify_provider(compile(source), provider)['status'], 'PASS')
                if 'StrList' in source:
                    wrong_type = source.replace('char far * far *StrList', 'char far * near *StrList')
                elif 'unsigned char' in source:
                    wrong_type = source.replace('unsigned char', 'signed char', 1)
                elif 'long far' in source:
                    wrong_type = source.replace('long far', 'unsigned long far', 1)
                else:
                    wrong_type = source.replace('int far', 'unsigned int far', 1)
                with self.assertRaises(ValueError):
                    bindings.review_provider_source(wrong_type, provider, symbols)
                # OMF does not encode source signedness/pointer depth. Source
                # guards and object guards therefore prove different facts.
                with self.assertRaises(ValueError):
                    bindings.verify_provider(compile(source + '\nint far extra_owner;\n'), provider)
                changed = json.loads(json.dumps(symbols))
                name = provider['communals'][0]['name'][1:]
                changed['data'][name]['off'] += 1
                with self.assertRaises(ValueError):
                    bindings.review_provider_source(source, provider, changed)
                changed = json.loads(json.dumps(symbols))
                changed['data']['invented_same_base_view'] = dict(changed['data'][name])
                with self.assertRaises(ValueError):
                    bindings.review_provider_source(source, provider, changed)

    def test_v15_runtime_matrix_preserves_special_results_and_excludes_diagnostics(self):
        worker = ROOT / 'build/workers/source_only_dos_tests'
        worker.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=worker) as directory:
            report = {'inputs': [], 'generated_files': [], 'translation_units': [], 'semantic_substitutions': []}
            dos.prepare(Path(directory), report)
            report['runtime_components'] = []
            tc = compiler.toolchain()
            for profile in ('rtlink400', 'rtlink610'):
                bindings.require_v15_storage_contracts(report, profile, tc['linkers'][profile])
            for module, (key, required) in bindings.V15_STORAGE_CONTRACTS.items():
                for change in ('missing', 'duplicate', 'result', 'dictionary', 'tool'):
                    wrong = json.loads(json.dumps(report))
                    contract = wrong[key]
                    index = next(i for i, r in enumerate(contract['cases']) if r['linker'] == 'rtlink400')
                    if change == 'missing': contract['cases'].pop(index)
                    elif change == 'duplicate': contract['cases'].append(dict(contract['cases'][index]))
                    elif change == 'result': contract['cases'][index]['actual'] = 'UNREVIEWED'
                    elif change == 'dictionary': contract['required_cases']['invented_positive'] = 'PASS'
                    else:
                        for identity in contract['inputs']: identity['sha256'] = '0' * 64
                    with self.assertRaisesRegex(ValueError, 'startup contract'):
                        bindings.require_v15_storage_contracts(wrong, 'rtlink400', tc['linkers']['rtlink400'])
            self.assertNotIn('wrong_long_extent_width_control',
                             bindings.V15_STORAGE_CONTRACTS['source-owned:player-locations'][1])
            self.assertNotIn('wrong_two_byte_owner_extent_diagnostic',
                             bindings.V15_STORAGE_CONTRACTS['source-owned:ant-counters-timer'][1])

    def test_initialized_recipes_reject_wrong_values_types_and_extra_live_contributions(self):
        worker = ROOT / 'build/workers/source_only_dos_tests'
        worker.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=worker) as directory:
            report = {'inputs': [], 'generated_files': [], 'translation_units': [], 'semantic_substitutions': []}
            _, symbols = dos.prepare(Path(directory), report)
            for module in bindings.INITIALIZED_PROVIDER_SPECS:
                row = next(r for r in report['translation_units'] if r['module'] == module)
                provider = row['storage_provider']
                text = (ROOT / row['source']['path']).read_text(encoding='ascii')
                def compile(source):
                    result = compiler.compile_c(source, row['profile'], row['flags'], basename=row['basename'])
                    self.assertTrue(result.ok, result.log)
                    return OmfReader(communals=True).read(result.obj)
                bindings.review_provider_source(text, provider, symbols)
                self.assertEqual(bindings.verify_provider(compile(text), provider)['status'], 'PASS')
                wrong_value = text.replace('0x80u', '0x40u') if module.endswith('graphics-formulas') else text.replace('0x00F', '0x00A')
                for contrast in (wrong_value, text.replace('unsigned char near', 'unsigned char far'),
                                 text + '\nint near extra_live = 1;\n', text + '\nint extra_code(void) { return 1; }\n'):
                    with self.assertRaises(ValueError):
                        bindings.verify_provider(compile(contrast), provider)
                    with self.assertRaises(ValueError):
                        bindings.review_provider_source(contrast, provider, symbols)
                changed = json.loads(json.dumps(provider))
                changed['public_DATA'][0]['offset'] += 1
                with self.assertRaises(ValueError):
                    bindings.verify_provider(compile(text), changed)
            # Initialization closes functional payload only; historical ledger and
            # the unchecked clip-copy layout gate stay explicit.
            dos.audit_layout(report)
            for row in report['translation_units']:
                if row.get('source_binding'):
                    row['binding_verification'] = {'status': 'PASS'}
                if row.get('storage_provider'):
                    row['provider_verification'] = {'status': 'PASS'}
            dos.accept_binding_checks(report)
            self.assertEqual(sum(r['size'] for r in report['unresolved_data']), 78)
            self.assertEqual(sum(r['size'] for r in report['historical_data_debt']), 113)
            self.assertEqual(sum(r['size'] for r in report['resolved_initialized_data']), 34)
            self.assertEqual(next(r['status'] for r in report['layout_dependencies']
                                  if r['id'] == 'graphics-computed-copy-layout'), 'UNRESOLVED')
            self.assertFalse(any(r['id'] in ('dgroup_2100', 'dgroup_68ac') for r in report['unresolved_data']))

    def test_indexed_sites_and_generated_glyph_view_are_closed_and_preserve_whole_objects(self):
        worker = ROOT / 'build/workers/source_only_dos_tests'
        worker.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=worker) as directory:
            report = {'inputs': [], 'generated_files': [], 'translation_units': [], 'semantic_substitutions': []}
            manifest, symbols = dos.prepare(Path(directory), report)
            modules = set(bindings.INDEXED_OPERANDS) | set(bindings.GRAPHICS_MASK_OPERANDS) | {'root:2650'}
            for row in report['translation_units']:
                if row['module'] not in modules:
                    continue
                binding = row['source_binding']
                original = (ROOT / row['source']['path']).read_text(encoding='latin1')
                generated = (ROOT / row['generated_source']['path']).read_text(encoding='latin1')
                def assemble(source):
                    result = compiler.assemble(source, row['profile'], row['flags'], basename=row['basename'])
                    self.assertTrue(result.ok, result.log)
                    return OmfReader(communals=True).read(result.obj)
                control, candidate = assemble(original), assemble(generated)
                bindings.review_addresses(binding, manifest['modules'][row['module']], symbols)
                self.assertEqual(bindings.verify_objects(control, candidate, binding)['status'], 'PASS')
                changed = json.loads(json.dumps(binding))
                selected = next((s for s in changed['relocations'] if s.get('indexed_operand') or s.get('graphics_mask_operand')), None)
                if selected:
                    selected['offsets'][0] += 1
                else:
                    changed['exports'][0]['offset'] += 1
                with self.assertRaises(ValueError):
                    bindings.verify_objects(control, candidate, changed)
            report['runtime_components'] = []
            tc = compiler.toolchain()
            for profile in ('rtlink400', 'rtlink610'):
                bindings.require_initialized_and_indexed_contracts(report, profile, tc['linkers'][profile])
            changed = json.loads(json.dumps(report))
            changed['driver_indexed_address_contract']['cases'][0]['actual'] = 'PASS'
            with self.assertRaises(ValueError):
                bindings.require_initialized_and_indexed_contracts(changed, 'rtlink400', tc['linkers']['rtlink400'])
            changed = json.loads(json.dumps(report))
            changed['g2108_color_translation_contract']['cases'].pop()
            with self.assertRaises(ValueError):
                bindings.require_initialized_and_indexed_contracts(changed, 'rtlink610', tc['linkers']['rtlink610'])

    def test_rtlink_alias_offsets_are_explicit_hexadecimal(self):
        self.assertEqual(bindings.runtime_component_path('C:/TOOLS/runtime.lib'),
                         bindings.runtime_component_path(r'C:\\tools\\RUNTIME.lib'))
        self.assertNotEqual(bindings.runtime_component_path('C:/tools/runtime.lib'),
                            bindings.runtime_component_path('C:/other/runtime.lib'))
        self.assertEqual(bindings.rtlink_alias_delta(12), ' + 0Ch')
        self.assertEqual(bindings.rtlink_alias_delta(40), ' + 028h')
        self.assertEqual(bindings.rtlink_alias_delta(0), '')
        with self.assertRaises(ValueError):
            bindings.rtlink_alias_delta(-1)

    def test_oracle_read_guard_in_isolated_process(self):
        # The audit hook is intentionally permanent: isolate it from historical tests.
        program = (
            "import sys; from pathlib import Path; sys.path.insert(0,'tools'); "
            "import source_only_dos as d; denied=d.install_input_guard(); "
            "p=d.ROOT/'assets'/'SIMANT.EXE'; "
            "\ntry: p.read_bytes()\nexcept PermissionError: pass\n"
            "else: raise AssertionError('oracle read allowed')\n"
            "assert len(denied)==1\n"
        )
        run = subprocess.run([sys.executable, '-c', program], cwd=ROOT,
                             capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)

    def test_aliases_do_not_rewrite_literals_or_comments(self):
        source = '/* old_name */ char *s="old_name"; int old_name;'
        self.assertEqual(dos.rename_identifiers(source, {'old_name': 'new_name'}),
                         '/* old_name */ char *s="old_name"; int new_name;')

    def test_preparation_uses_registered_bodies_and_preserves_module_order(self):
        worker = ROOT / 'build/workers/source_only_dos_tests'
        worker.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=worker) as directory:
            report = {'inputs': [], 'generated_files': [], 'translation_units': [],
                      'semantic_substitutions': []}
            manifest, symbols = dos.prepare(Path(directory), report)
            self.assertEqual(len(report['translation_units']), len(manifest['modules']) + len(bindings.PROVIDER_SPECS))
            self.assertEqual(report['function_dispositions'], {
                'EXACT_C': 1244, 'GENUINE_ASM': 367, 'BEHAVIOR_EXACT_CONFIRMED': 29,
                'EXACT_AFTER_STATIC_AUDIT': 0, 'CONTRACT_EQUIVALENT': 0, 'UNRESOLVED': 0})
            self.assertEqual(report['historical_behavior_registrations'], 29)
            self.assertEqual(len(report['semantic_substitutions']), 29)
            aliases = dos.identifier_aliases(symbols)
            for row in report['translation_units']:
                original = (ROOT / row['source']['path']).read_text(encoding='latin1')
                generated = (ROOT / row['generated_source']['path']).read_text(encoding='latin1')
                if row['lang'] == 'asm':
                    if not row.get('source_binding'):
                        self.assertEqual(generated, original)
                elif row['reviewed_bodies']:
                    names_before = [aliases.get(f.name, f.name) for f in csrc.Source(original).functions()]
                    names_after = [f.name for f in csrc.Source(generated).functions()]
                    self.assertEqual(names_before, names_after, row['module'])
                    self.assertNotIn('SCAFFOLD BEGIN', generated)
            # Live/unknown data dispositions must remain visible, never emitted as bytes.
            self.assertEqual(sum(r['size'] for r in report['unresolved_data']), 113)
            self.assertTrue(any(r['classification'] == 'UNKNOWN_FIELD_SEMANTICS'
                                for r in report['unresolved_data']))

    def test_stale_registered_source_rejected(self):
        with self.assertRaisesRegex(ValueError, 'stale source/evidence pin'):
            dos.pin(ROOT / 'README.md', '0' * 64)

    def test_strict_static_gate_rejects_missing_mapping_and_unexplained_semantics(self):
        registry = json.loads((ROOT / 'evidence/behavior/manifest.json').read_text())
        index = json.loads((ROOT / 'work/source-only-dos/static-completeness/index-v1.json').read_text())
        worker = ROOT / 'build/workers/source_only_dos_tests'
        worker.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=worker) as directory:
            directory = Path(directory)
            missing = {**index, 'entries': dict(index['entries'])}
            missing['entries'].pop('DrawBalloons')
            path = directory / 'index.json'
            path.write_text(json.dumps(missing))
            with self.assertRaisesRegex(ValueError, 'does not cover'):
                dos.strict_static_reviews(registry, {'inputs': []}, path)
            original = json.loads((ROOT / index['entries']['DrawBalloons']['path']).read_text())
            for change in ('missing_axis', 'semantic_gap', 'stale_source', 'false_exact', 'unreviewed_correction'):
                receipt = json.loads(json.dumps(original))
                if change == 'missing_axis':
                    receipt['root_review']['complete_cfg'] = False
                elif change == 'semantic_gap':
                    receipt['audit']['unexplained_semantic_differences'] = ['unknown write']
                elif change == 'stale_source':
                    receipt['audit']['source']['sha256'] = '0' * 64
                elif change == 'false_exact':
                    receipt['status'] = receipt['audit']['status'] = 'EXACT'
                else:
                    receipt['root_review']['source_correction_reviewed'] = False
                altered = directory / 'receipt.json'
                altered.write_text(json.dumps(receipt))
                updated = {**index, 'entries': {**index['entries'], 'DrawBalloons': dos.pin(altered)[1]}}
                path.write_text(json.dumps(updated))
                with self.assertRaises(ValueError, msg=change):
                    dos.strict_static_reviews(registry, {'inputs': []}, path)

    def test_contract_only_static_verdict_remains_a_link_blocker(self):
        registry = json.loads((ROOT / 'evidence/behavior/manifest.json').read_text())
        index = json.loads((ROOT / 'work/source-only-dos/static-completeness/index-v1.json').read_text())
        worker = ROOT / 'build/workers/source_only_dos_tests'
        worker.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=worker) as directory:
            directory = Path(directory)
            receipt = json.loads((ROOT / index['entries']['DrawBalloons']['path']).read_text())
            receipt['status'] = receipt['audit']['status'] = 'CONTRACT_EQUIVALENT'
            path = directory / 'receipt.json'
            path.write_text(json.dumps(receipt))
            index['entries']['DrawBalloons'] = dos.pin(path)[1]
            path = directory / 'index.json'
            path.write_text(json.dumps(index))
            report = {'inputs': [], 'errors': [], 'unresolved_data': [], 'translation_units': []}
            dos.strict_static_reviews(registry, report, path)
            self.assertEqual([r['function'] for r in report['unresolved_functions']], ['DrawBalloons'])
            dos.link_units(directory, report, 'rtlink400')
            self.assertIn('independent link refused: incomplete source/data preflight', report['errors'])

    def test_reviewed_body_cannot_use_different_macro_or_type_context(self):
        original = '#define WIDTH 2\nstruct X { int a; };\nint f(int n) { return n; }'
        self.assertEqual(dos.reviewed_context(original, original, 'f')['status'], 'MATCH')
        for changed in (original.replace('WIDTH 2', 'WIDTH 4'),
                        original.replace('int a;', 'long a;'),
                        original.replace('int n)', 'long n)')):
            with self.assertRaises(ValueError):
                dos.reviewed_context(original, changed, 'f')

    def test_link_refuses_debt_before_launching_tool(self):
        report = {'errors': [], 'unresolved_functions': [], 'unresolved_data': [{'id': 'unknown'}],
                  'translation_units': []}
        dos.link_units(ROOT / 'build/workers/source_only_dos_tests/never-link', report, 'rtlink400')
        self.assertIn('independent link refused: incomplete source/data preflight', report['errors'])

    def test_link_refuses_unknown_queue_layout_with_other_gates_clear(self):
        worker = ROOT / 'build/workers/source_only_dos_tests'
        worker.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=worker) as directory:
            report = {'errors': [], 'unresolved_functions': [], 'unresolved_data': [],
                      'unresolved_symbols': [], 'duplicate_publics': {},
                      'translation_units': [], 'layout_dependencies': [
                          {'id': 'input-event-queue-fixed-pointer', 'status': 'UNRESOLVED'}]}
            dos.link_units(Path(directory), report, 'rtlink400')
            self.assertIn('independent link refused: incomplete source/data preflight', report['errors'])
            self.assertFalse((Path(directory) / 'link').exists())

    def test_binding_proof_rejects_wrong_frames_and_unrelated_instruction_changes(self):
        packet = json.loads((ROOT / 'work/source-only-dos/source-bindings-v1.json').read_text())
        binding = next(r for r in packet['bindings'] if r['module'] == 'S01:3126')
        module = json.loads((ROOT / 'layout/manifest.json').read_text())['modules'][binding['module']]
        canonical = dos.pin(ROOT / binding['source'], binding['source_sha256'])[0].decode('latin1')
        generated = bindings.apply_binding(canonical.replace('\r\n', '\n'), binding)
        def assemble(text):
            result = compiler.assemble(text, module['profile'], module['flags'], basename='CONTROL')
            self.assertTrue(result.ok, result.log)
            return OmfReader().read(result.obj)
        control = assemble(canonical)
        self.assertEqual(bindings.verify_objects(control, assemble(generated), binding)['status'], 'PASS')
        # These are separately assembled source contrasts, never patched objects.
        for contrast in (generated.replace('assume ss:DGROUP', 'assume ss:nothing'),
                         generated.replace('OFFSET DGROUP:_g_3DFC', 'OFFSET _g_3DFC'),
                         generated.replace('mov cx, 4000h', 'mov cx, 4001h')):
            self.assertTrue(contrast != generated, 'contrast did not change source')
            with self.assertRaises(ValueError):
                bindings.verify_objects(control, assemble(contrast), binding)

    def test_binding_proof_rejects_exporting_a_different_timer_word(self):
        packet = json.loads((ROOT / 'work/source-only-dos/source-bindings-v1.json').read_text())
        binding = next(r for r in packet['bindings'] if r['module'] == 'root:1B73')
        module = json.loads((ROOT / 'layout/manifest.json').read_text())['modules'][binding['module']]
        canonical = dos.pin(ROOT / binding['source'], binding['source_sha256'])[0].decode('latin1')
        generated = bindings.apply_binding(canonical.replace('\r\n', '\n'), binding)
        label = '_fd_1B73_0006 label word\n'
        contrast = generated.replace(label, '').replace('mickey_mode\tdb', label+'mickey_mode\tdb')
        def assemble(text):
            result = compiler.assemble(text, module['profile'], module['flags'], basename='TIMER')
            self.assertTrue(result.ok, result.log)
            return OmfReader().read(result.obj)
        control = assemble(canonical)
        self.assertEqual(bindings.verify_objects(control, assemble(generated), binding)['status'], 'PASS')
        with self.assertRaisesRegex(ValueError, 'exported wrong storage'):
            bindings.verify_objects(control, assemble(contrast), binding)

    def test_c_visibility_exports_preserve_full_reviewed_objects(self):
        worker = ROOT / 'build/workers/source_only_dos_tests'
        worker.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=worker) as directory:
            report = {'inputs': [], 'generated_files': [], 'translation_units': [],
                      'semantic_substitutions': []}
            dos.prepare(Path(directory), report)
            for row in report['translation_units']:
                if row['lang'] != 'c' or not row.get('source_binding'):
                    continue
                if row['source_binding'].get('communals'):
                    continue
                before = (ROOT / row['binding_control_source']['path']).read_text(encoding='latin1')
                after = (ROOT / row['generated_source']['path']).read_text(encoding='latin1')
                def compile(text):
                    result = compiler.compile_c(text, row['profile'], row['flags'], basename=row['basename'])
                    self.assertTrue(result.ok, result.log)
                    return OmfReader().read(result.obj)
                control = compile(before)
                self.assertEqual(bindings.verify_objects(control, compile(after),
                    row['source_binding'])['status'], 'PASS')
                if row['module'] == 'S12:384C':
                    contrast = after.replace('int g_2996 = 0;', 'int g_2996 = 1;')
                    self.assertTrue(contrast != after)
                    with self.assertRaisesRegex(ValueError, 'outside reviewed address operands'):
                        bindings.verify_objects(control, compile(contrast), row['source_binding'])

    def test_history_communal_contract_rejects_wrong_extent_type_initialization_and_code(self):
        worker = ROOT / 'build/workers/source_only_dos_tests'
        worker.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=worker) as directory:
            report = {'inputs': [], 'generated_files': [], 'translation_units': [],
                      'semantic_substitutions': []}
            dos.prepare(Path(directory), report)
            row = next(r for r in report['translation_units'] if r['module'] == 'S24:39C7')
            before = (ROOT / row['binding_control_source']['path']).read_text(encoding='latin1')
            after = (ROOT / row['generated_source']['path']).read_text(encoding='latin1')
            def compile(text):
                result = compiler.compile_c(text, row['profile'], row['flags'], basename=row['basename'])
                self.assertTrue(result.ok, result.log)
                return OmfReader(communals=True).read(result.obj)
            control = compile(before)
            proof = bindings.verify_objects(control, compile(after), row['source_binding'])
            self.assertEqual(proof['status'], 'PASS')
            self.assertEqual(len(proof['added_communals']), 10)
            declaration = 'int far fd_50F6_0516[64];'
            for contrast in (after.replace(declaration, 'int far fd_50F6_0516[63];'),
                             after.replace(declaration, 'long far fd_50F6_0516[64];'),
                             after.replace(declaration, 'int far fd_50F6_0516[64] = {1};'),
                             after.replace('for (i = 0; i < 64; i++)', 'for (i = 0; i < 63; i++)')):
                self.assertNotEqual(after, contrast)
                with self.assertRaises(ValueError):
                    bindings.verify_objects(control, compile(contrast), row['source_binding'])

    def test_history_storage_requires_matching_linker_and_msc_runtime(self):
        worker = ROOT / 'build/workers/source_only_dos_tests'
        worker.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=worker) as directory:
            report = {'inputs': [], 'generated_files': [], 'translation_units': [],
                      'semantic_substitutions': []}
            dos.prepare(Path(directory), report)
            tc = compiler.toolchain()
            for profile in ('rtlink400', 'rtlink610'):
                bindings.require_history_startup_contract(report, profile, tc['linkers'][profile])
            wrong = json.loads(json.dumps(report))
            wrong['runtime_components'][0]['sha256'] = '0'*64
            with self.assertRaisesRegex(ValueError, 'startup contract'):
                bindings.require_history_startup_contract(wrong, 'rtlink400', tc['linkers']['rtlink400'])

            wrong = json.loads(json.dumps(report))
            for case in wrong['history_storage_contract']['cases']:
                if case['case'] == 'crt_overlay_zero_communal':
                    case['startup'] = 'USE'
            with self.assertRaisesRegex(ValueError, 'startup contract'):
                bindings.require_history_startup_contract(wrong, 'rtlink400', tc['linkers']['rtlink400'])

    def test_scalar_owners_preserve_complete_objects_and_reject_storage_guesses(self):
        worker = ROOT / 'build/workers/source_only_dos_tests'
        worker.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=worker) as directory:
            report = {'inputs': [], 'generated_files': [], 'translation_units': [], 'semantic_substitutions': []}
            manifest, symbols = dos.prepare(Path(directory), report)
            rows = [r for r in report['translation_units'] if (r.get('source_binding') or {}).get('scalar_storage')]
            self.assertEqual({r['module'] for r in rows}, {'S08:35F5', 'S22:39C7', 'root:0BE8', 'root:0AD9'})
            self.assertEqual(sum(sum(c['length'] == 2 for c in r['source_binding']['communals']) for r in rows), 21)
            for row in rows:
                before = (ROOT / row['binding_control_source']['path']).read_text(encoding='latin1')
                after = (ROOT / row['generated_source']['path']).read_text(encoding='latin1')
                def compile(text):
                    result = compiler.compile_c(text, row['profile'], row['flags'], basename=row['basename'])
                    self.assertTrue(result.ok, result.log)
                    return OmfReader(communals=True).read(result.obj)
                control = compile(before)
                binding = row['source_binding']
                self.assertEqual(bindings.verify_objects(control, compile(after), binding)['status'], 'PASS')
                owner = binding['communals'][0]['name'][1:]
                declaration = f'int far {owner};'
                for contrast in (after.replace(declaration, f'long far {owner};'),
                                 after.replace(declaration, f'int far {owner}[2];'),
                                 after.replace(declaration, f'int far {owner} = 1;')):
                    self.assertNotEqual(after, contrast)
                    result = compiler.compile_c(contrast, row['profile'], row['flags'], basename=row['basename'])
                    if result.ok:
                        with self.assertRaises(ValueError):
                            bindings.verify_objects(control, OmfReader(communals=True).read(result.obj), binding)
                    else:
                        self.assertIn('error', result.log.lower())
                wrong = json.loads(json.dumps(binding))
                wrong['communals'][0]['historical_address'][1] += 1
                with self.assertRaises(ValueError):
                    bindings.review_addresses(wrong, manifest['modules'][row['module']], symbols)
            tc = compiler.toolchain()
            for profile in ('rtlink400', 'rtlink610'):
                bindings.require_scalar_startup_contracts(report, profile, tc['linkers'][profile])
            for key in ('health_storage_contract', 'food_cycle_storage_contract',
                        'population_storage_contract', 'lion_storage_contract',
                        'init_sim_storage_contract', 'yellow_reset_storage_contract'):
                wrong = json.loads(json.dumps(report))
                wrong[key]['cases'].pop(0)
                with self.assertRaisesRegex(ValueError, 'startup contract'):
                    bindings.require_scalar_startup_contracts(wrong, 'rtlink400', tc['linkers']['rtlink400'])
            wrong = json.loads(json.dumps(report))
            wrong['runtime_components'][0]['sha256'] = '0' * 64
            with self.assertRaisesRegex(ValueError, 'startup contract'):
                bindings.require_scalar_startup_contracts(wrong, 'rtlink400', tc['linkers']['rtlink400'])

    def test_queue_owner_rejects_extent_initializer_pointer_and_other_field_changes(self):
        worker = ROOT / 'build/workers/source_only_dos_tests'
        worker.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=worker) as directory:
            report = {'inputs': [], 'generated_files': [], 'translation_units': [], 'semantic_substitutions': []}
            dos.prepare(Path(directory), report)
            row = next(r for r in report['translation_units'] if r['module'] == 'root:1FD2')
            before = (ROOT / row['binding_control_source']['path']).read_text(encoding='latin1')
            after = (ROOT / row['generated_source']['path']).read_text(encoding='latin1')
            def compile(text):
                result = compiler.compile_c(text, row['profile'], row['flags'], basename=row['basename'])
                self.assertTrue(result.ok, result.log)
                return OmfReader(communals=True).read(result.obj)
            control = compile(before)
            proof = bindings.verify_objects(control, compile(after), row['source_binding'])
            self.assertEqual(proof['status'], 'PASS')
            self.assertTrue(proof['live_segment_extents_unchanged'])
            self.assertEqual(proof['added_communals'], [{'name': '_input_queue', 'kind': 'near', 'length': 112}])
            for contrast in (after.replace('input_queue[7]', 'input_queue[6]'),
                             after.replace('input_queue[7];', 'input_queue[7] = {{1}};'),
                             after.replace('(struct Event near *)input_queue', '(struct Event near *)(input_queue + 1)'),
                             after.replace('int g_5FF0 = 7;', 'int g_5FF0 = 6;')):
                self.assertNotEqual(after, contrast)
                with self.assertRaises(ValueError):
                    bindings.verify_objects(control, compile(contrast), row['source_binding'])
            wrong = json.loads(json.dumps(row['source_binding']))
            wrong['debug_contributions']['$$SYMBOLS']['generated'] = '0' * 64
            with self.assertRaisesRegex(ValueError, 'debug contribution or relocation'):
                bindings.verify_objects(control, compile(after), wrong)

    def test_queue_storage_requires_matching_runtime_and_frame_contrasts(self):
        worker = ROOT / 'build/workers/source_only_dos_tests'
        worker.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=worker) as directory:
            report = {'inputs': [], 'generated_files': [], 'translation_units': [], 'semantic_substitutions': []}
            dos.prepare(Path(directory), report)
            tc = compiler.toolchain()
            for profile in ('rtlink400', 'rtlink610'):
                bindings.require_queue_startup_contract(report, profile, tc['linkers'][profile])
            wrong = json.loads(json.dumps(report))
            wrong['runtime_components'][0]['sha256'] = '0' * 64
            with self.assertRaisesRegex(ValueError, 'startup contract'):
                bindings.require_queue_startup_contract(wrong, 'rtlink400', tc['linkers']['rtlink400'])
            wrong = json.loads(json.dumps(report))
            wrong['queue_storage_contract']['cases'] = [r for r in wrong['queue_storage_contract']['cases']
                                                       if r['case'] != 'data_segment_frame_contrast']
            with self.assertRaisesRegex(ValueError, 'startup contract'):
                bindings.require_queue_startup_contract(wrong, 'rtlink400', tc['linkers']['rtlink400'])
    def test_data_aliases_require_existing_bounded_source_storage(self):
        source = ("_DATA segment word public 'DATA'\npublic _owner\n"
                  "db 30 dup (0)\n_owner db 8 dup (1)\n_DATA ends\nend\n")
        result = compiler.assemble(source, 'masm510', ['/Mx'], basename='ALIAS')
        self.assertTrue(result.ok, result.log)
        obj = OmfReader().read(result.obj)
        spec = {'alias': '_view', 'owner': '_owner', 'source': 'fixture.asm',
                'source_sha256': 'a'*64, 'segment': '_DATA', 'owner_offset': 30,
                'owner_size': 8, 'offset': 2, 'view_size': 2, 'source_anchor': 'fixture'}
        module = {'source': 'fixture.asm', 'source_sha256': 'a'*64,
                  'placements': {'_DATA': {'seg': 0x55B3, 'off': 100, 'size': 38}}}
        row = {'basename': 'ALIAS', 'module': 'fixture'}
        symbols = {'data': {'view': {'seg': 0x55B3, 'off': 132}}}
        self.assertEqual(bindings.bind_data_alias(spec, obj, row, module, symbols)['offset'], 2)
        for field, wrong in (('offset', 4), ('view_size', 7), ('owner', '_missing'),
                             ('source_sha256', 'b'*64), ('owner_offset', 32)):
            with self.assertRaises(ValueError):
                bindings.bind_data_alias({**spec, field: wrong}, obj, row, module, symbols)

    def test_callback_provider_requires_one_typed_object_and_bounded_registry_views(self):
        worker = ROOT / 'build/workers/source_only_dos_tests'
        worker.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=worker) as directory:
            report = {'inputs': [], 'generated_files': [], 'translation_units': [], 'semantic_substitutions': []}
            _, symbols = dos.prepare(Path(directory), report)
            row = next(r for r in report['translation_units'] if r['module'] == 'source-owned:driver-callback-table')
            text = (ROOT / row['source']['path']).read_text(encoding='ascii')
            def compile(text):
                result = compiler.compile_c(text, row['profile'], row['flags'], basename=row['basename'])
                self.assertTrue(result.ok, result.log)
                return OmfReader(communals=True).read(result.obj)
            obj = compile(text)
            self.assertEqual(bindings.verify_provider(obj, row['storage_provider'])['status'], 'PASS')
            for contrast in (text.replace('[25]', '[24]'), text.replace('[25]', '[26]'),
                             text.replace('();', '() = {0};'), text + '\nvoid extra(void) {}\n'):
                with self.assertRaises(ValueError):
                    bindings.verify_provider(compile(contrast), row['storage_provider'])
            callback_aliases = [a for a in report['reviewed_communal_aliases'] if a['module'] == row['module']]
            self.assertEqual(len(callback_aliases), 23)
            for spec in callback_aliases:
                self.assertEqual(bindings.bind_communal_alias(spec, obj, row, symbols)['offset'], spec['offset'])
            spec = callback_aliases[0]
            for field, value in (('offset', 100), ('offset', 2), ('view_size', 2),
                                 ('source_sha256', '0' * 64), ('owner', '_other')):
                with self.assertRaises(ValueError):
                    bindings.bind_communal_alias({**spec, field: value}, obj, row, symbols)
            tc = compiler.toolchain()
            for profile in ('rtlink400', 'rtlink610'):
                bindings.require_callback_storage_contract(report, profile, tc['linkers'][profile])
            wrong = json.loads(json.dumps(report))
            wrong['callback_storage_contract']['cases'].pop(0)
            with self.assertRaisesRegex(ValueError, 'startup contract'):
                bindings.require_callback_storage_contract(wrong, 'rtlink400', tc['linkers']['rtlink400'])

    def test_assembly_frame_scope_changes_only_three_reviewed_fixups(self):
        worker = ROOT / 'build/workers/source_only_dos_tests'
        worker.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=worker) as directory:
            report = {'inputs': [], 'generated_files': [], 'translation_units': [], 'semantic_substitutions': []}
            dos.prepare(Path(directory), report)
            row = next(r for r in report['translation_units'] if r['module'] == 'root:1B73')
            before = (ROOT / row['source']['path']).read_text(encoding='latin1')
            after = (ROOT / row['generated_source']['path']).read_text(encoding='latin1')
            def assemble(text):
                result = compiler.assemble(text, row['profile'], row['flags'], basename=row['basename'])
                self.assertTrue(result.ok, result.log)
                return OmfReader(communals=True).read(result.obj)
            control = assemble(before)
            generated = assemble(after)
            proof = bindings.verify_objects(control, generated, row['source_binding'])
            self.assertEqual([s for s in proof['reviewed_frame_corrections']
                              if 'target' in s and s.get('target_kind', 'external') == 'external'],
                             row['source_binding']['reframes'])
            self.assertEqual(len(row['source_binding']['reframes']), 3)
            for contrast in (after.replace('assume es:DGROUP', 'assume es:_DATA'),
                             after.replace('mov cx, word ptr es:_g_9122', 'mov cx, word ptr es:_g_9124')):
                with self.assertRaises(ValueError):
                    bindings.verify_objects(control, assemble(contrast), row['source_binding'])
            tc = compiler.toolchain()
            for profile in ('rtlink400', 'rtlink610'):
                bindings.require_assembly_frame_contract(report, profile, tc['linkers'][profile])
            report['assembly_frame_contract']['cases'] = [r for r in report['assembly_frame_contract']['cases']
                                                         if r['case'] != 'canonical_data_frame']
            with self.assertRaisesRegex(ValueError, 'shifted DGROUP contract'):
                bindings.require_assembly_frame_contract(report, 'rtlink400', tc['linkers']['rtlink400'])

    def test_typed_near_owners_reject_extent_type_initialization_and_runtime_gaps(self):
        worker = ROOT / 'build/workers/source_only_dos_tests'
        worker.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=worker) as directory:
            report = {'inputs': [], 'generated_files': [], 'translation_units': [], 'semantic_substitutions': []}
            _, symbols = dos.prepare(Path(directory), report)
            rows = [r for r in report['translation_units'] if r['module'] in
                    ('source-owned:mouse-words', 'source-owned:memory-state')]
            self.assertEqual(sum(sum(c['length'] for c in r['storage_provider']['communals']) for r in rows), 22)
            for row in rows:
                text = (ROOT / row['source']['path']).read_text(encoding='ascii')
                provider = row['storage_provider']
                def compile(source):
                    result = compiler.compile_c(source, row['profile'], row['flags'], basename=row['basename'])
                    self.assertTrue(result.ok, result.log)
                    return OmfReader(communals=True).read(result.obj)
                bindings.review_provider_source(text, provider, symbols)
                self.assertEqual(bindings.verify_provider(compile(text), provider)['status'], 'PASS')
                if row['module'] == 'source-owned:mouse-words':
                    contrasts = [text.replace('int near g_9122;', 'char near g_9122;'),
                                 text.replace('int near g_9120;', 'int near g_9120 = 1;')]
                    wrong_type = text.replace('int near g_9122;', 'unsigned near g_9122;')
                else:
                    contrasts = [text.replace('Block far * near g_91A4;', 'Block near * near g_91A4;'),
                                 text.replace('unsigned near g_91A0;', 'unsigned near g_91A0 = 1;')]
                    wrong_type = text.replace('unsigned near g_91A0;', 'int near g_91A0;')
                with self.assertRaises(ValueError):
                    bindings.review_provider_source(wrong_type, provider, symbols)
                for contrast in contrasts + [text + '\nvoid extra(void) {}\n']:
                    with self.assertRaises(ValueError):
                        bindings.verify_provider(compile(contrast), provider)
                wrong = json.loads(json.dumps(symbols))
                name = provider['communals'][0]['name'][1:]
                wrong['data'][name]['off'] += 1
                with self.assertRaises(ValueError):
                    bindings.review_provider_source(text, provider, wrong)
            tc = compiler.toolchain()
            for profile in ('rtlink400', 'rtlink610'):
                bindings.require_near_storage_contracts(report, profile, tc['linkers'][profile])
            for key in ('mouse_storage_contract', 'memory_storage_contract'):
                wrong = json.loads(json.dumps(report))
                wrong[key]['cases'].pop(0)
                with self.assertRaisesRegex(ValueError, 'startup contract'):
                    bindings.require_near_storage_contracts(wrong, 'rtlink400', tc['linkers']['rtlink400'])
            wrong = json.loads(json.dumps(report))
            wrong['runtime_components'][0]['sha256'] = '0' * 64
            with self.assertRaisesRegex(ValueError, 'startup contract'):
                bindings.require_near_storage_contracts(wrong, 'rtlink400', tc['linkers']['rtlink400'])

    def test_driver_ss_frames_preserve_whole_modules_and_require_exact_site_sets(self):
        worker = ROOT / 'build/workers/source_only_dos_tests'
        worker.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=worker) as directory:
            report = {'inputs': [], 'generated_files': [], 'translation_units': [], 'semantic_substitutions': []}
            dos.prepare(Path(directory), report)
            rows = [r for r in report['translation_units'] if r['module'] in bindings.DRIVER_SS_SITE_HASHES]
            self.assertEqual(sum(len(r['source_binding']['reframes']) for r in rows), 128)
            for row in rows:
                before = (ROOT / row['binding_control_source']['path']).read_text(encoding='latin1')
                after = (ROOT / row['generated_source']['path']).read_text(encoding='latin1')
                def assemble(text):
                    result = compiler.assemble(text, row['profile'], row['flags'], basename=row['basename'])
                    self.assertTrue(result.ok, result.log)
                    return OmfReader(communals=True).read(result.obj)
                control, generated = assemble(before), assemble(after)
                proof = bindings.verify_objects(control, generated, row['source_binding'])
                self.assertEqual(len(proof['reviewed_frame_corrections']), len(row['source_binding']['reframes'])
                                 + len(row['source_binding'].get('local_reframes', [])))
                contrast = after.replace('assume ss:DGROUP', 'assume ss:_DATA', 1)
                self.assertNotEqual(contrast, after)
                with self.assertRaises(ValueError):
                    bindings.verify_objects(control, assemble(contrast), row['source_binding'])
                for change in ('remove', 'offset', 'target'):
                    wrong = json.loads(json.dumps(row['source_binding']))
                    if change == 'remove': wrong['reframes'].pop()
                    elif change == 'offset': wrong['reframes'][0]['offset'] += 1
                    else: wrong['reframes'][0]['target'] = '_g_9120'
                    with self.assertRaisesRegex(ValueError, 'location set'):
                        bindings.verify_objects(control, generated, wrong)
            tc = compiler.toolchain()
            for profile in ('rtlink400', 'rtlink610'):
                bindings.require_driver_ss_frame_contract(report, profile, tc['linkers'][profile])
            for change in ('case', 'site', 'runtime'):
                wrong = json.loads(json.dumps(report))
                if change == 'case': wrong['driver_ss_frame_contract']['runtime_fixture']['cases'].pop(0)
                elif change == 'site': wrong['driver_ss_frame_contract']['signed_site_tuples'][0][2] += 1
                else: wrong['runtime_components'][0]['sha256'] = '0' * 64
                with self.assertRaisesRegex(ValueError, 'shifted DGROUP contract'):
                    bindings.require_driver_ss_frame_contract(wrong, 'rtlink400', tc['linkers']['rtlink400'])

    def test_pattern_bank_owner_and_three_operands_preserve_complete_contributions(self):
        worker = ROOT / 'build/workers/source_only_dos_tests'
        worker.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=worker) as directory:
            report = {'inputs': [], 'generated_files': [], 'translation_units': [], 'semantic_substitutions': []}
            manifest, symbols = dos.prepare(Path(directory), report)
            rows = [r for r in report['translation_units'] if r['module'] in ('root:1B4E', 'S00:31AD')]
            for row in rows:
                before = (ROOT / row['binding_control_source']['path']).read_text(encoding='latin1')
                after = (ROOT / row['generated_source']['path']).read_text(encoding='latin1')
                def assemble(text):
                    result = compiler.assemble(text, row['profile'], row['flags'], basename=row['basename'])
                    self.assertTrue(result.ok, result.log)
                    return OmfReader(communals=True).read(result.obj)
                control, generated = assemble(before), assemble(after)
                proof = bindings.verify_objects(control, generated, row['source_binding'])
                if row['module'] == 'root:1B4E':
                    self.assertEqual(proof['added_exports'][0]['offset'], 0x4B0)
                    wrong = json.loads(json.dumps(row['source_binding']))
                    wrong['pattern_bank_owner']['length'] = 16
                else:
                    self.assertEqual(sorted(c['offset'] for c in proof['symbolic_operand_checks']
                                            if c['target'] == '_g_41D0'), bindings.PATTERN_BANK_SITES)
                    with self.assertRaises(ValueError):
                        bindings.verify_objects(control, assemble(after.replace('[si+_g_41D0]',
                            '[si+_g_41D0+1]', 1)), row['source_binding'])
                    wrong = json.loads(json.dumps(row['source_binding']))
                    next(s for s in wrong['relocations'] if s.get('pattern_operand'))['offsets'][0] += 1
                with self.assertRaisesRegex(ValueError, 'pattern bank'):
                    bindings.verify_objects(control, generated, wrong)
                changed = json.loads(json.dumps(symbols))
                changed['data']['g_4220']['off'] += 1
                if row['module'] == 'root:1B4E':
                    with self.assertRaisesRegex(ValueError, 'interior anchor'):
                        bindings.review_addresses(row['source_binding'], manifest['modules'][row['module']], changed)
            tc = compiler.toolchain()
            for profile in ('rtlink400', 'rtlink610'):
                bindings.require_pattern_bank_contract(report, profile, tc['linkers'][profile])
            for change in ('case', 'site', 'owner', 'runtime'):
                wrong = json.loads(json.dumps(report))
                if change == 'case': wrong['pattern_bank_contract']['cases'].pop(0)
                elif change == 'site': wrong['pattern_bank_contract']['sites'][0][1] += 1
                elif change == 'owner': wrong['pattern_bank_contract']['owner']['length'] = 16
                else: wrong['runtime_components'][0]['sha256'] = '0' * 64
                with self.assertRaisesRegex(ValueError, 'pattern bank'):
                    bindings.require_pattern_bank_contract(wrong, 'rtlink400', tc['linkers']['rtlink400'])

    def test_pattern_extension_pins_complete_previous_binding_chain(self):
        original_pin = dos.pin
        for change in ('chain', 'effective'):
            def changed_pin(path, expected=None):
                raw, identity = original_pin(path, expected)
                if path.name == 'pattern-bank-bindings-v1.json':
                    packet = json.loads(raw)
                    if change == 'chain': packet['extends_packets'].pop(0)
                    else:
                        next(b for b in packet['bindings'] if b['module'] == 'S00:31AD')[
                            'extends_effective_binding_sha256'] = '0' * 64
                    raw = json.dumps(packet).encode()
                return raw, identity
            with tempfile.TemporaryDirectory(dir=ROOT / 'build/workers/source_only_dos_tests') as directory:
                with patch.object(dos, 'pin', side_effect=changed_pin):
                    with self.assertRaisesRegex(ValueError, 'binding chain|effective control binding'):
                        dos.prepare(Path(directory), {'inputs': [], 'generated_files': [],
                            'translation_units': [], 'semantic_substitutions': []})

    def test_render_and_far_memory_providers_reject_type_extent_and_runtime_changes(self):
        worker = ROOT / 'build/workers/source_only_dos_tests'
        worker.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=worker) as directory:
            report = {'inputs': [], 'generated_files': [], 'translation_units': [], 'semantic_substitutions': []}
            _, symbols = dos.prepare(Path(directory), report)
            modules = ('source-owned:render-scalars', 'source-owned:memory-far-state')
            rows = [r for r in report['translation_units'] if r['module'] in modules]
            self.assertEqual(len(rows), 2)
            for row in rows:
                text = (ROOT / row['source']['path']).read_text(encoding='ascii')
                provider = row['storage_provider']
                def compile(source):
                    result = compiler.compile_c(source, row['profile'], row['flags'], basename=row['basename'])
                    self.assertTrue(result.ok, result.log)
                    return OmfReader(communals=True).read(result.obj)
                bindings.review_provider_source(text, provider, symbols)
                proof = bindings.verify_provider(compile(text), provider)
                self.assertEqual(proof['live_initialized_bytes'], 0)
                if row['module'] == modules[0]:
                    self.assertEqual([c['length'] for c in proof['communals']], [2, 2, 2, 1])
                    contrasts = [text.replace('unsigned char near g_94E4;', 'unsigned near g_94E4;'),
                                 text.replace('unsigned near g_9126;', 'unsigned near g_9126 = 1;')]
                    wrong_type = text.replace('unsigned char near g_94E4;', 'char near g_94E4;')
                else:
                    self.assertEqual([c['length'] for c in proof['communals']], [2, 2, 2, 4, 4])
                    contrasts = [text.replace('char far * far fd_50F6_3948;', 'char far * near fd_50F6_3948;'),
                                 text.replace('unsigned far fd_50F6_394C;', 'unsigned far fd_50F6_394C = 1;')]
                    wrong_type = text.replace('unsigned far fd_50F6_394C;', 'int far fd_50F6_394C;')
                with self.assertRaises(ValueError):
                    bindings.review_provider_source(wrong_type, provider, symbols)
                for contrast in contrasts:
                    with self.assertRaises(ValueError):
                        bindings.verify_provider(compile(contrast), provider)
                changed = json.loads(json.dumps(symbols))
                name = provider['communals'][0]['name'][1:]
                changed['data'][name]['seg'] ^= 1
                with self.assertRaises(ValueError):
                    bindings.review_provider_source(text, provider, changed)
            tc = compiler.toolchain()
            for profile in ('rtlink400', 'rtlink610'):
                bindings.require_additional_storage_contracts(report, profile, tc['linkers'][profile])
            for key in ('render_scalar_contract', 'memory_far_storage_contract'):
                wrong = json.loads(json.dumps(report))
                wrong[key]['cases'].pop(0)
                with self.assertRaisesRegex(ValueError, 'startup contract'):
                    bindings.require_additional_storage_contracts(wrong, 'rtlink400', tc['linkers']['rtlink400'])
            wrong = json.loads(json.dumps(report))
            wrong['runtime_components'][0]['sha256'] = '0' * 64
            with self.assertRaisesRegex(ValueError, 'startup contract'):
                bindings.require_additional_storage_contracts(wrong, 'rtlink400', tc['linkers']['rtlink400'])

    def test_mono_clip_and_yard_owners_guard_complete_types_aliases_and_runtime(self):
        worker = ROOT / 'build/workers/source_only_dos_tests'
        worker.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=worker) as directory:
            report = {'inputs': [], 'generated_files': [], 'translation_units': [], 'semantic_substitutions': []}
            _, symbols = dos.prepare(Path(directory), report)
            modules = ('source-owned:mono-pattern-prefix', 'source-owned:clip-pointer', 'source-owned:yard-scalars')
            rows = [r for r in report['translation_units'] if r['module'] in modules]
            self.assertEqual(len(rows), 3)
            clip_obj = clip_row = None
            for row in rows:
                text = (ROOT / row['source']['path']).read_text(encoding='ascii')
                provider = row['storage_provider']
                bindings.review_provider_source(text, provider, symbols)
                def compile(source):
                    result = compiler.compile_c(source, row['profile'], row['flags'], basename=row['basename'])
                    self.assertTrue(result.ok, result.log)
                    return OmfReader(communals=True).read(result.obj)
                obj = compile(text)
                self.assertEqual(bindings.verify_provider(obj, provider)['status'], 'PASS')
                if row['module'] == modules[0]:
                    wrong_type = text.replace('[24]', '[23]')
                    contrast = wrong_type
                elif row['module'] == modules[1]:
                    clip_obj, clip_row = obj, row
                    wrong_type = text.replace('struct Rect far * near', 'int far * near')
                    contrast = text.replace('far * near', 'near * near')
                    changed = json.loads(json.dumps(symbols))
                    changed['data']['g_5AAE']['off'] -= 2
                    with self.assertRaises(ValueError):
                        bindings.review_provider_source(text, provider, changed)
                else:
                    wrong_type = text.replace('int far MapPlane;', 'unsigned far MapPlane;')
                    contrast = text.replace('int far MapPlane;', 'int near MapPlane;')
                    self.assertEqual([c['length'] for c in provider['communals']], [2] * 8)
                with self.assertRaises(ValueError):
                    bindings.review_provider_source(wrong_type, provider, symbols)
                with self.assertRaises(ValueError):
                    bindings.verify_provider(compile(contrast), provider)
            clip_row['provider_verification'] = bindings.verify_provider(clip_obj, clip_row['storage_provider'])
            alias = next(a for a in report['reviewed_communal_aliases'] if a['alias'] == '_g_5AAE')
            self.assertEqual(bindings.bind_communal_alias(alias, clip_obj, clip_row, symbols)['offset'], 2)
            for field, value in (('offset', 0), ('view_size', 4), ('owner_size', 8), ('alias', '_g_5A9C')):
                wrong = dict(alias, **{field: value})
                with self.assertRaisesRegex(ValueError, 'communal slot view'):
                    bindings.bind_communal_alias(wrong, clip_obj, clip_row, symbols)
            tc = compiler.toolchain()
            for profile in ('rtlink400', 'rtlink610'):
                bindings.require_additional_storage_contracts(report, profile, tc['linkers'][profile])
            # The independently compiled pointer closes its four bytes only.
            report['unresolved_data'] = [{'id': 'dgroup_5a96', 'size': 25,
                'residual_ranges': [{'offset': 0, 'size': 1}, {'offset': 2, 'size': 24}]}]
            report['historical_data_debt'] = [{'id': 'dgroup_5a96', 'size': 26}]
            report['resolved_source_state'] = [{'id': 'dgroup_5a96', 'offset': 1,
                'size': 1, 'module': 'source-owned:display-mode-selector'}]
            report['layout_dependencies'] = [{'id': 'graphics-computed-copy-layout', 'status': 'UNRESOLVED'}]
            for change in ('uncompiled', 'width', 'root', 'control', 'geometry', 'residual', 'decision'):
                wrong = json.loads(json.dumps(report))
                owner = next(r for r in wrong['translation_units'] if r['module'] == modules[1])
                if change == 'uncompiled': owner.pop('provider_verification')
                elif change == 'width': owner['provider_verification']['communals'][0]['length'] = 8
                elif change == 'root': wrong['clip_pointer_contract']['root_reviewed'] = False
                elif change == 'control': wrong['clip_pointer_contract']['required_cases']['wrong_alias_plus0'] = 'PASS'
                elif change == 'geometry': wrong['clip_pointer_contract']['cases'][0]['map_alias_geometry'] = False
                elif change == 'residual': wrong['unresolved_data'][0]['residual_ranges'][1]['size'] = 20
                else: wrong['clip_pointer_data_disposition']['accepted'][0]['size'] = 8
                if change in ('uncompiled', 'width'):
                    dos.accept_clip_pointer_data(wrong)
                    self.assertEqual(wrong['unresolved_data'][0]['size'], 25)
                    self.assertEqual(len(wrong['resolved_source_state']), 1)
                else:
                    with self.assertRaises(ValueError): dos.accept_clip_pointer_data(wrong)
            dos.accept_clip_pointer_data(report)
            self.assertEqual(report['unresolved_data'], [{'id': 'dgroup_5a96', 'size': 21,
                'residual_ranges': [{'offset': 0, 'size': 1}, {'offset': 2, 'size': 20}]}])
            self.assertEqual(report['historical_data_debt'][0]['size'], 26)
            self.assertEqual(report['resolved_source_state'][1]['offset'], 22)
            self.assertEqual(report['resolved_source_state'][1]['size'], 4)
            self.assertEqual(report['layout_dependencies'][0]['status'], 'UNRESOLVED')
            dos.accept_clip_pointer_data(report)
            self.assertEqual(len(report['resolved_source_state']), 2)
            wrong = json.loads(json.dumps(report))
            wrong['resolved_source_state'][1]['offset'] = 2
            with self.assertRaises(ValueError): dos.accept_clip_pointer_data(wrong)
            for key in ('mono_pattern_prefix_contract', 'clip_pointer_contract', 'yard_scalar_contract'):
                wrong = json.loads(json.dumps(report))
                wrong[key]['cases'].pop(0)
                with self.assertRaisesRegex(ValueError, 'startup contract'):
                    bindings.require_additional_storage_contracts(wrong, 'rtlink400', tc['linkers']['rtlink400'])
            wrong = json.loads(json.dumps(report))
            next(r for r in wrong['clip_pointer_contract']['cases'] if r['expected'] == 'PASS')['map_alias_geometry'] = False
            with self.assertRaisesRegex(ValueError, 'startup contract'):
                bindings.require_additional_storage_contracts(wrong, 'rtlink400', tc['linkers']['rtlink400'])

    def test_database_index_state_is_two_scalars_without_record_table_or_error_path_claim(self):
        worker = ROOT / 'build/workers/source_only_dos_tests'
        worker.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=worker) as directory:
            report = {'inputs': [], 'generated_files': [], 'translation_units': [], 'semantic_substitutions': []}
            _, symbols = dos.prepare(Path(directory), report)
            row = next(r for r in report['translation_units'] if r['module'] == 'source-owned:database-index-state')
            text = (ROOT / row['source']['path']).read_text(encoding='ascii')
            provider = row['storage_provider']
            def compile(source):
                result = compiler.compile_c(source, row['profile'], row['flags'], basename=row['basename'])
                self.assertTrue(result.ok, result.log)
                return OmfReader(communals=True).read(result.obj)
            bindings.review_provider_source(text, provider, symbols)
            proof = bindings.verify_provider(compile(text), provider)
            self.assertEqual([c['length'] for c in proof['communals']], [4, 2])
            self.assertNotIn('fd_50F6_3958', text)
            for contrast in (text.replace('IndexEntry far * far', 'IndexEntry near * far'),
                             text.replace('int far fd_50F6_3956;', 'long far fd_50F6_3956;'),
                             text + '\nint far invented_records[248];\n'):
                with self.assertRaises(ValueError):
                    bindings.verify_provider(compile(contrast), provider)
            with self.assertRaises(ValueError):
                bindings.review_provider_source(text.replace('int far fd_50F6_3956;',
                    'unsigned far fd_50F6_3956;'), provider, symbols)
            tc = compiler.toolchain()
            for profile in ('rtlink400', 'rtlink610'):
                bindings.require_additional_storage_contracts(report, profile, tc['linkers'][profile])
            wrong = json.loads(json.dumps(report))
            wrong['database_index_state_contract']['cases'].pop(0)
            with self.assertRaisesRegex(ValueError, 'startup contract'):
                bindings.require_additional_storage_contracts(wrong, 'rtlink400', tc['linkers']['rtlink400'])

    def test_spider_counter_provider_preserves_signed_singletons_and_alias_contracts(self):
        worker = ROOT / 'build/workers/source_only_dos_tests'
        worker.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=worker) as directory:
            report = {'inputs': [], 'generated_files': [], 'translation_units': [], 'semantic_substitutions': []}
            _, symbols = dos.prepare(Path(directory), report)
            row = next(r for r in report['translation_units'] if r['module'] == 'source-owned:spider-counters')
            provider = row['storage_provider']
            text = (ROOT / row['source']['path']).read_text(encoding='ascii')
            bindings.review_provider_source(text, provider, symbols)
            def compile(source):
                result = compiler.compile_c(source, row['profile'], row['flags'], basename=row['basename'])
                self.assertTrue(result.ok, result.log)
                return OmfReader(communals=True).read(result.obj)
            self.assertEqual([c['length'] for c in bindings.verify_provider(compile(text), provider)['communals']], [2] * 7)
            with self.assertRaises(ValueError):
                bindings.review_provider_source(text.replace('int far DeathCnt;', 'unsigned far DeathCnt;'), provider, symbols)
            for contrast in (text.replace('int far EatCnt;', 'int far EatCnt[2];'),
                             text.replace('int far Scycle2;', 'int far Scycle2 = 1;')):
                with self.assertRaises(ValueError):
                    bindings.verify_provider(compile(contrast), provider)
            tc = compiler.toolchain()
            for profile in ('rtlink400', 'rtlink610'):
                bindings.require_additional_storage_contracts(report, profile, tc['linkers'][profile])
            for change in ('case', 'signedness_negative'):
                wrong = json.loads(json.dumps(report))
                contract = wrong['spider_counter_contract']
                if change == 'case': contract['cases'].pop(0)
                else: contract['required_cases']['unsigned_word_consumer_sign_contrast'] = 'PASS'
                with self.assertRaisesRegex(ValueError, 'startup contract'):
                    bindings.require_additional_storage_contracts(wrong, 'rtlink400', tc['linkers']['rtlink400'])

    def test_lion_sow_pillar_provider_has_measured_word_array_shapes_and_byte_views(self):
        worker = ROOT / 'build/workers/source_only_dos_tests'
        worker.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=worker) as directory:
            report = {'inputs': [], 'generated_files': [], 'translation_units': [], 'semantic_substitutions': []}
            _, symbols = dos.prepare(Path(directory), report)
            row = next(r for r in report['translation_units'] if r['module'] == 'source-owned:lion-sow-pillar')
            provider = row['storage_provider']
            text = (ROOT / row['source']['path']).read_text(encoding='ascii')
            bindings.review_provider_source(text, provider, symbols)
            def compile(source):
                result = compiler.compile_c(source, row['profile'], row['flags'], basename=row['basename'])
                self.assertTrue(result.ok, result.log)
                return OmfReader(communals=True).read(result.obj)
            proof = bindings.verify_provider(compile(text), provider)
            arrays = {c['name']: (c['count'], c['element_size'], c['length']) for c in proof['communals']}
            self.assertEqual(arrays['_PillarMap'], (6, 2, 12))
            self.assertEqual(arrays['_SowX'], (3, 2, 6))
            self.assertEqual(arrays['_LionListM'], (10, 1, 10))
            for contrast in (text.replace('int far SowX[3];', 'int far SowX[2];'),
                             text.replace('int far PillarMap[6];', 'unsigned char far PillarMap[12];'),
                             text.replace('int far PillDir;', 'int far PillDir = 1;')):
                with self.assertRaises(ValueError):
                    bindings.verify_provider(compile(contrast), provider)
            with self.assertRaises(ValueError):
                bindings.review_provider_source(text.replace('int far SowDir[3];',
                    'unsigned far SowDir[3];'), provider, symbols)
            tc = compiler.toolchain()
            for profile in ('rtlink400', 'rtlink610'):
                bindings.require_additional_storage_contracts(report, profile, tc['linkers'][profile])
            wrong = json.loads(json.dumps(report))
            wrong['lion_array_storage_contract']['cases'].pop(0)
            with self.assertRaisesRegex(ValueError, 'startup contract'):
                bindings.require_additional_storage_contracts(wrong, 'rtlink400', tc['linkers']['rtlink400'])

    def test_spider_controls_and_points_have_exact_types_and_persistent_views(self):
        worker = ROOT / 'build/workers/source_only_dos_tests'
        worker.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=worker) as directory:
            report = {'inputs': [], 'generated_files': [], 'translation_units': [], 'semantic_substitutions': []}
            _, symbols = dos.prepare(Path(directory), report)
            for module in ('source-owned:spider-controls', 'source-owned:point-state'):
                row = next(r for r in report['translation_units'] if r['module'] == module)
                text = (ROOT / row['source']['path']).read_text(encoding='ascii')
                provider = row['storage_provider']
                def compile(source):
                    result = compiler.compile_c(source, row['profile'], row['flags'], basename=row['basename'])
                    self.assertTrue(result.ok, result.log)
                    return OmfReader(communals=True).read(result.obj)
                bindings.review_provider_source(text, provider, symbols)
                proof = bindings.verify_provider(compile(text), provider)
                self.assertEqual(proof['code_bytes'], 0)
                self.assertEqual(proof['live_initialized_bytes'], 0)
                if module == 'source-owned:spider-controls':
                    self.assertEqual([c['length'] for c in proof['communals']], [2] * 6)
                    wrong_type = text.replace('int far Starg;', 'unsigned far Starg;')
                    wrong_extent = text.replace('int far Starg;', 'long far Starg;')
                else:
                    self.assertEqual([c['length'] for c in proof['communals']], [4] * 5)
                    # Equal four-byte COMDEF shape cannot establish signed Point fields.
                    wrong_type = text.replace('    int x;', '    unsigned x;')
                    same_shape = compile(wrong_type)
                    self.assertEqual(bindings.verify_provider(same_shape, provider)['status'], 'PASS')
                    wrong_extent = text.replace('Point far fd_50F6_0508;', 'Point far fd_50F6_0508[2];')
                    self.assertNotIn('fd_50F6_0620', text)
                with self.assertRaises(ValueError):
                    bindings.review_provider_source(wrong_type, provider, symbols)
                with self.assertRaises(ValueError):
                    bindings.verify_provider(compile(wrong_extent), provider)
                changed = json.loads(json.dumps(symbols))
                changed['data'][provider['communals'][0]['name'][1:]]['off'] += 1
                with self.assertRaises(ValueError):
                    bindings.review_provider_source(text, provider, changed)
            tc = compiler.toolchain()
            for profile in ('rtlink400', 'rtlink610'):
                bindings.require_additional_storage_contracts(report, profile, tc['linkers'][profile])
            for key in ('spider_control_contract', 'point_state_contract'):
                wrong = json.loads(json.dumps(report))
                wrong[key]['cases'].pop(0)
                with self.assertRaisesRegex(ValueError, 'startup contract'):
                    bindings.require_additional_storage_contracts(wrong, 'rtlink400', tc['linkers']['rtlink400'])

    def test_database_record_owners_preserve_overlays_and_failure_layout_gates(self):
        worker = ROOT / 'build/workers/source_only_dos_tests'
        worker.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=worker) as directory:
            report = {'inputs': [], 'generated_files': [], 'translation_units': [], 'semantic_substitutions': []}
            _, symbols = dos.prepare(Path(directory), report)
            row = next(r for r in report['translation_units'] if r['module'] == 'source-owned:database-record-state')
            provider = row['storage_provider']
            text = (ROOT / row['source']['path']).read_text(encoding='ascii')
            def compile(source):
                result = compiler.compile_c(source, row['profile'], row['flags'], basename=row['basename'])
                self.assertTrue(result.ok, result.log)
                return OmfReader(communals=True).read(result.obj)
            bindings.review_provider_source(text, provider, symbols)
            proof = bindings.verify_provider(compile(text), provider)
            self.assertEqual([(c['count'], c['element_size'], c['length']) for c in proof['communals']],
                             [(4, 124, 496), (4, 2, 8)])
            wrong_type = text.replace('IndexEntry far *index;', 'IndexEntry near *index;')
            # The byte union keeps the same object extent while the typed header moves.
            self.assertEqual(bindings.verify_provider(compile(wrong_type), provider)['status'], 'PASS')
            with self.assertRaises(ValueError):
                bindings.review_provider_source(wrong_type, provider, symbols)
            for contrast in (text.replace('fd_50F6_3958[4]', 'fd_50F6_3958[3]'),
                             text.replace('db_handles[4]', 'db_handles[5]')):
                with self.assertRaises(ValueError):
                    bindings.verify_provider(compile(contrast), provider)
            dos.audit_layout(report)
            gates = {r['id']: r for r in report['layout_dependencies']}
            for key in ('database-open-minus-one-record', 'database-handle-plus-four'):
                self.assertEqual(gates[key]['status'], 'UNRESOLVED')
            tc = compiler.toolchain()
            for profile in ('rtlink400', 'rtlink610'):
                bindings.require_additional_storage_contracts(report, profile, tc['linkers'][profile])
            wrong = json.loads(json.dumps(report))
            wrong['database_record_state_contract']['cases'].pop(0)
            with self.assertRaisesRegex(ValueError, 'startup contract'):
                bindings.require_additional_storage_contracts(wrong, 'rtlink400', tc['linkers']['rtlink400'])

    def test_clip_rect_seg_correction_preserves_offset_and_unrelated_fixups(self):
        worker = ROOT / 'build/workers/source_only_dos_tests'
        worker.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=worker) as directory:
            report = {'inputs': [], 'generated_files': [], 'translation_units': [], 'semantic_substitutions': []}
            manifest, symbols = dos.prepare(Path(directory), report)
            row = next(r for r in report['translation_units'] if r['module'] == 'root:1B73')
            binding = row['source_binding']
            before = (ROOT / row['binding_control_source']['path']).read_text(encoding='latin1')
            after = (ROOT / row['generated_source']['path']).read_text(encoding='latin1')
            def compile(source):
                result = compiler.assemble(source, row['profile'], row['flags'], basename=row['basename'])
                self.assertTrue(result.ok, result.log)
                return OmfReader(communals=True).read(result.obj)
            control, generated = compile(before), compile(after)
            proof = bindings.verify_objects(control, generated, binding)
            self.assertEqual(len(proof['reviewed_frame_corrections']), 9)
            offset = lambda o: [bindings.fixup_key(f) for f in o.linker_fixups
                               if (f['segment'], f['offset']) == ('MOUSE_TEXT', 0x139)]
            self.assertEqual(offset(control), offset(generated))
            for change in ('site', 'target', 'addend', 'remove'):
                wrong = json.loads(json.dumps(binding))
                correction = wrong['segment_corrections'][0]
                if change == 'site': correction['offset'] += 1
                elif change == 'target': correction['new']['target'] = '_g_5A9C'
                elif change == 'addend': correction['new']['encoded_addend'] = '0100'
                else: wrong['segment_corrections'].clear()
                with self.assertRaises(ValueError):
                    bindings.verify_objects(control, generated, wrong)
            with self.assertRaises(ValueError):
                bindings.verify_objects(control, compile(after.replace('mov cx, DGROUP',
                    'mov cx, seg _g_5A9C', 1)), binding)
            tc = compiler.toolchain()
            for profile in ('rtlink400', 'rtlink610'):
                bindings.require_dgroup_rect_frame_contract(report, profile, tc['linkers'][profile])
            wrong = json.loads(json.dumps(report))
            wrong['dgroup_rect_frame_contract']['cases'][0]['timed_out'] = True
            with self.assertRaisesRegex(ValueError, 'shifted DGROUP contract'):
                bindings.require_dgroup_rect_frame_contract(wrong, 'rtlink400', tc['linkers']['rtlink400'])

    def test_mouse_code_offset_frames_are_closed_and_runtime_controls_are_mandatory(self):
        worker = ROOT / 'build/workers/source_only_dos_tests'
        worker.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=worker) as directory:
            report = {'inputs': [], 'generated_files': [], 'translation_units': [], 'semantic_substitutions': []}
            manifest, symbols = dos.prepare(Path(directory), report)
            row = next(r for r in report['translation_units'] if r['module'] == 'root:1B73')
            binding = row['source_binding']
            self.assertEqual(len(binding['code_offset_reframes']), 5)
            for change in ('site', 'target', 'displacement', 'frame', 'missing'):
                wrong = json.loads(json.dumps(binding))
                spec = wrong['code_offset_reframes'][0]
                if change == 'site': spec['offset'] += 1
                elif change == 'target': spec['source_symbol'] = '_f_1B73_051F'
                elif change == 'displacement': spec['displacement'] += 1
                elif change == 'frame': spec['frame'] = 'DGROUP'
                else: wrong['code_offset_reframes'].pop()
                with self.assertRaisesRegex(ValueError, 'code-offset'):
                    bindings.review_addresses(wrong, manifest['modules'][row['module']], symbols)
            tc = compiler.toolchain()
            for profile in ('rtlink400', 'rtlink610'):
                bindings.require_mouse_code_offset_contract(report, profile, tc['linkers'][profile])
            for change in ('case', 'text', 'map', 'ordering', 'runtime'):
                wrong = json.loads(json.dumps(report))
                c = wrong['mouse_code_offset_contract']
                if change == 'case': c['cases'].pop()
                elif change == 'text': c['cases'][0]['run_log_text'] = 'PASS\r\n'
                elif change == 'map': c['cases'][0]['map_physical_frame']['prefix_span'] = 15
                elif change == 'ordering': c['source_fixup_controls']['wrong_frame_exits_before_callback_call']['only_callback_call_offset'] = 12
                else:
                    next(p for p in c['inputs'] if p['path'].lower().endswith('llibcr.lib'))['sha256'] = '0' * 64
                with self.assertRaises(ValueError):
                    bindings.require_mouse_code_offset_contract(wrong, 'rtlink400', tc['linkers']['rtlink400'])

    def test_v26_storage_types_and_shared_balloon_count_fail_closed(self):
        worker = ROOT / 'build/workers/source_only_dos_tests'
        worker.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=worker) as directory:
            report = {'inputs': [], 'generated_files': [], 'translation_units': [], 'semantic_substitutions': []}
            _, symbols = dos.prepare(Path(directory), report)
            contrasts = {
                'source-owned:remaining-ui-state': ('int far fd_50F6_1092;',
                    'unsigned far fd_50F6_1092;', 'long far fd_50F6_1092;'),
                'source-owned:remaining-window-state': ('struct Rect far fd_50F6_3842;',
                    'Handle far fd_50F6_3842;', 'struct Rect far fd_50F6_3842[2];'),
                'source-owned:remaining-scalar-tail': ('long far fd_50F6_0736;',
                    'unsigned long far fd_50F6_0736;', 'int far fd_50F6_0736;'),
                'source-owned:balloon-buffer-tables': ('int far fd_50F6_04E6[6];',
                    'unsigned far fd_50F6_04E6[6];', 'int far fd_50F6_04E6[5];'),
            }
            total = 0
            for module, (anchor, type_error, extent_error) in contrasts.items():
                row = next(r for r in report['translation_units'] if r['module'] == module)
                provider = row['storage_provider']
                text = (ROOT / row['source']['path']).read_text(encoding='ascii')
                self.assertIn(anchor, text)
                def compile(source):
                    result = compiler.compile_c(source, row['profile'], row['flags'], basename=row['basename'])
                    self.assertTrue(result.ok, result.log)
                    return OmfReader(communals=True).read(result.obj)
                bindings.review_provider_source(text, provider, symbols)
                proof = bindings.verify_provider(compile(text), provider)
                total += sum(c['length'] for c in proof['communals'])
                self.assertEqual((proof['code_bytes'], proof['live_initialized_bytes']), (0, 0))
                with self.assertRaises(ValueError):
                    bindings.review_provider_source(text.replace(anchor, type_error), provider, symbols)
                with self.assertRaises(ValueError):
                    bindings.verify_provider(compile(text.replace(anchor, extent_error)), provider)
            self.assertEqual(total, 279)
            dos.audit_layout(report)
            self.assertEqual(next(r['status'] for r in report['layout_dependencies']
                                  if r['id'] == 'map-viewport-grid-layout'), 'UNRESOLVED')
            tc = compiler.toolchain()
            for profile in ('rtlink400', 'rtlink610'):
                bindings.require_v26_storage_contracts(report, profile, tc['linkers'][profile])
            wrong = json.loads(json.dumps(report))
            wrong['translation_units'] = [r for r in wrong['translation_units']
                                         if r['module'] != 'source-owned:remaining-ui-state']
            with self.assertRaisesRegex(ValueError, 'count owner'):
                bindings.require_v26_storage_contracts(wrong, 'rtlink400', tc['linkers']['rtlink400'])
            for module, (key, _) in bindings.V26_STORAGE_CONTRACTS.items():
                wrong = json.loads(json.dumps(report))
                wrong[key]['cases'].pop()
                with self.assertRaises(ValueError):
                    bindings.require_v26_storage_contracts(wrong, 'rtlink400', tc['linkers']['rtlink400'])

    def test_v27_storage_types_extents_and_full_control_evidence_fail_closed(self):
        worker = ROOT / 'build/workers/source_only_dos_tests'
        worker.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=worker) as directory:
            report = {'inputs': [], 'generated_files': [], 'translation_units': [], 'semantic_substitutions': []}
            _, symbols = dos.prepare(Path(directory), report)
            contrasts = {
                'source-owned:remaining-sound-storage': ('int far fd_50F6_4B8E[14];',
                    'unsigned far fd_50F6_4B8E[14];', 'int far fd_50F6_4B8E[13];'),
                'source-owned:remaining-misc-storage': ('char far fd_50F6_0B0A[4];',
                    'unsigned char far fd_50F6_0B0A[4];', 'char far fd_50F6_0B0A[3];'),
                'source-owned:window-ralloc-handles': ('Handle far fd_50F6_385A;',
                    'char far * far fd_50F6_385A;', 'Handle far fd_50F6_385A[2];'),
                'source-owned:render-delay-word': ('int far fd_50F6_46D0;',
                    'unsigned far fd_50F6_46D0;', 'long far fd_50F6_46D0;'),
            }
            total = 0
            for module, (anchor, type_error, extent_error) in contrasts.items():
                row = next(r for r in report['translation_units'] if r['module'] == module)
                provider = row['storage_provider']
                text = (ROOT / row['source']['path']).read_text(encoding='ascii')
                self.assertIn(anchor, text)
                def compile(source):
                    result = compiler.compile_c(source, row['profile'], row['flags'], basename=row['basename'])
                    self.assertTrue(result.ok, result.log)
                    return OmfReader(communals=True).read(result.obj)
                bindings.review_provider_source(text, provider, symbols)
                proof = bindings.verify_provider(compile(text), provider)
                total += sum(c['length'] for c in proof['communals'])
                self.assertEqual((proof['code_bytes'], proof['live_initialized_bytes']), (0, 0))
                with self.assertRaises(ValueError):
                    bindings.review_provider_source(text.replace(anchor, type_error), provider, symbols)
                with self.assertRaises(ValueError):
                    bindings.verify_provider(compile(text.replace(anchor, extent_error)), provider)
            self.assertEqual(total, 3730)
            dos.audit_layout(report)
            self.assertEqual(next(r['status'] for r in report['layout_dependencies']
                                  if r['id'] == 'map-viewport-grid-layout'), 'UNRESOLVED')
            self.assertEqual(next(r['status'] for r in report['layout_dependencies']
                                  if r['id'] == 'menu-table-cross-owner-layout'), 'UNRESOLVED')
            tc = compiler.toolchain()
            for profile in ('rtlink400', 'rtlink610'):
                bindings.require_v27_storage_contracts(report, profile, tc['linkers'][profile])
            for module, (key, _) in bindings.V27_STORAGE_CONTRACTS.items():
                for tamper in ('case', 'omf', 'raw', 'map', 'runtime_duplicate'):
                    wrong = json.loads(json.dumps(report))
                    contract = wrong[key]
                    if tamper == 'case':
                        contract['cases'].pop()
                    elif tamper == 'omf':
                        control = next(iter(contract['compiler_controls'].values()))
                        control['communals'][0]['length'] += 2
                    elif tamper == 'raw':
                        contract['cases'][0]['raw']['hex'] += '00'
                    elif tamper == 'map':
                        case = contract['cases'][0]
                        name = next(iter(case['public_address_matrix']['Name']))
                        case['public_address_matrix']['Name'][name] = 'FFFF:FFFF'
                    else:
                        original = next(p for p in contract['inputs']
                                        if p['path'].lower().endswith('llibcr.lib'))
                        contract['inputs'].append(dict(original, sha256='0' * 64))
                    with self.assertRaises(ValueError, msg=(module, tamper)):
                        bindings.require_v27_storage_contracts(wrong, 'rtlink400', tc['linkers']['rtlink400'])

    def test_water_pair_adds_exact_array_owners_without_changing_population_or_code(self):
        worker = ROOT / 'build/workers/source_only_dos_tests'
        worker.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=worker) as directory:
            report = {'inputs': [], 'generated_files': [], 'translation_units': [], 'semantic_substitutions': []}
            manifest, symbols = dos.prepare(Path(directory), report)
            row = next(r for r in report['translation_units'] if r['module'] == 'root:0BE8')
            binding = row['source_binding']
            self.assertEqual(binding['scalar_storage'], {'families': ['population']})
            self.assertEqual(binding['array_storage'], {'families': ['water_drop']})
            self.assertEqual([c['length'] for c in binding['communals']], [2, 2, 100, 100])
            before = (ROOT / row['binding_control_source']['path']).read_text(encoding='latin1')
            after = (ROOT / row['generated_source']['path']).read_text(encoding='latin1')
            def compile(source):
                result = compiler.compile_c(source, row['profile'], row['flags'], basename=row['basename'])
                self.assertTrue(result.ok, result.log)
                return OmfReader(communals=True).read(result.obj)
            control, generated = compile(before), compile(after)
            self.assertEqual(bindings.verify_objects(control, generated, binding)['status'], 'PASS')
            for replacement in ('unsigned char far fd_50F6_0256[99];',
                                'unsigned char near fd_50F6_0256[100];'):
                contrast = after.replace('unsigned char far fd_50F6_0256[100];', replacement)
                self.assertNotEqual(contrast, after)
                with self.assertRaises(ValueError):
                    bindings.verify_objects(control, compile(contrast), binding)
            wrong = json.loads(json.dumps(binding))
            wrong['communals'][-1]['count'] = 99
            with self.assertRaises(ValueError):
                bindings.review_addresses(wrong, manifest['modules'][row['module']], symbols)
            tc = compiler.toolchain()
            for profile in ('rtlink400', 'rtlink610'):
                bindings.require_array_startup_contracts(report, profile, tc['linkers'][profile])
            wrong = json.loads(json.dumps(report))
            wrong['water_storage_contract']['element_count'] = 99
            with self.assertRaisesRegex(ValueError, 'array storage'):
                bindings.require_array_startup_contracts(wrong, 'rtlink400', tc['linkers']['rtlink400'])

    def test_local_ss_frames_guard_segment_displacements_and_linker_normalization(self):
        worker = ROOT / 'build/workers/source_only_dos_tests'
        worker.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=worker) as directory:
            report = {'inputs': [], 'generated_files': [], 'translation_units': [], 'semantic_substitutions': []}
            manifest, symbols = dos.prepare(Path(directory), report)
            rows = [r for r in report['translation_units'] if r['module'] in bindings.LOCAL_SS_SITES]
            self.assertEqual(sum(len(r['source_binding']['local_reframes']) for r in rows), 10)
            for row in rows:
                binding = row['source_binding']
                for change in ('site', 'displacement', 'kind', 'missing'):
                    wrong = json.loads(json.dumps(binding))
                    if change == 'site': wrong['local_reframes'][0]['offset'] += 1
                    elif change == 'displacement': wrong['local_reframes'][0]['displacement'] += 2
                    elif change == 'kind': wrong['local_reframes'][0]['target_kind'] = 'external'
                    else: wrong['local_reframes'].pop()
                    with self.assertRaisesRegex(ValueError, 'local assembly frame'):
                        bindings.review_addresses(wrong, manifest['modules'][row['module']], symbols)
                changed = json.loads(json.dumps(symbols))
                changed['data'][binding['local_reframes'][0]['source_symbol'][1:]]['off'] += 1
                with self.assertRaisesRegex(ValueError, 'local frame source owner'):
                    bindings.review_addresses(binding, manifest['modules'][row['module']], changed)
            tc = compiler.toolchain()
            for profile in ('rtlink400', 'rtlink610'):
                bindings.require_local_frame_contract(report, profile, tc['linkers'][profile])
            for change in ('site', 'skew', 'case', 'runtime'):
                wrong = json.loads(json.dumps(report))
                c = wrong['driver_local_frame_contract']
                if change == 'site': c['signed_site_tuples'][0][2] += 1
                elif change == 'skew': c['runtime_fixture']['cases'][0]['map']['segment_frame_skew'] = 0
                elif change == 'case': c['runtime_fixture']['cases'].pop(0)
                else: wrong['runtime_components'][0]['sha256'] = '0' * 64
                with self.assertRaisesRegex(ValueError, 'local SS frames'):
                    bindings.require_local_frame_contract(wrong, 'rtlink400', tc['linkers']['rtlink400'])


if __name__ == '__main__':
    unittest.main()
