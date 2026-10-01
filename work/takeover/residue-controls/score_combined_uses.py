from pathlib import Path
import sys,json,itertools
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'tools'))
import autosearch,csrc,modctx
name='CalcScore';text=autosearch.unscaffold((ROOT/'src/S14/m384C.c').read_text(),name)
f=csrc.Source(text).function(name);b=text[f.body.s:f.body.e]
out=ROOT/'build/workers/takeover/score-combined-uses';out.mkdir(exist_ok=True);vs=[]
sites=[('k < fd_3D57_0828; k++','k < fd_3D57_0828 && CHECK; k++'),('if (j > 0)','if (j > 0 && CHECK)'),('j < 16; j++','j < 16 && CHECK; j++'),('if (fd_3D57_00A4[k][j])','if (fd_3D57_00A4[k][j] && CHECK)'),('if (sum > 0)','if (sum > 0 && CHECK)'),('k < 12; k++','k < 12 && CHECK; k++')]
for check in ['((unsigned)j >= 0)','((unsigned)j <= 65535U)']:
 for mask in range(1,64):
  bb=b
  for bit,(old,new) in enumerate(sites):
   if mask&(1<<bit):bb=bb.replace(old,new.replace('CHECK',check))
  vs.append(('v'+str(len(vs)),text[:f.body.s]+bb+text[f.body.e:]))
ev=autosearch.Evaluator(modctx.resolve(func=name),name,6,out/'cache');rows=[]
for (n,t),r in zip(vs,ev.many([t for _,t in vs])):
 (out/(n+'.c')).write_text(t);rows.append({'name':n,**r})
 if r.get('score')!=[1,12,12,0]:print(n,r.get('score'),r.get('all_exact'),flush=True)
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1));print('Finished',len(rows),flush=True)
