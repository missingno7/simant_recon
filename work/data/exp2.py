import sys
sys.path.insert(0,'tools')
import compiler
from omf import OmfReader
sizes=[0x180,0x2000,0x1000,0x1000,0x1000,0x1000,0x2000,0x1000,0x1000]+[1001]*5+[501]*10+[0x800]*7
mode=sys.argv[1]
lines=[]
for i,z in enumerate(sizes):
    if mode=='init': lines.append(f"unsigned char far v{i}[{z}] = {{0}};")
    elif mode=='static': lines.append(f"static unsigned char far v{i}[{z}];")
    else: lines.append(f"unsigned char far v{i}[{z}];")
lines.append('char far hdr[256] = "pSimAnt";')
lines.append('int far f(void){ return v0[1]+v30[3]+hdr[0]; }')
r=compiler.compile_c("\n".join(lines)+"\n",'msc600ax',['/AL','/Os','/Oe','/Og','/Zi'])
print(r.ok, r.log[-400:])
if r.ok:
    o=OmfReader(communals=True).read(r.obj)
    for s in o.segment_defs:
        if s['class'] not in ('DEBSYM','DEBTYP'): print(s['name'],s['class'],hex(s['length']),s['alignment'])
    print([(p['name'],p['segment'],hex(p['offset'])) for p in o.publics])
    print(len(o.communals))
