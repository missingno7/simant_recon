"""Minimum ownership cannot silently waive source layout or startup semantics."""
from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import compiler
import dos_minimum_views as views
import dos_source_bindings as bindings
import dos_startup_debt as startup
import source_only_dos as dos

def contract(kind):
    return json.loads((ROOT/f'work/source-only-dos/{kind}-minimum-view-contract-v36.json').read_bytes())

def packet(kind,name):
    return json.loads((ROOT/f'work/source-only-dos/structural-audits-v36/{kind}/{name}').read_bytes())

class MinimumViewTests(unittest.TestCase):
    def test_admitted_views_require_raw_controls_and_literal_scope(self):
        for kind,module in [('window',views.WINDOW),('selector',views.SELECTOR)]:
            original=contract(kind)
            self.assertEqual(views.require_contract(ROOT,original,module)['status'],'PASS')
            for field,value in [('computed_aliases_closed',True),('maximal_extent_claimed',True),
                                ('historical_producer_or_placement_claimed',True),('game_lifecycle_claimed',True),
                                ('original_game_bytes_used',1),('required_unresolved_gate','RESOLVED')]:
                changed=deepcopy(original);changed[field]=value
                with self.subTest(kind=kind,field=field),self.assertRaises(ValueError):
                    views.require_contract(ROOT,changed,module)

    def test_window_wider_success_does_not_prove_maximum_extent(self):
        runtime=packet('window','runtime-normalized.json')
        extraction=packet('window','loadall-extraction.json');proposal=packet('window','functional-view-proposal.json')
        for change in ['omit-negative','extra-case','change-output','change-reset']:
            r,e,p=deepcopy((runtime,extraction,proposal))
            if change=='omit-negative':r['cases']=[x for x in r['cases'] if x['case']!='nonzero-initializer']
            elif change=='extra-case':r['cases'].append(deepcopy(r['cases'][0]))
            elif change=='change-output':r['cases'][0]['run_log']='PASS\n'
            else:e['extractions'][0]['view_effects']['offset_reset_loop']='for (i=0;i<40;i++) win_offsets[i]=g_635C;'
            with self.subTest(change=change),self.assertRaises(ValueError):views.validate_window(ROOT,r,e,p)

    def test_selector_static_complete_contribution_and_shift_are_required(self):
        runtime=packet('selector','fixture-receipt-v36.json');whole=packet('selector','whole-tu-v36.json')
        for change in ['omit-width','code-mismatch','unbound','extent','unshifted','wrong-output']:
            r,w=deepcopy((runtime,whole))
            if change=='omit-width':r['runtime_cases']=[x for x in r['runtime_cases'] if x['case']!='word_width']
            elif change=='code-mismatch':w['selector_binding']['exact']=False
            elif change=='unbound':w['selector_binding']['unbound']=['unexplained']
            elif change=='extent':w['selector_binding']['candidate_extent']=55
            elif change=='unshifted':r['shifted_DGROUP_controls'][0]['shifted']['offset']=r['shifted_DGROUP_controls'][0]['base']['offset']
            else:r['runtime_cases'][0]['stdout']='SELECTOR PASS\n'
            with self.subTest(change=change),self.assertRaises(ValueError):views.validate_selector(ROOT,r,w)

    def test_provider_source_rejects_guessed_capacity_initializer_and_unsigned_byte(self):
        symbols=json.loads((ROOT/'layout/symbols.json').read_bytes())
        for kind in ('window','selector'):
            binding=json.loads((ROOT/f'work/source-only-dos/{kind}-minimum-view-bindings-v36.json').read_bytes())
            provider=binding['providers'][0];source=(ROOT/provider['source']['path']).read_text()
            bindings.review_provider_source(source,provider,symbols)
            changes=[source.replace('[45]','[46]'),source.replace('[45]','[40]')] if kind=='window' else [
                source.replace('char near','unsigned char near'),source.replace('g_8CCB;','g_8CCB = 0;')]
            for changed in changes:
                with self.assertRaises(ValueError):bindings.review_provider_source(changed,provider,symbols)

    def test_each_new_gate_blocks_link_even_with_storage_and_other_gates_clear(self):
        report={'translation_units':[]};dos.audit_layout(report)
        for name in views.GATES.values():
            gate=next(r for r in report['layout_dependencies'] if r['id']==name)
            isolated=dict(errors=[],translation_units=[],unresolved_functions=[],unresolved_data=[],
                          unresolved_symbols=[],duplicate_publics={},layout_dependencies=[gate])
            with tempfile.TemporaryDirectory(dir=ROOT/'build') as directory:
                with patch.object(compiler,'toolchain',side_effect=AssertionError('linker must not run')):
                    dos.link_units(Path(directory),isolated,'rtlink400')
                self.assertIn('independent link refused: incomplete source/data preflight',isolated['errors'])

    def test_resolving_gate_requires_a_separate_integration_receipt(self):
        libraries=json.loads((ROOT/'layout/manifest.json').read_bytes())['runtime']['libraries']
        report=dict(translation_units=[dict(module=views.WINDOW,lang='c'),dict(module=views.SELECTOR,lang='c')],
                    runtime_components=list(libraries.values()),window_minimum_view_contract=contract('window'),
                    selector_minimum_view_contract=contract('selector'))
        dos.audit_layout(report)
        tool=compiler.toolchain()['linkers']['rtlink400']
        views.require_all(ROOT,report,'rtlink400',tool)
        gate=next(r for r in report['layout_dependencies'] if r['id']==views.GATES[views.WINDOW])
        gate['status']='RESOLVED'
        with self.assertRaisesRegex(ValueError,'silently waived'):
            views.require_all(ROOT,report,'rtlink400',tool)

class StartupErasureTests(unittest.TestCase):
    def setUp(self):
        self.contract=json.loads((ROOT/'work/source-only-dos/startup-tail-erasure-contract-v36.json').read_bytes())
        self.historical=json.loads((ROOT/'work/takeover/behavioral-oracle/data-debt-disposition-approved-v1.json').read_bytes())['spans']

    def test_two_values_only_and_historical_ledger_are_retained(self):
        historical=[{k:r[k] for k in ('id','classification','size','semantic_assessment')} for r in self.historical]
        report=dict(startup_tail_erasure_contract=self.contract,historical_data_debt=deepcopy(historical),
                    unresolved_data=deepcopy(historical))
        startup.apply(ROOT,report);startup.apply(ROOT,report)
        self.assertEqual(report['historical_data_debt'],historical)
        self.assertEqual(sum(r['size'] for r in historical),113)
        tail=next(r for r in report['unresolved_data'] if r['id']=='common_tail_overlap_3')
        self.assertEqual((tail['size'],tail['residual_ranges']),(1,[dict(offset=0,size=1)]))
        self.assertFalse(report['resolved_runtime_state_erasure'][0]['source_owner_claim'])

    def test_overbroad_erasure_environment_or_game_claim_rejected(self):
        for field,value in [('scope','arbitrary_observer'),('disposition',dict(id='common_tail_overlap_3',offset=0,size=3)),
                            ('historical_data_debt_modified',True),('added_storage_bytes',2),
                            ('new_owner_or_field_claim',True),('actual_game_entry_review_required',False),
                            ('game_link_or_execution_claimed',True),('root_reviewed',False)]:
            c=deepcopy(self.contract);c[field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):startup.require_contract(ROOT,c)

    def test_observer_terminal_seed_and_complete_main_contrasts_are_required(self):
        vm=packet('tail','stock-crt-controls.json');full=packet('tail','full-dos-execution.json')
        for change in ['omit-observer','observe-first-byte','erase-seed','missing-main','DOS1-returns']:
            v,f=deepcopy((vm,full))
            if change=='omit-observer':v['runs']=[r for r in v['runs'] if not r['injected_external_observer']]
            elif change=='observe-first-byte':v['runs'][0]['boundary_final']='000000'
            elif change=='erase-seed':next(r for r in v['runs'] if r['name']=='file_seed')['probe_final']='0000'
            elif change=='missing-main':f['cases'].pop()
            else:next(r for r in v['runs'] if r['dos_version']==1)['terminated']=False
            with self.subTest(change=change),self.assertRaises(ValueError):startup.validate_runs(v,f)

    def test_fixture_startup_cannot_claim_actual_game_startup(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'build') as directory:
            self.assertFalse(startup.require_linked_game_review(Path(directory),{},dict(path='SOURCE.EXE'), 'rtlink400'))

if __name__=='__main__':unittest.main()
