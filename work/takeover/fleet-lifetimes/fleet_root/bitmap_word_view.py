from pathlib import Path
import sys, json, itertools, hashlib
sys.path.insert(0, 'tools')
import csrc, modctx, variants

name='win_DrawBitMap'
ctx=modctx.resolve(func=name)
base=Path('work/takeover/residue-controls/bitmap-original-order.c').read_text(encoding='utf-8')
f=csrc.Source(base).function(name)
b=base[f.body.s:f.body.e]
out=Path('build/workers/fleet_root/bitmap-word-view')
out.mkdir(parents=True,exist_ok=True)
vs=[('base',base,'')]
for typ, remove_header, flag in itertools.product(['int','unsigned int'],[False,True],['literal','early','type3']):
    bb=b.replace('struct Pic far *pic;', typ+' far *pic;')
    bb=bb.replace('pic = *(struct Pic far * far *)h;', 'pic = *('+typ+' far * far *)h;')
    bb=bb.replace('pic->type','((int)pic[0])').replace('pic->width','((int)pic[4])').replace('pic->height','((int)pic[5])').replace('pic->mode','((unsigned char far *)pic)[2]')
    # The second type check intentionally reloads through the handle, as in the oracle.
    bb=bb.replace('(*(struct Pic far * far *)h)->type', '(**(int far * far *)h)')
    if flag!='literal':
        bb=bb.replace('    unsigned int n;', '    unsigned int n;\n    int flag;')
        if flag=='early':bb=bb.replace('    h = db_LoadObject', '    flag = 0;\n    h = db_LoadObject',1)
        else:bb=bb.replace('        if (((int)pic[0]) == 3) {','        if (((int)pic[0]) == 3) {\n            flag = 0;')
        bb=bb.replace(', x & 1, 0);',', x & 1, flag);').replace(', x & 7, 0);',', x & 7, flag);')
    text=base[:f.body.s]+bb+base[f.body.e:]
    if remove_header:
        a=text.index('struct Pic {');z=text.index('};',a)+3
        text=text[:a]+text[z:]
    vs.append((f'{typ}-header{not remove_header}-flag{flag}',text,'Win16 semantic counterpart uses an int far pointer; DOS offsets independently anchored by original loads'))
rows=variants.run(ctx,vs,extra_funcs=[name],claims_only=True,jobs=2,out_dir=out)
for row,(_,source,_) in zip(rows,vs):
    row['source_sha256_lf']=hashlib.sha256(source.encode()).hexdigest()
    r=row['result'];losses=[c['name'] for c in ctx.claims if not r.get('claims',{}).get(c['name'],{}).get('exact')]
    print(row['name'],r.get('claims',{}).get(name), 'peer losses',losses,flush=True)
(out/'results.json').write_text(json.dumps({'function':name,'profile':ctx.profile,'flags':ctx.flags,'variants':rows},indent=1)+'\n',encoding='utf-8')
