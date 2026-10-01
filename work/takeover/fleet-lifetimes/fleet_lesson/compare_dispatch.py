from pathlib import Path
import sys,hashlib
root=Path(__file__).resolve().parents[3];sys.path.insert(0,str(root/'tools'))
import exe,functions,modctx,modules,variants,autosearch
ctx=modctx.resolve(func='LessonDone');row=functions.get('LessonDone');claims=variants.check_set(ctx,['LessonDone'],claims_only=True)
x=exe.load();lin=row['seg']*16+row['off'];ub,unit=x.unit_bytes(row['unit']);orig=unit[lin-ub:lin-ub+row['size']]
outs=[]
for nm in ['base','case0_based_expression']:
 t=(Path(__file__).with_name('round6-sources')/(nm+'.c')).read_text(encoding='latin1'); col={}; r=modules.verify_module(t,ctx.module_dict(extent=True),claims,collect=col); b=autosearch.candidate_bytes(col['object'],row,ctx.placements);outs.append(b)
 print(nm,len(b),hashlib.sha256(b).hexdigest(),sum(x!=y for x,y in zip(b,orig))+abs(len(b)-len(orig)),r['claims']['LessonDone']['reasons'])
print('candidate bytes identical?',outs[0]==outs[1])
