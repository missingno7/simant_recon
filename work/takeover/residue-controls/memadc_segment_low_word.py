from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'tools'))
import autosearch,csrc,modctx
name='f_171C_0ADC';ctx=modctx.resolve(func=name);base=autosearch.unscaffold(ctx.source.read_text(),name)
f=csrc.Source(base).function(name);b=base[f.body.s:f.body.e]
out=ROOT/'build/workers/takeover/memadc-segment-low-word';out.mkdir(exist_ok=True);vs=[]
for segvalue in ['*(unsigned *)&seg','*(unsigned far *)&seg','FP_OFF(seg)','(unsigned)seg']:
 for first in ['SEG(b)','(unsigned)SEG(b)','FP_SEG(b)']:
  for null in ['n','SEG(n)']:
   bb=b.replace('seg = SEG(b);','seg = '+first+';').replace('BLK(b->paras + seg)', 'BLK(b->paras + '+segvalue+')').replace('if (n)', 'if ('+null+')')
   vs.append(('v'+str(len(vs)),base[:f.body.s]+bb+base[f.body.e:]))
ev=autosearch.Evaluator(ctx,name,6,out/'cache');rows=[]
for (n,t),r in zip(vs,ev.many([t for _,t in vs])):
 (out/(n+'.c')).write_text(t);rows.append({'name':n,**r});print(n,r.get('score'),r.get('all_exact'),flush=True)
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1))
