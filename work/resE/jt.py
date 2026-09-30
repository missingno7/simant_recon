"""jt.py FUNC SRC.c TABLEOFF NCASES [LOW] : compile SRC with the module's manifest flags, take the
function's full candidate bytes from the object (not truncated to the target), decode the switch
jump table in candidate and original, print case -> block, then (CODE=1) the code after the table."""
import sys, os, json, itertools
sys.path.insert(0, 'D:/Prog/simant_recon/tools')
import search, compiler, exe
import functions as fnmod
from omf import OmfReader
func, src = sys.argv[1], sys.argv[2]
toff = int(sys.argv[3], 16); n = int(sys.argv[4]); lo = int(sys.argv[5]) if len(sys.argv) > 5 else 1
f = fnmod.get(func)
man = json.load(open('D:/Prog/simant_recon/layout/manifest.json'))['modules'][f"{f['unit']}:{f['seg']:04X}"]
r = compiler.compile_c(open(src, encoding='latin1').read(), man['profile'], man['flags'])
if not r.ok:
    print(r.log); sys.exit(1)
obj = OmfReader(communals=True).read(r.obj)
pub = [p for p in obj.publics + obj.local_publics if p['name'] == '_' + func][0]
seg = bytes(obj.segments[pub['segment']])
starts = sorted(p['offset'] for p in obj.publics + obj.local_publics if p['segment'] == pub['segment'])
nxt = [s for s in starts if s > pub['offset']]
cand = seg[pub['offset']:(nxt[0] if nxt else len(seg))]
orig = exe.load().read(f['unit'], f['seg'] * 16 + f['off'], f['size'])
print('candidate length', len(cand), 'original', len(orig))
def tab(b):
    o = toff - f['off']
    return [int.from_bytes(b[o + 2 * i:o + 2 * i + 2], 'little') for i in range(n)]
# candidate table is relative to its own function start at f['off'] (same origin)
delta = f['off'] - pub['offset']
ta = [x + delta for x in tab(cand)]; tb = tab(orig)
for i, (a, b) in enumerate(zip(ta, tb)):
    if a != b or os.environ.get('ALL'):
        print('case %2d: cand %04X orig %04X %s' % (i + lo, a, b, '' if a == b else '!'))
end = toff + 2 * n
if os.environ.get('CODE'):
    a = search.disasm(cand[end - f['off']:], end); b = search.disasm(orig[end - f['off']:], end)
    for x, y in itertools.zip_longest(a, b):
        l = f"{x[0]:04X} {x[2]}" if x else ""; rr = f"{y[0]:04X} {y[2]}" if y else ""
        print(f"{' ' if (x and y and x[1] == y[1]) else '!'} {l:<46}| {rr}")
