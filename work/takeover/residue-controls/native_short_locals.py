from pathlib import Path
import sys,json,itertools
ROOT=Path.cwd();sys.path.insert(0,str(ROOT/'tools'));import csrc,autosearch,modctx
allrows=[]
for name,path,decls in [('f_0250_129E','build/workers/takeover/mapdraw-coordinate-copies/v9.c',['ay','screenY','i']),('o15_384C_0239',None,['result'])]:
 text=Path(path).read_text() if path else autosearch.unscaffold(modctx.resolve(func=name).text,name);f=csrc.Source(text).function(name);b=text[f.body.s:f.body.e];out=ROOT/'build/workers/takeover'/('native-short-'+name);out.mkdir(exist_ok=True);vs=[]
 for mask in range(1<<len(decls)):
  bb=b
  for i,v in enumerate(decls):
   if mask&(1<<i):bb=bb.replace('    int '+v+';', '    short '+v+';')
  vs.append(text[:f.body.s]+bb+text[f.body.e:])
 ev=autosearch.Evaluator(modctx.resolve(func=name),name,4,out/'cache');rows=[]
 for i,(t,r) in enumerate(zip(vs,ev.many(vs))):
  (out/f'v{i}.c').write_text(t);rows.append({'name':f'v{i}',**r})
 ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1));print(name,'variants',len(rows),'exact',sum(bool(r.get('all_exact')) for r in rows));print([(r['name'],r.get('score'),r.get('length')) for r in rows])
