from pathlib import Path
import sys, json, itertools
ROOT=Path.cwd();sys.path.insert(0,str(ROOT/'tools'))
import modctx,autosearch,csrc
name='FindIndex';ctx=modctx.resolve(func=name);base=autosearch.unscaffold(ctx.text,name)
f=csrc.Source(base).function(name);body=base[f.body.s:f.body.e]
start=body.index('        if (fd_50F6_3952->kind > kind');end=body.index('\n    }',start)
out=ROOT/'build/workers/blockers/index-trees';out.mkdir(parents=True,exist_ok=True)
k='fd_50F6_3952->kind';i='fd_50F6_3952->id';hi='top = mid - 1;';lo='fd_50F6_3956 = mid + 1;'
def iff(cond,a,b,inv):
    if inv: cond='!('+cond+')';a,b=b,a
    return 'if ('+cond+') {\n'+a+'\n} else {\n'+b+'\n}'
trees=[]
for a,b,c in itertools.product([False,True],repeat=3):
    # Explicit three-way kind comparison, avoiding the previously tested two-clause graph.
    for equaltest in [f'{k} != kind',f'{k} == kind']:
        inner=iff(f'{i} < id',lo,hi,c)
        unequal=iff(equaltest,lo,inner,b) if '!=' in equaltest else iff(equaltest,inner,lo,b)
        trees.append(iff(f'{k} > kind',hi,unequal,a))
        unequal=iff(equaltest,hi,inner,b) if '!=' in equaltest else iff(equaltest,inner,hi,b)
        trees.append(iff(f'{k} < kind',lo,unequal,a))
    for comp in [f'{i} >= id',f'!({i} < id)',f'({i} < id) == 0']:
        inner=iff(comp,hi,lo,c)
        trees.append(iff(f'{k} == kind',inner,iff(f'{k} > kind',hi,lo,b),a))
variants=[];seen=set()
for tree in trees:
    for style in ['plain','continue','empty_else']:
        if style=='continue': tree2=tree.replace(hi,hi+' continue;').replace(lo,lo+' continue;')
        elif style=='empty_else':tree2=tree.replace('else {','else if (1) {')
        else:tree2=tree
        t=base[:f.body.s]+body[:start]+tree2+body[end:]+base[f.body.e:]
        if t not in seen:variants.append(t);seen.add(t)
ev=autosearch.Evaluator(ctx,name,6,out/'cache');rows=[]
for start in range(0,len(variants),24):
    batch=variants[start:start+24]
    for idx,(t,r) in enumerate(zip(batch,ev.many(batch)),start):
        (out/f'v{idx}.c').write_text(t);rows.append({'name':f'v{idx}',**r})
    ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1))
    print('done',len(rows),'exact',[(r['name'],r['all_exact']) for r in rows if r.get('exact')],flush=True)
    if any(r.get('all_exact') for r in rows):break
print('best',[(r['name'],r.get('score'),r.get('all_exact')) for r in sorted(rows,key=lambda r:r.get('score',[9]))[:8]])
