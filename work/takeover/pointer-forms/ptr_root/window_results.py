from pathlib import Path
import hashlib,itertools,json,sys
sys.path.insert(0,'tools')
import autosearch,csrc,modctx,variants

name='f_2505_0453';ctx=modctx.resolve(func=name)
base=autosearch.unscaffold(Path('build/workers/ptr_root/window-forms/seed.c').read_text(encoding='utf-8'),name)
f=csrc.Source(base).function(name);b=base[f.body.s:f.body.e]
out=Path('build/workers/ptr_root/window-results');out.mkdir(parents=True,exist_ok=True)
vs=[('base',base,'Frozen original target and accepted peers')]
for wtype,rtype,result in itertools.product(['byte','window'],['byte','rect','array4'],['index','address']):
    bb=b
    if wtype=='window':
        bb=bb.replace('char far *w;','struct Win far *w;')
        bb=bb.replace('w = f_2505_0006(win);','w = (struct Win far *)f_2505_0006(win);')
        bb=bb.replace('*(int far *)(w + 0xc)','w->count')
        table='w->objs[idx]'
    else:table='((char far * far *)(w + 0x2c))[idx]'
    cast={'byte':'char far *','rect':'struct Rect far *','array4':'int (far *)[4]'}[rtype]
    decl={'byte':'char far *r;','rect':'struct Rect far *r;','array4':'int (far *r)[4];'}[rtype]
    bb=bb.replace('int far *r;',decl)
    bb=bb.replace('r = ((int far * far *)(w + 0x2c))[idx];',f'r = ({cast}){table};')
    rv='((int far *)r)[kind]' if result=='index' else '*(int far *)((char far *)r + kind * 2)'
    bb=bb.replace('return r[kind];','return '+rv+';')
    vs.append((f'{wtype}-{rtype}-{result}',base[:f.body.s]+bb+base[f.body.e:],
               'Object table is a char/rectangle/four-int coordinate view; layout retains same bytes and genuine selected coordinate'))
rows=variants.run(ctx,vs,extra_funcs=[name],claims_only=True,jobs=2,out_dir=out)
for row,(_,source,_) in zip(rows,vs):
    row['source_sha256_lf']=hashlib.sha256(source.encode()).hexdigest()
    r=row['result'];t=r.get('claims',{}).get(name,{})
    print(row['name'],r.get('compile_ok'),t.get('exact'),t.get('reasons'),
          'peer_losses',[n for n,c in r.get('claims',{}).items() if n!=name and not c['exact']],
          'data_losses',[n for n,c in r.get('data',{}).items() if not c['exact']],flush=True)
(out/'results.json').write_text(json.dumps({'function':name,'module':ctx.key,'profile':ctx.profile,
 'flags':ctx.flags,'placements':ctx.placements,'variants':rows},indent=1)+'\n',encoding='utf-8')
