"""Package the rejected capacity hypothesis and precise controls, without admission."""
import sys,json,hashlib
from pathlib import Path
sys.dont_write_bytecode=True
OUT=Path(__file__).resolve().parent
def pin(p):
 b=p.read_bytes();return dict(path=str(p).replace('\\','/'),size=len(b),sha256=hashlib.sha256(b).hexdigest())
census=json.loads((OUT/'source-census.json').read_text())
controls=json.loads((OUT/'full-omf-controls.json').read_text())
startup=json.loads((OUT/'startup-observation.json').read_text())
(OUT/'context-crt-startup.txt').write_text('Independent original __astart symbolic disassembly, research only.\n'+
 '\n'.join(i['linear']+'  '+i['text'] for i in startup['startup_instructions'])+'\n',encoding='utf-8')
dimensions=[c for c in controls['cases'] if c['case'] in ('extern41','extern42')]
far=[c for c in controls['cases'] if c['case']=='far_outer_negative']
assert len(dimensions)==8 and all(c['equal_complete_nondebug_code_data_publics_ordered_fixups_communals'] for c in dimensions)
assert len(far)==4 and all(not c['equal_complete_nondebug_code_data_publics_ordered_fixups_communals'] for c in far)
assert census['effective_tu_count']==190 and len(census['declarations'])==4
assert len(census['direct_touches'])==14 and not census['parser_failures']
assert not census['asm_target_mentions'] and not census['numeric_address_mentions']
assert startup['loaded_image_bytes_present']==0 and startup['all_zero_image_view'] is None
contract=dict(schema='window-handles-minimum-negative-worker-v37',root_reviewed=False,admitted=False,
 disposition='NO_SOURCE_RESET_OWNER_RECOVERED',provider_proposed=False,extent41_claimed=False,
 original_full_defining_tu_recovered=False,full_consumer_tus_compiled=4,compiler_cases=17,
 dimension_controls_equal=8,far_outer_negatives_different=4,crt_before_main_clear_independently_disassembled=True,
 meaningful_pointer_abi_words=[2,4,4,4],effective_tus=190,c_tus=161,asm_tus=29,parsed_functions=1264,
 handle_unsized_extern_declarations=4,handle_body_occurrences=10,
 baseline_warnings='root:20E8 C4113 lines12 and17 persist unchanged in each variant; other compiler logs have no warnings/errors',
 runtime_cases_executed=0,unsafe_cases_executed=0,
 mandatory_gates_preserved=['window-index-resource-cross-owner-layout','critical-selector'],
 proposed_count_changes=dict(translation_units=0,providers=0,imports=0,layout_gates=0),
 limitations=['41 is guard-derived domain cardinality only.',
  'The actual initializer clears45 cache pointers and45 depth bytes, never win_handles.',
  'CRT zero interval proves initial null representation but no producing TU/extent.',
  'Named-source census does not close unrestricted computed aliases/reachability/invalid resource domains.',
  'Returning Punt, saved selector cleanup and event decoder clobber continuation stay unresolved.'],
 writes={'scope':str(OUT).replace('\\','/'),'canonical':False,'production':False,'git':False,'promote':False,'validate':False},
 original_bytes_as_compiler_inputs=False)
(OUT/'worker-contract.json').write_text(json.dumps(contract,indent=2),encoding='utf-8')
paths=sorted(p for p in OUT.rglob('*') if p.is_file() and 'cc' not in p.relative_to(OUT).parts and p.name!='candidate-index.json')
(OUT/'candidate-index.json').write_text(json.dumps(dict(schema='window-handle-negative-packet-pins-v37',root_reviewed=False,
 admitted=False,artifacts=[pin(p) for p in paths]),indent=2),encoding='utf-8')
print(json.dumps(contract,indent=2))
