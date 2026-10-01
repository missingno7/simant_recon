from pathlib import Path
import sys,itertools,json,re
sys.path.insert(0,'tools')
import modctx,csrc,variants
name='o17_384C_0039';ctx=modctx.resolve(func=name);base=Path('work/takeover/menu-loader/s17-folded-index-near.c').read_text();f=csrc.Source(base).function(name);b=base[f.body.s:f.body.e];vs=[]
for ref,site in itertools.product(['(unsigned)h','(unsigned long)h','(unsigned char)(unsigned)h','(unsigned)r','(unsigned long)r','(unsigned char)(unsigned)r'],['before','after']):
 bb=b
 if ref.endswith('h') or ref.endswith('h)'):
  cond='h == 0L';expr='('+ref+' >= 0)'
 else:cond='*r';expr='('+ref+' >= 0)'
 if cond=='h == 0L':bb=bb.replace('if (h == 0L)', 'if ('+ (expr+' && '+cond if site=='before' else cond+' && '+expr)+')')
 else:bb=bb.replace('; *r; i++, r++)','; '+(expr+' && *r' if site=='before' else '*r && '+expr)+'; i++, r++)')
 vs.append((ref.replace(' ','-').replace('(','').replace(')','')+'-'+site,base[:f.body.s]+bb+base[f.body.e:],'folded pointer-use ranking; original eliminated expression unknown'))
for ref in ['(unsigned char)i','(unsigned long)i','(*(unsigned near *)&i)','(*(unsigned char near *)&i)']:
 bb=b.replace('(unsigned)i',ref)
 vs.append(('index-view-'+str(len(vs)),base[:f.body.s]+bb+base[f.body.e:],'folded index view; original eliminated expression unknown'))
# Vary scope and declaration order only for these real, used locals.
for scope,order in itertools.product([False,True],[False,True]):
 bb=b
 if scope:bb=bb.replace('    int i;\n','').replace('    i = 0;','    {\n    int i;\n    i = 0;').replace('    return 1;','    }\n    return 1;')
 elif order:bb=bb.replace('    int i;\n','').replace('    long far * far *h;', '    int i;\n    long far * far *h;')
 if scope and order:continue
 vs.append((f'scope-{scope}-order-{order}',base[:f.body.s]+bb+base[f.body.e:],''))
# A used reset parameter local, without a folded source expression.
raw=Path('work/takeover/menu-loader/s17-base.c').read_text();rf=csrc.Source(raw).function(name);rb=raw[rf.body.s:rf.body.e]
for typ,site in itertools.product(['int','unsigned','unsigned char'],['entry','before_fixup','before_clear']):
 bb=rb.replace('    int i;', '    int i;\n    '+typ+' reset;')
 marker={'entry':'    h = db_LoadObject','before_fixup':'    for (p =','before_clear':'    f_1FD2_0663'}[site]
 bb=bb.replace(marker,'    reset = 0;\n'+marker).replace('f_1FD2_0663(0);','f_1FD2_0663(reset);')
 vs.append((f'reset-{typ}-{site}',raw[:rf.body.s]+bb+raw[rf.body.e:],''))
out=Path('build/workers/continue_next/s17-home-ranking');out.mkdir(parents=True,exist_ok=True)
rows=variants.run(ctx,[('base',base,'')]+vs,extra_funcs=[name],claims_only=True,jobs=6,out_dir=out)
(out/'results.json').write_text(json.dumps({'function':name,'profile':ctx.profile,'flags':ctx.flags,'variants':rows},indent=1))
for x in rows:
 r=x['result'];print(x['name'],r.get('claims',{}).get(name),[c['name'] for c in ctx.claims if not r.get('claims',{}).get(c['name'],{}).get('exact')],flush=True)
