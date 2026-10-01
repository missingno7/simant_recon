from pathlib import Path
import sys,json,itertools
ROOT=Path.cwd();sys.path.insert(0,str(ROOT/'tools'));import csrc,autosearch,modctx
name='f_0250_129E';text=(ROOT/'build/workers/takeover/mapdraw-coordinate-copies/v9.c').read_text();f=csrc.Source(text).function(name);b=text[f.body.s:f.body.e];out=ROOT/'build/workers/takeover/mapdraw-declaration-initializers';out.mkdir(exist_ok=True);vs=[]
for form in range(7):
 bb=b
 if form==0:bb=bb.replace('    screenY = y;\n    ay = fd_50F6_0508.y + screenY;', '    ay = fd_50F6_0508.y + y;\n    screenY = y;')
 elif form==1:bb=bb.replace('    int screenY;', '    int screenY = y;').replace('    screenY = y;\n','')
 elif form==2:bb=bb.replace('    int ay;', '    int ay = fd_50F6_0508.y + y;').replace('    ay = fd_50F6_0508.y + screenY;\n','')
 elif form==3:bb=bb.replace('    int ay;\n    int screenY;', '    int ay = fd_50F6_0508.y + y;\n    int screenY = y;').replace('    screenY = y;\n    ay = fd_50F6_0508.y + screenY;\n','')
 elif form==4:bb=bb.replace('    int ay;\n    int screenY;', '    int screenY = y;\n    int ay = fd_50F6_0508.y + screenY;').replace('    screenY = y;\n    ay = fd_50F6_0508.y + screenY;\n','')
 elif form==5:bb=bb.replace('    screenY = y;\n    ay = fd_50F6_0508.y + screenY;', '    ay = fd_50F6_0508.y + (screenY = y);')
 else:bb=bb.replace('    screenY = y;\n    ay = fd_50F6_0508.y + screenY;', '    ay = (screenY = y) + fd_50F6_0508.y;')
 vs.append(text[:f.body.s]+bb+text[f.body.e:])
ev=autosearch.Evaluator(modctx.resolve(func=name),name,4,out/'cache');rows=[]
for i,(t,r) in enumerate(zip(vs,ev.many(vs))):
 (out/f'v{i}.c').write_text(t);rows.append({'name':f'v{i}',**r})
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1));print('variants',len(rows),'exact',sum(bool(r.get('all_exact')) for r in rows));print([(r['name'],r.get('score'),r.get('length')) for r in rows])
