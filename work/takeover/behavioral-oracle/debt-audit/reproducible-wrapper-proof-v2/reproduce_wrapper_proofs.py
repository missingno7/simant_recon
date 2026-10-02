"""Reproduce the bounded supplemental DOS-address behavior suite (proof v2).

From any working directory inside a fresh clone:
  python work/takeover/behavioral-oracle/debt-audit/reproducible-wrapper-proof-v2/reproduce_wrapper_proofs.py

Default outputs are build/workers/behavior_gap_repro_v2 only. `--archive`
explicitly copies the run report, candidate source/object files and this script
into the v2 archive directory. No executable image is copied or rewritten.
"""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, shutil, sys
from pathlib import Path


def find_root():
    for candidate in (Path.cwd().resolve(), *Path(__file__).resolve().parents):
        if (candidate/'layout/manifest.json').is_file() and (candidate/'tools/behavior.py').is_file():
            return candidate
    raise RuntimeError('repository root not found (expected layout/manifest.json and tools/behavior.py)')

ROOT=find_root()
ARCH=ROOT/'work/takeover/behavioral-oracle/debt-audit'
V1_DIR=ARCH/'reproducible-wrapper-proof'
V1_REPORT=V1_DIR/'report.json'
V1_PRODUCER=ARCH/'reproduce_wrapper_proofs.py'
OUT=ROOT/'build/workers/behavior_gap_repro_v2'
ARCHIVE=ARCH/'reproducible-wrapper-proof-v2'

def sha(data): return hashlib.sha256(data).hexdigest()
def file_sha(path): return sha(Path(path).read_bytes())

def load_and_verify_v1():
    report=json.loads(V1_REPORT.read_text())
    if file_sha(V1_PRODUCER)!=report['components']['producer_sha256']:
        raise RuntimeError('immutable v1 producer hash drift')
    component_paths={'behavior.py':'tools/behavior.py','compiler.py':'tools/compiler.py','modules.py':'tools/modules.py',
      'modctx.py':'tools/modctx.py','match.py':'tools/match.py','toolchain.json':'layout/toolchain.json'}
    for key,rel in component_paths.items():
        if file_sha(ROOT/rel)!=report['components'][key]: raise RuntimeError(f'v1 component hash drift: {rel}')
    for old in report['candidates']:
        if file_sha(ROOT/old['source_rel'])!=old['source_sha256']:
            raise RuntimeError(f'canonical source drift: {old["source_rel"]}')
    return report

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--archive',action='store_true',help='copy generated report/sources/objects into the v2 archive'); args=ap.parse_args()
    old=load_and_verify_v1()
    OUT.mkdir(parents=True,exist_ok=True)
    # Import the untouched v1 suite from its original, known-correct depth. Its main()
    # is not called, so its unconditional archive copy is never reached.
    spec=importlib.util.spec_from_file_location('supplemental_wrapper_v1',V1_PRODUCER)
    suite=importlib.util.module_from_spec(spec);sys.modules[spec.name]=suite;spec.loader.exec_module(suite)
    suite.ROOT=ROOT;suite.OUT=OUT;suite.ARCH=ARCH;suite.CANDIDATES.clear()
    actual_cases=suite.wrapper_cases()
    old_candidates={x['function']:x for x in old['candidates']}
    candidate_report=[]
    for item in suite.CANDIDATES:
        prior=old_candidates.get(item['function'])
        if prior is None: raise RuntimeError('unexpected candidate in v1 suite: '+item['function'])
        for k in ('source_sha256','compiled_source_sha256','object_sha256','target_sha256','target_size','profile','flags','module'):
            if item[k]!=prior[k]: raise RuntimeError(f'{item["function"]}: v1 evidence drift at {k}')
        candidate_path=OUT/(item['function']+'.c')
        actual_bytes=candidate_path.read_bytes()
        normalized=candidate_path.read_text(encoding='latin1').replace('\r\n','\n').replace('\r','\n').encode('latin1')
        if sha(normalized)!=item['compiled_source_sha256']:
            raise RuntimeError(f'{item["function"]}: candidate C normalized-source hash mismatch')
        object_path=OUT/(item['function']+'.obj')
        if file_sha(object_path)!=item['object_sha256']:
            raise RuntimeError(f'{item["function"]}: candidate object hash mismatch')
        candidate_report.append({**item,'candidate_c_artifact_sha256':sha(actual_bytes),
          'candidate_c_normalized_sha256':sha(normalized),'candidate_object_artifact_sha256':file_sha(object_path),
          'v1_candidate_pin_match':True})
    import behavior
    components={'producer_v1_sha256':file_sha(V1_PRODUCER),'producer_v2_sha256':file_sha(__file__),
      'behavior.py':file_sha(ROOT/'tools/behavior.py'),'compiler.py':file_sha(ROOT/'tools/compiler.py'),
      'modules.py':file_sha(ROOT/'tools/modules.py'),'modctx.py':file_sha(ROOT/'tools/modctx.py'),
      'match.py':file_sha(ROOT/'tools/match.py'),'toolchain.json':file_sha(ROOT/'layout/toolchain.json'),
      'behavior_harness_sha256':sha(behavior.HARNESS_SOURCE)}
    report={'schema':'supplemental-address-proof-v2-reproduction','oracle_sha256':behavior.exe.load().sha256,
      'manifest_sha256':file_sha(ROOT/'layout/manifest.json'),'v1_report_sha256':file_sha(V1_REPORT),
      'suite_id':'supplemental-address-wrappers-and-empty-far-retf','case_count':len(actual_cases),
      'mismatches':sum(not result.equal for _,_,result in actual_cases),'components':components,
      'candidates':candidate_report,'runs':[]}
    for name,case,result in actual_cases:
        report['runs'].append({'function':name,'case':case.label,'equal':result.equal,'diff':result.diff,
          'modeled_boundaries':case.metadata.get('modeled_boundaries',[]),
          'actual_helpers':case.metadata.get('actual_helpers',[]),
          'original':result.original,'candidate':result.candidate})
    if report['mismatches']: raise RuntimeError('one or more cases differ; inspect output before any proof claim')
    output=OUT/'report.json';output.write_text(json.dumps(report,indent=2)+'\n')
    if args.archive:
        ARCHIVE.mkdir(parents=True,exist_ok=True)
        shutil.copy2(output,ARCHIVE/'report.json')
        if Path(__file__).resolve()!= (ARCHIVE/'reproduce_wrapper_proofs.py').resolve():
            shutil.copy2(Path(__file__),ARCHIVE/'reproduce_wrapper_proofs.py')
        for item in candidate_report:
            for suffix in ('.c','.obj'):
                shutil.copy2(OUT/(item['function']+suffix),ARCHIVE/(item['function']+suffix))
        rows=[]
        for path in sorted(ARCHIVE.rglob('*')):
            if path.is_file() and path.name!='SHA256SUMS.txt':
                rows.append(f'{file_sha(path)} {path.relative_to(ARCHIVE).as_posix()}')
        (ARCHIVE/'SHA256SUMS.txt').write_text('\n'.join(rows)+'\n')
    print(json.dumps({'suite_id':report['suite_id'],'cases':report['case_count'],'mismatches':report['mismatches'],
      'v1_pins_verified':True,'archive_written':args.archive,'report':str(output)},indent=2))

if __name__=='__main__': main()
