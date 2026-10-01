from pathlib import Path
import sys,json,itertools
ROOT=Path.cwd();sys.path.insert(0,str(ROOT/'tools'));import csrc,autosearch,modctx
name='DisplayCard';ctx=modctx.resolve(func=name);text=autosearch.unscaffold(ctx.text,name);f=csrc.Source(text).function(name);b=text[f.body.s:f.body.e];out=ROOT/'build/workers/takeover/card-pointer-qualifiers';out.mkdir(exist_ok=True);vs=[];meta=[]
variables=['h1','h2','p','q','base','styles','styl','text','nul','hText','hStyl'];choices=[[]]+[[v] for v in variables]+[['base',v] for v in variables if v!='base']
for vspec in choices:
 bb=b
 for v in vspec:
  old=('struct StyleRun far *' if v=='styles' else 'int far *' if v=='styl' else 'char far *')+v+';';assert old in bb
  bb=bb.replace(old,old[:-len(v)-1]+' volatile '+v+';')
 vs.append(text[:f.body.s]+bb+text[f.body.e:]);meta.append(vspec)
ev=autosearch.Evaluator(ctx,name,4,out/'cache');rows=[]
for i,(t,r) in enumerate(zip(vs,ev.many(vs))):
 (out/f'v{i}.c').write_text(t);rows.append({'name':f'v{i}','meta':meta[i],**r})
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1));print('variants',len(rows),'exact',sum(bool(r.get('all_exact')) for r in rows));print([(r['name'],r.get('meta'),r.get('score'),r.get('length')) for r in sorted(rows,key=lambda r:r.get('score',[9]))[:10]])
