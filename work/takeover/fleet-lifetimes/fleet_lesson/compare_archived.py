from pathlib import Path
import sys,hashlib
root=Path(__file__).resolve().parents[3];sys.path.insert(0,str(root/'tools'))
import functions,modctx,modules,variants,autosearch
ctx=modctx.resolve(func='LessonDone');row=functions.get('LessonDone');claims=variants.check_set(ctx,['LessonDone'],claims_only=True)
paths=[('archived',root/'work/takeover/full-search/LessonDone/best.c'),('current_reproduction',Path(__file__).with_name('case9_split_only.c'))];bs=[]
for nm,p in paths:
 col={};r=modules.verify_module(p.read_text(encoding='latin1'),ctx.module_dict(extent=True),claims,collect=col);b=autosearch.candidate_bytes(col['object'],row,ctx.placements);bs.append(b);print(nm,'len',len(b),'sha256',hashlib.sha256(b).hexdigest(),'result',r['claims']['LessonDone']['reasons'])
print('bound_function_bytes_identical',bs[0]==bs[1])
