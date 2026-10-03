"""Archive a current mechanical-build receipt without claiming game acceptance."""
from pathlib import Path
import argparse
import hashlib
import json

ROOT = Path(__file__).resolve().parents[2]

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--migration', default='build/workers/whole_program/generated/migration.json')
    ap.add_argument('--out', required=True)
    args = ap.parse_args()
    source, out = ROOT / args.migration, (ROOT / args.out).resolve()
    if not out.is_relative_to(ROOT / 'portable') or out.exists():
        raise ValueError('a new, versioned portable receipt is required')
    report = json.loads(source.read_text())
    if not report['inputs_stable'] or not report['partial_core_link']['passed']:
        raise ValueError('successful stable partial-core build required')
    failed = [p for p,h in report['inputs'].items() if sha(ROOT / p) != h]
    for row in report['modules'] + report['native_support']:
        if ('generated_sha256' in row and
                sha(ROOT / row['generated']) != row['generated_sha256']):
            failed.append(row['generated'])
        compiled = row.get('compile',{})
        if compiled.get('passed') and sha(ROOT / compiled['object']) != compiled['object_sha256']:
            failed.append(compiled['object'])
    if sha(ROOT / report['partial_core_link']['object']) != report['partial_core_link']['object_sha256']:
        failed.append(report['partial_core_link']['object'])
    if failed:
        raise ValueError(f'build inputs or outputs have changed: {failed}')
    receipt = {k:report[k] for k in ('schema','claim','frozen_oracle_check',
        'source_module_count','code_module_count','data_module_count',
        'source_function_definition_count','original_lexical_function_count',
        'compile_pass_count','duplicate_object_definitions',
        'unprovided_contract_class_counts','compiler','inputs')}
    receipt.update(
        receipt_generator_sha256=sha(Path(__file__)),
        migration_report_sha256=sha(source),
        inputs_verified_current=True,
        native_support_compile_pass_count=sum(r['compile']['passed'] for r in report['native_support']),
        missing_reference_count=len(report['unprovided_object_symbols']),
        unprovided_references=report['unprovided_object_symbols'],
        source_modules=[{'source':r['source'],'generated_sha256':r['generated_sha256'],
            'function_count':len(r['functions']), 'compile':r['compile']} for r in report['modules']],
        native_support=report['native_support'],
        partial_core_link=report['partial_core_link'],
        scope='Full original C-module mechanical migration and relocatable object link only. No executable, whole-game coverage, or new DOS equivalence claim. Missing references include CRT imports and unimplemented native boundaries.')
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps({'original_modules_compiled':receipt['compile_pass_count'],
        'native_modules_compiled':receipt['native_support_compile_pass_count'],
        'missing_references':receipt['missing_reference_count']}))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
