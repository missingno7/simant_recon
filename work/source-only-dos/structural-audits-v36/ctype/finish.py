"""Consolidate and recheck the bounded CRT sequence packet without rebuilding."""
from __future__ import annotations
import argparse,hashlib,json,re,sys
from pathlib import Path
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[2]
def sha(b):return hashlib.sha256(b).hexdigest()
def pin(p):return {'path':p.relative_to(ROOT).as_posix(),'size':p.stat().st_size,'sha256':sha(p.read_bytes())}
def bits_diff(a,b):return [i-128 for i,(x,y) in enumerate(zip(a,b)) if x!=y]
def consolidate():
    cases={(plan,profile):json.loads((OUT/'links'/plan/profile/'receipt.json').read_text())
        for plan in ('sequence','shift_dgroup','wrong_data_order','shift_code_binding')
        for profile in ('rtlink400','rtlink610')}
    controls=[]
    for profile in ('rtlink400','rtlink610'):
        a=cases['sequence',profile];b=cases['shift_dgroup',profile];c=cases['wrong_data_order',profile];d=cases['shift_code_binding',profile]
        assert a['data_offsets_relative_to_ctype']['fdata.asm']==-46
        assert b['data_offsets_relative_to_ctype']['fdata.asm']==-46
        assert b['ctype_linear']-a['ctype_linear']==462
        assert a['runtime']['raw_hex']==b['runtime']['raw_hex']
        assert a['runtime']['lower_bits']==b['runtime']['lower_bits']
        assert (a['runtime']['mut_before'],a['runtime']['mut_after'])==(1,0)
        assert (b['runtime']['mut_before'],b['runtime']['mut_after'])==(1,0)
        assert (c['runtime']['mut_before'],c['runtime']['mut_after'])==(0,0)
        assert c['data_offsets_relative_to_ctype']['fdata.asm']==-16
        assert a['data_offsets_relative_to_ctype']==d['data_offsets_relative_to_ctype']
        diffs=bits_diff(a['runtime']['lower_bits'],d['runtime']['lower_bits'])
        assert diffs==[-31,-30,-27,-26,-23,-22,-19,-18,-15,-14,-11,-10]
        for v in (a,b,c,d):
            assert v['link_rc']==0 and not v['diagnostics']
            assert len(v['whole_data_verification'])==6
            assert all(x['bound_whole_data_equal'] and x['relocation_set_equal'] for x in v['whole_data_verification'])
        controls.append({'profile':profile,'positive_whole_data_order':a['data_offsets_relative_to_ctype'],
             'genuine_462_byte_dgroup_shift':b['ctype_linear']-a['ctype_linear'],
             'shift_preserves_all_127_startup_raw_bytes_and_predicates':True,
             'typed_heap_flags_DD_observation':[a['runtime']['mut_before'],a['runtime']['mut_after']],
             'wrong_order_heap_DD_observation':[c['runtime']['mut_before'],c['runtime']['mut_after']],
             'code_binding_contrast_publics':[a['public_coordinates']['__fptrap'],d['public_coordinates']['__fptrap']],
             'unchanged_data_order_changed_predicate_inputs':diffs,
             'whole_bound_data_and_relocation_set_checks':24})
    compare={}
    for plan in ('sequence','shift_dgroup','wrong_data_order','shift_code_binding'):
        a=cases[plan,'rtlink400'];b=cases[plan,'rtlink610']
        assert a['runtime']['raw_hex']==b['runtime']['raw_hex']
        assert a['runtime']['lower_bits']==b['runtime']['lower_bits']
        compare[plan]={'runtime_raw_and_predicates_equal_between_linkers':True,
                       'unrelocated_127_bytes_equal':a['prefix_unrelocated_hex']==b['prefix_unrelocated_hex']}
    summary={'schema':'simant-ctype-runtime-sequence-v36','status':'RESEARCH_SUPPORTED_RELATIVE_VIEW; NO_ADMISSION',
       'complete_clean_isolated_link_and_execution_count':8,'controls':controls,'cross_linker':compare,
       'build_ingredients':'fresh MSC600AX MAIN.C plus eight complete unmodified pinned LLIBCR OMF members, with real LLIBCR/LIBH dependency search',
       'original_usage':'research-only neighboring-byte, reference and relocation comparisons; no build construction',
       'historical_owner':'fdata.asm is strongly corroborated by independently code/public-anchored neighbors, segment identity/order and descriptor-vs-bdata flag contrast; no original direct __fheap public/fixup anchor',
       'functional_closure':'relative view is realizable; complete original memory-state equivalence for D1..DE remains unproved; full prefix has code/load-dependent pointer bytes; suffix remains separate',
       'recommended_disposition':'retain all 14 functional/historical bytes and ctype gate; preserve new exact relative-owner binding as research evidence, not a count-reducing owner-only waiver',
       'no_application_fixture_stubs':True,'no_original_bytes_in_build':True,
       'no_source_rewrite_or_canonical_edits':True,'no_object_or_image_patching':True,
       'initial_fixture_limitation':'Preserved sequence-initial emitted MUT 1 1 because same-function ctype reads were compiler-reused. Corrected main calls separately emitted lower_test, which contains the signed ctype read; all eight primary cases use its fresh object. The initial result is not an alias negative.'}
    (OUT/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    files=[p for p in sorted(OUT.rglob('*')) if p.is_file() and p.name!='packet-index.json']
    (OUT/'packet-index.json').write_text(json.dumps({'files':[pin(p) for p in files]},indent=2)+'\n')
    print('8 clean executions, 48 whole bound _DATA/relocation checks, all controls confirmed; packet files',len(files))
def recheck():
    ix=json.loads((OUT/'packet-index.json').read_text());fail=[]
    for r in ix['files']:
        p=ROOT/r['path']
        if not p.is_file() or p.stat().st_size!=r['size'] or sha(p.read_bytes())!=r['sha256']:fail.append(r['path'])
    if fail:raise SystemExit('Pin drift: '+str(fail))
    print('Packet pin recheck passed:',len(ix['files']),'files; no compiler/linker/oracle invocation')
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--recheck',action='store_true');ns=a.parse_args()
    recheck() if ns.recheck else consolidate()
