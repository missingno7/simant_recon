from pathlib import Path
import hashlib,itertools,json,sys
sys.path.insert(0,'tools')
import autosearch,csrc,modctx,variants

name='f_2815_0165';ctx=modctx.resolve(func=name)
out=Path('build/workers/ptr_root/adlib-forms');out.mkdir(parents=True,exist_ok=True)
seed=out/'seed.c'
if not seed.exists():seed.write_text(ctx.text,encoding='utf-8',newline='\n')
base=autosearch.unscaffold(seed.read_text(encoding='utf-8'),name)
f=csrc.Source(base).function(name);b=base[f.body.s:f.body.e]
old='    vol += fd_50F6_4B16;\n    p = fd_50F6_0000[instr].p;\n    vol += *(int far *)(p + 0xd);'
assert old in b
factors=['((p[2] & 0x3f) ^ 0x3f)',
         '(unsigned char)((p[2] & 0x3f) ^ 0x3f)',
         '((unsigned char)(p[2] & 0x3f) ^ 0x3f)',
         '(0x3f - (p[2] & 0x3f))',
         '((unsigned char)~p[2] & 0x3f)']
vs=[]
for order,factor,pointer in itertools.product(range(3),range(5),range(2)):
    pexpr='fd_50F6_0000[instr].p' if pointer==0 else '(fd_50F6_0000 + instr)->p'
    stages=[f'    vol += fd_50F6_4B16;\n    p = {pexpr};\n    vol += *(int far *)(p + 0xd);',
            f'    vol = vol + fd_50F6_4B16 + *(int far *)((p = {pexpr}) + 0xd);',
            f'    vol += fd_50F6_4B16;\n    vol += *(int far *)((p = {pexpr}) + 0xd);']
    bb=b.replace(old,stages[order]).replace(factors[0],factors[factor])
    vs.append((f'stage{order}-factor{factor}-pointer{pointer}',base[:f.body.s]+bb+base[f.body.e:],
               'Same volume sum and six-bit attenuation factor; explicit table pointer address is value equivalent'))
assert len({s for _,s,_ in vs})==30
rows=variants.run(ctx,vs,extra_funcs=[name],claims_only=True,jobs=2,out_dir=out)
for row,(_,source,_) in zip(rows,vs):
    row['source_sha256_lf']=hashlib.sha256(source.encode()).hexdigest()
    r=row['result'];t=r.get('claims',{}).get(name,{})
    print(row['name'],r.get('compile_ok'),t.get('exact'),t.get('reasons'),
          'peer_losses',[n for n,c in r.get('claims',{}).items() if n!=name and not c['exact']],
          'data_losses',[n for n,c in r.get('data',{}).items() if not c['exact']],flush=True)
(out/'results.json').write_text(json.dumps({'function':name,'module':ctx.key,'profile':ctx.profile,
 'flags':ctx.flags,'placements':ctx.placements,'variants':rows},indent=1)+'\n',encoding='utf-8')
