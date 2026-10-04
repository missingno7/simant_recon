"""Read-only review of the retained v37 packet; no production/build writes."""
from __future__ import annotations
import hashlib,json,sys
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[3]; OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'tools'))
from omf import OmfReader
def sha(b): return hashlib.sha256(b).hexdigest()
def read(p): return json.loads(p.read_text(encoding='utf-8'))
def model(o):
    segs={r['name'] for r in o.segment_defs if r.get('class','').upper() not in {'DEBSYM','DEBTYP'}}
    return {'segment_lengths':{n:v for n,v in o.segment_lengths.items() if n in segs},
        'segment_sha256':{n:sha(bytes(b)) for n,b in o.segments.items() if n in segs},
        'segment_defs':[r for r in o.segment_defs if r['name'] in segs],
        'publics':[r for r in o.publics if r['segment'] in segs],
        'externals':o.externals,'external_scopes':o.external_scopes,'communals':o.communals,
        'ordered_fixups':[f for f in o.linker_fixups if f['segment'] in segs]}
def main():
    audit=read(OUT/'audit-facts.json'); runtime=read(OUT/'runtime-facts.json'); proposal=read(OUT/'proposal-v37.json')
    pins={}
    def visit(value):
        if isinstance(value,dict):
            if {'path','sha256'}<=set(value) and 'size' in value: pins[(value['path'],value['sha256'])]=value
            for v in value.values(): visit(v)
        elif isinstance(value,list):
            for v in value: visit(v)
    visit(audit); visit(runtime); visit(proposal)
    for (path,digest),r in pins.items():
        p=Path(path); p=p if p.is_absolute() else ROOT/p
        b=p.read_bytes()
        assert sha(b)==digest and len(b)==r['size'],str(p)
    assert sha((ROOT/'layout/manifest.json').read_bytes())=='025a0a9255d910cae4b122ab5a3f3fb40888bb456d7fe42158db7c9e622fcf50'
    consumer={r['label']:r for r in audit['whole_consumer_controls']}
    for n in ('m208F_baseline','m208F_array_one'):
        r=consumer[n]; assert r['whole_module_check']['exact'] and r['whole_module_check']['extent']['exact']
        assert len(r['whole_module_check']['claims'])==24 and all(x['exact'] for x in r['whole_module_check']['claims'].values())
        assert [x['status'] for x in r['search']]==['EXACT','EXACT'] and r['full_nondebug_equal_baseline']
    for n in ('m208F_rawfar','m208F_near_cell','m208F_word_payload'):
        r=consumer[n]; assert not r['whole_module_check']['exact']
        assert [x['status'] for x in r['search']]==['MISMATCH','MISMATCH']
    for r in audit['whole_consumer_controls']+audit['provider_controls']:
        assert model(OmfReader(communals=True).read(Path(r['object']['path']).read_bytes()))==r['full_nondebug_model'],r['label']
    providers={r['label']:r['full_nondebug_model'] for r in audit['provider_controls']}
    owner=providers['icon-functional-provider']
    assert owner['communals']==[{'name':'_fd_50F6_46D2','kind':'far','type_index':0,'count':4,'element_size':1,'length':4}]
    assert all(v==0 for v in owner['segment_lengths'].values()) and not owner['ordered_fixups']
    assert providers['provider_typedef']==owner and providers['provider_rawfar']==owner and providers['provider_unsigned_long']==owner
    assert providers['provider_near_handle']['communals'][0]['length']==2
    assert providers['provider_two_handles']['communals'][0]['length']==8
    assert not providers['provider_explicit_zero']['communals'] and not providers['provider_explicit_zero']['ordered_fixups']
    assert providers['provider_nonzero']['ordered_fixups'][0]['target']=='_fixtureMaster'
    init=audit['static']['original_initial_state']
    assert init['common_all_zero'] and init['slot_all_zero'] and init['slot_length']==4 and not init['overlapping_relocations']
    assert len(audit['static']['current_generated_object_census'])==190 and len(audit['static']['reopened_prior_pins'])==208
    assert not audit['static']['naming']['xver_pairs_for_consumers']
    assert len(runtime['cases'])==12 and runtime['all_observations_as_expected']
    for r in runtime['cases']:
        assert r['runner_returncode']==0 and not r['link_diagnostics'] and r['observation_pass']
        expected=(['PASS_INITIAL_ZERO_4BYTE_VIEW','FAIL_POINTER_CHAIN_OR_BYTE_STRIDE'] if r['case']=='rawfar-negative'
            else ['FAIL_INITIAL_ZERO'] if r['case']=='nonzero-initializer-negative'
            else ['PASS_INITIAL_ZERO_4BYTE_VIEW','PASS_HANDLE_CELL_REPOINT_BYTE_STRIDE','PASS_TYPED_RAW_WRITE_ZERO_RESET'])
        assert r['run_log'].strip().splitlines()==expected
        if r['case']=='typed-shifted': assert r['location_changed_from_root']
        if r['case'] in ('typed-root','typed-shifted','rawfar-negative','explicit-zero-nondiscriminator'):
            assert r['mz_slot_before_crt']['zero_before_crt']
        if r['case']=='nonzero-initializer-negative':
            assert r['mz_slot_before_crt']['overlapping_relocation_word_offsets']==[2]
    assert proposal['admitted'] is False and proposal['historical_extent_admitted'] is False
    assert proposal['menu_gate']['status']=='UNRESOLVED' and proposal['computed_alias_gate']['status']=='UNRESOLVED'
    print(json.dumps({'status':'PASS','artifact_identities':len(pins),'whole_consumer_TUs':5,'provider_controls':8,
        'runtime_cases':12,'baseline_claims':24,'production_manifest_unchanged':True,'writes':0},indent=2))
if __name__=='__main__': main()
