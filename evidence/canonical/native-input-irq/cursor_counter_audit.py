from pathlib import Path
import sys,json,re,hashlib
sys.path.insert(0,str(Path('tools').resolve()));import exe,functions
from capstone import Cs,CS_ARCH_X86,CS_MODE_16
from capstone.x86 import X86_OP_MEM,X86_OP_IMM,X86_REG_DS
x=exe.load();md=Cs(CS_ARCH_X86,CS_MODE_16);md.detail=True;direct=[];immediates=[];seen=set()
for r in functions.table()['functions']:
 if not r.get('size'):continue
 try:base,data=x.unit_bytes(r['unit'])
 except (KeyError,ValueError):continue
 lin=r['seg']*16+r['off']
 for i in md.disasm(data[lin-base:lin-base+r['size']],lin):
  key=(r['unit'],i.address)
  if key in seen:continue
  seen.add(key)
  for op in i.operands:
   if op.type==X86_OP_MEM and op.mem.segment in (0,X86_REG_DS) and op.mem.base==op.mem.index==0 and 0x434e<=op.mem.disp<0x4356:
    direct.append(dict(unit=r['unit'],function=functions.name_of(r['unit'],r['seg'],r['off']),address=hex(i.address),instruction=i.mnemonic+' '+i.op_str,bytes=i.bytes.hex()))
   if op.type==X86_OP_IMM and 0x434e<=op.imm<0x4356:immediates.append(dict(unit=r['unit'],address=hex(i.address),instruction=i.mnemonic+' '+i.op_str))
refs=[]
for p in Path('src').rglob('*'):
 if p.suffix not in ('.c','.h','.asm'):continue
 for n,line in enumerate(p.read_text().splitlines(),1):
  if re.search(r'\bg_43(?:4E|52)\b|_g_43(?:4E|52)\b',line):refs.append(dict(path=p.as_posix(),line=n,text=line))
report=dict(original_sha256=hashlib.sha256(Path('assets/SIMANT.EXE').read_bytes()).hexdigest(),instructions_examined=len(seen),direct_dgroup_references=direct,address_immediate_candidates=immediates,canonical_source_references=refs,
 conclusion='Only the four INC words access these two counters directly in the indexed original functions. Their flags carry the counter increment only; no ordinary canonical reader or address materialization was found. This supports a presentation call-counter classification proposal; arbitrary dynamic aliasing is not proven absent by this census.')
Path('evidence/canonical/native-input-irq/cursor-counter-audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
