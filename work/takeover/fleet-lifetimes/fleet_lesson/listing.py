from pathlib import Path
import sys, struct
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'tools'))
sys.path.insert(0, 'C:/tools/capstone-5.0.3')
import exe, functions
from capstone import Cs, CS_ARCH_X86, CS_MODE_16
f = functions.get('LessonDone')
base, unit = exe.load().unit_bytes(f['unit'])
lin = f['seg'] * 16 + f['off']
b = unit[lin-base:lin-base+f['size']]
md = Cs(CS_ARCH_X86, CS_MODE_16)
print(f'{f["name"]} {f["unit"]}:{f["seg"]:04X}:{f["off"]:04X} size={len(b)}')
print('switch table bytes [001E,008E), words:')
words=struct.unpack_from('<56H', b, 0x1e)
for i in range(0,56,4):
 print('  '+', '.join(f'{j+1:02d}:{v:04X}' for j,v in enumerate(words[i:i+4],i)))
print('CODE before table:')
for ins in md.disasm(b[:0x1e], f['off']): print(f'  {ins.address:04X} {ins.bytes.hex():<20} {ins.mnemonic:<8} {ins.op_str}')
print('CODE after table:')
for ins in md.disasm(b[0x8e:], f['off']+0x8e): print(f'  {ins.address:04X} {ins.bytes.hex():<20} {ins.mnemonic:<8} {ins.op_str}')
print('FUNCTION TAIL bytes',b[-32:].hex())
print('fixups',sorted(x-lin for x in exe.load().reloc_sites(f['unit']) if lin <= x < lin+len(b)))
