from pathlib import Path
import sys,json,hashlib
ROOT=Path.cwd();sys.path.insert(0,str(ROOT/'tools'))
import csrc,modctx,variants
out=ROOT/'build/workers/fleet_index';basepath=out/'findindex-base.c';base=basepath.read_text(encoding='latin1');ctx=modctx.resolve(func='FindIndex',source=basepath)
f=csrc.Source(base).function('FindIndex');body=base[f.body.s:f.body.e];k='fd_50F6_3952->kind';v='fd_50F6_3952->id';lo='fd_50F6_3956 = mid + 1;';hi='top = mid - 1;'
old='''        if (!(fd_50F6_3952->kind < kind || (fd_50F6_3952->kind == kind && fd_50F6_3952->id < id)))
            top = mid - 1;
        else
            fd_50F6_3956 = mid + 1;'''
variants_src=[
('reverse-sequential-continues',f'''        if (kind < {k}) {{ {hi} continue; }}
        if ({k} != kind) {{ {lo} continue; }}
        if (id > {v}) {{ {lo} continue; }}
        {hi}''','Equivalent ordered tests; the high-key path exits the iteration immediately.'),
('reverse-sequential-gotos',f'''        if (kind < {k}) goto upper_bound;
        if ({k} != kind) goto lower_bound;
        if (id > {v}) goto lower_bound;
upper_bound:
        {hi}
        continue;
lower_bound:
        {lo}''','Same ordered tests with shared bound blocks and a direct loop-back from the upper block.'),
('reverse-nested-id-first',f'''        if (kind == {k}) {{
            if (id <= {v})
                {hi}
            else
                {lo}
        }} else if (kind < {k})
            {hi}
        else
            {lo}''','Partitions equal kind first, then compares IDs in reversed relational order; other kinds use the query-first comparison.'),
('reverse-nested-kind-first',f'''        if (kind < {k})
            {hi}
        else if (kind != {k})
            {lo}
        else if (id > {v})
            {lo}
        else
            {hi}''','Nested direct conditions, with query-first comparisons for both strict ordering tests.'),
('reverse-upper-continue',f'''        if (kind < {k} || (kind == {k} && id <= {v})) {{
            {hi}
            continue;
        }}
        {lo}''','Direct upper-bound predicate; the upper branch uses an explicit continue.'),
('reverse-lower-guard',f'''        if (kind >= {k}) {{
            if (kind != {k} || id > {v})
                {lo}
            else
                {hi}
        }} else
            {hi}''','Equivalent guard nesting from the complementary comparison, preserving first-match behavior.'),
]
rows=[]
for name,repl,rationale in variants_src:
    assert old in body
    b=body.replace(old,repl)
    rows.append((name,base[:f.body.s]+b+base[f.body.e:],rationale))
# One block-scoped loop index tests source lifetime without changing the loop's condition or updates.
b=body.replace('    int mid;\n','',1).replace('    while (fd_50F6_3956 <= top) {\n','    while (fd_50F6_3956 <= top) {\n        int mid;\n',1)
rows.append(('loop-scoped-mid',base[:f.body.s]+b+base[f.body.e:],'Scopes the midpoint to the iteration body; all values and decision structure remain unchanged.'))
# Scoped midpoint combined with the first reversed-bound condition, keeping the same branch body.
b=body.replace('    int mid;\n','',1).replace('    while (fd_50F6_3956 <= top) {\n','    while (fd_50F6_3956 <= top) {\n        int mid;\n',1).replace(old,variants_src[3][1])
rows.append(('loop-scoped-mid-reverse-nested',base[:f.body.s]+b+base[f.body.e:],'Combines the loop-local midpoint lifetime with query-first nested comparison structure.'))
D=out/'followup';D.mkdir(parents=True,exist_ok=True)
res=variants.run(ctx,[('base',base,'')]+[(n,t,'') for n,t,_ in rows],extra_funcs=['FindIndex'],claims_only=True,jobs=2,out_dir=D)
summary=[]
for (n,t,why),r in zip(rows,res[1:]):
 fi=r['result'].get('claims',{}).get('FindIndex',{})
 summary.append({'name':n,'rationale':why,'source_sha256':hashlib.sha256(t.encode('latin1')).hexdigest(),'compile_ok':r['result'].get('compile_ok'),'findindex':fi,'whole_module_exact':r['result'].get('exact'),'warnings':r['result'].get('warnings',[])})
(out/'followup-results.json').write_text(json.dumps({'module':ctx.key,'profile':ctx.profile,'flags':ctx.flags,'placements':ctx.placements,'variants':summary},indent=2,default=str))
print('variants',len(rows),'exact',sum(bool(s['findindex'].get('exact')) for s in summary))
for x in summary:print(x['name'],'compile',x['compile_ok'],'length-reasons',x['findindex'].get('reasons'),'sha256',x['source_sha256'])
