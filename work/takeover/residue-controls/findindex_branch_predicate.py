from pathlib import Path
import sys,json,itertools
ROOT=Path.cwd();sys.path.insert(0,str(ROOT/'tools'));import csrc,autosearch,modctx
name='FindIndex';ctx=modctx.resolve(func=name);text=autosearch.unscaffold(ctx.text,name);f=csrc.Source(text).function(name);b=text[f.body.s:f.body.e];out=ROOT/'build/workers/takeover/findindex-branch-predicate';out.mkdir(exist_ok=True);vs=[];meta=[]
k='fd_50F6_3952->kind';ident='fd_50F6_3952->id';expr=f'{k} > kind || ({k} == kind && {ident} >= id)'
forms=[expr,f'{k} < kind || ({k} == kind && {ident} < id)',f'{k} > kind || ({k} >= kind && {ident} >= id)',f'{k} < kind || ({k} <= kind && {ident} < id)']
for condition,typ,chain in itertools.product(forms,['int','unsigned char'],['local','assign','ternary']):
 lower=condition in forms[1::2];test='!direction' if lower else 'direction'
 bb=b.replace('    int top;', '    int top;\n    '+typ+' direction;')
 if chain=='local':replacement='direction = '+condition+';\n        if ('+test+')'
 elif chain=='assign':replacement='if ('+('!' if lower else '')+'(direction = '+condition+'))'
 else:replacement='direction = ('+condition+') ? 1 : 0;\n        if ('+test+')'
 bb=bb.replace('if ('+expr+')',replacement)
 vs.append(text[:f.body.s]+bb+text[f.body.e:]);meta.append([condition,typ,chain])
ev=autosearch.Evaluator(ctx,name,4,out/'cache');rows=[]
for i,(t,r) in enumerate(zip(vs,ev.many(vs))):
 (out/f'v{i}.c').write_text(t);rows.append({'name':f'v{i}','meta':meta[i],**r})
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1));print('variants',len(rows),'exact',sum(bool(r.get('all_exact')) for r in rows));print([(r['name'],r.get('score'),r.get('length')) for r in rows])
