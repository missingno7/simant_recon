from pathlib import Path
import sys,json,re
sys.path.insert(0,'tools')
import modctx,variants,srcrules,csrc
name='CalcScore';ctx=modctx.resolve(func=name)
p=Path('build/workers/context_next/score-phase-homes/001_history-sum2False-drop_tFalse-reverseFalse.c')
text=p.read_text();f=csrc.Source(text).function(name);pic=csrc.Source(text).function('PictureDialog')
out=Path('build/workers/context_next/score-peer-repair');out.mkdir(exist_ok=True)
vs=[('base',text,'')]
for m in re.finditer(r'^extern [^\n]*;',text,re.M):
 if not f.body.e<m.start()<pic.body.s:continue
 line=m.group();call=re.search(r'\b([A-Za-z_]\w*)\s*\(',line)
 if not call or '(*' in line or '* far g_' in line or '* near g_' in line:continue
 lp=call.end()-1;rp=line.rfind(')');ps=srcrules.split_params(line[lp+1:rp]);pos=lp+1
 for idx,param in enumerate(ps):
  pname=srcrules.param_name(param.strip())
  if pname:
   replacement=re.sub(r'\b'+re.escape(pname)+r'\b','',param)
   new=ps.copy();new[idx]=replacement
   newline=line[:lp+1]+','.join(new)+line[rp:]
   cand=text[:m.start()]+newline+text[m.end():]
   vs.append((call.group(1)+'-'+pname,cand,'remove one real prototype parameter name after CalcScore'))
rows=variants.run(ctx,vs,extra_funcs=[name],claims_only=True,jobs=6,out_dir=out)
(out/'results.json').write_text(json.dumps({'function':name,'profile':ctx.profile,'flags':ctx.flags,'variants':rows},indent=1))
for row in rows:
 r=row['result'];print(row['name'],r.get('exact'),r.get('claims',{}).get(name),[c['name'] for c in ctx.claims if not r.get('claims',{}).get(c['name'],{}).get('exact')],flush=True)
