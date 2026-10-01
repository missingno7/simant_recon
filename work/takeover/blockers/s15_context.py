from pathlib import Path
import sys, json, re, itertools
ROOT=Path.cwd(); sys.path.insert(0,str(ROOT/'tools'))
import autosearch, modctx, csrc, srcrules as R
name='o15_384C_0239'; ctx=modctx.resolve(func=name); text=ctx.text
out=ROOT/'build/workers/blockers/s15-context'; out.mkdir(parents=True,exist_ok=True)
moves=[m for m in list(R.r_proto_names(R.Ctx(text,name)))+list(R.r_sym_names(R.Ctx(text,name))) if ' unnamed' in m.site]
print('moves',[(m.rule,m.site) for m in moves],flush=True)
variants=[('base',text,[])]; seen={text}
groups=[list(range(k)) for k in range(1,len(moves)+1)]
groups += [[k] for k in range(len(moves))]
groups += list(itertools.combinations(range(len(moves)),2))
for ids in groups:
    t=R.apply_edits(text,[e for i in ids for e in moves[i].edits])
    if t not in seen:
        variants.append(('v'+str(len(variants)),t,list(ids))); seen.add(t)
ev=autosearch.Evaluator(ctx,name,6,out/'cache'); rows=[]
for start in range(0,len(variants),24):
    batch=variants[start:start+24]
    for (n,t,meta),r in zip(batch,ev.many([t for _,t,_ in batch])):
        (out/(n+'.c')).write_text(t); rows.append({'name':n,'meta':meta,**r})
    ev.save(); (out/'results.json').write_text(json.dumps(rows,indent=1))
    print('done',len(rows),'exact',[(r['name'],r.get('all_exact')) for r in rows if r.get('exact')],flush=True)
print('best',[(r['name'],r.get('score'),r.get('all_exact')) for r in sorted(rows,key=lambda r:r.get('score',[9]))[:10]],flush=True)
