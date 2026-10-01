from pathlib import Path
import sys,json,re,itertools
sys.path.insert(0,'tools')
import csrc,modctx,variants
name='o25_3BA4_1035';ctx=modctx.resolve(func=name);base=Path('work/takeover/phase-next/s25-base.c').read_text();vs=[]
fields=['fd_50F6_048C','fd_50F6_047C','fd_50F6_048A']
for field,rep in itertools.product(fields,['short','array','member','unsigned-view']):
 if rep=='short':t=base.replace('extern int far '+field+';', 'extern short far '+field+';')
 else:
  ref=field+'[0]' if rep=='array' else field+'.value' if rep=='member' else '(*(int far *)&'+field+')'
  t=re.sub(r'\b'+field+r'\b',ref,base)
  old='extern int far '+ref+';'
  new=('extern int far '+field+'[1];') if rep=='array' else ('extern struct { int value; } far '+field+';') if rep=='member' else ('extern unsigned far '+field+';')
  assert old in t;t=t.replace(old,new)
 vs.append((field+'-'+rep,t,''))
out=Path('build/workers/phase_next/s25-field-views');out.mkdir(parents=True,exist_ok=True)
rows=variants.run(ctx,[('base',base,'')]+vs,extra_funcs=[name],claims_only=True,jobs=6,out_dir=out)
(out/'results.json').write_text(json.dumps({'function':name,'profile':ctx.profile,'flags':ctx.flags,'variants':rows},indent=1))
for x in rows:
 r=x['result'];print(x['name'],r.get('claims',{}).get(name),[c['name'] for c in ctx.claims if not r.get('claims',{}).get(c['name'],{}).get('exact')],flush=True)
