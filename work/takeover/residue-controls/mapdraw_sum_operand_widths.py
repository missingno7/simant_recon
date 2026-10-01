from pathlib import Path
import sys,json,itertools
ROOT=Path.cwd();sys.path.insert(0,str(ROOT/'tools'));import csrc,autosearch,modctx
name='f_0250_129E';ctx=modctx.resolve(func=name);text=(ROOT/'build/workers/takeover/mapdraw-coordinate-copies/v9.c').read_text();f=csrc.Source(text).function(name);b=text[f.body.s:f.body.e];out=ROOT/'build/workers/takeover/mapdraw-sum-operand-widths';out.mkdir(exist_ok=True);vs=[]
for wt,yt in itertools.product(['','unsigned','long','unsigned long'],repeat=2):
 world='fd_50F6_0508.y' if not wt else '('+wt+')fd_50F6_0508.y';y='screenY' if not yt else '('+yt+')screenY'
 bb=b.replace('ay = fd_50F6_0508.y + screenY;', 'ay = (int)('+world+' + '+y+');')
 vs.append(text[:f.body.s]+bb+text[f.body.e:])
ev=autosearch.Evaluator(ctx,name,4,out/'cache');rows=[]
for i,(t,r) in enumerate(zip(vs,ev.many(vs))):
 (out/f'v{i}.c').write_text(t);rows.append({'name':f'v{i}',**r})
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1));print('variants',len(rows),'exact',sum(bool(r.get('all_exact')) for r in rows));print([(r['name'],r.get('score'),r.get('length')) for r in rows])
