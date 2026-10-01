from pathlib import Path
import sys,json,itertools,re
ROOT=Path.cwd();sys.path.insert(0,str(ROOT/'tools'))
import modctx,autosearch,csrc
name='f_2505_0453';ctx=modctx.resolve(func=name);base=autosearch.unscaffold(ctx.text,name)
f=csrc.Source(base).function(name);b=base[f.body.s:f.body.e]
out=ROOT/'build/workers/blockers/window-live';out.mkdir(parents=True,exist_ok=True);vs=[]
for typed,retval,count,copies,index in itertools.product([False,True],['none','early','late'],[False,True],[False,True],['plain','separate','repeated']):
    bb=b
    if typed:
        bb=bb.replace('char far *w;','struct Win far *w;').replace('w = f_2505_0006(win);','w = (struct Win far *)f_2505_0006(win);')
        bb=bb.replace('*(int far *)(w + 0xc)','w->count').replace('((int far * far *)(w + 0x2c))[idx]','(int far *)w->objs[idx]')
    if retval!='none':
        if retval=='early':bb=bb.replace('{\n','{\n    int value;\n',1)
        else:bb=bb.replace('int far *r;','int far *r;\n    int value;')
        bb=bb.replace('return r[kind];','value = r[kind];\n            return value;')
    if count:
        bb=bb.replace('int idx;','int idx;\n    int n;')
        value='w->count' if typed else '*(int far *)(w + 0xc)'
        bb=bb.replace('if ('+value+' > idx)', 'n = '+value+';\n        if (n > idx)')
    if copies:
        bb=bb.replace('int idx;','int idx;\n    int index;').replace('idx = obj & 0xff;','index = obj & 0xff;\n        idx = index;')
    if index=='separate':bb=bb.replace('idx = obj & 0xff;','idx = obj;\n        idx &= 0xff;')
    elif index=='repeated':bb=bb.replace(' > idx)', ' > (obj & 0xff))')
    vs.append(('v'+str(len(vs)),base[:f.body.s]+bb+base[f.body.e:],typed,retval,count,copies,index))
ev=autosearch.Evaluator(ctx,name,6,out/'cache');rows=[]
for start in range(0,len(vs),24):
    batch=vs[start:start+24]
    for (n,t,*meta),r in zip(batch,ev.many([t for _,t,*_ in batch])):
        (out/(n+'.c')).write_text(t);rows.append({'name':n,'meta':meta,**r})
    ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1));print('done',len(rows),'exact',[(r['name'],r.get('all_exact')) for r in rows if r.get('exact')],flush=True)
    if any(r.get('all_exact') for r in rows):break
print('best',[(r['name'],r.get('score'),r.get('all_exact')) for r in sorted(rows,key=lambda r:r.get('score',[9]))[:8]])
