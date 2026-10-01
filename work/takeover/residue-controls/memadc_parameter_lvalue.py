from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'tools'))
import autosearch,csrc,modctx
name='f_171C_0ADC';ctx=modctx.resolve(func=name);base=autosearch.unscaffold(ctx.source.read_text(),name)
f=csrc.Source(base).function(name);b=base[f.body.s:f.body.e]
out=ROOT/'build/workers/takeover/memadc-parameter-lvalue';out.mkdir(exist_ok=True);vs=[]
dataexprs=['(unsigned long)b','*(unsigned long *)&b','*(unsigned long far *)&b','*(unsigned long volatile far *)&b','(unsigned long)*(Block far * volatile *)&b']
for data in dataexprs:
 for nextseg in ['FP_SEG(b)','(unsigned)SEG(b)']:
  for null in ['n','SEG(n)','FP_SEG(n) > 0','(unsigned long)n != 0L']:
   bb=b.replace('seg = SEG(b);','seg = (unsigned)SEG(b);').replace('NEXTBLK(b)', 'BLK('+nextseg+' + (unsigned long)b->paras)').replace('(unsigned long)b + 0x20000L',data+' + 0x20000L').replace('if (n)', 'if ('+null+')')
   vs.append(('v'+str(len(vs)),base[:f.body.s]+bb+base[f.body.e:]))
ev=autosearch.Evaluator(ctx,name,6,out/'cache');rows=[]
for (n,t),r in zip(vs,ev.many([t for _,t in vs])):
 (out/(n+'.c')).write_text(t);rows.append({'name':n,**r});print(n,r.get('score'),r.get('all_exact'),flush=True)
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1))
