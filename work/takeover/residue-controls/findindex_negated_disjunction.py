from pathlib import Path
import sys,json,itertools
ROOT=Path.cwd();sys.path.insert(0,str(ROOT/'tools'));import csrc,autosearch,modctx
name='FindIndex';ctx=modctx.resolve(func=name);text=autosearch.unscaffold(ctx.text,name);f=csrc.Source(text).function(name);b=text[f.body.s:f.body.e];out=ROOT/'build/workers/takeover/findindex-negated-disjunction';out.mkdir(exist_ok=True);vs=[];meta=[]
k='fd_50F6_3952->kind';ident='fd_50F6_3952->id';expr=f'{k} > kind || ({k} == kind && {ident} >= id)'
forms=[f'{k} > kind || !({k} != kind || {ident} < id)',f'{k} > kind || !({k} == kind ? {ident} < id : 1)',f'{k} > kind || ({k} == kind && !({ident} < id))',f'!({k} <= kind && ({k} != kind || {ident} < id))',f'!({k} > kind ? 0 : ({k} != kind || {ident} < id))',f'{k} > kind ? 1 : !({k} != kind || {ident} < id)',f'{k} > kind || ({k} != kind ? 0 : !({ident} < id))',f'{k} > kind || ({k} != kind ? 0 : {ident} >= id)']
for condition,invert in itertools.product(forms,[False,True]):
 bb=b.replace(expr,condition)
 if invert:
  bb=bb.replace('if ('+condition+')\n            top = mid - 1;\n        else\n            fd_50F6_3956 = mid + 1;', 'if (!('+condition+'))\n            fd_50F6_3956 = mid + 1;\n        else\n            top = mid - 1;')
 vs.append(text[:f.body.s]+bb+text[f.body.e:]);meta.append([condition,invert])
ev=autosearch.Evaluator(ctx,name,4,out/'cache');rows=[]
for i,(t,r) in enumerate(zip(vs,ev.many(vs))):
 (out/f'v{i}.c').write_text(t);rows.append({'name':f'v{i}','meta':meta[i],**r})
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1));print('variants',len(rows),'exact',sum(bool(r.get('all_exact')) for r in rows));print([(r['name'],r.get('score'),r.get('length')) for r in rows])
