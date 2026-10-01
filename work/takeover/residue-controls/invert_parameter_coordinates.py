from pathlib import Path
import sys,json,itertools,re
ROOT=Path.cwd();sys.path.insert(0,str(ROOT/'tools'));import csrc,autosearch,modctx
name='InvertPatch';text=autosearch.unscaffold((ROOT/'src/S13/m384C.c').read_text(),name);f=csrc.Source(text).function(name);b=text[f.body.s:f.body.e];out=ROOT/'build/workers/takeover/invert-parameter-coordinates';out.mkdir(exist_ok=True);vs=[]
for expr,split,loops,orgfirst in itertools.product(['x * 28 - y * 10 + fd_50F6_10D2.left','x * 28 + (fd_50F6_10D2.left - y * 10)','fd_50F6_10D2.left - y * 10 + x * 28'],[False,True],['plain','h','v','both'],[False,True]):
 bb=b.replace('    int i, h, v;','    int i;')
 bb=bb.replace('org.h = x * 28 - y * 10 + fd_50F6_10D2.left;', 'org.h = '+expr+';')
 # Token substitution affects scalar locals, never the Pt's member names.
 bb=re.sub(r'(?<![.\w])h\b','x',bb);bb=re.sub(r'(?<![.\w])v\b','y',bb)
 if split:bb=bb.replace('x = (x >> 1) + fd_50F6_10D2.left + 4;', 'x >>= 1;\n        x += fd_50F6_10D2.left + 4;').replace('y = (y >> 1) + fd_50F6_10D2.top + 10;', 'y >>= 1;\n        y += fd_50F6_10D2.top + 10;')
 if loops in ['h','both']:bb=bb.replace(' + org.h;', ' + x;')
 if loops in ['v','both']:bb=bb.replace(' + y;', ' + org.v;')
 if orgfirst:bb=bb.replace('    org.h = '+expr+';\n    org.v = y * 10 + fd_50F6_10D2.top;', '    org.v = y * 10 + fd_50F6_10D2.top;\n    org.h = '+expr+';')
 vs.append(text[:f.body.s]+bb+text[f.body.e:])
ev=autosearch.Evaluator(modctx.resolve(func=name),name,4,out/'cache');rows=[]
for i,(t,r) in enumerate(zip(vs,ev.many(vs))):
 (out/f'v{i}.c').write_text(t);rows.append({'name':f'v{i}',**r})
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1));print('variants',len(rows),'exact',sum(bool(r.get('all_exact')) for r in rows));print([(r['name'],r.get('score'),r.get('length')) for r in sorted(rows,key=lambda r:r.get('score',[9]))[:8]])
