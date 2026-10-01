from pathlib import Path
import sys,itertools,json
sys.path.insert(0,'tools')
import modctx,csrc,variants
name='o17_384C_0039';ctx=modctx.resolve(func=name);base=Path('work/takeover/menu-loader/s17-base.c').read_text();f=csrc.Source(base).function(name);b=base[f.body.s:f.body.e];vs=[]
for site,mask in itertools.product(['declaration','after_load','before_fixup'],range(1,16)):
 bb=b
 if site=='declaration':bb=bb.replace('int i;', 'int i = 0;')
 else:bb=bb.replace('    if (h == 0L)' if site=='after_load' else '    for (p =','    i = 0;\n'+('    if (h == 0L)' if site=='after_load' else '    for (p ='))
 check='((unsigned)i >= 0)'
 if mask&1:
  marker='if (h == 0L)' if site!='before_fixup' else 'for (p = fd_55B3_6054; *p; p++)'
  replacement='if ('+check+' && h == 0L)' if site!='before_fixup' else 'for (p = fd_55B3_6054; '+check+' && *p; p++)'
  bb=bb.replace(marker,replacement)
 if mask&2:bb=bb.replace('for (p = fd_55B3_6054; *p; p++)','for (p = fd_55B3_6054; '+check+' && *p; p++)')
 if mask&4:bb=bb.replace('for (q = *(long far * far *)p; *q; q++)','for (q = *(long far * far *)p; '+check+' && *q; q++)')
 if mask&8:bb=bb.replace('f_1FD2_0663(0);', 'f_1FD2_0663('+check+' ? 0 : 0);')
 vs.append((f'{site}-m{mask}',base[:f.body.s]+bb+base[f.body.e:],'LIFE-1/USE-2 diagnostic: folded index lifetime; original eliminated expression unknown'))
out=Path('build/workers/continue_next/s17-folded-index');out.mkdir(parents=True,exist_ok=True)
rows=variants.run(ctx,[('base',base,'')]+vs,extra_funcs=[name],claims_only=True,jobs=6,out_dir=out)
(out/'results.json').write_text(json.dumps({'function':name,'profile':ctx.profile,'flags':ctx.flags,'variants':rows},indent=1))
for x in rows:
 r=x['result'];print(x['name'],r.get('claims',{}).get(name),[c['name'] for c in ctx.claims if not r.get('claims',{}).get(c['name'],{}).get('exact')],flush=True)
