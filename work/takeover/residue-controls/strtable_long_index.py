from pathlib import Path
import sys,json,itertools
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'tools'))
import autosearch,csrc,modctx
name='f_23E6_0000';text=autosearch.unscaffold((ROOT/'src/root/m23E6.c').read_text(),name)
f=csrc.Source(text).function(name);b=text[f.body.s:f.body.e]
out=ROOT/'build/workers/takeover/strtable-long-index';out.mkdir(exist_ok=True);vs=[]
for expr in ['(long)(_fstrlen(s) + 1)','(unsigned long)(_fstrlen(s) + 1)','(long)_fstrlen(s) + 1','(unsigned long)_fstrlen(s) + 1','_fstrlen(s) + 1L','_fstrlen(s) + 1UL','(int)(_fstrlen(s) + 1)']:
 for form in ['s += EXPR;','s = &(EXPR)[s];','s = &s[EXPR];']:
  bb=b.replace('s += _fstrlen(s) + 1;',form.replace('EXPR',expr))
  vs.append(('v'+str(len(vs)),text[:f.body.s]+bb+text[f.body.e:]))
ev=autosearch.Evaluator(modctx.resolve(func=name),name,6,out/'cache');rows=[]
for (n,t),r in zip(vs,ev.many([t for _,t in vs])):
 (out/(n+'.c')).write_text(t);rows.append({'name':n,**r});print(n,r.get('score'),r.get('all_exact'),flush=True)
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1))
