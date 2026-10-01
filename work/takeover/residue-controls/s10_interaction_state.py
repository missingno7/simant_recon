from pathlib import Path
import sys,json,itertools,re
ROOT=Path.cwd();sys.path.insert(0,str(ROOT/'tools'));import csrc,autosearch,modctx
name='o10_35F5_0384';ctx=modctx.resolve(func=name);text=autosearch.unscaffold(ctx.text,name);f=csrc.Source(text).function(name);b=text[f.body.s:f.body.e];out=ROOT/'build/workers/takeover/s10-interaction-state';out.mkdir(exist_ok=True);vs=[];meta=[]
variables=['j','t','key','old','cur'];orders=list(itertools.permutations(variables));orders.insert(0,tuple(reversed(variables)));orders=list(dict.fromkeys(orders))
for order in orders:
 bb=b
 for v in variables:bb=bb.replace('    int '+v+';\n','')
 at=bb.index('    cur = -1;');prefix=bb[:at];body=bb[at:]
 for v in variables:body=re.sub(r'\b'+v+r'\b','interaction.'+v,body)
 declaration='    struct { int '+', '.join(order)+'; } interaction;\n'
 bb=prefix.replace('{\n','{\n'+declaration,1)+body
 vs.append(text[:f.body.s]+bb+text[f.body.e:]);meta.append(list(order))
ev=autosearch.Evaluator(ctx,name,8,out/'cache');rows=[]
for start in range(0,len(vs),20):
 for i,(t,r) in enumerate(zip(vs[start:start+20],ev.many(vs[start:start+20])),start):
  (out/f'v{i}.c').write_text(t);rows.append({'name':f'v{i}','meta':meta[i],**r})
 ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1));best=min((r for r in rows if r.get('score')),key=lambda r:r['score']);print('done',len(rows),'best',best['name'],best.get('score'),best.get('length'),'exact',sum(bool(r.get('all_exact')) for r in rows),flush=True)
 if any(r.get('all_exact') for r in rows):break
