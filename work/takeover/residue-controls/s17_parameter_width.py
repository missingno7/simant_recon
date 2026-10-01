from pathlib import Path
import sys,json,itertools
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'tools'))
import autosearch,csrc,modctx
name='o17_384C_0039';text=autosearch.unscaffold((ROOT/'src/S17/m384C.c').read_text(),name)
f=csrc.Source(text).function(name);old=(ROOT/'work/resF/s17d.c').read_text();of=csrc.Source(old).function(name)
text=text[:f.body.s]+old[of.body.s:of.body.e]+text[f.body.e:]
f=csrc.Source(text).function(name);head=text[f.head_s:f.body.s];b=text[f.body.s:f.body.e]
out=ROOT/'build/workers/takeover/s17-parameter-width';out.mkdir(exist_ok=True);vs=[]
for ty in ['int','unsigned','long','unsigned long','volatile int','register int']:
 for casts in [False,True]:
  hh=head.replace('int id)',ty+' id)')
  bb=b
  if casts:bb=bb.replace('db_LoadObject(id, 6)','db_LoadObject((int)id, 6)').replace('db_UnhookObject(id, 6)','db_UnhookObject((int)id, 6)')
  vs.append(('v'+str(len(vs)),text[:f.head_s]+hh+bb+text[f.body.e:]))
ev=autosearch.Evaluator(modctx.resolve(func=name),name,4,out/'cache');rows=[]
for (n,t),r in zip(vs,ev.many([t for _,t in vs])):
 (out/(n+'.c')).write_text(t);rows.append({'name':n,**r});print(n,r.get('score'),r.get('all_exact'),flush=True)
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1))
