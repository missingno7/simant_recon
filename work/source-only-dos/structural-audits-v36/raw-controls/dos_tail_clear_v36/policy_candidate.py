"""Unadmitted fail-closed functional accounting draft, no production writes."""
import copy
import hashlib
from pathlib import Path

MEMBER_SHA='2e9a254b9bd00ea59884089e78e951f0e40343e11d24976f32d9582f4ded259d'

def discharge_two(report,contract):
    # Candidate tests supply a simulated reviewed flag; only root may authorize real intake.
    expected={
      'schema':'dos-tail-runtime-erasure-functional-contract-v36',
      'root_reviewed':True,'admitted':True,'functional_bytes':2,
      'historical_data_debt_modified':False,'added_storage_bytes':0,
      'new_owner_or_field_claim':False,'original_build_bytes':0,
      'member_sha256':MEMBER_SHA,'edata':0x8b9e,'end':0x94f0,
      'historical_tail_offset':0x8b9d,'historical_tail_size':3,
      'scope':'ordinary_tracked_loader_crt_dos_api',
      'prefix_after_resident_load_no_value_observation':True,
      'failure_routes_terminal_or_value_independent':True,
      'clear_dominates_initializers_and_main':True,
      'candidate_runtime_and_linker_pinned':True,
      'source_built_controls_pass':True,
    }
    if any(contract.get(k)!=v for k,v in expected.items()):
        raise ValueError('unproved or overbroad tail erasure contract')
    for item in contract['artifact_pins']+contract['source_fixture_artifact_pins']:
        b=Path(item['path']).read_bytes()
        if len(b)!=item['size'] or hashlib.sha256(b).hexdigest()!=item['sha256']:
            raise ValueError('tail evidence artifact changed')
    if not contract['artifact_pins'] or not contract['source_fixture_artifact_pins']:
        raise ValueError('unretained tail evidence')
    historical=copy.deepcopy(report['historical_data_debt'])
    if sum(r['size'] for r in historical)!=113:raise ValueError('historical ledger drift')
    tail=next(r for r in report['unresolved_data'] if r['id']=='common_tail_overlap_3')
    if tail['size']!=3 or tail.get('residual_ranges') not in (None,[{'offset':0,'size':3}]):
        raise ValueError('unexpected functional tail residual')
    result=copy.deepcopy(report)
    tail=next(r for r in result['unresolved_data'] if r['id']=='common_tail_overlap_3')
    tail.update(size=1,residual_ranges=[{'offset':0,'size':1}])
    result['resolved_runtime_state_erasure']=[dict(id='common_tail_overlap_3',offset=1,size=2,
        disposition='pre_initialization_file_values_overwritten_by_stock_crt',source_owner_claim=False)]
    assert result['historical_data_debt']==historical
    return result
