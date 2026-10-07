"""Analyze every generated canonical TU in a native build receipt."""
from pathlib import Path
from collections import Counter
import argparse
import json
import sys
import copy
import hashlib

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'portable'))
from canonical_native_abi.integer_frontend import convert

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--report',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--cc',default='C:/msys64/mingw64/bin/gcc.exe')
    args=p.parse_args()
    report=json.loads(args.report.read_text())
    build=args.report.resolve().parent
    rows=[];counts=Counter();categories=Counter();errors=[]
    output=args.out.resolve();output.parent.mkdir(parents=True,exist_ok=True)
    def write():
        output.write_text(json.dumps({'schema':'msc16-expression-census-v1','counts':dict(counts),
            'categories':dict(categories),'translation_units':rows,'errors':errors},indent=2)+'\n')
    for index,row in enumerate(report['canonical_TUs']):
        if row['lang']!='c':continue
        path=Path(row['generated'])
        try:
            if 'integer_expressions' in row:
                receipt=copy.deepcopy(row['integer_expressions'])
                generated=path.read_text(encoding='latin1')
                if hashlib.sha256(generated.encode('latin1')).hexdigest()!=receipt['output_sha256']:
                    raise ValueError('Generated whole TU differs from its expression receipt')
            else:
                generated,receipt=convert(path.read_text(encoding='latin1'),path.as_posix(),args.cc,
                    [build/'include',ROOT,build,ROOT/'portable/whole_program'])
            receipt['source']=row['source'];receipt['module']=row['module']
            receipt['compiled']=row.get('status')!='PLATFORM_BOUNDARY'
            for expr in receipt['expressions']:
                expr['canonical_source']=row['source']
            rows.append(receipt);counts.update(receipt['counts']);categories.update(receipt['categories'])
            if 'integer_expressions' not in row:
                draft=output.parent/'lowered-drafts'/path.name
                draft.parent.mkdir(exist_ok=True);draft.write_text(generated,encoding='latin1')
        except Exception as exc:
            errors.append({'source':row['source'],'error':str(exc)})
        if index%20==0:write()
    write()
    print(json.dumps({'TUs':len(rows),'counts':dict(counts),'categories':dict(categories),'errors':errors},indent=2))
    return bool(errors)

if __name__=='__main__':raise SystemExit(main())
