#!/usr/bin/env python3
"""Verify the source/build closure supporting the 50F6 V6 diagnostic lane."""
from __future__ import annotations
import hashlib,json,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
PLAN=ROOT/'portable/research/whole_program_simulation_state_50f6_v6.json'
CONSUMER=ROOT/'portable/research/whole_program_simulation_state_50f6_consumer_v6.json'
OUT=ROOT/'portable/research/whole_program_simulation_state_50f6_closure_v6.json'
def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def main()->None:
    if OUT.exists():raise SystemExit(f'refusing to overwrite immutable report {OUT.relative_to(ROOT)}')
    plan=json.loads(PLAN.read_text(encoding='utf-8'));test=json.loads(CONSUMER.read_text(encoding='utf-8'))
    checks=[]
    for rel,v in plan['input_hashes'].items():
        p=ROOT/rel; actual=sha(p) if p.exists() else None
        checks.append({'path':rel,'before_sha256':v['sha256'],'after_sha256':actual,'stable':actual==v['sha256']})
    for rel,digest in plan['source_hashes'].items():
        p=ROOT/rel; actual=sha(p) if p.exists() else None
        checks.append({'path':rel,'before_sha256':digest,'after_sha256':actual,'stable':actual==digest})
    extra=['portable/tools/whole_program.py','portable/build.py','docs/dos-semantic-oracle-v1.json','layout/oracle.lock.json',
           'build/portable/simant-sdl3.build.json','build/portable/simant-sdl3.exe',
           'portable/whole_program/conversions/simulation_state_50f6_preword.py',
           'portable/whole_program/conversions/simulation_state_50f6_plan_v6.py',
           'portable/whole_program/conversions/simulation_state_50f6_consumer_probe_v6.py',
           'portable/whole_program/conversions/simulation_state_50f6_closure_v6.py',
           'portable/research/whole_program_simulation_state_50f6_v6.json',
           'portable/research/whole_program_simulation_state_50f6_consumer_v6.json']
    for rel in extra:
        p=ROOT/rel
        if p.exists():checks.append({'path':rel,'after_sha256':sha(p),'stable':True,'post_run_pin':True})
    compiler=Path(test['compiler']['path']); compiler_hash=sha(compiler)
    if compiler_hash!=test['compiler']['sha256']:raise SystemExit('test compiler binary changed since consumer receipt')
    unstable=[x for x in checks if not x['stable']]
    if unstable:raise SystemExit(f'closure changed: {unstable}')
    report={'schema':'simant-whole-program-simulation-state-closure-v6','claim':'FINITE_CURRENTNESS_ONLY: confirms pinned generation/source/tool inputs remained stable for this diagnostic test lane.',
       'plan_report':{'path':PLAN.relative_to(ROOT).as_posix(),'sha256':sha(PLAN)},
       'consumer_report':{'path':CONSUMER.relative_to(ROOT).as_posix(),'sha256':sha(CONSUMER)},
       'checks':checks,'summary':{'checked_before_pinned_paths':sum(1 for x in checks if 'before_sha256' in x),'post_run_pins':sum(1 for x in checks if x.get('post_run_pin')),'changed_paths':0},
       'toolchain':{'compiler':test['compiler'],'test_executable_hashes':{'point':sha(ROOT/'build/workers/whole_program/simulation_state_50f6_v6_consumer/point_consumer.exe'),'score':sha(ROOT/'build/workers/whole_program/simulation_state_50f6_v6_consumer/score_consumer.exe')},
          'production_build_receipt':json.loads((ROOT/'build/portable/simant-sdl3.build.json').read_text(encoding='utf-8')).get('sdl_sdk_sha256'),
          'frozen_oracle':json.loads((ROOT/'layout/oracle.lock.json').read_text(encoding='utf-8'))},
       'nonclaims':['No new production executable was built for this task.','The pinned production SDL build is contextual toolchain provenance only, not evidence about the tested generated consumers.','This currentness receipt does not promote owners or claim full simulation behavior.']}
    OUT.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(f'WROTE {OUT.relative_to(ROOT)}; pinned_before={report["summary"]["checked_before_pinned_paths"]}; post_run={report["summary"]["post_run_pins"]}; changed=0')
if __name__=='__main__':main()
