from pathlib import Path
import sys,json,itertools
ROOT=Path.cwd();sys.path.insert(0,str(ROOT/'tools'));import csrc,autosearch,modctx
name='DrawBalloons';text=autosearch.unscaffold((ROOT/'src/root/m0250.c').read_text(),name);f=csrc.Source(text).function(name);b=text[f.body.s:f.body.e];out=ROOT/'build/workers/takeover/balloons-allocation-size';out.mkdir(exist_ok=True);vs=[]
for typ,prod in itertools.product(['int','unsigned','long'],itertools.permutations(['ht','wt','rowbytes'])):
 bb=b.replace('    unsigned n;', '    '+typ+' n;').replace('n = ht * wt * rowbytes;', 'n = '+' * '.join(prod)+';')
 vs.append(text[:f.body.s]+bb+text[f.body.e:])
ev=autosearch.Evaluator(modctx.resolve(func=name),name,4,out/'cache');rows=[]
for i,(t,r) in enumerate(zip(vs,ev.many(vs))):
 (out/f'v{i}.c').write_text(t);rows.append({'name':f'v{i}',**r})
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1));print('variants',len(rows),'exact',sum(bool(r.get('all_exact')) for r in rows));print([(r['name'],r.get('score'),r.get('length')) for r in sorted(rows,key=lambda r:r.get('score',[9]))[:8]])
