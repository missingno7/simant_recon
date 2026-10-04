"""DOS list text lookup with real lock/unlock and runtime strlen execution."""
import argparse
import hashlib
import json
import random
import struct
import sys
import time
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / 'layout/functions.json').is_file())

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




