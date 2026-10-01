"""Test a real cached rectangle address before the far string acquisition."""
from pathlib import Path
import sys,json,itertools
sys.path.insert(0,'tools')
import csrc,modctx,autosearch,variants
name='o15_384C_0239';ctx=modctx.resolve(func=name);base=autosearch.unscaffold(ctx.text,name)
fn=csrc.Source(base).function(name);body=base[fn.body.s:fn.body.e]
out=Path('build/workers/context_next/s15-rect-address');out.mkdir(parents=True,exist_ok=True)
drafts=[('base',base,'')]
for ty,site,scope in itertools.product(['struct Rect far *','struct Rect near *'],['entry','after_handle','after_text'],['all','draw']):
    bb=body.replace('    int result;','    int result;\n    '+ty+'rect;')
    if scope=='all':bb=bb.replace('&r','rect')
    else:bb=bb.replace('f_1CE2_044D(&r, 2);','f_1CE2_044D(rect, 2);').replace('win_PrintTextInRect(0, text, &r);','win_PrintTextInRect(0, text, rect);')
    if site=='entry':bb=bb.replace('    win_Open(0x2100);','    rect = &r;\n    win_Open(0x2100);')
    elif site=='after_handle':bb=bb.replace('    text = f_171C_1B84(h);','    rect = &r;\n    text = f_171C_1B84(h);')
    else:bb=bb.replace('    text = f_171C_1B84(h);','    text = f_171C_1B84(h);\n    rect = &r;')
    label=ty.split()[2]+'-'+site+'-'+scope
    drafts.append((label,base[:fn.body.s]+bb+base[fn.body.e:],''))
rows=variants.run(ctx,drafts,extra_funcs=[name],claims_only=True,jobs=6,out_dir=out)
(out/'results.json').write_text(json.dumps({'profile':ctx.profile,'flags':ctx.flags,'variants':rows},indent=1))
for row in rows:
    v=row['result'].get('claims',{}).get(name,{})
    print(row['name'],v.get('exact'),v.get('reasons'),flush=True)
