from pathlib import Path
import sys,itertools,json,re
sys.path.insert(0,'tools')
import csrc,modctx,variants
name='o15_384C_0239';ctx=modctx.resolve(func=name);base=Path('work/takeover/phase-next/s15-base.c').read_text();f=csrc.Source(base).function(name);b=base[f.body.s:f.body.e];vs=[]
for rect,event in itertools.product(['struct','words','bytes','longs'],['struct','words','bytes']):
 if rect=='struct' and event=='struct':continue
 bb=b
 if rect!='struct':
  decl={'words':'int r[4];','bytes':'char r[8];','longs':'long r[2];'}[rect]
  bb=bb.replace('struct Rect r;',decl);bb=re.sub(r'&r\b','(struct Rect far *)r',bb)
 if event!='struct':
  decl='int ev[8];' if event=='words' else 'char ev[16];';bb=bb.replace('struct Event ev;',decl).replace('win_GetEvent(&ev)','win_GetEvent((struct Event far *)ev)')
  bb=bb.replace('ev.code','ev[6]' if event=='words' else '((struct Event near *)ev)->code')
 vs.append((f'rect-{rect}-event-{event}',base[:f.body.s]+bb+base[f.body.e:],''))
out=Path('build/workers/phase_next/s15-aggregate-storage');out.mkdir(parents=True,exist_ok=True)
rows=variants.run(ctx,[('base',base,'')]+vs,extra_funcs=[name],claims_only=True,jobs=6,out_dir=out)
(out/'results.json').write_text(json.dumps({'function':name,'profile':ctx.profile,'flags':ctx.flags,'variants':rows},indent=1))
for x in rows:
 r=x['result'];print(x['name'],r.get('claims',{}).get(name),[c['name'] for c in ctx.claims if not r.get('claims',{}).get(c['name'],{}).get('exact')],flush=True)
