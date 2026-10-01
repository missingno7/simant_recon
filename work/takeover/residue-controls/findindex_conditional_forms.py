from pathlib import Path
import sys,json,itertools
ROOT=Path.cwd();sys.path.insert(0,str(ROOT/'tools'));import csrc,autosearch,modctx
name='FindIndex';ctx=modctx.resolve(func=name);text=autosearch.unscaffold(ctx.text,name);f=csrc.Source(text).function(name);b=text[f.body.s:f.body.e];out=ROOT/'build/workers/takeover/findindex-conditional-forms';out.mkdir(exist_ok=True);vs=[];meta=[]
k='fd_50F6_3952->kind';ident='fd_50F6_3952->id';expr=f'{k} > kind || ({k} == kind && {ident} >= id)'
forms=[f'{k} == kind ? {ident} >= id : {k} > kind', f'{k} != kind ? {k} > kind : {ident} >= id', f'{k} > kind ? 1 : ({k} == kind ? {ident} >= id : 0)', f'{k} < kind ? 0 : ({k} == kind ? {ident} >= id : 1)', f'!({k} < kind || ({k} == kind && {ident} < id))', f'{k} >= kind && ({k} > kind || {ident} >= id)',f'{k} > kind || ({k} != kind ? 0 : {ident} >= id)',f'{k} <= kind ? ({k} == kind && {ident} >= id) : 1']
for condition,qual in itertools.product(forms,['','id','kind','both']):
 t=text[:f.body.s]+b.replace(expr,condition)+text[f.body.e:]
 if qual in ['id','both']:t=t.replace('FindIndex(int db, int id, int kind)','FindIndex(int db, volatile int id, int kind)')
 if qual in ['kind','both']:t=t.replace('int id, int kind)','int id, volatile int kind)')
 vs.append(t);meta.append([condition,qual])
ev=autosearch.Evaluator(ctx,name,4,out/'cache');rows=[]
for i,(t,r) in enumerate(zip(vs,ev.many(vs))):
 (out/f'v{i}.c').write_text(t);rows.append({'name':f'v{i}','meta':meta[i],**r})
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1));print('variants',len(rows),'exact',sum(bool(r.get('all_exact')) for r in rows));print([(r['name'],r.get('score'),r.get('length')) for r in sorted(rows,key=lambda r:r.get('score',[9]))[:10]])
