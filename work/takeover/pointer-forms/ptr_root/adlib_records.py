from pathlib import Path
import hashlib,itertools,json,sys
sys.path.insert(0,'tools')
import autosearch,csrc,modctx,variants

name='f_2815_0165';ctx=modctx.resolve(func=name)
base=autosearch.unscaffold(Path('build/workers/ptr_root/adlib-forms/seed.c').read_text(encoding='utf-8'),name)
f=csrc.Source(base).function(name);b=base[f.body.s:f.body.e]
record='#pragma pack(1)\nstruct SynthRecord { unsigned char operators[11]; int transpose; int volume; };\n#pragma pack()\n'
out=Path('build/workers/ptr_root/adlib-records');out.mkdir(parents=True,exist_ok=True)
vs=[('base',base,'Canonical split-volume contrast')]
for scope,stage,source_form in itertools.product(['file','local'],range(3),['index','add']):
    bb=b.replace('unsigned char far *p;','struct SynthRecord far *p;')
    bb=bb.replace('*(int far *)(p + 0xd)','p->volume').replace('*(int far *)(p + 0xb)','p->transpose').replace('p[2]','p->operators[2]')
    pexpr='fd_50F6_0000[instr].p' if source_form=='index' else '(fd_50F6_0000 + instr)->p'
    old='    vol += fd_50F6_4B16;\n    p = fd_50F6_0000[instr].p;\n    vol += p->volume;'
    stages=[f'    vol += fd_50F6_4B16;\n    p = (struct SynthRecord far *){pexpr};\n    vol += p->volume;',
            f'    vol = vol + fd_50F6_4B16 + (p = (struct SynthRecord far *){pexpr})->volume;',
            f'    vol += fd_50F6_4B16;\n    vol += (p = (struct SynthRecord far *){pexpr})->volume;']
    assert old in bb;bb=bb.replace(old,stages[stage])
    if scope=='local':bb=bb.replace('{\n','{\n'+record,1)
    prefix=base[:f.body.s] if scope=='local' else base[:f.head_s]+record+base[f.head_s:f.body.s]
    vs.append((f'{scope}-stage{stage}-{source_form}',prefix+bb+base[f.body.e:],
               'Packed record view: eleven OPL operator bytes, signed transpose at +11, signed volume at +13; offsets grounded in target reads'))
rows=variants.run(ctx,vs,extra_funcs=[name],claims_only=True,jobs=2,out_dir=out)
for row,(_,source,_) in zip(rows,vs):
    row['source_sha256_lf']=hashlib.sha256(source.encode()).hexdigest()
    r=row['result'];t=r.get('claims',{}).get(name,{})
    print(row['name'],r.get('compile_ok'),t.get('exact'),t.get('reasons'),
          'peer_losses',[n for n,c in r.get('claims',{}).items() if n!=name and not c['exact']],
          'data_losses',[n for n,c in r.get('data',{}).items() if not c['exact']],flush=True)
(out/'results.json').write_text(json.dumps({'function':name,'module':ctx.key,'profile':ctx.profile,
 'flags':ctx.flags,'placements':ctx.placements,'variants':rows},indent=1)+'\n',encoding='utf-8')
