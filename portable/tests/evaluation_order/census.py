"""Reproduce the canonical C census and verify pinned MSC order evidence.

--objects compiles the 17 affected whole modules with their manifest profiles
and flags plus /Fc. The listing switch must retain the pinned object hash.
Every retained instruction/context is checked against that object and its
fixups. Output, including compiler scratch, stays in --out.
"""
from pathlib import Path
from collections import Counter
import argparse
import hashlib
import json
import re
import sys

ROOT=Path(__file__).resolve().parents[3]
sys.path[:0]=[str(ROOT/'portable'),str(ROOT/'tools')]
from canonical_native_abi import integer_frontend as f, evaluation_order as e, scalar, lexical, tokenizer


def canonical_census(cc):
    rows=[];units=[]
    for unit in json.loads((ROOT/'src/program.json').read_text())['modules']:
        if unit['lang']!='c':continue
        path=unit['source']
        source=scalar.convert(lexical.expand_shared_headers((ROOT/path).read_text(encoding='latin1')))
        # Parse-only removal of MSC storage/ASM syntax. No C expression is
        # replaced; the assembler bodies have no C evaluation trees.
        source=re.sub(r'\binterrupt\b','',source)
        source=re.sub(r'\b_segment\b','uint16_t',source)
        source=re.sub(r'_asm\s*\{[^{}]*\}',lambda m:';'+'\n'*m[0].count('\n'),source,flags=re.S)
        source=re.sub(r'\b_based\s*\([^()]*\)','',source)
        for t in reversed(tokenizer.tokenize(source)):
            if t.kind=='asm':source=source[:t.s]+';'+'\n'*t.text.count('\n')+source[t.e:]
        source='#include <stdint.h>\n#include <stddef.h>\n'+source
        pp,_=f.preprocess(source,path,cc,[ROOT/'include'])
        tree=f.c_parser.CParser().parse(pp,filename=path)
        found=e.serializable(e.census(tree))
        rows.extend(dict(r,source=path) for r in found)
        units.append(dict(source=path,sites=len(found),source_sha256=hashlib.sha256((ROOT/path).read_bytes()).hexdigest()))
    return rows,units


def verify_census(rows,contracts):
    def identity(r):return {k:v for k,v in r.items() if k!='line'}
    if [identity(r) for r in rows]!=[identity(r) for r in contracts['canonical_sites']]:
        raise ValueError('canonical unsequenced site census changed; new object order evidence required')


def verify_objects(contracts,out):
    import compiler
    from omf import OmfReader
    compiler.WORK=out/'compiler'
    modules=json.loads((ROOT/'layout/manifest.json').read_text())['modules'];receipts=[]
    for expected in contracts['modules']:
        key=expected['module'];unit=modules[key]
        compiled=compiler.compile_c((ROOT/unit['source']).read_text(encoding='latin1'),unit['profile'],unit['flags']+['/Fc'],keep=True)
        if not compiled.ok:raise ValueError(compiled.log)
        digest=hashlib.sha256(compiled.obj).hexdigest()
        if digest!=unit['object_sha256'] or digest!=expected['object_sha256']:
            raise ValueError('MSC whole-object identity changed: '+key)
        obj=OmfReader(communals=True).read(compiled.obj)
        code=obj.segment_bytes('UNIT_TEXT');fixups=obj.fixups_in('UNIT_TEXT')
        listing=(compiled.workdir/'UNIT.COD').read_text(encoding='latin1')
        decoded={}
        for line in listing.splitlines():
            m=re.match(r'\s*\*\*\* ([0-9a-f]+)\s+((?:[0-9a-f]{2} )+)\s*(.*)',line)
            if not m:continue
            at=int(m[1],16);raw=bytes.fromhex(m[2]);asm=m[3]
            if code[at:at+len(raw)]!=raw:continue # non-code segment listing
            decoded[at]=dict(asm=asm,fixups=[x for x in fixups if at<=x['offset']<at+len(raw)])
        count=0
        for region in contracts['regions']:
            if region['module']!=key:continue
            for event in region['instructions']:
                for ins in [event,*event['context']]:
                    if decoded.get(ins['offset'])!={k:ins[k] for k in ('asm','fixups')}:
                        raise ValueError('instruction/fixup evidence drift: '+region['id'])
                count+=1
        receipts.append(dict(module=key,object_sha256=digest,exact_object=True,events=count,
                             compiler_command=compiled.argv,workdir=str(compiled.workdir)))
        print(key,'exact object;',count,'event witnesses',flush=True)
    return receipts


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--objects',action='store_true')
    ap.add_argument('--report',type=Path)
    ap.add_argument('--cc',default='C:/msys64/mingw64/bin/gcc.exe')
    args=ap.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    contracts=json.loads(e.CONTRACT_PATH.read_text())
    rows,units=canonical_census(args.cc);verify_census(rows,contracts)
    result=dict(passed=True,translation_units=len(units),sites=len(rows),counts=dict(Counter(r['kind'] for r in rows)),units=units)
    if args.objects:result['objects']=verify_objects(contracts,args.out)
    if args.report:
        report=json.loads(args.report.read_text());receipts=[]
        for unit in report['canonical_TUs']:
            if unit['lang']!='c':continue
            receipt=unit['integer_expressions']['evaluation_order']
            if receipt['status']!='COVERED':raise ValueError('native census not covered: '+unit['source'])
            receipts.extend(receipt['regions'])
        if len(receipts)!=len(contracts['regions']):raise ValueError('native region count drift')
        result['native_regions']=len(receipts)
    (args.out/'census.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in {'units','objects'}},indent=2))


if __name__=='__main__':main()
