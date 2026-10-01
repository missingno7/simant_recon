from pathlib import Path
import sys,json,re
ROOT=Path.cwd();sys.path.insert(0,str(ROOT/'tools'));import csrc,autosearch,modctx
jobs=[('f_0250_129E','mapdraw-coordinate-copies/v9.c'),('InvertPatch',None),('CalcScore',None),('o10_35F5_0384',None),('o15_384C_0239',None),('f_171C_0CF4','memcf4-result-lifetime/v6.c')]
for name,filename in jobs:
 ctx=modctx.resolve(func=name);text=autosearch.unscaffold(ctx.text,name)
 if filename:
  seed=(ROOT/'build/workers/takeover'/filename).read_text();sf=csrc.Source(seed).function(name);f=csrc.Source(text).function(name);text=text[:f.body.s]+seed[sf.body.s:sf.body.e]+text[f.body.e:]
 f=csrc.Source(text).function(name);head=text[f.head_s:f.body.s];prefix=head[:head.index(name)];out=ROOT/'build/workers/takeover'/('legacy-definition-'+name);out.mkdir(exist_ok=True);vs=[];meta=[]
 for style in ['ansi','kr']:
  for returntype in ['original','int_return'] if prefix.strip().startswith('void ') else ['original']:
   hp=prefix.replace('void ','int ',1) if returntype=='int_return' else prefix
   if style=='kr':h=hp+name+'('+', '.join(n for _,n in f.params)+')\n'+''.join(t+' '+n+';\n' for t,n in f.params)
   else:h=head.replace(prefix,hp,1)
   vs.append(text[:f.head_s]+h+text[f.body.s:]);meta.append([style,returntype])
 ev=autosearch.Evaluator(ctx,name,2,out/'cache');rows=[]
 for i,(t,r) in enumerate(zip(vs,ev.many(vs))):
  (out/f'v{i}.c').write_text(t);rows.append({'name':f'v{i}','meta':meta[i],**r})
 ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1));print(name,[(r['meta'],r.get('score'),r.get('length'),r.get('error')) for r in rows],flush=True)
