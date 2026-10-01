from pathlib import Path
import sys,json,itertools
ROOT=Path.cwd();sys.path.insert(0,str(ROOT/'tools'));import csrc,autosearch,modctx
name='InvertPatch';ctx=modctx.resolve(func=name);text=autosearch.unscaffold(ctx.text,name);f=csrc.Source(text).function(name);b=text[f.body.s:f.body.e];out=ROOT/'build/workers/takeover/invert-origin-storage';out.mkdir(exist_ok=True);vs=[]
for qualifier,typ,assoc,split in itertools.product(['','volatile'],['int i, h, v;','int i; register int h, v;','int i; short h, v;'],[False,True],[False,True]):
 bb=b.replace('struct Pt org;',qualifier+' struct Pt org;').replace('int i, h, v;',typ)
 if assoc:bb=bb.replace('org.h = x * 28 - y * 10 + fd_50F6_10D2.left;', 'org.h = x * 28 + (fd_50F6_10D2.left - y * 10);')
 if split:bb=bb.replace('h = (h >> 1) + fd_50F6_10D2.left + 4;', 'h >>= 1;\n        h += fd_50F6_10D2.left + 4;').replace('v = (v >> 1) + fd_50F6_10D2.top + 10;', 'v >>= 1;\n        v += fd_50F6_10D2.top + 10;')
 vs.append(text[:f.body.s]+bb+text[f.body.e:])
ev=autosearch.Evaluator(ctx,name,4,out/'cache');rows=[]
for i,(t,r) in enumerate(zip(vs,ev.many(vs))):
 (out/f'v{i}.c').write_text(t);rows.append({'name':f'v{i}',**r})
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1));print('variants',len(rows),'exact',sum(bool(r.get('all_exact')) for r in rows));print([(r['name'],r.get('score'),r.get('length')) for r in sorted(rows,key=lambda r:r.get('score',[9]))[:10]])
