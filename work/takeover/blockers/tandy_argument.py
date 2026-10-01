from pathlib import Path
import sys,json,itertools
ROOT=Path.cwd();sys.path.insert(0,str(ROOT/'tools'))
import modctx,autosearch,csrc
name='f_29D6_000A';ctx=modctx.resolve(func=name);base=ctx.text;f=csrc.Source(base).function(name);b=base[f.body.s:f.body.e]
out=ROOT/'build/workers/blockers/tandy-argument';out.mkdir(parents=True,exist_ok=True);vs=[]
for ty,reverse in itertools.product(['int','unsigned','char','unsigned char'],[False,True]):
    bb=b.replace('int f;','int f;\n    '+ty+' channel;')
    exp='(channel = (char)chan + 0x80)'
    bb=bb.replace('(f & 0xf) + ((char)chan + 0x80)',exp+' + (f & 0xf)' if reverse else '(f & 0xf) + '+exp)
    bb=bb.replace('vol + ((char)chan + 0x80) + 0x10', 'vol + channel + 0x10')
    vs.append(('v'+str(len(vs)),base[:f.body.s]+bb+base[f.body.e:],ty,reverse))
for where,sign in itertools.product(['before_second','before_third','after_first'],['word','byte']):
    bb=b;cond='(unsigned'+(' char' if sign=='byte' else '')+')((char)chan + 0x80) >= 0'
    if where in ['before_second','after_first']:bb=bb.replace('    f_29F0_002A(0x205, f >> 4);','    if ('+cond+') f_29F0_002A(0x205, f >> 4);')
    else:bb=bb.replace('    vol >>= 3;', '    if ('+cond+') vol >>= 3;')
    vs.append(('v'+str(len(vs)),base[:f.body.s]+bb+base[f.body.e:],where,sign))
ev=autosearch.Evaluator(ctx,name,6,out/'cache');rows=[]
for (n,t,*meta),r in zip(vs,ev.many([t for _,t,*_ in vs])):
    (out/(n+'.c')).write_text(t);rows.append({'name':n,'meta':meta,**r})
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1));print([(r['name'],r.get('score'),r.get('all_exact')) for r in rows])
