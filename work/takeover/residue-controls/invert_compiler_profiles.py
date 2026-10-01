from pathlib import Path
import sys,json
from dataclasses import replace
ROOT=Path.cwd();sys.path.insert(0,str(ROOT/'tools'));import csrc,autosearch,modctx
name='InvertPatch';ctx=modctx.resolve(func=name);text=autosearch.unscaffold(ctx.source.read_text(),name);f=csrc.Source(text).function(name);b=text[f.body.s:f.body.e];out=ROOT/'build/workers/takeover/invert-compiler-profiles';out.mkdir(exist_ok=True);rows=[]
vs=[]
for reg in [False,True]:
 for assoc in [False,True]:
  bb=b
  if reg:bb=bb.replace('int i, h, v;', 'int i; register int h, v;')
  if assoc:bb=bb.replace('x * 28 - y * 10 + fd_50F6_10D2.left;', 'x * 28 + (fd_50F6_10D2.left - y * 10);',1)
  vs.append(text[:f.body.s]+bb+text[f.body.e:])
for profile in ['msc600ax','msc600a','msc600a-c2l','msc600']:
 ev=autosearch.Evaluator(replace(ctx,profile=profile),name,4,out/('cache-'+profile))
 for i,(t,r) in enumerate(zip(vs,ev.many(vs))):
  n=profile+'-v'+str(i);(out/(n+'.c')).write_text(t);rows.append({'name':n,'profile':profile,**r})
 ev.save()
(out/'results.json').write_text(json.dumps(rows,indent=1));print('variants',len(rows),'exact',sum(bool(r.get('all_exact')) for r in rows));print([(r['name'],r.get('score'),r.get('length')) for r in sorted(rows,key=lambda r:r.get('score',[9]))[:8]])
