from pathlib import Path
import sys,json,itertools
ROOT=Path.cwd();sys.path.insert(0,str(ROOT/'tools'));import csrc,autosearch,modctx
name='f_1E57_038E';ctx=modctx.resolve(func=name);text=autosearch.unscaffold(ctx.text,name);f=csrc.Source(text).function(name);b=text[f.body.s:f.body.e];out=ROOT/'build/workers/takeover/clip-phase-pointers';out.mkdir(exist_ok=True);vs=[];meta=[]
for first,separate,last,position in itertools.product([False,True],[False,True],[False,True],['before','after']):
 bb=b;decl=[]
 if first:
  decl.append('    struct Rect far *firstEnd;')
  old='    fd_50F6_3B60[win >> 8] = f_171C_1A9E(n = (f_1D8E_02BD(&r, list, tmp, 0L) - tmp + 1) * sizeof(struct Rect), 1, "winClipList");'
  new='    firstEnd = f_1D8E_02BD(&r, list, tmp, 0L);\n    fd_50F6_3B60[win >> 8] = f_171C_1A9E(n = (firstEnd - tmp + 1) * sizeof(struct Rect), 1, "winClipList");'
  assert old in bb;bb=bb.replace(old,new)
 if separate:
  decl.append('    struct Rect far *includedEnd;')
  bb=bb.replace('        end = f_1D8E_02BD(&r, list, tmp, 0L);\n        n = count = end - tmp;', '        includedEnd = f_1D8E_02BD(&r, list, tmp, 0L);\n        n = count = includedEnd - tmp;')
 if last:
  decl.append('    struct Rect far *lastEnd;')
  bb=bb.replace('    end = f_1D8E_02BD(&r, list, 0L, tmp);\n    n = end - tmp;', '    lastEnd = f_1D8E_02BD(&r, list, 0L, tmp);\n    n = lastEnd - tmp;')
 if decl:
  if position=='before':bb=bb.replace('    int win;', '\n'.join(decl)+'\n    int win;')
  else:bb=bb.replace('    int count;', '    int count;\n'+'\n'.join(decl))
 vs.append(text[:f.body.s]+bb+text[f.body.e:]);meta.append([first,separate,last,position])
ev=autosearch.Evaluator(ctx,name,4,out/'cache');rows=[]
for i,(t,r) in enumerate(zip(vs,ev.many(vs))):
 (out/f'v{i}.c').write_text(t);rows.append({'name':f'v{i}','meta':meta[i],**r})
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1));print('variants',len(rows),'exact',sum(bool(r.get('all_exact')) for r in rows));print([(r['name'],r.get('meta'),r.get('score'),r.get('length')) for r in sorted(rows,key=lambda r:r.get('score',[9]))[:8]])
