"""multi.py BASE.c FUNC SPEC.py: append renamed copies of FUNC (one per variant in SPEC's V, edits applied to
the function text only) to BASE, compile once with /Fc, print per copy: size and the listing lines matching
PATTERN (default 'es$'). Analysis only."""
import sys, re, shutil, runpy
sys.path.insert(0, 'tools')
import compiler

base, func, spec = sys.argv[1], sys.argv[2], sys.argv[3]
pat = sys.argv[4] if len(sys.argv) > 4 else r',es\s*$'
text = open(base, encoding='latin1').read()
lines = text.split('\n')
start = next(i for i, l in enumerate(lines) if re.match(r'^[A-Za-z].*\b' + func + r'\s*\(', l) and not l.rstrip().endswith(';'))
end = start
while lines[end] != '}':
    end += 1
ftext = '\n'.join(lines[start:end + 1])
V = runpy.run_path(spec)['V']
names = []
extra = []
for k, (name, edits) in enumerate(V.items()):
    t = ftext
    for old, new in edits:
        if old not in t:
            print('EDIT NOT FOUND', name, old[:60]); continue
        t = t.replace(old, new, 1)
    q = 'q%02d' % k
    t = t.replace(func, q, 1)
    names.append((q, name))
    extra.append(t)
src = text + '\n' + '\n\n'.join(extra) + '\n'
r = compiler.compile_c(src, 'msc600ax', ['/AL', '/Oeg', '/Gs', '/Zi', '/Fc'], keep=True)
cod = None
for p in r.workdir.iterdir():
    if p.suffix.upper() == '.COD':
        cod = p.read_text(encoding='latin1')
if cod is None:
    print(r.log[-1500:]); sys.exit(1)
procs = {}
cur = None
for line in cod.splitlines():
    m = re.match(r'^_(\w+)\s+PROC', line)
    if m:
        cur = m.group(1); procs[cur] = []
        continue
    if cur and re.match(r'^_\w+\s+ENDP', line):
        cur = None
    if cur and '***' in line:
        procs[cur].append(line)
def size(ls):
    offs = [int(l.split()[1], 16) for l in ls]
    return offs[-1] - offs[0] + len(l.split('\t')[2].split()) if ls else 0
for fn in [func] + [q for q, _ in names]:
    ls = procs.get(fn, [])
    label = dict(names).get(fn, 'orig-draft')
    hits = [re.sub(r'\s+', ' ', l.split('\t', 3)[-1]) for l in ls if re.search(pat, l)]
    first = int(ls[0].split()[1], 16) if ls else 0
    last = ls[-1] if ls else ''
    n = (int(last.split()[1], 16) - first + len(last.split('\t')[2].split())) if ls else 0
    print('%-6s %-24s size %4d  %s' % (fn, label[:24], n, ' | '.join(hits)))
shutil.rmtree(r.workdir, ignore_errors=True)
