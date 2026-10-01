from pathlib import Path
import sys,json,hashlib
sys.path.insert(0,'tools')
import modctx,variants
name='f_23E6_0000';base=Path('work/takeover/menu-loader/list-base.c').read_text(encoding='utf-8')
ctx=modctx.resolve(func=name,source='work/takeover/menu-loader/list-base.c');out=Path('build/workers/fleet_list/huge-pointer');out.mkdir(parents=True,exist_ok=True)
vs=[('base',base,''),('local-huge',base.replace('char far *s;','char huge *s;',1),''),('ret-and-local-huge',base.replace('char far * far f_171C_1B84','char huge * far f_171C_1B84',1).replace('char far *s;','char huge *s;',1),''),('cast-huge-offset',base.replace('s = f_171C_1B84(list->text) + off;','s = (char huge *)f_171C_1B84(list->text) + off;',1).replace('char far *s;','char huge *s;',1),'')]
rows=variants.run(ctx,vs,extra_funcs=[name],claims_only=True,jobs=2,out_dir=out)
(out/'results.json').write_text(json.dumps({'function':name,'profile':ctx.profile,'flags':ctx.flags,'placements':ctx.placements,'base_sha256':hashlib.sha256(base.replace('\r\n','\n').encode()).hexdigest(),'variants':rows},indent=1))
for x in rows:
 r=x['result'];c=r.get('claims',{}).get(name,{})
 lost=[q['name'] for q in ctx.claims if not r.get('claims',{}).get(q['name'],{}).get('exact')]
 print(x['name'],'exact=',c.get('exact'),'reasons=',c.get('reasons'),'peer_losses=',lost)
