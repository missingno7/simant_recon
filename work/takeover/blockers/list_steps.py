from pathlib import Path
import sys,json,itertools
ROOT=Path.cwd();sys.path.insert(0,str(ROOT/'tools'))
import modctx,autosearch,csrc
name='f_23E6_0000';ctx=modctx.resolve(func=name);base=autosearch.unscaffold(ctx.text,name);f=csrc.Source(base).function(name);b=base[f.body.s:f.body.e]
out=ROOT/'build/workers/blockers/list-steps';out.mkdir(parents=True,exist_ok=True);vs=[]
updates=['s += _fstrlen(s);\n        s++;','s = s + _fstrlen(s);\n        s++;','s += _fstrlen(s);\n        ++s;','s = &s[_fstrlen(s)];\n        s++;','s = s + (_fstrlen(s) + 1);','s = (_fstrlen(s) + s) + 1;', 's += 1 + _fstrlen(s);', 's = &_fstrlen(s)[s] + 1;']
for update,nform in itertools.product(updates,['after','before','for']):
    bb=b.replace('s += _fstrlen(s) + 1;',update)
    if nform=='before':bb=bb.replace('        '+update+'\n        n++;','        n++;\n        '+update)
    elif nform=='for':bb=bb.replace('while (n < line)', 'for (; n < line; n++)').replace('        n++;\n','')
    vs.append(('v'+str(len(vs)),base[:f.body.s]+bb+base[f.body.e:],update,nform))
ev=autosearch.Evaluator(ctx,name,6,out/'cache');rows=[]
for (n,t,*meta),r in zip(vs,ev.many([t for _,t,*_ in vs])):
    (out/(n+'.c')).write_text(t);rows.append({'name':n,'meta':meta,**r})
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1));print([(r['name'],r.get('score'),r.get('all_exact')) for r in rows])
