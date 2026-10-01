from pathlib import Path
import sys,json,itertools
ROOT=Path.cwd();sys.path.insert(0,str(ROOT/'tools'));import csrc,autosearch,modctx
name='o15_384C_0239';text=autosearch.unscaffold(modctx.resolve(func=name).text,name);f=csrc.Source(text).function(name);b=text[f.body.s:f.body.e];out=ROOT/'build/workers/takeover/s15-text-scope';out.mkdir(exist_ok=True);vs=[]
for typ,scope,init in itertools.product(['char far *','char far * const','const char far *'],[False,True],[False,True]):
 if typ=='char far * const' and not init:continue
 bb=b.replace('    char far *text;\n','')
 decl='    '+typ+' text'+(' = f_171C_1B84(h);' if init else ';')
 if scope:bb=bb.replace('    text = f_171C_1B84(h);','    {\n'+decl+('' if init else '\n    text = f_171C_1B84(h);')).replace('    f_24AB_02AD(0);\n    for (;;)', '    f_24AB_02AD(0);\n    }\n    for (;;)')
 else:
  # A declaration initializer requires a block that starts after the handle exists.
  if init:continue
  bb=bb.replace('    int result;',decl+'\n    int result;')
 vs.append(text[:f.body.s]+bb+text[f.body.e:])
ev=autosearch.Evaluator(modctx.resolve(func=name),name,4,out/'cache');rows=[]
for i,(t,r) in enumerate(zip(vs,ev.many(vs))):
 (out/f'v{i}.c').write_text(t);rows.append({'name':f'v{i}',**r})
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1));print('variants',len(rows),'exact',sum(bool(r.get('all_exact')) for r in rows));print([(r['name'],r.get('score'),r.get('length')) for r in rows])
