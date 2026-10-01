from pathlib import Path
import sys,json,itertools
ROOT=Path.cwd();sys.path.insert(0,str(ROOT/'tools'));import csrc,autosearch,modctx
name='InvertPatch';text=autosearch.unscaffold((ROOT/'src/S13/m384C.c').read_text(),name);f=csrc.Source(text).function(name);b=text[f.body.s:f.body.e];out=ROOT/'build/workers/takeover/invert-coordinate-expressions';out.mkdir(exist_ok=True);vs=[]
for initial,usefield,split in itertools.product(['x * 28 - y * 10 + fd_50F6_10D2.left','x * 28 + (fd_50F6_10D2.left - y * 10)','fd_50F6_10D2.left - y * 10 + x * 28'],[False,True],[False,True]):
 bb=b.replace('    int i, h, v;', '    int i;').replace('    h = x * 28 - y * 10;\n    v = y * 10;\n','').replace('org.h = x * 28 - y * 10 + fd_50F6_10D2.left;', 'org.h = '+initial+';')
 rawx='org.h - fd_50F6_10D2.left' if usefield else 'x * 28 - y * 10';rawy='org.v - fd_50F6_10D2.top' if usefield else 'y * 10'
 bb=bb.replace('h = (h >> 1) + fd_50F6_10D2.left + 4;', 'org.h = (('+rawx+') >> 1) + fd_50F6_10D2.left + 4;').replace('v = (v >> 1) + fd_50F6_10D2.top + 10;', 'org.v = (('+rawy+') >> 1) + fd_50F6_10D2.top + 10;').replace('        org.h = h;\n','').replace('        org.v = v;\n','').replace('h += fd_50F6_10D2.left;', 'org.h = x * 28 - y * 10 + fd_50F6_10D2.left;').replace('v += fd_50F6_10D2.top;', 'org.v = y * 10 + fd_50F6_10D2.top;').replace(' + v;', ' + org.v;')
 if split:bb=bb.replace('org.h = (('+rawx+') >> 1) + fd_50F6_10D2.left + 4;', 'org.h = ('+rawx+') >> 1;\n        org.h += fd_50F6_10D2.left + 4;').replace('org.v = (('+rawy+') >> 1) + fd_50F6_10D2.top + 10;', 'org.v = ('+rawy+') >> 1;\n        org.v += fd_50F6_10D2.top + 10;')
 vs.append(text[:f.body.s]+bb+text[f.body.e:])
ev=autosearch.Evaluator(modctx.resolve(func=name),name,4,out/'cache');rows=[]
for i,(t,r) in enumerate(zip(vs,ev.many(vs))):
 (out/f'v{i}.c').write_text(t);rows.append({'name':f'v{i}',**r})
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1));print('variants',len(rows),'exact',sum(bool(r.get('all_exact')) for r in rows));print([(r['name'],r.get('score'),r.get('length')) for r in sorted(rows,key=lambda r:r.get('score',[9]))[:8]])
