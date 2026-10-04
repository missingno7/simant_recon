"""Package the narrow source-functional minimum views for parent review."""
import hashlib,json,sys
from pathlib import Path
sys.dont_write_bytecode=True
OUT=Path(__file__).resolve().parent; ROOT=OUT.parents[2]
sys.path.insert(0,str(ROOT/'tools'))
from omf import OmfReader
def sha(b): return hashlib.sha256(b).hexdigest()
def pin(p):
 b=p.read_bytes(); return {'path':str(p).replace('\\','/'),'size':len(b),'sha256':sha(b)}
def projection(p):
 b=p.read_bytes(); o=OmfReader(communals=True).read(b)
 fields={k:v for k,v in vars(o).items() if k!='segments'}
 fields['segments']={n:{'hex':bytes(v).hex(),'sha256':sha(bytes(v))} for n,v in o.segments.items()}
 return {'object':pin(p),'origin':'fresh MSC compilation of worker natural source; no original-object input','full_reader_projection':fields}
def main():
 src=(OUT/'sources/owner45.c').read_bytes(); p=OUT/'window-functional-provider45.c'; p.write_bytes(src)
 obj=(OUT/'sources/owner45.obj').read_bytes(); (OUT/'window-functional-provider45.obj').write_bytes(obj)
 o=OmfReader(communals=True).read(obj)
 comm=[{k:v for k,v in c.items() if k!='type_index'} for c in o.communals]
 raw=json.loads((OUT/'runtime-normalized.json').read_text())
 checks=[]
 for c in raw['cases']:
  checks.append({'profile':c['profile'],'case':c['case'],'link_diagnostics':c['link_diagnostics'],
   'run_log':c['run_log'],'map_owner_locations':c['map_owner_locations'],
   'passed_expected':c['run_log'].strip()==('FAIL_INITIAL_FAR_HOOKS' if c['case']=='nonzero-initializer'
      else 'PASS_SIGNED_WINDOW_INDEX\nPASS_45_VIEW_RESET_40_COPY_CALLBACK')})
 contract={'schema':'simant-dos-window-functional-minimum-view-proposal-v36',
  'module':'source-owned:window-initialized-views','root_reviewed':False,'admitted':False,
  'all_required_checks_pass':False,'worker_supported_checks_pass':all(c['passed_expected'] and not c['link_diagnostics'] for c in checks),
  'status':'PROPOSED_MINIMUM_FUNCTIONAL_OWNERS_WITH_MANDATORY_OPEN_LAYOUT_GATE',
  'communals':comm,'bindings':[],
  'providers':[{'module':'source-owned:window-initialized-views','basename':'WINVIEWS','owner':None,
    'profile':'msc600ax','flags':['/AL','/Os','/Gs'],'source':pin(p),'compiled_object':pin(OUT/'window-functional-provider45.obj'),
    'communals':comm}],
  'view_types':{'win_drawHooks':{'element':'void (far *)(int phase)','element_bytes':4,'count':45,
      'element_fields':{'offset':{'byte_offset':0,'width':2},'segment':{'byte_offset':2,'width':2}},
      'source_proof':'root:20E8 win_LoadAllWindows unconditional _fmemset(...,0,0xb4)',
      'escapes':['Indexed callback invocation in win_DrawWindow; no whole-table pointer escape found except _fmemset argument.']},
    'win_offsets':{'element':'struct Rect { int left,top,right,bottom; }','element_bytes':8,'count':45,
      'element_fields':{'left':{'byte_offset':0,'signed_bits':16},'top':{'byte_offset':2,'signed_bits':16},
        'right':{'byte_offset':4,'signed_bits':16},'bottom':{'byte_offset':6,'signed_bits':16}},
      'source_proof':'root:20E8 win_LoadAllWindows writes all four signed fields for i=0..44; fixed resource copy covers only0..39',
      'escapes':['Whole table pointer passed to _fmemcpy(...,320); indexed Rect values copied to/from window object0.']}},
  'unconditional_claims':['Every load-all reset requires180 hook bytes and360 Rect bytes regardless of resource counts.',
    'Natural typed arrays45 provide exactly the independently proved minimum spans with no source initializer.',
    'Consumer addressing/callback ABI and full reset/copy effects are preserved within those views.',
    'Original preloaded FarBSS and stock linked natural commons are zero before CRT; near-only CRT clear is not the justification.'],
  'bounded_compatible_domains':['Installed HCEGANT header has34 windows and all34 window records IDs0..33.',
    'Direct hook registrations use indices0,1,21,18,19,25,5.',
    'Intended lock-check admitted signed-char indices0..40 fit; Punt return does not enforce that domain.',
    'All explicit indexed formulas are in source-census.json; none imposes a new maximum or proves external call reachability.'],
  'not_claimed':['Historical maximum capacity, original owner declaration/producing TU, allocation identity/order/address.',
    'All public/dynamic window IDs are bounded, all palette/menu computed aliases are absent, all shipped alternate colors are consumed in bounds.',
    'win_colors or win_handles owner/capacity; any color-table padding, initializer or extra row.'],
  'mandatory_open_gate':{'id':'WINDOW_INDEX_RESOURCE_CROSS_OWNER_LAYOUT_V36','status':'UNRESOLVED','must_block_independent_link':True,
    'reason':'Solving minimum source owners does not make original unchecked computed-address effects safe or layout-independent.',
    'requirements':['Account for signed window index<0 or>=45 in setters, drawing, open/close/load/unlock/resize paths.',
      'Account for invalid-window Punt returning, including load handle store before lock, and high-ID getter bypasses.',
      'Validate or account for source resource count/length producers: signed numWindows, purge40 overrun and signed numColors*6 truncated to16-bit copy length.',
      'Preserve or exclude computed palette and menu reads/writes reaching hooks/Rects/Event owners.',
      'Resolve shipped window18 object3 alternate color63 selection-plus-redraw reachability or its cross-owner byte observation.',
      'If a valid-domain access beyond44 is found, extend only with new independent source/representation evidence; do not waive this gate.'],
    'specific_aliases':[
      {'expression':'win_drawHooks[45]','original_target':'win_offsets[0] left/top words','original_offset':'50F6:4892'},
      {'expression':'win_offsets[45]','original_target':'current Event fields0..3','original_offset':'50F6:49FA'},
      {'expression':'win_offsets[46]','original_target':'current Event fields4..7','original_offset':'50F6:4A02'},
      {'expression':'win_offsets[47..48]','original_target':'previous Event fields0..7','original_offset':'50F6:4A0A'},
      {'expression':'win_colors[42]','original_target':'hook0 plus first two bytes of hook1','original_offset':'50F6:47DE'},
      {'expression':'win_colors[63]','original_target':'hook31 segment word, hook32 offset word, hook32 segment word','original_offset':'50F6:485C'},
      {'expression':'fd_50F6_46BC[145] / fd_50F6_46A8[155]','original_target':'hook0 offset word','original_offset':'50F6:47DE'},
      {'expression':'fd_50F6_46BC[235] / fd_50F6_46A8[245]','original_target':'Rect0 left word','original_offset':'50F6:4892'}]},
  'controls':checks,'review_sources':[pin(OUT/n) for n in ['review-facts.json','runtime-normalized.json','source-census.json','functional-view-proposal.json']],
  'integration_instructions':['Parent independently reviews and admits a provider/contract through existing functional storage authorities.',
    'Use standalone WINVIEWS provider rather than changing canonical/generated consumer TU ownership.',
    'Keep WINDOW_INDEX_RESOURCE_CROSS_OWNER_LAYOUT_V36 mandatory and open, separate from the solved minimum storage imports.',
    'No scalar alias is exposed: bindings[] is empty; array-base names resolve to their two natural common owners.']}
 (OUT/'worker-contract.json').write_text(json.dumps(contract,indent=2),encoding='utf-8')
 paths=[OUT/'sources'/n for n in ['m20E8_baseline.obj','m20E8_extern45.obj','m20E8_extern46.obj',
   'm20E8_functional_view45.obj','m20E8_functional_view46.obj','owner45.obj','owner46.obj']]
 paths += [OUT/'runtime-sources'/n for n in ['MAIN.obj','OW40.obj','OW45.obj','OW46.obj','OWINIT.obj']]
 (OUT/'full-omf-projections.json').write_text(json.dumps({'root_reviewed':False,'admitted':False,
   'projections':[projection(p) for p in paths]},indent=2,
   default=lambda b: {'hex':bytes(b).hex()} if isinstance(b,(bytes,bytearray)) else str(b)),encoding='utf-8')
 print(json.dumps({'provider':pin(OUT/'window-functional-provider45.c'),'communals':comm,
  'worker_supported_checks_pass':contract['worker_supported_checks_pass'],'mandatory_gate':contract['mandatory_open_gate']['id']},indent=2))
if __name__=='__main__': main()
