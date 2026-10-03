#!/usr/bin/env python3
"""Strict whole-TU consumer compile receipt for the fixed V6 adapter."""
from __future__ import annotations
import hashlib,json,shutil,subprocess
from pathlib import Path
from portable.whole_program.conversions.source_bounded_simulation_state_v6 import (
    ROOT,PLAN_PATH,load_plan,render_owners,adapt)

GEN=ROOT/'build/workers/whole_program/generated'
MIGRATION=GEN/'migration.json'
WORK=ROOT/'build/workers/whole_program/simulation_state_50f6_v6_production'
REPORT=ROOT/'portable/research/whole_program_simulation_state_50f6_production_strict_v6.json'
def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def run(args:list[str])->str:
    p=subprocess.run(args,cwd=ROOT,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    if p.returncode:raise RuntimeError(f'command failed ({p.returncode}): {args}\n{p.stdout}')
    return p.stdout.strip()
def main()->None:
    if REPORT.exists():raise SystemExit(f'refusing to overwrite immutable report {REPORT.relative_to(ROOT)}')
    plan=load_plan();header,owners=render_owners(plan)
    migration=json.loads(MIGRATION.read_text(encoding='utf-8'))
    module_by_source={m['source']:m for m in migration['modules']}
    sources=sorted({d['source'] for o in plan['targets'] for d in o['declarations']})
    if not sources:raise ValueError('V6 plan has no consumers')
    WORK.mkdir(parents=True,exist_ok=True)
    hpath=WORK/'simulation_state_50f6.h';cpath=WORK/'simulation_state_50f6.c'
    hpath.write_text(header,encoding='utf-8',newline='\n');cpath.write_text(owners,encoding='utf-8',newline='\n')
    cc=shutil.which('gcc')
    if not cc:raise RuntimeError('gcc missing')
    flags=['-std=c11','-fsigned-char','-fno-builtin','-DSIMANT_NATIVE_LITTLE_ENDIAN=1',
           '-Werror=implicit-function-declaration','-Werror=implicit-int',
           '-I'+str(ROOT),'-I'+str(ROOT/'portable/whole_program'),'-I'+str(GEN),'-I'+str(WORK)]
    results=[]
    for rel in sources:
        mod=module_by_source.get(rel)
        if not mod:raise ValueError(f'whole-TU migration receipt missing consumer {rel}')
        gen=ROOT/mod['generated']
        before=sha(gen)
        if before!=mod['generated_sha256']:
            raise ValueError(f'generated consumer changed since migration receipt: {mod["generated"]}')
        raw=gen.read_text(encoding='utf-8')
        converted,evidence=adapt(raw,rel,plan)
        if evidence is None:raise ValueError(f'V6 selected consumer was not adapted: {rel}')
        out=WORK/(gen.stem+'_v6.c');obj=WORK/(gen.stem+'_v6.o')
        out.write_text(converted,encoding='utf-8',newline='\n')
        command=[cc,*flags,'-c',str(out),'-o',str(obj)]
        output=run(command)
        results.append({'source':rel,'generated_path':mod['generated'],'generated_sha256_before':before,
            'adapter':evidence,'adapted_source_sha256':sha(out),'object_sha256':sha(obj),'command':command,'compiler_output':output})
    # Negative controls prove strictness on caller plan and generated declarations.
    wrong=dict(plan);wrong['targets']=plan['targets'][:-1]
    try:render_owners(wrong)
    except ValueError:bad_plan_rejected=True
    else:bad_plan_rejected=False
    first=results[0];generated_path=ROOT/first['generated_path'];original=generated_path.read_text(encoding='utf-8')
    rel=first['source'];target=next(iter(first['adapter']['source_views']))
    bad_source=original.replace(next(line for line in original.splitlines(True) if line.lstrip().startswith('extern ') and target in line), '', 1)
    try:adapt(bad_source,rel,plan)
    except ValueError:bad_decl_rejected=True
    else:bad_decl_rejected=False
    if not bad_plan_rejected or not bad_decl_rejected:raise AssertionError('V6 strict negative controls failed')
    inputs=[PLAN_PATH,MIGRATION,ROOT/'portable/tools/whole_program.py',Path(__file__),ROOT/'portable/whole_program/conversions/source_bounded_simulation_state_v6.py',
            ROOT/'portable/whole_program/conversions/simulation_state_50f6_preword.py',ROOT/'portable/whole_program/conversions/simulation_state_50f6_plan_v6.py',
            ROOT/'portable/whole_program/conversions/simulation_state_50f6_consumer_probe_v6.py',hpath,cpath]
    for row in results:inputs.append(ROOT/row['generated_path'])
    report={'schema':'simant-whole-program-simulation-state-production-v6','claim':'FINITE_STRICT_INTEGRATION_CHECK: fixed-plan owner emission and whole-generated-TU compile checks; no DOS behavioral, rendering, or general program-equivalence claim.',
       'plan_sha256':sha(PLAN_PATH),'plan_input_hashes_checked':len(plan['source_hashes']),'target_owner_count':len(plan['targets']),
       'owner_emission_sha256':{'header':sha(hpath),'source':sha(cpath)},
       'compiler':{'path':str(Path(cc).resolve()),'sha256':sha(Path(cc).resolve()),'version':run([cc,'--version']).splitlines()[0]},
       'whole_tu_consumer_count':len(results),'consumers':results,
       'negative_controls':{'modified_plan_argument_rejected':bad_plan_rejected,'missing_pinned_generated_extern_rejected':bad_decl_rejected},
       'inputs':[{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)} for p in inputs],
       'nonclaims':['Diagnostic generated consumers are not executions of the DOS binary.','The owner converter is a separate module; this probe does not alter or invoke the central generator.','No output-size extent is inferred from FAR_BSS or address gaps.']}
    if REPORT.exists():raise SystemExit(f'refusing to overwrite immutable report {REPORT.relative_to(ROOT)}')
    REPORT.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(f'PASS: adapted and compiled {len(results)} whole generated TUs; strict negative controls PASS')
    print(f'WROTE {REPORT.relative_to(ROOT)}')
if __name__=='__main__':main()
