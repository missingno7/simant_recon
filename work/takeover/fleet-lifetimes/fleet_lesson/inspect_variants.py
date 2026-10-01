from pathlib import Path
import sys,struct
root=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(root/'tools'));sys.path.insert(0,'C:/tools/capstone-5.0.3')
import exe,functions,modctx,modules,variants,autosearch
from capstone import Cs,CS_ARCH_X86,CS_MODE_16
name='LessonDone';ctx=modctx.resolve(func=name);row=functions.get(name);claims=variants.check_set(ctx,[name],claims_only=True);md=Cs(CS_ARCH_X86,CS_MODE_16)
origx=exe.load();lin=row['seg']*16+row['off'];base,unit=origx.unit_bytes(row['unit']);orig=unit[lin-base:lin-base+row['size']]
print('EXPECTED table:',','.join(f'{x:04X}' for x in struct.unpack_from('<56H',orig,0x1e)))
for nm in ['base','case54_shared_return','case54_nested_switch_returns','case54_nested_switch_shared_return','case54_result_local_lifetime','outer_default_first','outer_default_last']:
 p=Path(__file__).with_name('round2-sources')/(nm+'.c'); text=p.read_text(encoding='latin1');col={};res=modules.verify_module(text,ctx.module_dict(extent=True),claims,collect=col)
 cb=autosearch.candidate_bytes(col['object'],row,ctx.placements) if col.get('object') else b''
 print('\n',nm,'len',len(cb),'exact',res.get('claims',{}).get(name,{}).get('exact'),'reasons',res.get('claims',{}).get(name,{}).get('reasons'))
 if len(cb)>=0x8e:
  words=struct.unpack_from('<56H',cb,0x1e)
  dif=[(i+1,words[i],struct.unpack_from('<H',orig,0x1e+2*i)[0]) for i in range(56) if words[i]!=struct.unpack_from('<H',orig,0x1e+2*i)[0]]
  print('table diffs',[(i,f'{a:04X}',f'{b:04X}') for i,a,b in dif[:20]],'n=',len(dif))
  print('first code')
  for ins in list(md.disasm(cb[0x8e:],row['off']+0x8e))[:26]:print(f' {ins.address:04X} {ins.mnemonic:<7} {ins.op_str}')
