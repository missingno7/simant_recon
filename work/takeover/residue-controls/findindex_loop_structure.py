from pathlib import Path
import sys,json,itertools
ROOT=Path.cwd();sys.path.insert(0,str(ROOT/'tools'));import csrc,autosearch,modctx
name='FindIndex';ctx=modctx.resolve(func=name);out=ROOT/'build/workers/takeover/findindex-loop-structure';out.mkdir(exist_ok=True);vs=[];meta=[]
for filename,loop in itertools.product(['findindex-bound-updates/v0.c','findindex-conditional-forms/v16.c','findindex-shared-blocks/v0.c'],['guard_break','positive_block','goto_test','tail_break']):
 text=(ROOT/'build/workers/takeover'/filename).read_text();f=csrc.Source(text).function(name);b=text[f.body.s:f.body.e];bb=b
 if loop=='guard_break':bb=bb.replace('    while (fd_50F6_3956 <= top) {','    for (;;) {\n        if (fd_50F6_3956 > top) break;')
 elif loop=='positive_block':
  bb=bb.replace('    while (fd_50F6_3956 <= top) {','    for (;;) {\n        if (fd_50F6_3956 <= top) {').replace('    }\n    fd_50F6_3952 =','        } else break;\n    }\n    fd_50F6_3952 =',1)
 elif loop=='goto_test':
  bb=bb.replace('    while (fd_50F6_3956 <= top) {','    goto test;\nagain: {').replace('    }\n    fd_50F6_3952 =','    }\ntest:\n    if (fd_50F6_3956 <= top) goto again;\n    fd_50F6_3952 =',1)
 else:
  bb=bb.replace('    while (fd_50F6_3956 <= top) {','    if (fd_50F6_3956 <= top) for (;;) {').replace('    }\n    fd_50F6_3952 =','        if (fd_50F6_3956 > top) break;\n    }\n    fd_50F6_3952 =',1)
 vs.append(text[:f.body.s]+bb+text[f.body.e:]);meta.append([filename,loop])
ev=autosearch.Evaluator(ctx,name,4,out/'cache');rows=[]
for i,(t,r) in enumerate(zip(vs,ev.many(vs))):
 (out/f'v{i}.c').write_text(t);rows.append({'name':f'v{i}','meta':meta[i],**r})
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1));print('variants',len(rows),'exact',sum(bool(r.get('all_exact')) for r in rows));print([(r['name'],r.get('meta'),r.get('score'),r.get('length')) for r in rows])
