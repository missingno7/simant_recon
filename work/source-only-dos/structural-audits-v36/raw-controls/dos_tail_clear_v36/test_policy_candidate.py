"""Targeted accounting tests; simulated root admission is test-local only."""
import copy
import json
import unittest
from pathlib import Path
from policy_candidate import discharge_two

OUT=Path(__file__).resolve().parent
class PolicyTests(unittest.TestCase):
    def setUp(self):
        self.contract=json.loads((OUT/'functional-tail-candidate.json').read_bytes())
        self.contract.update(root_reviewed=True,admitted=True)
        self.report=dict(unresolved_data=[dict(id='other',size=43),dict(id='common_tail_overlap_3',size=3)],
            historical_data_debt=[dict(id='other',size=110),dict(id='common_tail_overlap_3',size=3)])
    def test_positive_exactly_two(self):
        got=discharge_two(self.report,self.contract)
        self.assertEqual(sum(r['size'] for r in got['unresolved_data']),44)
        self.assertEqual(got['unresolved_data'][1]['residual_ranges'],[dict(offset=0,size=1)])
        self.assertEqual(got['historical_data_debt'],self.report['historical_data_debt'])
        self.assertEqual(self.report['unresolved_data'][1]['size'],3)
    def test_negative_every_required_condition(self):
        mutations=dict(root_reviewed=False,admitted=False,functional_bytes=3,
            historical_data_debt_modified=True,added_storage_bytes=2,new_owner_or_field_claim=True,
            original_build_bytes=1,member_sha256='bad',edata=0x8b9d,end=0x8b9f,
            historical_tail_offset=0x8b9e,historical_tail_size=2,scope='arbitrary_external_observers',
            prefix_after_resident_load_no_value_observation=False,failure_routes_terminal_or_value_independent=False,
            clear_dominates_initializers_and_main=False,candidate_runtime_and_linker_pinned=False,
            source_built_controls_pass=False)
        for key,val in mutations.items():
            with self.subTest(key=key):
                bad=copy.deepcopy(self.contract);bad[key]=val
                with self.assertRaises(ValueError):discharge_two(self.report,bad)
    def test_negative_pin(self):
        bad=copy.deepcopy(self.contract);bad['artifact_pins'][0]['sha256']='00'*32
        with self.assertRaises(ValueError):discharge_two(self.report,bad)
    def test_negative_missing_pins(self):
        bad=copy.deepcopy(self.contract);bad['artifact_pins']=[]
        with self.assertRaises(ValueError):discharge_two(self.report,bad)
    def test_negative_fixture_pin(self):
        bad=copy.deepcopy(self.contract);bad['source_fixture_artifact_pins'][0]['sha256']='00'*32
        with self.assertRaises(ValueError):discharge_two(self.report,bad)
    def test_negative_inventory_drift(self):
        for field in ('unresolved_data','historical_data_debt'):
            bad=copy.deepcopy(self.report);bad[field][1]['size']-=1
            with self.assertRaises(ValueError):discharge_two(bad,self.contract)

if __name__=='__main__':unittest.main(verbosity=2)
