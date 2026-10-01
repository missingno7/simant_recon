from pathlib import Path
import sys,json,itertools
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'tools'))
import autosearch,csrc,modctx
name='f_171C_0160';text=autosearch.unscaffold((ROOT/'src/root/m171C.c').read_text(),name)
f=csrc.Source(text).function(name);b=text[f.body.s:f.body.e]
out=ROOT/'build/workers/takeover/freeblock-next';out.mkdir(exist_ok=True);vs=[]
for seg,paras in itertools.product(['SEG(b)','(unsigned)SEG(b)','(int)SEG(b)','FP_SEG(b)','((long)b >> 16)','((unsigned long)b / 65536UL)'],['b->paras','(int)b->paras','(unsigned long)b->paras']):
 for order in [0,1]:
  expr=paras+' + '+seg if order else seg+' + '+paras
  bb=b.replace('NEXTBLK(b)','BLK('+expr+')')
  vs.append(('v'+str(len(vs)),text[:f.body.s]+bb+text[f.body.e:]))
ev=autosearch.Evaluator(modctx.resolve(func=name),name,6,out/'cache');rows=[]
for (n,t),r in zip(vs,ev.many([t for _,t in vs])):
 (out/(n+'.c')).write_text(t);rows.append({'name':n,**r});print(n,r.get('score'),r.get('all_exact'),flush=True)
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1))
