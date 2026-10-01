from pathlib import Path
import itertools, sys, json, hashlib
sys.path.insert(0,'tools')
import csrc, modctx, autosearch, variants

name='ch_LookUpId'
ctx=modctx.resolve(func=name)
base=Path('build/workers/fleet_root/lookup-controls/000_chain0-first0-wrap0.c').read_text(encoding='utf-8')
f=csrc.Source(base).function(name)
body=base[f.body.s:f.body.e]
out=Path('build/workers/fleet_root/lookup-controls')
out.mkdir(parents=True,exist_ok=True)
vs=[]
for reversed_chain, first, second in itertools.product([False,True],[False,True],[False,True]):
    b=body
    if reversed_chain:b=b.replace('start = i =','i = start =')
    if first:b=b.replace('    p = &base[i];','    p = base + i;',1)
    if second:b=b.replace('for (i = count - 1, p = &base[i];','for (i = count - 1, p = base + i;',1)
    label=f'chain{int(reversed_chain)}-first{int(first)}-wrap{int(second)}'
    vs.append((label,base[:f.body.s]+b+base[f.body.e:],'Equivalent chained stores and pointer arithmetic; no artificial expression'))
rows=variants.run(ctx,vs,extra_funcs=[name],claims_only=True,jobs=2,out_dir=out)
for row,(_,source,_) in zip(rows,vs):
    row['source_sha256_lf']=hashlib.sha256(source.encode()).hexdigest()
    r=row['result'];print(row['name'],r.get('claims',{}).get(name),flush=True)
(out/'results.json').write_text(json.dumps({'function':name,'profile':ctx.profile,'flags':ctx.flags,'placements':ctx.placements,'variants':rows},indent=1)+'\n',encoding='utf-8')
