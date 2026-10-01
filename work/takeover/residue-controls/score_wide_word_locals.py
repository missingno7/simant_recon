from pathlib import Path
import sys,json,itertools,re
ROOT=Path.cwd();sys.path.insert(0,str(ROOT/'tools'));import csrc,autosearch,modctx
name='CalcScore';ctx=modctx.resolve(func=name);text=autosearch.unscaffold(ctx.text,name);f=csrc.Source(text).function(name);b=text[f.body.s:f.body.e];out=ROOT/'build/workers/takeover/score-wide-word-locals';out.mkdir(exist_ok=True);vs=[]
for jtype,stype in itertools.product(['int','long','unsigned long'],repeat=2):
 bb=b.replace('    int i, j, k, n, t;', '    int i, k, n, t;\n    '+jtype+' j;').replace('    int sum, sum2;', '    int sum;\n    '+stype+' sum2;')
 for v,ty in [('j',jtype),('sum2',stype)]:
  if ty=='int':continue
  at=bb.index('    for (i = 0;');prefix=bb[:at];body=re.sub(r'\b'+v+r'\b','(int)'+v,bb[at:]);body=re.sub(r'\(int\)'+v+r'(?=\s*(?:=(?!=)|\+=))',v,body)
  # These loop counters consume only the signed low word, including wraparound.
  if v=='j':body=body.replace('(int)j++','j = (int)j + 1')
  else:body=body.replace('sum2 += fd_50F6_06AE[(int)j];','sum2 = (int)((int)sum2 + fd_50F6_06AE[(int)j]);').replace('sum2 += fd_50F6_06AE[j];','sum2 = (int)((int)sum2 + fd_50F6_06AE[j]);')
  bb=prefix+body
 vs.append(text[:f.body.s]+bb+text[f.body.e:])
ev=autosearch.Evaluator(ctx,name,4,out/'cache');rows=[]
for i,(t,r) in enumerate(zip(vs,ev.many(vs))):
 (out/f'v{i}.c').write_text(t);rows.append({'name':f'v{i}',**r})
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1));print('variants',len(rows),'exact',sum(bool(r.get('all_exact')) for r in rows));print([(r['name'],r.get('score'),r.get('length')) for r in rows])
