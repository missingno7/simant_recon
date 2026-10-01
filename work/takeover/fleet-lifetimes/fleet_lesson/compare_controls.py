from pathlib import Path
import sys,hashlib
root=Path(__file__).resolve().parents[3];sys.path.insert(0,str(root/'tools'))
import exe,functions,modctx,modules,variants,autosearch
ctx=modctx.resolve(func='LessonDone');row=functions.get('LessonDone');claims=variants.check_set(ctx,['LessonDone'],claims_only=True)
items=[('base',Path(__file__).with_name('round2-sources')/'base.c'),('outer_default_break',Path(__file__).with_name('round2-sources')/'outer_default_break.c'),('case54_shared_return',Path(__file__).with_name('round2-sources')/'case54_shared_return.c'),('case7_nested_only',Path(__file__).with_name('round5-sources')/'case7_nested_only.c')]
bs=[]
for nm,p in items:
 col={};r=modules.verify_module(p.read_text(encoding='latin1'),ctx.module_dict(extent=True),claims,collect=col);b=autosearch.candidate_bytes(col['object'],row,ctx.placements);bs.append(b);print(nm,len(b),hashlib.sha256(b).hexdigest())
for n,(a,b) in enumerate(zip(items,bs)):
 for m,(c,d) in enumerate(zip(items,bs)):
  if m>n:print(a[0],c[0], 'same_bytes',b==d)
