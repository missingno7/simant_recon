from pathlib import Path
import sys,json,hashlib
sys.path.insert(0,'tools')
import modctx,variants
name='f_23E6_0000';base=Path('work/takeover/menu-loader/list-base.c').read_text(encoding='utf-8')
ctx=modctx.resolve(func=name,source='work/takeover/menu-loader/list-base.c');out=Path('build/workers/fleet_list/far-assignment');out.mkdir(parents=True,exist_ok=True)
# Explicit assignment is a distinct C expression from the archived compound assignment and
# next-pointer tests. It asks whether materializing the far-pointer value keeps its segment live.
vs=[('base',base,''),
    ('far-pointer-assignment',base.replace('s += _fstrlen(s) + 1;','s = s + _fstrlen(s) + 1;',1),''),
    ('parenthesized-far-pointer-assignment',base.replace('s += _fstrlen(s) + 1;','s = s + (_fstrlen(s) + 1);',1),''),
    ('right-associated-far-pointer-assignment',base.replace('s += _fstrlen(s) + 1;','s = (s + 1) + _fstrlen(s);',1),'')]
rows=variants.run(ctx,vs,extra_funcs=[name],claims_only=True,jobs=2,out_dir=out)
(out/'results.json').write_text(json.dumps({'function':name,'profile':ctx.profile,'flags':ctx.flags,'placements':ctx.placements,'base_sha256':hashlib.sha256(base.replace('\r\n','\n').encode()).hexdigest(),'variants':rows},indent=1))
for x in rows:
 r=x['result'];c=r.get('claims',{}).get(name,{})
 lost=[q['name'] for q in ctx.claims if not r.get('claims',{}).get(q['name'],{}).get('exact')]
 print(x['name'],'exact=',c.get('exact'),'reasons=',c.get('reasons'),'peer_losses=',lost)
