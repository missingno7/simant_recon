from pathlib import Path
import sys,difflib
ROOT=Path.cwd();sys.path.insert(0,str(ROOT/'tools'));import autosearch,modctx,modules,variants
name,path=sys.argv[1:3];ctx=modctx.resolve(func=name);ev=autosearch.Evaluator(ctx,name,1,ROOT/'build/workers/takeover/compare-cache');col={}
modules.verify_module(Path(path).read_text(),ctx.module_dict(extent=True),ev.claims,collect=col)
cb=autosearch.candidate_bytes(col['object'],ev.row,ctx.placements)
x=autosearch.insns(ev.orig);y=autosearch.insns(cb)
print('original',len(ev.orig),'candidate',len(cb))
print('\n'.join(difflib.unified_diff(x,y,fromfile='original',tofile='candidate',n=4)))
