from pathlib import Path
import sys,json,itertools
from dataclasses import replace
ROOT=Path.cwd();sys.path.insert(0,str(ROOT/'tools'));import csrc,autosearch,modctx
name='f_284A_0138';ctx=modctx.resolve(func=name);text=autosearch.unscaffold(ctx.text,name);f=csrc.Source(text).function(name)
out=ROOT/'build/workers/takeover/midi-word-compiler-profiles';out.mkdir(exist_ok=True);vs=[];rows=[]
for expr in ['SONG(off) << 8 | SONG(off + 1)','SONG(off) * 256 + SONG(off + 1)','SONG(off + 1) + SONG(off) * 256']:
 for local in [False,True]:
  bb='{\n'+('    unsigned high = SONG(off);\n' if local else '')+'    return '+(expr.replace('SONG(off)','high') if local else expr)+';\n}'
  vs.append(text[:f.body.s]+bb+text[f.body.e:])
for profile in ['msc600ax','msc600a','msc600','msc510','qc250','qc251']:
 ev=autosearch.Evaluator(replace(ctx,profile=profile),name,4,out/('cache-'+profile))
 for i,(t,r) in enumerate(zip(vs,ev.many(vs))):
  n=profile+'-v'+str(i);(out/(n+'.c')).write_text(t);rows.append({'name':n,'profile':profile,**r})
 ev.save()
(out/'results.json').write_text(json.dumps(rows,indent=1));print('variants',len(rows),'exact',sum(bool(r.get('all_exact')) for r in rows));print([(r['name'],r.get('score'),r.get('length'),r.get('error')) for r in rows])
