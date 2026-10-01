from pathlib import Path
import sys,json,itertools
ROOT=Path.cwd();sys.path.insert(0,str(ROOT/'tools'))
import modctx,autosearch,csrc
name='o15_384C_0239';ctx=modctx.resolve(func=name);base=ctx.text
f=csrc.Source(base).function(name);b=base[f.body.s:f.body.e]
out=ROOT/'build/workers/blockers/s15-initializers';out.mkdir(parents=True,exist_ok=True);vs=[]
for tinit,hinit,rinit,style in itertools.product([False,True],[False,True],[False,True],['decl','early','after_open']):
    bb=b
    if style=='decl':
        if tinit:bb=bb.replace('char far *text;','char far *text = 0L;')
        if hinit:bb=bb.replace('Handle h;','Handle h = 0L;')
        if rinit:bb=bb.replace('int result;','int result = 0;')
    else:
        stmts=['text = 0L;' if tinit else '', 'h = 0L;' if hinit else '', 'result = 0;' if rinit else '']
        stmts='\n    '.join(s for s in stmts if s)
        if style=='early':bb=bb.replace('    win_Open(0x2100);','    '+stmts+'\n    win_Open(0x2100);')
        else:bb=bb.replace('    win_Open(0x2100);','    win_Open(0x2100);\n    '+stmts)
    vs.append(('v'+str(len(vs)),base[:f.body.s]+bb+base[f.body.e:],tinit,hinit,rinit,style))
ev=autosearch.Evaluator(ctx,name,6,out/'cache');rows=[]
for (n,t,*meta),r in zip(vs,ev.many([t for _,t,*_ in vs])):
    (out/(n+'.c')).write_text(t);rows.append({'name':n,'meta':meta,**r})
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1));print([(r['name'],r.get('score'),r.get('all_exact')) for r in rows])
