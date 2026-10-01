from pathlib import Path
import sys,json,itertools
ROOT=Path.cwd();sys.path.insert(0,str(ROOT/'tools'));import csrc,autosearch,modctx
name='InvertPatch';text=autosearch.unscaffold((ROOT/'src/S13/m384C.c').read_text(),name);f=csrc.Source(text).function(name);b=text[f.body.s:f.body.e];out=ROOT/'build/workers/takeover/invert-explicit-products';out.mkdir(exist_ok=True);vs=[]
first='    org.h = x * 28 - y * 10 + fd_50F6_10D2.left;\n    org.v = y * 10 + fd_50F6_10D2.top;\n    h = x * 28 - y * 10;\n    v = y * 10;'
for opts,decl,form,half in itertools.product(['','g','eg'],['int i; register int h, v;','int i; register int v, h;','int i, h, v;'],range(3),[False,True]):
 bb=b.replace('    int i, h, v;', '    '+decl+'\n    int sx, sy, left, top;')
 forms=['    sx = x * 28;\n    sy = y * 10;\n    left = fd_50F6_10D2.left;\n    top = fd_50F6_10D2.top;\n    org.h = sx + (left - sy);\n    org.v = sy + top;\n    h = sx - sy;\n    v = sy;', '    org.h = (sx = x * 28) + ((left = fd_50F6_10D2.left) - (sy = y * 10));\n    org.v = sy + (top = fd_50F6_10D2.top);\n    h = sx - sy;\n    v = sy;', '    org.h = (sx = x * 28) - (sy = y * 10) + (left = fd_50F6_10D2.left);\n    org.v = sy + (top = fd_50F6_10D2.top);\n    h = sx - sy;\n    v = sy;']
 bb=bb.replace(first,forms[form]);bb=bb.replace(' + fd_50F6_10D2.left + 4;', ' + left + 4;').replace(' + fd_50F6_10D2.top + 10;', ' + top + 10;').replace('h += fd_50F6_10D2.left;', 'h += left;').replace('v += fd_50F6_10D2.top;', 'v += top;')
 if half:bb=bb.replace('h = (h >> 1) + left + 4;', 'h >>= 1;\n        h += left + 4;').replace('v = (v >> 1) + top + 10;', 'v >>= 1;\n        v += top + 10;')
 src=text[:f.body.s]+bb+text[f.body.e:]
 if opts:src=src[:f.head_s]+f'#pragma optimize("{opts}", off)\n'+src[f.head_s:];end=csrc.Source(src).function(name).e;src=src[:end]+f'\n#pragma optimize("{opts}", on)\n'+src[end:]
 vs.append(src)
ev=autosearch.Evaluator(modctx.resolve(func=name),name,4,out/'cache');rows=[]
for i,(t,r) in enumerate(zip(vs,ev.many(vs))):
 (out/f'v{i}.c').write_text(t);rows.append({'name':f'v{i}',**r})
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1));print('variants',len(rows),'exact',sum(bool(r.get('all_exact')) for r in rows));print([(r['name'],r.get('score'),r.get('length')) for r in sorted(rows,key=lambda r:r.get('score',[9]))[:8]])
