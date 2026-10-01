from pathlib import Path
import sys,json,itertools
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'tools'))
import autosearch,csrc,modctx
name='f_2505_0453';text=autosearch.unscaffold((ROOT/'src/root/m2505.c').read_text(),name)
f=csrc.Source(text).function(name);b=text[f.body.s:f.body.e]
out=ROOT/'build/workers/takeover/window-typed-view';out.mkdir(exist_ok=True);vs=[]
for prefix in ['int prefix[6];','long prefix[3];','char prefix[12];']:
 for scope in ['local','global']:
  for idx in ['normal','volatile','unsigned']:
   view='struct WindowView { '+prefix+' int count; int middle[15]; int far *objects[1]; };'
   bb=b.replace('char far *w;','struct WindowView far *w;')
   bb=bb.replace('w = f_2505_0006(win);','w = (struct WindowView far *)f_2505_0006(win);')
   bb=bb.replace('*(int far *)(w + 0xc)','w->count')
   bb=bb.replace('((int far * far *)(w + 0x2c))[idx]','w->objects[idx]')
   if idx=='volatile':bb=bb.replace('int idx;','volatile int idx;')
   elif idx=='unsigned':bb=bb.replace('int idx;','unsigned idx;').replace('w->count > idx','w->count > (int)idx')
   if scope=='local':bb=bb.replace('{\n','{\n    '+view+'\n',1);tt=text[:f.body.s]+bb+text[f.body.e:]
   else:tt=text[:f.head_s]+view+'\n'+text[f.head_s:f.body.s]+bb+text[f.body.e:]
   vs.append(('v'+str(len(vs)),tt))
ev=autosearch.Evaluator(modctx.resolve(func=name),name,6,out/'cache');rows=[]
for (n,t),r in zip(vs,ev.many([t for _,t in vs])):
 (out/(n+'.c')).write_text(t);rows.append({'name':n,**r});print(n,r.get('score'),r.get('all_exact'),flush=True)
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1))
