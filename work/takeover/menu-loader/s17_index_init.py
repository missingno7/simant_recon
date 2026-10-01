from pathlib import Path
import sys,json,itertools
sys.path.insert(0,'tools')
import modctx,csrc,variants
name='o17_384C_0039';ctx=modctx.resolve(func=name);base=Path('work/takeover/menu-loader/s17-base.c').read_text();f=csrc.Source(base).function(name);b=base[f.body.s:f.body.e];vs=[]
for site,repeat,typ in itertools.product(['declaration','before_load','before_store','before_unhook','before_fixup','before_clear'],[False,True],['int','unsigned']):
 bb=b.replace('    int i;','    '+typ+' i;')
 if site=='declaration':bb=bb.replace('    '+typ+' i;', '    '+typ+' i = 0;')
 else:
  marker={'before_load':'    h = db_LoadObject','before_store':'    fd_55B3_6054 = *h;','before_unhook':'    db_UnhookObject','before_fixup':'    for (p =','before_clear':'    f_1FD2_0663'}[site]
  bb=bb.replace(marker,'    i = 0;\n'+marker)
 if not repeat:bb=bb.replace('for (i = 0, r =', 'for (r =')
 vs.append((f'{site}-repeat{repeat}-{typ}',base[:f.body.s]+bb+base[f.body.e:],''))
out=Path('build/workers/continue_next/s17-index-init');out.mkdir(parents=True,exist_ok=True)
rows=variants.run(ctx,[('base',base,'')]+vs,extra_funcs=[name],claims_only=True,jobs=6,out_dir=out)
(out/'results.json').write_text(json.dumps({'function':name,'profile':ctx.profile,'flags':ctx.flags,'variants':rows},indent=1))
for x in rows:
 r=x['result'];print(x['name'],r.get('claims',{}).get(name),[c['name'] for c in ctx.claims if not r.get('claims',{}).get(c['name'],{}).get('exact')],flush=True)
