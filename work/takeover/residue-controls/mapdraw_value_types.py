from pathlib import Path
import sys,json,itertools,re
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'tools'))
import autosearch,csrc,modctx
name='f_0250_1018';text=autosearch.unscaffold((ROOT/'src/root/m0250.c').read_text(),name)
f=csrc.Source(text).function(name);b=text[f.body.s:f.body.e]
out=ROOT/'build/workers/takeover/mapdraw-value-types';out.mkdir(exist_ok=True);vs=[]
for split in [False,True]:
 for ty in ['int','unsigned short','unsigned char','volatile unsigned char']:
  for coords in ['plain','mx','my','both']:
   for scentreg in [False,True] if split else [False]:
    bb=b.replace('    int v;','    '+ty+' v;')
    if split:
     at=bb.index('        v = LifeA')
     # The pheromone word and creature byte are separate values and lifetimes.
     part=bb[:at];part=re.sub(r'\bv\b','scent',part)
     part=part.replace('    '+ty+' scent;', '    '+ty+' v;\n    '+('register ' if scentreg else '')+'int scent;')
     bb=part+bb[at:]
    for c in ['mx','my']:
     if coords in [c,'both']:bb=bb.replace('    int '+c+';','    register int '+c+';')
    vs.append(('v'+str(len(vs)),text[:f.body.s]+bb+text[f.body.e:]))
ev=autosearch.Evaluator(modctx.resolve(func=name),name,6,out/'cache');rows=[]
for (n,t),r in zip(vs,ev.many([t for _,t in vs])):
 (out/(n+'.c')).write_text(t);rows.append({'name':n,**r});print(n,r.get('score'),r.get('all_exact'),flush=True)
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1))
