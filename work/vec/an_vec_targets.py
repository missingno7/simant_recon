"""For every vector: all far references through it (by kind and referencing unit), and every far
reference in the image that addresses a vectored procedure's (seg:off) *directly*."""
import sys, struct, collections
sys.path.insert(0, 'tools')
import exe
x = exe.load()
M = exe.MANAGER_SEG
vec = {v.offset: v for v in x.vectors}
by_addr = collections.defaultdict(list)
for v in x.vectors: by_addr[(v.target_seg, v.target_off)].append(v)
via = collections.defaultdict(collections.Counter)
direct = []
kinds = collections.Counter()
for u in x.units():
    base, data = x.unit_bytes(u)
    for sg, o in x.unit_relocs(u):
        lin = sg*16+o; i = lin-base
        if u == 'root' and M*16 + 0x25F6 <= lin < M*16 + 0x25F6 + 10*len(x.vectors): continue
        val = struct.unpack_from('<H', data, i)[0]
        if u == 'S27': kind, ow = 'data', struct.unpack_from('<H', data, i-2)[0]
        elif i >= 3 and data[i-3] == 0x9A: kind, ow = 'call', struct.unpack_from('<H', data, i-2)[0]
        elif i >= 3 and data[i-3] == 0xEA: kind, ow = 'jmp', struct.unpack_from('<H', data, i-2)[0]
        elif i >= 4 and data[i-1] == 0xBA and data[i-4] == 0xB8: kind, ow = 'addr', struct.unpack_from('<H', data, i-3)[0]
        else: continue
        if val == M and ow in vec:
            via[ow][(kind, 'root' if u == 'root' else 'ovl')] += 1; kinds[kind] += 1
        elif (val, ow) in by_addr:
            direct.append((u, sg, o, kind, val, ow, [v.unit for v in by_addr[(val, ow)]]))
for v in x.vectors:
    print(f"{v.offset:04X} {v.unit:4s} {v.target_seg:04X}:{v.target_off:04X} via {dict(via[v.offset])}")
print("references through vectors by kind:", dict(kinds), "total", sum(kinds.values()))
print("direct far references to an address that some vector targets:")
for d in direct:
    u, sg, o, kind, val, ow, units = d
    print(f"  {u}:{sg:04X}:{o:04X} {kind} -> {val:04X}:{ow:04X}  vector section(s) {units}  {'SAME SECTION' if u in units else 'other section'}")
