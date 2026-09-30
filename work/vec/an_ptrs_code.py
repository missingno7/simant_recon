"""Every relocated segment word in CODE (root game/runtime/manager, overlays) whose value is a code
frame (game 0000-29F3, runtime 29F4, manager 2CFB-3125 incl. vectors, overlay areas 3126-3D56) and
which is not the segment of a far call/jmp: disassemble the containing instruction in context."""
import sys, struct, json, bisect, collections
sys.path.insert(0, 'tools')
import exe
from capstone import Cs, CS_ARCH_X86, CS_MODE_16
md = Cs(CS_ARCH_X86, CS_MODE_16)
x = exe.load()
funcs = json.load(open('layout/functions.json'))['functions']
byunit = collections.defaultdict(list)
for f in funcs:
    byunit[f['unit']].append((f['seg']*16+f['off'], f))
for u in byunit: byunit[u].sort(key=lambda t: t[0])
def area(seg):
    return 'game' if seg < 0x29F4 else 'rt' if seg < 0x2CFB else 'mgr' if seg < 0x3126 else 'ovl' if seg < 0x3D57 else 'data'
def func_at(u, lin):
    L = byunit.get(u, [])
    k = bisect.bisect_right([a for a, _ in L], lin) - 1
    if k >= 0:
        a, f = L[k]
        if a <= lin < a + f['size']: return f
    return None
vec = {v.offset: v for v in x.vectors}
for u in x.units():
    if u == 'S27': continue
    base, data = x.unit_bytes(u)
    rs = x.unit_relocs(u)
    sites = {sg*16+o for sg, o in rs}
    for sg, o in rs:
        lin = sg*16+o; i = lin-base
        val = struct.unpack_from('<H', data, i)[0]
        if area(val) == 'data': continue
        if i >= 3 and data[i-3] in (0x9A, 0xEA): continue
        f = func_at(u, lin)
        where = area(sg)
        if f is None:
            print(f"{u} {sg:04X}:{o:04X} [{where}] val={val:04X}  (no inventoried function)")
            # show raw hex
            print("    ", data[i-6:i+4].hex())
            continue
        fl = f['seg']*16+f['off']
        off = fl; ins_list = []
        while off < fl + f['size']:
            ins = list(md.disasm(data[off-base:off-base+16], off - sg*16, 1))
            if not ins: off += 1; continue
            ins_list.append((off, ins[0])); off += ins[0].size
        k = next((k for k, (a, ii) in enumerate(ins_list) if a <= lin < a+ii.size), None)
        nm = f"f_{f['seg']:04X}_{f['off']:04X}"
        print(f"{u} {sg:04X}:{o:04X} [{where}] val={val:04X} in {nm}")
        if k is None:
            print("     (site not on an instruction boundary)"); continue
        for a, ii in ins_list[max(0, k-3):k+3]:
            mark = '>>' if a <= lin < a+ii.size else '  '
            print(f"   {mark} {ii.address:04X} {ii.bytes.hex():18s} {ii.mnemonic} {ii.op_str}")
