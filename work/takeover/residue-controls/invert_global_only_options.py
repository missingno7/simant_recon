from pathlib import Path
import sys,json,itertools
ROOT=Path.cwd();sys.path.insert(0,str(ROOT/'tools'));import csrc,autosearch,modctx
name='InvertPatch';text=autosearch.unscaffold((ROOT/'src/S13/m384C.c').read_text(),name);f=csrc.Source(text).function(name);b=text[f.body.s:f.body.e];out=ROOT/'build/workers/takeover/invert-global-only-options';out.mkdir(exist_ok=True);vs=[]
for decl,expr,split in itertools.product(['int i; register int h, v;','int i; register int v, h;','int i, h, v;','register int i; int h, v;','int i, v; register int h;','int i, h; register int v;'],['x * 28 - y * 10 + fd_50F6_10D2.left','x * 28 + (fd_50F6_10D2.left - y * 10)','fd_50F6_10D2.left - y * 10 + x * 28'],[False,True]):
 bb=b.replace('    int i, h, v;', '    '+decl).replace('org.h = x * 28 - y * 10 + fd_50F6_10D2.left;', 'org.h = '+expr+';')
 if split:bb=bb.replace('h = (h >> 1) + fd_50F6_10D2.left + 4;', 'h >>= 1;\n        h += fd_50F6_10D2.left + 4;').replace('v = (v >> 1) + fd_50F6_10D2.top + 10;', 'v >>= 1;\n        v += fd_50F6_10D2.top + 10;')
 src=text[:f.body.s]+bb+text[f.body.e:];src=src[:f.head_s]+'#pragma optimize("e", off)\n'+src[f.head_s:];end=csrc.Source(src).function(name).e;src=src[:end]+'\n#pragma optimize("e", on)\n'+src[end:];vs.append(src)
ev=autosearch.Evaluator(modctx.resolve(func=name),name,4,out/'cache');rows=[]
for i,(t,r) in enumerate(zip(vs,ev.many(vs))):
 (out/f'v{i}.c').write_text(t);rows.append({'name':f'v{i}',**r})
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1));print('variants',len(rows),'exact',sum(bool(r.get('all_exact')) for r in rows));print([(r['name'],r.get('score'),r.get('length')) for r in sorted(rows,key=lambda r:r.get('score',[9]))[:8]])
