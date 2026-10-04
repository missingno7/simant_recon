"""Final provenance joins; preserve the previous compact intake exactly."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import shutil
import sys
ROOT=Path(__file__).resolve().parents[3]
BASE=ROOT/'work/source-only-dos/structural-audits-v36'
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'tools'))
import source_only_dos as dos

def pin(p):
    if not p.is_absolute():p=ROOT/p
    b=p.read_bytes()
    return dict(path=str(p.relative_to(ROOT)).replace('\\','/') if p.is_relative_to(ROOT) else str(p),
                size=len(b),sha256=hashlib.sha256(b).hexdigest())
def write(p,d):p.write_text(json.dumps(d,indent=2)+'\n',encoding='utf-8')
report_path=ROOT/'build/source-only-dos-v36/build-report.json';report=json.loads(report_path.read_bytes())
assert len(report['translation_units'])==190
assert all(r['status'] in ('COMPILED','COMPILED_REUSED') for r in report['translation_units'])
assert len(report['unresolved_symbols'])==12
assert len(report['symbolic_aliases'])==193
assert sum(r['size'] for r in report['unresolved_data'])==44
assert sum(r['size'] for r in report['historical_data_debt'])==113
assert sum(r['status']=='UNRESOLVED' for r in report['layout_dependencies'])==10
assert report['function_dispositions']['BEHAVIOR_EXACT_CONFIRMED']==29
assert not report['standalone_dos_executable'] and not any(report['original_exe_bytes_used'].values())
denied=dos.install_input_guard()
identities={}
for row in report['inputs']+[r['object'] for r in report['translation_units']]:
    p=Path(row['path']);p=p if p.is_absolute() else ROOT/p
    key=str(p.resolve()).casefold()
    if key in identities:
        assert identities[key]['sha256']==row['sha256'];continue
    b,actual=dos.pin(p,row['sha256']);assert len(b)==row['size'];identities[key]=actual
assert denied==report['denied_oracle_reads']==[]
validation=HERE/'validate-rerun.log';log=validation.read_text(encoding='utf-8',errors='replace')
assert 'VALIDATION PASSED' in log or 'VALIDATION PASS' in log, 'full validation not yet complete'
current=ROOT/'work/source-only-dos/current-intake.json'
previous=BASE/'previous-intake.json'
if previous.exists():
    assert previous.read_bytes()==current.read_bytes(), 'previous intake recovery differs'
else:
    shutil.copyfile(current,previous)
intake=json.loads(current.read_bytes())
intake.update(full_local_report=pin(report_path),
    reproduction='python tools/source_only_dos.py --out build/source-only-dos-v36 --compile --link --reuse --linker rtlink610 --jobs 8',
    status=report['status'],errors=report['errors'],compiled_translation_units=190,
    function_dispositions=report['function_dispositions'],original_exe_bytes_used=report['original_exe_bytes_used'],
    denied_oracle_reads=report['denied_oracle_reads'],unresolved_data_disposition_bytes=44,
    unresolved_symbols=12,unresolved_symbol_categories=dict(Counter(r['required_resolution'] for r in report['unresolved_symbols'])),
    symbolic_aliases=193,duplicate_publics=report['duplicate_publics'],layout_dependencies=report['layout_dependencies'],
    resolved_source_state=report['resolved_source_state'],resolved_runtime_state_erasure=report['resolved_runtime_state_erasure'],
    storage_provider_proofs=[dict(module=r['module'],source=r['source'],object=r['object'],**r['provider_verification'])
                            for r in report['translation_units'] if r.get('storage_provider')],
    binding_proofs=[dict(module=r['module'],source=r['source'],control_source=r['source'],object=r['object'],**r['binding_verification'])
                   for r in report['translation_units'] if r.get('binding_verification')],
    tool_inputs=list({r['path']:r for r in report['inputs'] if r['path'].replace('\\','/').startswith('tools/')}.values()),
    minimum_view_admission_v36=pin(BASE/'root/minimum-views-admission.json'),
    minimum_view_verification=report['minimum_source_view_verification'],
    minimum_view_contracts=[pin(ROOT/f'work/source-only-dos/{k}-minimum-view-contract-v36.json') for k in ('window','selector')],
    startup_erasure_contract_v36=pin(ROOT/'work/source-only-dos/startup-tail-erasure-contract-v36.json'),
    structural_audits_v36=pin(BASE/'preservation-index.json'),
    historical_validation='PASS',source_only_tests='10 v36 negative-control tests PASS; full validation recorded separately',
    validation_logs=intake['validation_logs']+[pin(validation),pin(HERE/'focused-tests.log'),pin(HERE/'regression-test.log'),pin(HERE/'preflight-final-rerun.log')],
    claim_limit='Compiled source and reviewed minimum views; computed layout gates remain open. Two prior file values are erased under ordinary startup, with actual game-entry review mandatory. No complete link, game execution/comparison or human acceptance.')
research=ROOT/'work/source-only-dos/structural-audits-v37/preservation-index.json'
if research.exists():
    intake['structural_research_v37']=pin(research)
write(current,intake)
write(BASE/'context.json',dict(schema='simant-dos-source-only-context-v36',full_report=pin(report_path),
    previous_intake=pin(previous),current_intake=pin(current),compiled_TUs=190,source_providers=63,
    unresolved_imports=12,functional_data_bytes=44,historical_data_bytes=113,aliases=193,open_layout_gates=10,
    active_preflight_inputs_and_objects=list(identities.values()),guarded_reopen_denied_reads=denied,
    original_build_bytes=report['original_exe_bytes_used'],game_linked=False,game_executed=False,
    strict_behavior_confirmed=29))
for name in ('validate.log','validate-rerun.log','focused-tests.log','regression-test.log',
             'preflight-final.log','preflight-final-rerun.log','finalize_intake.py','finish_archive_v36.py'):
    target=BASE/'root'/name;assert not target.exists();shutil.copyfile(HERE/name,target)
print('Current intake refreshed; every active input/object pin reopened under source-only guard:',len(identities))
