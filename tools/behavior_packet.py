"""Archive a completed family run and an explicit supervisor contract review.

This packages evidence; it cannot accept a claim. The separate validation and
registration tools must subsequently verify the packet. No historical files
are modified.
"""
import argparse
import gzip
import json
import shutil
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import behavior_validate as bv


def dump(path,data):
    path.write_text(json.dumps(data,indent=2)+'\n',encoding='utf8')


def pin(path):
    return {'path':path.relative_to(ROOT).as_posix(),'sha256':bv.sha256_file(path)}


def harness_pins(review,identity):
    snapshot=review.get('harness_snapshot')
    base=ROOT/'evidence/behavior/harnesses'/snapshot if snapshot else ROOT
    runner=pin(base/bv.RUNNER)
    if runner['sha256']!=identity['harness_sha256']:
        raise ValueError('selected runner was not the executed runner')
    components={rel:pin(base/rel) for rel in bv.HARNESS_COMPONENTS}
    result={'runner':runner,'components':components}
    if snapshot:
        approval=review['harness_snapshot_review']
        if approval.get('status')!='APPROVED':raise ValueError('snapshot requires explicit supervisor review')
        result['runner_snapshot_review']={**approval,'runner_snapshot_reviewed':True,
            'archived_components':[{'component':rel,**record} for rel,record in components.items()]}
    return result


def package(raw_path,review_path,destination=None):
    raw_path=raw_path.resolve(); review_path=review_path.resolve()
    raw=json.loads(raw_path.read_text()); review=json.loads(review_path.read_text())
    standard=raw.get('schema')=='behavior-run-evidence-v1'
    identity=raw['identity']; function=identity['function'] if standard else raw['function']
    if function!=review['function']: raise ValueError('review names another function')
    if raw.get('errors')!=0 or raw.get('mismatches')!=0: raise ValueError('run contains failures')
    if not standard and not raw.get('negative_control',{}).get('detected'): raise ValueError('negative control absent')
    suite=ROOT/review['suite']
    source=ROOT/(review['source'] if standard else identity['source'])
    if bv.sha256_file(source)!=identity['source_sha256']: raise ValueError('source changed after run')
    suite_hash=identity['suite_sha256'] if standard else raw['suite_sha256']
    if bv.sha256_file(suite)!=suite_hash: raise ValueError('suite changed after run')
    out=(ROOT/destination).resolve() if destination else ROOT/'evidence/behavior/functions'/function
    out.relative_to((ROOT/'evidence/behavior/functions'/function).resolve())
    if out.exists(): raise ValueError('packet destination already exists; never overwrite proof')
    out.mkdir(parents=True)
    shutil.copyfile(source,out/'module.c');shutil.copyfile(raw_path,out/'raw-run.json')
    shutil.copyfile(review_path,out/'contract-review.json')
    artifacts=[]
    for record in review.get('artifacts',[]):
        original=ROOT/record['path'];target=out/'supplemental'/record['name']
        target.resolve().relative_to((out/'supplemental').resolve())
        target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(original,target)
        artifacts.append({'original_path':record['path'],**pin(target)})
    if artifacts:dump(out/'supplemental-artifacts.json',artifacts)
    original_ledger=raw['case_ledger']; ledger_path=Path(original_ledger['path'])
    if not ledger_path.is_absolute():
        ledger_path=(ROOT/ledger_path) if (ROOT/ledger_path).is_file() else raw_path.parent/ledger_path
    if bv.sha256_file(ledger_path)!=original_ledger['sha256']: raise ValueError('ledger hash changed')
    shutil.copyfile(ledger_path,out/'cases.jsonl.gz')
    ledger={**original_ledger,**pin(out/'cases.jsonl.gz')}
    if standard:
        return package_standard(raw,review,identity,out,suite,suite_hash,ledger)
    negative_source=raw_path.parent/'negative.c'
    negative_object=raw_path.parent/'negative/candidate.obj'
    shutil.copyfile(negative_source,out/'negative.c')
    shutil.copyfile(negative_object,out/'negative.obj')
    negative_id='source-mutation'
    negative={'schema':'behavior-negative-controls-v1','function':function,'suite_id':review['suite_id'],'identity':{
        k:identity[k] for k in ('source_sha256','harness_sha256','oracle_sha256')},
        'errors':0,'mismatches_detected':1,'controls':[{
            'id':negative_id,'executed':True,'detected_mismatch':True,
            'original_executed':True,'mutant_executed':True,'baseline_matches':True,
            'mutant_differs':True,'execution_errors':0,
            'mutant_source_sha256':bv.sha256_file(negative_source),
            'mutant_source':pin(out/'negative.c'),'mutant_object':pin(out/'negative.obj'),
            'mismatch_categories':list(raw['negative_control']['diff']),
            'difference':raw['negative_control']['diff']} ]}
    negative['identity']['suite_sha256']=raw['suite_sha256']
    negative['identity']['historical_manifest_sha256']=identity['manifest_sha256']
    dump(out/'negative-controls.json',negative)
    ident={**identity,'suite_id':review['suite_id'],'module':review['module'],
           'suite_sha256':raw['suite_sha256'],
           'historical_manifest_sha256':identity['manifest_sha256']}
    report={'schema':'behavior-run-evidence-v1','completion':'COMPLETE','identity':ident,
        'execution':{'engine':'PreparedPair.compare','actual_original_execution':True,
            'actual_candidate_execution':True,'original_exe_sha256':identity['oracle_sha256']},
        'cases':{lane:{'generated':raw[lane],'executed':raw[lane],
            'actual_original_invocations':raw[lane],'actual_candidate_invocations':raw[lane],
            'seeds':[raw['seed']] if lane=='randomized' else []} for lane in ('directed','randomized')},
        'errors':0,'mismatches':0,'compared_effects':raw['compared'],
        'case_ledger':ledger,'unmodeled_boundaries':0,'peer_data_gates':'PASS',
        'positive_controls':review['positive_controls'],
        'helper_boundaries':review['helper_boundaries'],
        'raw_report':pin(out/'raw-run.json')}
    dump(out/'run.json',report)
    evidence={'schema':'simant-behavior-evidence-v1','function':function,'status':'BEHAVIOR_EXACT',
        'source':{**pin(out/'module.c'),'whole_module':True,'module':review['module']},
        'suite':{**pin(suite),'id':review['suite_id']},
        'harness':harness_pins(review,identity),
        'oracle':{**pin(ROOT/'assets/SIMANT.EXE'),'lock_sha256':bv.sha256_file(ROOT/bv.ORACLE_LOCK)},
        'historical_manifest_sha256':identity['manifest_sha256'],
        'checkpoint':review['checkpoint'],'contract':review['contract'],
        'run_report':pin(out/'run.json'),'negative_controls':pin(out/'negative-controls.json'),
        'historical_difference':review['historical_difference'],
        'semantic_evidence':review['semantic_evidence'],'evidence_date':review['date'],
        'review_record':pin(out/'contract-review.json')}
    dump(out/'evidence.json',evidence)
    return out/'evidence.json'


def package_standard(raw,review,identity,out,suite,suite_hash,ledger):
    """Retain normalized worker evidence without inventing execution counts."""
    negative_path=ROOT/review['negative_controls']
    negative=json.loads(negative_path.read_text())
    if negative.get('errors')!=0 or not negative.get('mismatches_detected'):
        raise ValueError('successful executed source mutants are required')
    shutil.copyfile(negative_path,out/'raw-negative-controls.json')
    for index,control in enumerate(negative['controls']):
        for field,suffix in [('mutant_source','.c'),('mutant_object','.obj')]:
            artifact=control[field]; origin=ROOT/artifact['path']
            if bv.sha256_file(origin)!=artifact['sha256']: raise ValueError('negative artifact changed')
            target=out/f'negative-{index}{suffix}';shutil.copyfile(origin,target)
            control[field]=pin(target)
    dump(out/'negative-controls.json',negative)
    # Positive-control identity and observations must be anchored to a row that
    # the VM actually emitted.  The review may identify the intended case, but
    # it cannot supply replacement hashes or execution claims.
    rows={}
    ledger_copy=out/'cases.jsonl.gz'
    with gzip.open(ledger_copy,'rt',encoding='utf-8') as stream:
        for line in stream:
            row=json.loads(line)
            rows[row.get('case_id')]=row
    positives=review.get('positive_controls')
    if not isinstance(positives,list) or not positives:
        raise ValueError('standard evidence needs ledger-backed positive controls')
    ledger_identity=ledger['identity']
    for control in positives:
        row=rows.get(control.get('case_id'))
        if row is None or row.get('equal') is not True or row.get('original_executed') is not True or row.get('candidate_executed') is not True:
            raise ValueError('positive control does not identify an actual matched ledger row')
        for key,expected in (('source_sha256',ledger_identity.get('source_sha256')),
                             ('object_sha256',ledger_identity.get('object_sha256')),
                             ('oracle_sha256',ledger_identity.get('oracle_sha256')),
                             ('original_observation_sha256',row.get('original_observation_sha256')),
                             ('candidate_observation_sha256',row.get('candidate_observation_sha256'))):
            if control.get(key)!=expected:
                raise ValueError(f'positive control {control.get("id")} has ungrounded {key}')
        if row.get('oracle_sha256')!=ledger_identity.get('oracle_sha256'):
            raise ValueError('positive-control ledger row oracle differs from ledger identity')
    report={**raw,'identity':{**identity,'address':ledger['identity']['address']},
            'case_ledger':ledger,'raw_report':pin(out/'raw-run.json')}
    report['positive_controls']=positives
    if review.get('helper_boundaries') is not None:
        report['helper_boundaries']=review['helper_boundaries']
    dump(out/'run.json',report)
    manifest_hash=identity['historical_manifest_sha256']
    if bv.sha256_file(ROOT/bv.HISTORICAL_MANIFEST)!=manifest_hash:
        raise ValueError('historical manifest changed after execution')
    evidence={'schema':'simant-behavior-evidence-v1','function':identity['function'],'status':'BEHAVIOR_EXACT',
        'source':{**pin(out/'module.c'),'whole_module':True,'module':review['module']},
        'suite':{**pin(suite),'id':identity['suite_id']},
        'harness':harness_pins(review,identity),
        'oracle':{**pin(ROOT/'assets/SIMANT.EXE'),'lock_sha256':bv.sha256_file(ROOT/bv.ORACLE_LOCK)},
        'historical_manifest_sha256':manifest_hash,'checkpoint':review['checkpoint'],
        'contract':review['contract'],'run_report':pin(out/'run.json'),
        'negative_controls':pin(out/'negative-controls.json'),
        'historical_difference':review['historical_difference'],'semantic_evidence':review['semantic_evidence'],
        'evidence_date':review['date'],'review_record':pin(out/'contract-review.json')}
    dump(out/'evidence.json',evidence)
    return out/'evidence.json'


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('run',type=Path);p.add_argument('review',type=Path)
    p.add_argument('--destination',help='new immutable packet directory, within this function evidence tree')
    a=p.parse_args();print(package(a.run,a.review,a.destination))
