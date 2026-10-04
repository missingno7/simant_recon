"""Read-only historical startup disassembly; no executable bytes emitted."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'tools'))
import exe
from capstone import Cs, CS_ARCH_X86, CS_MODE_16
from omf import OmfReader

x = exe.load()
cs = Cs(CS_ARCH_X86, CS_MODE_16)
def listing(seg, start, end):
    return '\n'.join(f'{seg:04X}:{i.address:04X}  {i.mnemonic} {i.op_str}'
                     for i in cs.disasm(x.read('root', seg * 16 + start, end - start), start))

(OUT / 'original-manager-analysis.txt').write_text(listing(0x2cff, 0, 0xb5f), encoding='utf-8')
(OUT / 'original-manager-far-analysis.txt').write_text(listing(0x2fb3, 0, 0x176b), encoding='utf-8')
(OUT / 'original-manager-selected-analysis.txt').write_text('\n\n'.join(
    listing(seg, start, end) for seg, start, end in (
        (0x2cff, 0x1b0, 0x1b8), (0x2cff, 0x950, 0x9cb),
        (0x2fb3, 0x6f, 0x49f), (0x2fb3, 0x137d, 0x1449),
        (0x2fb3, 0x1449, 0x158a), (0x2fb3, 0x158a, 0x1760),
        (0x2fb3, 0x1245, 0x1279), (0x2fb3, 0x1290, 0x137d))), encoding='utf-8')
(OUT / 'original-cinit-analysis.txt').write_text(listing(0x29f4, 0x11c, 0x2a4), encoding='utf-8')
manifest = json.loads((ROOT / 'layout/manifest.json').read_bytes())
rows = []
for row in manifest['runtime']['members']:
    if any(t in row['member'].lower() for t in ('cinit', 'crt0', 'nmsghdr', 'xinit', 'crt0dat')):
        rows.append(row)
(OUT / 'runtime-startup-rows.json').write_text(json.dumps(rows, indent=2), encoding='utf-8')
rd = OmfReader(communals=True)
selected = []
for name, blob in rd.split_library(Path('C:/tools/msc-6.00/LIB/llibcr.lib').read_bytes()):
    ob = rd.read(blob, name)
    if any(p['name'] == '__cinit' for p in ob.publics):
        selected.append(dict(name=name, segments=ob.segment_lengths, publics=ob.publics,
                             externals=ob.externals, fixups=ob.linker_fixups))
(OUT / 'cinit-object-analysis.json').write_text(json.dumps(selected, indent=2), encoding='utf-8')
print(json.dumps(dict(manager_listing='written analysis only', startup_members=len(rows),
                     cinit_members=[r['name'] for r in selected],
                     relocation_overlap=[dict(unit=s.name, seg=seg, off=off)
                       for s in x.sections for seg, off in s.relocs
                       if seg*16+off < 0x55b30+0x8ba0 and seg*16+off+2 > 0x55b30+0x8b9d]), indent=2))
