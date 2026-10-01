"""Reuse the consumed choice parameter for the result, with real switch temporaries."""
from pathlib import Path
import sys,re,itertools,json
sys.path.insert(0,'tools')
import modctx,csrc,autosearch,variants
name='o15_384C_0239';ctx=modctx.resolve(func=name);base=autosearch.unscaffold(ctx.text,name)
fn=csrc.Source(base).function(name);body=base[fn.body.s:fn.body.e]
out=Path('build/workers/context_next/s15-parameter-result');out.mkdir(parents=True,exist_ok=True)
drafts=[('base',base,'')]
for mask,reg,form in itertools.product(range(4),['','register '],['assignment','embedded']):
    bb=body.replace('    int result;\n','')
    bb=re.sub(r'\bresult\b','which',bb)
    declarations=[]
    for bit,var,expr in [(1,'key','f_1F58_0090()'),(2,'button','ev.code')]:
        if not mask&bit:continue
        declarations.append('    '+reg+'int '+var+';')
        if form=='assignment':bb=bb.replace('switch ('+expr+')', var+' = '+expr+';\n            switch ('+var+')')
        else:bb=bb.replace('switch ('+expr+')','switch ('+var+' = '+expr+')')
    bb=bb.replace('{\n','{\n'+'\n'.join(declarations)+'\n',1)
    label=f'{mask}-{bool(reg)}-{form}'
    drafts.append((label,base[:fn.body.s]+bb+base[fn.body.e:],''))
rows=variants.run(ctx,drafts,extra_funcs=[name],claims_only=True,jobs=6,out_dir=out)
(out/'results.json').write_text(json.dumps({'profile':ctx.profile,'flags':ctx.flags,'variants':rows},indent=1))
for row in rows:
    r=row['result'];v=r.get('claims',{}).get(name,{})
    print(row['name'],v.get('exact'),v.get('reasons'),[c['name'] for c in ctx.claims if not r.get('claims',{}).get(c['name'],{}).get('exact')],flush=True)
