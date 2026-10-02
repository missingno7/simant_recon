"""DOS list text lookup with real lock/unlock and runtime strlen execution."""
import argparse
import hashlib
import json
import random
import struct
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
import behavior as b
from behavior_ledger import CaseLedger

FUNCTION = 'f_23E6_0000'
SUITE_SOURCE=Path(__file__).read_bytes()
EFFECTS=['far pointer return','list cache','text','lock count and block age',
         'global age','ordered actual lock/unlock/strlen calls','all nonstack writes','caller ABI']
HANDLE = (0x100,0xA000)
DATA = (0,0xA100)
LIST = (0x100,0xA500)


def make_case(label, lines, top, visible, line, age=0, lock=0):
    if not 0 <= top <= top+visible <= len(lines):
        raise ValueError('invalid list cache range')
    if any(b'\0' in s for s in lines): raise ValueError('embedded terminator')
    offsets = [0]
    for s in lines: offsets.append(offsets[-1]+len(s)+1)
    text = b'\0'.join(lines)+b'\0\0'
    if len(text)>0x3000: raise ValueError('text arena exhausted')
    # Original lock/unlock evidence: root:171C:1FC2 and :2086 use
    # DS:2F30 age, DS:2F42 master count and DS:2F46/48 end pointer.
    dg = b.match.DGROUP_SEG*16
    header = bytearray(32)
    struct.pack_into('<HIH',header,0,HANDLE[0],len(text),(len(text)+47)//16)
    header[8],header[9] = 0,lock
    list_data = b.words(visible,len(lines),top,offsets[top],offsets[top+visible],*HANDLE)
    return b.Case(label,args=list(LIST),registers={'ax':line & 65535},
        callee_pop=4,return_kind='farptr',
        writes=[(dg+0x2F30,struct.pack('<I',age)),(dg+0x2F42,b.words(1)),
                (dg+0x2F46,b.words(HANDLE[0]+4,HANDLE[1])),
                (HANDLE[1]*16+HANDLE[0],b.words(*DATA)),
                ((DATA[1]-2)*16,bytes(header)),
                (DATA[1]*16,text), (LIST[1]*16+LIST[0],list_data)],
        observe=[b.Range('list',LIST[1]*16+LIST[0],14),
                 b.Range('text',DATA[1]*16,len(text)),
                 b.Range('block_header',(DATA[1]-2)*16,32),
                 b.Range('age',dg+0x2F30,4)],
        callbacks={'f_171C_1B84':b.Callback(2),'f_171C_1BBA':b.Callback(2),
                   '_fstrlen':b.Callback(2)},
        metadata={'line':line,'top':top,'visible':visible,'lengths':list(map(len,lines)),
                  'helpers':'all original; no modeled callbacks'})


def cases(count,seed):
    for lengths in ([],[0],[1],[1,0,3],[1,2,3,4,5], [0,1,7,31,255]):
        lines = [bytes([65+i])*n for i,n in enumerate(lengths)]
        for top in range(len(lines)+1):
            for visible in range(len(lines)-top+1):
                for line in [-32768,-1,*range(len(lines)+3),32767]:
                    yield 'directed',make_case(f'grid/{lengths}/{top}/{visible}/{line}',lines,top,visible,line)
    rng = random.Random(seed)
    for i in range(count):
        n = rng.randrange(129)
        lines = [bytes(rng.randrange(1,256) for _ in range(rng.randrange(65))) for _ in range(n)]
        top = rng.randrange(n+1); visible=rng.randrange(n-top+1)
        line = rng.choice([-32768,-1,rng.randrange(n+8),32767])
        yield 'randomized',make_case(f'random/{seed}/{i}',lines,top,visible,line,
                                    rng.randrange(1<<32),rng.randrange(100))


def run(count,seed,out):
    pair = b.PreparedPair(FUNCTION,out=out)
    ledger=CaseLedger(out/'cases.jsonl.gz',pair,EFFECTS)
    counts = {'directed':0,'randomized':0}; failures=[]
    started=time.monotonic()
    for group,case in cases(count,seed):
        result=pair.compare(case); counts[group]+=1
        ledger.record(case,result,lane=group)
        if not result.equal:
            failures.append({'label':case.label,'state':case.metadata,'diff':result.diff})
            break
    source = pair.source.read_text(encoding='latin1')
    anchor='s++;\n        n++;'
    if source.count(anchor)!=1: raise RuntimeError('negative source anchor not unique')
    mutant=out/'negative.c'; mutant.write_text(source.replace(anchor,'s++;\n        n += 2;',1),encoding='latin1')
    negpair=b.PreparedPair(FUNCTION,source=mutant,out=out/'negative')
    negative=negpair.compare(make_case('negative/skip-line',[b'a',b'bb',b'ccc'],0,3,2))
    report={'schema':'behavior-suite-run-v1','function':FUNCTION,'identity':pair.identity,
        'suite_sha256':hashlib.sha256(SUITE_SOURCE).hexdigest(),
        'case_ledger':ledger.finalize(),
        'directed':counts['directed'],'randomized':counts['randomized'],'seed':seed,
        'mismatches':len(failures),'errors':0,'failures':failures,
        'negative_control':{'detected':not negative.equal,'diff':negative.diff},
        'compared':EFFECTS,
        'domain':'all cache ranges for six finite line-length patterns; random valid cached lists 0..128 rows, 0..64 bytes per row; signed line extremes; all 32-bit ages; lock 0..99',
        'boundaries':'all helpers execute original; no modeled callbacks or I/O',
        'historical_difference':'original additionally reloads pointer segment into CX at +0x73; later instructions do not consume CX before return or redefine it',
        'status':'UNRESOLVED pending supervisor review',
        'elapsed_seconds':round(time.monotonic()-started,3)}
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    if failures or negative.equal: raise AssertionError('list differential failed')
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--count',type=int,default=10000)
    p.add_argument('--seed',type=lambda s:int(s,0),default=0x23E6)
    p.add_argument('--out',type=Path,default=ROOT/'build/workers/behavior_lists/ledger-20261002')
    args=p.parse_args()
    print(json.dumps(run(args.count,args.seed,args.out),indent=2))
