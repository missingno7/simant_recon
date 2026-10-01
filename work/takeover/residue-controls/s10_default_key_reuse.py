from pathlib import Path
import sys,json,itertools
ROOT=Path.cwd();sys.path.insert(0,str(ROOT/'tools'));import csrc,autosearch,modctx
name='o10_35F5_0384';ctx=modctx.resolve(func=name);text=autosearch.unscaffold(ctx.text,name);f=csrc.Source(text).function(name);b=text[f.body.s:f.body.e];out=ROOT/'build/workers/takeover/s10-default-key-reuse';out.mkdir(exist_ok=True);vs=[];meta=[]
for reuse,initial,volatileold,chain in itertools.product([False,True],['t','j'],[False,True],range(4)):
 bb=b
 if reuse:
  bb=bb.replace('                  old = k;\n                  if (key & 0x800)', '                  old = k;\n                  k = key;\n                  if (k & 0x800)').replace('if (!isalpha(key))','if (!isalpha(k))')
 bb=bb.replace('                  k = t;', '                  k = '+initial+';')
 if volatileold:bb=bb.replace('    int old;', '    volatile int old;')
 if chain&1:bb=bb.replace('old = maxLen = i = 0;', 'i = maxLen = old = 0;')
 if chain&2:bb=bb.replace('result = down = 0;', 'down = result = 0;')
 vs.append(text[:f.body.s]+bb+text[f.body.e:]);meta.append([reuse,initial,volatileold,chain])
ev=autosearch.Evaluator(ctx,name,4,out/'cache');rows=[]
for i,(t,r) in enumerate(zip(vs,ev.many(vs))):
 (out/f'v{i}.c').write_text(t);rows.append({'name':f'v{i}','meta':meta[i],**r})
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1));print('variants',len(rows),'exact',sum(bool(r.get('all_exact')) for r in rows));print([(r['name'],r.get('meta'),r.get('score'),r.get('length')) for r in sorted(rows,key=lambda r:r.get('score',[9]))[:10]])
