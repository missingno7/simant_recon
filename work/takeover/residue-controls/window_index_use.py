from pathlib import Path
import sys,json,itertools
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'tools'))
import autosearch,csrc,modctx
name='f_2505_0453';text=autosearch.unscaffold((ROOT/'src/root/m2505.c').read_text(),name)
f=csrc.Source(text).function(name);b=text[f.body.s:f.body.e]
out=ROOT/'build/workers/takeover/window-index-use';out.mkdir(exist_ok=True);vs=[]
for ty in ['int','unsigned','register int']:
 for expr in ['obj & 0xff','(unsigned)obj % 256','(unsigned)obj & 0xffU','(unsigned char)obj']:
  for fold in ['none','before','after','return']:
   bb=b.replace('int idx;',ty+' idx;').replace('idx = obj & 0xff;','idx = '+expr+';')
   cond='*(int far *)(w + 0xc) > '+('(int)idx' if ty=='unsigned' else 'idx')
   bb=bb.replace('*(int far *)(w + 0xc) > idx',cond)
   if fold in ['before','after']:
    check='((unsigned)idx >= 0)';new=check+' && ('+cond+')' if fold=='before' else '('+cond+') && '+check
    bb=bb.replace('if ('+cond+')','if ('+new+')')
   elif fold=='return':bb=bb.replace('return r[kind];','return ((unsigned)idx >= 0) ? r[kind] : r[kind];')
   vs.append(('v'+str(len(vs)),text[:f.body.s]+bb+text[f.body.e:]))
ev=autosearch.Evaluator(modctx.resolve(func=name),name,6,out/'cache');rows=[]
for (n,t),r in zip(vs,ev.many([t for _,t in vs])):
 (out/(n+'.c')).write_text(t);rows.append({'name':n,**r});print(n,r.get('score'),r.get('all_exact'),flush=True)
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1))
