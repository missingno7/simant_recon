from pathlib import Path
import sys,struct,hashlib
root=Path(__file__).resolve().parents[3];sys.path.insert(0,str(root/'tools'))
import exe,functions,modctx,modules,variants,autosearch
ctx=modctx.resolve(func='LessonDone');row=functions.get('LessonDone');claims=variants.check_set(ctx,['LessonDone'],claims_only=True)
x=exe.load();lin=row['seg']*16+row['off'];ub,unit=x.unit_bytes(row['unit']);orig=unit[lin-ub:lin-ub+row['size']]
items=[('base',Path(__file__).with_name('base.c')),('case9_split_only',Path(__file__).with_name('case9_split_only.c'))]
for nm,p in items:
 t=p.read_text(encoding='latin1'); col={};res=modules.verify_module(t,ctx.module_dict(extent=True),claims,collect=col);b=autosearch.candidate_bytes(col['object'],row,ctx.placements)
 print(nm,'length',len(b),'sha256',hashlib.sha256(b).hexdigest(),'reasons',res['claims']['LessonDone']['reasons'])
 print('  raw diffs prefix/table/body:',*[sum(1 for i in range(lo,min(hi,len(b),len(orig))) if orig[i]!=b[i]) for lo,hi in [(0,0x1e),(0x1e,0x8e),(0x8e,10000)]])
 if len(b)>=0x8e:
  ow=struct.unpack_from('<56H',orig,0x1e);cw=struct.unpack_from('<56H',b,0x1e)
  ds=[(i+1,f'{cw[i]:04X}',f'{ow[i]:04X}') for i in range(56) if cw[i]!=ow[i]]
  print('  table word diffs',len(ds),'first',ds[:12])
