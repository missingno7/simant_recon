"""Bind f_00BA_0002 drafts with the patched binder and report the vector bindings + first mismatch.
usage: python work/vec/run_patched.py work/vec/check00BA.py DRAFT.c [DRAFT2.c ...]"""
import sys
sys.path.insert(0, 'tools')
import compiler, match
from omf import OmfReader
t = match.Target('root', 0xBA, 2, 436)
for p in sys.argv[1:]:
    r = compiler.compile_c(open(p).read(), 'msc600ax', ['/AL', '/Os', '/Oe', '/Og', '/Zi'])
    obj = OmfReader(communals=True).read(r.obj)
    seg = next(s for s in obj.segments if s.endswith('_TEXT'))
    res = match.Binder(t, obj, seg, '_f_00BA_0002',
                       placements={'_DATA': {'seg': 0x55B3, 'off': 0x1852}, 'CONST': {'seg': 0x55B3, 'off': 0x7DF6}}).bind()
    print(f"== {p}: {res.summary()}")
    for rec in res.fixups:
        if 'via_vector' in rec or rec['kind'] == 'code' and rec['loc'] != 'pointer32':
            print(f"   +{rec['at']:#06x} {rec['loc']:16s} {rec['target']:24s} via_vector={rec.get('via_vector')}")
    fd = res.first_diff
    print(f"   first differing byte +{fd:#x}" if fd is not None else "   bytes equal")
    # bytes equal before the residue at +0x123 (except the jmp displacement at +0xd0 that the residue shifts)
    pre = [i for i in range(0x123) if res.candidate[i] != res.original[i]]
    print(f"   differing bytes before +0x123: {[hex(i) for i in pre]}")
    exp = [a for a in res.relocs_expected if a < t.linear + 0x123]
    cand = [a for a in res.relocs_candidate if a < t.linear + 0x123]
    print(f"   relocation sites before +0x123: expected {len(exp)}, candidate {len(cand)}, set equal {sorted(exp) == sorted(cand)}")
