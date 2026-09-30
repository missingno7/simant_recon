"""Enumerate RTLink vectors, every reference to them, and every far code pointer in the image."""
import sys, struct, json, collections
sys.path.insert(0, 'tools')
import exe
x = exe.load()
M = exe.MANAGER_SEG
syms = json.load(open('layout/symbols.json'))
name_at = {}
for k in ('code', 'runtime'):
    for n, r in syms[k].items():
        if r.get('alias_of'):
            continue
        name_at.setdefault((r.get('unit', 'root'), r['seg'], r['off']), n)
funcs = json.load(open('layout/functions.json'))['functions']
fstart = {(f['unit'], f['seg'], f['off']): f for f in funcs}

def nm(unit, seg, off):
    return name_at.get((unit, seg, off)) or (f"f_{seg:04X}_{off:04X}" if (unit, seg, off) in fstart else f"?{seg:04X}:{off:04X}")

def area_of(seg):
    if seg < 0x29F4: return 'game'
    if seg < 0x2CFB: return 'rt'
    if seg < 0x3126: return 'mgr'
    if seg < 0x3D57: return 'ovl'
    return 'data'

vec = {v.offset: v for v in x.vectors}
def vunit(v): return 'root' if v.section == 0xFFFF else f"S{v.section:02d}"

# classify each relocation site
refs = collections.defaultdict(list)      # vector offset -> list of (unit, site, kind)
ptrs = []                                   # far code pointers that are not call/jmp
def site_kind(data, i, base):
    """return (kind, offset_word) for the segment word at data[i]"""
    if i >= 3 and data[i-3] == 0x9A: return 'callfar', struct.unpack_from('<H', data, i-2)[0]
    if i >= 3 and data[i-3] == 0xEA: return 'jmpfar', struct.unpack_from('<H', data, i-2)[0]
    # mov dx,SEG preceded by mov ax,OFF
    if i >= 4 and data[i-1] == 0xBA and data[i-4] == 0xB8: return 'mov ax,off;mov dx,seg', struct.unpack_from('<H', data, i-3)[0]
    if i >= 1 and 0xB8 <= data[i-1] <= 0xBF: return f'mov r{data[i-1]-0xB8},seg', None
    if i >= 2 and data[i-2] == 0xC7: return 'mov m,seg', None
    return 'other', None

for u in x.units():
    base, data = x.unit_bytes(u)
    for sg, o in x.unit_relocs(u):
        lin = sg*16 + o; i = lin - base
        val = struct.unpack_from('<H', data, i)[0]
        ar = area_of(val)
        if ar not in ('game', 'rt', 'mgr', 'ovl'):
            continue
        if u == 'S27':
            kind, ow = 'data', struct.unpack_from('<H', data, i-2)[0]
        else:
            kind, ow = site_kind(data, i, base)
        if val == M and ow in vec:
            refs[ow].append((u, sg, o, kind))
        if kind not in ('callfar', 'jmpfar'):
            ptrs.append((u, sg, o, kind, val, ow))

rows = []
for v in x.vectors:
    tu = vunit(v)
    kinds = collections.Counter(r[3] for r in refs[v.offset])
    fromu = collections.Counter(r[0] for r in refs[v.offset])
    rows.append((v, tu, nm(tu, v.target_seg, v.target_off), kinds, fromu))
out = []
out.append(f"{len(x.vectors)} vectors")
for v, tu, n, kinds, fromu in rows:
    out.append(f"{v.offset:04X} {tu:4s} {v.target_seg:04X}:{v.target_off:04X} {n:28s} refs={sum(kinds.values())} {dict(kinds)} from={dict(fromu)}")
print("\n".join(out))
print()
print("== far code pointers that are not call/jmp far ==")
for u, sg, o, kind, val, ow in ptrs:
    tgt = ''
    if ow is not None:
        if val == M and ow in vec:
            v = vec[ow]; tgt = f"VECTOR {ow:04X} -> {vunit(v)} {nm(vunit(v), v.target_seg, v.target_off)}"
        else:
            tu = 'root' if val < 0x3126 else '?'
            tgt = nm(tu, val, ow) if val < 0x3126 else f"ovl {val:04X}:{ow:04X}"
    print(f"{u:4s} {sg:04X}:{o:04X} {kind:22s} seg={val:04X} off={'' if ow is None else f'{ow:04X}'} {tgt}")
