from pathlib import Path
import sys,json,itertools
ROOT=Path.cwd();sys.path.insert(0,str(ROOT/'tools'))
import modctx,autosearch,csrc
name='f_29D6_000A';ctx=modctx.resolve(func=name);base=ctx.text;f=csrc.Source(base).function(name);b=base[f.body.s:f.body.e]
out=ROOT/'build/workers/blockers/tandy-subtractions';out.mkdir(parents=True,exist_ok=True);vs=[]
c='((char)chan + 0x80)';p='(f & 0xf)'
firsts=[p+' + '+c,p+' - (-'+c+')',c+' - (-'+p+')','-(-'+p+' - '+c+')','(int)((unsigned)'+c+' + '+p+')',p+' - ((-0x80) - (char)chan)']
lasts=['vol + '+c+' + 0x10','vol - (-'+c+') + 0x10',c+' - (-vol) + 0x10','-(-vol - '+c+') + 0x10','vol + ('+c+' - (-0x10))','vol - ((-0x80) - (char)chan) + 0x10','vol - (-'+c+' - 0x10)','0x10 - (-vol - '+c+')']
for first,last in itertools.product(firsts,lasts):
    bb=b.replace(p+' + '+c,first).replace('vol + '+c+' + 0x10',last)
    vs.append(('v'+str(len(vs)),base[:f.body.s]+bb+base[f.body.e:],first,last))
ev=autosearch.Evaluator(ctx,name,6,out/'cache');rows=[]
for (n,t,*meta),r in zip(vs,ev.many([t for _,t,*_ in vs])):
    (out/(n+'.c')).write_text(t);rows.append({'name':n,'meta':meta,**r})
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1));print('exact',[(r['name'],r.get('all_exact')) for r in rows if r.get('exact')]);print('best',[(r['name'],r.get('score')) for r in sorted(rows,key=lambda r:r.get('score',[9]))[:12]])
