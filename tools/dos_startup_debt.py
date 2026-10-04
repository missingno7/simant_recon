"""Bounded erasure of prior file values, without inventing a storage owner."""
import json
from pathlib import Path

from dos_minimum_views import load_pin, need, path_key, read_pin
from omf import OmfReader

MEMBER_SHA = '2e9a254b9bd00ea59884089e78e951f0e40343e11d24976f32d9582f4ded259d'
DISPOSITION = dict(id='common_tail_overlap_3',offset=1,size=2)

def validate_runs(vm, full):
    need(vm['controls_pass'] is True and vm['original_executable_build_bytes']==0
         and vm['denied_original_reads']==[], 'startup erasure fixture provenance changed')
    rows=vm['runs']; seen=set()
    for row in rows:
        key=(row['linker'],row['name'],row['poison'],row['dos_version'],row['injected_external_observer'])
        need(key not in seen,'duplicate startup erasure control');seen.add(key)
        need(row['genuine_whole_stock_crt_member'] is True and row['pre_clear_target_reads']==[],
             'startup prefix observation/member changed')
        poison=f"{row['poison']:02x}"
        if row['dos_version']==1:
            need(row['events']==['dos1-transfer-to-psp-zero'] and row['terminated'] is True
                 and row['boundary_final']==poison*3 and row['probe_final']==poison*2,
                 'DOS1 terminal-before-clear contrast changed')
        else:
            need(row['events']==['clear-complete','qczrinit-after-clear','first-environment-call-after-clear']
                 and row['terminated'] is False,'startup clear dominance controls changed')
            if row['name']=='file_seed':
                need(row['edata']==row['end'] and row['boundary_final']==poison*3
                     and row['probe_final']=='3157', 'initialized seed/empty-clear contrast changed')
            else:
                need(row['edata']<row['end'] and row['boundary_final']==poison+'0000'
                     and row['probe_final']=='0000','first-byte retention/two-byte erasure changed')
            observers=[poison*2] if row['injected_external_observer'] else []
            need(row['observer_output']==observers,'pre-clear observer contrast changed')
    ordinary={(p,n,b,5,False) for p in ('rtlink400','rtlink610')
              for n in ('bss_two','bss_shift','file_seed') for b in (0xA5,0x5A)}
    terminal={(p,'bss_two',0xC7,1,False) for p in ('rtlink400','rtlink610')}
    observer={(p,'bss_two',b,5,True) for p in ('rtlink400','rtlink610') for b in (0xA5,0x5A)}
    need(len(rows)==18 and seen==ordinary|terminal|observer,'startup erasure control matrix incomplete')
    outcomes={(p,n,v) for p in ('rtlink400','rtlink610')
              for n,v in [('bss_two',0),('bss_shift',111),('file_seed',136)]}
    need(full['original_build_bytes']==0 and full['denied_original_reads']==[] and len(full['cases'])==6
         and {(r['linker'],r['case'],r['expected_main_return']) for r in full['cases']}==outcomes
         and all(r['result']=='PASS' for r in full['cases']),'full stock CRT/main execution controls changed')

def require_contract(root, contract, components=()):
    literals=dict(schema='simant-dos-bounded-startup-erasure-v36',root_reviewed=True,admitted=True,
        scope='ordinary_tracked_loader_crt_dos_api',disposition=DISPOSITION,residual=[dict(offset=0,size=1)],
        historical_ledger_bytes=113,historical_data_debt_modified=False,new_owner_or_field_claim=False,
        added_storage_bytes=0,original_build_bytes=0,member_sha256=MEMBER_SHA,
        actual_game_entry_review_required=True,game_link_or_execution_claimed=False)
    need(all(contract.get(k)==v for k,v in literals.items()),'bounded startup-erasure admission/scope changed')
    need(contract.get('control_pins') and contract.get('inputs'),'startup erasure evidence missing')
    for row in contract['control_pins']:read_pin(root,row)
    identities={path_key(r['path']):r['sha256'] for r in contract['inputs']}
    need(all(identities.get(path_key(p))==digest for p,digest in components),
         'startup erasure selected runtime/linker identities changed')
    packets={name:load_pin(root,row) for name,row in contract['receipts'].items()}
    prefix=packets['pre-clear-prefix-review.json']; review=packets['independent-review.json']
    need(prefix['runtime_members_reopened']==90 and prefix['stock_crt_member_sha256']==MEMBER_SHA
         and prefix['resident_section_flags']==0x100 and prefix['resident_section_tail_relocation_overlap']==[]
         and prefix['crt_clear']==dict(start=0x8B9E,end=0x94F0,count=0x952)
         and prefix['post_load_callback']=='2CFF:01B0 NOP; RETF'
         and prefix['crt_actual_stack_check_carry'] is False,'original startup-boundary proof changed')
    need(review['verdict']=='SUPPORTED' and review['functional_disposition_supported']==DISPOSITION
         and review['functional_residual_required']==dict(id='common_tail_overlap_3',offset=0,size=1)
         and review['historical_ledger_required_bytes']==113
         and review['independent_game_link_or_execution_proven'] is False,
         'independent startup review scope changed')
    validate_runs(packets['stock-crt-controls.json'],packets['full-dos-execution.json'])
    # Reopen the genuine whole member, not code lifted from the historical image.
    libraries=[r for r in contract['inputs'] if Path(r['path']).name.casefold()=='llibcr.lib']
    need(len(libraries)==1,'startup library identity missing/duplicated')
    import hashlib
    member=next(blob for name,blob in OmfReader().split_library(read_pin(root,libraries[0]))
                if name.casefold()=='dos\\crt0.asm')
    need(hashlib.sha256(member).hexdigest()==MEMBER_SHA,'whole stock CRT member changed')

def apply(root, report):
    contract=report['startup_tail_erasure_contract']
    require_contract(root,contract)
    historical=report['historical_data_debt']
    tail=[r for r in historical if r['id']=='common_tail_overlap_3']
    need(sum(r['size'] for r in historical)==113 and len(tail)==1 and tail[0]['size']==3,
         'historical debt ledger changed')
    spans=[r for r in report['unresolved_data'] if r['id']=='common_tail_overlap_3']
    need(len(spans)==1,'functional tail inventory changed')
    span=spans[0]
    resolution=dict(**DISPOSITION,disposition='prior_file_values_overwritten_before_initializers_or_main',
                    source_owner_claim=False,actual_game_entry_review='PENDING_ACTUAL_GAME_IMAGE')
    previous=report.get('resolved_runtime_state_erasure',[])
    if previous:
        need(previous==[resolution] and span['size']==1 and span['residual_ranges']==[dict(offset=0,size=1)],
             'recorded startup erasure inventory changed')
        return
    need(span['size']==3 and span.get('residual_ranges') in (None,[dict(offset=0,size=3)]),
         'functional tail residual changed')
    span.update(size=1,residual_ranges=[dict(offset=0,size=1)])
    report['resolved_runtime_state_erasure']=[resolution]

def require_linked_game_review(root, report, image_pin, profile):
    """A linked candidate cannot claim complete intake using fixture entry proof.

    The first actual game link creates the reviewable image. A separately
    reviewed receipt must then bind its concrete manager/CRT prefix and all
    pre-clear paths before standalone success can be reported.
    """
    path=root/'work/source-only-dos/startup-tail-linked-game-review-v1.json'
    if not path.exists():
        return False
    raw=path.read_bytes()
    review=json.loads(raw)
    expected=dict(root_reviewed=True,all_required_checks_pass=True,linker=profile,
        executable=image_pin,member_sha256=MEMBER_SHA,scope='ordinary_tracked_loader_crt_dos_api',
        actual_manager_crt_chain_reviewed=True,whole_crt_fixups_and_relocations_bound=True,
        natural_clear_bounds_verified=True,pre_clear_stack_and_descriptor_accesses_verified=True,
        all_pre_clear_load_relocation_callback_paths_reviewed=True,
        all_pre_clear_failure_routes_terminal_or_value_independent=True,
        clear_dominates_all_initializers_and_main=True,arbitrary_observer_or_entry_override=False)
    need(all(review.get(k)==v for k,v in expected.items()) and review.get('evidence_pins'),
         'actual game startup-erasure review incomplete/stale')
    for row in review['evidence_pins']:read_pin(root,row)
    import hashlib
    report.setdefault('inputs',[]).append(dict(path=str(path.relative_to(root)),
        size=len(raw),sha256=hashlib.sha256(raw).hexdigest()))
    report['inputs'] += review['evidence_pins']
    report['linked_startup_erasure_review']=dict(status='PASS',executable=image_pin)
    return True
