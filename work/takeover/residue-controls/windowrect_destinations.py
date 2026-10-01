from pathlib import Path
import sys,json,re
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'tools'))
import autosearch,csrc,modctx
name='f_20E8_0903';ctx=modctx.resolve(func=name);base=autosearch.unscaffold(ctx.source.read_text(),name)
f=csrc.Source(base).function(name);b=base[f.body.s:f.body.e]
out=ROOT/'build/workers/takeover/windowrect-destinations';out.mkdir(exist_ok=True);vs=[]
forms=['origin[i]','i[origin]','*(origin + i)','*(i + origin)','*(int far *)((char far *)origin + i * 2)','*(int far *)(i * 2 + (char far *)origin)','*(int far *)((char far *)origin + (i << 1))','((int far (*)[4])origin)[0][i]']
for form in forms:
 for scope in ['store','all']:
  for fold in ['none','index_after','pointer_after','index_before']:
   bb=b.replace('origin[i]',form)
   if scope=='all':bb=bb.replace('origin[j]',re.sub(r'\bi\b','j',form))
   cond='mode[i] && mode[i] != 5 && ref[i] == obj'
   if fold=='index_after':bb=bb.replace(cond,'('+cond+') && (unsigned)i >= 0')
   elif fold=='pointer_after':bb=bb.replace(cond,'('+cond+') && (unsigned)origin >= 0')
   elif fold=='index_before':bb=bb.replace(cond,'(unsigned)i >= 0 && ('+cond+')')
   vs.append(('v'+str(len(vs)),base[:f.body.s]+bb+base[f.body.e:]))
ev=autosearch.Evaluator(ctx,name,6,out/'cache');rows=[]
for (n,t),r in zip(vs,ev.many([t for _,t in vs])):
 (out/(n+'.c')).write_text(t);rows.append({'name':n,**r});print(n,r.get('score'),r.get('all_exact'),flush=True)
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1))
