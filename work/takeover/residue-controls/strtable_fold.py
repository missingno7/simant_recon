from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'tools'))
import autosearch,csrc,modctx
name='f_23E6_0000';text=autosearch.unscaffold((ROOT/'src/root/m23E6.c').read_text(),name)
f=csrc.Source(text).function(name);b=text[f.body.s:f.body.e]
out=ROOT/'build/workers/takeover/strtable-fold';out.mkdir(exist_ok=True);vs=[]
for expr in ['((unsigned long)s >= 0)','((unsigned long)s < 0)','((unsigned)s >= 0)','((unsigned)s < 0)']:
 for site in ['while','break','increment','pointer','after','return']:
  bb=b
  truth=' < 0)' not in expr
  if site=='while':bb=bb.replace('while (n < line)', 'while (n < line && '+(expr if truth else '!'+expr)+')')
  elif site=='break':bb=bb.replace('if (*s == 0)', 'if (*s == 0 '+('&& '+expr if truth else '|| '+expr)+')')
  elif site=='increment':bb=bb.replace('n++;','n += '+(expr if truth else '(1 + '+expr+')')+';')
  elif site=='pointer':bb=bb.replace('_fstrlen(s) + 1','_fstrlen(s) + '+(expr if truth else '(1 + '+expr+')'))
  elif site=='after':bb=bb.replace('n++;', 'if ('+expr+') n++;' if truth else 'if (!'+expr+') n++;')
  else:bb=bb.replace('return s;','return '+expr+' ? s : s;')
  vs.append(('v'+str(len(vs)),text[:f.body.s]+bb+text[f.body.e:]))
ev=autosearch.Evaluator(modctx.resolve(func=name),name,4,out/'cache');rows=[]
for (n,t),r in zip(vs,ev.many([t for _,t in vs])):
 (out/(n+'.c')).write_text(t);rows.append({'name':n,**r});print(n,r.get('score'),r.get('all_exact'),flush=True)
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1))
