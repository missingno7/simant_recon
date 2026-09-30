"""Is vector allocation order = order of first reference (module link order)?"""
import sys, struct, collections, json
sys.path.insert(0, 'tools')
import exe
x = exe.load()
M = exe.MANAGER_SEG
vec = {v.offset: v for v in x.vectors}
syms = json.load(open('layout/symbols.json'))
name_at = {}
for k in ('code',):
    for n, r in syms[k].items():
        if not r.get('alias_of'): name_at.setdefault((r.get('unit'), r['seg'], r['off']), n)
first = {}
refs = collections.defaultdict(list)
order_units = x.units()
for ui, u in enumerate(order_units):
    base, data = x.unit_bytes(u)
    for ri, (sg, o) in enumerate(x.unit_relocs(u)):
        lin = sg*16+o; i = lin-base
        if M*16 + 0x25F6 <= lin < M*16 + 0x25F6 + 10*len(x.vectors): continue
        val = struct.unpack_from('<H', data, i)[0]
        if val != M: continue
        if i >= 3 and data[i-3] in (0x9A, 0xEA): ow = struct.unpack_from('<H', data, i-2)[0]
        elif i >= 4 and data[i-1] == 0xBA and data[i-4] == 0xB8: ow = struct.unpack_from('<H', data, i-3)[0]
        else: continue
        if ow in vec:
            refs[ow].append((ui, lin, ri, u, sg))
for v in x.vectors:
    r = sorted(refs[v.offset])
    ui, lin, ri, u, sg = r[0]
    nm = name_at.get((v.unit, v.target_seg, v.target_off), '?')
    print(f"{v.offset:04X} {v.unit:4s} {nm:26s} first-ref {u}:{sg:04X} (lin {lin:05X}, reloc#{ri}) all={[f'{a[3]}:{a[4]:04X}' for a in r]}")
