"""Five routine tests with fixed DOS witnesses against native production objects.

No emulator or differential harness dependency. Expected values were observed
in both DOS executables. The negative control removes only CalcScore's reviewed
word-product narrowing in a freshly compiled whole native TU.
"""
from pathlib import Path
import argparse
import ctypes as ct
import hashlib
import json
import os
import re
import subprocess
import sys
import unittest

ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'tools'))
from workspace import prepare_output


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def command(args,out,log):
    result=subprocess.run(args,cwd=out,capture_output=True,text=True,timeout=120)
    (out/log).write_text(result.stdout+result.stderr)
    if result.returncode:raise RuntimeError(result.stderr[-4000:])


def link(report,out,mutation=False):
    out.mkdir()
    objects=list(report['core_link']['object_inputs'])
    pins={p:sha(p) for p in objects}
    if mutation:
        row=next(r for r in report['canonical_TUs'] if r['source']=='src/S14/m384C.c')
        source=Path(row['generated']).read_text(encoding='latin1')
        pattern=r'scores\[3\] = [^;]+;'
        matches=list(re.finditer(pattern,source))
        if len(matches)!=2 or 'int16_t' not in matches[0][0]:
            raise ValueError('negative-control product anchor changed')
        match=matches[0]
        source=source[:match.start()]+'scores[3] = fd_50F6_09FA * 100 / n;'+source[match.end():]
        changed=out/'unwrapped-score.c';changed.write_text(source,encoding='latin1')
        obj=out/'unwrapped-score.o';args=list(row['compile']['command'])
        args[args.index('-c')+1]=str(changed);args[args.index('-o')+1]=str(obj)
        command(args,out,'mutation-compile.log')
        objects=[str(obj) if p==row['object'] else p for p in objects]
    rsp=out/'objects.rsp';rsp.write_text(''.join('"'+Path(p).as_posix()+'"\n' for p in objects))
    dll=out/'words.dll'
    args=[report['core_link']['command'][0],'-shared','-Wl,--export-all-symbols',
          '-Wl,@objects.rsp',str(Path(report['sdk']['path'])/'lib/libSDL3.dll.a'),
          '-static','-lstdc++','-o',str(dll)]
    command(args,out,'link.log')
    if any(sha(p)!=value for p,value in pins.items()):raise ValueError('production objects changed during test')
    return dll,dict(objects=pins,dll_sha256=sha(dll),mutation=mutation)


class Native:
    def __init__(self,dll,cases):
        self.dll=ct.CDLL(str(dll))
        inventory=json.loads((ROOT/'src/program.json').read_text())
        self.aliases={x['alias'].lstrip('_@'):x for x in inventory['aliases'] if x['kind']!='code'}
        self.baselines={}
        for case in cases:
            for region in case['memory']+case['expected_memory']:
                key=(self.address(region),region['size'])
                self.baselines.setdefault(key,ct.string_at(*key))

    def address(self,region):
        name=region['owner'];offset=region['offset'];seen=set()
        while name in self.aliases:
            if name in seen:raise ValueError('cyclic owner alias')
            seen.add(name);alias=self.aliases[name];offset+=alias.get('offset',0)
            name=alias.get('target',alias.get('owner')).lstrip('_@')
        return ct.addressof(ct.c_uint8.in_dll(self.dll,name))+offset

    def check(self,case):
        for (address,size),value in self.baselines.items():ct.memmove(address,value,size)
        for region in case['memory']:
            value=bytes.fromhex(region['hex']);ct.memmove(self.address(region),value,len(value))
        fn=getattr(self.dll,case['routine'])
        types={'s16':ct.c_int16,'s32':ct.c_int32,'ptr':ct.c_void_p,'void':None}
        fn.argtypes=[types[t] for t in case['arg_types']];fn.restype=types[case['return_kind']]
        value=fn(*[self.address(a['pointer']) if isinstance(a,dict) else a for a in case['args']])
        differences=[]
        if case['return_kind']!='void':
            bits=32 if case['return_kind']=='s32' else 16
            if value&((1<<bits)-1)!=case['return_value']:differences.append('return')
        for region in case['expected_memory']:
            if ct.string_at(self.address(region),region['size']).hex()!=region['hex']:
                differences.append(region['owner'])
        return differences


class WordWitnessTests(unittest.TestCase):
    native=None
    cases={}

    def witness(self,name):
        for case in self.cases[name]:
            with self.subTest(case=case['name']):self.assertEqual([],self.native.check(case),name)
    def test_CalcScore(self):self.witness('CalcScore')
    def test_GetDis(self):self.witness('GetDis')
    def test_viewport_clamp(self):self.witness('f_0250_0F2C')
    def test_BalloonIsVisible(self):self.witness('BalloonIsVisible')
    def test_BoundPointToTri(self):self.witness('BoundPointToTri')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report',type=Path,default=ROOT/'build/current/portable/report.json')
    parser.add_argument('--out',type=Path,default=ROOT/'build/current/tests/word-intermediates')
    args=parser.parse_args();report=json.loads(args.report.read_text())
    if not report.get('passed') or not report['input_stability']['at_end']:
        raise ValueError('successful unchanged native build required')
    for name,pin in report['input_pins'].items():
        if sha(ROOT/name)!=pin:raise ValueError('production input changed: '+name)
    out=prepare_output(args.out.absolute(),ROOT/'build/current/tests/word-intermediates',ROOT)
    cases=json.loads((HERE/'witnesses.json').read_text())['cases']
    ct.windll.kernel32.SetErrorMode(3)
    dll_dir=os.add_dll_directory(str(Path(report['sdk']['path'])/'bin'))
    positive,positive_receipt=link(report,out/'production')
    negative,negative_receipt=link(report,out/'negative',True)
    WordWitnessTests.native=Native(positive,cases)
    WordWitnessTests.cases={}
    for case in cases:WordWitnessTests.cases.setdefault(case['routine'],[]).append(case)
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(WordWitnessTests))
    wrong=Native(negative,cases)
    detected=bool(wrong.check(WordWitnessTests.cases['CalcScore'][0]))
    print('Unwrapped CalcScore negative control detected:',detected)
    receipt=dict(passed=result.wasSuccessful() and detected,tests=result.testsRun,cases=len(cases),
                 negative_control_detected=detected,production=positive_receipt,negative=negative_receipt,
                 build_report_sha256=sha(args.report),witnesses_sha256=sha(HERE/'witnesses.json'))
    (out/'report.json').write_text(json.dumps(receipt,indent=2)+'\n')
    return int(not receipt['passed'])


if __name__=='__main__':raise SystemExit(main())
