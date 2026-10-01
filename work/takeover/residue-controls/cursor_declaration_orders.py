from pathlib import Path
import sys,json,itertools
ROOT=Path.cwd();sys.path.insert(0,str(ROOT/'tools'));import csrc,autosearch,modctx
name='DrawMapCursor';ctx=modctx.resolve(func=name);text=(ROOT/'build/workers/takeover/cursor-current-near.c').read_text();out=ROOT/'build/workers/takeover/cursor-declaration-orders';out.mkdir(exist_ok=True)
# Preserve the current canonical bodies; reproduce only the three reviewed header differences.
text=text.replace('f_171C_1A9E(long size, int kind, char far *name)', 'f_171C_1A9E(long, int, char far *)')
text=text.replace('extern int far fd_50F6_3856;\nextern int far fd_50F6_3858;', 'extern int far fd_50F6_3858;\nextern int far fd_50F6_3856;')
decls=['extern int far fd_50F6_0508[2];','extern struct Rect far fd_50F6_10D2;','extern struct Rect far fd_50F6_38C2;','extern int far fd_50F6_10DE;','extern int far fd_50F6_38C0;','extern int far fd_50F6_10E0;']
old='\n'.join(decls);assert old in text
ev=autosearch.Evaluator(ctx,name,8,out/'cache');rows=[];orders=list(itertools.permutations(decls))
for start in range(0,len(orders),40):
 vs=[text.replace(old,'\n'.join(ds),1) for ds in orders[start:start+40]]
 for i,(t,r) in enumerate(zip(vs,ev.many(vs)),start):
  (out/f'v{i}.c').write_text(t);rows.append({'name':f'v{i}','meta':list(orders[i]),**r})
 ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1));best=min((r for r in rows if r.get('score')),key=lambda r:r['score']);print('done',len(rows),'best',best['name'],best.get('score'),'exact',sum(bool(r.get('all_exact')) for r in rows),flush=True)
 if any(r.get('all_exact') for r in rows):break
