from pathlib import Path
import sys,json,itertools,re
ROOT=Path.cwd();sys.path.insert(0,str(ROOT/'tools'))
import modctx,autosearch,csrc
name='f_29D6_000A';ctx=modctx.resolve(func=name);base=ctx.text;f=csrc.Source(base).function(name);b=base[f.body.s:f.body.e]
out=ROOT/'build/workers/blockers/tandy-cse';out.mkdir(parents=True,exist_ok=True);vs=[]
exprs=['(char)(chan + 0x80)','(unsigned char)(chan + 0x80)','(char)((char)chan + 0x80)','(unsigned char)((unsigned char)chan + 0x80)','((chan + 0x80) & 0xff)','((unsigned)chan + 0x80)','(char)(0x80 + chan)','(unsigned char)(chan | 0x80)','((char)chan | 0x80)','((char)chan ^ 0x80)']
for e,order in itertools.product(exprs,['first','last']):
    bb=b.replace('((char)chan + 0x80)',e)
    if order=='first':bb=bb.replace('(f & 0xf) + '+e,e+' + (f & 0xf)').replace('vol + '+e+' + 0x10',e+' + vol + 0x10')
    vs.append(('v'+str(len(vs)),base[:f.body.s]+bb+base[f.body.e:],e,order))
ev=autosearch.Evaluator(ctx,name,6,out/'cache');rows=[]
for (n,t,*meta),r in zip(vs,ev.many([t for _,t,*_ in vs])):
    (out/(n+'.c')).write_text(t);rows.append({'name':n,'meta':meta,**r})
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1));print([(r['name'],r.get('score'),r.get('all_exact')) for r in rows])
