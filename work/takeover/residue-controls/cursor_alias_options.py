from pathlib import Path
import sys,json,itertools
ROOT=Path.cwd();sys.path.insert(0,str(ROOT/'tools'));import csrc,autosearch,modctx
name='DrawMapCursor';ctx=modctx.resolve(func=name);out=ROOT/'build/workers/takeover/cursor-alias-options';out.mkdir(exist_ok=True);vs=[]
for basekind,alias,chain in itertools.product(['fresh','old'],[False,True],range(4)):
 text=(ROOT/('build/workers/takeover/cursor-current-near.c' if basekind=='fresh' else 'work/takeover/full-search/DrawMapCursor/best.c')).read_text();f=csrc.Source(text).function(name);b=text[f.body.s:f.body.e]
 for bit,field,other,term in [(1,'top','bottom','fd_50F6_3858 * fd_50F6_10DE'),(2,'left','right','fd_50F6_3856 * fd_50F6_10E0')]:
  if not chain&bit:continue
  import re
  pattern=r'    fd_50F6_38C2\.'+field+r' = ([^;]+);\n    fd_50F6_38C2\.'+other+r' = fd_50F6_38C2\.'+field+r' \+ '+re.escape(term)+r';'
  b,n=re.subn(pattern,lambda m:'    fd_50F6_38C2.'+other+' = (fd_50F6_38C2.'+field+' = '+m[1]+') + '+term+';',b);assert n==1
 src=text[:f.body.s]+b+text[f.body.e:]
 if alias:
  src=src[:f.head_s]+'#pragma optimize("a", on)\n'+src[f.head_s:];end=csrc.Source(src).function(name).e;src=src[:end]+'\n#pragma optimize("a", off)\n'+src[end:]
 vs.append(src)
ev=autosearch.Evaluator(ctx,name,4,out/'cache');rows=[]
for i,(t,r) in enumerate(zip(vs,ev.many(vs))):
 (out/f'v{i}.c').write_text(t);rows.append({'name':f'v{i}',**r})
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1));print('variants',len(rows),'exact',sum(bool(r.get('all_exact')) for r in rows));print([(r['name'],r.get('score'),r.get('length')) for r in sorted(rows,key=lambda r:r.get('score',[9]))[:8]])
