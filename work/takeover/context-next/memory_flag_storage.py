"""Real scalar Boolean types and explicit word accesses, after peer-context repair."""
from pathlib import Path
import sys,json,itertools
sys.path.insert(0,'tools')
import csrc,modctx,autosearch,variants
name='f_171C_0CF4';ctx=modctx.resolve(func=name)
base=Path('build/workers/context_next/memory-alias/004_before_size-all.c').read_text()
fn=csrc.Source(base).function(name);body=base[fn.body.s:fn.body.e]
out=Path('build/workers/context_next/memory-flag-storage');out.mkdir(parents=True,exist_ok=True)
drafts=[('base',base,'')]
for ty,access in itertools.product(['int','unsigned','volatile int','volatile unsigned','long','unsigned long'],['direct','word','volatile-word']):
    bb=body.replace('unsigned long moved;',ty+' moved;')
    if access=='direct':bb=bb.replace('*(int near *)&moved','(int)moved')
    elif access=='word':
        bb=bb.replace('moved = 0;', '*(int near *)&moved = 0;').replace('moved = 1;', '*(int near *)&moved = 1;')
    else:
        bb=bb.replace('*(int near *)&moved','*(volatile int near *)&moved').replace('moved = 0;', '*(volatile int near *)&moved = 0;').replace('moved = 1;', '*(volatile int near *)&moved = 1;')
    label=ty.replace(' ','-')+'-'+access
    drafts.append((label,base[:fn.body.s]+bb+base[fn.body.e:],''))
rows=variants.run(ctx,drafts,extra_funcs=[name],claims_only=True,jobs=6,out_dir=out)
(out/'results.json').write_text(json.dumps({'profile':ctx.profile,'flags':ctx.flags,'variants':rows},indent=1))
for row in rows:
    r=row['result'];v=r.get('claims',{}).get(name,{})
    print(row['name'],v.get('exact'),v.get('reasons'),[c['name'] for c in ctx.claims if not r.get('claims',{}).get(c['name'],{}).get('exact')],flush=True)
