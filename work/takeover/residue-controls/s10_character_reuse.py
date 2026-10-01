from pathlib import Path
import sys,json,itertools,re
ROOT=Path.cwd();sys.path.insert(0,str(ROOT/'tools'));import csrc,autosearch,modctx
name='o10_35F5_0384';ctx=modctx.resolve(func=name);text=autosearch.unscaffold(ctx.text,name);f=csrc.Source(text).function(name);b=text[f.body.s:f.body.e];out=ROOT/'build/workers/takeover/s10-character-reuse';out.mkdir(exist_ok=True);vs=[];meta=[]
for v,mask in itertools.product(['i','len','d','j'],range(8)):
 bb=b.replace('    int c;\n','');bb=re.sub(r'\bc\b',v,bb)
 if mask&1:bb=bb.replace('for (; items[i] != 0; i++)', 'for (; (unsigned)old >= 0 && items[i] != 0; i++)')
 if mask&2:bb=bb.replace('switch (key) {','switch ((unsigned)old >= 0 ? key : 0) {')
 if mask&4:bb=bb.replace('if (!isalpha(key))','if ((unsigned)j < 0 || !isalpha(key))')
 vs.append(text[:f.body.s]+bb+text[f.body.e:]);meta.append([v,mask])
ev=autosearch.Evaluator(ctx,name,4,out/'cache');rows=[]
for i,(t,r) in enumerate(zip(vs,ev.many(vs))):
 (out/f'v{i}.c').write_text(t);rows.append({'name':f'v{i}','meta':meta[i],**r})
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1));print('variants',len(rows),'exact',sum(bool(r.get('all_exact')) for r in rows));print([(r['name'],r.get('meta'),r.get('score'),r.get('length')) for r in sorted(rows,key=lambda r:r.get('score',[9]))[:10]])
