from pathlib import Path
import sys,json,itertools,re
sys.path.insert(0,'tools')
import csrc,modctx,autosearch,variants
name='CalcScore';ctx=modctx.resolve(func=name);text=Path('work/takeover/context-next/score-shared-index.c').read_text()
f=csrc.Source(text).function(name);b=text[f.body.s:f.body.e];out=Path('build/workers/context_next/score-phase-homes');out.mkdir(exist_ok=True)
start=b.index('    j = (fd_50F6_04F4');end=b.index('    if (fd_50F6_0FC2')
matrix=b.index('        sum = 0;',b.index('    if (fd_50F6_0EAC == 2'))
matrix_end=b.index('    score = MeHealth;')
vs=[('base',text,'')]
for site,s2,drop,order in itertools.product(['history','matrix'],[False,True],[False,True],[False,True]):
    bb=b;decls=['int j;']
    if site=='history':
        part=b[start:end]
        if s2:decls.append('int sum2;')
        if order:decls.reverse()
        bb=b[:start]+'    {\n    '+'\n    '.join(decls)+'\n'+part+'    }\n\n'+b[end:]
    else:
        # Both matrix scans share their own column index; the historical index remains outer.
        part=b[matrix:matrix_end]
        last=part.rfind('    }')
        part=part[:last]+'        }\n'+part[last:]
        bb=b[:matrix]+'        {\n        int j;\n'+part+b[matrix_end:]
    if s2:
        bb=bb.replace('    int sum, sum2;','    int sum;')
        if site=='matrix':
            bb=bb.replace('    j = (fd_50F6_04F4','    {\n    int sum2;\n    j = (fd_50F6_04F4').replace('    if (fd_50F6_0FC2','    }\n\n    if (fd_50F6_0FC2')
    if drop:bb=bb.replace('int i, j, k, n, t;','int i, j, k, n;')
    label=f'{site}-sum2{s2}-drop_t{drop}-reverse{order}'
    cand=text[:f.body.s]+bb+text[f.body.e:]
    if any(cand==v[1] for v in vs):continue
    vs.append((label,cand,''))
rows=variants.run(ctx,vs,extra_funcs=[name],claims_only=True,jobs=6,out_dir=out)
(out/'results.json').write_text(json.dumps({'function':name,'profile':ctx.profile,'flags':ctx.flags,'variants':rows},indent=1))
for row in rows:
    r=row['result'];print(row['name'],r.get('claims',{}).get(name),[c['name'] for c in ctx.claims if not r.get('claims',{}).get(c['name'],{}).get('exact')],flush=True)
