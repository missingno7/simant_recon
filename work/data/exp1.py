import sys, json
sys.path.insert(0,'tools')
import compiler
from omf import OmfReader
src = r'''
int far ga[4];
int far gb[3] = {1,2,3};
static int far sa[5];
static int far sb[2] = {7,8};
extern int far ex;
int dn[2];
int di = 5;
char far *fp = "hello";
int far f1(void) { return ga[1] + gb[1] + sa[1] + sb[1] + ex + dn[0] + di + *fp; }
'''
prof = sys.argv[1] if len(sys.argv)>1 else 'msc600ax'
r = compiler.compile_c(src, prof, ['/AL','/Os','/Oe','/Og','/Zi'])
print(r.ok, r.log[-300:])
o = OmfReader(communals=True).read(r.obj)
for s in o.segment_defs: print('SEGDEF', s)
print('GROUPS', o.groups)
print('COMM', o.communals)
print('PUB', o.publics)
for n,b in o.segments.items(): print('SEG', n, bytes(b).hex()[:80])
for f in o.linker_fixups: print('FIX', {k:f[k] for k in ('segment','offset','loc','target_kind','target','frame_kind','frame')})
