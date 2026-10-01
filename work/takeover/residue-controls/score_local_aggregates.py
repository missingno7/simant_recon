from pathlib import Path
import sys,json,itertools,re
ROOT=Path.cwd();sys.path.insert(0,str(ROOT/'tools'));import csrc,autosearch,modctx
name='CalcScore';ctx=modctx.resolve(func=name);text=autosearch.unscaffold(ctx.text,name);f=csrc.Source(text).function(name);b=text[f.body.s:f.body.e];out=ROOT/'build/workers/takeover/score-local-aggregates';out.mkdir(exist_ok=True);vs=[]
for pair,kind,reverse in itertools.product([('sum','sum2'),('sum2','j')],['array','struct'],[False,True]):
 variables=list(reversed(pair)) if reverse else list(pair)
 bb=b
 if 'j' in pair:bb=bb.replace('    int i, j, k, n, t;', '    int i, k, n, t;')
 bb=bb.replace('    int sum, sum2;', ('    int sum;' if 'sum' not in pair else ''))
 declaration='    int totals[2];' if kind=='array' else '    struct { int '+', '.join(variables)+'; } totals;'
 bb=bb.replace('    long score, q;',declaration+'\n    long score, q;')
 at=bb.index('    for (i = 0;');prefix=bb[:at];body=bb[at:]
 for i,v in enumerate(variables):body=re.sub(r'\b'+v+r'\b', 'totals['+str(i)+']' if kind=='array' else 'totals.'+v,body)
 vs.append(text[:f.body.s]+prefix+body+text[f.body.e:])
ev=autosearch.Evaluator(ctx,name,4,out/'cache');rows=[]
for i,(t,r) in enumerate(zip(vs,ev.many(vs))):
 (out/f'v{i}.c').write_text(t);rows.append({'name':f'v{i}',**r})
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1));print('variants',len(rows),'exact',sum(bool(r.get('all_exact')) for r in rows));print([(r['name'],r.get('score'),r.get('length')) for r in rows])
