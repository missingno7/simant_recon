from pathlib import Path
import sys,json,re,itertools
sys.path.insert(0,'tools')
import csrc,modctx,variants,autosearch
name='o25_3BA4_1035';ctx=modctx.resolve(func=name)
base=Path('work/takeover/phase-next/s25-base.c').read_text();f=csrc.Source(base).function(name);b=base[f.body.s:f.body.e];vs=[]
fields=['fd_50F6_048C','fd_50F6_047C','fd_50F6_048A']
for idx,site,reg in itertools.product(range(3),['entry','after_saved'],['','register ']):
 var='fieldPtr';bb=b.replace('{\n','{\n    '+reg+'int far *'+var+';\n',1)
 at=bb.index('    f_10F7_09A8(') if site=='entry' else bb.index('    if (fd_50F6_047C >')
 bb=bb[:at]+'    '+var+' = &'+fields[idx]+';\n'+re.sub(r'\b'+fields[idx]+r'\b','(*'+var+')',bb[at:])
 vs.append((f'pointer-{idx}-{site}-{bool(reg)}',base[:f.body.s]+bb+base[f.body.e:],''))
for var,reg,scope in itertools.product(['x','y','plane'],['','register '],[False,True]):
 field=fields[{'plane':0,'x':1,'y':2}[var]];bb=b
 if scope:
  start=bb.index('    if (fd_50F6_048C == 2)');stop=bb.index('    f_10F7_0A44')
  phase=bb[start:stop].replace(field,var)
  bb=bb[:start]+'    {\n    '+reg+'int '+var+';\n    '+var+' = '+field+';\n'+phase+'    }\n'+bb[stop:]
 else:
  bb=bb.replace('{\n','{\n    '+reg+'int '+var+';\n',1)
  start=bb.index('    if (fd_50F6_048C == 2)');stop=bb.index('    f_10F7_0A44')
  bb=bb[:start]+'    '+var+' = '+field+';\n'+bb[start:stop].replace(field,var)+bb[stop:]
 vs.append((f'value-{var}-{bool(reg)}-{scope}',base[:f.body.s]+bb+base[f.body.e:],''))
# Capture x at the existing x=y store, with no intervening call before DigMyTile.
for ty in ['int','unsigned','long','unsigned long']:
 bb=b.replace('{\n','{\n    '+ty+' x;\n',1).replace('fd_50F6_047C = fd_50F6_048A;', 'x = fd_50F6_048A;\n    fd_50F6_047C = (int)x;')
 bb=bb.replace('DigMyTile(fd_50F6_048C, fd_50F6_047C, fd_50F6_048A)', 'DigMyTile(fd_50F6_048C, (int)x, fd_50F6_048A)')
 vs.append(('copied-x-'+ty.replace(' ','-'),base[:f.body.s]+bb+base[f.body.e:],''))
out=Path('build/workers/phase_next/s25-field-lifetimes');out.mkdir(parents=True,exist_ok=True)
rows=variants.run(ctx,[('base',base,'')]+vs,extra_funcs=[name],claims_only=True,jobs=6,out_dir=out)
(out/'results.json').write_text(json.dumps({'function':name,'profile':ctx.profile,'flags':ctx.flags,'variants':rows},indent=1))
for x in rows:
 r=x['result'];print(x['name'],r.get('claims',{}).get(name),[c['name'] for c in ctx.claims if not r.get('claims',{}).get(c['name'],{}).get('exact')],flush=True)
