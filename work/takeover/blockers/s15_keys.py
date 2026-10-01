from pathlib import Path
import sys,json,itertools,re
ROOT=Path.cwd();sys.path.insert(0,str(ROOT/'tools'))
import modctx,autosearch,csrc
name='o15_384C_0239';ctx=modctx.resolve(func=name);base=ctx.text
f=csrc.Source(base).function(name);b=base[f.body.s:f.body.e]
out=ROOT/'build/workers/blockers/s15-keys';out.mkdir(parents=True,exist_ok=True);vs=[]
for key,evkey,font,form in itertools.product(['none','int','unsigned','char'],['none','int'],['none','int'],['plain','in_switch']):
    bb=b;decl=[]
    if key!='none':
        decl.append(key+' key;')
        if form=='plain':bb=bb.replace('switch (f_1F58_0090())','key = f_1F58_0090();\n            switch (key)')
        else:bb=bb.replace('switch (f_1F58_0090())','switch (key = f_1F58_0090())')
    if evkey!='none':
        decl.append(evkey+' button;')
        if form=='plain':bb=bb.replace('switch (ev.code)','button = ev.code;\n            switch (button)')
        else:bb=bb.replace('switch (ev.code)','switch (button = ev.code)')
    if font!='none':
        decl.append(font+' font;');bb=bb.replace('f_24AB_02AD(g_3DB2 == 0x140 ? 2 : 4);','font = g_3DB2 == 0x140 ? 2 : 4;\n    f_24AB_02AD(font);')
    if decl:bb=bb.replace('int result;', 'int result;\n    '+'\n    '.join(decl))
    vs.append(('v'+str(len(vs)),base[:f.body.s]+bb+base[f.body.e:],key,evkey,font,form))
ev=autosearch.Evaluator(ctx,name,6,out/'cache');rows=[]
for (n,t,*meta),r in zip(vs,ev.many([t for _,t,*_ in vs])):
    (out/(n+'.c')).write_text(t);rows.append({'name':n,'meta':meta,**r})
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1));print('exact',[(r['name'],r['meta'],r.get('all_exact')) for r in rows if r.get('exact')]);print('best',[(r['name'],r.get('score')) for r in sorted(rows,key=lambda r:r.get('score',[9]))[:12]])
