"""Recheck declarative span placements against the linked canonical DOS oracle.

This evidence tool uses canonical MAP/OMF, never nearest-public extents or
original-image addresses. It is not a native runtime/build dependency.
"""
from pathlib import Path
import argparse,hashlib,json,sys

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'portable'))
from canonical_native_abi.semantic_spans import Contracts
from canonical_dos_layout import canonical_layout


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--oracle-root',type=Path,default=ROOT)
    ap.add_argument('--dos-report',type=Path)
    ap.add_argument('--out',type=Path)
    args=ap.parse_args();oracle=args.oracle_root.resolve()
    report=args.dos_report or oracle/'build/current/dos/build-report.json'
    from canonical_native_abi import asm_data
    asm_data.ROOT=oracle
    placements,errors=canonical_layout(oracle,report)
    if errors:raise ValueError('unproved canonical placement: '+str(errors))
    doc=json.loads((ROOT/'portable/semantic-spans.json').read_text())
    program=json.loads((ROOT/'src/program.json').read_text())
    texts={m['source']:(ROOT/m['source']).read_text(encoding='latin1') for m in program['modules'] if m['lang']=='c'}
    contract=Contracts(ROOT,texts,doc)
    for name,fact in doc['owner_layout'].items():
        actual=placements.get(name)
        if not actual or actual['dos_address']!=fact['address']:
            raise ValueError('canonical MAP/OMF placement contradicts span catalog: '+name)
        if 'bytes' in actual and actual['bytes']!=fact['bytes']:
            raise ValueError('canonical COMDEF extent contradicts span catalog: '+name)
    result=dict(schema='simant-semantic-span-dos-layout-check-v1',passed=True,
                named_placements=len(placements),checked_owner_addresses=len(doc['owner_layout']),
                cross_owner_save_records=contract.cross_records,
                literal_crossings=len(contract.cross_accesses),
                contract_sha256=hashlib.sha256((ROOT/'portable/semantic-spans.json').read_bytes()).hexdigest(),
                dos_executable_sha256=json.loads(report.read_text())['link']['candidate_executable']['sha256'],
                scope='All catalog owner addresses and available COMDEF extents independently re-resolved from canonical MAP/OMF; initialized member extents are canonical declarations enforced by native sizeof assertions.')
    if args.out:args.out.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
    return 0


if __name__=='__main__':raise SystemExit(main())
