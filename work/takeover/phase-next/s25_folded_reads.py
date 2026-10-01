from pathlib import Path
import sys,itertools,json
sys.path.insert(0,'tools')
import csrc,modctx,variants
name='o25_3BA4_1035';ctx=modctx.resolve(func=name);base=Path('work/takeover/phase-next/s25-base.c').read_text();f=csrc.Source(base).function(name);b=base[f.body.s:f.body.e]
fields=['fd_50F6_048C','fd_50F6_047C','fd_50F6_048A'];vs=[]
for mask,kind,side in itertools.product(range(1,8),['word','byte'],['before','after']):
 checks=[f'((unsigned{ " char" if kind=="byte" else ""}){field} >= 0)' for i,field in enumerate(fields) if mask&(1<<i)];check=' && '.join(checks);cond=check+' && fd_50F6_048C == 2' if side=='before' else 'fd_50F6_048C == 2 && '+check
 bb=b.replace('if (fd_50F6_048C == 2)', 'if ('+cond+')');vs.append((f'm{mask}-{kind}-{side}',base[:f.body.s]+bb+base[f.body.e:],'USE-1/USE-2 diagnostic: original eliminated expression unknown; any match requires STEERED'))
for field in fields:
 expr='((unsigned)'+field+' >= 0 ? '+field+' : '+field+')'
 bb=b.replace('DigMyTile(fd_50F6_048C, fd_50F6_047C, fd_50F6_048A)', 'DigMyTile('+', '.join(expr if x==field else x for x in fields)+')')
 vs.append(('argument-'+field,base[:f.body.s]+bb+base[f.body.e:],'folded argument control'))
out=Path('build/workers/phase_next/s25-folded-reads');out.mkdir(parents=True,exist_ok=True)
rows=variants.run(ctx,[('base',base,'')]+vs,extra_funcs=[name],claims_only=True,jobs=6,out_dir=out)
(out/'results.json').write_text(json.dumps({'function':name,'profile':ctx.profile,'flags':ctx.flags,'variants':rows},indent=1))
for x in rows:
 r=x['result'];print(x['name'],r.get('claims',{}).get(name),[c['name'] for c in ctx.claims if not r.get('claims',{}).get(c['name'],{}).get('exact')],flush=True)
