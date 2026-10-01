from pathlib import Path
import sys, json, hashlib
ROOT=Path.cwd(); sys.path.insert(0,str(ROOT/'tools'))
import csrc, modctx, variants
out=ROOT/'build/workers/fleet_index'; basepath=out/'findindex-base.c'; base=basepath.read_text(encoding='latin1')
ctx=modctx.resolve(func='FindIndex',source=basepath); f=csrc.Source(base).function('FindIndex'); body=base[f.body.s:f.body.e]
k='fd_50F6_3952->kind'; ident='fd_50F6_3952->id'
lo='fd_50F6_3956 = mid + 1;'; hi='top = mid - 1;'
forms=[
 ('reverse-kind-first', f'''        if (kind < {k})\n            {hi}\n        else if ({k} != kind)\n            {lo}\n        else if ({ident} < id)\n            {lo}\n        else\n            {hi}''', 'Equivalent tuple ordering with the first comparison written as query-kind < record-kind; then preserves the original unequal-kind and ID tests.'),
 ('reverse-kind-and-id-first', f'''        if (kind < {k})\n            {hi}\n        else if (kind != {k})\n            {lo}\n        else if (id > {ident})\n            {lo}\n        else\n            {hi}''', 'Equivalent tuple ordering with query/record operands reversed at both first-kind and lower-ID tests.'),
 ('ordered-two-way-kind', f'''        if (kind < {k})\n            {hi}\n        else if (kind > {k})\n            {lo}\n        else if ({ident} < id)\n            {lo}\n        else\n            {hi}''', 'Equivalent explicit less/equal/greater partition, with query-first kind comparisons.'),
 ('reverse-compound-boundary', f'''        if (kind < {k} || (kind == {k} && id <= {ident}))\n            {hi}\n        else\n            {lo}''', 'Equivalent first-lower-bound test written in the reversed relational direction; equality retains the first matching record.'),
]
rows=[]; draftdir=out/'novel';draftdir.mkdir(parents=True,exist_ok=True)
for name, block, rationale in forms:
    marker='        if (!(fd_50F6_3952->kind < kind || (fd_50F6_3952->kind == kind && fd_50F6_3952->id < id)))\n            top = mid - 1;\n        else\n            fd_50F6_3956 = mid + 1;'
    assert marker in body,name
    b=body.replace(marker,block)
    text=base[:f.body.s]+b+base[f.body.e:]
    rows.append((name,text,rationale))
(out/'novel').mkdir(parents=True,exist_ok=True)
vr=variants.run(ctx,[('base',base,'')]+[(n,t,'') for n,t,_ in rows],extra_funcs=['FindIndex'],claims_only=True,jobs=2,out_dir=out/'novel')
result=[]
for (name,text,rationale),row in zip(rows,vr[1:]):
    res=row['result']; fi=res.get('claims',{}).get('FindIndex',{})
    item={'name':name,'rationale':rationale,'source_sha256':hashlib.sha256(text.encode('latin1')).hexdigest(),'findindex':fi,'compile_ok':res.get('compile_ok'),'warnings':res.get('warnings',[]),'whole_module_exact':res.get('exact')}
    result.append(item)
(out/'novel-results.json').write_text(json.dumps({'module':ctx.key,'profile':ctx.profile,'flags':ctx.flags,'placements':ctx.placements,'variants':result},indent=2,default=str))
print('variants',len(rows),'exact',sum(bool(x['findindex'].get('exact')) for x in result))
for x in result: print(x['name'],'compile',x['compile_ok'],'result',x['findindex'].get('reasons'),'sha256',x['source_sha256'])
