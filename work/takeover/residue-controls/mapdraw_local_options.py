from pathlib import Path
import sys,json,itertools
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'tools'))
import autosearch,csrc,modctx
name='f_0250_1018';text=autosearch.unscaffold((ROOT/'src/root/m0250.c').read_text(),name)
f=csrc.Source(text).function(name);b=text[f.body.s:f.body.e]
out=ROOT/'build/workers/takeover/mapdraw-local-options';out.mkdir(exist_ok=True);vs=[]
for opt in ['g','e','eg']:
 for order in ['vfirst','vlast']:
  for regs in ['none','coords','all']:
   bb=b
   if order=='vlast':bb=bb.replace('    int v;\n','').replace('    int my;','    int my;\n    int v;')
   for var in ['v','mx','my']:
    if regs=='all' or (regs=='coords' and var!='v'):bb=bb.replace('    int '+var+';','    register int '+var+';')
   tt=text[:f.head_s]+'#pragma optimize("'+opt+'", off)\n'+text[f.head_s:f.body.s]+bb+text[f.body.e:f.e]+'\n#pragma optimize("'+opt+'", on)\n'+text[f.e:]
   vs.append(('v'+str(len(vs)),tt))
ev=autosearch.Evaluator(modctx.resolve(func=name),name,6,out/'cache');rows=[]
for (n,t),r in zip(vs,ev.many([t for _,t in vs])):
 (out/(n+'.c')).write_text(t);rows.append({'name':n,**r});print(n,r.get('score'),r.get('all_exact'),flush=True)
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1))
