"""Markdown classification table of the 136 RTLink vectors."""
import sys, struct, json, collections
sys.path.insert(0, 'tools')
import exe
x = exe.load(); M = exe.MANAGER_SEG
vec = {v.offset: v for v in x.vectors}
syms = json.load(open('layout/symbols.json'))
name_at = {}
for n, r in syms['code'].items():
    if not r.get('alias_of'): name_at.setdefault((r.get('unit'), r['seg'], r['off']), n)
refs = collections.defaultdict(list)
for u in x.units():
    if u == 'S27': continue
    base, data = x.unit_bytes(u)
    for sg, o in x.unit_relocs(u):
        lin = sg*16+o; i = lin-base
        if u == 'root' and M*16+0x25F6 <= lin < M*16+0x25F6+10*len(x.vectors): continue
        if struct.unpack_from('<H', data, i)[0] != M: continue
        if data[i-3] in (0x9A, 0xEA): k, ow = ('call' if data[i-3] == 0x9A else 'jmp'), struct.unpack_from('<H', data, i-2)[0]
        elif data[i-1] == 0xBA and data[i-4] == 0xB8: k, ow = 'addr', struct.unpack_from('<H', data, i-3)[0]
        else: continue
        if ow in vec: refs[ow].append((k, u, sg))
cls = collections.Counter()
print("| vector | section | target | name | references (kind: referencing units) | class |")
print("|---|---|---|---|---|---|")
for v in x.vectors:
    r = refs[v.offset]
    by = collections.defaultdict(collections.Counter)
    for k, u, sg in r: by[k][u] += 1
    desc = "; ".join(f"{k}: " + ", ".join(f"{u}x{n}" if n > 1 else u for u, n in sorted(c.items())) for k, c in by.items())
    if any(k == 'addr' for k, _, _ in r):
        c = 'A: address-taken hook, root target' if v.unit == 'root' else 'A: address-taken hook, overlay target'
    elif v.offset <= 0x26A0:
        c = 'B: display-driver entry called from root 205F'
    else:
        units = {u for _, u, _ in r}
        c = 'C: cross-section call' + (' (root callers only)' if units == {'root'} else ' (overlay callers only)' if 'root' not in units else ' (root + overlay callers)')
    cls[c] += 1
    nm = name_at.get((v.unit, v.target_seg, v.target_off), '?')
    print(f"| {v.offset:04X} | {v.unit} | {v.target_seg:04X}:{v.target_off:04X} | {nm} | {desc} | {c.split(':')[0]} |")
print()
for c, n in sorted(cls.items()): print(f"* {c}: {n}")
