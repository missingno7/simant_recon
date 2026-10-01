from pathlib import Path
import sys,json,itertools,re
ROOT=Path.cwd();sys.path.insert(0,str(ROOT/'tools'));import csrc,autosearch,modctx
name='DrawMapCursor';out=ROOT/'build/workers/takeover/cursor-scale-types';out.mkdir(exist_ok=True);vs=[]
for basekind,mask in itertools.product(['fresh','old'],range(16)):
 text=(ROOT/('build/workers/takeover/cursor-current-near.c' if basekind=='fresh' else 'work/takeover/full-search/DrawMapCursor/best.c')).read_text()
 for bit,var in [(1,'fd_50F6_3856'),(2,'fd_50F6_3858'),(4,'fd_50F6_10DE'),(8,'fd_50F6_10E0')]:
  if mask&bit:text=text.replace('extern int far '+var+';', 'extern unsigned int far '+var+';')
 vs.append(text)
ev=autosearch.Evaluator(modctx.resolve(func=name),name,4,out/'cache');rows=[]
for i,(t,r) in enumerate(zip(vs,ev.many(vs))):
 (out/f'v{i}.c').write_text(t);rows.append({'name':f'v{i}',**r})
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1));print('variants',len(rows),'exact',sum(bool(r.get('all_exact')) for r in rows));print([(r['name'],r.get('score'),r.get('length')) for r in sorted(rows,key=lambda r:r.get('score',[9]))[:8]])
