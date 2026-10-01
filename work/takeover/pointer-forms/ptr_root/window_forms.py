from pathlib import Path
import hashlib, itertools, json, sys
sys.path.insert(0,'tools')
import autosearch, csrc, modctx, variants

name='f_2505_0453'
ctx=modctx.resolve(func=name)
out=Path('build/workers/ptr_root/window-forms')
out.mkdir(parents=True,exist_ok=True)
seed=out/'seed.c'
if not seed.exists():seed.write_text(ctx.text,encoding='utf-8',newline='\n')
base=autosearch.unscaffold(seed.read_text(encoding='utf-8'),name)
f=csrc.Source(base).function(name)
b=base[f.body.s:f.body.e]
vs=[]
for count,table,result in itertools.product(range(2),range(3),range(2)):
    bb=b
    if count:bb=bb.replace('*(int far *)(w + 0xc)','((int far *)w)[6]')
    table_expr=['((int far * far *)(w + 0x2c))[idx]',
                '*((int far * far *)(w + 0x2c) + idx)',
                '*(int far * far *)(w + 0x2c + idx * 4)'][table]
    bb=bb.replace('((int far * far *)(w + 0x2c))[idx]',table_expr)
    if result:bb=bb.replace('return r[kind];','return *(r + kind);')
    vs.append((f'count{count}-table{table}-result{result}',base[:f.body.s]+bb+base[f.body.e:],
               'Equivalent typed word, far-pointer table and result address forms; original real values retained'))
for decl,when,result in itertools.product(['before_w','after_r'],['before_guard','inside_guard'],range(2)):
    bb=b
    if decl=='before_w':bb=bb.replace('    char far *w;','    int far * far *objects;\n    char far *w;')
    else:bb=bb.replace('    int far *r;','    int far *r;\n    int far * far *objects;')
    if when=='before_guard':bb=bb.replace('        if (*(int far *)(w + 0xc) > idx)',
        '        objects = (int far * far *)(w + 0x2c);\n        if (*(int far *)(w + 0xc) > idx)')
    else:bb=bb.replace('            r = ','            objects = (int far * far *)(w + 0x2c);\n            r = ',1)
    bb=bb.replace('((int far * far *)(w + 0x2c))[idx]','*(objects + idx)')
    if result:bb=bb.replace('return r[kind];','return *(r + kind);')
    vs.append((f'table_local-{decl}-{when}-result{result}',base[:f.body.s]+bb+base[f.body.e:],
               'Used object-table pointer represents the table base visible in target address arithmetic'))
assert len({s for _,s,_ in vs})==20
rows=variants.run(ctx,vs,extra_funcs=[name],claims_only=True,jobs=2,out_dir=out)
for row,(_,source,_) in zip(rows,vs):
    row['source_sha256_lf']=hashlib.sha256(source.encode()).hexdigest()
    r=row['result'];t=r.get('claims',{}).get(name,{})
    print(row['name'],r.get('compile_ok'),t.get('exact'),t.get('reasons'),
          'peer_losses',[n for n,c in r.get('claims',{}).items() if n!=name and not c['exact']],
          'data_losses',[n for n,c in r.get('data',{}).items() if not c['exact']],flush=True)
(out/'results.json').write_text(json.dumps({'function':name,'module':ctx.key,'profile':ctx.profile,
    'flags':ctx.flags,'placements':ctx.placements,'variants':rows},indent=1)+'\n',encoding='utf-8')
